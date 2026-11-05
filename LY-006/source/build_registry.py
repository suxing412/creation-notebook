# -*- coding: utf-8 -*-
# LY-006 registry builder. Resolves registry_spec.py against measured files and writes registry/*.json.
# Read-only on the lab repo. Usage (from LY-006/):
#   python -I source/build_registry.py <LY-006 dir> <lab docs dir>
import json, sys, os, re, hashlib, math, itertools
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import registry_spec as R

W6 = sys.argv[1]; DOCS = sys.argv[2]
WP = os.path.dirname(os.path.abspath(W6))
J = lambda *p: os.path.join(W6, *p)
def load(p): return json.load(open(p, encoding='utf-8'))
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
def dump(obj, rel):
    os.makedirs(os.path.dirname(J(rel)), exist_ok=True)
    json.dump(obj, open(J(rel), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

INPUTS = {
    'taskboard': os.path.join(WP, 'taskboard.json'),
    'ly001_ledger': os.path.join(WP, 'LY-001/qa/snapshot-ledger.json'),
    'ly001_dump': os.path.join(WP, 'LY-001/qa/city-data.dump.json'),
    'ly005_ports': os.path.join(WP, 'LY-005/qa/ports-bce3211.json'),
    'ly005_contract': os.path.join(WP, 'LY-005/coordinate-contract.json'),
    'ly005_port_schema': os.path.join(WP, 'LY-005/port-schema.json'),
    'glb_index': J('qa/glb-node-index.json'),
    'wall_ends': J('qa/wall-end-ports.measure.json'),
    'probes': J('qa/frozen-ports.probes.json'),
    'chunks': J('qa/chunk-measure.json'),
    'court_free': J('qa/court-A2-free-space.json'),
    'k_objects': J('qa/source-objects/kaiyang-K-v1.objects.json'),
    'p_objects': J('qa/source-objects/pingcheng-P-v1.objects.json'),
    'k_trial': J('qa/kaiyang-hidden-trial.objects.json'),
    'p_trial': J('qa/pingcheng-hidden-trial.objects.json'),
    'frontage_openings': J('qa/frontage-openings.from-LY-021-prep.json'),
    'spec': J('source/registry_spec.py'),
}
board = load(INPUTS['taskboard']); seats_board = {s['id']: s for s in board['seats']}
ledger = load(INPUTS['ly001_ledger']); dumpd = load(INPUTS['ly001_dump'])
idx = load(INPUTS['glb_index'])['files']
walls = load(INPUTS['wall_ends']); probes = load(INPUTS['probes']); chunks = load(INPUTS['chunks'])
ly5 = load(INPUTS['ly005_ports'])
SPEC = R.SPEC()
SEATS = [f'LY-{i:03d}' for i in range(11, 91)]

# ---------------------------------------------------------------- geometry helpers
def place(frame):
    f = R.FRAMES.get(frame)
    if frame == 'world': return {'t': [0, 0, 0], 'yaw': 0.0}
    return f['placement'] if f else None

def rot_y(yaw, v):
    c, s = math.cos(yaw), math.sin(yaw)
    return [c * v[0] + s * v[2], v[1], -s * v[0] + c * v[2]]

def to_world(frame, p):
    pl = place(frame)
    if pl is None: return None
    r = rot_y(pl['yaw'], p)
    return [r[0] + pl['t'][0], r[1] + pl['t'][1], r[2] + pl['t'][2]]

def mat_col_major(frame):
    pl = place(frame)
    if pl is None: return None
    c, s = math.cos(pl['yaw']), math.sin(pl['yaw'])
    t = pl['t']
    return [c, 0, -s, 0, 0, 1, 0, 0, s, 0, c, 0, t[0], t[1], t[2], 1]

def box_to_obb(frame, box):
    """local AABB -> world OBB {c, yaw, h} (yaw-only) or None if frame unplaced"""
    pl = place(frame)
    if pl is None: return None
    (x0, y0, z0), (x1, y1, z1) = box
    c = to_world(frame, [(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return {'c': c, 'yaw': pl['yaw'], 'h': [(x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2]}

def obb_corners_xz(o):
    c, s = math.cos(o['yaw']), math.sin(o['yaw'])
    ax = np.array([c, -s]); az = np.array([s, c])  # world (x,z) of local x and local z axes
    C = np.array([o['c'][0], o['c'][2]])
    return [C + sx * o['h'][0] * ax + sz * o['h'][2] * az for sx in (-1, 1) for sz in (-1, 1)], (ax, az)

def obb_overlap(a, b, shrink=1e-4):
    """positive-volume overlap test (touching faces = no overlap)"""
    if a['c'][1] + a['h'][1] - shrink <= b['c'][1] - b['h'][1] or b['c'][1] + b['h'][1] - shrink <= a['c'][1] - a['h'][1]:
        return False
    A = dict(a, h=[max(a['h'][0] - shrink, 0), a['h'][1], max(a['h'][2] - shrink, 0)])
    Bb = dict(b, h=[max(b['h'][0] - shrink, 0), b['h'][1], max(b['h'][2] - shrink, 0)])
    ca, axa = obb_corners_xz(A); cb, axb = obb_corners_xz(Bb)
    for ax in list(axa) + list(axb):
        pa = [float(np.dot(p, ax)) for p in ca]; pb = [float(np.dot(p, ax)) for p in cb]
        if max(pa) <= min(pb) or max(pb) <= min(pa): return False
    return True

def aabb_overlap_vol(a, b):
    v = 1.0
    for i in range(3):
        lo = max(a[0][i], b[0][i]); hi = min(a[1][i], b[1][i])
        if hi <= lo: return 0.0
        v *= hi - lo
    return v

def aabb_contains(outer_list, inner, tol=0.05):
    """inner AABB covered by the union of outer AABBs (grid sampling at 0.05 m on the inner box)"""
    xs = np.linspace(inner[0][0] + 1e-6, inner[1][0] - 1e-6, max(2, int((inner[1][0] - inner[0][0]) / 0.05) + 1))
    ys = np.linspace(inner[0][1] + 1e-6, inner[1][1] - 1e-6, max(2, int((inner[1][1] - inner[0][1]) / 0.25) + 1))
    zs = np.linspace(inner[0][2] + 1e-6, inner[1][2] - 1e-6, max(2, int((inner[1][2] - inner[0][2]) / 0.05) + 1))
    G = np.array(np.meshgrid(xs, ys, zs, indexing='ij')).reshape(3, -1).T
    ok = np.zeros(len(G), bool)
    for o in outer_list:
        lo = np.array(o[0]) - tol; hi = np.array(o[1]) + tol
        ok |= np.all((G >= lo) & (G <= hi), axis=1)
    return bool(ok.all()), float(1 - ok.mean())

def subtract_boxes(box, minus, res=None):
    """exact: box minus plan footprints of `minus` boxes that overlap it in y (coordinate compression),
    returned as merged rectangles with the box's y range"""
    (x0, y0, z0), (x1, y1, z1) = box
    ms = [m for m in minus if m[1][1] > y0 and m[0][1] < y1]
    xs = sorted({x0, x1} | {min(max(v, x0), x1) for m in ms for v in (m[0][0], m[1][0])})
    zs = sorted({z0, z1} | {min(max(v, z0), z1) for m in ms for v in (m[0][2], m[1][2])})
    nx, nz = len(xs) - 1, len(zs) - 1
    keep = np.ones((nz, nx), bool)
    for j in range(nz):
        for i in range(nx):
            cx = (xs[i] + xs[i + 1]) / 2; cz = (zs[j] + zs[j + 1]) / 2
            if xs[i + 1] - xs[i] < 1e-9 or zs[j + 1] - zs[j] < 1e-9: keep[j, i] = False; continue
            if any(m[0][0] < cx < m[1][0] and m[0][2] < cz < m[1][2] for m in ms): keep[j, i] = False
    rects = []; used = np.zeros_like(keep)
    for j in range(nz):
        i = 0
        while i < nx:
            if keep[j, i] and not used[j, i]:
                i1 = i
                while i1 < nx and keep[j, i1] and not used[j, i1]: i1 += 1
                j1 = j
                while j1 + 1 < nz and keep[j1 + 1, i:i1].all() and not used[j1 + 1, i:i1].any(): j1 += 1
                used[j:j1 + 1, i:i1] = True
                rects.append([[round(xs[i], 6), y0, round(zs[j], 6)], [round(xs[i1], 6), y1, round(zs[j1 + 1], 6)]])
                i = i1
            else:
                i += 1
    return rects

# ---------------------------------------------------------------- special footprints
def file_aabb(path_rel):
    f = idx[path_rel]; mn = [1e9] * 3; mx = [-1e9] * 3
    for n in f['nodes']:
        if 'aabb' in n:
            mn = [min(a, b) for a, b in zip(mn, n['aabb'][0])]; mx = [max(a, b) for a, b in zip(mx, n['aabb'][1])]
    return [mn, mx]
MKT_T = R.FRAMES['local:market-site']['placement']['t']
def routes_local():
    out = []
    for n in idx['cities/luoyang/assets/market/market-cluster.glb']['nodes']:
        if n['name'].startswith('route_') and 'aabb' in n:
            (a, b) = n['aabb']
            out.append((n['name'], [[a[0] - MKT_T[0], a[1], a[2] - MKT_T[2]], [b[0] - MKT_T[0], b[1], b[2] - MKT_T[2]]]))
    return out
SPECIAL = {
    '__routes__': [b for _, b in routes_local()],
    '__mingtang_B_core__': [file_aabb('library/models/m-luoyang-mingtang/files/mingtang-B-LOD0.glb')],
}

# ---------------------------------------------------------------- zones resolution
zones = []
def add_zone(seat, z, boxes, extra=None):
    for k, bx in enumerate(boxes):
        rec = {'zoneId': f"{seat}:{z['class']}:{len([q for q in zones if q['seat'] == seat]) + 1:03d}", 'seat': seat, 'site': SPEC[seat]['site'],
               'class': z['class'], 'frame': z['frame'], 'box': [[round(v, 4) for v in bx[0]], [round(v, 4) for v in bx[1]]],
               'label': z['label'], 'basis': z['basis'], 'exclusiveGroup': z.get('exclusiveGroup')}
        rec['worldOBB'] = box_to_obb(z['frame'], bx) if z['frame'] != 'world' else {'c': [(bx[0][i] + bx[1][i]) / 2 for i in range(3)], 'yaw': 0.0, 'h': [(bx[1][i] - bx[0][i]) / 2 for i in range(3)]}
        if extra: rec.update(extra)
        zones.append(rec)

def wall_face_bands(halfw, yr):
    """2 m-type foot bands outside each long vertical side face of every A-wall prism (world OBBs)"""
    from glbio import read_glb, mesh_items, apply
    bands = []
    for n in dumpd['nodes']:
        if not n['id'].startswith('wall-A-'): continue
        a = {x['id']: x for x in dumpd['assets']}[n['asset']]
        g = read_glb(os.path.join(DOCS, 'cities/luoyang', a['sourcePath']))
        for i, nm, w, pos, tri, anc in mesh_items(g):
            V = apply(w, pos)
            for t in tri:
                A, Bv, Cv = V[t]
                nrm = np.cross(Bv - A, Cv - A); L = np.linalg.norm(nrm)
                if L < 1e-9: continue
                nrm /= L
                if abs(nrm[1]) > 0.05: continue
                P = np.array([A, Bv, Cv])[:, [0, 2]]
                span = max(np.linalg.norm(P[0] - P[1]), np.linalg.norm(P[0] - P[2]), np.linalg.norm(P[1] - P[2]))
                if span < 12: continue
                # take the face's base edge (lowest two verts)
                Q = np.array([A, Bv, Cv]); lo = Q[np.argsort(Q[:, 1])][:2]
                if abs(lo[0][1] - lo[1][1]) > 1e-3 or np.linalg.norm(lo[0][[0, 2]] - lo[1][[0, 2]]) < 12: continue
                d = lo[1][[0, 2]] - lo[0][[0, 2]]; Ld = np.linalg.norm(d); u = d / Ld
                hn = np.array([nrm[0], nrm[2]]); hn /= np.linalg.norm(hn)
                mid = (lo[0][[0, 2]] + lo[1][[0, 2]]) / 2 + hn * halfw / 2
                yaw = -math.atan2(u[1], u[0])  # local +x -> u
                bands.append({'node': n['id'], 'c': [float(mid[0]), (yr[0] + yr[1]) / 2, float(mid[1])], 'yaw': yaw,
                              'h': [Ld / 2, (yr[1] - yr[0]) / 2, halfw / 2]})
    # dedupe (two triangles per face share the base edge)
    out = []
    for b in bands:
        if not any(abs(b['c'][0] - o['c'][0]) < 1e-3 and abs(b['c'][2] - o['c'][2]) < 1e-3 for o in out): out.append(b)
    return out

def seam_obb(seam_key, half_depth, yr):
    wa, wb = seam_key.split(':', 1)[1].split('/')
    for s in walls['seams']:
        pair = {s['a'][0], s['b'][0]}
        if pair == {wa, wb}:
            ca = walls['walls'][s['a'][0]]['caps'][s['a'][1]]; cb = walls['walls'][s['b'][0]]['caps'][s['b'][1]]
            pa = np.array(ca['baseCenter'])[[0, 2]]; pb = np.array(cb['baseCenter'])[[0, 2]]
            u = (pb - pa) / np.linalg.norm(pb - pa); mid = (pa + pb) / 2
            return {'c': [float(mid[0]), (yr[0] + yr[1]) / 2, float(mid[1])], 'yaw': -math.atan2(u[1], u[0]),
                    'h': [float(np.linalg.norm(pb - pa) / 2), (yr[1] - yr[0]) / 2, half_depth]}
    raise KeyError(seam_key)

for seat in SEATS:
    for z in SPEC[seat].get('zones', []):
        if 'wallFootBands' in z:
            for b in wall_face_bands(z['halfWidth'], z['y']):
                zones.append({'zoneId': f"{seat}:write:{len([q for q in zones if q['seat'] == seat]) + 1:03d}", 'seat': seat, 'site': SPEC[seat]['site'], 'class': 'write',
                              'frame': 'world', 'box': None, 'worldOBB': b, 'label': f"{z['label']} ({b['node']})", 'basis': z['basis'], 'exclusiveGroup': None})
        elif 'cornerSeam' in z:
            wa, ia, wb, ib = z['cornerSeam']
            ca = walls['walls'][wa]['caps'][ia]; cb = walls['walls'][wb]['caps'][ib]
            pts = np.array([ca['baseCenter'], cb['baseCenter']])
            lo = pts.min(0) - 4.0; hi = pts.max(0) + 4.0
            add_zone(seat, z, [[[lo[0], z['y'][0], lo[2]], [hi[0], z['y'][1], hi[2]]]])
        elif 'fromNodes' in z:
            path, rx = z['fromNodes']
            for n in idx[path]['nodes']:
                if re.search(rx, n['name']) and 'aabb' in n and n['name'].endswith('static_earth'):
                    (a, b) = n['aabb']; e = z['endBand']
                    long_z = (b[2] - a[2]) >= (b[0] - a[0])
                    if long_z:
                        bx = [[[a[0], z['y'][0], a[2] - e], [b[0], z['y'][1], a[2]]], [[a[0], z['y'][0], b[2]], [b[0], z['y'][1], b[2] + e]]]
                    else:
                        bx = [[[a[0] - e, z['y'][0], a[2]], [a[0], z['y'][1], b[2]]], [[b[0], z['y'][0], a[2]], [b[0] + e, z['y'][1], b[2]]]]
                    add_zone(seat, dict(z, label=f"{z['label']} [{n['name']}]"), bx, {'measuredFrom': {'file': 'docs/' + path, 'sha256': idx[path]['sha256'], 'node': n['name']}})
        elif 'minusSeats' in z:
            pass  # second pass
        else:
            add_zone(seat, z, [z['box']])
for seat in SEATS:
    for z in SPEC[seat].get('zones', []):
        if 'minusSeats' in z:
            minus = []
            for m in z['minusSeats']:
                if m in SPECIAL: minus += SPECIAL[m]
                else: minus += [q['box'] for q in zones if q['seat'] == m and q['frame'] == z['frame'] and q['box'] and q['class'] == 'write']
            add_zone(seat, z, subtract_boxes(z['box'], minus), {'derivedFrom': {'box': z['box'], 'minus': z['minusSeats']}})

# site envelopes
envelopes = []
for sid, site in R.SITES.items():
    e = site.get('envelope')
    if not e: continue
    if e['frame'].startswith('wallseam:'):
        o = seam_obb(e['frame'], e['halfDepth'], e['y'])
        envelopes.append({'site': sid, 'owner': site['owner'], 'frame': 'world', 'worldOBB': o, 'from': e['frame']})
    elif 'boxes' in e:
        for bx in e['boxes']:
            envelopes.append({'site': sid, 'owner': site['owner'], 'frame': e['frame'], 'box': bx,
                              'worldOBB': {'c': [(bx[0][i] + bx[1][i]) / 2 for i in range(3)], 'yaw': 0.0, 'h': [(bx[1][i] - bx[0][i]) / 2 for i in range(3)]}})
    else:
        envelopes.append({'site': sid, 'owner': site['owner'], 'frame': e['frame'], 'box': e['box'],
                          'worldOBB': box_to_obb(e['frame'], e['box']) if e['frame'] != 'world' else {'c': [(e['box'][0][i] + e['box'][1][i]) / 2 for i in range(3)], 'yaw': 0.0, 'h': [(e['box'][1][i] - e['box'][0][i]) / 2 for i in range(3)]}})

# ---------------------------------------------------------------- source objects
def catalog_objects(key):
    c = R.SOURCE_CATALOG[key]
    if c['kind'] == 'generator-objects':
        d = load(J(c['objects']))
        objs = {}
        for name, v in d.items():
            if name.startswith('__'): continue
            l0 = v.get('LOD0') or list(v.values())[0]
            objs[name] = {'aabbLocal': l0['aabb'], 'lods': {k: {'mesh': x['mesh'], 'triangle_range': x['triangle_range']} for k, x in v.items()}}
        files = {k: {'path': x['path'].split('docs/')[-1], 'sha256': x['sha256']} for k, x in d['__glb__'].items()}
        return objs, files, {'rangesFile': c['objects'], 'rangesSha256': d['__ranges__']['sha256']}
    if c['kind'] == 'glb-nodes':
        objs = {}; files = {}
        for p, f in idx.items():
            if any(re.search(rx, p) for rx in c['glbs']):
                files[p] = {'path': p, 'sha256': f['sha256']}
                for n in f['nodes']:
                    if 'aabb' not in n: continue
                    if any(re.search(e, n['name']) for e in c.get('except', [])): continue
                    o = objs.setdefault(n['name'], {'files': []}); o['files'].append(p)
        if not files: raise RuntimeError(f'catalog {key}: no GLB matched {c["glbs"]}')
        return objs, files, {}
    if c['kind'] == 'listed':
        return {o: {} for o in c['objects']}, {}, {'evidence': c.get('evidence')}
    if c['kind'] == 'external':
        return {key: {}}, {}, {'note': c['note']}

ownership = {'sourceObjects': {}, 'cityNodes': {}, 'groundPieces': {}, 'cuts': {}, 'cardFields': {}, 'components': {}, 'dataObjects': {}, 'hiddenTrials': {}}
conflicts = []
claims = {}
for seat in SEATS:
    for (key, rx, mode) in SPEC[seat].get('sourceObjects', []):
        claims.setdefault(key, []).append((seat, rx, mode))
catalog_files = {}
for key in R.SOURCE_CATALOG:
    objs, files, meta = catalog_objects(key)
    catalog_files[key] = {'files': files, **meta}
    for name, info in objs.items():
        oid = f'{key}:{name}'
        hits = [(s, rx, m) for (s, rx, m) in claims.get(key, []) if re.search(rx, name)]
        strong = [h for h in hits if h[2] != 'keep']; weak = [h for h in hits if h[2] == 'keep']
        if len(strong) > 1: conflicts.append({'object': oid, 'claims': strong, 'kind': 'two non-keep claims'})
        if len(weak) > 1 and not strong: conflicts.append({'object': oid, 'claims': weak, 'kind': 'two keep claims'})
        win = strong[0] if strong else (weak[0] if weak else None)
        rec = {'owner': win[0] if win else None, 'mode': win[2] if win else 'unclaimed', 'catalog': key, 'card': R.SOURCE_CATALOG[key].get('card')}
        rec.update({k: v for k, v in info.items() if k in ('aabbLocal', 'files')})
        if 'lods' in info: rec['lods'] = info['lods']
        rec['readers'] = sorted({h[0] for h in hits} - ({win[0]} if win else set()))
        ownership['sourceObjects'][oid] = rec
# every claim must match something
for key, cl in claims.items():
    if key not in R.SOURCE_CATALOG: conflicts.append({'object': key, 'kind': 'claim on unknown catalog', 'claims': cl}); continue
    for (s, rx, m) in cl:
        if not any(o.startswith(key + ':') and ownership['sourceObjects'][o]['owner'] == s for o in ownership['sourceObjects']) and \
           not any(o.startswith(key + ':') and re.search(rx, o.split(':', 1)[1]) for o in ownership['sourceObjects']):
            conflicts.append({'object': key, 'kind': 'claim matches no object', 'claims': [(s, rx, m)]})

# city nodes + research models + hidden trials
all_nodes = [n['id'] for n in dumpd['nodes']] + [r['id'] for r in dumpd['researchModels']]
node_claims = {}
for seat in SEATS:
    for nid in SPEC[seat].get('cityNodes', []) + SPEC[seat].get('researchModels', []):
        node_claims.setdefault(nid, []).append(seat)
for nid in all_nodes:
    cl = node_claims.get(nid, [])
    if len(cl) > 1: conflicts.append({'object': nid, 'kind': 'city node claimed twice', 'claims': cl})
    if cl: rec = {'owner': cl[0], 'status': 'owned (proposal rights only; LY-100 writes city-data)'}
    elif nid in R.NODE_FROZEN_REASONS: rec = {'owner': None, 'status': 'frozen', 'reason': R.NODE_FROZEN_REASONS[nid]}
    elif nid.startswith('C02-') or nid.startswith('FROZEN-D08'): rec = {'owner': None, 'status': 'frozen', 'reason': R.COURT_FROZEN_REASON}
    else: rec = {'owner': None, 'status': 'UNCOVERED'}
    ownership['cityNodes'][nid] = rec
for nid in node_claims:
    if nid not in all_nodes: conflicts.append({'object': nid, 'kind': 'claimed node not in city-data dump', 'claims': node_claims[nid]})
pkgs = sorted({h['package'] for h in ledger['hiddenTrials']})
HT = {'luoyang-kaiyang-gate-study-v1': 'LY-015', 'luoyang-pingcheng-gate-study-v1': 'LY-017'}
for p in pkgs:
    ownership['hiddenTrials'][p] = {'owner': HT.get(p), 'status': 'owned' if p in HT else 'frozen',
                                    'reason': None if p in HT else ('13院压缩（保护）' if 'court' in p or 'north-' in p else '十二门本体/雍门（不在 011-090）')}

# ground pieces
for gid, (frx, nrx) in R.GROUND_PIECES.items():
    hits = [(p, n['name']) for p, f in idx.items() if re.search(frx, p) for n in f['nodes'] if 'aabb' in n and re.search(nrx, n['name'])]
    owners = [s for s in SEATS if gid in SPEC[s].get('groundPieces', [])]
    if len(owners) != 1: conflicts.append({'object': gid, 'kind': f'ground piece owners={owners}'})
    if not hits: conflicts.append({'object': gid, 'kind': 'ground piece matches no GLB node'})
    ownership['groundPieces'][gid] = {'owner': owners[0] if owners else None, 'instances': [{'file': 'docs/' + p, 'sha256': idx[p]['sha256'], 'node': n} for p, n in hits]}
for nid in ('ground-network-ground-stitched', 'ground-retained', 'ground-south', 'ground-D08'):
    ownership['groundPieces']['gp:city-node:' + nid] = {'owner': ownership['cityNodes'][nid]['owner'], 'instances': [{'cityNode': nid}],
                                                         'rule': 'only LY-090 may emit a diff/replacement of this file; all cut requests go through LY-090'}
for seat in SEATS:
    for g in SPEC[seat].get('groundPieces', []):
        if g.startswith('gp:LY-'):
            ownership['groundPieces'][g] = {'owner': seat, 'instances': [], 'rule': 'new ground piece in the owner namespace'}
ownership['groundPiecesFrozen'] = R.GROUND_FROZEN
ownership['newGroundNamespaceRule'] = 'any new ground piece must be named gp:<seat>:<name> and lie inside one of that seat write zones'

# cuts
for seat in SEATS:
    for c in SPEC[seat].get('cuts', []):
        if c in ownership['cuts']: conflicts.append({'object': c, 'kind': 'cut declared twice'})
        cz = [z['zoneId'] for z in zones if z['seat'] == seat and z['class'] == 'cut']
        ownership['cuts'][c] = {'requester': seat, 'composer': 'LY-090' if c != 'cut:LY-086:waterway-wall-block' else 'LY-086 (own wall research block; LY-090 only if a city ground opening is ever added)',
                                'cutZones': cz}

# components
for seat in SEATS:
    for (cid, cls) in SPEC[seat].get('components', []):
        if cid in ownership['components']: conflicts.append({'object': cid, 'kind': 'component declared twice'})
        ownership['components'][cid] = {'owner': seat, 'class': cls}
# data objects
for seat in SEATS:
    for d in SPEC[seat].get('dataObjects', []):
        ownership['dataObjects'][d] = {'owner': seat}

# card fields
cards = {c['id']: c for c in ledger['cards']}
lab_cards = {}
for cid, c in cards.items():
    p = os.path.join(DOCS, c['card'])
    if os.path.exists(p):
        lab_cards[cid] = {'path': 'docs/' + c['card'], 'sha256': sha(p), 'data': load(p)}
card_owner = {}
for seat in SEATS:
    for cid in SPEC[seat].get('cards', []):
        if cid in card_owner: conflicts.append({'object': cid, 'kind': 'card owned twice', 'claims': [card_owner[cid], seat]})
        card_owner[cid] = seat
        if cid not in cards: conflicts.append({'object': cid, 'kind': 'card id not in LY-001 ledger'})
CARD_SCOPE = [cid for cid in cards if cid.startswith('m-luoyang') or cid in ('m-market-functional', 'm-storage-functional', 'm-well-family', 'm-courtyard-family',
                                                                            'm-passage-interface', 'm-eaves-shell', 'm-gate-roof-study', 'p-luoyang')]
for cid in CARD_SCOPE:
    data = lab_cards.get(cid, {}).get('data', {})
    fields = [k for k in data if k != 'notes'] + ['notes.' + k for k in data.get('notes', {})]
    owner = card_owner.get(cid)
    for f in sorted(set(fields) | set(R.CARD_PROPOSAL_FIELDS) | {'notes.*'}):
        if cid == 'p-luoyang':
            rec = {'owner': 'LY-100', 'status': 'outside 011-090 (shared project card; only LY-100 writes; LY-098 audits text)'}
        elif f in R.CARD_FROZEN_FIELDS:
            rec = {'owner': None, 'status': 'frozen (identity field; change only via coordinator / LY-100)'}
        elif owner:
            rec = {'owner': owner, 'status': 'proposal owner (LY-100 writes the public card)'}
        else:
            rec = {'owner': None, 'status': 'frozen (no 011-090 seat touches this card)'}
        ownership['cardFields'][f'{cid}#{f}'] = rec
card_meta = {cid: {'path': v['path'], 'sha256': v['sha256']} for cid, v in lab_cards.items() if cid in CARD_SCOPE}

# ---------------------------------------------------------------- ports
ports = {}
def add_port(pid, kind, frame, local, forward, producer, steward, measuredFrom, status='frozen-measured', note=None, extra=None, version=1):
    up = [0.0, 1.0, 0.0]
    rec = {'portId': pid, 'version': version, 'kind': kind, 'producer': producer, 'steward': steward, 'status': status,
           'frames': {'local': frame, 'world': 'luoyang-local-schematic-v01'},
           'local': None if local is None else {'position': [round(v, 6) for v in local], 'up': up, 'forward': forward},
           'world': None, 'nodeMatrixColumnMajor': mat_col_major(frame) if frame else None,
           'measuredFrom': measuredFrom, 'elevationClass': 'C-engineering', 'tolerance_m': {'position': 0.005, 'elevation': 0.002}, 'consumers': []}
    if local is not None and frame and place(frame) is not None:
        pl = place(frame)
        rec['world'] = {'position': [round(v, 6) for v in to_world(frame, local)], 'up': up, 'forward': [round(v, 9) for v in rot_y(pl['yaw'], forward)]}
    if note: rec['note'] = note
    if extra: rec.update(extra)
    ports[pid] = rec

# wall caps
for nid, w in walls['walls'].items():
    for i, c in enumerate(w['caps']):
        f = [c['outwardPlan_xz'][0], 0.0, c['outwardPlan_xz'][1]]
        mf = {'file': w['glb'], 'sha256': w['sha256'], 'method': 'qa/wall-end-ports.measure.json (source/wall_ends.py): base-edge midpoint of end cap'}
        steward = ownership['cityNodes'].get(nid, {}).get('owner')
        add_port(f'{nid}:cap-{i}:wall-end', 'wall-end', 'world', c['baseCenter'], f, 'LY-006', steward, mf,
                 extra={'capBaseWidth_m': c['baseWidth'], 'capTopWidth_m': c['topWidth'], 'capBaseY': c['baseY'], 'capTopY': c['topY'], 'capPlanarity_m': c['planarity_m']})
        add_port(f'{nid}:cap-{i}-top:floor', 'floor', 'world', [c['baseCenter'][0], c['topY'], c['baseCenter'][2]], f, 'LY-006', steward, mf,
                 note='wall-top centre line at the cap plane (top width in capTopWidth_m)', extra={'capTopWidth_m': c['topWidth']})
pr = {p['id']: p for p in probes['probes']}
def pmf(pid): p = pr[pid]; return {'file': p['file'], 'sha256': p['sha256'], 'method': f"vertical ray, top upward surface at local ({p['x']},{p['z']}) (qa/frozen-ports.probes.json)"}
for nm, x in (('C', 0.0), ('W', -7.6), ('E', 7.6)):
    y = pr[f'kaiyang-ground passage-{nm}']['topUpwardY']
    add_port(f'kaiyang-K-v1:passage-{nm}:threshold', 'threshold', 'local:kaiyang-K-v1', [x, y, 0.0], [0.0, 0.0, -1.0], 'LY-006', 'LY-015', pmf(f'kaiyang-ground passage-{nm}'),
             note='ground strip top in the passage; forward = from city outside (+z) to inside (-z). World uses the inactive hidden-trial placement')
y = pr['kaiyang-ground outer-edge-C']['topUpwardY']
add_port('kaiyang-K-v1:outer-apron-edge:road-end', 'road-end', 'local:kaiyang-K-v1', [0.0, y, 7.0], [0.0, 0.0, 1.0], 'LY-006', 'LY-015', pmf('kaiyang-ground outer-edge-C'),
         note='outer edge z=+7 of the strip (x -8.5..8.5); LY-085 starts here')
for nm, x in (('W', -7.9), ('E', 7.9)):
    y = pr[f'pingcheng-ground passage-{nm}']['topUpwardY']
    add_port(f'pingcheng-P-v1:passage-{nm}:threshold', 'threshold', 'local:pingcheng-P-v1', [x, y, 0.0], [0.0, 0.0, -1.0], 'LY-006', 'LY-016', pmf(f'pingcheng-ground passage-{nm}'))
add_port('pingcheng-P-v1:old-ramp:ground', 'ground', 'local:pingcheng-P-v1', None, None, 'LY-006', 'LY-017',
         {'searched': ['docs GLBs at bce3211 (ground-network-ground-stitched probes in front of both south gates: no surface; qa/chunk-measure.json)',
                       'source ZIP city/pingcheng-P-mid-hidden-trial.blend (3 mesh objects only; qa/pingcheng-hidden-trial.objects.json)',
                       'city-visible chunks C_gate_local_ground (only pingcheng_ground_trial_v1 = the ground attachment)']},
         status='frozen-id / value-pending', note='LY-016 prep cites an exact 6 m x 0.05 m old ramp; LY-006 could not locate it in any file it read. ID/version frozen; LY-016 registers position + file SHA in its interface file; steward LY-017')
for s in load(INPUTS['frontage_openings']):
    zf = -s['frontY']; inward = -1.0 if s['frontY'] > 0 else 1.0
    for k, (x0, x1) in enumerate(s['openings']):
        p = pr[f"frontage shop{s['idx']} door{k} inside"]
        add_port(f"market-site:shop{s['idx']}-door{k}:threshold", 'threshold', 'local:market-site', [(x0 + x1) / 2, p['topUpwardY'] + 0.2, zf], [0.0, 0.0, inward], 'LY-006', 'LY-029',
                 {'file': p['file'], 'sha256': p['sha256'], 'method': 'vertical ray 0.30 m inside the front line on street_frontage-LOD0 (frontage local) + 0.2 (frontage->market-site, verified from mother-scene chunk); opening x-range from LY-021 prep (qa/frontage-openings.from-LY-021-prep.json)'},
                 extra={'openingX': [x0, x1]})
for name, b in routes_local():
    nm = name.replace('route_', '')
    c = [(b[0][0] + b[1][0]) / 2, b[1][1], (b[0][2] + b[1][2]) / 2]
    add_port(f'market-site:route-{nm}:road-end', 'road-end', 'local:market-site', c, [1.0, 0.0, 0.0], 'LY-006', 'LY-029',
             {'file': 'docs/cities/luoyang/assets/market/market-cluster.glb', 'sha256': idx['cities/luoyang/assets/market/market-cluster.glb']['sha256'], 'method': f'node {name} AABB (world) - market-site translation'},
             note='strip centre at top; whole strip extent in stripAABB_local (frozen road strip, do not re-lay)', extra={'stripAABB_local': b})
for nm, (x, z) in (('A', (-11.95, -1.5)), ('B', (12.05, -1.35))):
    add_port(f'granary-{nm}:step-foot:ground', 'ground', 'local:storage-site', [x, 0.2, z], [0.0, 0.0, -1.0], 'LY-006', 'LY-033',
             {'file': 'docs/cities/luoyang/progress-assets/granary-city-v1/granary-city-LOD0.glb', 'sha256': idx['cities/luoyang/progress-assets/granary-city-v1/granary-city-LOD0.glb']['sha256'],
              'method': 'vertical-ray profile (qa/frozen-ports.probes.json) + x scan: step x-range A [-12.7,-11.2], B [11.3,12.8] (1.5 m), foot where top drops to 0.20'},
             extra={'stepWidth_m': 1.5})
ne = chunks['ne']
nemf = {'file': 'qa/chunks/northeast_C_access.glb (= chunk extracted from origin/luoyang-content city-visible ZIP 5895ef23...)', 'sha256': ne['file_sha256'], 'method': 'source/measure_chunks.py'}
add_port('ne-approach:start:road-end', 'road-end', 'world', [sum(ne['start']['xRange']) / 2, ne['start']['topY'], ne['start']['z']], [0.0, 0.0, -1.0], 'LY-006', 'LY-039', nemf, note='3 m wide end at the granary site north edge')
add_port('ne-approach:end-E:road-end', 'road-end', 'world', [ne['endE']['x'], ne['endE']['topY'], sum(ne['endE']['zRange']) / 2], [1.0, 0.0, 0.0], 'LY-006', 'LY-039', nemf, note='5.5 m end cap, top y 0.0 (old wuku support level)')
# LY-005 imported ports (stewardship assigned here)
for p in ly5['ports']:
    pid = p['portId']; node = p['owner']['nodeId']
    st = ownership['cityNodes'].get(node, {}).get('owner')
    rec = dict(p); rec['producer'] = 'LY-005'; rec['steward'] = st; rec['status'] = 'imported from LY-005 (frozen)'; rec['consumers'] = []
    rec['stewardReason'] = None if st else ownership['cityNodes'].get(node, {}).get('reason')
    ports[pid] = rec

# seat-produced ports
for seat in SEATS:
    for pid in SPEC[seat].get('produces', []):
        if pid in ports: conflicts.append({'object': pid, 'kind': 'port produced twice', 'claims': [ports[pid]['producer'], seat]}); continue
        kind = pid.rsplit(':', 1)[1]
        ports[pid] = {'portId': pid, 'version': 1, 'kind': kind, 'producer': seat, 'steward': seat, 'status': 'declared (values filled by producer at delivery)',
                      'frames': {'local': SPEC[seat]['frames'][0], 'world': 'luoyang-local-schematic-v01'}, 'local': None, 'world': None,
                      'nodeMatrixColumnMajor': mat_col_major(SPEC[seat]['frames'][0]), 'measuredFrom': None, 'elevationClass': 'C-engineering',
                      'tolerance_m': {'position': 0.005, 'elevation': 0.002}, 'consumers': []}
for seat in SEATS:
    for pid in SPEC[seat].get('consumes', []):
        if pid == 'FROZEN:*':
            for q in ports.values():
                if q['producer'] in ('LY-006', 'LY-005'): q['consumers'].append(seat)
            continue
        if pid not in ports: conflicts.append({'object': pid, 'kind': 'consumed port has no producer', 'claims': [seat]}); continue
        ports[pid]['consumers'].append(seat)
for q in ports.values(): q['consumers'] = sorted(set(q['consumers']))

# seams (each consumed port = one seam record between producer and consumer)
seams = []
for pid, q in sorted(ports.items()):
    for c in q['consumers']:
        seams.append({'seamId': f"{pid}@v{q['version']}::{q['producer']}->{c}", 'portId': pid, 'version': q['version'],
                      'producer': q['producer'], 'steward': q['steward'], 'consumer': c, 'sideA': {'seat': q['producer'], 'portId': pid, 'version': q['version']},
                      'sideB': {'seat': c, 'portId': pid, 'version': q['version']}})
gate_slots = []
for s in walls['seams']:
    key = tuple(sorted([s['a'][0], s['b'][0]]))
    name, site = None, None
    for k, v in R.SEAM_GATES.items():
        if tuple(sorted(k)) == key: name, site = v
    gate_slots.append({'pair': key, 'caps': [f"{s['a'][0]}:cap-{s['a'][1]}:wall-end", f"{s['b'][0]}:cap-{s['b'][1]}:wall-end"], 'gap_plan_m': s['gap_plan_m'],
                       'midpoint': s['midpoint'], 'gateSlot': name, 'site': site, 'siteOwner': R.SITES[site]['owner'] if site else None})
gate_slots.append({'pair': ('wall-A-wall-01', 'wall-A-wall-02'), 'caps': ['wall-A-wall-01:cap-1:wall-end', 'wall-A-wall-02:cap-0:wall-end'], 'gap_plan_m': None,
                   'midpoint': None, 'gateSlot': '上东门 Shangdong corner gap (not facing caps; LY-020 prep: a gate opening)', 'site': 'S-WALLS', 'siteOwner': 'LY-020'})

# ---------------------------------------------------------------- per-seat consolidated table
seat_table = {}
for seat in SEATS:
    sp = SPEC[seat]; sb = seats_board[seat]
    seat_table[seat] = {
        'seat': seat, 'title': sb['title'], 'type': sb['type'], 'deps': sb['deps'], 'usesG': sb['usesG'], 'site': sp['site'], 'siteOwner': R.SITES[sp['site']]['owner'],
        'role': sp['role'], 'frames': sp['frames'],
        'writeZones': [z['zoneId'] for z in zones if z['seat'] == seat and z['class'] == 'write'],
        'cutZones': [z['zoneId'] for z in zones if z['seat'] == seat and z['class'] == 'cut'],
        'claimProtocol': bool(sp.get('claimProtocol')),
        'ownsCityNodes': sorted([n for n, r in ownership['cityNodes'].items() if r['owner'] == seat]),
        'ownsSourceObjects': {'modify/replace': sorted([o for o, r in ownership['sourceObjects'].items() if r['owner'] == seat and r['mode'] != 'keep']),
                              'keep (assembly steward)': len([o for o, r in ownership['sourceObjects'].items() if r['owner'] == seat and r['mode'] == 'keep'])},
        'ownsGroundPieces': sorted([g for g, r in ownership['groundPieces'].items() if r['owner'] == seat]),
        'ownsCuts': sorted([c for c, r in ownership['cuts'].items() if r['requester'] == seat]),
        'ownsCards': sorted([c for c, s in card_owner.items() if s == seat]),
        'components': [{'id': c, 'class': k} for (c, k) in sp.get('components', [])],
        'produces': sp.get('produces', []), 'consumes': sp.get('consumes', []),
        'placementProposal': sp.get('placementProposal'),
    }

out_meta = {'registry': 'LY-006 module ports & ownership', 'version': R.REGISTRY_VERSION, 'baseline': R.BASELINE,
            'inputs': {k: {'path': os.path.relpath(v, WP).replace('\\', '/'), 'sha256': sha(v)} for k, v in INPUTS.items()}}
dump({**out_meta, 'frames': R.FRAMES, 'sites': R.SITES, 'zones': zones, 'envelopes': envelopes}, 'registry/zones.json')
dump({**out_meta, 'ports': ports}, 'registry/ports.json')
dump({**out_meta, 'seams': seams, 'gateSlots': gate_slots}, 'registry/seams.json')
dump({**out_meta, 'catalogs': catalog_files, 'ownership': ownership, 'cards': card_meta, 'conflicts': conflicts}, 'registry/ownership.json')
dump({**out_meta, 'seats': seat_table}, 'registry/seats.json')
print('zones', len(zones), 'envelopes', len(envelopes), 'ports', len(ports), 'seams', len(seams), 'sourceObjects', len(ownership['sourceObjects']),
      'cardFields', len(ownership['cardFields']), 'conflicts', len(conflicts))
for c in conflicts[:40]: print('CONFLICT', c)
