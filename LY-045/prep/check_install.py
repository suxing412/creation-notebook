# LY-045 prep: installation checker for the 圈厕关系 A atomic package (entry, stair, privy hole, ground below).
# Read-only on inputs. Surface rasters / vertical rays only: NOT solid collision, gait, structure or sanitation.
#
# python -I check_install.py <lab_root> <case.json> [<out.json>]
#   case.json = {"yard": "C02-010", "matrix": [16 col-major], "variant": "no-hole" | "has-hole",
#                "grounds": ["ground-south", ...] (city ground ids to load; default all four),
#                "extraGroundGLB": [paths] (package ground patch, world coords), "loadExcludedPrototypeNodes": false,
#                "mockCutHoleFrom": null | "ground-south"  (TEST FIXTURE ONLY: in-memory removal of ground tris
#                 touching the hole rect; never a deliverable), "expectSha": {...}}
# python -I check_install.py <lab_root> --selftest <out.json>     runs the positive + negative cases below.
import sys, os, json
import numpy as np
from scipy import ndimage, signal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbio

H = 0.1; BAND = 0.03; ROUTE_HALF = 0.45; TOL = 0.005
SC_REL = 'docs/library/models/m-luoyang-service-court/files/service-A-LOD0.glb'
SC_SHA = 'cc02f68fa0f0412ea491e903dedefb028ba88a444a6ff6384250e483f82d23d7'
EXCL = ['site_lot', 'site_neutral_lane', 'designed_hardpacked_activity_ground']
GROUNDS = {'ground-south': ('assets/ground-atomic/south.glb', '4313826ddf5fbe0c0d8dcb4983d6cdbd647713d49faa1980cd34f587a3273a0e', None),
           'ground-retained': ('assets/ground-atomic/retained.glb', 'aed8b3d4cb12aeaddf5c696a8a86355b15b7cb4fc8ebd76cc364d23789d630cc', None),
           'ground-network': ('assets/ground-atomic/network-ground-stitched.glb', 'fdfc3ce5c63305f79aa746b31c3be60f3d11a6acb75f190886124f2d3446db60', None),
           'ground-D08': ('assets/ground-atomic/D08.glb', '3ab933108b88c5c359fc7512d324e14f15157eaa54fb17f80f2adeb6c4626d9a', [580, 0, -960])}
YARDS = {'C02-010': [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 531, 0, -818.45, 1],
         'C02-021': [0, 0, 1.0, 0, 0, 1, 0, 0, -1.0, 0, 0, 0, 717.45, 0, -893.64308, 1]}
A2 = ('docs/cities/luoyang/assets/c02v/A2-LOD0-prototype.glb', '19b052022b2f6955e4a72f1a48280f7f8c229e11f001aa02ac95e357b890d9c7')
LOCAL_ROUTES = {"gate_to_main": [[-3.5, -15], [-3.5, -7], [0, -4], [0.6, 2.8], [0.6, 5.25]], "yard_to_side": [[0.6, 0.6], [-4.4, 0.6]]}
PEN_C, PEN_ROUT = (0.0, -0.0013), 2.8012
HOLE = {'x': [-0.21, 0.21], 'z': [-2.47, -2.05]}
FLOOR_Y = 1.4
STAIR_FOOT = {'x': [3.45, 3.75], 'z': [-4.0, -3.0], 'y': 0.175}
APRONS = {'stairFoot': {'x': [3.75, 4.95], 'z': [-4.0, -3.0]}, 'penGap': {'x': [-0.6, 0.6], 'z': [2.85, 3.85]}}


def tri_n(t):
    n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]); a = np.linalg.norm(n, axis=1)
    return n / (a[:, None] + 1e-15)


def xform(t, M):
    v = t.reshape(-1, 3); p = np.c_[v, np.ones(len(v))] @ M.T
    return p[:, :3].reshape(-1, 3, 3)


def ptx(M, x, y, z):
    return (M @ np.array([x, y, z, 1.0]))[:3]


def clip(t, x0, z0, x1, z1):
    lo = t.min(1); hi = t.max(1)
    return t[(hi[:, 0] >= x0) & (lo[:, 0] <= x1) & (hi[:, 2] >= z0) & (lo[:, 2] <= z1)]


