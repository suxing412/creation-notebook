"""LY-009 board builder.

python -I build_board.py <workpacks root> <lab repo> <baseline commit> <out dir (LY-009)>

Reads (read-only): TASKPOOL.md, taskboard.json, every LY-###/status.json and prep/prep-status.json,
LY-001/qa/city-nodes.csv, LY-006/registry/ownership.json, the lab repo via read-only git
(ls-tree / cat-file / diff / show). Writes only into <out dir>/board and <out dir>/qa.
"""
import csv, fnmatch, hashlib, json, os, re, subprocess, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import parse_taskpool  # noqa: E402
import check_whitelist  # noqa: E402
from locks_spec import LOCKS, COMMON_ALLOWED, COMMON_FORBIDDEN  # noqa: E402
from pause_spec import PAUSES  # noqa: E402

STATUSES = ['待输入', '可开工', '制作中', '待验收', '阻断', '复用完成', '交付完成']
SEAT_STATUS_MAP = {'交付完成': '交付完成', '复用完成': '复用完成', '阻断': '阻断', '待验': '待验收'}
DONE = {'交付完成', '复用完成'}
LANES = {'补件/修订': '模型补件', '复用装配': '复用装配', '考据/契约': '资料契约', '独立验收': '独立验收',
         '唯一整合': '唯一整合'}
STATED_COUNTS = {'补件/修订': 46, '复用装配': 31, '考据/契约': 13, '独立验收': 9, '唯一整合': 1}


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def git(repo, *args, binary=False, inp=None):
    r = subprocess.run(['git', '--no-optional-locks', '-C', repo, *args], capture_output=True, input=inp, check=True)
    return r.stdout if binary else r.stdout.decode('utf-8')


def blob_sha256s(repo, commit, paths):
    """SHA256 + size of committed bytes for many paths via one cat-file --batch."""
    if not paths:
        return {}
    req = ''.join(f'{commit}:{p}\n' for p in paths).encode('utf-8')
    out = git(repo, 'cat-file', '--batch', binary=True, inp=req)
    res, i = {}, 0
    for p in paths:
        nl = out.index(b'\n', i)
        hdr = out[i:nl].decode()
        _, typ, size = hdr.split(' ')
        size = int(size)
        data = out[nl + 1:nl + 1 + size]
        res[p] = {'bytes': size, 'sha256': hashlib.sha256(data).hexdigest()}
        i = nl + 1 + size + 1
    return res


def glob_match(path, pat):
    """'dir/**' matches everything below dir (dir may itself contain * ?);
    other patterns match one path with the same depth."""
    if pat.endswith('/**'):
        prefix = pat[:-3]
        depth = prefix.count('/') + 1
        parts = path.split('/')
        return len(parts) > depth and fnmatch.fnmatchcase('/'.join(parts[:depth]), prefix)
    return fnmatch.fnmatchcase(path, pat) and path.count('/') == pat.count('/')


# ---------------------------------------------------------------- parse & compare
def compare(parsed, tb):
    ts = {s['id']: s for s in tb['seats']}
    ps = {s['id']: s for s in parsed['seats']}
    secs = parsed['sections']
    rows = []
    for sid, s in ps.items():
        o = ts.get(sid)
        if o is None:
            rows.append({'id': sid, 'field': '*', 'kind': 'missing-in-taskboard'})
            continue
        for k in ['title', 'type', 'deps', 'usesG']:
            if o.get(k) != s.get(k):
                rows.append({'id': sid, 'field': k, 'kind': 'mismatch', 'taskboard': o.get(k), 'original': s.get(k)})
        if o.get('text') != s['text']:
            kind = 'mismatch'
            extra = o['text'][len(s['text']):] if o['text'].startswith(s['text']) else None
            if extra is not None:
                for sec in secs:
                    head = f"## {sec['range'][0]:02d}—{sec['range'][1]:02d}｜{sec['title']}"
                    if extra == f"\n\n{head}\n\n{sec['intro']}":
                        kind = 'text-bleeds-next-section'
                        extra = head
            rows.append({'id': sid, 'field': 'text', 'kind': kind, 'appendedInTaskboard': extra})
    for sid in ts:
        if sid not in ps:
            rows.append({'id': sid, 'field': '*', 'kind': 'missing-in-original'})
    # topo order of the taskboard respects deps?
    pos = {x: i for i, x in enumerate(tb['topo'])}
    topo_bad = [(s['id'], d) for s in parsed['seats'] for d in s['deps'] if pos.get(d, 1e9) >= pos.get(s['id'], -1)]
    return {
        'original': {'file': 'TASKPOOL.md', 'sha256': parsed['sha256'], 'bytes': parsed['bytes'], 'crlf': parsed['crlf']},
        'seatsOriginal': len(ps), 'seatsTaskboard': len(ts),
        'fieldsCompared': ['title', 'type', 'deps (G expanded)', 'usesG', 'text'],
        'differences': rows,
        'summary': {
            'title/type/deps/usesG identical for': sum(
                1 for sid in ps if sid in ts and all(ts[sid].get(k) == ps[sid].get(k) for k in ['title', 'type', 'deps', 'usesG'])),
            'text identical for': sum(1 for sid in ps if sid in ts and ts[sid].get('text') == ps[sid]['text']),
            'text-bleeds-next-section': [r['id'] for r in rows if r['kind'] == 'text-bleeds-next-section'],
            'other mismatches': [r for r in rows if r['kind'] not in ('text-bleeds-next-section',)],
        },
        'taskboardTopoOrderViolations': topo_bad,
    }


