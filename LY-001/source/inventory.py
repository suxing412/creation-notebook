"""LY-001 snapshot inventory.  READ-ONLY on the lab repository: it only opens files for
reading and runs read-only git queries.  All output goes to the LY-001 workpack.

usage: python -I inventory.py <lab_root> <out_dir> <city_dump_json> <mq_cards_dir>
"""
import hashlib, json, os, re, subprocess, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import glbinfo  # noqa: E402

LAB = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
DUMP = Path(sys.argv[3]).resolve()
MQ = Path(sys.argv[4]).resolve()
DOCS = LAB / 'docs'
CITY = DOCS / 'cities' / 'luoyang'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def git(*args):
    return subprocess.run(['git', '-C', str(LAB), *args], capture_output=True, text=True, encoding='utf8').stdout.strip()


def rel_docs(p):
    return Path(p).resolve().relative_to(DOCS).as_posix()


# ---------------------------------------------------------------- git identity
gitinfo = {
    'head': git('rev-parse', 'HEAD'), 'branch': git('branch', '--show-current'),
    'origin_main': git('rev-parse', 'origin/main'), 'local_main': git('rev-parse', 'main'),
    'head_subject': git('log', '-1', '--format=%s'), 'head_date': git('log', '-1', '--format=%cI'),
    'status_porcelain': git('status', '--porcelain', '--untracked-files=no').splitlines(),
    'status_city': git('status', '--porcelain', '--', 'docs/cities/luoyang').splitlines(),
    'status_library': git('status', '--porcelain', '--', 'docs/library', 'docs/model-library').splitlines(),
}
tracked = {}
for line in git('ls-files', '-s', '--', 'docs/cities/luoyang', 'docs/library', 'docs/model-library', 'docs/fusions/F01/vendor', 'docs/vendor/meshopt_decoder.module.js', 'docs/prototypes/luoyang-m0/shaders.mjs').splitlines():
    meta, path = line.split('\t', 1)
    tracked[path] = meta.split()[1]

