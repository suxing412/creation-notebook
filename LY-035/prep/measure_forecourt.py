# LY-035 prep measurement (read-only). Measures the in-city granary group's forecourt:
#   ground support, stairs/landing/door/eave clearances, free-space clearance map,
#   envelope connectivity receiving->A/B stair feet, and candidate staging/turning boxes.
# Usage: python -X utf8 measure_forecourt.py <out_json>
# Inputs are read from the lab repo at bce3211; nothing is written outside the given output path.
import sys, os, json, re
import numpy as np
from scipy import ndimage
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbread as G

LAB = 'D:/GitHub/creation-notebook-lab/docs/'
CITY = LAB + 'cities/luoyang/progress-assets/granary-city-v1/granary-city-LOD0.glb'
V1 = LAB + 'cities/luoyang/assets/storage/storage-group-organized.glb'
OUT = sys.argv[1] if len(sys.argv) > 1 else 'qa/forecourt-measure.json'

RES = 0.05            # grid cell (m)
BAND = (0.05, 2.00)   # obstacle band above walk surface (m): 1.8 m body + 0.2 m head/load margin (C test value)
R = {}


def tri_samples(tris, step=0.02):
    """Dense barycentric samples of each triangle (works for vertical faces)."""
    out = []
    for t in tris:
        a, b, c = t
        n = int(np.ceil(max(np.linalg.norm(b - a), np.linalg.norm(c - a), np.linalg.norm(c - b)) / step)) + 1
        i, j = np.meshgrid(np.arange(n + 1), np.arange(n + 1), indexing='ij')
        m = (i + j) <= n
        u, v = i[m] / n, j[m] / n
        out.append(a[None] + u[:, None] * (b - a)[None] + v[:, None] * (c - a)[None])
    return np.concatenate(out) if out else np.zeros((0, 3))


city, cjs = G.world_triangles(CITY)
v1, vjs = G.world_triangles(V1)
R['inputs'] = {'city_lod0': {'path': CITY, 'sha256': G.sha256(CITY)}, 'v1_organized': {'path': V1, 'sha256': G.sha256(V1)}}
R['city_nodes'] = [{'node': p['node'], 'material': p['material'], 'tris': int(len(p['tris'])), 'det': round(p['det'], 9),
                    'bboxMin': np.round(p['tris'].reshape(-1, 3).min(0), 4).tolist(),
                    'bboxMax': np.round(p['tris'].reshape(-1, 3).max(0), 4).tolist()} for p in city]

# ---- 1. ground support -------------------------------------------------------------
ground = [p for p in city if p['node'] == 'original_city_ground_preserved'][0]['tris']
gv = ground.reshape(-1, 3)
fn = np.cross(ground[:, 1] - ground[:, 0], ground[:, 2] - ground[:, 0])
up = ground[(fn[:, 1] / np.linalg.norm(fn, axis=1)) > 0.99]
walk_y = float(up.reshape(-1, 3)[:, 1].max())
R['ground'] = {'tris': int(len(ground)), 'upFacingTris': int(len(up)), 'topY': walk_y,
               'topYSpread': float(np.ptp(up.reshape(-1, 3)[:, 1])),
               'xRange': [float(gv[:, 0].min()), float(gv[:, 0].max())], 'zRange': [float(gv[:, 2].min()), float(gv[:, 2].max())]}
sg = [p for p in v1 if p['node'] == 'sample_ground'][0]['tris']
R['ground']['sameAsV1SampleGround'] = bool(np.allclose(np.sort(np.round(sg.reshape(-1, 3), 4), axis=0), np.sort(np.round(gv, 4), axis=0)))

# ---- 2. city LOD0 architecture == v1 organized (triangle multiset, 1e-4 m) -------------
ca = np.concatenate([p['tris'] for p in city if p['node'] != 'original_city_ground_preserved'])
va = np.concatenate([p['tris'] for p in v1 if p['node'] != 'sample_ground'])


def canon(t):
    t = np.round(t, 4)
    t = np.sort(t.view([('x', float), ('y', float), ('z', float)]).reshape(len(t), 3), axis=1).view(float).reshape(len(t), 9)
    return t[np.lexsort(t.T[::-1])]
