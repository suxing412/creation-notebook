#!/usr/bin/env python3
"""LY-008 全部重算（按依赖顺序）。只读原仓库；所有输出写在本席位目录。
用法：python -I source/run_all.py <LY-008 目录> <LY-007 目录> <原仓库> <commit> <workpacks 目录>
"""
import os, shutil, subprocess, sys

ROOT, LY7, REPO, COMMIT, WP = (os.path.abspath(a) if i != 3 else a for i, a in enumerate(sys.argv[1:6]))
PY = [sys.executable, '-I']
COPY = os.path.join(ROOT, 'tmp', 'repo')
os.chdir(ROOT)


def run(*a):
    print('>>', ' '.join(a), flush=True)
    subprocess.run(list(a), check=True)


def export():
    if os.path.isdir(COPY):
        shutil.rmtree(COPY)
    os.makedirs(COPY)
    arc = subprocess.Popen(['git', '-C', REPO, '-c', 'core.autocrlf=false', 'archive', COMMIT], stdout=subprocess.PIPE)
    subprocess.run(['tar', '-x', '-C', COPY], stdin=arc.stdout, check=True)
    arc.wait()


export()
run(*PY, 'source/make_negatives.py', ROOT, LY7)
run(*PY, 'source/run_selftest.py', ROOT, LY7)
run(*PY, 'source/run_official.py', ROOT, REPO, COMMIT)
run(*PY, 'source/calibrate.py', ROOT, WP)
subprocess.run([*PY, 'source/ly_check.py', '--json', 'qa/privacy-docs-bce3211.json', 'privacy', 'tmp/repo/docs',
                '--archived', 'tmp/repo/docs/asset-spec/source-archive.json'])  # 已知会报 README.md 的 D:/ 路径（退出码 1）
run(*PY, 'source/draw_preview.py', ROOT)
run(*PY, 'source/checks.py', ROOT, LY7, REPO, COMMIT, WP)
run(*PY, 'source/make_manifest.py', ROOT)
