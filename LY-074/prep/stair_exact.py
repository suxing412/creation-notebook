"""LY-074 prep: exact stair tread rectangles (vertex-level) for each side of each GLB.
usage: python -I stair_exact.py <glb>...   (imports measure_access.py from this dir)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from measure_access import load, meshes
out = {}
for p in sys.argv[1:]:
    js, b, sha, n = load(p)
    M = meshes(js, b)
    T = np.concatenate(list(M.values()))
    nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); ny = nrm[:, 1] / np.linalg.norm(nrm, axis=1)
    up = T[ny > 0.5]
    which = {k: [] for k in M}
    half = float(np.abs(T[:, :, [0, 2]]).max())
    res = {}
    for side, (ax, sg) in {'+X': (0, 1), '-X': (0, -1), '+Z': (2, 1), '-Z': (2, -1)}.items():
        lat = 2 - ax
        r = up[:, :, ax] * sg
        sel = up[(r.min(1) > half - 4.0) & (np.abs(up[:, :, lat]).max(1) < 4.0) & (up[:, :, 1].max(1) < 2.0)]
        rows = {}
        for tri in sel:
            y = round(float(tri[:, 1].mean()), 4)
            rr = tri[:, ax] * sg; ll = tri[:, lat]
            a = rows.setdefault(y, [9e9, -9e9, 9e9, -9e9])
            a[0] = min(a[0], rr.min()); a[1] = max(a[1], rr.max()); a[2] = min(a[2], ll.min()); a[3] = max(a[3], ll.max())
        res[side] = {str(y): [round(float(v), 4) for v in a] for y, a in sorted(rows.items())}
    # which mesh owns the stair treads
    own = {}
    for k, v in M.items():
        nn = np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0]); nyy = nn[:, 1] / np.linalg.norm(nn, axis=1)
        u = v[nyy > 0.5]
        own[k] = int(((u[:, :, 0].min(1) > half - 3.0) & (u[:, :, 1].max(1) < 2.0)).sum())
    out[os.path.basename(p)] = {'sha256': sha, 'treads_r0_r1_lat0_lat1': res, 'upfaces_in_+X_stair_band_by_mesh': own}
json.dump(out, sys.stdout, indent=1)