# ---------------------------------------------------------------- DAG
def dag(seats):
    ids = [s['id'] for s in seats]
    deps = {s['id']: s['deps'] for s in seats}
    unknown = [(i, d) for i in ids for d in deps[i] if d not in deps]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    # Kahn
    indeg = {i: 0 for i in ids}
    for i in ids:
        for d in deps[i]:
            if d in indeg:
                indeg[i] += 1
    rdeps = {i: [] for i in ids}
    for i in ids:
        for d in deps[i]:
            if d in rdeps:
                rdeps[d].append(i)
    q = sorted(i for i in ids if indeg[i] == 0)
    order = []
    while q:
        n = q.pop(0)
        order.append(n)
        for m in sorted(rdeps[n]):
            indeg[m] -= 1
            if indeg[m] == 0:
                q.append(m)
        q.sort()
    cyclic = sorted(i for i in ids if i not in order)
    level, via = {}, {}
    for n in order:
        ds = [d for d in deps[n] if d in level]
        if ds:
            best = max(ds, key=lambda d: (level[d], d))
            level[n], via[n] = level[best] + 1, best
        else:
            level[n], via[n] = 1, None
    longest = max(level.values()) if level else 0
    tail = max((n for n in level if level[n] == longest), key=lambda n: n) if level else None
    chain = []
    while tail:
        chain.append(tail)
        tail = via[tail]
    chain.reverse()
    ends_at_longest = sorted(n for n in level if level[n] == longest)
    edges = [[d, i] for i in ids for d in deps[i]]
    return {'nodes': len(ids), 'edges': len(edges), 'duplicates': dup, 'unknownDeps': unknown, 'cyclic': cyclic,
            'acyclic': not cyclic, 'topo': order, 'level': level, 'longestChainLevels': longest,
            'oneLongestChain': chain, 'seatsAtDeepestLevel': ends_at_longest,
            'reverseDeps': {k: sorted(v) for k, v in rdeps.items()}, 'edgeList': edges}


# ---------------------------------------------------------------- status
def seat_status(root, sid):
    d = os.path.join(root, sid)
    info = {'dir': os.path.isdir(d), 'files': 0, 'prepFiles': 0, 'statusFile': None, 'issues': []}
    if not info['dir']:
        return info
    for dp, dns, fns in os.walk(d):
        rel = os.path.relpath(dp, d).replace(os.sep, '/')
        for fn in fns:
            if rel == 'prep' or rel.startswith('prep/'):
                info['prepFiles'] += 1
            else:
                info['files'] += 1
    sp = os.path.join(d, 'status.json')
    if os.path.isfile(sp):
        info['statusFile'] = {'path': f'{sid}/status.json', 'sha256': sha256_file(sp)}
        try:
            st = json.load(open(sp, encoding='utf-8'))
        except Exception as e:  # noqa: BLE001
            info['issues'].append(f'status.json unreadable: {e}')
            return info
        info['declared'] = st.get('status')
        if st.get('seat') != sid:
            info['issues'].append(f"seat field {st.get('seat')!r} != {sid}")
        if st.get('status') not in SEAT_STATUS_MAP:
            info['issues'].append(f"status {st.get('status')!r} not in 交付完成|复用完成|阻断|待验")
        for k in ['summary', 'deliverables', 'blockers']:
            if k not in st:
                info['issues'].append(f'missing key {k}')
        missing = [p for p in st.get('deliverables', []) if not os.path.exists(os.path.join(d, p))]
        if missing:
            info['issues'].append(f'deliverables missing on disk: {missing}')
        info['deliverables'] = len(st.get('deliverables', []))
        info['deliverablesMissing'] = missing
        info['blockers'] = st.get('blockers', [])
        info['openItems'] = len(st.get('openItems', []) or [])
        info['nextDependentsDeclared'] = st.get('nextDependents')
    pp = os.path.join(d, 'prep', 'prep-status.json')
    if os.path.isfile(pp):
        info['prepStatus'] = {'path': f'{sid}/prep/prep-status.json', 'sha256': sha256_file(pp)}
    return info


