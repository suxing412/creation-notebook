# LY-031 prep: finite body-box passage probe through granary A doorway (read-only; not continuous human motion).
# Usage: python -I probe_passage.py <granary-A-LOD*.glb> [--leaf xmin,ymin,zmin,xmax,ymax,zmax ...]
# A body box (width W, height H, depth 0.30 m) is stepped every 0.02 m along local z from the stair foot (z=4.60)
# to inside the granary (z=1.90), centred on x=0. Support = highest upward-facing surface under the footprint.
# Box bottom = support + 0.02 m (foot clearance). Any triangle-box overlap of timber/cargo = failure at that station.
# --leaf adds virtual axis-aligned boxes (e.g. a closed door leaf) as negative controls; nothing is written to GLBs.
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbread as G

GROUND_Y = 0.2


def tri_box(tri, c, h):
    # Akenine-Moller triangle/AABB SAT. tri (3,3), c centre, h half sizes
    v = tri - c
    e = [v[1] - v[0], v[2] - v[1], v[0] - v[2]]
    for i in range(3):
        if v[:, i].min() > h[i] or v[:, i].max() < -h[i]:
            return False
    n = np.cross(e[0], e[1])
    r = np.dot(h, np.abs(n))
    if abs(np.dot(n, v[0])) > r:
        return False
    ax = np.eye(3)
    for ei in e:
        for a in ax:
            L = np.cross(a, ei)
            if np.allclose(L, 0):
                continue
            p = v @ L
            r = np.dot(h, np.abs(L))
            if p.min() > r or p.max() < -r:
                return False
    return True


def run(path, W, H, leaves, eps=1e-4):
    js, res = G.prims(path)
    tris = []
    up = []
    for r in res:
        T = r['pos'][r['tris']]
        tris.append(T)
        n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
        nn = n / np.maximum(np.linalg.norm(n, axis=1), 1e-30)[:, None]
        up.append(T[nn[:, 1] > 0.99])
    T = np.concatenate(tris)
    U = np.concatenate(up)
    for lb in leaves:
        lo, hi = np.array(lb[:3]), np.array(lb[3:])
        # 12 triangles of the virtual box
        c = [[lo[0], lo[1], lo[2]], [hi[0], lo[1], lo[2]], [hi[0], hi[1], lo[2]], [lo[0], hi[1], lo[2]],
             [lo[0], lo[1], hi[2]], [hi[0], lo[1], hi[2]], [hi[0], hi[1], hi[2]], [lo[0], hi[1], hi[2]]]
        c = np.array(c)
        f = [(0, 1, 2), (0, 2, 3), (4, 6, 5), (4, 7, 6), (0, 4, 5), (0, 5, 1), (3, 2, 6), (3, 6, 7), (0, 3, 7), (0, 7, 4), (1, 5, 6), (1, 6, 2)]
        T = np.concatenate([T, c[np.array(f)]])
    D = 0.30
    fails, stations = [], 0
    supports = []
    prev = GROUND_Y  # city ground top measured 0.2 m (granary-city-LOD0 original_city_ground_preserved)
    STEP_UP = 0.35   # a support face more than this above the previous support is not reachable by stepping
    for z in np.arange(4.60, 1.90 - 1e-9, -0.02):
        stations += 1
        x0, x1, z0, z1 = -W / 2, W / 2, z - D / 2, z + D / 2
        # support: upward faces whose xz bbox overlaps footprint
        m = (U[:, :, 0].max(1) > x0) & (U[:, :, 0].min(1) < x1) & (U[:, :, 2].max(1) > z0) & (U[:, :, 2].min(1) < z1)
        ys = U[m][:, :, 1].max(1) if m.any() else np.zeros(0)
        ys = ys[ys <= prev + STEP_UP]
        sup = max([GROUND_Y] + ys.tolist()) if (ys.size or GROUND_Y <= prev + STEP_UP) else None
        if sup is None:
            fails.append({'z': round(float(z), 3), 'reason': 'no support'})
            continue
        prev = sup
        supports.append(sup)
        y0, y1 = sup + 0.02, sup + H
        c = np.array([0.0, (y0 + y1) / 2, z]); h = np.array([W / 2 - eps, (y1 - y0) / 2 - eps, D / 2 - eps])
        # broad phase
        bm = (T[:, :, 0].max(1) > -W / 2) & (T[:, :, 0].min(1) < W / 2) & (T[:, :, 1].max(1) > y0) & (T[:, :, 1].min(1) < y1) & \
             (T[:, :, 2].max(1) > z0) & (T[:, :, 2].min(1) < z1)
        hit = [i for i in np.nonzero(bm)[0] if tri_box(T[i], c, h)]
        if hit:
            fails.append({'z': round(float(z), 3), 'support_y': round(sup, 4), 'hits': len(hit)})
    return {'glb': os.path.basename(path), 'sha256': G.sha256(path), 'body_W': W, 'body_H': H, 'body_D': D,
            'stations': stations, 'failures': len(fails), 'first_failures': fails[:5],
            'support_range_y': [round(min(supports), 4), round(max(supports), 4)] if supports else None,
            'virtual_leaves': leaves}


if __name__ == '__main__':
    path = sys.argv[1]
    leaves = []
    args = sys.argv[2:]
    for i, a in enumerate(args):
        if a == '--leaf':
            leaves.append([float(x) for x in args[i + 1].split(',')])
    out = []
    for W, H in [(0.9, 1.8), (0.9, 2.05), (1.4, 1.8), (1.8, 1.8)]:
        out.append(run(path, W, H, leaves))
    print(json.dumps(out, ensure_ascii=False, indent=1))
