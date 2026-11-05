# LY-082 prep: which ground files both put an up-face over the C02_access lane band (read-only).
# python -I layers_laneband82.py <lab_root> <out.json>
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbio82 import prim_tris, translation
lab, out = sys.argv[1].rstrip('/'), sys.argv[2]
L = lab + '/docs/cities/luoyang/assets/ground-atomic/'
x0, x1, z0, z1, h = 380.0, 712.0, -803.5, -796.5, 0.25
nx, nz = int((x1 - x0) / h), int((z1 - z0) / h)
xs = x0 + (np.arange(nx) + 0.5) * h; zs = z0 + (np.arange(nz) + 0.5) * h
per = {}
for g, t in [('network-ground-stitched', [0, 0, 0]), ('retained', [0, 0, 0]), ('south', [0, 0, 0]), ('D08', [580, 0, -960])]:
    top = np.full((nz, nx), -np.inf)
    for pr in prim_tris(L + g + '.glb', translation(t)):
        T = pr['tris']; mn = T.min(1); mx = T.max(1)
        T = T[(mx[:, 0] >= x0) & (mn[:, 0] <= x1) & (mx[:, 2] >= z0) & (mn[:, 2] <= z1)]
        if not len(T): continue
        n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); T = T[n[:, 1] / (np.linalg.norm(n, axis=1) + 1e-30) > 0.3]
        for a, b, c in T:
            i0 = max(0, int(math.floor((min(a[0], b[0], c[0]) - x0) / h - .5))); i1 = min(nx - 1, int(math.ceil((max(a[0], b[0], c[0]) - x0) / h - .5)))
            j0 = max(0, int(math.floor((min(a[2], b[2], c[2]) - z0) / h - .5))); j1 = min(nz - 1, int(math.ceil((max(a[2], b[2], c[2]) - z0) / h - .5)))
            if i1 < i0 or j1 < j0: continue
            X, Z = np.meshgrid(xs[i0:i1 + 1], zs[j0:j1 + 1])
            d = (b[2] - c[2]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[2] - c[2])
            if abs(d) < 1e-14: continue
            l1 = ((b[2] - c[2]) * (X - c[0]) + (c[0] - b[0]) * (Z - c[2])) / d
            l2 = ((c[2] - a[2]) * (X - c[0]) + (a[0] - c[0]) * (Z - c[2])) / d
            l3 = 1 - l1 - l2; ins = (l1 >= -1e-9) & (l2 >= -1e-9) & (l3 >= -1e-9)
            Y = np.where(ins, l1 * a[1] + l2 * b[1] + l3 * c[1], -np.inf)
            sub = top[j0:j1 + 1, i0:i1 + 1]; np.maximum(sub, Y, out=sub)
    per[g] = top
R = {'band_xz': [x0, x1, z0, z1], 'grid_m': h, 'perFileCells': {g: int(np.isfinite(v).sum()) for g, v in per.items()}, 'pairs': {}}
gs = list(per)
for i in range(len(gs)):
    for j in range(i + 1, len(gs)):
        both = np.isfinite(per[gs[i]]) & np.isfinite(per[gs[j]])
        if both.any():
            cols = np.where(both.any(0))[0]
            sep = np.abs(per[gs[i]][both] - per[gs[j]][both])
            R['pairs'][gs[i] + '|' + gs[j]] = {'cells': int(both.sum()), 'x': [round(float(xs[cols[0]]), 3), round(float(xs[cols[-1]]), 3)],
                                               'dy_max': round(float(sep.max()), 4), 'dy_min': round(float(sep.min()), 4)}
json.dump(R, open(out, 'w'), indent=1); print(json.dumps(R))
