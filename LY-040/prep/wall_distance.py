# LY-040 prep: plan (XY native) minimum distance from region footprint corners/edges samples to city wall-A-wall-01 triangle edges.
# Usage: python -I wall_distance.py <wall-01.glb>
import sys, numpy as np, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbinspect as g
js, b = g.load(sys.argv[1]); segs = []
for i, n, W, pth in g.walk(js):
    if 'mesh' not in n: continue
    for p in js['meshes'][n['mesh']]['primitives']:
        pos = g.acc(js, b, p['attributes']['POSITION']).astype(float); wp = (W[:3, :3] @ pos.T).T + W[:3, 3]
        nat = np.c_[wp[:, 0], -wp[:, 2]]
        idx = g.acc(js, b, p['indices']).reshape(-1, 3)
        for t in idx:
            for a, c in ((0, 1), (1, 2), (2, 0)): segs.append((nat[t[a]], nat[t[c]]))
A = np.array([s[0] for s in segs]); B = np.array([s[1] for s in segs])
def d(q):
    q = np.array(q); AB = B - A; t = np.clip(((q - A) * AB).sum(1) / np.maximum((AB * AB).sum(1), 1e-12), 0, 1)
    return np.hypot(*(A + AB * t[:, None] - q).T).min()
boxes = {'granary_ground': (2249.714, 2321.714, 3647.469, 3699.469), 'road': (2284.214, 2317.827, 3484.5, 3647.469), 'wuku_patch': (2307.327, 2329.327, 3490.0, 3510.0)}
for k, (x0, x1, y0, y1) in boxes.items():
    pts = [(x, y) for x in np.linspace(x0, x1, 25) for y in (y0, y1)] + [(x, y) for y in np.linspace(y0, y1, 60) for x in (x0, x1)]
    print(k, 'min plan distance to wall-A-wall-01 m', round(min(d(p) for p in pts), 2))
