"""LY-074 prep: re-runnable acceptance checker for the future "four-side arrival ground"
(apron) against a chosen mingtang variant.  Written BEFORE G freezes; it contains no
delivery geometry.  `--selftest` builds throw-away in-memory rectangles (good + broken
cases) only to prove each check can fail.  They are test fixtures, not a design.

usage:
  python -I check_apron.py --selftest
  python -I check_apron.py --mingtang <mingtang-X-LODn.glb> --apron <apron.glb> --variant A|B \
         [--depth 3.0] [--ports ports.json] [--expect-mingtang-sha <sha>]

ports.json (to come from LY-006): {"+X": {"r": 19.64, "y": 0.0, "half_width": 2.7}, ...}
in the mingtang local frame (origin = platform centre, y=0 = base bottom), metres.

What it proves: vertical point-probe support and edge/overlap geometry only.  It does NOT
prove continuous body motion, structural safety, city placement or historical validity.
"""
import sys, os, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from measure_access import load, meshes, Field, support

# measured on bce3211 GLBs (stair-exact.json); identical on LOD0/1/2 and on all four sides
VARIANTS = {
    'A': {'base_half': 14.0, 'foot_r': 16.64, 'platform_y': 1.2, 'risers': 8, 'stair_half_w': 2.1},
    'B': {'base_half': 12.5, 'foot_r': 14.48, 'platform_y': 0.9, 'risers': 6, 'stair_half_w': 2.1},
}
SIDES = {'+X': (1, 0), '-X': (-1, 0), '+Z': (0, 1), '-Z': (0, -1)}
TOL_Y = 0.005      # m, height match at the stair foot / port
TOL_GAP = 0.005    # m, horizontal gap allowed between bottom riser and apron edge
TOL_OVER = 0.005   # m, horizontal overlap allowed under the riser line
MAX_DOUBLE_AREA = 0.01  # m2 of apron top face allowed inside the building footprint


def xz(dx, dz, r, t):
    return dx * r - dz * t, dz * r + dx * t


def in_footprint(x, z, v):
    """inside platform square or inside one of the four stair blocks"""
    h = v['base_half']; w = v['stair_half_w']; f = v['foot_r']
    if abs(x) < h - TOL_OVER and abs(z) < h - TOL_OVER:
        return True
    for a, b in ((x, z), (z, x)):
        if h - TOL_OVER <= abs(a) < f - TOL_OVER and abs(b) < w - TOL_OVER:
            return True
    return False


def up_tris(T):
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    ny = n[:, 1] / np.maximum(np.linalg.norm(n, axis=1), 1e-12)
    return T[ny > 0.5]


def check(apronT, v, depth=3.0, ports=None, mingT=None):
    """returns dict side -> list of (check_id, pass, detail)"""
    F = Field(apronT)
    out = {}
    w = v['stair_half_w']; f = v['foot_r']
    for s, (dx, dz) in SIDES.items():
        res = []
        # C1 support over the arrival band in front of the stair (stair width + 0.3 m each side)
        pts = sup = 0; badh = []
        for o in np.arange(0.01, depth + 1e-9, 0.05):
            for t in np.arange(-(w + 0.3), w + 0.3 + 1e-9, 0.1):
                x, z = xz(dx, dz, f + o, t)
                y = support(F, x, z, 0.5)
                pts += 1
                if y is not None and abs(y) <= TOL_Y:
                    sup += 1
                elif y is not None:
                    badh.append(round(y, 4))
        res.append(('C1_band_support', bool(sup == pts), f'{sup}/{pts} probes supported at |y|<={TOL_Y}; off-height {badh[:5]}'))
        # C2 foot joint: apron must reach the riser line across the full stair width
        worst = 0.0
        for t in np.arange(-w + 0.02, w - 0.02 + 1e-9, 0.05):
            found = None
            for o in np.arange(0.0, 0.2, 0.001):
                x, z = xz(dx, dz, f + o, t)
                y = support(F, x, z, 0.5)
                if y is not None and abs(y) <= TOL_Y:
                    found = o; break
            worst = max(worst, found if found is not None else 9.0)
        res.append(('C2_foot_gap', bool(worst <= TOL_GAP), f'max gap riser->apron {worst:.3f} m (tol {TOL_GAP})'))
        out[s] = res
    # C3/C4 whole-apron checks: vertical probes on a 0.1 m grid over the building footprint
    # (platform square + four stair blocks, shrunk by TOL_OVER).  Any apron face found there is
    # double coverage under the building; any such face above TOL_Y is intrusion into it.
    g = 0.1; hits = 0; maxy = None
    lim = v['foot_r']
    for x in np.arange(-lim + g / 2, lim, g):
        for z in np.arange(-lim + g / 2, lim, g):
            if not in_footprint(x, z, v):
                continue
            y, ny = F.hits(x, z)
            if len(y):
                hits += 1
                maxy = max(maxy if maxy is not None else -9e9, float(y.max()))
    dbl = hits * g * g
    glob = [('C3_double_cover_under_building', bool(dbl <= MAX_DOUBLE_AREA), f'apron faces inside footprint ~{dbl:.3f} m2 ({hits} probes @0.1 m; tol {MAX_DOUBLE_AREA})'),
            ('C4_no_intrusion_into_platform_or_stairs', bool(maxy is None or maxy <= TOL_Y), f'max apron y inside footprint {maxy}')]
    # C5 ports (only once LY-006 has frozen them)
    if ports:
        for s, p in ports.items():
            dx, dz = SIDES[s]
            ok = True; det = []
            for t in np.linspace(-p['half_width'] + 0.02, p['half_width'] - 0.02, 9):
                x, z = xz(dx, dz, p['r'] - 0.02, t)
                y = support(F, x, z, p['y'] + 0.5)
                if y is None or abs(y - p['y']) > TOL_Y:
                    ok = False; det.append((round(float(t), 2), y))
            glob.append((f'C5_port_{s}', bool(ok), f'port r={p["r"]} y={p["y"]} misses {det[:4]}'))
    else:
        glob.append(('C5_ports', None, 'NOT RUN: LY-006 ports not frozen'))
    out['all'] = glob
    return out


