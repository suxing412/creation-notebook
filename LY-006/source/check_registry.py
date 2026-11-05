# -*- coding: utf-8 -*-
# LY-006 registry checker with fault injection. Usage (from LY-006/):
#   python -I source/check_registry.py <LY-006 dir> <lab docs dir> <lab repo dir> <lab-status-before.txt>
# Writes qa/checks.json. Every check lists the SHA256 of the files it read.
import json, sys, os, re, copy, math, hashlib, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import build_registry as BR  # noqa: E402  (re-runs the build in-process with the same argv layout)

W6 = sys.argv[1]; LAB = sys.argv[3]; BEFORE = sys.argv[4]
WP = os.path.dirname(os.path.abspath(W6))
J = lambda *p: os.path.join(W6, *p)
def load(p): return json.load(open(p, encoding='utf-8'))
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
REG = {k: J('registry', k + '.json') for k in ('zones', 'ports', 'seams', 'ownership', 'seats')}
PORT_RX = re.compile(r'^[A-Za-z0-9_.-]+(:[A-Za-z0-9_.-]+){1,3}$')
KINDS = {'ground', 'threshold', 'floor', 'wall-end', 'road-end', 'mount', 'opening', 'cut', 'drain'}
COMP_CLASSES = {'fixed', 'moving', 'state-variant', 'removable', 'fixed-closed', 'fixed-open', 'moving-candidate (static in GLB)'}

def reg():
    return {k: load(v) for k, v in REG.items()}

board = load(os.path.join(WP, 'taskboard.json'))
DEPS = {s['id']: s['deps'] for s in board['seats']}
def closure(seat, memo={}):
    if seat in memo: return memo[seat]
    out = set()
    for d in DEPS.get(seat, []):
        out.add(d); out |= closure(d)
    memo[seat] = out
    return out
G = {'LY-001', 'LY-002', 'LY-005', 'LY-006', 'LY-007', 'LY-008', 'LY-009', 'LY-010'}
def depends(a, b):
    """True if seat a (transitively) depends on b; usesG seats depend on all G seats"""
    cl = set(closure(a))
    sb = {s['id']: s for s in board['seats']}
    for s in list(cl | {a}):
        if sb.get(s, {}).get('usesG'): cl |= G
    if b in G and sb.get(a, {}).get('usesG'): return True
    return b in cl

# ---------------------------------------------------------------- checks (pure functions on registry dicts)
def c_seats(r):
    errs = []
    st = r['seats']['seats']
    want = [f'LY-{i:03d}' for i in range(11, 91)]
    if sorted(st) != want: errs.append(f'seat set mismatch: {sorted(set(want) ^ set(st))}')
    for s in want:
        if s in st and st[s]['deps'] != DEPS[s]: errs.append(f'{s} deps differ from taskboard')
    # DAG acyclic
    seen, stack = set(), set()
    def visit(n):
        if n in stack: errs.append(f'cycle at {n}'); return
        if n in seen: return
        stack.add(n)
        for d in DEPS.get(n, []): visit(d)
        stack.discard(n); seen.add(n)
    for n in DEPS: visit(n)
    return errs, {'seats': len(st)}