def resolve_status(seats, infos):
    status, why = {}, {}
    # pass 1: declared statuses
    for s in seats:
        i = infos[s['id']]
        if i.get('statusFile') and i.get('declared') in SEAT_STATUS_MAP:
            st = SEAT_STATUS_MAP[i['declared']]
            if st in DONE and i.get('deliverablesMissing'):
                status[s['id']], why[s['id']] = '待验收', 'S1b 声明完成但交付清单有缺件，降为待验收'
            else:
                status[s['id']], why[s['id']] = st, 'S1 本席位 status.json'
    # pass 2: derived, in topo order handled by caller
    return status, why


def derive(seats, topo, infos):
    status, why = resolve_status(seats, infos)
    sd = {s['id']: s for s in seats}
    for sid in topo:
        if sid in status:
            continue
        i = infos[sid]
        if i['files'] > 0:
            status[sid], why[sid] = '制作中', 'S2 工作包有 prep/ 以外的文件但没有 status.json'
            continue
        open_deps = [d for d in sd[sid]['deps'] if status.get(d) not in DONE]
        if not open_deps:
            status[sid], why[sid] = '可开工', 'S3 依赖全部交付完成/复用完成'
        else:
            status[sid] = '待输入'
            why[sid] = 'S4 未完成依赖：' + '、'.join(open_deps)
    return status, why


# ---------------------------------------------------------------- locks
def resolve_locks(root, lab, base, head, pool_text, seats, city_nodes, own6):
    tree_b = git(lab, 'ls-tree', '-r', '--name-only', base).splitlines()
    tree_h = git(lab, 'ls-tree', '-r', '--name-only', head).splitlines()
    changed = git(lab, 'diff', '--name-only', f'{base}..{head}').splitlines()
    out = []
    for L in LOCKS:
        L = json.loads(json.dumps(L, ensure_ascii=False))
        rec = {k: L[k] for k in L}
        rec['poolQuoteFound'] = L['poolQuote'] in pool_text
        mb, mh = [], []
        per_pat = {}
        for pat in L['paths']:
            a = [p for p in tree_b if glob_match(p, pat)]
            b = [p for p in tree_h if glob_match(p, pat)]
            per_pat[pat] = {'baseline': len(a), 'head': len(b),
                            'expectedOnlyAfterBaseline': pat in L.get('afterBaselinePaths', [])}
            mb += a
            mh += b
        mb, mh = sorted(set(mb)), sorted(set(mh))
        rec['patternMatches'] = per_pat
        if L['id'] == 'LOCK-PUBLIC-DOCS':
            rec['files'] = {'baselineCount': len(mb), 'note': '全部 docs/ 与 lab/，不逐件列 SHA'}
        else:
            hb = blob_sha256s(lab, base, mb)
            rec['files'] = [{'path': p, **hb[p]} for p in mb]
            new_in_head = [p for p in mh if p not in set(mb)]
            hh = blob_sha256s(lab, head, new_in_head)
            rec['filesAddedAfterBaseline'] = [{'path': p, **hh[p]} for p in new_in_head]
        rec['changedAfterBaseline'] = sorted(p for p in changed if any(glob_match(p, pat) for pat in L['paths']))
        if L.get('expectCount', {}).get('gateCards') is not None:
            cards = sorted({p.split('/')[3] for p in mb if p.startswith('docs/library/models/m-luoyang-') and p.split('/')[3].endswith('-gate')})
            rec['gateCardsFound'] = cards
            rec['gateCardCountOk'] = len(cards) == L['expectCount']['gateCards']
        rec['cityNodesCheck'] = {n: {'inBaselineCityData': n in city_nodes,
                                     'ly006': (own6.get(n) or {}).get('status')} for n in L['cityNodes']}
        for ef in L.get('extFiles', []):
            p = os.path.join(root, ef['path'])
            ef['present'] = os.path.isfile(p)
            ef['sha256Recomputed'] = sha256_file(p) if ef['present'] else None
            ef['match'] = ef['sha256Recomputed'] == ef['sha256']
        rec['extFiles'] = L.get('extFiles', [])
        # seats whose original text mentions the item
        hits = []
        if L.get('appliesTo') == 'ALL':
            rec['seatsAffected'] = 'ALL'
        else:
            for s in seats:
                txt = s['text'] + '\n' + (s.get('_intro') or '')
                kws = [k for k in L['keywords'] if k in txt]
                if kws:
                    line = next(l for l in txt.split('\n') if any(k in l for k in kws))
                    hits.append({'seat': s['id'], 'keywords': kws, 'line': line.strip()[:160]})
            rec['seatsAffected'] = hits
        rec['forbidden'] = COMMON_FORBIDDEN if L['kind'] == 'protected-work' else (
            ['LY-001…099 写入、改名、删除这些路径', '以「顺手修」名义提交到 lab main'] if L['kind'] == 'shared-file'
            else ['任何席位自行行使此权利'])
        rec['allowed'] = COMMON_ALLOWED if L['kind'] == 'protected-work' else (
            ['只读', '在自己工作包内交 overlay / 语义合并提案'] if L['kind'] == 'shared-file' else ['向持权人提出申请'])
        rec['state'] = 'active'
        out.append(rec)
    return out, changed


