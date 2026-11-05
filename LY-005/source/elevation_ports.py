# LY-005 elevation survey + measured port instances (local and world) on bce3211 geometry.
# Usage: python -I elevation_ports.py <city-dump.json> <frames.json> <out-elevation.json> <out-ports.json>
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbio, vray

dump, frames_p, out_e, out_p = sys.argv[1:5]
d = json.load(open(dump, encoding='utf-8'))
frames = json.load(open(frames_p, encoding='utf-8'))
LAB = 'D:/GitHub/creation-notebook-lab'
assets = {a['id']: a for a in d['assets']}
nodes = {n['id']: n for n in d['nodes']}


def path_of(url):
    u = url.replace('\\', '/')
    return LAB + '/' + u[u.find('/docs/') + 1:]


def node_m(n):
    if n.get('matrix'):
        return glbio.gltf_col_major_to_np(n['matrix'])
    t = n.get('transform') or n
    return glbio.compose_three(t.get('position', [0, 0, 0]), t.get('rotationY', 0) or 0, t.get('scale', [1, 1, 1]))


def kept_tris(asset_id, near=False):
    a = assets[asset_id]
    g = glbio.read_glb(path_of(a['nearUrl'] if near else a['url']))
    ex = set(a.get('excludeNodes') or [])
    out = []
    for ni, name, w, pos, tri, anc in glbio.mesh_items(g):
        if any(x in ex for x in anc):
            continue
        out.append(glbio.apply(w, pos)[tri])
    return np.concatenate(out), g['sha256']


def world_tris(node_id):
    n = nodes[node_id]
    t, sha = kept_tris(n['asset'])
    m = node_m(n)
    return glbio.apply(m, t.reshape(-1, 3)).reshape(-1, 3, 3), sha


ground_ids = [k for k, n in nodes.items() if n.get('chapter') == 'terrain']
G = []
gsha = {}
for k in ground_ids:
    t, sha = world_tris(k)
    G.append(t)
    gsha[k] = {'asset': nodes[k]['asset'], 'sha256': sha, 'triangles': len(t)}
ground = vray.VSampler(np.concatenate(G), cell=16.0)


def terrain_at(x, z, below=None):
    hs = [y for y, ny in ground.heights(x, z) if ny > 0.05]
    if below is not None:
        hs = [y for y in hs if y <= below + 1.0]
    return max(hs) if hs else None


elev = {'groundNodes': gsha, 'groundNodesInitial': [nodes[k].get('initial', True) for k in ground_ids], 'courtyards': [], 'walls': [], 'others': []}

# courtyards: kept footprint corners inset 0.5 m + centre
for k, n in nodes.items():
    if not n['asset'].startswith('courtyard-'):
        continue
    f = frames['assets'][n['asset']]['files']['far']['boundsKept']
    mn, mx = np.array(f['min']), np.array(f['max'])
    m = node_m(n)
    base = float(mn[1])
    pts = [(mn[0] + .5, mn[2] + .5), (mx[0] - .5, mn[2] + .5), (mx[0] - .5, mx[2] - .5), (mn[0] + .5, mx[2] - .5), ((mn[0] + mx[0]) / 2, (mn[2] + mx[2]) / 2)]
    samples = []
    for lx, lz in pts:
        wp = glbio.apply(m, np.array([[lx, base, lz]]))[0]
        ty = terrain_at(wp[0], wp[2], wp[1])
        samples.append({'local': [lx, base, lz], 'world': wp.tolist(), 'terrainY': ty, 'baseMinusTerrain_m': None if ty is None else float(wp[1] - ty)})
    gaps = [s['baseMinusTerrain_m'] for s in samples if s['baseMinusTerrain_m'] is not None]
    elev['courtyards'].append({'node': k, 'asset': n['asset'], 'worldBaseY': float(m[1, 3] + base), 'samples': samples,
                               'samplesWithTerrain': len(gaps), 'gapMin_m': min(gaps) if gaps else None, 'gapMax_m': max(gaps) if gaps else None})

# walls: base end points along principal axis
for k, n in nodes.items():
    if not n['asset'].startswith('wall-'):
        continue
    t, sha = world_tris(k)
    v = t.reshape(-1, 3)
    base = v[:, 1].min()
    bv = v[np.abs(v[:, 1] - base) < 1e-4]
    c = bv[:, [0, 2]].mean(0)
    u, s, vt = np.linalg.svd(bv[:, [0, 2]] - c, full_matrices=False)
    proj = (bv[:, [0, 2]] - c) @ vt[0]
    ends = [bv[np.argmin(proj)], bv[np.argmax(proj)]]
    rec = {'node': k, 'baseY': float(base), 'topY': float(v[:, 1].max()), 'ends': []}
    for e in ends:
        ty = terrain_at(e[0], e[2], e[1])
        rec['ends'].append({'world': e.tolist(), 'terrainY': ty, 'baseMinusTerrain_m': None if ty is None else float(e[1] - ty)})
    elev['walls'].append(rec)

