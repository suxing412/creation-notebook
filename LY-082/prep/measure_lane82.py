# LY-082 prep measurement (read-only). Usage:
#   python -I measure_lane82.py <lab_root> <city-nodes-near.json> <out.json> [--drop-ground south] [--grid 0.05]
# Measures, in world coords (x east, y up, z = -north):
#  A. top-surface heightfield of the four loaded ground atoms in the strip between
#     C02-010's front lot edge (z=-806.45) and the opposite row (C02-006 lot edge z=-793.70),
#     x 518..548; plus the gate corridor profile (gate opening x 526.025..529.0);
#  B. lane band along the C02_access band (land-contract north 796.5..803.5 = z -803.5..-796.5)
#     across x 380..712 (south domain and both ends);
#  C. building triangles (C02-005/006/009/010/011, LOD0 and LOD1, excludeNodes applied)
#     whose AABB enters the body box gate -> lane centre (x 526.025..529.0, y 0.205..2.2, z -806.40..-800);
#  D. extents of the excluded prototype site nodes of C02-010 (what the city removed).
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbio82 import prim_tris, sha256, translation

lab = sys.argv[1].rstrip('/'); cdpath = sys.argv[2]; out = sys.argv[3]
args = sys.argv[4:]
drop = set(); grid = 0.05
for i, a in enumerate(args):
    if a == '--drop-ground': drop.add(args[i + 1])
    if a == '--grid': grid = float(args[i + 1])
L = lab + '/docs/cities/luoyang/'
GROUNDS = {'network-ground-stitched': [0, 0, 0], 'retained': [0, 0, 0], 'south': [0, 0, 0], 'D08': [580, 0, -960]}
CD = json.load(open(cdpath, encoding='utf-8'))


def mat(m):
    return np.array(m, dtype=np.float64).reshape(4, 4).T


def ground_prims():
    res = []
    for g, t in GROUNDS.items():
        if g in drop:
            continue
        p = L + 'assets/ground-atomic/' + g + '.glb'
        for pr in prim_tris(p, translation(t)):
            pr['file'] = g
            res.append(pr)
    return res


def heightfield(prims, x0, x1, z0, z1, h, nmin=0.3):
    nx = int(round((x1 - x0) / h)); nz = int(round((z1 - z0) / h))
    xs = x0 + (np.arange(nx) + 0.5) * h; zs = z0 + (np.arange(nz) + 0.5) * h
    top = np.full((nz, nx), -np.inf); src = np.full((nz, nx), -1, dtype=np.int32)
    layers = np.zeros((nz, nx), dtype=np.int32)
    names = []
    for pi, pr in enumerate(prims):
        T = pr['tris']
        mn = T.min(1); mx = T.max(1)
        sel = (mx[:, 0] >= x0) & (mn[:, 0] <= x1) & (mx[:, 2] >= z0) & (mn[:, 2] <= z1)
        T = T[sel]
        if not len(T):
            continue
        n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); nl = np.linalg.norm(n, axis=1) + 1e-30
        T = T[n[:, 1] / nl > nmin]
        names.append((pi, pr['file'], pr['node'], pr['material'], int(len(T))))
        for tri in T:
            a, b, c = tri
            ix0 = max(0, int(math.floor((min(a[0], b[0], c[0]) - x0) / h - 0.5)))
            ix1 = min(nx - 1, int(math.ceil((max(a[0], b[0], c[0]) - x0) / h - 0.5)))
            iz0 = max(0, int(math.floor((min(a[2], b[2], c[2]) - z0) / h - 0.5)))
            iz1 = min(nz - 1, int(math.ceil((max(a[2], b[2], c[2]) - z0) / h - 0.5)))
            if ix1 < ix0 or iz1 < iz0:
                continue
            X, Z = np.meshgrid(xs[ix0:ix1 + 1], zs[iz0:iz1 + 1])
            d = (b[2] - c[2]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[2] - c[2])
            if abs(d) < 1e-14:
                continue
            l1 = ((b[2] - c[2]) * (X - c[0]) + (c[0] - b[0]) * (Z - c[2])) / d
            l2 = ((c[2] - a[2]) * (X - c[0]) + (a[0] - c[0]) * (Z - c[2])) / d
            l3 = 1 - l1 - l2
            ins = (l1 >= -1e-9) & (l2 >= -1e-9) & (l3 >= -1e-9)
            if not ins.any():
                continue
            Y = l1 * a[1] + l2 * b[1] + l3 * c[1]
            sub = top[iz0:iz1 + 1, ix0:ix1 + 1]; ss = src[iz0:iz1 + 1, ix0:ix1 + 1]; ll = layers[iz0:iz1 + 1, ix0:ix1 + 1]
            better = ins & (Y > sub)
            ll[ins] += 1
            sub[better] = Y[better]; ss[better] = pi
    return xs, zs, top, src, layers, names