cc, vc = canon(ca), canon(va)
R['v1_vs_city_architecture'] = {'cityTris': int(len(ca)), 'v1Tris': int(len(va)),
                                 'sameMultisetAt1e-4': bool(cc.shape == vc.shape and np.abs(cc - vc).max() <= 2e-4),
                                 'maxAbsDiff': float(np.abs(cc - vc).max()) if cc.shape == vc.shape else None}

# ---- 3. named parts from v1 (identity of A/B/stairs/receiving) --------------------------
parts = {}
for p in v1:
    t = p['tris'].reshape(-1, 3)
    parts[p['node']] = (t.min(0), t.max(0))


def bb(n):
    lo, hi = parts[n]
    return lo, hi


def stair(prefix, nsteps, floor):
    st = []
    for k in range(nsteps):
        lo, hi = bb('%s_step_%d' % (prefix, k))
        st.append({'k': k, 'topY': round(float(hi[1]), 4), 'run': round(float(hi[2] - lo[2]), 4), 'width': round(float(hi[0] - lo[0]), 4),
                   'zSouth': round(float(hi[2]), 4), 'zNorth': round(float(lo[2]), 4)})
    rises = [round(st[0]['topY'] - walk_y, 4)] + [round(st[k]['topY'] - st[k - 1]['topY'], 4) for k in range(1, nsteps)]
    flo, fhi = bb(prefix + '_floor')
    wlo, whi = bb(prefix + '_frontwall_-1')
    llo, lhi = bb(prefix + '_door_lintel')
    rlo, rhi = bb(prefix + '_roofbed_-1')
    w2lo, w2hi = bb(prefix + '_frontwall_1')
    foot = [round(float((st[0]['k'] * 0) + (bb(prefix + '_step_0')[0][0] + bb(prefix + '_step_0')[1][0]) / 2), 4), round(walk_y, 4), st[0]['zSouth']]
    return {
        'steps': st, 'rises': rises, 'totalRise': round(float(fhi[1] - walk_y), 4), 'floorTopY': round(float(fhi[1]), 4),
        'stairWidth': st[0]['width'], 'stairRunTotal': round(sum(s['run'] for s in st), 4),
        'doorClearWidth': round(float(w2lo[0] - whi[0]), 4), 'doorClearHeight': round(float(llo[1] - fhi[1]), 4),
        'lipFloorBeforeWall': round(float(fhi[2] - whi[2]), 4),
        'landingDepthTopStepPlusLip': round(st[-1]['run'] + float(fhi[2] - whi[2]), 4),
        'eaveUnderside': round(float(rlo[1]), 4), 'eaveSouthEdgeZ': round(float(rhi[2]), 4),
        'headroomTopStepToEave': round(float(rlo[1] - st[-1]['topY']), 4),
        'headroomFootToEave_at_eaveEdge': round(float(rlo[1] - walk_y), 4),
        'footPort_provisional': foot,
    }
R['A'] = stair('A', 4, 'A_floor')
R['B'] = stair('B', 6, 'B_floor')
clo, chi = bb('receiving_cover')
tlo, thi = bb('checking_table')
R['receiving'] = {'coverMin': np.round(clo, 4).tolist(), 'coverMax': np.round(chi, 4).tolist(), 'coverUndersideMinY': round(float(clo[1]), 4),
                  'tableMin': np.round(tlo, 4).tolist(), 'tableMax': np.round(thi, 4).tolist(),
                  'bags': {n: [np.round(parts[n][0], 4).tolist(), np.round(parts[n][1], 4).tolist()] for n in parts if n.startswith('C_bag')}}
recv_port = [round(float((clo[0] + chi[0]) / 2), 4), walk_y, round(float(clo[2]) - 0.5, 4)]  # 0.5 m north of canopy edge (C provisional)
R['receiving']['northPort_provisional'] = recv_port

# ---- 4. occupancy grid from ACTUAL city LOD0 --------------------------------------------
x0, x1 = R['ground']['xRange']
z0, z1 = R['ground']['zRange']
nx, nz = int(round((x1 - x0) / RES)), int(round((z1 - z0) / RES))


