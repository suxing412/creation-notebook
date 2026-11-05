# LY-040 prep: list up-facing horizontal faces (z<1.3 m) of the city granary group LOD0 per height band, to locate A/B stair feet
# and the receiving area relative to the C road north port P_N (2285.714, 3647.469, 0.2).
# Usage: python -I granary_steps.py <granary-city-LOD0.glb>
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbinspect as g
js, b = g.load(sys.argv[1])
for i, n, W, pth in g.walk(js):
    if 'mesh' not in n: continue
    ts = []
    for p in js['meshes'][n['mesh']]['primitives']:
        pos = g.acc(js, b, p['attributes']['POSITION']).astype(float); wp = (W[:3, :3] @ pos.T).T + W[:3, 3]
        nat = np.c_[wp[:, 0], -wp[:, 2], wp[:, 1]]
        ts.append(nat[g.acc(js, b, p['indices']).reshape(-1).astype(np.int64)].reshape(-1, 3, 3))
    t = np.concatenate(ts)
    nz = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]); L = np.linalg.norm(nz, axis=1); ok = L > 1e-12
    t = t[ok]; nz = nz[ok, 2] / L[ok]
    up = t[(nz > 0.999) & (t[:, :, 2].max(1) < 1.3)]
    if not len(up): continue
    zs = np.round(up[:, :, 2].mean(1), 3)
    print(n['name'])
    for z in sorted(set(zs.tolist())):
        u = up[zs == z]
        # cluster by x-centre to separate A and B
        cx = u[:, :, 0].mean(1)
        for side, m in (('W(x<2285.7)', cx < 2285.714), ('E(x>=2285.7)', cx >= 2285.714)):
            if m.any():
                v = u[m]
                print('   z=%.3f %s x[%.3f,%.3f] y[%.3f,%.3f] tris=%d' % (z, side, v[:, :, 0].min(), v[:, :, 0].max(), v[:, :, 1].min(), v[:, :, 1].max(), len(v)))
