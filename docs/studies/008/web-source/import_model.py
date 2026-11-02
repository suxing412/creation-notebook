"""Snapshot-verified 008 model import. It never consumes the archive path twice.

The target is a model-only staging directory, replaced only after complete path,
CRC, manifest and final-input identity verification. The web author composes into
a separate copy; this importer cannot preserve candidate web files or old parity.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import io
import json
import re
import shutil
import stat
import tempfile
import unicodedata
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIRS = frozenset({'assets', 'review', 'source', 'configs', 'vendor', 'viewer'})
MODEL_ROOT = frozenset({'README.md', 'schema.json', 'manifest.json', 'parameter-contract.json'})
VARIANTS = frozenset({'veil', 'horizon', 'fold'})
PRIVATE_PARTS = frozenset({'work', 'qa', '__qa', '__modelqa', 'before', '__pycache__', '.git', '.aws', '.codex', '.agents'})
ARCHIVE_SUFFIXES = frozenset({'.zip', '.tar', '.gz', '.tgz', '.7z', '.rar', '.bz2', '.xz'})
BAD_SUFFIXES = frozenset({'.log', '.pyc', '.pyo', '.blend1', '.blend2'})
HASH_PATTERN = re.compile(r'^[0-9a-f]{64}$')
MAX_ENTRIES = 20000
MAX_UNCOMPRESSED_BYTES = 2 * 1024 * 1024 * 1024


def sha(data):
    return hashlib.sha256(data).hexdigest()


def strict_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    def reject_constant(value):
        raise ValueError('Nonfinite JSON constant: ' + value)
    return json.loads(data, object_pairs_hook=pairs, parse_constant=reject_constant)


def canonical_path(name, is_directory=False, model_namespace=True):
    if type(name) is not str or not name or '\x00' in name or '\\' in name:
        raise ValueError('Unsafe empty/NUL/backslash path')
    if unicodedata.normalize('NFC', name) != name:
        raise ValueError('Noncanonical Unicode path: ' + name)
    spelling = name[:-1] if is_directory and name.endswith('/') else name
    p = PurePosixPath(spelling)
    if not spelling or not p.parts or p.is_absolute() or '..' in p.parts or spelling != p.as_posix():
        raise ValueError('Noncanonical or parent/absolute path: ' + name)
    if any(ord(c) < 32 or c in ':?#%' for c in spelling):
        raise ValueError('Unsafe control/URL/drive path spelling: ' + name)
    if any(part in PRIVATE_PARTS for part in p.parts) or p.suffix.lower() in BAD_SUFFIXES:
        raise ValueError('Private/temporary path: ' + name)
    if p.suffix.lower() in ARCHIVE_SUFFIXES:
        raise ValueError('Nested archive excluded: ' + name)
    if model_namespace and p.parts[0] not in MODEL_DIRS and spelling not in MODEL_ROOT:
        raise ValueError('Outside model namespace: ' + name)
    return spelling


def validate_records(records, expected_paths):
    if not isinstance(records, list):
        raise ValueError('Manifest files must be a list')
    by_path = {}
    for item in records:
        if not isinstance(item, dict):
            raise ValueError('Manifest file record must be an object')
        name = canonical_path(item.get('path'))
        if name in by_path:
            raise ValueError('Duplicate manifest path: ' + name)
        size, digest = item.get('bytes'), item.get('sha256')
        if type(size) is not int or size < 0 or type(digest) is not str or not HASH_PATTERN.fullmatch(digest):
            raise ValueError('Invalid manifest bytes/SHA record: ' + name)
        by_path[name] = item
    if set(by_path) != set(expected_paths):
        raise ValueError('Original manifest exact file set differs from archive')
    return by_path


def validate_identity(entries, manifest):
    """Bind each declared final report to the actual 008 inputs and checkers.

    Historical review reports may coexist, but may not be selected implicitly.
    Only the exact three paths declared by the approved manifest are consumed.
    """
    selected = manifest.get('final_identity_reports')
    if not isinstance(selected, dict) or set(selected) != VARIANTS:
        raise ValueError('Manifest must explicitly map three final identity reports')
    source_paths = {'native_checker': 'source/check.py', 'glb_checker': 'source/check_glb.py', 'recipe': 'source/recipe.py', 'comparison_checker': 'source/compare_exports.py'}
    required_flags = {'new_report_exists', 'explicit_pass', 'run_id_present', 'model_identity_matches', 'checker_identity_matches'}
    result = {}
    for variant, identity_path in selected.items():
        canonical_path(identity_path)
        if not identity_path.startswith('review/') or identity_path.count('/') != 1 or not identity_path.endswith('-identity.json'):
            raise ValueError('Final identity path must name a public review identity report')
        report = strict_json(entries[identity_path])
        if not isinstance(report, dict) or report.get('asset') != 'assets/' + variant or report.get('passed') is not True or report.get('inputs_stable_during_checks') is not True:
            raise ValueError('Final identity asset/pass/stability mismatch: ' + variant)
        paths = {'native': 'assets/' + variant + '/model.blend', 'glb': 'assets/' + variant + '/model.glb', 'info': 'assets/' + variant + '/model-info.json', **source_paths}
        digests = report.get('input_sha256')
        if not isinstance(digests, dict) or set(digests) != set(paths):
            raise ValueError('Final identity input set mismatch: ' + variant)
        for key, path in paths.items():
            if path not in entries or digests.get(key) != sha(entries[path]):
                raise ValueError('Final input SHA mismatch: ' + path)
        if report.get('wrapper_sha256') != sha(entries['source/run_gates.py']):
            raise ValueError('Final identity wrapper SHA mismatch')
        checks = report.get('checks')
        if not isinstance(checks, dict) or set(checks) != {'native', 'glb', 'comparison'}:
            raise ValueError('Final identity check set must be exactly native/glb/comparison')
        for kind, check in checks.items():
            extra_flags = {'info_identity_matches', 'recipe_identity_matches'} if kind == 'native' else {'glb_identity_matches', 'glb_checker_identity_matches'} if kind == 'comparison' else set()
            if not isinstance(check, dict) or not required_flags | extra_flags <= set(check):
                raise ValueError('Required identity check flags missing: ' + kind)
            if type(check.get('exit_code')) is not int or check['exit_code'] != 0 or any(value is not True for key, value in check.items() if key not in {'exit_code', 'report'}):
                raise ValueError('Identity checks require exit zero and boolean true flags: ' + kind)
            basename = check.get('report')
            expected_basename = PurePosixPath(identity_path).name.removesuffix('-identity.json') + '-' + kind + '.json'
            if basename != expected_basename:
                raise ValueError('Final subreport basename does not share the identity run label')
            subreport = strict_json(entries['review/' + basename])
            if not isinstance(subreport, dict) or subreport.get('passed') is not True or type(subreport.get('run_id')) is not str or not subreport['run_id']:
                raise ValueError('Final subreport explicit pass/run identity missing')
            expected_fields = {'model_sha256': digests['native' if kind == 'comparison' else kind], 'checker_sha256': digests[kind + '_checker']}
            if kind == 'native':
                expected_fields.update(info_sha256=digests['info'], recipe_sha256=digests['recipe'])
            if kind == 'comparison':
                expected_fields.update(glb_sha256=digests['glb'], glb_checker_sha256=digests['glb_checker'])
            if any(subreport.get(field) != digest for field, digest in expected_fields.items()):
                raise ValueError('Final subreport bytes identity mismatch: ' + kind)
        result[variant] = {'path': identity_path, 'sha256': sha(entries[identity_path])}
    if len({item['path'] for item in result.values()}) != len(VARIANTS):
        raise ValueError('Final identity report paths must be unique')
    return result


def validate_manifest(entries):
    if not isinstance(entries, dict) or not {'manifest.json', 'README.md', 'parameter-contract.json', 'viewer/index.html'} <= entries.keys():
        raise ValueError('Required model entry missing')
    manifest = strict_json(entries['manifest.json'])
    if not isinstance(manifest, dict) or manifest.get('study') != '008':
        raise ValueError('Not an 008 model manifest')
    if type(manifest.get('version')) is not str or not manifest['version']:
        raise ValueError('Model manifest version missing')
    if manifest.get('manifest_does_not_hash_itself') is not True or manifest.get('contains_source_archive_itself') is not False:
        raise ValueError('Manifest self/archive flags must be explicit booleans')
    records = validate_records(manifest.get('files'), set(entries) - {'manifest.json'})
    for name, item in records.items():
        data = entries[name]
        if type(data) is not bytes or len(data) != item['bytes'] or sha(data) != item['sha256']:
            raise ValueError('Original manifest bytes/SHA mismatch: ' + name)
    validate_identity(entries, manifest)
    return manifest


def load_archive(archive, expected):
    if type(expected) is not str or not HASH_PATTERN.fullmatch(expected):
        raise ValueError('Expected SHA256 must be 64 lowercase hex characters')
    raw = Path(archive).read_bytes()
    if sha(raw) != expected:
        raise ValueError('Unapproved source archive SHA256')
    entries, declared, file_paths = {}, {}, set()
    # Immutable snapshot used for both hashing and all subsequent ZIP reads.
    with zipfile.ZipFile(io.BytesIO(raw)) as archive_zip:
        infos = archive_zip.infolist()
        if len(infos) > MAX_ENTRIES or sum(q.file_size for q in infos) > MAX_UNCOMPRESSED_BYTES:
            raise ValueError('Archive exceeds declared import bounds')
        for info in infos:
            name = canonical_path(info.filename, info.is_dir())
            folded = name.casefold()
            if folded in declared:
                raise ValueError('Duplicate/case-colliding ZIP entry: ' + info.filename)
            declared[folded] = name
            mode = (info.external_attr >> 16) & 0o170000
            if mode not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise ValueError('Symlink or special file rejected: ' + name)
            if info.is_dir() and mode == stat.S_IFREG or not info.is_dir() and mode == stat.S_IFDIR:
                raise ValueError('ZIP directory/type mismatch: ' + name)
            if info.flag_bits & 1:
                raise ValueError('Encrypted ZIP entry is unsupported')
            payload = archive_zip.read(info)  # Full decompression and CRC, including directory records.
            if info.is_dir():
                if info.file_size != 0 or payload:
                    raise ValueError('Directory entry contains payload')
                continue
            file_paths.add(name)
            entries[name] = payload
    folded_files = {p.casefold() for p in file_paths}
    for name in file_paths:
        if any(parent.as_posix().casefold() in folded_files for parent in PurePosixPath(name).parents if parent.as_posix() != '.'):
            raise ValueError('File/directory prefix collision: ' + name)
    validate_manifest(entries)
    return entries


def make_parity(entries, archive_name, expected):
    files = [{'path': name, 'bytes': len(data), 'sha256': sha(data)} for name, data in sorted(entries.items())]
    return {
        'passed': True,
        'study': '008',
        'scope': 'All original model ZIP file entries CRC-read from the approved immutable snapshot and imported byte-for-byte. Transfer identity and final-input report binding only; not independent model quality or browser validation.',
        'source_archive_name': archive_name,
        'source_archive_sha256': expected,
        'manifest_sha256': sha(entries['manifest.json']),
        'final_identity_reports': validate_identity(entries, strict_json(entries['manifest.json'])),
        'files': files,
    }


def run(archive, expected, dest):
    archive, dest = Path(archive), Path(dest)
    entries = load_archive(archive, expected)
    if any(path.is_symlink() for path in (dest, *dest.parents)) or dest.exists() and not dest.is_dir():
        raise ValueError('Import destination and ancestors must be real directories')
    if not dest.parent.is_dir():
        raise ValueError('Import destination parent must already exist')
    if (dest / 'index.html').exists() or (dest / 'style.css').exists() or (dest / '.openai').exists():
        raise ValueError('Refusing to replace an authored webpage/hosting directory; use a model-only staging destination')
    backup = dest.with_name(dest.name + '.previous-import')
    if backup.exists() or backup.is_symlink():
        raise ValueError('Previous import backup exists; resolve it explicitly')
    temp = Path(tempfile.mkdtemp(prefix='008-model-import-', dir=dest.parent))
    try:
        for name, data in entries.items():
            target = temp / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        report = make_parity(entries, archive.name, expected)
        (temp / 'web-review').mkdir()
        (temp / 'web-review/asset-parity.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        (temp / 'web-source').mkdir()
        lock = {
            'APPROVED_ARCHIVE_SHA256': expected,
            'APPROVED_MANIFEST_SHA256': report['manifest_sha256'],
            'APPROVED_IDENTITIES_SHA256': sha(json.dumps(report['final_identity_reports'], sort_keys=True, separators=(',', ':')).encode()),
            'APPROVED_ENTRYSET_SHA256': sha(json.dumps(report['files'], sort_keys=True, separators=(',', ':')).encode()),
        }
        (temp / 'web-source/model_lock.py').write_text('# Generated only by snapshot-verified import; do not replace with old web files.\n' + ''.join(key + ' = ' + repr(value) + '\n' for key, value in lock.items()))
        # Re-read staged bytes, not just the bytes intended to be written.
        for name, data in entries.items():
            if (temp / name).read_bytes() != data:
                raise ValueError('Staged write verification failed: ' + name)
        if dest.exists():
            dest.rename(backup)
        try:
            temp.rename(dest)
        except BaseException:
            if backup.exists():
                backup.rename(dest)
            raise
        if backup.exists():
            shutil.rmtree(backup)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
    return {'imported': len(entries), 'archive_sha256': expected, 'manifest_sha256': report['manifest_sha256']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('archive', type=Path)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--dest', type=Path, required=True, help='Fresh model-only staging directory; never the authored webpage directory')
    args = parser.parse_args()
    print(json.dumps(run(args.archive, args.sha256, args.dest), indent=2))