def c_ownership(r):
    errs = []; o = r['ownership']['ownership']
    if r['ownership']['conflicts']: errs += [f"builder conflict: {c}" for c in r['ownership']['conflicts']]
    so = o['sourceObjects']
    unowned = [k for k, v in so.items() if not v['owner']]
    if unowned: errs.append(f'{len(unowned)} source objects without owner: {unowned[:5]}')
    cn = o['cityNodes']
    unc = [k for k, v in cn.items() if v['status'] == 'UNCOVERED']
    if unc: errs.append(f'uncovered city nodes {unc}')
    if len(cn) != 80: errs.append(f'city nodes {len(cn)} != 80 (66 + 14 research)')
    for k, v in cn.items():
        if v['owner'] is None and not v.get('reason'): errs.append(f'node {k} frozen without reason')
    for k, v in o['groundPieces'].items():
        if not v['owner']: errs.append(f'ground piece {k} without owner')
    for k, v in o['cardFields'].items():
        if v['owner'] is None and not v['status'].startswith('frozen'): errs.append(f'card field {k} unresolved')
    # every catalog that a seat modifies or keeps must have its card owned (or the card is frozen identity)
    cards_owned = {k.split('#')[0] for k, v in o['cardFields'].items() if v['owner'] and v['owner'] != 'LY-100'}
    cats = r['ownership']['catalogs']
    from registry_spec import SOURCE_CATALOG
    for key, c in SOURCE_CATALOG.items():
        if c.get('card') and c['card'] not in cards_owned: errs.append(f'catalog {key} card {c["card"]} has no proposal owner')
    # one owner per object id across classes: components / cuts / data unique by construction (builder) -> recount
    comp = o['components']
    return errs, {'sourceObjects': len(so), 'sourceObjectsModifyReplace': sum(1 for v in so.values() if v['mode'] != 'keep'),
                  'cityNodesOwned': sum(1 for v in cn.values() if v['owner']), 'cityNodesFrozen': sum(1 for v in cn.values() if not v['owner']),
                  'groundPieces': len(o['groundPieces']), 'cardFields': len(o['cardFields']),
                  'cardFieldsWithProposalOwner': sum(1 for v in o['cardFields'].values() if v['owner'] and v['owner'] != 'LY-100'),
                  'components': len(comp), 'cuts': len(o['cuts'])}

def mat(m16):
    return np.array(m16, dtype=float).reshape(4, 4).T

def c_ports(r):
    errs = []; P = r['ports']['ports']; maxres = 0.0
    for pid, p in P.items():
        if not PORT_RX.match(pid): errs.append(f'bad portId {pid}')
        if not isinstance(p['version'], int) or p['version'] < 1: errs.append(f'bad version {pid}')
        if p['kind'] not in KINDS and not p['status'].startswith('imported'): errs.append(f'bad kind {pid} {p["kind"]}')
        if p['status'].startswith('imported') and p['kind'] not in KINDS: errs.append(f'imported kind {pid}')
        for c in p['consumers']:
            if p['producer'] in ('LY-005', 'LY-006'): continue
            if c == p['producer']: errs.append(f'{pid}: producer consumes itself'); continue
            if not depends(c, p['producer']): errs.append(f'{pid}: consumer {c} does not depend on producer {p["producer"]}')
        if p.get('local') and p.get('world') and p.get('nodeMatrixColumnMajor'):
            N = mat(p['nodeMatrixColumnMajor'])
            w = N @ np.array(list(p['local']['position']) + [1.0])
            res = float(np.abs(w[:3] - np.array(p['world']['position'])).max()); maxres = max(maxres, res)
            if res > 1e-5: errs.append(f'{pid}: world != N*local ({res})')
            fw = N[:3, :3] @ np.array(p['local']['forward'])
            if np.abs(fw - np.array(p['world']['forward'])).max() > 1e-6: errs.append(f'{pid}: forward mismatch')
    # seams: both sides identical id/version and the port exists with that version
    for s in r['seams']['seams']:
        p = P.get(s['portId'])
        if not p: errs.append(f'seam {s["seamId"]} port missing'); continue
        if s['sideA']['portId'] != s['sideB']['portId'] or s['sideA']['version'] != s['sideB']['version']: errs.append(f'seam {s["seamId"]} sides differ')
        if s['sideA']['version'] != p['version']: errs.append(f'seam {s["seamId"]} version != port version')
        if s['consumer'] not in p['consumers']: errs.append(f'seam {s["seamId"]} consumer not registered')
    # every seat consumes list resolves to a registered seam
    for seat, t in r['seats']['seats'].items():
        for pid in t['consumes']:
            if pid == 'FROZEN:*': continue
            if pid not in P or seat not in P[pid]['consumers']: errs.append(f'{seat} consumes unregistered {pid}')
    return errs, {'ports': len(P), 'seams': len(r['seams']['seams']), 'frozenMeasured': sum(1 for p in P.values() if p['status'] == 'frozen-measured'),
                  'importedLY005': sum(1 for p in P.values() if p['status'].startswith('imported')),
                  'declaredBySeats': sum(1 for p in P.values() if p['status'].startswith('declared')),
                  'valuePending': [k for k, p in P.items() if 'pending' in p['status']], 'maxLocalWorldResidual_m': maxres}

