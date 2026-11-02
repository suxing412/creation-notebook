"""Verify exact model identity and an explicit public 008 web-delivery contract.

The JSON contract is page-authored, not guessed from directory globs. Example:
{"study":"008","schema_version":"008-web-delivery-1", "model_archive_sha256":"approved SHA",
 "allowed_files":["index.html","web-review/delivery-contract.json",...],
 "required_files":["index.html",...],
 "required_reports":[{"path":"web-review/import-unit-checks.json",
   "scope":"exact report scope", "bindings":{"source_sha256":"web-source/import_model.py"}}]}

Report `passed: true` is accepted only as a boolean. Optional scope and bindings
must exactly match. This verifies declared evidence identity; it never reruns
model quality, browser, GPU, physical-device, accessibility or manufacturing QA.
"""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import re
import sys
sys.dont_write_bytecode = True
from import_model import canonical_path, strict_json, validate_manifest, validate_records, sha, HASH_PATTERN, PRIVATE_PARTS, BAD_SUFFIXES, ARCHIVE_SUFFIXES, MODEL_DIRS, MODEL_ROOT

DEFAULT_CONTRACT = 'web-review/delivery-contract.json'
DEFAULT_OUTPUT = 'web-review/delivery-files.json'
FREEZE = 'WEB-FROZEN-SHA256.json'
LOCK_NAMES = {'APPROVED_ARCHIVE_SHA256', 'APPROVED_MANIFEST_SHA256', 'APPROVED_IDENTITIES_SHA256', 'APPROVED_ENTRYSET_SHA256'}
TEXT_SUFFIXES = {'.html', '.js', '.mjs', '.cjs', '.css', '.md', '.json', '.py', '.txt'}


def has_concrete_private_path(content):
    # Prefix literals in a detector are not concrete host paths.
    prefixes = ('/' + 'workspace' + '/', '/' + 'home' + '/' + 'agent' + '/')
    if any(re.search(re.escape(prefix) + r'[A-Za-z0-9_.~/-]+', content) for prefix in prefixes):
        return True
    return bool(re.search('/' + 'tmp' + r'/(?:web008|008-import|008-model-import)[A-Za-z0-9_.~/-]*', content))


def privacy_controls():
    workspace = '/' + 'workspace' + '/'
    home = '/' + 'home' + '/' + 'agent' + '/'
    cases = [(workspace + 'scratch/private', True), (home + 'credentials', True), ("b'" + workspace + "'", False), ("b'" + home + "'", False), ("rb'" + workspace + r"(?:scratch|shared)/[A-Za-z0-9_-]{6,}'", False)]
    return all(has_concrete_private_path(value) == expected for value, expected in cases)


def read_lock(path):
    result = {}
    for node in ast.parse(path.read_text()).body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            raise ValueError('Generated import lock contains non-assignment code')
        key = node.targets[0].id
        if key not in LOCK_NAMES or key in result:
            raise ValueError('Generated import lock has unexpected/duplicate name')
        value = ast.literal_eval(node.value)
        if type(value) is not str or not HASH_PATTERN.fullmatch(value):
            raise ValueError('Generated import lock digest is malformed')
        result[key] = value
    if set(result) != LOCK_NAMES:
        raise ValueError('Generated import lock is incomplete')
    return result


