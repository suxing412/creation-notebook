# LY-040 prep: straight-line clearance probe from the C road north port P_N to each granary stair foot,
# through the receiving forecourt of granary-city-LOD0. Plan point-in-triangle against all non-ground triangles
# whose z-range overlaps [ground+0.02, ground+2.0]. Probe body widths 0.9 m and 1.8 m; 0.1 m along-step.
# This is a discrete probe, not continuous body motion. Usage: python -I forecourt_clear.py <granary-city-LOD0.glb>
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbinspect as g
js, b = g.load(sys.argv[1]); obst = []
for i, n, W, pth in g.walk(js):
    if 'mesh' not in n or 'ground' in n['name']: continue
    for p in js['meshes'][n['mesh']]['primitives']:
        pos = g.acc(js, b, p['attributes']['POSITION']).astype(float); wp = (W[:3, :3] @ pos.T).T + W[:3, 3]
        nat = np.c_[wp[:, 0], -wp[:, 2], wp[:, 1]]
        t = nat[g.acc(js, b, p['indices']).reshape(-1).astype(np.int64)].reshape(-1, 3, 3)
        obst.append((n['name'], t))
G = 0.2
def blocked(x, y):
    hits = []
    for nm, t in obst:
        zmin, zmax = t[:, :, 2].min(1), t[:, :, 2].max(1)
        m = (zmax > G + 0.02) & (zmin < G + 2.0)
        tt = t[m]
        if not len(tt): continue
        a, b_, c = tt[:, 0, :2], tt[:, 1, :2], tt[:, 2, :2]
        def s(p1, p2): return (x - p2[:, 0]) * (p1[:, 1] - p2[:, 1]) - (p1[:, 0] - p2[:, 0]) * (y - p2[:, 1])
        d1, d2, d3 = s(a, b_), s(b_, c), s(c, a)
        neg = (d1 < 0) | (d2 < 0) | (d3 < 0); pos = (d1 > 0) | (d2 > 0) | (d3 > 0)
        inside = ~(neg & pos)
        if inside.any(): hits.append(nm.split('static_')[-1])
    return hits
PN = (2285.714, 3647.469)
feet = {'A_stair_foot': (2273.714, 3674.60), 'B_stair_foot': (2297.714, 3674.50)}
for k, f in feet.items():
    for w in (0.0, 0.9, 1.8):
        L = np.hypot(f[0] - PN[0], f[1] - PN[1]); u = ((f[0] - PN[0]) / L, (f[1] - PN[1]) / L); nrm = (-u[1], u[0])
        first = None; count = 0; tot = 0
        offs = [0.0] if w == 0 else np.linspace(-w / 2, w / 2, 5)
        for s in np.arange(0.05, L - 0.05, 0.1):
            for o in offs:
                x, y = PN[0] + u[0] * s + nrm[0] * o, PN[1] + u[1] * s + nrm[1] * o
                tot += 1; h = blocked(x, y)
                if h:
                    count += 1
                    if first is None: first = (round(s, 2), round(x, 3), round(y, 3), sorted(set(h)))
        print(k, 'width', w, 'length_m', round(L, 2), 'blocked samples', count, '/', tot, 'first', first)
# negative control: straight north along the road axis must hit the checking table/receiving geometry
f = (2285.714, 3668.0)
L = f[1] - PN[1]; first = None; cnt = 0
for s in np.arange(0.05, L, 0.1):
    h = blocked(PN[0], PN[1] + s)
    if h:
        cnt += 1
        if first is None: first = (round(s, 2), round(PN[1] + s, 3), sorted(set(h)))
print('NEGATIVE axis-north probe blocked samples', cnt, 'first', first, 'EXPECT blocked>0')
