# LY-082 prep: generic gate->lane corridor probe (read-only).
# Usage: python -I measure_corridor82.py <lab_root> <city-nodes-near.json> <out.json> <court_id> [--drop-ground NAME ...] [--grid 0.05] [--reach 14]
# For a courtyard node: derives the gate opening from the A2 local opening (x -4.975..-2.000 at local z=+12,
# measured by LY-048 prep, LOD0 = LOD1) through the node matrix, then samples the four ground atoms along the
# outward normal for --reach metres. Reports per-row y range, ground sources, stacked layers from different
# files (overlap = potential double floor), step/slope, and building triangles entering the body box.
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbio82 import prim_tris, sha256, translation

lab = sys.argv[1].rstrip('/'); CD = json.load(open(sys.argv[2], encoding='utf-8')); out = sys.argv[3]; cid = sys.argv[4]
args = sys.argv[5:]
drop = set(); grid = 0.05; reach = 14.0
for i, a in enumerate(args):
    if a == '--drop-ground': drop.add(args[i + 1])
    if a == '--grid': grid = float(args[i + 1])
    if a == '--reach': reach = float(args[i + 1])
L = lab + '/docs/cities/luoyang/'
GROUNDS = {'network-ground-stitched': [0, 0, 0], 'retained': [0, 0, 0], 'south': [0, 0, 0], 'D08': [580, 0, -960]}
GATE_LOCAL = {'courtyard-A2': (-4.975, -2.000, 12.0)}  # LY-048 prep measure (x0, x1, z_front)
BODY = (0.205, 2.2)  # body box above y=0.2 ground; C engineering value, not a norm


def mat(m):
    return np.array(m, dtype=np.float64).reshape(4, 4).T


node = CD['nodes'][cid]; asset = CD['assets'][node['asset']]
M = mat(node['matrix'])
gx0, gx1, gz = GATE_LOCAL[node['asset']]
# local frame: u along gate (local x), v outward (local +z)
P0 = (M @ [gx0, 0.2, gz, 1])[:3]; P1 = (M @ [gx1, 0.2, gz, 1])[:3]
nrm = (M[:3, :3] @ [0, 0, 1]); nrm = nrm / np.linalg.norm(nrm)
u = (P1 - P0); width = float(np.linalg.norm(u)); u = u / width

prims = []
for g, t in GROUNDS.items():
    if g in drop:
        continue
    for pr in prim_tris(L + 'assets/ground-atomic/' + g + '.glb', translation(t)):
        pr['file'] = g; prims.append(pr)

# sample points in the corridor (local u in [0,width], v in [0,reach])
nu = int(round(width / grid)); nv = int(round(reach / grid))
us = (np.arange(nu) + 0.5) * grid; vs = (np.arange(nv) + 0.5) * grid
UU, VV = np.meshgrid(us, vs)
PX = P0[0] + UU * u[0] + VV * nrm[0]; PZ = P0[2] + UU * u[2] + VV * nrm[2]
top = np.full(PX.shape, -np.inf); src = np.full(PX.shape, -1)
# per-file top heights to detect stacked floors from different files
perfile = {}
xmin, xmax, zmin, zmax = PX.min(), PX.max(), PZ.min(), PZ.max()
for pi, pr in enumerate(prims):
    T = pr['tris']; mn = T.min(1); mx = T.max(1)
    T = T[(mx[:, 0] >= xmin) & (mn[:, 0] <= xmax) & (mx[:, 2] >= zmin) & (mn[:, 2] <= zmax)]
    if not len(T):
        continue
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); T = T[n[:, 1] / (np.linalg.norm(n, axis=1) + 1e-30) > 0.3]
    pf = perfile.setdefault(pr['file'], np.full(PX.shape, -np.inf))
    for a, b, c in T:
        bx0, bx1 = min(a[0], b[0], c[0]), max(a[0], b[0], c[0]); bz0, bz1 = min(a[2], b[2], c[2]), max(a[2], b[2], c[2])
        m = (PX >= bx0) & (PX <= bx1) & (PZ >= bz0) & (PZ <= bz1)
        if not m.any():
            continue
        d = (b[2] - c[2]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[2] - c[2])
        if abs(d) < 1e-14:
            continue
        X = PX[m]; Z = PZ[m]
        l1 = ((b[2] - c[2]) * (X - c[0]) + (c[0] - b[0]) * (Z - c[2])) / d
        l2 = ((c[2] - a[2]) * (X - c[0]) + (a[0] - c[0]) * (Z - c[2])) / d
        l3 = 1 - l1 - l2
        ins = (l1 >= -1e-9) & (l2 >= -1e-9) & (l3 >= -1e-9)
        Y = np.where(ins, l1 * a[1] + l2 * b[1] + l3 * c[1], -np.inf)
        t0 = top[m]; s0 = src[m]; better = Y > t0
        t0[better] = Y[better]; s0[better] = pi; top[m] = t0; src[m] = s0
        p0 = pf[m]; pf[m] = np.maximum(p0, Y)