def vhits(tris, x, z):
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    d = (b[:, 0] - a[:, 0]) * (c[:, 2] - a[:, 2]) - (c[:, 0] - a[:, 0]) * (b[:, 2] - a[:, 2])
    ok = np.abs(d) > 1e-12; dd = np.where(ok, d, 1)
    l1 = ((b[:, 0] - x) * (c[:, 2] - z) - (c[:, 0] - x) * (b[:, 2] - z)) / dd
    l2 = ((c[:, 0] - x) * (a[:, 2] - z) - (a[:, 0] - x) * (c[:, 2] - z)) / dd
    l3 = 1 - l1 - l2
    m = ok & (l1 >= -1e-9) & (l2 >= -1e-9) & (l3 >= -1e-9)
    return np.sort(l1[m] * a[m, 1] + l2[m] * b[m, 1] + l3[m] * c[m, 1])


def seg_mask(X, Z, pts, half):
    m = np.zeros_like(X, bool)
    for (ax, az), (bx, bz) in zip(pts[:-1], pts[1:]):
        dx, dz = bx - ax, bz - az; L2 = dx * dx + dz * dz
        u = np.clip(((X - ax) * dx + (Z - az) * dz) / L2, 0, 1)
        m |= np.hypot(X - (ax + u * dx), Z - (az + u * dz)) <= half
    return m