def occupancy(tri_list):
    occ = np.zeros((nx, nz), bool)
    for t in tri_list:
        ys = t[:, :, 1]
        keep = (ys.max(1) >= walk_y + BAND[0]) & (ys.min(1) <= walk_y + BAND[1])
        s = tri_samples(t[keep], RES * 0.4)
        s = s[(s[:, 1] >= walk_y + BAND[0]) & (s[:, 1] <= walk_y + BAND[1])]
        ix = np.clip(((s[:, 0] - x0) / RES).astype(int), 0, nx - 1)
        iz = np.clip(((s[:, 2] - z0) / RES).astype(int), 0, nz - 1)
        occ[ix, iz] = True
    return occ
occ = occupancy([p['tris'] for p in city if p['node'] != 'original_city_ground_preserved'])
occ_v1 = occupancy([p['tris'] for p in v1 if p['node'] != 'sample_ground'])
R['occupancy'] = {'res': RES, 'bandAboveWalk': BAND, 'grid': [nx, nz], 'blockedCells': int(occ.sum()),
                  'blockedArea_m2': round(float(occ.sum()) * RES * RES, 3), 'plotArea_m2': round((x1 - x0) * (z1 - z0), 3),
                  'cellsDifferentFromV1': int((occ ^ occ_v1).sum())}
# plot edge is NOT treated as a wall but as the end of support (outside = no ground => blocked)
free = ~occ
free[0, :] = free[-1, :] = free[:, 0] = free[:, -1] = False
clear = ndimage.distance_transform_edt(free) * RES   # distance to nearest obstacle/plot edge (m)


def ij(x, z):
    return int((x - x0) / RES), int((z - z0) / RES)


def xz(i, j):
    return x0 + (i + 0.5) * RES, z0 + (j + 0.5) * RES

# forecourt box: between canopy north edge and the warehouse stair feet, spanning A..B outer walls
fc = dict(x=(float(bb('A_sidewall_-1')[0][0]), float(bb('B_sidewall_1')[1][0])), z=(float(R['B']['footPort_provisional'][2]) + 0.0, float(clo[2])))
fc['z'] = (min(R['A']['footPort_provisional'][2], R['B']['footPort_provisional'][2]), float(clo[2]))
fz0, fz1 = sorted(fc['z'])
fi0, fj0 = ij(fc['x'][0], -3674.849 if False else fz0)
fi1, fj1 = ij(fc['x'][1], fz1)
sub = clear[fi0:fi1, min(fj0, fj1):max(fj0, fj1)]
k = np.unravel_index(np.argmax(sub), sub.shape)
cx, cz = xz(fi0 + k[0], min(fj0, fj1) + k[1])
R['forecourt'] = {'box_x': [round(fc['x'][0], 4), round(fc['x'][1], 4)], 'box_z': [round(fz0, 4), round(fz1, 4)],
                  'depth_m': round(fz1 - fz0, 4), 'width_m': round(fc['x'][1] - fc['x'][0], 4),
                  'freeFraction': round(float((sub > 0).mean()), 4),
                  'maxInscribedRadius_m': round(float(sub.max()), 3), 'maxInscribedCenter': [round(cx, 3), round(cz, 3)]}

# clearance immediately in front of each stair foot (disc centred d m south of foot)
for w in ('A', 'B'):
    fx, _, fzz = R[w]['footPort_provisional']
    rows = []
    for d in (0.3, 0.6, 1.0, 1.5, 2.0, 3.0):
        i, j = ij(fx, fzz + d)
        rows.append({'distSouthOfFoot_m': d, 'clearRadius_m': round(float(clear[i, j]), 3)})
    R[w]['clearanceInFrontOfFoot'] = rows