for k in ('market-main', 'market-N2', 'storage-main', 'wall-direct-gate-body-only', 'yong-gate-body', 'yong-gate-interface'):
    t, sha = world_tris(k)
    v = t.reshape(-1, 3)
    elev['others'].append({'node': k, 'worldMinY': float(v[:, 1].min()), 'worldMaxY': float(v[:, 1].max()), 'sha256': sha})

# ---------------- ports ----------------
ports = []


def mkport(pid, kind, node_id, local, fwd, measured, cls='C-engineering', note=''):
    n = nodes[node_id]
    m = node_m(n)
    lp = np.array(local, dtype=float)
    wp = glbio.apply(m, lp[None])[0]
    up_w = m[:3, :3] @ np.array([0, 1, 0.])
    f_w = m[:3, :3] @ np.array(fwd, dtype=float)
    ty = terrain_at(wp[0], wp[2], wp[1])
    ports.append({
        'portId': pid, 'version': 1, 'kind': kind,
        'owner': {'nodeId': node_id, 'assetId': n['asset'], 'responsibleSeat': 'unassigned (LY-006)'},
        'frames': {'local': 'asset frame = GLB default scene after node hierarchy bake (city-renderer loadAsset)', 'world': 'luoyang-local-schematic-v01'},
        'local': {'position': lp.tolist(), 'up': [0, 1, 0], 'forward': list(map(float, fwd))},
        'world': {'position': wp.tolist(), 'up': up_w.tolist(), 'forward': f_w.tolist()},
        'nodeMatrixColumnMajor': m.T.reshape(-1).tolist(),
        'measuredFrom': measured, 'elevationClass': cls,
        'cityTerrainYBelow': ty, 'portMinusTerrain_m': None if ty is None else float(wp[1] - ty),
        'tolerance_m': {'position': 0.005, 'elevation': 0.002},
        'note': note,
    })


# Yong gate: passages from body pier gaps (body has no floor geometry in passages; apron top is the walking surface).
body_t, body_sha = kept_tris('yong-gate-near')
apron_t, apron_sha = kept_tris('yong-gate-apron')
bs = vray.VSampler(body_t, 1.0)
asam = vray.VSampler(apron_t, 1.0)
xs = np.round(np.arange(-12.55, 12.56, 0.05), 3)
solid = [any(abs(y) < 1e-6 and ny < -0.5 for y, ny in bs.heights(x, 0.0)) for x in xs]
runs, cur = [], None
for x, s_ in zip(xs, solid):
    if not s_ and cur is None:
        cur = [x, x]
    elif not s_:
        cur[1] = x
    elif cur is not None:
        runs.append(cur); cur = None
if cur:
    runs.append(cur)
passages = [r for r in runs if r[0] > -12 and r[1] < 12]
zf = float(body_t.reshape(-1, 3)[:, 2].max())
names = ['N', 'C', 'S']  # local +X = world north for this node; sort by x descending => N first
passages = sorted(passages, key=lambda r: -r[0])
for nm, (x0, x1) in zip(names, passages):
    xc = (x0 + x1) / 2
    for side, z, fwd in (('outer', -zf, [0, 0, -1]), ('inner', zf, [0, 0, 1])):
        hs = [y for y, ny in asam.heights(xc, z) if ny > 0.5]
        ytop = max(hs)
        mkport(f'yong-gate:passage-{nm}:threshold-{side}', 'threshold', 'yong-gate-body', [xc, ytop, z], fwd,
               {'surfaceFile': assets['yong-gate-apron']['sourcePath'], 'surfaceSha256': apron_sha,
                'bodyFile': assets['yong-gate-near']['sourcePath'], 'bodySha256': body_sha,
                'method': f'pier gap by downward-facing y=0 faces of body along local z=0 (step 0.05 m): local x {x0}..{x1}; walking surface = top upward face of apron at that point'},
               note=f'passage clear width approx {round(x1 - x0 + 0.05, 2)} m (sampling step 0.05 m). Body has no floor/threshold geometry; surface comes from apron. outer = local -Z = world west (outside city).')
