# LY-040 prep: locate wuku-B stair foot / up-facing tread heights in the placed mother chunk and its margin to the support patch.
# Usage: python -I stair_foot.py <wuku_C_with_support-01.glb>
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbinspect as g
js, b = g.load(sys.argv[1]); T = {}
for i, n, W, pth in g.walk(js):
    if 'mesh' not in n: continue
    ts = []
    for p in js['meshes'][n['mesh']]['primitives']:
        pos = g.acc(js, b, p['attributes']['POSITION']).astype(float); wp = (W[:3, :3] @ pos.T).T + W[:3, 3]
        nat = np.c_[wp[:, 0], -wp[:, 2], wp[:, 1]]
        ts.append(nat[g.acc(js, b, p['indices']).reshape(-1).astype(np.int64)].reshape(-1, 3, 3))
    T[n['name']] = np.concatenate(ts)
e = [v for k, v in T.items() if 'static_earth' in k][0]
nz = np.cross(e[:, 1] - e[:, 0], e[:, 2] - e[:, 0]); nz = nz[:, 2] / np.linalg.norm(nz, axis=1)
up = e[nz > 0.999]
zs = np.round(up[:, :, 2].mean(1), 3)
for z in sorted(set(zs.tolist())):
    t = up[zs == z]
    print('up-face z=%.3f  x[%.3f,%.3f] y[%.3f,%.3f] tris=%d' % (z, t[:, :, 0].min(), t[:, :, 0].max(), t[:, :, 1].min(), t[:, :, 1].max(), len(t)))
patch = [v for k, v in T.items() if 'SUPPORT_PATCH' in k][0]
print('patch x[%.3f,%.3f] y[%.3f,%.3f] ztop %.3f' % (patch[:, :, 0].min(), patch[:, :, 0].max(), patch[:, :, 1].min(), patch[:, :, 1].max(), patch[:, :, 2].max()))
print('earth footprint x[%.3f,%.3f] y[%.3f,%.3f]' % (e[:, :, 0].min(), e[:, :, 0].max(), e[:, :, 1].min(), e[:, :, 1].max()))
tm = [v for k, v in T.items() if 'static_timber' in k][0]
print('timber footprint x[%.3f,%.3f] y[%.3f,%.3f] zmin %.3f' % (tm[:, :, 0].min(), tm[:, :, 0].max(), tm[:, :, 1].min(), tm[:, :, 1].max(), tm[:, :, 2].min()))
