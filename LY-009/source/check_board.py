"""LY-009 checker: re-validates the board, locks, pause zone, whitelist and handover template,
and proves every check can fail with injected negatives.

python -I check_board.py <workpacks root> <lab repo> <baseline> <LY-009 dir> <scratch dir> [<user original TASKPOOL copy>]

Read-only except: writes <LY-009 dir>/qa/checks.json and makes a throw-away git repo in <scratch dir>
(for the branch-name test). Never writes the lab repo or other seats.
"""
import copy, hashlib, json, os, re, shutil, subprocess, sys, datetime

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parse_taskpool  # noqa: E402
import check_whitelist as W  # noqa: E402
import check_handover as H  # noqa: E402

STATUSES = ['待输入', '可开工', '制作中', '待验收', '阻断', '复用完成', '交付完成']
DONE = {'交付完成', '复用完成'}
CRLF, LF = bytes([13, 10]), bytes([10])


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def git(repo, *a, binary=False):
    r = subprocess.run(['git', '--no-optional-locks', '-C', repo, *a], capture_output=True, check=True)
    return r.stdout if binary else r.stdout.decode('utf-8')


# ------------------------------------------------------------------ validators (used on real + injected data)
def v_ids(board):
    ids = [s['id'] for s in board['seats']]
    e = []
    if len(ids) != 100:
        e.append(f'{len(ids)} seats, expected 100')
    if len(set(ids)) != len(ids):
        e.append('duplicate ids: ' + ','.join(sorted({i for i in ids if ids.count(i) > 1})))
    if sorted(set(ids)) != [f'LY-{i:03d}' for i in range(1, 101)]:
        e.append('ids are not exactly LY-001..LY-100')
    return e


def v_dag(board, expect_levels=15):
    deps = {s['id']: s['deps'] for s in board['seats']}
    e = [f'{i} -> unknown {d}' for i, ds in deps.items() for d in ds if d not in deps]
    state, level = {}, {}

    def visit(n, stack):
        if state.get(n) == 1:
            e.append('cycle: ' + ' -> '.join(stack + [n]))
            return 0
        if state.get(n) == 2:
            return level[n]
        state[n] = 1
        lv = 1 + max([visit(d, stack + [n]) for d in deps[n] if d in deps] or [0])
        state[n] = 2
        level[n] = lv
        return lv

    for n in sorted(deps):
        if state.get(n) != 2:
            visit(n, [])
    if not any(x.startswith('cycle') for x in e):
        mx = max(level.values())
        if mx != expect_levels:
            e.append(f'longest chain {mx} levels, stated {expect_levels}')
        bad = [s['id'] for s in board['seats'] if s['level'] != level[s['id']]]
        if bad:
            e.append(f'board level field disagrees for {bad[:5]}')
    return e


def v_status(board, root):
    e = []
    sd = {s['id']: s for s in board['seats']}
    for s in board['seats']:
        if s['status'] not in STATUSES:
            e.append(f"{s['id']}: status {s['status']!r} not in vocabulary")
            continue
        sp = os.path.join(root, s['id'], 'status.json')
        if s['status'] in DONE | {'阻断', '待验收'}:
            if not os.path.isfile(sp):
                e.append(f"{s['id']}: {s['status']} without status.json")
                continue
            st = json.load(open(sp, encoding='utf-8'))
            miss = [p for p in st.get('deliverables', []) if not os.path.exists(os.path.join(root, s['id'], p))]
            if s['status'] in DONE and miss:
                e.append(f"{s['id']}: {s['status']} but deliverables missing {miss[:3]}")
            want = {'待验': '待验收'}.get(st.get('status'), st.get('status'))
            if want != s['status'] and not (want in DONE and miss and s['status'] == '待验收'):
                e.append(f"{s['id']}: board {s['status']} vs status.json {st.get('status')}")
        elif os.path.isfile(sp):
            e.append(f"{s['id']}: has status.json but board says {s['status']}")
        if s['status'] == '可开工':
            und = [d for d in s['deps'] if sd[d]['status'] not in DONE]
            if und:
                e.append(f"{s['id']}: 可开工 with unfinished deps {und}")
        if s['status'] == '待输入':
            if all(sd[d]['status'] in DONE for d in s['deps']):
                e.append(f"{s['id']}: 待输入 but all deps done")
    return e


