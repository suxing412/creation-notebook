"""Isolated fixtures for 008 snapshot import; no writes to authored or model dirs."""
from pathlib import Path
import argparse
import copy
import json
import re
import tempfile
import warnings
import zipfile
import sys
sys.dont_write_bytecode = True
import import_model as im
import verify_delivery as vd


def fixture():
    entries = {'README.md': b'Fixture only', 'viewer/index.html': b'<title>Fixture</title>', 'parameter-contract.json': b'{"fixture":true,"scope":"contract content is retained without being interpreted as geometry approval"}'}
    source_paths = {'native_checker': 'source/check.py', 'glb_checker': 'source/check_glb.py', 'recipe': 'source/recipe.py', 'comparison_checker': 'source/compare_exports.py'}
    for path in list(source_paths.values()) + ['source/run_gates.py']:
        entries[path] = ('# Fixture ' + path).encode()
    selected = {}
    for variant in sorted(im.VARIANTS):
        paths = {'native': f'assets/{variant}/model.blend', 'glb': f'assets/{variant}/model.glb', 'info': f'assets/{variant}/model-info.json', **source_paths}
        for key in ('native', 'glb', 'info'):
            entries[paths[key]] = ('fixture ' + variant + ' ' + key).encode()
        digests = {key: im.sha(entries[path]) for key, path in paths.items()}
        prefix = f'gate-locked-{variant}-v1'
        selected[variant] = 'review/' + prefix + '-identity.json'
        checks = {}
        for kind in ('native', 'glb', 'comparison'):
            check = {'exit_code': 0, 'new_report_exists': True, 'explicit_pass': True, 'run_id_present': True, 'model_identity_matches': True, 'checker_identity_matches': True, 'report': prefix + '-' + kind + '.json'}
            sub = {'passed': True, 'run_id': variant + '-' + kind, 'model_sha256': digests['native' if kind == 'comparison' else kind], 'checker_sha256': digests[kind + '_checker']}
            if kind == 'native':
                check.update(info_identity_matches=True, recipe_identity_matches=True)
                sub.update(info_sha256=digests['info'], recipe_sha256=digests['recipe'])
            if kind == 'comparison':
                check.update(glb_identity_matches=True, glb_checker_identity_matches=True)
                sub.update(glb_sha256=digests['glb'], glb_checker_sha256=digests['glb_checker'])
            checks[kind] = check
            entries['review/' + check['report']] = json.dumps(sub).encode()
        identity = {'asset': 'assets/' + variant, 'passed': True, 'inputs_stable_during_checks': True, 'input_sha256': digests, 'checks': checks, 'wrapper_sha256': im.sha(entries['source/run_gates.py'])}
        entries[selected[variant]] = json.dumps(identity).encode()
    manifest = {'study': '008', 'version': '1.0.0', 'schema_version': '1.0.0', 'manifest_does_not_hash_itself': True, 'contains_source_archive_itself': False, 'final_identity_reports': selected}
    return entries, manifest


def with_manifest(entries, manifest):
    entries = dict(entries)
    manifest = copy.deepcopy(manifest)
    manifest['files'] = [{'path': name, 'bytes': len(data), 'sha256': im.sha(data)} for name, data in sorted(entries.items()) if name != 'manifest.json']
    entries['manifest.json'] = json.dumps(manifest).encode()
    return entries