def stats(a):
    a = a[np.isfinite(a)]
    return None if not len(a) else {'min': round(float(a.min()), 4), 'max': round(float(a.max()), 4), 'mean': round(float(a.mean()), 4)}


R = {'lab': lab, 'grid_m': grid, 'droppedGrounds': sorted(drop), 'inputs': {}}
for g, t in GROUNDS.items():
    p = L + 'assets/ground-atomic/' + g + '.glb'
    R['inputs']['ground-' + g] = {'path': 'docs/cities/luoyang/assets/ground-atomic/' + g + '.glb', 'sha256': sha256(p), 'translation': t}
G = ground_prims()

# ---- A. strip heightfield
X0, X1, Z0, Z1 = 518.0, 548.0, -806.45, -793.70
xs, zs, top, src, layers, names = heightfield(G, X0, X1, Z0, Z1, grid)
srcc = {}
for k in np.unique(src):
    key = 'none' if k < 0 else G[k]['file'] + ':' + G[k]['node'] + ':' + str(G[k]['material'])
    srcc[key] = srcc.get(key, 0) + int((src == k).sum())
R['A_strip'] = {'bounds_xz': [X0, X1, Z0, Z1], 'cells': int(top.size), 'noGround': int((~np.isfinite(top)).sum()),
                'stackedCells_gt1_upface': int((layers > 1).sum()), 'top': stats(top),
                'sources': [{'file': n[1], 'node': n[2], 'material': n[3], 'upTrisInROI': n[4]} for n in names],
                'topSourceCells': srcc}
gx = (xs >= 526.025) & (xs <= 529.0)
T = top[:, gx]
prof = []
for j, z in enumerate(zs):
    row = T[j]
    f = row[np.isfinite(row)]
    prof.append([round(float(z), 3), round(float(f.min()), 4) if len(f) else None, round(float(f.max()), 4) if len(f) else None])
step = max(1, int(round(0.25 / grid)))
R['A_gateCorridorProfile'] = {'x_range': [526.025, 529.0], 'every_m': step * grid, 'rows_z_ymin_ymax': prof[::step]}
fin = np.isfinite(T).all()
dz = np.abs(np.diff(T, axis=0)); dx = np.abs(np.diff(T, axis=1))
R['A_gateCorridor'] = {'cells': int(T.size), 'noGround': int((~np.isfinite(T)).sum()), 'top': stats(T),
                       'maxAdjacentStep_m': round(float(max(dz.max(), dx.max())), 4) if fin else None,
                       'maxSlopeAlongZ_pct': round(float(dz.max() / grid * 100), 2) if fin else None}
mins = np.array([p[1] if p[1] is not None else np.nan for p in prof])
if np.isfinite(mins).any():
    k = int(np.nanargmin(mins))
    R['A_gateCorridor']['lowest'] = {'z': prof[k][0], 'y': prof[k][1], 'depthBelow0.200_m': round(0.2 - prof[k][1], 4)}
# full-strip per-row profile over all x (to see whether the trough is a continuous E-W feature)
rowmin = [round(float(top[j][np.isfinite(top[j])].min()), 4) if np.isfinite(top[j]).any() else None for j in range(len(zs))]
rowmax = [round(float(top[j][np.isfinite(top[j])].max()), 4) if np.isfinite(top[j]).any() else None for j in range(len(zs))]
R['A_stripRowProfile'] = [[round(float(zs[j]), 3), rowmin[j], rowmax[j]] for j in range(0, len(zs), step)]

# ---- B. lane band
bx0, bx1, h2 = 380.0, 712.0, 0.25
xs2, zs2, top2, src2, lay2, names2 = heightfield(G, bx0, bx1, -803.5, -796.5, h2)
cov = np.isfinite(top2)
colcov = cov.all(axis=0)
gaps = []; inrun = False; s = None
for i, ok in enumerate(colcov):
    if not ok and not inrun:
        s = xs2[i]; inrun = True
    if ok and inrun:
        gaps.append([round(float(s), 3), round(float(xs2[i - 1]), 3)]); inrun = False