# ---------------------------------------------------------------- pause
def flatten_strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from flatten_strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from flatten_strings(v)


def resolve_pauses(root, lab, out_dir):
    res = []
    for P in PAUSES:
        P = json.loads(json.dumps(P, ensure_ascii=False))
        for src in P['sources']:
            if 'lab-git' in src:
                text = git(lab, 'show', src['lab-git'])
                src['sha256'] = hashlib.sha256(text.encode('utf-8')).hexdigest()
                src['found'] = src['quote'] in text
                continue
            fp = os.path.join(root, src['file'])
            if src['file'].startswith('LY-009/'):
                fp = os.path.join(out_dir, src['file'][len('LY-009/'):])
            if not os.path.isfile(fp):
                src['found'] = False
                src['sha256'] = None
                continue
            src['sha256'] = sha256_file(fp)
            raw = open(fp, encoding='utf-8').read()
            if fp.endswith('.json'):
                src['found'] = any(src['quote'] in s for s in flatten_strings(json.loads(raw))) or src['quote'] in raw
            else:
                src['found'] = src['quote'] in raw
        P['state'] = 'open'
        P['clearedBy'] = None
        P['clearedAt'] = None
        res.append(P)
    return res


# ---------------------------------------------------------------- ownership / whitelist
def ownership(seats):
    per = {}
    for s in seats:
        sid = s['id']
        per[sid] = {
            'writeArea': s.get('writeArea'),
            'allow': [f'{sid}/**'],
            'deny': [f'{sid}/**/*.blend*', f'{sid}/**/*.zip', f'{sid}/**/*.7z', f'{sid}/**/*.rar',
                     f'{sid}/**/*.part###', f'{sid}/**/*.z##', 'GLB > 15,000,000 B', 'any file > 100 MiB'],
            'warn': ['__pycache__/', '*.pyc', 'Thumbs.db', '.DS_Store', 'any file > 50 MiB'],
            'branch': {'shared': 'workpacks', 'ifSeparate': f'wp/{sid}'},
            'labWrite': 'LY-100 only, per coordinator batch' if sid == 'LY-100' else 'none',
            'publish': 'none (coordinator only)',
            'cityWrite': 'yes (LY-100 batches, coordinator-authorized)' if sid == 'LY-100' else 'proposal only',
        }
    return {
        'ruleset': check_whitelist.RULESET,
        'checker': 'LY-009/source/check_whitelist.py',
        'coordinatorFiles': sorted(check_whitelist.COORD_FILES),
        'branches': {
            'workpacks': {'repo': 'D:/GitHub/creation-notebook-workpacks (git worktree of creation-notebook-lab)',
                          'remote': 'origin/workpacks', 'writers': 'LY-001…100 each inside own LY-### dir; coordinator for root files',
                          'push': 'coordinator only'},
            'lab main': {'repo': 'D:/GitHub/creation-notebook-lab', 'writers': 'LY-100 only, per coordinator batch',
                         'push': 'coordinator only'},
            'luoyang-content': {'writers': 'coordinator (source packs / Release)', 'seats': 'read-only'},
            'per-seat branches': {'naming': 'wp/LY-### (based on workpacks)',
                                  'why not workpacks/LY-###': 'refs/heads/workpacks already exists; git refuses a ref that is both a file and a directory (tested in qa/checks.json C9)',
                                  'content': 'must contain only that seat whitelist (check_whitelist --git)'},
        },
        'external': {'D:/GitHub/creation-notebook-待传/': 'coordinator only (LOCK-SOURCE-RELEASE)',
                     'scratchpad mq/cards/<id>/': 'read-only shared inputs (audit/render), not a write area'},
        'seats': per,
    }


