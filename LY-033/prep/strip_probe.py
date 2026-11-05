# LY-033 prep: finite strip probes on the as-installed city GLB (read-only baseline for later A/B door packs).
# python -I strip_probe.py <granary-city-LOD0.glb> <out.json> [extra-door-glb ...]
# For each warehouse and strip width W (0.9 / 1.5 / 1.8 m) the path runs from outside ground
# (stair foot + 0.6 m) to 1.0 m inside the front wall along the stair centreline (local x = 0, -Z).
#  * support: downward ray from (floor + 1.9 m) at every (x, z) sample, dx = 0.05, dz = 0.04;
#    a sample FAILS when its support differs from the centreline support at the same z by > 0.02 m
#    (lateral step / drop inside the body footprint) or has no support.
#  * clearance: horizontal rays along -Z at heights floor + {0.1, 0.5, 1.0, 1.5, 1.7} m for every x
#    of the strip; a column FAILS when anything is hit before 1.0 m inside the front plane (jamb / closed or parked leaf).
#  --fixture closed|intrude adds an in-memory test box (never exported) to prove the probe can fail.
# This is a finite sampled probe, NOT continuous body motion, loads, vehicles or structural proof.
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbread as R

CITY = np.array([2285.714111328125, 0.0, -3673.468994140625])
WH = {'A': dict(c=CITY + [-12, 0, -6], front=3.0, floor=0.85, stairEnd=4.48),
      'B': dict(c=CITY + [12, 0, -6], front=2.5, floor=1.10, stairEnd=4.62)}
TOL_STEP = 0.02


def ray_first(o, d, T):
    e1 = T[:, 1] - T[:, 0]; e2 = T[:, 2] - T[:, 0]
    h = np.cross(d, e2); a = (e1 * h).sum(1)
    ok = np.abs(a) > 1e-12
    f = np.where(ok, 1.0 / np.where(ok, a, 1), 0)
    s = o - T[:, 0]
    u = f * (s * h).sum(1)
    q = np.cross(s, e1)
    v = f * (q @ d)
    t = f * (e2 * q).sum(1)
    m = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9) & (t > 1e-6)
    return float(t[m].min()) if m.any() else None


def box_tris(lo, hi):
    """12 triangles of an axis-aligned box (in-memory test fixture only, never exported)."""
    x0, y0, z0 = lo; x1, y1, z1 = hi
    v = np.array([[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0], [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]])
    f = [(0, 1, 2), (0, 2, 3), (4, 6, 5), (4, 7, 6), (0, 4, 5), (0, 5, 1), (3, 2, 6), (3, 6, 7), (0, 3, 7), (0, 7, 4), (1, 5, 6), (1, 6, 2)]
    return v[np.array(f)]


# In-memory synthetic fixtures (warehouse-local) used ONLY to prove the probe can fail:
#   closed: a 0.06 m slab filling the 1.5 x 2.1 opening in the front-wall plane
#   intrude: an open leaf parked across the 0.9 m path (x -0.45..0.30, 0.06 thick, just inside)
def fixtures(kind, wh):
    s = WH[wh]
    if kind == 'closed':
        return box_tris((-0.75, s['floor'], s['front'] - 0.13), (0.75, s['floor'] + 2.1, s['front'] - 0.07))
    if kind == 'intrude':
        return box_tris((-0.45, s['floor'], s['front'] - 0.40), (0.30, s['floor'] + 2.0, s['front'] - 0.34))
    raise SystemExit('unknown fixture')


def run(paths, fixture=None):
    tris = []
    shas = {}
    for p in paths:
        js, ps = R.prims(p)
        shas[os.path.basename(p)] = R.sha256(p)
        tris += [q['pos'][q['tris']] for q in ps]
    T = np.concatenate(tris)
    if fixture:
        T = np.concatenate([T] + [fixtures(fixture, wh) + WH[wh]['c'] for wh in WH])
    out = dict(fixture=fixture, files=shas, tolStep=TOL_STEP, method='see header', results={})
    for wh, s in WH.items():
        L = T - s['c']
        sel = (L[:, :, 0].min(1) < 3) & (L[:, :, 0].max(1) > -3) & (L[:, :, 2].max(1) > s['front'] - 2) & (L[:, :, 2].min(1) < s['stairEnd'] + 1)
        L = L[sel]
        zs = np.round(np.arange(s['stairEnd'] + 0.6, s['front'] - 1.0, -0.04), 3)
        for W in (0.9, 1.5, 1.8):
            xs = np.round(np.arange(-W / 2, W / 2 + 1e-9, 0.05), 3)
            fails, samples = [], 0
            for z in zs:
                y0 = s['floor'] + 1.9
                hc = ray_first(np.array([0.0, y0, z]), np.array([0, -1.0, 0]), L)
                hc = None if hc is None else y0 - hc
                for x in xs:
                    samples += 1
                    h = ray_first(np.array([x, y0, z]), np.array([0, -1.0, 0]), L)
                    h = None if h is None else y0 - h
                    if h is None or hc is None or abs(h - hc) > TOL_STEP:
                        fails.append([float(x), float(z), None if h is None else round(h, 4), None if hc is None else round(hc, 4)])
            jamb = []
            for dy in (0.1, 0.5, 1.0, 1.5, 1.7):
                for x in xs:
                    t = ray_first(np.array([x, s['floor'] + dy, s['front'] + 1.0]), np.array([0, 0, -1.0]), L)
                    if t is not None and t < 1.0 + 1.0:  # any hit between outside and 1.0 m inside the front plane
                        jamb.append([float(x), dy, round(t - 1.0, 4)])
            out['results']['%s-%.1f' % (wh, W)] = dict(supportSamples=samples, supportFails=len(fails),
                                                     clearanceColumnsTested=len(xs) * 5, clearanceFails=len(jamb),
                                                     firstSupportFails=fails[:8], firstClearanceFails=jamb[:8])
            print(wh, W, 'support fails %d/%d' % (len(fails), samples), 'clearance fails %d/%d' % (len(jamb), len(xs) * 5))
    return out


if __name__ == '__main__':
    a = sys.argv[1:]
    fx = None
    if '--fixture' in a:
        i = a.index('--fixture'); fx = a[i + 1]; a = a[:i] + a[i + 2:]
    out = run([a[0]] + a[2:], fx)
    json.dump(out, open(a[1], 'w'), indent=1)