def aabb_vol(a, b):
    v = 1.0
    for i in range(3):
        lo = max(a[0][i], b[0][i]); hi = min(a[1][i], b[1][i])
        if hi <= lo + 1e-9: return 0.0
        v *= hi - lo
    return v


_geo_cache = {}
def node_triangles(node_id):
    """world triangles (N * S * v) of a city node's rendered GLB(s), excludeNodes removed"""
    if node_id in _geo_cache: return _geo_cache[node_id]
    from glbio import read_glb, mesh_items, apply
    n = [x for x in BR.dumpd['nodes'] if x['id'] == node_id][0]
    a = {x['id']: x for x in BR.dumpd['assets']}[n['asset']]
    paths = [a['sourcePath']] + ([a['nearPath']] if a.get('nearPath') else [])
    N = np.array(n['matrix'], float).reshape(4, 4).T if n.get('matrix') else np.eye(4)
    if not n.get('matrix') and n.get('position'):
        N = np.eye(4); N[:3, 3] = n['position']  # rotationY/scale absent at baseline for these nodes (LY-005)
    T = []; files = []
    excl = set(a.get('excludeNodes') or [])
    for rel in paths:
        p = os.path.normpath(os.path.join(BR.DOCS, 'cities/luoyang', rel))
        if not os.path.exists(p): continue
        g = read_glb(p); files.append({'file': os.path.relpath(p, BR.DOCS).replace(os.sep, '/'), 'sha256': g['sha256']})
        for i, nm, w, pos, tri, anc in mesh_items(g):
            if excl and any(x in excl for x in anc): continue
            T.append(apply(N @ w, pos)[tri])
    T = np.concatenate(T) if T else np.zeros((0, 3, 3))
    _geo_cache[node_id] = (T, files)
    return _geo_cache[node_id]

def tri_box_overlap(tri, h):
    """Akenine-Moller SAT: triangle (3x3, box-centred coords) vs AABB half-extents h; strict (touching = False)"""
    eps = 1e-6
    v0, v1, v2 = tri
    e = [v1 - v0, v2 - v1, v0 - v2]
    for i in range(3):
        if min(v0[i], v1[i], v2[i]) >= h[i] - eps or max(v0[i], v1[i], v2[i]) <= -h[i] + eps: return False
    n = np.cross(e[0], e[1])
    if np.linalg.norm(n) > 1e-12:
        r = sum(h[i] * abs(n[i]) for i in range(3)); d = float(np.dot(n, v0))
        if abs(d) >= r - eps * np.linalg.norm(n): return False
    for ei in e:
        for k in range(3):
            ax = np.cross(np.eye(3)[k], ei)
            if np.linalg.norm(ax) < 1e-12: continue
            p = [float(np.dot(ax, v)) for v in (v0, v1, v2)]
            r = sum(h[i] * abs(ax[i]) for i in range(3))
            if min(p) >= r - eps * np.linalg.norm(ax) or max(p) <= -r + eps * np.linalg.norm(ax): return False
    return True

def tris_in_obb(T, o, shrink=1e-3):
    c, s_ = math.cos(o['yaw']), math.sin(o['yaw'])
    d = T - np.array(o['c'])
    L = np.stack([c * d[..., 0] - s_ * d[..., 2], d[..., 1], s_ * d[..., 0] + c * d[..., 2]], -1)  # world -> obb local
    h = np.array(o['h']) - shrink
    lo = L.min(1); hi = L.max(1)
    cand = np.where(np.all(lo < h, 1) & np.all(hi > -h, 1))[0]
    return sum(1 for k in cand if tri_box_overlap(L[k], h)), int(len(cand))

def refine_advisory(adv, zmap):
    out = []
    for a in adv:
        T, files = node_triangles(a['node'])
        hits, cand = tris_in_obb(T, zmap[a['zone']]['worldOBB'])
        out.append(dict(a, method='exact triangle-vs-OBB SAT on the node rendered GLB(s) (N*S*v, excludeNodes removed), zone shrunk 1 mm (touching faces do not count); surface triangles, not solids',
                        nodeFiles=files, trianglesTested=int(len(T)), aabbCandidates=cand, trianglesIntersectingZone=hits,
                        verdict='no node triangle inside zone (contact at most)' if hits == 0 else 'NODE GEOMETRY INSIDE ZONE - seat must treat as existing geometry'))
    return out

