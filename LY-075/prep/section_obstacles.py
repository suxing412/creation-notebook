# LY-075 prep: horizontal-section obstacle raster, to catch members that vertical rays miss
# (e.g. open-ended post cylinders with no caps). Intersects every triangle of the GLB with planes
# y = floor + h for h in HEIGHTS, rasterises the cut segments onto the same grid as <floor.npz>.
# Usage: python section_obstacles.py <glb> <floor.npz> <out.npz> <floor_y>
# Output: OBST[k] bool grid per height, plus per-height segment counts. Read-only on inputs.
import sys, numpy as np
from glbinfo import load, acc

HEIGHTS = (0.10, 0.50, 0.90, 1.30, 1.70, 2.00, 2.30)

def tris(path):
    js, b = load(path)
    out = []
    for n in js['nodes']:
        if 'mesh' not in n: continue
        for pr in js['meshes'][n['mesh']]['primitives']:
            P = acc(js, b, pr['attributes']['POSITION']).astype(np.float64)
            I = acc(js, b, pr['indices']).reshape(-1, 3).astype(np.int64)
            out.append(P[I])
    return np.concatenate(out)  # (n,3,3); no node transforms in these GLBs (checked: all identity)

def cut(T, y):
    d = T[:, :, 1] - y
    segs = []
    for a, b in ((0, 1), (1, 2), (2, 0)):
        pass
    s = np.sign(d); s[s == 0] = 1e-9
    m = ~((s > 0).all(1) | (s < 0).all(1))
    T = T[m]; d = d[m]
    pts = []
    for a, b in ((0, 1), (1, 2), (2, 0)):
        da, db = d[:, a], d[:, b]
        cross = (da * db) < 0
        t = np.where(cross, da / np.where(cross, da - db, 1), 0)
        p = T[:, a] + (T[:, b] - T[:, a]) * t[:, None]
        pts.append(np.where(cross[:, None], p, np.nan))
    pts = np.stack(pts, 1)  # (n,3,3) up to 2 valid
    segs = []
    for row in pts:
        v = row[~np.isnan(row[:, 0])]
        if len(v) >= 2: segs.append((v[0][[0, 2]], v[1][[0, 2]]))
    return segs

def raster(segs, xs, zs, step):
    G = np.zeros((len(xs), len(zs)), bool)
    x0 = xs[0]; z0 = zs[0]; dz = zs[1] - zs[0]
    for p, q in segs:
        L = np.linalg.norm(q - p); n = max(2, int(L / (step * 0.3)) + 2)
        t = np.linspace(0, 1, n)[:, None]; pts = p + (q - p) * t
        i = np.round((pts[:, 0] - x0) / step).astype(int); j = np.round((pts[:, 1] - z0) / dz).astype(int)
        ok = (i >= 0) & (i < len(xs)) & (j >= 0) & (j < len(zs))
        G[i[ok], j[ok]] = True
    return G

if __name__ == '__main__':
    glb, fnpz, out, fy = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
    f = np.load(fnpz); xs, zs, step = f['xs'], f['zs'], float(f['step'])
    T = tris(glb)
    OB = []; counts = []
    for h in HEIGHTS:
        segs = cut(T, fy + h); counts.append(len(segs))
        OB.append(raster(segs, xs, zs, step))
    np.savez_compressed(out, OBST=np.array(OB), heights=np.array(HEIGHTS), floor_y=fy, counts=np.array(counts))
    print(glb.split('/')[-1], 'segments per height', dict(zip(HEIGHTS, counts)))
