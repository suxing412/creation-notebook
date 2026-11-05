"""LY-074 prep: centreline overhead profile (first face above the floor) per side, to
locate the existing door passage that the stair leads to, its head height and jamb width.
Discrete vertical probes; not a continuous body sweep. usage: python -I door_probe.py <glb>..."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from measure_access import load, meshes, Field, support
SIDES = {'+X': (1, 0), '-X': (-1, 0), '+Z': (0, 1), '-Z': (0, -1)}
out = {}
for p in sys.argv[1:]:
    js, b, sha, n = load(p)
    T = np.concatenate(list(meshes(js, b).values()))
    F = Field(T)
    half = float(np.abs(T[:, :, [0, 2]]).max())
    res = {}
    for s, (dx, dz) in SIDES.items():
        prof = []
        for r in np.arange(0, half, 0.05):
            x, z = dx * r, dz * r
            fy = support(F, x, z, 1.5)
            y, ny = F.hits(x, z)
            m = y > (fy if fy is not None else 0) + 0.02
            if m.any():
                k = np.argmin(np.where(m, y, 1e9)); prof.append((round(float(r), 2), fy, round(float(y[k]), 3), 'down' if ny[k] < 0 else 'up'))
            else:
                prof.append((round(float(r), 2), fy, None, None))
        # compress
        runs = []
        for r, fy, h, d in prof:
            key = (fy, h, d)
            if runs and runs[-1]['k'] == key: runs[-1]['r1'] = r
            else: runs.append({'k': key, 'r0': r, 'r1': r})
        # door jamb width at the outermost run whose first-hit is 'up' (inside wall solid) -> use its mid r
        wall = [q for q in runs if q['k'][2] == 'up' and q['k'][1] is not None and q['k'][1] > 3]
        jamb = None
        if wall:
            q = wall[-1]; rm = (q['r0'] + q['r1']) / 2
            lat = []
            for t in np.arange(-4, 4.0001, 0.02):
                x, z = dx * rm - dz * t, dz * rm + dx * t
                fy = support(F, x, z, 1.5)
                y, ny = F.hits(x, z)
                m = y > (fy if fy is not None else 0) + 0.02
                lat.append((round(float(t), 2), (round(float(y[m].min()), 3) if m.any() else None), ('down' if m.any() and ny[m][np.argmin(y[m])] < 0 else 'up' if m.any() else None)))
            jr = []
            for t, h, d in lat:
                if jr and jr[-1]['k'] == (h, d): jr[-1]['t1'] = t
                else: jr.append({'k': (h, d), 't0': t, 't1': t})
            jamb = {'probe_r': rm, 'lateral_runs': jr}
        res[s] = {'overhead_runs': [{'floor_y': q['k'][0], 'first_above_y': q['k'][1], 'face': q['k'][2], 'r0': q['r0'], 'r1': q['r1']} for q in runs], 'wall_lateral': jamb}
    out[os.path.basename(p)] = {'sha256': sha, 'sides': res}
json.dump(out, sys.stdout, indent=1)