R = {'court': cid, 'asset': node['asset'], 'matrix': node['matrix'], 'grid_m': grid, 'reach_m': reach, 'droppedGrounds': sorted(drop),
     'gateWorld': {'p0': P0.round(4).tolist(), 'p1': P1.round(4).tolist(), 'width_m': round(width, 4), 'outwardNormal': nrm.round(4).tolist()},
     'inputs': {g: sha256(L + 'assets/ground-atomic/' + g + '.glb') for g in GROUNDS}}
fin = np.isfinite(top)
R['cells'] = int(top.size); R['noGroundCells'] = int((~fin).sum())
if (~fin).any():
    rows = np.where((~fin).any(axis=1))[0]
    R['firstNoGround_v_m'] = round(float(vs[rows[0]]), 3)
srcc = {}
for k in np.unique(src):
    key = 'none' if k < 0 else prims[k]['file'] + ':' + prims[k]['node'] + ':' + str(prims[k]['material'])
    srcc[key] = int((src == k).sum())
R['topSourceCells'] = srcc
# stacked: >=2 files have an up-face at the same cell
cnt = sum(np.isfinite(v).astype(int) for v in perfile.values()) if perfile else np.zeros(PX.shape, int)
R['cellsWithUpFacesFromGe2Files'] = int((cnt >= 2).sum())
if (cnt >= 2).any():
    vals = [v for v in perfile.values()]
    st = np.stack(vals); st[~np.isfinite(st)] = np.nan
    sep = np.nanmax(st, 0) - np.nanmin(st, 0)
    R['stackedVerticalSeparation_m'] = {'max': round(float(np.nanmax(sep[cnt >= 2])), 4), 'min': round(float(np.nanmin(sep[cnt >= 2])), 4)}
    R['stackedFiles'] = sorted(perfile.keys())
if fin.all():
    dv = np.abs(np.diff(top, axis=0)); du = np.abs(np.diff(top, axis=1))
    R['y'] = {'min': round(float(top.min()), 4), 'max': round(float(top.max()), 4)}
    R['maxAdjacentStep_m'] = round(float(max(dv.max(), du.max() if du.size else 0)), 4)
    R['maxSlope_pct'] = round(float(max(dv.max(), du.max() if du.size else 0) / grid * 100), 2)
    rmin = top.min(1); k = int(np.argmin(rmin))
    R['lowest'] = {'v_m': round(float(vs[k]), 3), 'y': round(float(rmin[k]), 4)}
    R['yAtBoundary_v0'] = {'min': round(float(top[0].min()), 4), 'max': round(float(top[0].max()), 4)}
step = max(1, int(round(0.25 / grid)))
R['profile_v_ymin_ymax'] = [[round(float(vs[j]), 3),
                              (round(float(top[j][np.isfinite(top[j])].min()), 4) if np.isfinite(top[j]).any() else None),
                              (round(float(top[j][np.isfinite(top[j])].max()), 4) if np.isfinite(top[j]).any() else None)] for j in range(0, nv, step)]
# building triangles entering the body box (AABB-vs-oriented box, conservative via corner test in local frame)
Minv = np.linalg.inv(M)
hits = {}
for lod in (0, 1):
    hl = []
    for nid, nd in CD['nodes'].items():
        if not nid.startswith('C02-'):
            continue
        a = CD['assets'][nd['asset']]
        p = L + (a['nearUrl'].split('/docs/cities/luoyang/')[1] if lod == 0 else a['sourcePath'])
        for pr in prim_tris(p, mat(nd['matrix']), skip=tuple(a['excludeNodes'])):
            V = pr['tris'].reshape(-1, 3)
            loc = (Minv @ np.c_[V, np.ones(len(V))].T).T[:, :3].reshape(-1, 3, 3)
            mn = loc.min(1); mx = loc.max(1)
            s = (mx[:, 0] > gx0) & (mn[:, 0] < gx1) & (mx[:, 1] > BODY[0]) & (mn[:, 1] < BODY[1]) & (mx[:, 2] > gz + 0.05) & (mn[:, 2] < gz + reach)
            if s.any():
                hl.append({'court': nid, 'node': pr['node'], 'tris': int(s.sum()), 'localZmin': round(float(mn[s, 2].min()), 3)})
    hits['LOD%d' % lod] = hl
R['bodyBox_local'] = {'x': [gx0, gx1], 'y': list(BODY), 'z': [gz + 0.05, gz + reach], 'note': 'triangle AABB in C02 local frame; conservative, not swept-body collision'}
R['bodyBoxHits'] = hits
json.dump(R, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in R.items() if k != 'profile_v_ymin_ymax'}, ensure_ascii=False))