def validate_contract(contract, contract_name):
    if not isinstance(contract, dict) or contract.get('study') != '008' or contract.get('schema_version') != '008-web-delivery-1':
        raise ValueError('Unsupported 008 web-delivery contract')
    if type(contract.get('model_archive_sha256')) is not str or not HASH_PATTERN.fullmatch(contract['model_archive_sha256']):
        raise ValueError('Delivery contract requires independently approved model archive SHA256')
    sets = {}
    for key in ('allowed_files', 'required_files'):
        names = contract.get(key)
        if not isinstance(names, list) or any(type(name) is not str for name in names):
            raise ValueError('Delivery contract ' + key + ' must be a path list')
        normalized = [canonical_path(name, model_namespace=False) for name in names]
        if len(set(normalized)) != len(normalized) or len({n.casefold() for n in normalized}) != len(normalized):
            raise ValueError('Duplicate/case-colliding contract paths')
        sets[key] = set(normalized)
    if contract_name not in sets['allowed_files'] or not sets['required_files'] <= sets['allowed_files']:
        raise ValueError('Contract must include itself and required paths must be allowed')
    if any(name.split('/')[0] in MODEL_DIRS or name in MODEL_ROOT for name in sets['allowed_files']):
        raise ValueError('Web contract cannot expand or replace original model namespace')
    reports = contract.get('required_reports')
    if not isinstance(reports, list) or not reports:
        raise ValueError('Delivery contract must explicitly list at least one required report')
    report_paths = set()
    for report in reports:
        if not isinstance(report, dict):
            raise ValueError('Required report specification must be an object')
        name = canonical_path(report.get('path'), model_namespace=False)
        if name in report_paths or name not in sets['required_files'] or not name.startswith('web-review/') or not name.endswith('.json'):
            raise ValueError('Required reports must be unique required web-review JSON entries')
        report_paths.add(name)
        if 'scope' in report and (type(report['scope']) is not str or not report['scope']):
            raise ValueError('Report scope must be a nonempty exact string')
        bindings = report.get('bindings', {})
        if not isinstance(bindings, dict) or any(type(key) is not str or not key for key in bindings):
            raise ValueError('Report bindings must map field names to file paths')
        for filename in bindings.values():
            canonical_path(filename, model_namespace=False)
    return sets['allowed_files'], sets['required_files'], reports


def safe_path(root, name):
    """Reject symlink ancestors before any read or write, not just leaf links."""
    canonical_path(name, model_namespace=False)
    path = root
    for part in Path(name).parts:
        path = path / part
        if path.is_symlink():
            raise ValueError('Symlink path component forbidden: ' + name)
    return path