# ---------------------------------------------------------------- hash files
# Canonical bytes = the committed blob at HEAD (what the repository/Pages serves).
# The Windows checkout uses core.autocrlf, so multi-line text files can differ on disk;
# both hashes are recorded.
def blob_hashes(paths):
    proc = subprocess.Popen(['git', '-C', str(LAB), 'cat-file', '--batch'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    res = {}
    for p in paths:
        proc.stdin.write((tracked[p] + '\n').encode())
        proc.stdin.flush()
        header = proc.stdout.readline().split()
        size = int(header[2])
        data = proc.stdout.read(size)
        proc.stdout.read(1)
        res[p] = (size, hashlib.sha256(data).hexdigest())
    proc.stdin.close()
    proc.wait()
    return res


committed = blob_hashes(sorted(tracked))
files = {}
for root in [CITY, DOCS / 'library' / 'models', DOCS / 'model-library']:
    for p in sorted(root.rglob('*')):
        if p.is_file():
            r = rel_docs(p)
            wt = sha(p)
            g = committed.get('docs/' + r)
            files[r] = {'path': r, 'bytes': g[0] if g else p.stat().st_size, 'sha256': g[1] if g else wt,
                        'gitTracked': g is not None, 'worktreeBytes': p.stat().st_size, 'worktreeSha256': wt,
                        'worktreeDiffersFromCommit': bool(g and g[1] != wt)}
missing_on_disk = sorted(p for p in tracked if not (LAB / p).is_file())

# ---------------------------------------------------------------- GLB parse
glb = {}
for r, f in files.items():
    if r.endswith('.glb'):
        try:
            info, boxes, _ = glbinfo.summarize(DOCS / r)
            info.pop('nodeNames')
            glb[r] = info
        except Exception as e:  # noqa: BLE001
            glb[r] = {'error': repr(e)}

# ---------------------------------------------------------------- city manifest (current entry)
M = json.load(open(DUMP, encoding='utf8'))


def url_to_rel(u):
    # node import gives file:///D:/... urls
    from urllib.parse import unquote, urlparse
    p = Path(unquote(urlparse(u).path).lstrip('/'))
    return rel_docs(p)


tier_unlocated = {'U', 'X', 'unknown', 'excluded', '未知', '排除'}
assets = {a['id']: a for a in M['assets']}
chapters = M['chapters']
chapter_load = defaultdict(list)
for c in chapters:
    for nid in c.get('loadNodeIds', []):
        chapter_load[nid].append(c['id'])
city_rows = []
asset_rows = []
problems = []
asset_users = defaultdict(list)
for n in M['nodes']:
    asset_users[n['asset']].append(n['id'])
for n in M.get('researchModels', []):
    asset_users[n['asset']].append(n['id'])

for a in M['assets']:
    row = {'assetId': a['id']}
    for kind, key, bkey, skey in [('far', 'url', 'bytes', 'sha256'), ('near', 'nearUrl', 'nearBytes', 'nearSha256')]:
        if not a.get(key):
            continue
        r = url_to_rel(a[key])
        f = files.get(r)
        ok_exist = f is not None
        ok_bytes = ok_exist and f['bytes'] == a.get(bkey)
        ok_sha = ok_exist and (a.get(skey) is None or f['sha256'] == a.get(skey))
        row[kind] = {'path': r, 'declaredBytes': a.get(bkey), 'declaredSha256': a.get(skey),
                     'actualBytes': f and f['bytes'], 'actualSha256': f and f['sha256'],
                     'exists': ok_exist, 'bytesMatch': ok_bytes, 'shaMatch': ok_sha,
                     'sha256Declared': a.get(skey) is not None}
        if not (ok_exist and ok_bytes and ok_sha):
            problems.append({'kind': 'asset-file-mismatch', 'asset': a['id'], 'lod': kind, 'detail': row[kind]})
        if ok_exist and r.endswith('.glb'):
            info, _, _ = glbinfo.summarize(DOCS / r, exclude=a.get('excludeNodes') or [])
            ex = set(a.get('excludeNodes') or [])
            row[kind]['excludeNodes'] = sorted(ex)
            row[kind]['excludeMatched'] = info['excludeMatched']
            row[kind]['excludeAllMatched'] = set(info['excludeMatched']) == ex
            row[kind]['worldMinAfterExclude'] = info['worldMin']
            row[kind]['worldMaxAfterExclude'] = info['worldMax']
            if ex and kind == 'far' and set(info['excludeMatched']) != ex:
                problems.append({'kind': 'exclude-mismatch', 'asset': a['id'], 'missing': sorted(ex - set(info['excludeMatched']))})
    if a.get('sourceGlbSha256'):
        row['sourceGlbSha256'] = a['sourceGlbSha256']
        row['sourceRepositoryPath'] = a.get('sourceRepositoryPath')
    row['sourceAsset'] = a.get('sourceAsset')
    row['sourceContract'] = a.get('sourceContract')
    row['usedBy'] = asset_users.get(a['id'], [])
    asset_rows.append(row)

for n in M['nodes']:
    tier = n.get('tier') or assets[n['asset']].get('tier')
    if tier in tier_unlocated:
        state = '登记但不渲染（未定位/排除）'
    elif n.get('initial') is not False:
        state = '已入城·首屏默认加载'
    elif chapter_load.get(n['id']):
        state = '已入城·按章加载（initial=false）'
    else:
        state = '城中坐标但无加载入口（隐藏）'
    a = assets[n['asset']]
    city_rows.append({'nodeId': n['id'], 'assetId': n['asset'], 'chapter': n.get('chapter'), 'state': state,
                      'initial': n.get('initial'), 'tier': tier, 'loadedByChapters': chapter_load.get(n['id'], []),
                      'matrix': n.get('matrix'), 'position': n.get('position'), 'bounds': n.get('bounds'),
                      'variant': n.get('variant'), 'sourceGroup': n.get('sourceGroup'),
                      'nearSwapOnFocus': bool(a.get('nearUrl')), 'replaces': n.get('replaces'),
                      'farPath': url_to_rel(a['url']), 'nearPath': a.get('nearUrl') and url_to_rel(a['nearUrl'])})
for n in M.get('researchModels', []):
    a = assets[n['asset']]
    city_rows.append({'nodeId': n['id'], 'assetId': n['asset'], 'chapter': n.get('chapter'),
                      'state': '仅模型·独立研究视图（cityPlacement=null，城中不渲染）', 'space': n.get('space'),
                      'cityPlacement': n.get('cityPlacement'), 'tier': n.get('tier'), 'deliveryStatus': n.get('deliveryStatus'),
                      'sourceContract': n.get('sourceContract'), 'farPath': url_to_rel(a['url']),
                      'sourceGlbSha256': a.get('sourceGlbSha256'), 'sourceAsset': a.get('sourceAsset')})

contract_rows = []
for c in M['provenance'].get('sourceContracts', []):
    r = rel_docs(CITY / c['path'])
    f = files.get(r)
    okc = bool(f and f['sha256'] == c['sha256'])
    okw = bool(f and f['worktreeSha256'] == c['sha256'])
    basis = '提交字节(LF)' if okc else ('仅Windows检出字节(CRLF)' if okw else '均不符')
    contract_rows.append({'path': r, 'declaredSha256': c['sha256'], 'committedSha256': f and f['sha256'],
                          'worktreeSha256': f and f['worktreeSha256'], 'matchCommitted': okc, 'matchWorktree': okw,
                          'matchBasis': basis})
    if not okc:
        problems.append({'kind': 'contract-sha-eol-dependent' if okw else 'contract-sha-mismatch', 'path': r,
                         'detail': '城市清单声明的合同SHA只与本机autocrlf检出字节一致，与提交/线上字节不一致' if okw else '声明SHA与提交和检出字节都不一致'})

# ---------------------------------------------------------------- hidden-trial packages (activation false)
north = json.load(open(CITY / 'progress-assets/north13-gates/source.json', encoding='utf8'))
trial_rows = []
for p in north['packages']:
    pl = p.get('placement', {})
    for m in p['models']:
        r = rel_docs(CITY / 'progress-assets/north13-gates' / m['file'])
        f = files.get(r)
        trial_rows.append({'package': p['package'], 'file': r, 'lod': m.get('lod'), 'declaredSha256': m['sha256'],
                           'actualSha256': f and f['sha256'], 'shaMatch': bool(f and f['sha256'] == m['sha256']),
                           'displayMode': p.get('displayMode'), 'activation': pl.get('activation'),
                           'active': pl.get('active'), 'exclusive': pl.get('exclusive'),
                           'origin': pl.get('engineering_origin_from_existing_wall_caps'), 'rotation_z_rad': pl.get('rotation_z_rad'),
                           'targets': [{k: t.get(k) for k in ('id', 'variant', 'position', 'rotationDegrees')} for t in pl.get('targets', [])],
                           'state': '隐藏试放（候选覆盖包，activation=false/未激活，只在独立研究视图展示）'})

# ---------------------------------------------------------------- static reference scan
REF = re.compile(r"""[\"'`(]((?:\.{0,2}/)?[A-Za-z0-9_\-./${}]*?[A-Za-z0-9_\-]\.(?:glb|gltf|json|mjs|js|webp|png|jpg|html|md|css|woff2|bin))(?=[\"'`)?#])""")
scan_roots = [CITY / 'index.html', CITY / 'app.mjs', CITY / 'scene.mjs', CITY / 'city-renderer.mjs', CITY / 'city-data.mjs',
              CITY / 'project-notes.html', CITY / 'static-evidence.html', CITY / 'p-luoyang.asset.json']
scan_roots += sorted((CITY / 'v1').glob('*'))
scan_roots += sorted(p for p in CITY.rglob('*.json') if p not in scan_roots)
by_base = defaultdict(list)
for r in files:
    by_base[Path(r).name].append(r)
refs = defaultdict(set)  # target rel -> referrers
unresolved = []
for src in scan_roots:
    if not src.is_file():
        continue
    text = src.read_text(encoding='utf8', errors='replace')
    srel = rel_docs(src)
    for s in set(REF.findall(text)):
        if '${' in s or s.startswith('http'):
            continue
        cands = []
        for base in [src.parent, CITY, DOCS]:
            q = (base / s).resolve()
            try:
                rq = rel_docs(q)
            except ValueError:
                continue
            if rq in files:
                cands.append(rq)
        if not cands and '/' not in s.strip('./'):
            cands = by_base.get(Path(s).name, [])
        if not cands and '/' in s:
            tail = '/'.join(Path(s).parts[-2:])
            cands = [r for r in files if r.endswith('/' + tail)]
        if cands:
            for c in sorted(set(cands))[:1] if len(set(cands)) == 1 else sorted(set(cands)):
                refs[c].add(srel)
        else:
            unresolved.append({'from': srel, 'ref': s})

# ---------------------------------------------------------------- library cards
lib = json.load(open(OUT / 'assets.HEAD.json', encoding='utf8'))
cards = []
sha_index = defaultdict(list)
for r, f in files.items():
    if r.endswith('.glb'):
        sha_index[f['sha256']].append(r)
city_far_near = {}
for row in asset_rows:
    for k in ('far', 'near'):
        if k in row:
            city_far_near[row[k]['path']] = (row['assetId'], k)
city_loaded_sha = {}
for n in city_rows:
    if n['state'].startswith('已入城'):
        for k in ('farPath', 'nearPath'):
            if n.get(k):
                city_loaded_sha[files[n[k]]['sha256']] = n[k]
flat_source = {row.get('sourceGlbSha256'): row['assetId'] for row in asset_rows if row.get('sourceGlbSha256')}
trial_sha = {t['declaredSha256']: t['package'] for t in trial_rows}

audits = {}
for d in MQ.iterdir() if MQ.exists() else []:
    a = d / 'audit.json'
    if a.exists():
        try:
            audits[d.name] = json.load(open(a, encoding='utf8'))
        except Exception:  # noqa: BLE001
            pass

for c in lib['assets']:
    if c.get('category') not in ('models', 'projects'):
        continue
    is_ly = 'p-luoyang' in (c.get('related') or []) or 'luoyang' in c['id']
    rowfiles = []
    for f in c.get('files') or []:
        r = f['path']
        fr = files.get(r)
        if fr is None and (DOCS / r).is_file():
            fr = {'bytes': (DOCS / r).stat().st_size, 'sha256': sha(DOCS / r)}
        s = fr and fr['sha256']
        inCity = s in city_loaded_sha
        rowfiles.append({'label': f.get('label'), 'path': r, 'bytes': fr and fr['bytes'], 'declaredBytes': f.get('bytes'),
                         'sha256': s, 'triangles': f.get('triangles'), 'extUsed': f.get('extUsed'),
                         'over15MB': bool(fr and fr['bytes'] > 15_000_000),
                         'byteIdenticalCopies': [x for x in sha_index.get(s, []) if x != r],
                         'sameBytesAsCityLoaded': city_loaded_sha.get(s),
                         'sourceOfCityStudyFlat': flat_source.get(s), 'sameAsHiddenTrial': trial_sha.get(s)})
    au = audits.get(c['id'])
    issues = []
    if au:
        for e in au:
            if e.get('issues'):
                issues.append({'path': e['path'], 'sha256': e.get('sha256'), 'issues': e['issues']})
    cards.append({'id': c['id'], 'isLuoyang': is_ly, 'kind': c.get('kind'), 'title': c.get('title'), 'state': c.get('state'),
                  'status': c.get('status'), 'public': c.get('public'), 'updated': c.get('updated'), 'card': c.get('card'),
                  'files': rowfiles, 'mqAuditIssues': issues, 'mqAudited': au is not None})

# ---------------------------------------------------------------- classify every GLB in city dir
glb_rows = []
city_paths_loaded = {}
for n in city_rows:
    for k in ('farPath', 'nearPath'):
        if n.get(k):
            city_paths_loaded.setdefault(n[k], set()).add((n['state'], k))
trial_paths = {t['file'] for t in trial_rows}
# JSON read by the archived v1 app: literal refs in v1 modules + template expansions read from the code
v1_json = {t for t, srcs in refs.items() if t.endswith('.json') and any('/v1/' in s for s in srcs)}
for d in ('c01/placement.json', 'c01/research-candidate.json', 'd08/layout.json', 'd08/model-contract.json',
          'r01/layout.json', 'r01/model-contract.json', 'c02/layout.json', 'c02/partitions.json', 'c02/research-mask.json',
          'c02v/layout.json', 'c02v/partitions.json', 'c02v/research-mask.json', 'c02v/model-contract.json',
          'far44/preflight-contract.json', 'far44/instances-calt.json', 'far44/instances-original.json'):
    r = 'cities/luoyang/data/' + d
    if r in files:
        v1_json.add(r)
for r in sorted(x for x in files if x.endswith('.glb')):
    f = files[r]
    states = sorted({s for s, _ in city_paths_loaded.get(r, set())})
    lods = sorted({k for _, k in city_paths_loaded.get(r, set())})
    if states:
        cls = states
    elif r in trial_paths:
        cls = ['隐藏试放（activation=false）']
    elif any('/v1/' in x for x in refs.get(r, [])):
        cls = ['旧版v1归档入口代码直接引用（?mode/c01stage/c02stage 跳转可加载）']
    elif any(x in v1_json for x in refs.get(r, [])):
        cls = ['旧版v1读取的数据合同间接引用（v1可能加载）']
    elif refs.get(r):
        cls = ['仅出现在来源/合同记录中（当前入口与v1均不直接加载）']
    elif r.startswith('library/') or r.startswith('model-library/'):
        cls = ['仅模型（资产卡文件）']
    else:
        cls = ['城市目录内未被任何入口或合同引用']
    glb_rows.append({'path': r, 'bytes': f['bytes'], 'sha256': f['sha256'], 'gitTracked': f['gitTracked'],
                     'class': cls, 'cityLod': lods, 'over15MB': f['bytes'] > 15_000_000,
                     'byteIdenticalCopies': [x for x in sha_index[f['sha256']] if x != r],
                     'referencedBy': sorted(refs.get(r, [])), 'glb': glb.get(r)})

# ---------------------------------------------------------------- write
out = {
    'schema': 'LY-001/snapshot-1', 'lab': str(LAB).replace('\\', '/'), 'git': gitinfo,
    'counts': {
        'filesHashed': len(files), 'glbFiles': sum(1 for r in files if r.endswith('.glb')),
        'cityAssets': len(M['assets']), 'cityNodes': len(M['nodes']), 'researchModels': len(M.get('researchModels', [])),
        'chapters': len(chapters),
        'nodesByState': {s: sum(1 for n in city_rows if n['state'] == s) for s in sorted({n['state'] for n in city_rows})},
        'hiddenTrialModels': len(trial_rows), 'hiddenTrialPackages': len({t['package'] for t in trial_rows}),
        'unresolvedRefs': len(unresolved), 'problems': len(problems),
    },
    'chapters': [{k: c.get(k) for k in ('id', 'title', 'loadNodeIds', 'researchModelIds', 'defaultResearchModel', 'tier')} for c in chapters],
    'cityAssets': asset_rows, 'cityNodes': city_rows, 'sourceContracts': contract_rows, 'hiddenTrials': trial_rows,
    'cards': cards, 'glbFiles': glb_rows, 'unresolvedRefs': unresolved, 'problems': problems,
    'runtimeCodeDependencies': [
        {'path': p, 'exists': (DOCS / p).is_file(),
         'committedSha256': (committed.get('docs/' + p) or (None, None))[1] if ('docs/' + p) in tracked else None}
        for p in ['fusions/F01/vendor/three.module.js', 'vendor/meshopt_decoder.module.js',
                  'fusions/F01/vendor/addons/loaders/GLTFLoader.js', 'fusions/F01/vendor/addons/controls/OrbitControls.js',
                  'fusions/F01/vendor/addons/utils/BufferGeometryUtils.js', 'prototypes/luoyang-m0/shaders.mjs']],
    'v1JsonRead': sorted(v1_json), 'trackedMissingOnDisk': missing_on_disk,
    'worktreeEolDiffs': sorted(r for r, f in files.items() if f['worktreeDiffersFromCommit']),
}
out['counts']['glbByClass'] = {}
for g in glb_rows:
    k = ' + '.join(g['class'])
    out['counts']['glbByClass'][k] = out['counts']['glbByClass'].get(k, 0) + 1
json.dump(out, open(OUT / 'snapshot-ledger.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
json.dump(sorted(files.values(), key=lambda x: x['path']), open(OUT / 'file-hashes.json', 'w', encoding='utf8'), ensure_ascii=False, indent=0)
print(json.dumps(out['counts'], ensure_ascii=False, indent=1))
print('problems', json.dumps(problems, ensure_ascii=False)[:3000])
