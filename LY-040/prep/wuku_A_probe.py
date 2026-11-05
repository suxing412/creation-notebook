# LY-040 prep (what-if, not an installation): place library wuku-A-LOD0 at the same anchor as the placed B
# (2316.326904296875, 3500.0, 0) without rotation and report its stair up-faces and plan overlap with the C road east leg
# (x 2314.827..2317.827, y 3487.5..3490.0) and the B support patch (x 2307.327..2329.327, y 3490..3510).
# Usage: python -I wuku_A_probe.py <wuku-A-LOD0.glb>
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbinspect as g
js, b = g.load(sys.argv[1]); TX, TY = 2316.326904296875, 3500.0
for i, n, W, pth in g.walk(js):
    if 'mesh' not in n or 'earth' not in n['name']: continue
    ts = []
    for p in js['meshes'][n['mesh']]['primitives']:
        pos = g.acc(js, b, p['attributes']['POSITION']).astype(float); wp = (W[:3, :3] @ pos.T).T + W[:3, 3]
        nat = np.c_[wp[:, 0] + TX, -wp[:, 2] + TY, wp[:, 1]]
        ts.append(nat[g.acc(js, b, p['indices']).reshape(-1).astype(np.int64)].reshape(-1, 3, 3))
    e = np.concatenate(ts)
    nz = np.cross(e[:, 1] - e[:, 0], e[:, 2] - e[:, 0]); nz = nz[:, 2] / np.linalg.norm(nz, axis=1)
    up = e[nz > 0.999]; zs = np.round(up[:, :, 2].mean(1), 3)
    for z in sorted(set(zs.tolist())):
        t = up[zs == z]
        if z < 0.7: print('A up-face z=%.3f x[%.3f,%.3f] y[%.3f,%.3f]' % (z, t[:, :, 0].min(), t[:, :, 0].max(), t[:, :, 1].min(), t[:, :, 1].max()))
    x0, x1, y0, y1 = e[:, :, 0].min(), e[:, :, 0].max(), e[:, :, 1].min(), e[:, :, 1].max()
    print('A earth footprint x[%.3f,%.3f] y[%.3f,%.3f]' % (x0, x1, y0, y1))
    print('beyond patch south edge (m):', round(3490.0 - y0, 3))
    ov = (min(x1, 2317.827) - max(x0, 2314.827), min(y1, 3490.0) - max(y0, 3487.5))
    print('plan AABB overlap with road east leg (m x m):', [round(v, 3) for v in ov] if min(ov) > 0 else 'none')