if inrun:
    gaps.append([round(float(s), 3), round(float(xs2[-1]), 3)])
srcfile = {}
for k in np.unique(src2):
    key = 'none' if k < 0 else G[k]['file'] + ':' + G[k]['node'] + ':' + str(G[k]['material'])
    srcfile[key] = srcfile.get(key, 0) + int((src2 == k).sum())
ci = int(np.argmin(np.abs(zs2 + 800.0)))
cent = top2[ci]
# x-extent per source along centreline
ext = {}
for i in range(len(xs2)):
    k = src2[ci, i]
    key = 'none' if k < 0 else G[k]['file'] + ':' + str(G[k]['material'])
    e = ext.setdefault(key, [float(xs2[i]), float(xs2[i]), 0]); e[0] = min(e[0], float(xs2[i])); e[1] = max(e[1], float(xs2[i])); e[2] += 1
R['B_laneBand'] = {'bounds_xz': [bx0, bx1, -803.5, -796.5], 'grid_m': h2, 'cells': int(top2.size), 'noGround': int((~cov).sum()),
                   'columnsNotFullyCovered_xRuns': gaps, 'top': stats(top2), 'stackedCells_gt1_upface': int((lay2 > 1).sum()),
                   'topSourceCells': srcfile, 'centrelineZ': round(float(zs2[ci]), 3),
                   'centrelineSourceExtentX': {k: [round(v[0], 3), round(v[1], 3), v[2]] for k, v in ext.items()},
                   'centreline_y_every_10m': [[round(float(xs2[i]), 2), (round(float(cent[i]), 4) if np.isfinite(cent[i]) else None)] for i in range(0, len(xs2), 40)]}
seg = (xs2 >= 486) & (xs2 <= 710)
R['B_laneBand']['southDomainOnly'] = {'noGround': int((~cov[:, seg]).sum()), 'top': stats(top2[:, seg])}


# ---- C. corridor body-box clearance against buildings
def apath(a, lod):
    # city-data exports {sourcePath, nearUrl}; nearUrl is .../docs/cities/luoyang/<rel>
    if lod == 0:
        return L + a['nearUrl'].split('/docs/cities/luoyang/')[1]
    return L + a['sourcePath']


def court_prims(node, lod):
    a = CD['assets'][node['asset']]
    p = apath(a, lod)
    return prim_tris(p, mat(node['matrix']), skip=tuple(a['excludeNodes'])), p


C = {}
for lod in (0, 1):
    hits = []; files = {}
    for nid in ['C02-005', 'C02-006', 'C02-009', 'C02-010', 'C02-011']:
        node = CD['nodes'][nid]
        prs, p = court_prims(node, lod)
        files[nid] = {'file': p.replace(L, ''), 'sha256': sha256(p)}
        for pr in prs:
            Tt = pr['tris']; mn = Tt.min(1); mx = Tt.max(1)
            sl = (mx[:, 0] > 526.025) & (mn[:, 0] < 529.0) & (mx[:, 1] > 0.205) & (mn[:, 1] < 2.2) & (mx[:, 2] > -806.40) & (mn[:, 2] < -800.0)
            if sl.any():
                hits.append({'court': nid, 'node': pr['node'], 'tris': int(sl.sum()), 'zmax': round(float(mx[sl, 2].max()), 4),
                             'zmin': round(float(mn[sl, 2].min()), 4)})
    C['LOD%d' % lod] = {'files': files, 'corridorBox': {'x': [526.025, 529.0], 'y': [0.205, 2.2], 'z': [-806.40, -800.0]}, 'triAABBHits': hits}
R['C_corridorClearance'] = C

# ---- D. excluded site nodes of C02-010
node = CD['nodes']['C02-010']; D = {}
for lod in (0, 1):
    a = CD['assets'][node['asset']]
    p = apath(a, lod)
    for pr in prim_tris(p, mat(node['matrix'])):
        if pr['node'] in a['excludeNodes']:
            V = pr['tris'].reshape(-1, 3)
            D.setdefault('LOD%d' % lod, {})[pr['node']] = {'tris': int(len(pr['tris'])), 'min': V.min(0).round(4).tolist(), 'max': V.max(0).round(4).tolist()}
R['D_excludedSiteNodes_C02-010'] = D
json.dump(R, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps({k: R[k] for k in ('A_strip', 'A_gateCorridor', 'B_laneBand', 'C_corridorClearance', 'D_excludedSiteNodes_C02-010')}, ensure_ascii=False, indent=1)[:9000])