def v_locks(locks, pool_text, lab, base, protect_lines, intro_keys, recompute=True):
    e = []
    for L in locks:
        if not L.get('holder'):
            e.append(f"{L['id']}: no holder")
        if L['poolQuote'] not in pool_text:
            e.append(f"{L['id']}: poolQuote not in TASKPOOL.md")
        for pat, m in L.get('patternMatches', {}).items():
            if m['baseline'] == 0 and not m.get('expectedOnlyAfterBaseline'):
                e.append(f"{L['id']}: pattern {pat} matches nothing at baseline")
        for n, c in L.get('cityNodesCheck', {}).items():
            if not c['inBaselineCityData']:
                e.append(f"{L['id']}: city node {n} not in baseline city-data")
        for ef in L.get('extFiles', []):
            if not ef.get('match'):
                e.append(f"{L['id']}: ext file {ef['path']} sha mismatch")
        if recompute and isinstance(L['files'], list):
            for f in L['files']:
                b = git(lab, 'show', f"{base}:{f['path']}", binary=True)
                if hashlib.sha256(b).hexdigest() != f['sha256'] or len(b) != f['bytes']:
                    e.append(f"{L['id']}: sha/bytes mismatch {f['path']}")
    # every protect-list bullet covered by a lock quote
    quotes = [L['poolQuote'] for L in locks]
    for ln in protect_lines:
        body = ln[2:].strip()
        if not any(q in body or body in q for q in quotes):
            e.append(f'protect bullet without lock: {body[:40]}')
    for k in intro_keys:
        if not any(k in L['name'] for L in locks):
            e.append(f'section-intro exclusion without lock: {k}')
    g = [L for L in locks if L['id'] == 'LOCK-12GATES']
    if not g or not g[0].get('gateCardCountOk'):
        e.append('LOCK-12GATES does not resolve to exactly 12 gate cards')
    return e


def v_rights(locks, own):
    e = []
    by = {L['id']: L for L in locks}
    if by.get('RIGHT-PUBLISH', {}).get('holder') != '主协调者':
        e.append('RIGHT-PUBLISH holder is not 主协调者')
    if by.get('RIGHT-CITY-WRITE', {}).get('holder') != 'LY-100':
        e.append('RIGHT-CITY-WRITE holder is not LY-100')
    for sid, o in own['seats'].items():
        if o['publish'] != 'none (coordinator only)':
            e.append(f'{sid}: publish right delegated')
        if sid != 'LY-100' and (o['labWrite'] != 'none' or o['cityWrite'] != 'proposal only'):
            e.append(f'{sid}: lab/city write delegated')
        if o['allow'] != [f'{sid}/**']:
            e.append(f'{sid}: whitelist is not exactly its own dir')
    return e


def v_pauses(pz, ids):
    e = []
    for P in pz['entries']:
        if P['effect'] not in ('blocks-merge', 'blocks-city', 'blocks-start', 'advisory'):
            e.append(f"{P['id']}: bad effect")
        if not P.get('decider') or not P.get('unblock'):
            e.append(f"{P['id']}: missing decider/unblock")
        for s in P['seats']:
            if s not in ids:
                e.append(f"{P['id']}: unknown seat {s}")
        for src in P['sources']:
            if not src.get('found'):
                e.append(f"{P['id']}: source quote not found in {src.get('file') or src.get('lab-git')}")
    return e


