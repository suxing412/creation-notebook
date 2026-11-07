#!/usr/bin/env python3
"""Portable stdlib regression tests. Synthetic Git fixtures are never historical evidence."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

WP = Path(__file__).resolve().parents[2]
NEAR = WP / 'LY-007/source/near_retention.py'
RUNNER = WP / 'LY-009/source/run_safety_checks.py'
WHITE = WP / 'LY-009/source/check_whitelist.py'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


sys.path.insert(0, str(WP / 'LY-004/source'))
phase = load('tested_phase', WP / 'LY-004/source/build.py')
sys.path.pop(0)
near = load('tested_near', NEAR)
white = load('tested_white', WHITE)


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True).stdout.strip()


def cli(script, *args, **kwargs):
    return subprocess.run([sys.executable, '-I', '-B', str(script), *map(str, args)],
                          capture_output=True, text=True, **kwargs)


class SafetyChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='luoyang-safety-')
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        git(self.repo, 'init', '-q')
        git(self.repo, 'config', 'user.name', 'Synthetic regression fixture')
        git(self.repo, 'config', 'user.email', 'fixture@example.invalid')
        self.model = b'synthetic model fixture, not an archaeology asset'
        self.write('docs/cities/luoyang/a.glb', self.model)
        self.records = [{'id': 'test', 'path': 'a.glb', 'sha256': hashlib.sha256(self.model).hexdigest()}]
        self.city()
        self.base = self.commit()

    def tearDown(self):
        self.temp.cleanup()

    def write(self, path, data):
        p = self.repo / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def city(self):
        self.write('docs/cities/luoyang/city-data.mjs',
                   ('const assetRecords = ' + json.dumps(self.records) + ';\n').encode())

    def commit(self):
        git(self.repo, 'add', '-A')
        git(self.repo, 'commit', '-qm', 'Synthetic fixture')
        return git(self.repo, 'rev-parse', 'HEAD').decode()

    def run_near(self, name='near', commit=None):
        return cli(NEAR, self.root / name, self.repo, commit or 'HEAD')

    def run_preflight(self, out=None, *args):
        return cli(RUNNER, '--lab', self.repo, '--commit', 'HEAD', '--out', out or self.root / 'result', *args)

    def test_phase_current_items(self):
        rows = [(x, phase.gate(x)) for x in phase.SD.GATE_ITEMS]
        self.assertEqual(len(rows), 21)
        self.assertFalse(any(x['request'] == 'install180' and r['admitted'] for x, r in rows))
        self.assertEqual([x['id'] for x, r in rows if r['admitted']], ['P16','P17','P18','P19','P20','P21'])

    def test_phase_exact_claim_is_not_trusted(self):
        row = dict(phase.SD.GATE_ITEMS[0], phase='EH', position='A-surveyed-with-control-points')
        self.assertFalse(phase.gate(row)['admitted'])

    def test_phase_forged_evidence(self):
        row = dict(phase.SD.GATE_ITEMS[0], verified=True)
        self.assertFalse(phase.gate(row)['admitted'])

    def test_phase_marker_mutation(self):
        row = dict(phase.SD.GATE_ITEMS[-1], item='unsupported new item')
        self.assertFalse(phase.gate(row)['admitted'])

    def test_phase_wrong_tuple(self):
        row = dict(phase.SD.GATE_ITEMS[0], phase='EH', position='A-surveyed-with-control-points')
        self.assertFalse(phase.gate(row, verified_installations=[row])['admitted'])

    def test_near_real_git_success(self):
        self.assertEqual(self.run_near().returncode, 0)

    def test_near_recursive_reference(self):
        self.records[0]['extra'] = {'list': [{'path': 'a.glb', 'sha256': hashlib.sha256(self.model).hexdigest()}]}
        self.city(); self.commit()
        self.assertEqual(self.run_near().returncode, 0)
        r = json.loads((self.root / 'near/qa/near-retention.json').read_text())
        self.assertEqual(r['summary']['city_refs'], 2)

    def test_near_missing_path(self):
        self.records[0].pop('path'); self.city(); self.commit()
        self.assertNotEqual(self.run_near().returncode, 0)

    def test_near_missing_optional_container(self):
        self.records[0]['sourceAsset'] = {}; self.city(); self.commit()
        self.assertNotEqual(self.run_near().returncode, 0)

    def test_near_declared_hash_mismatch(self):
        self.records[0]['sha256'] = '0' * 64; self.city(); self.commit()
        self.assertEqual(self.run_near().returncode, 1)

    def test_near_blob_replace_ignored(self):
        original = git(self.repo, 'rev-parse', 'HEAD:docs/cities/luoyang/a.glb').decode()
        self.write('replacement', b'replacement model')
        replacement = git(self.repo, 'hash-object', '-w', 'replacement').decode()
        git(self.repo, 'replace', original, replacement)
        self.assertEqual(self.run_near().returncode, 0)
        r = json.loads((self.root / 'near/qa/near-retention.json').read_text())
        self.assertEqual(r['city'][0]['actual_sha256'], hashlib.sha256(self.model).hexdigest())

    def test_near_special_lod_paths(self):
        for n, directory in enumerate(('汉字', 'tab\tdir', 'line\ndir')):
            with self.subTest(directory=directory):
                for tier in (0, 1):
                    self.write('docs/cities/luoyang/' + directory + '/sample-LOD' + str(tier) + '.glb', b'identical synthetic tier')
                self.commit()
                self.assertEqual(self.run_near('near-' + str(n)).returncode, 1)

    def test_near_symlink_model_rejected(self):
        (self.repo / 'docs/cities/luoyang/a.glb').unlink()
        (self.repo / 'docs/cities/luoyang/a.glb').symlink_to('other.glb')
        self.records[0]['sha256'] = hashlib.sha256(b'other.glb').hexdigest()
        self.city(); self.commit()
        self.assertNotEqual(self.run_near().returncode, 0)

    def test_near_output_no_overwrite(self):
        self.assertEqual(self.run_near().returncode, 0)
        p = self.root / 'near/qa/near-retention.json'; before = p.read_bytes()
        self.assertNotEqual(self.run_near().returncode, 0)
        self.assertEqual(p.read_bytes(), before)

    def test_near_output_symlink_rejected(self):
        (self.root / 'other').mkdir(); (self.root / 'near').symlink_to(self.root / 'other', target_is_directory=True)
        self.assertNotEqual(self.run_near().returncode, 0)
        self.assertEqual(list((self.root / 'other').iterdir()), [])

    def test_near_output_hardlink_not_overwritten(self):
        p = self.root / 'near/qa/near-retention.json'; p.parent.mkdir(parents=True)
        target = self.root / 'precious'; target.write_text('preserve')
        os.link(target, p)
        self.assertNotEqual(self.run_near().returncode, 0)
        self.assertEqual(target.read_text(), 'preserve')

    def test_whitelist_wrong_seat(self):
        self.assertEqual(white.check_paths('LY-011', [('LY-007/source/a.py', 12)])['verdict'], 'FAIL')

    def test_whitelist_archive(self):
        self.assertEqual(white.check_paths('LY-009', [('LY-009/source/a.zip', 12)])['verdict'], 'FAIL')

    def test_whitelist_rename_checks_source(self):
        self.write('LY-008/a.txt', b'source'); a = self.commit()
        (self.repo / 'LY-009').mkdir(); (self.repo / 'LY-008/a.txt').rename(self.repo / 'LY-009/a.txt'); b = self.commit()
        result = white.check_paths('LY-009', white.git_items(str(self.repo), a, b))
        self.assertEqual(result['verdict'], 'FAIL')
        self.assertEqual(result['n'], 2)

    def test_whitelist_committed_size(self):
        self.write('LY-009/model.glb', b'x' * 15000001); head = self.commit()
        (self.repo / 'LY-009/model.glb').write_bytes(b'small working tree')
        result = white.check_paths('LY-009', white.git_items(str(self.repo), self.base, head))
        self.assertEqual(result['verdict'], 'FAIL')
        self.assertEqual(result['results'][0]['rule'], 'R4')

    def test_preflight_remains_blocked(self):
        result = self.run_preflight()
        self.assertEqual(result.returncode, 3, result.stderr)
        r = json.loads((self.root / 'result/summary.json').read_text())
        self.assertTrue(r['checksPassed']); self.assertEqual(r['admission'], 'blocked')
        self.assertEqual(r['installationCount'], 0); self.assertEqual(r['researchMarkerCount'], 6)
        self.assertFalse(r['G_frozen']); self.assertFalse(r['productionAuthorized'])
        self.assertEqual(r['acceptedSeats'], [])

    def test_preflight_failed_reference_no_output(self):
        self.records[0]['sha256'] = 'f' * 64; self.city(); self.commit()
        self.assertEqual(self.run_preflight().returncode, 2)
        self.assertFalse((self.root / 'result').exists())

    def test_preflight_existing_output(self):
        out = self.root / 'result'; out.mkdir(); (out / 'preserve').write_text('preserve')
        self.assertEqual(self.run_preflight().returncode, 2)
        self.assertEqual((out / 'preserve').read_text(), 'preserve')

    def test_preflight_inside_input(self):
        self.assertEqual(self.run_preflight(self.repo / 'unsafe').returncode, 2)
        self.assertFalse((self.repo / 'unsafe').exists())

    def test_preflight_symlink_ancestor(self):
        (self.root / 'alias').symlink_to(self.repo, target_is_directory=True)
        self.assertEqual(self.run_preflight(self.root / 'alias/unsafe').returncode, 2)
        self.assertFalse((self.repo / 'unsafe').exists())

    def test_preflight_no_approval_flag(self):
        self.assertEqual(self.run_preflight(None, '--approve').returncode, 2)
        self.assertFalse((self.root / 'result').exists())

    def test_legacy_entry_is_quarantined(self):
        r = cli(WP / 'LY-010/source/build_decision.py')
        self.assertNotEqual(r.returncode, 0)
        self.assertTrue(r.stderr.startswith('BLOCKED: unfinished legacy builder is quarantined;'), r.stderr)

    def test_run_all_stops_on_whitelist_failure(self):
        scripts = self.root / 'bin'; scripts.mkdir(); log = self.root / 'calls'
        fake = scripts / 'python'
        fake.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$TEST_LOG"\ncase "$*" in *check_whitelist.py*) exit 7;; esac\nexit 0\n')
        fake.chmod(0o755)
        env = dict(os.environ, PATH=str(scripts) + os.pathsep + os.environ['PATH'], TEST_LOG=str(log))
        r = subprocess.run(['sh', str(WP / 'LY-009/source/run_all.sh'), 'lab', 'base', 'scratch'],
                           cwd=self.root, env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 7)
        self.assertEqual(len(log.read_text().splitlines()), 2)
        self.assertNotIn('build_board.py', log.read_text())


if __name__ == '__main__':
    unittest.main(verbosity=2)