# ---- 5. envelope connectivity + geodesic length receiving -> stair feet ------------------
# Port cells sit just south of step_0 (foot), so the disc must fit *against* the stair face. To test the corridor
# itself we target a point at 'standoff' = r + 0.05 m south of the foot (the stair is the next, separate check).
def grid_graph(mask):
    idx = -np.ones(mask.shape, np.int64)
    nn = int(mask.sum())
    idx[mask] = np.arange(nn)
    rows, cols, w = [], [], []
    for di, dj, c in ((1, 0, 1.0), (0, 1, 1.0), (1, 1, 2 ** .5), (1, -1, 2 ** .5)):
        n0, n1 = mask.shape
        ja = slice(0, n1 - dj) if dj >= 0 else slice(-dj, n1)
        jb = slice(dj, n1) if dj >= 0 else slice(0, n1 + dj)
        a = idx[0:n0 - di, ja]
        b = idx[di:n0, jb]
        m = (a >= 0) & (b >= 0)
        rows += [a[m], b[m]]
        cols += [b[m], a[m]]
        w += [np.full(m.sum(), c * RES)] * 2
    g = csr_matrix((np.concatenate(w), (np.concatenate(rows), np.concatenate(cols))), shape=(nn, nn))
    return g, idx

# restrict to a work window around the forecourt to keep the graph small
wi0, wj0 = ij(fc['x'][0] - 6, fz0 - 2)
wi1, wj1 = ij(fc['x'][1] + 6, fz1 + 8)
win = (slice(wi0, wi1), slice(min(wj0, wj1), max(wj0, wj1)))
conn = []
for env in (0.9, 1.2, 1.8, 2.4, 3.0):   # envelope widths (m) - C test samples, not historic
    r = env / 2
    mask = clear[win] >= r
    g, idx = grid_graph(mask)
    def node(x, z):
        i, j = ij(x, z)
        i -= win[0].start; j -= win[1].start
        return idx[i, j]
    s = node(recv_port[0], recv_port[2])
    res = {'envelopeWidth_m': env}
    for w in ('A', 'B'):
        fx, _, fzz = R[w]['footPort_provisional']
        t = node(fx, fzz + r + 0.05)
        if s < 0 or t < 0:
            res[w] = {'reachable': False, 'reason': 'port cell lacks clearance r'}
            continue
        d = dijkstra(g, indices=s, limit=np.inf)[t]
        straight = float(np.hypot(fx - recv_port[0], (fzz + r + 0.05) - recv_port[2]))
        res[w] = {'reachable': bool(np.isfinite(d)), 'geodesic_m': round(float(d), 3) if np.isfinite(d) else None,
                  'straight_m': round(straight, 3)}
    conn.append(res)
R['connectivity'] = conn

# ---- 6. stair-width envelope: lateral probes on each step (reproduces the fact, not the old count) -------
for w, n in (('A', 4), ('B', 6)):
    st = R[w]['steps']
    cxs = R[w]['footPort_provisional'][0]
    rows = []
    for env in (0.9, 1.2, 1.5, 1.8):
        fails = 0; total = 0; worst = 0.0
        for s in st:
            for dz in np.linspace(s['zNorth'] + 0.02, s['zSouth'] - 0.02, 5):
                for dx in np.linspace(-env / 2, env / 2, 19):
                    x = cxs + dx
                    on = abs(dx) <= s['width'] / 2 + 1e-9
                    support = s['topY'] if on else walk_y
                    drop = s['topY'] - support
                    total += 1
                    if drop > 0.02:
                        fails += 1; worst = max(worst, drop)
        rows.append({'envelopeWidth_m': env, 'probes': total, 'probesOffStepEdge': fails, 'worstDrop_m': round(worst, 3)})
    R[w]['stairLateralProbe'] = rows

# ---- 7. candidate staging / turning boxes ----------------------------------------------------------
# Route corridors (provisional straight centrelines receiving->foot); a staging box must keep >= keep_m from both
# centrelines (mutual exclusion is a separate rule, this only finds room) and must be fully free with 0.3 m margin.
def seg_dist(px, pz, ax, az, bx, bz):
    vx, vz = bx - ax, bz - az
    t = np.clip(((px - ax) * vx + (pz - az) * vz) / (vx * vx + vz * vz), 0, 1)
    return np.hypot(px - (ax + t * vx), pz - (az + t * vz))
