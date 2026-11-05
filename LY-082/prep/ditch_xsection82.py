# LY-082 prep: x-section of the south-ground ditch in front of C02-010 (read-only).
# python -I ditch_xsection82.py <lab_root> <out.json>
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbio82 import prim_tris
lab, out = sys.argv[1].rstrip('/'), sys.argv[2]
T = prim_tris(lab + '/docs/cities/luoyang/assets/ground-atomic/south.glb')[0]['tris']
mn = T.min(1); mx = T.max(1)
T = T[(mx[:, 0] >= 515) & (mn[:, 0] <= 550) & (mx[:, 2] >= -807) & (mn[:, 2] <= -793)]
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
xs = np.round(np.arange(518.0, 548.01, 0.5), 3)
R = {'upTrisInWindow': int(len(T)), 'rows': {}}
for z in [-804.4, -804.0, -803.7, -803.3, -797.6, -796.2]:
    R['rows'][str(z)] = [[float(x), round(h(x, z), 4)] for x in xs]
# vertices of the window (unique), to show the grid the terrain was built on
V = np.unique(np.round(T.reshape(-1, 3), 4), axis=0)
R['uniqueVertexZ_in_window'] = sorted(set(np.round(V[:, 2], 3).tolist()))
R['uniqueVertexX_in_window_518_548'] = sorted(set(np.round(V[(V[:, 0] >= 518) & (V[:, 0] <= 548), 0], 3).tolist()))
json.dump(R, open(out, 'w'), indent=1)
for z, row in R['rows'].items():
    print(z, ' '.join('%.1f:%.3f' % (x, y) for x, y in row if y is not None and y < 0.1995 or x in (526.0, 527.5, 529.0)))
print('Z verts', R['uniqueVertexZ_in_window'][:80])
print('X verts n', len(R['uniqueVertexX_in_window_518_548']), R['uniqueVertexX_in_window_518_548'][:60])