# ---------------------------------------------------------------- main
def main():
    root, lab, base, out_dir = sys.argv[1:5]
    os.makedirs(os.path.join(out_dir, 'board'), exist_ok=True)
    os.makedirs(os.path.join(out_dir, 'qa'), exist_ok=True)
    pool_path = os.path.join(root, 'TASKPOOL.md')
    tb_path = os.path.join(root, 'taskboard.json')
    parsed = parse_taskpool.parse(pool_path)
    pool_text = open(pool_path, encoding='utf-8').read()
    tb = json.load(open(tb_path, encoding='utf-8'))
    head = git(lab, 'rev-parse', 'origin/main').strip()
    base_full = git(lab, 'rev-parse', base).strip()
    tb_blob = git(root, 'show', 'HEAD:taskboard.json', binary=True)
    wp_head = git(root, 'rev-parse', 'HEAD').strip()

    cmp_ = compare(parsed, tb)
    cmp_['taskboard'] = {'file': 'taskboard.json', 'worktreeSha256': sha256_file(tb_path),
                         'commitBlobSha256': hashlib.sha256(tb_blob).hexdigest(), 'workpacksHead': wp_head,
                         'worktreeIsCrlfOfCommit': open(tb_path, 'rb').read().replace(b'\r\n', b'\n') == tb_blob}
    json.dump(cmp_, open(os.path.join(out_dir, 'qa', 'parse-compare.json'), 'w', encoding='utf-8', newline='\n'),
              ensure_ascii=False, indent=1)

    seats = parsed['seats']
    sec_intro = {s['title']: s['intro'] for s in parsed['sections']}
    for s in seats:
        s['_intro'] = sec_intro.get(s['section'])
    D = dag(seats)
    infos = {s['id']: seat_status(root, s['id']) for s in seats}
    status, why = derive(seats, D['topo'], infos)

    city_nodes = set()
    with open(os.path.join(root, 'LY-001', 'qa', 'city-nodes.csv'), encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            city_nodes.add(r['nodeId'])
    own6 = json.load(open(os.path.join(root, 'LY-006', 'registry', 'ownership.json'), encoding='utf-8'))['ownership']['cityNodes']
    locks, lab_changed = resolve_locks(root, lab, base_full, head, pool_text, seats, city_nodes, own6)
    pauses = resolve_pauses(root, lab, out_dir)
    own = ownership(seats)

    # per-seat lock / pause refs
    lock_refs = {s['id']: [] for s in seats}
    for L in locks:
        if L['seatsAffected'] == 'ALL':
            continue
        for h in L['seatsAffected']:
            lock_refs[h['seat']].append(L['id'])
    pause_refs = {s['id']: [] for s in seats}
    for P in pauses:
        for sid in P['seats']:
            pause_refs[sid].append(P['id'])

    now = datetime.datetime.now().astimezone().isoformat(timespec='seconds')
    board_seats = []
    for s in seats:
        sid = s['id']
        board_seats.append({
            'id': sid, 'title': s['title'], 'type': s['type'], 'lane': LANES[s['type']],
            'section': s['section'], 'sectionIntro': s['_intro'],
            'depsRaw': s['depsRaw'], 'usesG': s['usesG'], 'depsExplicit': s['depsExplicit'], 'deps': s['deps'],
            'level': D['level'][sid], 'dependents': D['reverseDeps'][sid],
            'status': status[sid], 'statusRule': why[sid], 'statusEvidence': infos[sid],
            'assignee': 'Claude（README：城景和项目卡只由 LY-100（Claude）分批合入）' if sid == 'LY-100' else None,
            'writeArea': s.get('writeArea'), 'whitelist': own['seats'][sid]['allow'],
            'locks': sorted(set(lock_refs[sid])) + ['LOCK-SHARED-CITY', 'LOCK-PUBLIC-DOCS', 'RIGHT-PUBLISH',
                                                     'RIGHT-CITY-WRITE', 'RIGHT-TASKBOARD'],
            'pauses': pause_refs[sid],
            'lines': [s['lineStart'], s['lineEnd']],
            'text': s['text'],
        })
    counts = {k: sum(1 for b in board_seats if b['status'] == k) for k in STATUSES}
    lane_counts = {}
    for b in board_seats:
        lane_counts.setdefault(b['lane'], {k: 0 for k in STATUSES})
        lane_counts[b['lane']][b['status']] += 1
    gate = parsed['G']
    board = {
        'board': 'LY-009 taskboard v2 (proposal; root taskboard.json unchanged)',
        'generatedAt': now,
        'source': {'TASKPOOL.md': parsed['sha256'], 'taskboard.json(worktree)': cmp_['taskboard']['worktreeSha256'],
                   'taskboard.json(commit blob)': cmp_['taskboard']['commitBlobSha256'], 'workpacksHead': wp_head},
        'baseline': base_full, 'labOriginMainAtBuild': head,
        'statusVocabulary': STATUSES,
        'statusRules': {
            'S1': '席位自己的 status.json：交付完成/复用完成/阻断 照录，待验 记作 待验收',
            'S1b': '声明交付完成/复用完成但 deliverables 中有文件不存在：记作 待验收',
            'S2': '没有 status.json、但 prep/ 之外已有文件：制作中',
            'S3': '没有文件、依赖全部 交付完成/复用完成：可开工',
            'S4': '其余：待输入（prep/ 里的准备工作允许，不改变状态）',
            'note': '可开工 只说明依赖到齐；能否落城另看 LY-010 决策表、LY-094 与暂停区。',
        },
        'G': {'members': gate, 'frozen': all(status[g] in DONE for g in gate),
              'missing': [g for g in gate if status[g] not in DONE]},
        'counts': counts, 'laneCounts': lane_counts,
        'typeCounts': {t: sum(1 for b in board_seats if b['type'] == t) for t in STATED_COUNTS},
        'typeCountsStated': STATED_COUNTS,
        'sections': parsed['sections'],
        'dag': {k: D[k] for k in ['nodes', 'edges', 'acyclic', 'cyclic', 'duplicates', 'unknownDeps',
                                  'longestChainLevels', 'oneLongestChain', 'seatsAtDeepestLevel']},
        'locks': 'locks.json', 'pauseZone': 'pause-zone.json', 'ownership': 'ownership.json',
        'handoverTemplate': '../templates/daily-handover.md',
        'seats': board_seats,
    }
    bd = os.path.join(out_dir, 'board')

    def dump(name, obj):
        with open(os.path.join(bd, name), 'w', encoding='utf-8', newline='\n') as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)

    dump('taskboard.v2.json', board)
    dump('dag.json', {'G': gate, 'topo': D['topo'], 'level': D['level'], 'edges': D['edgeList'],
                      'reverseDeps': D['reverseDeps'], 'longestChainLevels': D['longestChainLevels'],
                      'oneLongestChain': D['oneLongestChain']})
    dump('locks.json', {'version': 1, 'generatedAt': now, 'baseline': base_full, 'labOriginMain': head,
                        'labChangedAfterBaseline': lab_changed, 'locks': locks})
    dump('pause-zone.json', {'version': 1, 'generatedAt': now,
                             'effects': {'blocks-merge': '可在本包内做，LY-100 不得合并受影响部分',
                                         'blocks-city': '只交局部包，不得落城',
                                         'blocks-start': '受影响部分不能开工',
                                         'advisory': '不阻断，须在交付中注明'},
                             'rules': [l.strip() for l in (__import__('pause_spec').__doc__ or '').split('\n  * ')[1:]],
                             'entries': pauses})
    dump('ownership.json', own)
    write_md(board, locks, pauses, os.path.join(bd, 'board.md'))
    print('status counts', counts)
    print('G frozen', board['G'])
    print('dag', board['dag']['acyclic'], board['dag']['longestChainLevels'])
    print('locks', [(L['id'], L['poolQuoteFound'], len(L['files']) if isinstance(L['files'], list) else L['files']['baselineCount'],
                     len(L['changedAfterBaseline'])) for L in locks])
    print('pauses', [(P['id'], all(s['found'] for s in P['sources'])) for P in pauses])