def run(output=None):
    cases = []
    with tempfile.TemporaryDirectory(prefix='008-import-test-') as temporary:
        root = Path(temporary)
        target = root / 'model-stage'
        target.mkdir()
        (target / 'sentinel').write_bytes(b'previous target must survive')
        (target / 'web-review').mkdir()
        (target / 'web-review/asset-parity.json').write_bytes(b'old parity must survive failed import')
        baseline = {p.relative_to(target).as_posix(): p.read_bytes() for p in target.rglob('*') if p.is_file()}
        entries, manifest = fixture()
        valid = with_manifest(entries, manifest)
        def archive(name, contents, extra=()):
            path = root / (re.sub(r'[^a-zA-Z0-9_-]', '_', name)[:70] + '-' + im.sha(name.encode())[:8] + '.zip')
            pairs = list(contents.items()) if isinstance(contents, dict) else list(contents)
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_STORED) as package:
                    for name, data in pairs + list(extra):
                        package.writestr(name, data)
            return path
        def reject(name, contents=None, message=None, archive_path=None, expected=None, extra=()):
            path = archive_path or archive(name.replace(' ', '-'), contents, extra)
            digest = expected or im.sha(path.read_bytes())
            try:
                im.run(path, digest, target)
            except (ValueError, KeyError, zipfile.BadZipFile) as exc:
                if message and message not in str(exc):
                    raise AssertionError(name + ' rejected for the wrong reason: ' + repr(exc))
            else:
                raise AssertionError('Invalid archive accepted: ' + name)
            current = {p.relative_to(target).as_posix(): p.read_bytes() for p in target.rglob('*') if p.is_file()}
            assert current == baseline, 'Failed import mutated prior target: ' + name
            assert not target.with_name(target.name + '.previous-import').exists()
            cases.append({'name': name, 'rejected': True, 'previous_target_and_parity_preserved': True})
        good = archive('good', valid)
        reject('unapproved hash', archive_path=good, expected='0' * 64, message='Unapproved')
        for path in ('../escape', '/assets/escape', './manifest.json', 'assets//escape', 'assets/./escape', 'assets/../escape', 'assets\\escape', '.', 'assets/a?b', 'assets/a%2fb', 'assets/a:b'):
            reject('unsafe path ' + repr(path), valid, extra=[(path, b'bad')])
        for path in ('work/raw.log', 'source/__pycache__/x.pyc', 'review/qa/x.json', 'source/x.log', 'source/x.pyc', 'source/x.blend1', 'web-review/asset-parity.json', 'web-source/model_lock.py', 'assets/copy.zip'):
            reject('forbidden path ' + path, valid, extra=[(path, b'bad')])
        reject('unknown root file rejected', valid, extra=[('unknown-root.json', b'not allowed')], message='Outside model namespace')
        reject('parameter contract dot path alias rejected', valid, extra=[('./parameter-contract.json', b'alias')], message='Noncanonical')
        reject('parameter contract directory alias rejected', valid, extra=[('parameter-contract.json/', b'')], message='Duplicate/case-colliding')
        missing_contract = {name: payload for name, payload in entries.items() if name != 'parameter-contract.json'}
        reject('required parameter contract absent', with_manifest(missing_contract, manifest), message='Required model entry missing')
        changed_contract = copy.deepcopy(valid); changed_contract['parameter-contract.json'] += b' '
        reject('parameter contract manifest hash mismatch rejected', changed_contract, message='bytes/SHA mismatch')
        reject('duplicate file', valid, extra=[('README.md', b'replacement')], message='Duplicate/case-colliding')
        reject('duplicate directory', valid, extra=[('source/', b''), ('source/', b'')], message='Duplicate/case-colliding')
        reject('file directory exact collision', valid, extra=[('README.md/', b'')], message='Duplicate/case-colliding')
        reject('case folded collision', valid, extra=[('SOURCE/check.py', b'bad')])
        reject('file directory prefix collision', valid, extra=[('source/nest', b'file'), ('source/nest/child.py', b'child')], message='prefix collision')
        reject('directory payload', valid, extra=[('source/empty/', b'not empty')], message='Directory entry contains payload')
        link = zipfile.ZipInfo('source/link.py'); link.create_system = 3; link.external_attr = 0o120777 << 16
        reject('symlink entry', valid, extra=[(link, b'outside')], message='Symlink or special')
        reject('missing manifest', {'README.md': b'only'}, message='Required model')
        corrupt = root / 'crc.zip'
        corrupted = bytearray(good.read_bytes()); pos = corrupted.index(b'Fixture only'); corrupted[pos] ^= 1; corrupt.write_bytes(corrupted)
        reject('CRC corruption after matching archive SHA', archive_path=corrupt, message='CRC')
        for field, value in [('study', '007'), ('version', ''), ('manifest_does_not_hash_itself', 'true'), ('contains_source_archive_itself', 0), ('final_identity_reports', {})]:
            changed = copy.deepcopy(manifest); changed[field] = value
            reject('invalid manifest ' + field, with_manifest(entries, changed))
        changed = copy.deepcopy(valid)
        m = json.loads(changed['manifest.json']); m['files'].append(copy.deepcopy(m['files'][0])); changed['manifest.json'] = json.dumps(m).encode()
        reject('duplicate manifest record', changed, message='Duplicate manifest')
        changed = copy.deepcopy(valid)
        m = json.loads(changed['manifest.json']); m['files'][0]['bytes'] = True; changed['manifest.json'] = json.dumps(m).encode()
        reject('boolean manifest bytes', changed, message='Invalid manifest bytes')
        changed = copy.deepcopy(valid); changed['source/unmanifested.py'] = b'extra'
        reject('unmanifested extra file', changed, message='exact file set')
        changed = copy.deepcopy(valid); changed['README.md'] += b'changed'
        reject('manifest data hash mismatch', changed, message='bytes/SHA mismatch')
        identity_path = manifest['final_identity_reports']['veil']
        def change_identity(callback):
            changed = copy.deepcopy(entries); report = json.loads(changed[identity_path]); callback(report); changed[identity_path] = json.dumps(report).encode(); return with_manifest(changed, manifest)
        for field in ('passed', 'inputs_stable_during_checks'):
            reject('identity string ' + field, change_identity(lambda r, f=field: r.update({f: 'true'})), message='asset/pass/stability')
        reject('identity wrong asset', change_identity(lambda r: r.update(asset='review/old-candidate')), message='asset/pass/stability')
        reject('stale native digest', change_identity(lambda r: r['input_sha256'].update(native='0' * 64)), message='Final input SHA mismatch')
        reject('stale checker digest', change_identity(lambda r: r['input_sha256'].update(native_checker='0' * 64)), message='Final input SHA mismatch')
        reject('stale wrapper digest', change_identity(lambda r: r.update(wrapper_sha256='0' * 64)), message='wrapper SHA mismatch')
        reject('missing identity check kind', change_identity(lambda r: r['checks'].pop('comparison')), message='check set')
        reject('missing identity boolean field', change_identity(lambda r: r['checks']['native'].pop('recipe_identity_matches')), message='Required identity check flags')
        reject('false identity boolean field', change_identity(lambda r: r['checks']['glb'].update(new_report_exists=False)), message='exit zero and boolean true')
        reject('string identity boolean field', change_identity(lambda r: r['checks']['native'].update(explicit_pass='true')), message='exit zero and boolean true')
        reject('boolean exit code', change_identity(lambda r: r['checks']['glb'].update(exit_code=False)), message='exit zero and boolean true')
        reject('nonzero exit code', change_identity(lambda r: r['checks']['comparison'].update(exit_code=1)), message='exit zero and boolean true')
        reject('subreport different run label', change_identity(lambda r: r['checks']['glb'].update(report='old-glb.json')), message='run label')
        for field, value in [('passed', 'true'), ('run_id', ''), ('model_sha256', '0' * 64), ('checker_sha256', '0' * 64), ('info_sha256', '0' * 64)]:
            changed = copy.deepcopy(entries); path = 'review/gate-locked-veil-v1-native.json'; report = json.loads(changed[path]); report[field] = value; changed[path] = json.dumps(report).encode()
            reject('invalid native subreport ' + field, with_manifest(changed, manifest))
        changed = copy.deepcopy(valid); changed['manifest.json'] = b'{"study":"008","study":"008"}'
        reject('duplicate JSON key', changed, message='Duplicate JSON key')
        # A path replacement after hashing must not change the ZIP bytes consumed.
        snapshot = archive('snapshot', valid); snapshot_bytes = snapshot.read_bytes()
        replacement = archive('replacement', with_manifest({**entries, 'README.md': b'different contents'}, manifest)).read_bytes()
        original_open = im.zipfile.ZipFile
        def swapped_open(source, *args, **kwargs):
            snapshot.write_bytes(replacement)
            return original_open(source, *args, **kwargs)
        try:
            im.zipfile.ZipFile = swapped_open
            snapshot_dest = root / 'snapshot-output'
            im.run(snapshot, im.sha(snapshot_bytes), snapshot_dest)
        finally:
            im.zipfile.ZipFile = original_open
        assert (snapshot_dest / 'README.md').read_bytes() == valid['README.md']
        cases.append({'name': 'disk replacement cannot change consumed approved snapshot', 'passed': True})
        # Simulated final rename failure must roll the previous target back.
        original_rename = Path.rename
        def fail_commit(path, destination):
            if path.name.startswith('008-model-import-') and Path(destination) == target:
                raise OSError('fixture commit interruption')
            return original_rename(path, destination)
        try:
            Path.rename = fail_commit
            try:
                im.run(good, im.sha(good.read_bytes()), target)
            except OSError as exc:
                assert 'fixture commit interruption' in str(exc)
            else:
                raise AssertionError('Commit failure fixture did not execute')
        finally:
            Path.rename = original_rename
        assert {p.relative_to(target).as_posix(): p.read_bytes() for p in target.rglob('*') if p.is_file()} == baseline
        assert not target.with_name(target.name + '.previous-import').exists()
        cases.append({'name': 'commit rename interruption restores previous target and parity', 'passed': True})
        # An accidentally selected authored web target is never replaced.
        (target / 'index.html').write_text('<title>Existing authored page</title>')
        try:
            try:
                im.run(good, im.sha(good.read_bytes()), target)
            except ValueError as exc:
                assert 'authored webpage' in str(exc)
            else:
                raise AssertionError('Authored webpage target was replaced')
            assert (target / 'index.html').read_text() == '<title>Existing authored page</title>'
        finally:
            (target / 'index.html').unlink()
        cases.append({'name': 'authored webpage destination cannot be replaced by model import', 'rejected': True})
        # Success replaces all candidate bytes and produces new locked parity.
        im.run(good, im.sha(good.read_bytes()), target)
        assert not (target / 'sentinel').exists()
        parity = json.loads((target / 'web-review/asset-parity.json').read_text())
        assert parity['passed'] is True and {x['path'] for x in parity['files']} == set(valid)
        assert all((target / name).read_bytes() == data for name, data in valid.items())
        cases.append({'name': 'valid fixture replaces old target and parity only after verification', 'passed': True})
        assert (target / 'parameter-contract.json').read_bytes() == valid['parameter-contract.json']
        cases.append({'name': 'required parameter contract imported byte-for-byte with manifest identity', 'passed': True})
        # Exact web delivery verification is tested on the successful synthetic import.
        (target / 'index.html').write_text('<title>Fixture web</title>')
        required = {'index.html', 'web-review/asset-parity.json', 'web-source/model_lock.py', 'web-review/delivery-contract.json', 'web-review/unit-checks.json'}
        contract = {'study': '008', 'schema_version': '008-web-delivery-1', 'model_archive_sha256': im.sha(good.read_bytes()), 'allowed_files': sorted(required | {'web-review/delivery-files.json'}), 'required_files': sorted(required), 'required_reports': [{'path': 'web-review/unit-checks.json', 'scope': 'fixture only', 'bindings': {'source_sha256': 'index.html'}}]}
        (target / 'web-review/delivery-contract.json').write_text(json.dumps(contract))
        (target / 'web-review/unit-checks.json').write_text(json.dumps({'passed': True, 'scope': 'fixture only', 'source_sha256': im.sha((target / 'index.html').read_bytes())}))
        result = vd.verify(target)
        assert result['passed'], result['errors']
        cases.append({'name': 'exact public web delivery fixture passes', 'passed': True})
        def reject_delivery(name, path, payload, expected_message, absent=False):
            destination = target / path
            previous = destination.read_bytes() if destination.exists() else None
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload)
            try:
                result = vd.verify(target)
                assert not result['passed'] and any(expected_message in error for error in result['errors']), (name, result['errors'])
            finally:
                if previous is None:
                    destination.unlink()
                else:
                    destination.write_bytes(previous)
            cases.append({'name': name, 'rejected': True})
        reject_delivery('undeclared web file rejected', 'extra.txt', b'not public', 'Outside exact delivery set')
        old_parity = json.loads((target / 'web-review/asset-parity.json').read_bytes()); old_parity['source_archive_sha256'] = '0' * 64
        reject_delivery('old parity overwrite rejected', 'web-review/asset-parity.json', json.dumps(old_parity).encode(), 'stale parity overwrite')
        old_lock = (target / 'web-source/model_lock.py').read_text().replace(im.sha(good.read_bytes()), '0' * 64)
        parity_bytes = (target / 'web-review/asset-parity.json').read_bytes()
        (target / 'web-review/asset-parity.json').write_text(json.dumps(old_parity))
        try:
            reject_delivery('old parity and matching lock rejected by independent archive anchor', 'web-source/model_lock.py', old_lock.encode(), 'independently approved delivery contract')
        finally:
            (target / 'web-review/asset-parity.json').write_bytes(parity_bytes)
        evidence = json.loads((target / 'web-review/unit-checks.json').read_bytes()); evidence['passed'] = 'true'
        reject_delivery('string passed web report rejected', 'web-review/unit-checks.json', json.dumps(evidence).encode(), 'Required evidence missing/false/stale')
        reject_delivery('stale web report source binding rejected', 'index.html', b'<title>Changed web</title>', 'Required evidence missing/false/stale')
        reject_delivery('changed original model bytes rejected', 'README.md', b'changed', 'Original model bytes/SHA changed')
        reject_delivery('pyc contamination rejected', 'web-source/hidden.pyc', b'bad', 'Private/temporary file')
        (target / 'web-review/link').symlink_to(root, target_is_directory=True)
        try:
            result = vd.verify(target)
            assert not result['passed'] and any('Symlink forbidden' in error for error in result['errors'])
        finally:
            (target / 'web-review/link').unlink()
        cases.append({'name': 'delivery directory symlink rejected without following', 'rejected': True})
        assert vd.verify(target)['passed']
    report = {'passed': True, 'study': '008', 'scope': 'Isolated tiny synthetic ZIP fixtures for path safety, CRC, immutable-snapshot consumption, exact manifest and current final-input identity binding, transactional rollback, and explicit delivery-contract evidence binding. Not actual model or browser validation.', 'source_sha256': im.sha(Path(im.__file__).read_bytes()), 'checker_sha256': im.sha(Path(__file__).read_bytes()), 'delivery_checker_sha256': im.sha(Path(vd.__file__).read_bytes()), 'count': len(cases), 'cases': cases}
    if output:
        output = Path(output); output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path); args = parser.parse_args()
    result = run(args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