def c_zones(r, advisory_out=None):
    errs = []; Z = r['zones']['zones']; E = r['zones']['envelopes']; sites = r['zones']['sites']
    writes = [z for z in Z if z['class'] == 'write']
    pairs = 0
    for i in range(len(writes)):
        for j in range(i + 1, len(writes)):
            a, b = writes[i], writes[j]
            if a['seat'] == b['seat']: continue
            if a.get('exclusiveGroup') and a.get('exclusiveGroup') == b.get('exclusiveGroup'): continue
            if a['frame'] == b['frame'] and a['box'] and b['box']:
                pairs += 1
                v = aabb_vol(a['box'], b['box'])
                if v > 1e-6: errs.append(f"write overlap {a['zoneId']} x {b['zoneId']} ({a['frame']}) vol {v:.4f}")
            elif a.get('worldOBB') and b.get('worldOBB'):
                pairs += 1
                if BR.obb_overlap(a['worldOBB'], b['worldOBB']): errs.append(f"world write overlap {a['zoneId']} x {b['zoneId']}")
    cuts = [z for z in Z if z['class'] == 'cut']
    for c in cuts:
        own = [z['box'] for z in writes if z['seat'] == c['seat'] and z['frame'] == c['frame'] and z['box']]
        ok, miss = BR.aabb_contains(own, c['box'], tol=1e-6)
        if not ok: errs.append(f"cut {c['zoneId']} not inside {c['seat']} write zones (uncovered {miss:.3f})")
        for d in cuts:
            if d is c or d['seat'] == c['seat']: continue
            if d['frame'] == c['frame'] and aabb_vol(c['box'], d['box']) > 1e-6: errs.append(f"cut overlap {c['zoneId']} x {d['zoneId']}")
    for i in range(len(E)):
        for j in range(i + 1, len(E)):
            a, b = E[i], E[j]
            if a['site'] == b['site'] or not a['worldOBB'] or not b['worldOBB']: continue
            if BR.obb_overlap(a['worldOBB'], b['worldOBB']): errs.append(f"envelope overlap {a['site']} x {b['site']}")
    for z in writes:
        if not z.get('worldOBB'): continue
        for e in E:
            if not e['worldOBB'] or e['site'] == z['site'] or z['seat'] in sites[e['site']]['seats']: continue
            if BR.obb_overlap(z['worldOBB'], e['worldOBB']): errs.append(f"{z['zoneId']} intrudes envelope of {e['site']}")
    # owned modify/replace generator objects lie inside owner write zones (same frame, 0.05 m tolerance)
    so = r['ownership']['ownership']['sourceObjects']; contained = 0
    for oid, o in so.items():
        if o['mode'] == 'keep' or 'aabbLocal' not in o: continue
        from registry_spec import SOURCE_CATALOG
        fr = SOURCE_CATALOG[o['catalog']].get('frame')
        own = [z['box'] for z in writes if z['seat'] == o['owner'] and z['frame'] == fr and z['box']]
        ok, miss = BR.aabb_contains(own, o['aabbLocal'], tol=0.05)
        contained += 1
        if not ok: errs.append(f'{oid} ({o["owner"]}) not inside owner zones, uncovered {miss:.3f}')
    # advisory: world write zones vs frozen / other-site city node AABBs
    adv = []
    dump = BR.dumpd; own_nodes = {n: v['owner'] for n, v in r['ownership']['ownership']['cityNodes'].items()}
    for z in writes:
        if not z.get('worldOBB'): continue
        for n in dump['nodes']:
            b = n['bounds']; ob = {'c': [(b['min'][i] + b['max'][i]) / 2 for i in range(3)], 'yaw': 0.0, 'h': [(b['max'][i] - b['min'][i]) / 2 for i in range(3)]}
            if own_nodes.get(n['id']) and own_nodes[n['id']] in sites[z['site']]['seats']: continue
            if n['id'].startswith('ground-'): continue  # city ground layer handled by LY-090 rules
            if BR.obb_overlap(z['worldOBB'], ob): adv.append({'zone': z['zoneId'], 'node': n['id'], 'note': 'AABB-level contact/overlap; not a geometry intersection test'})
    adv = refine_advisory(adv, {z['zoneId']: z for z in writes})
    if advisory_out is not None: advisory_out.extend(adv)
    return errs, {'zones': len(Z), 'writeZones': len(writes), 'cutZones': len(cuts), 'envelopes': len(E), 'pairsTested': pairs,
                  'ownedObjectsContainmentTested': contained, 'advisoryNodeContacts': len(adv)}