gx = x0 + (np.arange(nx) + 0.5) * RES
gz = z0 + (np.arange(nz) + 0.5) * RES
GX, GZ = np.meshgrid(gx, gz, indexing='ij')
dA = seg_dist(GX, GZ, recv_port[0], recv_port[2], R['A']['footPort_provisional'][0], R['A']['footPort_provisional'][2])
dB = seg_dist(GX, GZ, recv_port[0], recv_port[2], R['B']['footPort_provisional'][0], R['B']['footPort_provisional'][2])
cands = []
for side, keep in ((3.0, 0.9), (4.0, 0.9), (3.0, 1.8 / 2 + 0.3)):
    half = side / 2
    need = clear >= (half * 2 ** .5 + 0.3)        # conservative: disc circumscribing the square + 0.3 margin
    ok = need & (dA >= half * 2 ** .5 + keep) & (dB >= half * 2 ** .5 + keep)
    # restrict to forecourt window (+3 m)
    box = (GX >= fc['x'][0] - 3) & (GX <= fc['x'][1] + 3) & (GZ >= fz0 - 1) & (GZ <= fz1 + 6)
    okb = ok & box
    pick = []
    if okb.any():
        # closest to stair-foot midpoint, i.e. the most useful staging position
        mx = (R['A']['footPort_provisional'][0] + R['B']['footPort_provisional'][0]) / 2
        mz = (R['A']['footPort_provisional'][2] + R['B']['footPort_provisional'][2]) / 2
        dd = np.where(okb, np.hypot(GX - mx, GZ - mz), np.inf)
        k = np.unravel_index(np.argmin(dd), dd.shape)
        pick = [round(float(GX[k]), 3), round(float(GZ[k]), 3)]
    cands.append({'square_m': side, 'keepFromRouteCentreline_m': keep, 'feasibleCentreArea_m2': round(float(okb.sum()) * RES * RES, 2),
                  'nearestToStairMidpoint': pick})
R['stagingCandidates'] = cands

# ---- 8. existing staging proxies vs straight route centrelines -----------------------------------------
# U2/U3 bag proxies sit north of the canopy (between check table and stairs) = an existing C staging proxy.
def box_seg_dist(lo, hi, a, b, n=400):
    t = np.linspace(0, 1, n)
    px = a[0] + (b[0] - a[0]) * t
    pz = a[2] + (b[2] - a[2]) * t
    dx = np.maximum(0, np.maximum(lo[0] - px, px - hi[0]))
    dz = np.maximum(0, np.maximum(lo[2] - pz, pz - hi[2]))
    return float(np.hypot(dx, dz).min())
R['existingProxiesVsRoutes'] = {}
for n in sorted(x for x in parts if x.startswith('C_bag')):
    lo, hi = parts[n]
    R['existingProxiesVsRoutes'][n] = {
        'footprint_m': [round(float(hi[0] - lo[0]), 3), round(float(hi[2] - lo[2]), 3)], 'height_m': round(float(hi[1] - lo[1]), 3),
        'distToStraightRoute_A_m': round(box_seg_dist(lo, hi, recv_port, R['A']['footPort_provisional']), 3),
        'distToStraightRoute_B_m': round(box_seg_dist(lo, hi, recv_port, R['B']['footPort_provisional']), 3)}
# max envelope width that fits on the *straight* centreline (2 x min clearance sampled along it)
for w in ('A', 'B'):
    f = R[w]['footPort_provisional']
    t = np.linspace(0, 1, 600)                  # receiving port -> point 1.0 m south of the stair foot
    tx, tz = f[0], f[2] + 1.0
    px = recv_port[0] + (tx - recv_port[0]) * t
    pz = recv_port[2] + (tz - recv_port[2]) * t
    cl = np.array([clear[ij(x, z)] for x, z in zip(px, pz)])
    k = int(cl.argmin())
    R[w]['straightRouteMaxEnvelope_m'] = round(float(2 * cl.min()), 3)
    R[w]['straightRoutePinchAt'] = [round(float(px[k]), 3), round(float(pz[k]), 3)]

os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
json.dump(R, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps({k: R[k] for k in ('ground', 'v1_vs_city_architecture', 'occupancy', 'forecourt', 'connectivity', 'stagingCandidates')}, ensure_ascii=False, indent=1))
for w in ('A', 'B'):
    print(w, json.dumps({k: v for k, v in R[w].items() if k != 'steps'}, ensure_ascii=False))
