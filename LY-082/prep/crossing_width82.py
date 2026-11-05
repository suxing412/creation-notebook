# LY-082 prep: width of the existing south-ground gate crossing over the lane-side ditch (read-only).
# python -I crossing_width82.py <lab_root> <out.json> <x_lo> <x_hi> <z,z,...> [tol_m list]
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbio82 import prim_tris
lab, out = sys.argv[1].rstrip('/'), sys.argv[2]
xlo, xhi = float(sys.argv[3]), float(sys.argv[4]); zs = [float(z) for z in sys.argv[5].split(',')]
T = prim_tris(lab + '/docs/cities/luoyang/assets/ground-atomic/south.glb')[0]['tris']
mn = T.min(1); mx = T.max(1)
T = T[(mx[:, 0] >= xlo - 1) & (mn[:, 0] <= xhi + 1) & (mx[:, 2] >= min(zs) - 1) & (mn[:, 2] <= max(zs) + 1)]
n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); T = T[n[:, 1] / np.linalg.norm(n, axis=1) > 0.3]
def h(x, z):
    best = None
    for a, b, c in T:
        d = (b[2] - c[2]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[2] - c[2])
        if abs(d) < 1e-14: continue
        l1 = ((b[2] - c[2]) * (x - c[0]) + (c[0] - b[0]) * (z - c[2])) / d
        l2 = ((c[2] - a[2]) * (x - c[0]) + (a[0] - c[0]) * (z - c[2])) / d
        l3 = 1 - l1 - l2
        if min(l1, l2, l3) >= -1e-9:
            y = l1 * a[1] + l2 * b[1] + l3 * c[1]; best = y if best is None else max(best, y)
    return best
xs = np.round(np.arange(xlo, xhi + 1e-9, 0.01), 3)
R = {'x_range': [xlo, xhi], 'step': 0.01, 'rows': {}}
for z in zs:
    ys = np.array([h(x, z) for x in xs], dtype=float)
    row = {'ymin': round(float(np.nanmin(ys)), 4), 'ymax': round(float(np.nanmax(ys)), 4)}
    for tol in (0.002, 0.005, 0.010):
        ok = ys >= 0.2 - tol
        if ok.any():
            idx = np.where(ok)[0]
            # largest contiguous run
            runs = np.split(idx, np.where(np.diff(idx) != 1)[0] + 1); r = max(runs, key=len)
            row['flatWithin_%dmm' % int(tol * 1000)] = [float(xs[r[0]]), float(xs[r[-1]]), round(float(xs[r[-1]] - xs[r[0]]), 3)]
    R['rows'][str(z)] = row
json.dump(R, open(out, 'w'), indent=1); print(json.dumps(R))