def run(lab, case):
    res = {'case': case.get('name'), 'checks': {}, 'scope': 'surface raster + vertical rays; not solid collision, gait, structure, sanitation'}
    C = res['checks']
    city = os.path.join(lab, 'docs/cities/luoyang')
    scp = os.path.join(lab, SC_REL)
    sha = glbio.sha256(scp)
    C['C0_shaBound'] = {'pass': sha == SC_SHA and glbio.sha256(os.path.join(lab, A2[0])) == A2[1], 'serviceCourt': sha}
    M = glbio.col_major(case['matrix'])
    Minv = np.linalg.inv(M)
    sc = xform(np.concatenate(list(glbio.nodes_tris(scp).values())), M)
    MY = glbio.col_major(YARDS[case['yard']])
    yn = glbio.nodes_tris(os.path.join(lab, A2[0]), MY)
    kept = np.concatenate([t for k, t in yn.items() if k not in EXCL])
    lot = np.array([[-9, 0, -12, 1], [9, 0, -12, 1], [9, 0, 12, 1], [-9, 0, 12, 1]], float) @ MY.T
    lx0, lx1, lz0, lz1 = lot[:, 0].min(), lot[:, 0].max(), lot[:, 2].min(), lot[:, 2].max()
    grounds = []
    for gid in case.get('grounds', list(GROUNDS)):
        rel, gsha, pos = GROUNDS[gid]
        p = os.path.join(city, rel); root = np.eye(4)
        if pos: root[:3, 3] = pos
        assert glbio.sha256(p) == gsha, 'ground SHA drift ' + gid
        t = clip(np.concatenate(list(glbio.nodes_tris(p, root).values())), lx0 - 1, lz0 - 1, lx1 + 1, lz1 + 1)
        grounds.append((gid, t))
    for p in case.get('extraGroundGLB', []):
        grounds.append(('extra:' + os.path.basename(p), np.concatenate(list(glbio.nodes_tris(p).values()))))
    if case.get('loadExcludedPrototypeNodes'):
        for k in EXCL:
            grounds.append(('prototype:' + k, yn[k]))
    # hole rect in world
    hc = np.array([ptx(M, x, 0, z) for x in HOLE['x'] for z in HOLE['z']])
    hx0, hx1, hz0, hz1 = hc[:, 0].min(), hc[:, 0].max(), hc[:, 2].min(), hc[:, 2].max()
    cut = None
    if case.get('mockCutHoleFrom'):
        if case.get('mockCutMode', 'exact') == 'triangles':
            grounds = [(g, clip_out(t, hx0, hz0, hx1, hz1) if g == case['mockCutHoleFrom'] else t) for g, t in grounds]
            res['MOCK'] = 'TEST FIXTURE: every ground triangle touching the hole rect deleted in memory (over-cut); not a deliverable'
        else:
            cut = (case['mockCutHoleFrom'], hx0, hz0, hx1, hz1)
            res['MOCK'] = 'TEST FIXTURE: ground treated as absent exactly inside the hole rect (in memory); not a deliverable'

    def gh(x, z, up_only=False):
        out = []
        for gid, t in grounds:
            if cut and gid == cut[0] and cut[1] < x < cut[3] and cut[2] < z < cut[4]:
                continue
            if up_only:
                t = t[tri_n(t)[:, 1] > 0.5] if len(t) else t
            if len(t):
                out.append(vhits(t, x, z))
        return np.concatenate(out) if out else np.array([])

    def gtop(x, z):
        y = gh(x, z, True)
        return float(y.max()) if len(y) else None

    # C1 bottom contact: every down-facing model face at local y=0 sits on ground top within TOL
    loc = np.concatenate(list(glbio.nodes_tris(scp).values()))
    ln = tri_n(loc)
    bot = loc[(ln[:, 1] < -0.99) & (loc[:, :, 1].max(1) < 1e-3)]
    gaps = []
    for t in bot:
        for u, w in ((1 / 3, 1 / 3), (0.1, 0.1), (0.8, 0.1), (0.1, 0.8)):
            p = t[0] + u * (t[1] - t[0]) + w * (t[2] - t[0]); q = ptx(M, *p)
            g = gtop(q[0], q[2]); gaps.append(None if g is None else q[1] - g)
    noG = sum(1 for g in gaps if g is None); fl = sum(1 for g in gaps if g is not None and g > TOL); bu = sum(1 for g in gaps if g is not None and g < -TOL)
    gv = [g for g in gaps if g is not None]
    C['C1_bottomContact'] = {'pass': noG == 0 and fl == 0 and bu == 0, 'samples': len(gaps), 'noGround': noG, 'floating_gt5mm': fl,
                             'buried_gt5mm': bu, 'gap_min_max': [round(min(gv), 4), round(max(gv), 4)] if gv else None}
    # C2 footprint vs yard / routes / aprons (0.1 m raster in world)
    nx, nz = int(round((lx1 - lx0) / H)), int(round((lz1 - lz0) / H))
    gx = lx0 + (np.arange(nx) + 0.5) * H; gzz = lz0 + (np.arange(nz) + 0.5) * H
    X, Z = np.meshgrid(gx, gzz)
    gt_r = np.full((nz, nx), -np.inf)
    for gid_, t in grounds:
        tp, _, _ = glbio.raster(t, lx0, lz0, H, nx, nz)
        if cut and gid_ == cut[0]:
            tp[(X > cut[1]) & (X < cut[3]) & (Z > cut[2]) & (Z < cut[4])] = -np.inf
        gt_r = np.maximum(gt_r, tp)
    kt, _, _ = glbio.raster(kept, lx0, lz0, H, nx, nz, edge_step=0.02)
    blocked = np.isfinite(kt) & (kt > np.where(np.isfinite(gt_r), gt_r, 0.2) + BAND)
    st, _, _ = glbio.raster(sc, lx0, lz0, H, nx, nz, edge_step=0.02)
    occ = np.isfinite(st)
    L = np.stack([X.ravel(), np.zeros(X.size), Z.ravel(), np.ones(X.size)]) ; Lc = (Minv @ L)
    Xl = Lc[0].reshape(X.shape); Zl = Lc[2].reshape(X.shape)
    occ |= np.hypot(Xl - PEN_C[0], Zl - PEN_C[1]) <= PEN_ROUT
    inlot = bool(((sc.reshape(-1, 3)[:, 0] >= lx0) & (sc.reshape(-1, 3)[:, 0] <= lx1) & (sc.reshape(-1, 3)[:, 2] >= lz0) & (sc.reshape(-1, 3)[:, 2] <= lz1)).all())
    route = np.zeros_like(occ)
    for pts in LOCAL_ROUTES.values():
        P = np.array([[x, 0, -yn_, 1] for x, yn_ in pts], float) @ MY.T
        route |= seg_mask(X, Z, P[:, [0, 2]].tolist(), ROUTE_HALF)
    apr = {}
    for an, a in APRONS.items():
        am = (Xl >= a['x'][0]) & (Xl <= a['x'][1]) & (Zl >= a['z'][0]) & (Zl <= a['z'][1]) & ~occ
        apr[an] = int((am & (blocked | ~np.isfinite(gt_r))).sum())
    C['C2_footprint'] = {'pass': inlot and int((occ & blocked).sum()) == 0 and int((occ & route).sum()) == 0 and all(v == 0 for v in apr.values()),
                         'insideLot': inlot, 'overlapYardCells': int((occ & blocked).sum()), 'overlapRouteCells': int((occ & route).sum()),
                         'apronBlockedCells': apr}
    # C3 stair entry: first riser from real ground
    fx = np.mean(STAIR_FOOT['x']); fz = np.mean(STAIR_FOOT['z'])
    q = ptx(M, fx + 0.6, 0, fz); g0 = gtop(q[0], q[2])
    qt = ptx(M, fx, STAIR_FOOT['y'], fz)
    riser = None if g0 is None else qt[1] - g0
    C['C3_stairEntry'] = {'pass': bool(riser is not None and abs(riser - 0.175) <= TOL), 'firstRiser_m': None if riser is None else round(riser, 4),
                          'apronGroundY': None if g0 is None else round(g0, 4)}
    # C4 hole: rays from just under the floor top down through 25 points of the hole rect
    probes = []
    for fu in np.linspace(0.1, 0.9, 5):
        for fw in np.linspace(0.1, 0.9, 5):
            lx = HOLE['x'][0] + fu * (HOLE['x'][1] - HOLE['x'][0]); lz = HOLE['z'][0] + fw * (HOLE['z'][1] - HOLE['z'][0])
            q = ptx(M, lx, FLOOR_Y - 0.001, lz)
            ys = np.concatenate([gh(q[0], q[2]), vhits(sc, q[0], q[2])])
            below = ys[ys < q[1]]
            first = float(below.max()) if len(below) else None
            probes.append({'drop_m': None if first is None else round(q[1] + 0.001 - first, 4), 'firstHitY': None if first is None else round(first, 4)})
    datum = gtop(*ptx(M, 0, 0, PEN_C[1])[[0, 2]])
    drops = [p['drop_m'] for p in probes]
    residue = {}
    for gid, t in grounds:
        tt = clip(t, hx0 + 1e-3, hz0 + 1e-3, hx1 - 1e-3, hz1 - 1e-3)
        if cut and gid == cut[0]:
            tt = tt[:0]
        if len(tt):
            hit = [vhits(tt, x, z) for x, z in ((hx0 + 0.05, hz0 + 0.05), ((hx0 + hx1) / 2, (hz0 + hz1) / 2), (hx1 - 0.05, hz1 - 0.05))]
            ymax = max((float(h.max()) for h in hit if len(h)), default=None)
            if ymax is not None and datum is not None and ymax >= datum - 0.05:
                residue[gid] = round(ymax, 4)
    if case['variant'] == 'no-hole':
        ok = all(d is not None and abs(d - FLOOR_Y) <= TOL for d in drops)
        C['C4_holeBelow'] = {'pass': ok, 'variant': 'no-hole', 'expectedDrop_m': FLOOR_Y, 'drops_min_max': [min(d for d in drops if d is not None), max(d for d in drops if d is not None)] if any(d is not None for d in drops) else None,
                             'raysWithoutHit': sum(1 for d in drops if d is None),
                             'note': 'pen floor = city ground; no pit, no depth claim'}
    else:
        sealed = sum(1 for d in drops if d is not None and d <= FLOOR_Y + 0.05)
        C['C4_holeBelow'] = {'pass': sealed == 0 and not residue, 'variant': 'has-hole', 'raysStoppedAtOrAboveDatum': sealed,
                             'oldGroundResidueInHoleRect': residue,
                             'pitDepth': 'UNDETERMINED' if all(d is None for d in drops) else 'bounded by package geometry (must be declared C, not engineering)',
                             'drops': sorted(set(drops), key=lambda d: (d is None, d))[:6]}
        res['status_hasHole'] = 'OPEN_UNDETERMINED_DEPTH (not a completed engineering pit)' if C['C4_holeBelow']['pass'] else 'FAIL'
    # C5 exclusions still active (prototype old ground must not be loaded at all in the city path)
    C['C5_prototypeOldGroundExcluded'] = {'pass': not case.get('loadExcludedPrototypeNodes'), 'excludeNodes': EXCL}
    res['pass'] = all(v['pass'] for v in C.values())
    return res