def rect(r0, r1, t0, t1, dx, dz, y=0.0):
    a = xz(dx, dz, r0, t0); b = xz(dx, dz, r1, t0); c = xz(dx, dz, r1, t1); d = xz(dx, dz, r0, t1)
    P = [np.array([p[0], y, p[1]]) for p in (a, b, c, d)]
    T = np.array([[P[0], P[2], P[1]], [P[0], P[3], P[2]]])
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    if n[0, 1] < 0:
        T = T[:, [0, 2, 1]]
    return T


def fixture(v, depth=3.0, shift=0.0, dy=0.0, skip=None, under=0.0, width_pad=0.6):
    tris = []
    for s, (dx, dz) in SIDES.items():
        if s == skip:
            continue
        tris.append(rect(v['foot_r'] + shift - under, v['foot_r'] + depth + 0.5, -(v['stair_half_w'] + width_pad), v['stair_half_w'] + width_pad, dx, dz, dy))
    return np.concatenate(tris)


def verdict(res):
    flat = [c for side in res.values() for c in side]
    return all(c[1] is not False for c in flat)


def selftest():
    A, B = VARIANTS['A'], VARIANTS['B']
    cases = [
        ('good_A', fixture(A), A, True),
        ('good_B', fixture(B), B, True),
        ('neg_gap_6mm', fixture(A, shift=0.006), A, False),
        ('neg_raised_8mm', fixture(A, dy=0.008), A, False),
        ('neg_missing_-Z', fixture(A, skip='-Z'), A, False),
        ('neg_runs_under_stair_0.5m', fixture(A, under=0.5), A, False),
        ('neg_A_apron_on_B', fixture(A), B, False),      # A/B sizes must not mix
        ('neg_B_apron_on_A', fixture(B), A, False),
        ('neg_too_narrow', fixture(A, width_pad=0.1), A, False),
    ]
    ok_all = True
    for name, T, v, expect in cases:
        r = check(T, v)
        got = verdict(r)
        fails = [(s, c[0]) for s, cs in r.items() for c in cs if c[1] is False]
        status = 'OK ' if got == expect else 'BAD'
        ok_all &= (got == expect)
        print(f'{status} {name:28s} expect={expect} got={got} fails={fails[:6]}')
    print('SELFTEST', 'PASS' if ok_all else 'FAIL')
    return 0 if ok_all else 1


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--mingtang'); ap.add_argument('--apron'); ap.add_argument('--variant', choices=['A', 'B'])
    ap.add_argument('--depth', type=float, default=3.0); ap.add_argument('--ports')
    ap.add_argument('--expect-mingtang-sha')
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    js, b, msha, _ = load(a.mingtang)
    if a.expect_mingtang_sha and msha != a.expect_mingtang_sha:
        print('FAIL C6 mingtang SHA changed', msha); sys.exit(2)
    v = VARIANTS[a.variant]
    if abs(float(np.abs(np.concatenate(list(meshes(js, b).values()))[:, :, [0, 2]]).max()) - v['foot_r']) > 1e-3:
        print('FAIL C7 mingtang file does not match variant', a.variant); sys.exit(2)
    ajs, ab, asha, _ = load(a.apron)
    T = np.concatenate(list(meshes(ajs, ab).values()))
    ports = json.load(open(a.ports, encoding='utf-8')) if a.ports else None
    r = check(T, v, a.depth, ports)
    print(json.dumps({'mingtang_sha256': msha, 'apron_sha256': asha, 'variant': a.variant,
                      'result': {k: [list(c) for c in cs] for k, cs in r.items()}, 'pass': verdict(r)}, ensure_ascii=False, indent=1))
    sys.exit(0 if verdict(r) else 1)
