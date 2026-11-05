# LY-082 prep: compare Blender ray heights (blender-xcheck.json) with numpy barycentric heights at the same points.
# python -I xcheck_compare82.py <lab_root> <blender-xcheck.json> <out.json>
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbio82 import prim_tris, translation
lab, bx, out = sys.argv[1].rstrip('/'), sys.argv[2], sys.argv[3]
L = lab + '/docs/cities/luoyang/assets/ground-atomic/'
T = np.concatenate([p['tris'] for g, t in [('network-ground-stitched', [0, 0, 0]), ('retained', [0, 0, 0]), ('south', [0, 0, 0]), ('D08', [580, 0, -960])]
                    for p in prim_tris(L + g + '.glb', translation(t))])
n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); T = T[n[:, 1] / (np.linalg.norm(n, axis=1) + 1e-30) > 0.3]
mn = T.min(1); mx = T.max(1)
def h(x, z):
    s = (mn[:, 0] <= x) & (mx[:, 0] >= x) & (mn[:, 2] <= z) & (mx[:, 2] >= z); best = None
    for a, b, c in T[s]:
        d = (b[2] - c[2]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[2] - c[2])
        if abs(d) < 1e-14: continue
        l1 = ((b[2] - c[2]) * (x - c[0]) + (c[0] - b[0]) * (z - c[2])) / d
        l2 = ((c[2] - a[2]) * (x - c[0]) + (a[0] - c[0]) * (z - c[2])) / d
        l3 = 1 - l1 - l2
        if min(l1, l2, l3) >= -1e-9:
            y = l1 * a[1] + l2 * b[1] + l3 * c[1]; best = y if best is None else max(best, y)
    return best
B = json.load(open(bx))
rows = []
for r in B['rays']:
    y = h(r['gltf_x'], r['gltf_z'])
    rows.append({'court': r['court'], 'x': r['gltf_x'], 'z': r['gltf_z'], 'blender': r['y_gltf'], 'numpy': None if y is None else round(y, 5),
                 'diff_m': None if (y is None or r['y_gltf'] is None) else round(abs(y - r['y_gltf']), 5)})
d = [r['diff_m'] for r in rows if r['diff_m'] is not None]
R = {'n': len(rows), 'bothHit': len(d), 'maxDiff_m': max(d), 'rows': rows}
json.dump(R, open(out, 'w'), indent=1); print(R['n'], R['bothHit'], R['maxDiff_m'])
