"""LY-067 prep: probe whether the CURRENT city ground meshes (bce3211) have any
surface under given world XZ points.  Read-only.

Usage:
  python -I probe_ground.py <out.json> <points.json> <ground.glb> [<ground.glb> ...]

points.json: [{"id": str, "xz": [x, z]}, ...]  (world, glTF axes, metres)
The ground nodes in city-data.mjs are at position [0,0,0] with no rotation/
scale, so GLB-internal node matrices are the only transform applied.
Vertical ray from y=+1000 downward; reports every hit Y (top-most first).
This is NOT a placement of the gallery: the gallery has no city transform.
"""
import json
import sys

import numpy as np

sys.path.insert(0, __file__.rsplit('/', 1)[0] if '/' in __file__ else '.')
import measure_footings as mf  # noqa: E402


def tris_of(path):
    js, binc, sha, size = mf.load(path)
    out = []
    for ni, M in mf.node_matrices(js).items():
        for p in js['meshes'][js['nodes'][ni]['mesh']]['primitives']:
            P = mf.acc(js, binc, p['attributes']['POSITION']).astype(float)
            P = (np.c_[P, np.ones(len(P))] @ M.T)[:, :3]
            I = mf.acc(js, binc, p['indices']).reshape(-1, 3).astype(np.int64)
            out.append(P[I])
    return np.concatenate(out), sha, size


def hits(T, x, z):
    a, b, c = T[:, 0], T[:, 1], T[:, 2]
    # 2D barycentric in XZ
    v0 = c[:, [0, 2]] - a[:, [0, 2]]
    v1 = b[:, [0, 2]] - a[:, [0, 2]]
    v2 = np.array([x, z]) - a[:, [0, 2]]
    d00 = (v0 * v0).sum(1); d01 = (v0 * v1).sum(1); d11 = (v1 * v1).sum(1)
    d20 = (v2 * v0).sum(1); d21 = (v2 * v1).sum(1)
    den = d00 * d11 - d01 * d01
    ok = np.abs(den) > 1e-12
    u = np.where(ok, (d11 * d20 - d01 * d21) / np.where(ok, den, 1), -1)
    v = np.where(ok, (d00 * d21 - d01 * d20) / np.where(ok, den, 1), -1)
    m = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9)
    y = a[m, 1] + u[m] * (c[m, 1] - a[m, 1]) + v[m] * (b[m, 1] - a[m, 1])
    return sorted(set(np.round(y, 4).tolist()), reverse=True)


if __name__ == '__main__':
    out, pts = sys.argv[1], json.load(open(sys.argv[2], encoding='utf-8'))
    grounds = []
    for g in sys.argv[3:]:
        T, sha, size = tris_of(g)
        grounds.append((g.replace('\\', '/'), T, sha, size))
    res = {'grounds': [{'path': g, 'sha256': s, 'bytes': n, 'triangles': len(T),
                        'xz_min': T.reshape(-1, 3).min(0)[[0, 2]].round(3).tolist(),
                        'xz_max': T.reshape(-1, 3).max(0)[[0, 2]].round(3).tolist()}
                       for g, T, s, n in grounds],
           'points': []}
    for p in pts:
        row = {'id': p['id'], 'xz': p['xz'], 'hits': {}}
        for g, T, s, n in grounds:
            row['hits'][g.rsplit('/', 1)[-1]] = hits(T, *p['xz'])
        row['any_hit'] = any(row['hits'].values())
        res['points'].append(row)
        print(row['id'], row['xz'], row['hits'])
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