def verify(root, contract_name=DEFAULT_CONTRACT, output_name=DEFAULT_OUTPUT):
    root = Path(root).resolve()
    canonical_path(contract_name, model_namespace=False)
    canonical_path(output_name, model_namespace=False)
    output = safe_path(root, output_name)
    if not root.is_dir() or output.is_symlink():
        raise ValueError('Real delivery directory and non-symlink report output required')
    errors, inventory = [], []
    def add(message):
        errors.append(message)
    if not privacy_controls():
        add('Concrete-path detector positive/negative controls failed')
    contract = None
    try:
        contract = strict_json(safe_path(root, contract_name).read_bytes())
        web_allowed, web_required, reports = validate_contract(contract, contract_name)
    except (ValueError, KeyError, OSError, SyntaxError, TypeError):
        add('Public exact delivery contract missing or invalid')
        web_allowed, web_required, reports = set(), set(), []
    model_files, entries = set(), {}
    try:
        parity = strict_json(safe_path(root, 'web-review/asset-parity.json').read_bytes())
        if not isinstance(parity, dict) or parity.get('passed') is not True or parity.get('study') != '008':
            raise ValueError('Parity report must explicitly pass for study 008')
        records = parity.get('files')
        if not isinstance(records, list):
            raise ValueError('Parity record list missing')
        by_path = validate_records(records, {item['path'] for item in records if isinstance(item, dict) and type(item.get('path')) is str})
        model_files = set(by_path)
        for name, item in by_path.items():
            path = safe_path(root, name)
            if not path.is_file():
                add('Original model file missing/symlink: ' + name)
                continue
            data = path.read_bytes()
            if len(data) != item['bytes'] or sha(data) != item['sha256']:
                add('Original model bytes/SHA changed: ' + name)
            entries[name] = data
        lock = read_lock(safe_path(root, 'web-source/model_lock.py'))
        expected_lock = {
            'APPROVED_ARCHIVE_SHA256': parity.get('source_archive_sha256'),
            'APPROVED_MANIFEST_SHA256': parity.get('manifest_sha256'),
            'APPROVED_IDENTITIES_SHA256': sha(json.dumps(parity.get('final_identity_reports'), sort_keys=True, separators=(',', ':')).encode()),
            'APPROVED_ENTRYSET_SHA256': sha(json.dumps(records, sort_keys=True, separators=(',', ':')).encode()),
        }
        if lock != expected_lock:
            add('Approved import lock differs from parity; possible stale parity overwrite')
        if not isinstance(contract, dict) or contract.get('model_archive_sha256') != lock['APPROVED_ARCHIVE_SHA256']:
            add('Import archive differs from independently approved delivery contract; possible old model/lock/parity overwrite')
        if 'manifest.json' in entries and sha(entries['manifest.json']) != lock['APPROVED_MANIFEST_SHA256']:
            add('Original manifest differs from approved import lock')
        manifest = validate_manifest(entries)
        actual_identities = {variant: {'path': path, 'sha256': sha(entries[path])} for variant, path in manifest['final_identity_reports'].items()}
        if parity.get('final_identity_reports') != actual_identities:
            add('Parity final-report map differs from actual approved manifest evidence')
    except (ValueError, KeyError, OSError, SyntaxError, TypeError):
        add('Original model manifest/final identity/parity/lock contract missing or invalid')
    allowed = model_files | web_allowed
    if output_name not in web_allowed:
        add('Fresh delivery report output is not explicitly allowed by the contract')
    # Missing output is expected on the first run; this invocation writes it.
    for name in sorted(web_required - {output_name}):
        try:
            if not safe_path(root, name).is_file():
                add('Required web entry missing: ' + name)
        except ValueError:
            add('Required web path has symlink component: ' + name)
    observed_files = set()
    for path in sorted(root.rglob('*')):
        name = path.relative_to(root).as_posix()
        if path.is_symlink():
            add('Symlink forbidden: ' + name)
            continue
        if path.is_dir():
            if any(part in PRIVATE_PARTS for part in Path(name).parts):
                add('Private/temporary directory: ' + name)
            continue
        if not path.is_file():
            add('Special filesystem entry forbidden: ' + name)
            continue
        observed_files.add(name)
        if name not in allowed:
            add('Outside exact delivery set: ' + name)
        if path.suffix.lower() in ARCHIVE_SUFFIXES:
            add('Nested archive excluded from full model/web delivery: ' + name)
        if any(part in PRIVATE_PARTS for part in Path(name).parts) or path.suffix.lower() in BAD_SUFFIXES:
            add('Private/temporary file: ' + name)
        if path.suffix.lower() in TEXT_SUFFIXES and has_concrete_private_path(path.read_text(errors='replace')):
            add('Concrete private absolute path: ' + name)
        if name not in {FREEZE, output_name}:
            data = path.read_bytes()
            inventory.append({'path': name, 'bytes': len(data), 'sha256': sha(data)})
    if len({name.casefold() for name in observed_files}) != len(observed_files):
        add('Case-colliding delivery files')
    for specification in reports:
        name = specification['path']
        try:
            report = strict_json(safe_path(root, name).read_bytes())
            if not isinstance(report, dict) or report.get('passed') is not True:
                raise ValueError('Report does not explicitly pass')
            if 'scope' in specification and report.get('scope') != specification['scope']:
                raise ValueError('Report scope differs from contract')
            for field, filename in specification.get('bindings', {}).items():
                if report.get(field) != sha(safe_path(root, filename).read_bytes()):
                    raise ValueError('Report source binding mismatch')
        except (ValueError, KeyError, OSError, TypeError):
            add('Required evidence missing/false/stale: ' + name)
    result = {
        'passed': not errors,
        'study': '008',
        'scope': 'Exact original model entry identity, declared final 008 check-report binding, explicit web file set, and declared web evidence identity. Does not rerun model geometry or browser/GPU/physical/accessibility/manufacturing tests.',
        'privacy_detector_controls_passed': privacy_controls(),
        'contract_path': contract_name,
        'contract_sha256': sha(safe_path(root, contract_name).read_bytes()) if not errors and safe_path(root, contract_name).is_file() else None,
        'checker_sha256': sha(Path(__file__).read_bytes()),
        'files_count': len(inventory),
        'bytes': sum(item['bytes'] for item in inventory),
        'excluded_from_inventory': [FREEZE, output_name],
        'errors': errors,
        'files': inventory,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--contract', default=DEFAULT_CONTRACT, help='Relative public exact-file contract path')
    parser.add_argument('--output', default=DEFAULT_OUTPUT, help='Relative fresh verification report path')
    args = parser.parse_args()
    result = verify(args.directory, args.contract, args.output)
    print(json.dumps({key: value for key, value in result.items() if key != 'files'}, ensure_ascii=False, indent=2))
    raise SystemExit(not result['passed'])