# ------------------------------------------------------------------ main
def main():
    root, lab, base, me, scratch = sys.argv[1:6]
    user_copy = sys.argv[6] if len(sys.argv) > 6 else None
    lab_status_before = git(lab, 'status', '--porcelain=v1', '--untracked-files=no')
    lab_head_before = git(lab, 'rev-parse', 'HEAD').strip()
    base_full = git(lab, 'rev-parse', base).strip()
    pool_path = os.path.join(root, 'TASKPOOL.md')
    pool_text = open(pool_path, encoding='utf-8').read()
    board = json.load(open(os.path.join(me, 'board', 'taskboard.v2.json'), encoding='utf-8'))
    locks = json.load(open(os.path.join(me, 'board', 'locks.json'), encoding='utf-8'))['locks']
    pz = json.load(open(os.path.join(me, 'board', 'pause-zone.json'), encoding='utf-8'))
    own = json.load(open(os.path.join(me, 'board', 'ownership.json'), encoding='utf-8'))
    tb = json.load(open(os.path.join(root, 'taskboard.json'), encoding='utf-8'))
    parsed = parse_taskpool.parse(pool_path)
    lines = pool_text.split('\n')
    i0 = lines.index('**不得抢占或重做：**')
    protect = []
    for ln in lines[i0 + 1:]:
        if not ln.startswith('- '):
            break
        protect.append(ln)
    intro_keys = ['雍门接街', '13院', 'v2.1', 'v2.2', '196米', '31组']
    checks = []

    def add(cid, name, errs, evidence, negatives=None):
        neg_ok = all(n['detected'] for n in (negatives or []))
        checks.append({'id': cid, 'name': name, 'result': 'PASS' if not errs and neg_ok else 'FAIL',
                       'errors': errs, 'evidence': evidence, 'negatives': negatives or []})

    def neg(name, errs):
        return {'injection': name, 'detected': bool(errs), 'errors': errs[:3]}

    # C1 parse fidelity
    ps = {s['id']: s for s in parsed['seats']}
    ts = {s['id']: s for s in tb['seats']}
    same_meta = [i for i in ps if all(ps[i][k] == ts[i][k] for k in ['title', 'type', 'deps', 'usesG'])]
    same_text = [i for i in ps if ps[i]['text'] == ts[i]['text']]
    bleed = sorted(set(ps) - set(same_text))
    sec_heads = {f"## {s['range'][0]:02d}—{s['range'][1]:02d}｜{s['title']}": s['intro'] for s in parsed['sections']}
    bleed_ok = all(any(ts[i]['text'] == ps[i]['text'] + f'\n\n{h}\n\n{intro}' for h, intro in sec_heads.items()) for i in bleed)
    v2_text_ok = all(s['text'] == ps[s['id']]['text'] for s in board['seats'])
    v2_meta_ok = all(s['deps'] == ps[s['id']]['deps'] and s['type'] == ps[s['id']]['type'] for s in board['seats'])
    errs = []
    if len(same_meta) != 100:
        errs.append(f'title/type/deps/usesG identical only for {len(same_meta)}')
    if not bleed_ok:
        errs.append('some text differences are not pure next-section bleed')
    if not (v2_text_ok and v2_meta_ok):
        errs.append('v2 board deviates from original text/deps')
    ev = {'TASKPOOL.md': parsed['sha256'], 'taskboard.json worktree': sha(os.path.join(root, 'taskboard.json')),
          'metaIdentical': len(same_meta), 'textIdentical': len(same_text), 'textBleed': bleed,
          'v2TextIdenticalToOriginal': v2_text_ok}
    if user_copy and os.path.isfile(user_copy):
        ev['userOriginalSha256'] = sha(user_copy)
        ev['userOriginalIdentical'] = ev['userOriginalSha256'] == parsed['sha256']
        if not ev['userOriginalIdentical']:
            errs.append('TASKPOOL.md differs from the user-supplied original')
    bad = copy.deepcopy(tb)
    bad['seats'][20]['deps'] = bad['seats'][20]['deps'][:-1]
    neg1 = [x for x in [bad] if any(ps[s['id']]['deps'] != s['deps'] for s in x['seats'])]
    add('C1', '任务板解析与原文一致（标题/类型/依赖逐席、text 逐字）', errs, ev,
        [neg('taskboard 删去 LY-021 一个依赖', ['deps differ'] if neg1 else [])])

    # C2 ids
    nb = copy.deepcopy(board); nb['seats'][5]['id'] = 'LY-005'
    nb2 = copy.deepcopy(board); nb2['seats'].pop()
    add('C2', '100 个 ID 不重复且恰为 LY-001…100', v_ids(board), {'n': len(board['seats'])},
        [neg('把 LY-006 改成重复的 LY-005', v_ids(nb)), neg('删掉 LY-100', v_ids(nb2))])

    # C3 DAG
    nc = copy.deepcopy(board); nc['seats'][0]['deps'] = ['LY-100']
    nu = copy.deepcopy(board); nu['seats'][30]['deps'] = nu['seats'][30]['deps'] + ['LY-123']
    nl = copy.deepcopy(board); nl['seats'][99]['deps'] = list(board['G']['members'])
    pos = {x: i for i, x in enumerate(tb['topo'])}
    topo_bad = [(s['id'], d) for s in board['seats'] for d in s['deps'] if pos[d] >= pos[s['id']]]
    g_self = [s['id'] for s in board['seats'] if s['id'] in board['G']['members'] and s['usesG']]
    e3 = v_dag(board) + ([f'taskboard.topo violates {topo_bad[:3]}'] if topo_bad else []) + \
        ([f'G members using G: {g_self}'] if g_self else [])
    add('C3', '依赖无环、无未知依赖、最长链 15 层、根 taskboard.topo 合法、G 成员不引用 G',
        e3, {'edges': board['dag']['edges'], 'longest': board['dag']['longestChainLevels'],
             'oneLongestChain': board['dag']['oneLongestChain']},
        [neg('LY-001 依赖 LY-100（造环）', v_dag(nc)), neg('LY-031 依赖不存在的 LY-123', v_dag(nu)),
         neg('LY-100 只留 G 依赖（最长链变短）', v_dag(nl))])

    # C4 type counts vs stated
    tc = board['typeCounts']
    e4 = [] if tc == board['typeCountsStated'] else [f'type counts {tc}']
    if tc['补件/修订'] + tc['复用装配'] != 77:
        e4.append('46+31 != 77')
    add('C4', '类型计数与原文 46/31/13/9/1 一致（77 项产出模型或装配，23 项其他）', e4, tc)

    # C5 status
    ns = copy.deepcopy(board); ns['seats'][50]['status'] = '完成'
    nr = copy.deepcopy(board); nr['seats'][60]['status'] = '可开工'
    nd = copy.deepcopy(board); nd['seats'][40]['status'] = '交付完成'
    add('C5', '状态取自各席位 status.json 或依赖推导，词表 7 项，完成必有交付文件',
        v_status(board, root), {'counts': board['counts'], 'G': board['G']},
        [neg('状态写成词表外的「完成」', v_status(ns, root)),
         neg('LY-061 依赖未齐却标可开工', v_status(nr, root)),
         neg('LY-041 无 status.json 却标交付完成', v_status(nd, root))])

    # C6 locks
    e6 = v_locks(locks, pool_text, lab, base_full, protect, intro_keys, recompute=True)
    nlk = copy.deepcopy(locks); nlk[0]['holder'] = ''
    nlq = copy.deepcopy(locks); nlq[2]['poolQuote'] = '十二门本体可以重做'
    nlp = copy.deepcopy(locks); nlp[4]['patternMatches']['docs/library/models/m-luoyang-market-frontage-v9/**'] = {'baseline': 0, 'head': 0}
    nlm = [L for L in copy.deepcopy(locks) if L['id'] != 'LOCK-13COURT']
    nls = copy.deepcopy(locks); nls[5]['files'][0]['sha256'] = '0' * 64
    nfiles = sum(len(L['files']) for L in locks if isinstance(L['files'], list))
    add('C6', '排除项都有锁：保护清单逐条、各节导语的排除事项；锁定文件 SHA 由 git 提交字节逐件重算',
        e6, {'locks': len(locks), 'lockedFilesHashed': nfiles, 'protectBullets': len(protect),
             'introKeys': intro_keys},
        [neg('雍门锁去掉持锁人', v_locks(nlk, pool_text, lab, base_full, protect, intro_keys, False)),
         neg('篡改十二门锁的原文引句', v_locks(nlq, pool_text, lab, base_full, protect, intro_keys, False)),
         neg('加一个匹配不到文件的锁路径', v_locks(nlp, pool_text, lab, base_full, protect, intro_keys, False)),
         neg('删掉 13院锁', v_locks(nlm, pool_text, lab, base_full, protect, intro_keys, False)),
         neg('篡改武库B锁文件 SHA', v_locks(nls, pool_text, lab, base_full, protect, intro_keys, True)[-1:] if
             v_locks(nls, pool_text, lab, base_full, protect, intro_keys, True) else [])])

    # C7 rights
    no = copy.deepcopy(own); no['seats']['LY-030']['cityWrite'] = 'yes'
    np_ = copy.deepcopy(own); np_['seats']['LY-100']['publish'] = 'yes'
    nw = copy.deepcopy(own); nw['seats']['LY-021']['allow'] = ['LY-021/**', 'LY-022/**']
    add('C7', '发布账户与城市写入权不下放；每席白名单只含自己目录', v_rights(locks, own),
        {'seats': len(own['seats'])},
        [neg('LY-030 获得城市写入', v_rights(locks, no)), neg('LY-100 获得发布账户', v_rights(locks, np_)),
         neg('LY-021 白名单含 LY-022', v_rights(locks, nw))])

    # C8 whitelist checker + current tree
    pos_cases = [('LY-009', 'LY-009/board/taskboard.v2.json', 1000), ('LY-021', 'LY-021/models/step-LOD0.glb', 14_999_999),
                 ('LY-100', 'LY-100/batches/b01/manifest.json', 10)]
    neg_cases = [('LY-021', 'LY-022/brief.md', 10, 'R1'), ('LY-021', 'taskboard.json', 10, 'R2'),
                 ('LY-021', 'TASKPOOL.md', 10, 'R2'), ('LY-033', 'LY-033/native/door.blend', 10, 'R3'),
                 ('LY-033', 'LY-033/source/pack.zip', 10, 'R3'), ('LY-040', 'LY-040/models/x-LOD0.glb', 15_000_001, 'R4'),
                 ('LY-011', 'LY-011/../LY-012/x.json', 10, 'R1'), ('LY-011', 'D:/GitHub/creation-notebook-lab/docs/cities/luoyang/city-data.mjs', 10, 'R7'),
                 ('LY-011', '/docs/x', 10, 'R7'), ('LY-011', 'ly-011/brief.md', 10, 'R1'), ('LY-100', 'LY-099/status.json', 10, 'R1'),
                 ('LY-050', 'LY-050/qa/huge.bin', 101 * 1024 * 1024, 'R5'), ('LY-011', 'LY-011\\brief.md', 10, 'R1')]
    e8 = []
    for seat, p, size in pos_cases:
        r = W.classify(p, seat, size)
        if not r['ok']:
            e8.append(f'positive case failed: {seat} {p}: {r["reason"]}')
    negs = []
    for seat, p, size, rule in neg_cases:
        r = W.classify(p, seat, size)
        negs.append({'injection': f'{seat} 写 {p} ({size} B)', 'detected': (not r['ok']) and r['rule'] == rule,
                     'errors': [f"{r['rule']}: {r['reason']}"]})
    scan = json.load(open(os.path.join(me, 'qa', 'whitelist-scan.json'), encoding='utf-8'))
    wt = scan['workingTreeChanges']
    # content comparison (git diff --quiet gives false positives on stat-dirty CRLF files without an index refresh)
    coord_changed = [p for p in ['TASKPOOL.md', 'taskboard.json', 'README.md']
                     if open(os.path.join(root, p), 'rb').read().replace(CRLF, LF) != git(root, 'show', f'HEAD:{p}', binary=True)]
    coord_diff = 1 if coord_changed else 0
    if wt['outsideWhitelist']:
        e8.append(f"{len(wt['outsideWhitelist'])} changed paths outside every whitelist")
    if coord_diff != 0:
        e8.append(f'coordinator root files changed in working tree: {coord_changed}')
    add('C8', '写入白名单：检查器正反例；共享分支当前改动全部落在某个席位目录内，根文件未改',
        e8, {'scanFile': 'qa/whitelist-scan.json', 'scanSha256': sha(os.path.join(me, 'qa', 'whitelist-scan.json')),
             'filesScanned': scan['filesScanned'], 'changedPaths': wt['n'], 'seatsWithChanges': len(wt['seatsWithChanges']),
             'contentViolationsInsideSeatDirs': len(scan['violations']),
             'contentViolationsNotIgnored': scan['violationsNotIgnored'],
             'rootFilesContentChanged': coord_changed,
             'otherRootFilesChangedOrAdded': wt['coordinatorFilesChanged'],
             'rootFileNote': '根目录 .gitignore 为基线后新增（未跟踪），不是 LY-009 所写；按规则只有协调者可写根文件，作者未核实',
             'note': '目录内 R3/R4 违规不算越界写入，记在暂停区 PZ-14，由协调者裁定'}, negs)

    # C9 branch naming D/F conflict
    import stat, tempfile
    tmp = tempfile.mkdtemp(prefix='ly009-refs-', dir=scratch)

    def _rm(func, path, _exc):
        os.chmod(path, stat.S_IWRITE)
        func(path)
    run = lambda *a: subprocess.run(['git', '-C', tmp, *a], capture_output=True, text=True)  # noqa: E731
    run('init', '-q', '-b', 'main')
    run('-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', 'init')
    run('branch', 'workpacks')
    r1 = run('branch', 'workpacks/LY-011')
    r2 = run('branch', 'wp/LY-011')
    shutil.rmtree(tmp, onerror=_rm)
    e9 = []
    if r1.returncode == 0:
        e9.append('workpacks/LY-011 unexpectedly creatable')
    if r2.returncode != 0:
        e9.append('wp/LY-011 not creatable')
    add('C9', '分支命名：workpacks/LY-### 与既有 workpacks 分支冲突，采用 wp/LY-###（临时仓库实测）', e9,
        {'workpacks/LY-011': r1.stderr.strip()[:200], 'wp/LY-011 exit': r2.returncode,
         'liveBranches': git(root, 'branch', '--list', 'workpacks', 'wp/*').split()})

    # C10 pauses
    ids = {s['id'] for s in board['seats']}
    npz = copy.deepcopy(pz); npz['entries'][0]['sources'][0]['found'] = False
    npz2 = copy.deepcopy(pz); npz2['entries'][1]['seats'].append('LY-101')
    add('C10', '暂停区每条都有裁决人、解除条件，来源引句在源文件中重新找到', v_pauses(pz, ids),
        {'entries': len(pz['entries'])},
        [neg('来源引句找不到', v_pauses(npz, ids)), neg('登记不存在的席位 LY-101', v_pauses(npz2, ids))])

    # C11 handover template
    ex = os.path.join(me, 'templates', 'examples', 'LY-009-2026-11-05.handover.json')
    exj = json.load(open(ex, encoding='utf-8'))
    e11 = H.check(exj, root)
    hn = []
    for name, mut in [
        ('非 LY-100 声称已入城', lambda h: h['fiveClaims'].__setitem__('已入城', {'result': '做到', 'evidence': 'x', 'sha256': h['products'][0]['sha256']})),
        ('做到 无 SHA', lambda h: h['fiveClaims'].__setitem__('模型能读取', {'result': '做到', 'evidence': 'x'})),
        ('产物写到别席位', lambda h: h['products'].append({'path': '../LY-010/x.json', 'bytes': 1, 'sha256': '0' * 64, 'readBack': True})),
        ('产物是 .blend', lambda h: h['products'].append({'path': 'native/a.blend', 'bytes': 1, 'sha256': '0' * 64, 'readBack': True})),
        ('交付完成却无产物', lambda h: (h.__setitem__('status', '交付完成'), h.__setitem__('products', []))),
        ('状态写成词表外', lambda h: h.__setitem__('status', '差不多完成')),
        ('产物 SHA 与磁盘不符', lambda h: h['products'][0].__setitem__('sha256', 'f' * 64)),
        ('缺五项之一', lambda h: h['fiveClaims'].pop('真实结构安全')),
    ]:
        h = copy.deepcopy(exj)
        mut(h)
        hn.append(neg(name, H.check(h, root)))
    add('C11', '每日交接模板：样例通过 schema 与语义检查，8 个注入负例均被拒', e11,
        {'example': 'templates/examples/LY-009-2026-11-05.handover.json', 'exampleSha256': sha(ex)}, hn)

    # C12 lab read-only
    lab_status_after = git(lab, 'status', '--porcelain=v1', '--untracked-files=no')
    lab_head_after = git(lab, 'rev-parse', 'HEAD').strip()
    e12 = []
    if lab_head_after != lab_head_before:
        e12.append('lab HEAD moved')
    if lab_status_after != lab_status_before:
        e12.append('lab tracked status changed during run')
    add('C12', 'lab 仓库只读：本次运行前后 HEAD 与已跟踪文件状态不变', e12,
        {'labHead': lab_head_after, 'trackedChanges': lab_status_after.splitlines()[:10]})

    out = {'seat': 'LY-009', 'generatedAt': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
           'baseline': base_full, 'labOriginMain': git(lab, 'rev-parse', 'origin/main').strip(),
           'inputs': {p: sha(os.path.join(me, p)) for p in ['board/taskboard.v2.json', 'board/locks.json',
                                                             'board/pause-zone.json', 'board/ownership.json',
                                                             'board/dag.json', 'qa/parse-compare.json',
                                                             'qa/whitelist-scan.json']},
           'tools': {p: sha(os.path.join(me, 'source', p)) for p in sorted(os.listdir(os.path.join(me, 'source'))) if p.endswith('.py')},
           'summary': {c['id']: c['result'] for c in checks},
           'negativesDetected': f"{sum(n['detected'] for c in checks for n in c['negatives'])}/{sum(len(c['negatives']) for c in checks)}",
           'checks': checks}
    with open(os.path.join(me, 'qa', 'checks.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps(out['summary']), out['negativesDetected'])
    for c in checks:
        if c['result'] != 'PASS':
            print(c['id'], c['errors'][:5], [n for n in c['negatives'] if not n['detected']])
    sys.exit(0 if all(c['result'] == 'PASS' for c in checks) else 1)


if __name__ == '__main__':
    main()
