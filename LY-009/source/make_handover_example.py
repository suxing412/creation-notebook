"""Write LY-009's own 2026-11-05 handover as the filled example of templates/daily-handover.*.

python -I make_handover_example.py <workpacks root> <LY-009 dir> <lab repo> <baseline>
Products and sources carry real SHA256 of files on disk / committed bytes.
"""
import hashlib, json, os, subprocess, sys

root, me, lab, base = sys.argv[1:5]


def f(rel):
    p = os.path.join(me, rel)
    b = open(p, 'rb').read()
    return {'path': rel, 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest(), 'readBack': True}


def w(rel):
    p = os.path.join(root, rel)
    return hashlib.sha256(open(p, 'rb').read()).hexdigest() if os.path.isfile(p) else None


board = json.load(open(os.path.join(me, 'board', 'taskboard.v2.json'), encoding='utf-8'))
base_full = subprocess.run(['git', '--no-optional-locks', '-C', lab, 'rev-parse', base], capture_output=True,
                           text=True, check=True).stdout.strip()
prods = [f(p) for p in ['board/taskboard.v2.json', 'board/locks.json', 'board/pause-zone.json', 'board/ownership.json',
                        'board/dag.json', 'board/board.md', 'qa/parse-compare.json', 'qa/whitelist-scan.json']]
prods[0]['note'] = '100 席任务板 v2（提案，根 taskboard.json 未改）'
h = {
    'seat': 'LY-009', 'date': '2026-11-05', 'time': board['generatedAt'],
    'status': 'LY-009' and next(s['status'] for s in board['seats'] if s['id'] == 'LY-009'),
    'baseline': base_full,
    'baselineNote': f"lab origin/main 构建时为 {board['labOriginMainAtBuild'][:7]}，见暂停区 PZ-01",
    'dependencies': [{'seat': d, 'status': next(s['status'] for s in board['seats'] if s['id'] == d),
                      'statusSha256': w(f'{d}/status.json')} for d in ['LY-001', 'LY-006']],
    'products': prods,
    'sources': [
        {'what': '任务池原文', 'path': 'workpacks/TASKPOOL.md', 'sha256': w('TASKPOOL.md'), 'bytesKind': '本机检出字节'},
        {'what': '协调者解析的任务板', 'path': 'workpacks/taskboard.json', 'sha256': w('taskboard.json'),
         'bytesKind': '本机检出字节'},
        {'what': 'LY-006 所有权表', 'path': 'workpacks/LY-006/registry/ownership.json',
         'sha256': w('LY-006/registry/ownership.json'), 'bytesKind': '本机生成'},
        {'what': 'LY-001 城市节点表', 'path': 'workpacks/LY-001/qa/city-nodes.csv',
         'sha256': w('LY-001/qa/city-nodes.csv'), 'bytesKind': '本机生成'},
    ],
    'openItems': [
        {'item': '根 taskboard.json 9 处 text 串入下一节导语；是否以 v2 替换', 'to': '主协调者', 'pause': 'PZ-10'},
        {'item': '22 个源工程/超限 GLB 在 6 个席位目录里，未跟踪；native/ 规则冲突', 'to': '主协调者', 'pause': 'PZ-14'},
        {'item': '雍门接街、13院压缩的持锁人身份与 13院锁边界', 'to': '主协调者', 'pause': 'PZ-12'},
    ],
    'cityReadiness': '不涉及城市',
    'fiveClaims': {k: {'result': '不适用', 'evidence': '本席位只交任务板、锁、白名单与模板，不涉及模型、通行、入城、结构或史实'}
                   for k in ['模型能读取', '局部通行通过', '已入城', '真实结构安全', '历史复原成立']},
    'next': [{'direction': '交给', 'seat': 'LY-010', 'what': '任务板 v2、锁表、暂停区（LY-010 依赖 LY-009）'},
             {'direction': '等待', 'seat': 'LY-008', 'what': '交付后 G 才可能冻结（LY-010 还缺 008）'}],
    'writeCheck': {'ruleset': 'LY-009 whitelist v1', 'verdict': 'PASS', 'paths': 0},
    'locksRead': ['LOCK-YONG-ROAD', 'LOCK-13COURT', 'LOCK-SHARED-CITY', 'RIGHT-TASKBOARD'],
    'pausesRaised': [p['id'] for p in json.load(open(os.path.join(me, 'board', 'pause-zone.json'), encoding='utf-8'))['entries']],
    'pausesCleared': [],
    'evidence': [{'claim': '本席位没有新的史实或尺寸结论', 'class': 'C工程设计', 'ref': 'brief.md §证据分类'}],
}
# write check over LY-009's own files
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
import check_whitelist  # noqa: E402
mine = []
for dp, dns, fns in os.walk(me):
    for fn in fns:
        rel = os.path.relpath(os.path.join(dp, fn), root).replace(os.sep, '/')
        mine.append((rel, os.path.getsize(os.path.join(dp, fn))))
r = check_whitelist.check_paths('LY-009', mine)
h['writeCheck'] = {'ruleset': r['ruleset'], 'verdict': r['verdict'], 'paths': r['n'],
                   'failReasons': [x['path'] + ': ' + x['reason'] for x in r['results'] if not x['ok']]}
os.makedirs(os.path.join(me, 'templates', 'examples'), exist_ok=True)
with open(os.path.join(me, 'templates', 'examples', 'LY-009-2026-11-05.handover.json'), 'w', encoding='utf-8', newline='\n') as fo:
    json.dump(h, fo, ensure_ascii=False, indent=1)
print('example written; writeCheck', h['writeCheck']['verdict'], h['writeCheck']['paths'])
