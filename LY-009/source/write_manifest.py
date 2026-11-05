"""Write LY-009/inputs.json and LY-009/delivery-manifest.json (SHA256 of every file).

python -I write_manifest.py <workpacks root> [<lab repo>] [<user original TASKPOOL copy>]
"""
import hashlib, json, os, subprocess, sys, datetime

root = sys.argv[1]
lab = sys.argv[2] if len(sys.argv) > 2 else 'D:/GitHub/creation-notebook-lab'
orig = sys.argv[3] if len(sys.argv) > 3 else 'C:/Users/suxin/Downloads/东汉洛阳_100席位并行生产任务池.md'
me = os.path.join(root, 'LY-009')


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def ent(rel, base=root):
    p = os.path.join(base, rel)
    return {'path': rel, 'bytes': os.path.getsize(p), 'sha256': sha(p)}


def git(repo, *a):
    return subprocess.run(['git', '--no-optional-locks', '-C', repo, *a], capture_output=True, check=True).stdout


now = datetime.datetime.now().astimezone().isoformat(timespec='seconds')
tb_blob = git(root, 'show', 'HEAD:taskboard.json')
inputs = {
    'seat': 'LY-009', 'generatedAt': now,
    'baseline': {'lab': git(lab, 'rev-parse', 'bce3211').decode().strip(),
                 'labOriginMainAtManifest': git(lab, 'rev-parse', 'origin/main').decode().strip(),
                 'workpacksHead': git(root, 'rev-parse', 'HEAD').decode().strip()},
    'taskPool': {**ent('TASKPOOL.md'), 'userOriginal': {'path': orig, 'sha256': sha(orig) if os.path.isfile(orig) else None}},
    'taskboard': {**ent('taskboard.json'), 'commitBlobSha256': hashlib.sha256(tb_blob).hexdigest(),
                  'note': '工作树为 CRLF，提交 blob 为 LF，内容相同'},
    'prerequisites': [ent(p) for p in ['LY-001/status.json', 'LY-001/qa/city-nodes.csv', 'LY-001/qa/snapshot-ledger.json',
                                       'LY-006/status.json', 'LY-006/brief.md', 'LY-006/registry/ownership.json',
                                       'LY-006/registry/seats.json', 'LY-006/qa/chunks/northeast_C_access.glb']],
    'otherStatusRead': [ent(f'{s}/status.json') for s in ['LY-002', 'LY-003', 'LY-004', 'LY-005', 'LY-007']
                        if os.path.isfile(os.path.join(root, s, 'status.json'))],
    'labReadOnly': {'commands': ['git ls-tree -r', 'git cat-file --batch', 'git show <commit>:<path>', 'git diff --name-only',
                                 'git log', 'git status --porcelain (with --no-optional-locks)'],
                    'commitsRead': ['bce3211', 'f28d650', 'b70c495', 'cad338b']},
    'nativeSources': '不涉及（本席位不产模型）',
    'externalWeb': '未使用',
}
with open(os.path.join(me, 'inputs.json'), 'w', encoding='utf-8', newline='\n') as f:
    json.dump(inputs, f, ensure_ascii=False, indent=1)

CLASS = {'board': '任务板（提案，内部）', 'templates': '模板（内部）', 'source': '工具源码（内部）', 'qa': '检查记录（内部）',
         'preview': '示意图（PIL，非渲染）'}
files = []
for dp, dns, fns in os.walk(me):
    dns[:] = [d for d in dns if d != '__pycache__']
    for fn in sorted(fns):
        rel = os.path.relpath(os.path.join(dp, fn), me).replace(os.sep, '/')
        if rel == 'delivery-manifest.json':
            continue
        e = ent(rel, me)
        e['class'] = CLASS.get(rel.split('/')[0], '席位文档（内部）') if '/' in rel else '席位文档（内部）'
        files.append(e)
files.sort(key=lambda x: x['path'])
man = {
    'seat': 'LY-009', 'generatedAt': now,
    'publicFiles': [], 'publicNote': '本席位不产生公共 docs 文件；所有文件只供协调者与席位内部使用，城市/项目卡写入归 LY-100。',
    'sourceProjects': [], 'whitelist': ['LY-009/**'],
    'files': files, 'totalBytes': sum(f['bytes'] for f in files), 'fileCount': len(files),
    'dependsOn': {'LY-001': inputs['prerequisites'][0]['sha256'], 'LY-006': inputs['prerequisites'][3]['sha256']},
    'installOrder': [
        '1 协调者读 board/board.md 与 qa/checks.json，决定是否用 board/taskboard.v2.json 替换根 taskboard.json（RIGHT-TASKBOARD，只有协调者能做）',
        '2 协调者确认 locks.json 的持锁人（PZ-12）与 13院锁边界（PZ-13），在 locks_spec.py 写入后重跑 run_all.sh',
        '3 各席位每日按 templates/daily-handover.md/.schema.json 写交接，用 check_handover.py 与 check_whitelist.py 自检',
        '4 协调者每日按 templates/coordinator-daily.md 重跑 run_all.sh 与 board_diff.py',
        '5 LY-010 以本板 + 锁 + 暂停区为输入冻结首批方案与准入',
    ],
    'rerun': 'sh LY-009/source/run_all.sh D:/GitHub/creation-notebook-lab bce3211 <scratch> <user original>; python -I LY-009/source/write_manifest.py .',
}
with open(os.path.join(me, 'delivery-manifest.json'), 'w', encoding='utf-8', newline='\n') as f:
    json.dump(man, f, ensure_ascii=False, indent=1)
print('manifest', len(files), 'files', man['totalBytes'], 'bytes')