def clip_out(t, x0, z0, x1, z1):
    lo = t.min(1); hi = t.max(1)
    return t[~((hi[:, 0] >= x0) & (lo[:, 0] <= x1) & (hi[:, 2] >= z0) & (lo[:, 2] <= z1))]


REP = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 533.8, 0.2, -812.15, 1]   # candidate pose from measure-yard-fit.json (C02-010, rot 0)


def with_t(m, x=None, y=None, z=None):
    m = list(m)
    if x is not None: m[12] = x
    if y is not None: m[13] = y
    if z is not None: m[14] = z
    return m


SELFTEST = [
    {'name': 'P1 no-hole at candidate pose, ground-south', 'yard': 'C02-010', 'matrix': REP, 'variant': 'no-hole', 'grounds': ['ground-south'], 'expect': True},
    {'name': 'N1 datum 0.215 (prototype activity ground) -> floats 15 mm', 'yard': 'C02-010', 'matrix': with_t(REP, y=0.215), 'variant': 'no-hole', 'grounds': ['ground-south'], 'expect': False},
    {'name': 'N2 no ground loaded (default view, ground-south initial:false)', 'yard': 'C02-010', 'matrix': REP, 'variant': 'no-hole', 'grounds': [], 'expect': False},
    {'name': 'N3 has-hole claimed but ground-south still seals the hole', 'yard': 'C02-010', 'matrix': REP, 'variant': 'has-hole', 'grounds': ['ground-south'], 'expect': False},
    {'name': 'N4 has-hole, ground cut (MOCK) but prototype old ground loaded (exclusion dropped)', 'yard': 'C02-010', 'matrix': REP, 'variant': 'has-hole', 'grounds': ['ground-south'], 'mockCutHoleFrom': 'ground-south', 'loadExcludedPrototypeNodes': True, 'expect': False},
    {'name': 'P2 has-hole, ground cut (MOCK fixture) -> open, depth UNDETERMINED', 'yard': 'C02-010', 'matrix': REP, 'variant': 'has-hole', 'grounds': ['ground-south'], 'mockCutHoleFrom': 'ground-south', 'expect': True},
    {'name': 'N8 has-hole cut by deleting whole 2 m ground triangles (over-cut leaves pen wall unsupported)', 'yard': 'C02-010', 'matrix': REP, 'variant': 'has-hole', 'grounds': ['ground-south'], 'mockCutHoleFrom': 'ground-south', 'mockCutMode': 'triangles', 'expect': False},
    {'name': 'N5 pose on the gate route', 'yard': 'C02-010', 'matrix': with_t(REP, x=528.5, z=-811.0), 'variant': 'no-hole', 'grounds': ['ground-south'], 'expect': False},
    {'name': 'N6 pose inside the main hall', 'yard': 'C02-010', 'matrix': with_t(REP, x=531.0, z=-825.0), 'variant': 'no-hole', 'grounds': ['ground-south'], 'expect': False},
    {'name': 'N7 wrong ground file for this yard (ground-retained only)', 'yard': 'C02-010', 'matrix': REP, 'variant': 'no-hole', 'grounds': ['ground-retained'], 'expect': False},
]

if __name__ == '__main__':
    lab = sys.argv[1]
    if sys.argv[2] == '--selftest':
        out = []
        for c in SELFTEST:
            r = run(lab, c); r['expected'] = c['expect']; r['asExpected'] = (r['pass'] == c['expect'])
            out.append(r)
            print(('OK  ' if r['asExpected'] else 'BAD ') + c['name'], '-> pass' if r['pass'] else '-> fail',
                  {k: v['pass'] for k, v in r['checks'].items()}, r.get('status_hasHole', ''))
        json.dump({'allAsExpected': all(r['asExpected'] for r in out), 'cases': out}, open(sys.argv[3], 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=float)
    else:
        case = json.load(open(sys.argv[2], encoding='utf-8'))
        r = run(lab, case)
        txt = json.dumps(r, ensure_ascii=False, indent=1, default=float)
        if len(sys.argv) > 3: open(sys.argv[3], 'w', encoding='utf-8').write(txt)
        print(txt)