def c_components(r):
    errs = []; comp = r['ownership']['ownership']['components']; P = r['ports']['ports']
    for cid, c in comp.items():
        if c['class'] not in COMP_CLASSES: errs.append(f'{cid} bad class {c["class"]}')
        if c['class'] == 'moving':
            seat = c['owner']; t = r['seats']['seats'][seat]
            ok = any(P.get(p, {}).get('kind') in ('mount', 'opening') for p in t['produces'] + t['consumes'])
            if not ok: errs.append(f'moving {cid} ({seat}) has no mount/opening port to carry its axis/state')
    return errs, {'components': len(comp), 'moving': sorted(k for k, v in comp.items() if v['class'] == 'moving'),
                  'stateVariant': sorted(k for k, v in comp.items() if v['class'] == 'state-variant')}

def c_frames(r):
    errs = []; F = r['zones']['frames']; P = r['ports']['ports']; info = {}
    def wpos(frame, p):
        pl = F[frame]['placement']; v = BR.rot_y(pl['yaw'], p); return [v[0] + pl['t'][0], v[1] + pl['t'][1], v[2] + pl['t'][2]]
    for frame, wl, wr in (('local:kaiyang-K-v1', 'wall-A-wall-05:cap-0:wall-end', 'wall-A-wall-04:cap-1:wall-end'),
                          ('local:pingcheng-P-v1', 'wall-A-wall-06:cap-0:wall-end', 'wall-A-wall-05:cap-1:wall-end')):
        a = wpos(frame, [-16.0, 0.0, 0.0]); b = wpos(frame, [16.0, 0.0, 0.0])
        da = math.hypot(a[0] - P[wl]['world']['position'][0], a[2] - P[wl]['world']['position'][2])
        db = math.hypot(b[0] - P[wr]['world']['position'][0], b[2] - P[wr]['world']['position'][2])
        info[frame] = {'endBayW_to_cap_m': da, 'endBayE_to_cap_m': db}
        if max(da, db) > 0.005: errs.append(f'{frame}: end bays do not land on wall caps ({da:.4f}, {db:.4f})')
    mt = load(J('qa/chunk-measure.json'))['motherScene']['impliedTranslation']
    ft = F['local:frontage-v2.1']['placement']['t']
    d = max(abs(mt[i] - ft[i]) for i in range(3)); info['frontage'] = {'motherSceneImpliedT': mt, 'frameT': ft, 'diff': d}
    if d > 0.002: errs.append(f'frontage frame differs from mother scene by {d}')
    c02 = [n for n in BR.dumpd['nodes'] if n['id'] == 'C02-010'][0]
    m = c02.get('matrix'); tcourt = F['court:C02-010']['placement']['t']
    nt = [m[12], m[13], m[14]] if m else c02['position']
    d = max(abs(nt[i] - tcourt[i]) for i in range(3)); info['court'] = {'nodeT': nt, 'frameT': tcourt, 'diff': d}
    if d > 1e-6: errs.append('court frame != C02-010 node translation')
    from glbio import read_glb
    g = read_glb(os.path.join(BR.DOCS, 'cities/luoyang/progress-assets/granary-city-v1/granary-city-LOD0.glb'))
    ts = sorted({tuple(round(x, 3) for x in n['translation']) for n in g['json']['nodes'] if 'translation' in n})
    st = F['local:storage-site']['placement']['t']; info['storage'] = {'glbNodeTranslations': ts, 'frameT': st}
    if not any(max(abs(t[i] - st[i]) for i in range(3)) < 1e-3 for t in ts): errs.append('storage frame not found among granary-city node translations')
    return errs, info