# apron outer/inner edges (street connection ports)
amin, amax = apron_t.reshape(-1, 3).min(0), apron_t.reshape(-1, 3).max(0)
for side, z, fwd in (('outer', float(amin[2]), [0, 0, -1]), ('inner', float(amax[2]), [0, 0, 1])):
    mkport(f'yong-gate:apron-edge-{side}:ground', 'ground', 'yong-gate-interface', [0.0, 0.0, z], fwd,
           {'surfaceFile': assets['yong-gate-apron']['sourcePath'], 'surfaceSha256': apron_sha, 'method': 'apron kept bounds edge, top y=0'},
           note=('street/road receiver port on the west (outside-city) side; no road reaches it at bce3211 or f28d650.' if side == 'outer' else
                 'street/road receiver port on the east (inside-city) side; nothing reaches it at bce3211; at f28d650 yong-road-link-LOD0 starts here flush (see qa/f28d650-port-consumption.json).'))
# wall joints: adapter end faces at local x = +-16
for side, x in (('north', float(amax[0])), ('south', float(amin[0]))):
    mkport(f'yong-gate:wall-joint-{side}:base', 'wall-end', 'yong-gate-interface', [x, 0.0, 0.0], [float(np.sign(x)), 0, 0],
           {'surfaceFile': assets['yong-gate-apron']['sourcePath'], 'surfaceSha256': apron_sha, 'method': 'adapter extreme local x, base y=0, z=0 (adapter centre line)'},
           note='joins existing C wall end; local +X = world north for this node.')

# courtyard ground ports (one per node): footprint centre at kept base
for k, n in nodes.items():
    if not n['asset'].startswith('courtyard-'):
        continue
    f = frames['assets'][n['asset']]['files']['far']['boundsKept']
    mn, mx = np.array(f['min']), np.array(f['max'])
    mkport(f'{k}:ground-base', 'ground', k, [float((mn[0] + mx[0]) / 2), float(mn[1]), float((mn[2] + mx[2]) / 2)], [0, 0, 1],
           {'file': assets[n['asset']]['sourcePath'], 'sha256': frames['assets'][n['asset']]['files']['far']['sha256'], 'method': 'kept bounds (excludeNodes removed) centre at min y'},
           note='site_lot/lane removed by excludeNodes; base is the lowest kept geometry. forward = local +Z (side of site_neutral_lane in the GLB).')

# Guangyang direct gate body sits on wall top
t, sha = world_tris('wall-direct-gate-body-only')
v = t.reshape(-1, 3)
c = (v.min(0) + v.max(0)) / 2
mkport('guangyang-gate-body:floor-base', 'floor', 'wall-direct-gate-body-only', [float(c[0]), float(v[:, 1].min()), float(c[2])], [0, 0, 1],
       {'file': assets['wall-direct-gate-body-only']['sourcePath'], 'sha256': sha, 'method': 'city-absolute GLB, kept bounds centre at min y'},
       note='gate-house base at wall top level; asset is city-absolute so local == world (identity node).')

# self-check: world == N*local recomputed independently from city-data matrices
res = 0.0
for p in ports:
    m = node_m(nodes[p['owner']['nodeId']])
    res = max(res, float(np.max(np.abs(glbio.apply(m, np.array([p['local']['position']]))[0] - np.array(p['world']['position'])))))
json.dump(elev, open(out_e, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump({'schema': 'LY-005-port-v1', 'frame': 'luoyang-local-schematic-v01', 'baseline': 'bce3211', 'ports': ports, 'maxLocalWorldRecomputeResidual_m': res}, open(out_p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

cy = elev['courtyards']
print('ground nodes', gsha, elev['groundNodesInitial'])
print('courtyards', len(cy), 'with terrain samples', sum(1 for c in cy if c['samplesWithTerrain']), 'gap range', min(c['gapMin_m'] for c in cy if c['gapMin_m'] is not None), max(c['gapMax_m'] for c in cy if c['gapMax_m'] is not None))
print('no terrain under', [c['node'] for c in cy if c['samplesWithTerrain'] < 5])
for w in elev['walls']:
    print('wall', w['node'], w['baseY'], w['topY'], [e['baseMinusTerrain_m'] for e in w['ends']])
for o in elev['others']:
    print(o)
print('passages', passages)
for p in ports:
    if not p['portId'].startswith('C02') and not p['portId'].startswith('FROZEN'):
        print(p['portId'], [round(x, 4) for x in p['local']['position']], [round(x, 4) for x in p['world']['position']], p['cityTerrainYBelow'], p['portMinusTerrain_m'])
print('ports', len(ports), 'residual', res)