def write_md(board, locks, pauses, path):
    L = []
    L.append('# 东汉洛阳 100 席位任务板 v2（LY-009 提案）\n')
    L.append(f"生成：{board['generatedAt']}。原文 TASKPOOL.md sha256 `{board['source']['TASKPOOL.md']}`；"
             f"基线 `{board['baseline'][:7]}`，构建时 lab origin/main `{board['labOriginMainAtBuild'][:7]}`。\n")
    L.append('本表由 `LY-009/source/build_board.py` 生成，状态按 S1–S4 规则从各席位目录现读，不手填。'
             '「可开工」只说明依赖到齐，不代表地域准入或已入城。\n')
    g = board['G']
    L.append(f"**G 开工包**：{'、'.join(g['members'])}；{'已冻结' if g['frozen'] else '未冻结，缺 ' + '、'.join(g['missing'])}。\n")
    L.append('| 状态 | ' + ' | '.join(board['statusVocabulary']) + ' |')
    L.append('|---|' + '---|' * len(board['statusVocabulary']))
    L.append('| 合计 | ' + ' | '.join(str(board['counts'][k]) for k in board['statusVocabulary']) + ' |')
    for lane, c in board['laneCounts'].items():
        L.append(f'| {lane} | ' + ' | '.join(str(c[k]) for k in board['statusVocabulary']) + ' |')
    L.append('')
    d = board['dag']
    L.append(f"依赖图：{d['nodes']} 席、{d['edges']} 条边（G 展开后），无环={d['acyclic']}，最长链 {d['longestChainLevels']} 层；"
             f"一条最长链：{' → '.join(d['oneLongestChain'])}。\n")
    for lane in ['资料契约', '模型补件', '复用装配', '独立验收', '唯一整合']:
        L.append(f'## {lane}\n')
        L.append('| 席位 | 名称 | 层 | 状态 | 依赖（原文） | 锁 | 暂停区 |')
        L.append('|---|---|---|---|---|---|---|')
        for s in board['seats']:
            if s['lane'] != lane:
                continue
            lk = [x for x in s['locks'] if not x.startswith(('LOCK-SHARED', 'LOCK-PUBLIC', 'RIGHT-'))]
            L.append(f"| {s['id']} | {s['title']} | {s['level']} | {s['status']} | {s['depsRaw']} | "
                     f"{' '.join(x.replace('LOCK-', '') for x in lk) or '—'} | {' '.join(s['pauses']) or '—'} |")
        L.append('')
    L.append('## 排除锁\n')
    L.append('全部席位另受 LOCK-SHARED-CITY、LOCK-PUBLIC-DOCS、RIGHT-PUBLISH、RIGHT-CITY-WRITE、RIGHT-TASKBOARD 约束（表中省略）。\n')
    L.append('| 锁 | 对象 | 持锁 | 基线文件数 | 基线后变动 | 文本提及席位 |')
    L.append('|---|---|---|---|---|---|')
    for k in locks:
        n = k['files']['baselineCount'] if isinstance(k['files'], dict) else len(k['files'])
        sa = 'ALL' if k['seatsAffected'] == 'ALL' else ' '.join(h['seat'][3:] for h in k['seatsAffected']) or '—'
        L.append(f"| {k['id']} | {k['name']} | {k['holder']} | {n} | {len(k['changedAfterBaseline'])} | {sa} |")
    L.append('')
    L.append('## 暂停区\n')
    L.append('| 编号 | 事项 | 效果 | 裁决 | 解除条件 | 席位 |')
    L.append('|---|---|---|---|---|---|')
    for p in pauses:
        L.append(f"| {p['id']} | {p['title']} | {p['effect']} | {p['decider']} | {p['unblock']} | {' '.join(x[3:] for x in p['seats']) or '—'} |")
    L.append('')
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L))


if __name__ == '__main__':
    main()
