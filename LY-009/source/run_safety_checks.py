#!/usr/bin/env python3
"""Read-only safety preflight. Exit 3: checked, admission BLOCKED; 2: check failed.

Consumes this checkout's workpack sources and immutable Git model bytes. Writes
only a new external directory. Never accepts seats, freezes G, changes locks,
publishes, or installs models. This does not replace full seat acceptance.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

WP = Path(__file__).resolve().parents[2]
FILES = ('LY-004/source/build.py', 'LY-004/source/site_data.py',
         'LY-007/source/near_retention.py', 'LY-009/source/check_whitelist.py',
         'LY-010/source/build_decision.py', 'LY-010/source/decision_data.py',
         'LY-009/source/run_all.sh', 'LY-009/source/run_safety_checks.py',
         'LY-009/source/test_safety_checks.py', 'LY-009/source/SAFETY_CHECKS.md')


def safe_path(path):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('symlink paths are forbidden')
    return path.resolve()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def run(lab, commit, out):
    lab, out = safe_path(lab), safe_path(out)
    if out.exists() or out == WP or WP in out.parents or out == lab or lab in out.parents:
        raise ValueError('output must be a new directory outside both input trees')
    if not out.parent.is_dir():
        raise ValueError('output parent must already exist')
    identities = {}
    for rel in FILES:
        path = safe_path(WP / rel)
        data = path.read_bytes()
        identities[rel] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    whitelist = module('workflow_whitelist', WP / 'LY-009/source/check_whitelist.py')
    classified = [whitelist.check_paths(rel.split('/')[0], [(rel, identity['bytes'])])
                  for rel, identity in identities.items()]
    if any(c['verdict'] != 'PASS' for c in classified):
        raise ValueError('source destinations failed the seat whitelist')
    # Never supply the trusted-installation argument: this runner has no approval input.
    sys.path.insert(0, str(WP / 'LY-004/source'))
    try:
        phase = module('workflow_phase', WP / 'LY-004/source/build.py')
    finally:
        sys.path.pop(0)
    rows = [{'id': item['id'], 'request': item['request'], **phase.gate(item)}
            for item in phase.SD.GATE_ITEMS]
    installs = [r['id'] for r in rows if r['admitted'] and r['request'] == 'install180']
    markers = [r['id'] for r in rows if r['admitted'] and r['request'] == 'marker']
    if installs or sorted(markers) != ['P16', 'P17', 'P18', 'P19', 'P20', 'P21']:
        raise ValueError('unexpected installation or research-marker result')
    # Also check the original entry point; a new wrapper must not leave it unsafe.
    legacy = subprocess.run([sys.executable, '-I', '-B', str(WP / 'LY-010/source/build_decision.py')],
                            capture_output=True, text=True)
    if legacy.returncode == 0 or not legacy.stderr.startswith('BLOCKED: unfinished legacy builder is quarantined;'):
        raise ValueError('LY-010 legacy entry point is not safely quarantined')
    stage = Path(tempfile.mkdtemp(prefix='.' + out.name + '-', dir=out.parent))
    try:
        near = subprocess.run([sys.executable, '-I', '-B', str(WP / 'LY-007/source/near_retention.py'),
                               str(stage / 'near'), str(lab), commit], capture_output=True, text=True)
        if near.returncode:
            raise ValueError('LY-007 real Git CLI failed (exit ' + str(near.returncode) + ')')
        reference = json.loads((stage / 'near/qa/near-retention.json').read_text(encoding='utf-8'))
        if not reference['summary']['references_pass'] or reference['summary']['stems_with_tier_copy_of_LOD0']:
            raise ValueError('LY-007 report failed reference/LOD checks')
        dump(stage / 'phase-gate.json', {'rows': rows, 'installations': installs, 'researchMarkers': markers})
        dump(stage / 'whitelist.json', classified)
        summary = {'schema': 'luoyang-safety-preflight-v1', 'checksPassed': True, 'admission': 'blocked',
                   'G_frozen': False, 'formalGBaseline': None, 'acceptedSeats': [], 'productionAuthorized': False,
                   'installationCount': len(installs), 'researchMarkerCount': len(markers),
                   'references': reference['summary'], 'legacyBuilder': 'quarantined', 'sourceIdentities': identities,
                   'notRun': ['LY-004 full build', 'LY-009 run_all/check_board', 'LY-010 formal acceptance',
                              'historical model replay', 'glTF external resources and renderer'],
                   'note': 'Safety checks grant no installation, acceptance or publication authority.'}
        dump(stage / 'summary.json', summary)
        # mkdir refuses a destination created while the checks were running.
        out.mkdir()
        for child in stage.iterdir():
            child.rename(out / child.name)
        stage.rmdir()
        return summary
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--lab', required=True, help='Git repository with the requested real model objects')
    ap.add_argument('--commit', required=True, help='Commit/ref; resolved and pinned by LY-007')
    ap.add_argument('--out', required=True, help='New directory outside both input trees')
    args = ap.parse_args(argv)
    try:
        result = run(args.lab, args.commit, args.out)
    except (OSError, ValueError, subprocess.SubprocessError, KeyError, TypeError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        return 2
    print(json.dumps({'checksPassed': result['checksPassed'], 'admission': result['admission'],
                      'commit': result['references']['commit']}, ensure_ascii=False))
    return 3


if __name__ == '__main__':
    sys.exit(main())