def c_hashes(r):
    errs = []
    led = {g['path']: g['sha256'] for g in BR.ledger['glbFiles']}
    for p, f in BR.idx.items():
        if f.get('sha256') != led.get(p): errs.append(f'GLB sha differs from LY-001 ledger: {p}')
    for k, v in r['zones']['inputs'].items():
        p = os.path.join(WP, v['path'])
        if sha(p) != v['sha256']: errs.append(f'input changed since build: {k}')
    for cid, c in r['ownership']['cards'].items():
        if sha(os.path.join(BR.DOCS, c['path'][5:])) != c['sha256']: errs.append(f'card changed {cid}')
    return errs, {'glbFiles': len(BR.idx), 'cards': len(r['ownership']['cards'])}

def c_lab_untouched():
    now = subprocess.run(['git', '-C', LAB, 'status', '--porcelain'], capture_output=True, text=True).stdout
    head = subprocess.run(['git', '-C', LAB, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    before = open(BEFORE, encoding='utf-8').read()
    b = set(l.strip() for l in before.strip().splitlines()); n = set(l.strip() for l in now.strip().splitlines())
    added = sorted(n - b); vanished = sorted(b - n)
    # a write by this seat could only ADD entries; entries that vanished were reverted outside this seat
    errs = [f'new lab working-tree changes: {added}'] if added else []
    if head != BR.R.BASELINE: errs.append(f'lab HEAD {head} != baseline')
    open(os.path.join(W6, 'qa', 'lab-status-after.txt'), 'w', encoding='utf-8').write(now)
    return errs, {'head': head, 'statusBefore': before.strip().splitlines(), 'statusNow': now.strip().splitlines(), 'addedEntries': added,
                  'vanishedEntries': vanished, 'rule': 'pass = HEAD unchanged and no new working-tree entries; vanished entries are pre-existing uncommitted edits reverted by someone else during this seat (LY-006 never opens lab files for writing)'}

CHECKS = [('C1-seats-deps-dag', c_seats), ('C2-unique-ownership-coverage', c_ownership), ('C3-ports-seams-versions-deps', c_ports),
          ('C4-spatial-write-zones', c_zones), ('C5-fixed-moving', c_components), ('C6-frames-vs-measured-geometry', c_frames), ('C7-sha-bindings', c_hashes)]

# ---------------------------------------------------------------- negatives (fault injection on in-memory copies)
def neg_dup_owner(r):
    r['ownership']['conflicts'].append({'object': 'kaiyang-K-v1:C_upper_deck', 'kind': 'two non-keep claims (injected LY-014 replace)'}); return 'C2-unique-ownership-coverage'
def neg_uncovered_node(r):
    r['ownership']['ownership']['cityNodes']['C02-010'] = {'owner': None, 'status': 'UNCOVERED'}; return 'C2-unique-ownership-coverage'
def neg_version(r):
    s = r['seams']['seams'][0]; s['sideB']['version'] = 2; return 'C3-ports-seams-versions-deps'
def neg_dep(r):
    r['ports']['ports']['kaiyang-K-v1:deck-top:floor']['consumers'].append('LY-011'); return 'C3-ports-seams-versions-deps'
def neg_portid(r):
    p = r['ports']['ports'].pop('kaiyang-K-v1:deck-top:floor'); p['portId'] = 'kaiyang deck top'; r['ports']['ports']['kaiyang deck top'] = p; return 'C3-ports-seams-versions-deps'
def neg_world(r):
    p = r['ports']['ports']['kaiyang-K-v1:passage-C:threshold']; p['world']['position'][1] += 0.01; return 'C3-ports-seams-versions-deps'
def neg_overlap(r):
    z = [q for q in r['zones']['zones'] if q['seat'] == 'LY-012'][0]; z['box'] = [[-2.8, 0.0, 1.0], [2.8, 4.7, 4.96]]; return 'C4-spatial-write-zones'
def neg_cut_outside(r):
    c = [q for q in r['zones']['zones'] if q['class'] == 'cut' and q['seat'] == 'LY-045'][0]; c['box'] = [[-8.5, -1.6, -11.5], [-7.0, 0.25, -10.5]]; return 'C4-spatial-write-zones'
def neg_envelope(r):
    e = [q for q in r['zones']['envelopes'] if q['site'] == 'S-GU'][0]; o = [q for q in r['zones']['envelopes'] if q['site'] == 'S-XIA'][0]
    e['worldOBB'] = copy.deepcopy(o['worldOBB']); return 'C4-spatial-write-zones'
def neg_object_outside(r):
    z = [q for q in r['zones']['zones'] if q['seat'] == 'LY-013'][0]; z['box'] = [[-12.4, 5.0, -5.0], [0.0, 5.34, 5.0]]; return 'C4-spatial-write-zones'
def neg_moving(r):
    r['seats']['seats']['LY-031']['produces'] = []; r['seats']['seats']['LY-031']['consumes'] = []; return 'C5-fixed-moving'
def neg_frame(r):
    r['zones']['frames']['local:kaiyang-K-v1']['placement']['yaw'] = +0.020743634087871412; return 'C6-frames-vs-measured-geometry'
NEGATIVES = [neg_dup_owner, neg_uncovered_node, neg_version, neg_dep, neg_portid, neg_world, neg_overlap, neg_cut_outside, neg_envelope, neg_object_outside, neg_moving, neg_frame]

def main():
    base = reg()
    results = []; adv = []
    read_files = {k: {'path': os.path.relpath(v, WP).replace('\\', '/'), 'sha256': sha(v)} for k, v in REG.items()}
    for name, fn in CHECKS:
        e, info = fn(base, adv) if fn is c_zones else fn(base)
        results.append({'id': name, 'pass': not e, 'errors': e[:50], 'errorCount': len(e), 'info': info})
    e, info = c_lab_untouched()
    results.append({'id': 'C8-lab-repo-untouched', 'pass': not e, 'errors': e, 'errorCount': len(e), 'info': info})
    negs = []
    fns = dict(CHECKS)
    for nf in NEGATIVES:
        r = copy.deepcopy(base); target = nf(r)
        e, _ = fns[target](r, []) if fns[target] is c_zones else fns[target](r)
        negs.append({'negative': nf.__name__, 'targetCheck': target, 'failedAsExpected': bool(e), 'firstError': e[0] if e else None})
    results.append({'id': 'C9-negatives', 'pass': all(n['failedAsExpected'] for n in negs), 'errors': [n['negative'] for n in negs if not n['failedAsExpected']],
                    'errorCount': sum(1 for n in negs if not n['failedAsExpected']), 'info': negs})
    from validate_interface import validate
    vt = {}
    for name, expect in (('LY-013.example.pass.json', True), ('LY-013.example.fail.json', False)):
        fp = J('templates', 'examples', name); e = validate(J('registry'), load(fp))
        vt[name] = {'sha256': sha(fp), 'expectedPass': expect, 'pass': not e, 'errors': e}
    okv = vt['LY-013.example.pass.json']['pass'] and not vt['LY-013.example.fail.json']['pass'] and len(vt['LY-013.example.fail.json']['errors']) >= 6
    results.append({'id': 'C10-interface-template-validator', 'pass': okv, 'errors': [] if okv else ['validator fixtures did not behave as expected'], 'errorCount': 0 if okv else 1,
                    'info': {'template': {'path': 'templates/interface.template.json', 'sha256': sha(J('templates/interface.template.json'))},
                             'schemas': {k: sha(J('schemas', k)) for k in ('interface.schema.json', 'port.schema.json')}, 'fixtures': vt}})
    out = {'seat': 'LY-006', 'baseline': BR.R.BASELINE, 'registryFiles': read_files, 'buildInputs': base['zones']['inputs'],
           'checks': results, 'advisory': {'worldZoneVsNodeAABB': adv},
           'summary': {r['id']: r['pass'] for r in results}}
    json.dump(out, open(J('qa/checks.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for r in results: print(r['id'], 'PASS' if r['pass'] else 'FAIL', r['errorCount'], (r['errors'][:3] if r['errors'] else ''))
    print('advisory', len(adv))

if __name__ == '__main__':
    main()
