"""LY-020 acceptance checker for the Shangdong-gap corner stub (prepared before G; reuse at production time).

  python -I check_corner.py selftest <lab_root> <out.json>
      builds IN-MEMORY test fixtures only (never exported) and proves every check can pass and fail.
  python -I check_corner.py check <lab_root> <candidate.glb> <section A|B> <out.json> [--min-clear W]
      runs the same checks on a real exported candidate.

Checks (ids used by test-plan.md):
  K1 input binding: wall-01 / wall-02 GLB SHA-256 equal the bound values (A or B sample)
  K2 candidate shell: finite, closed (0 open / 0 non-manifold edges after 1 mm weld), positive volume, no degenerate tris
  K3 joint face: a candidate face lies on wall-01 cap plane (|d|<=1 mm, normal opposite); its corners match cap corners (<=1 mm);
     contact area >= 99% of the cap trapezoid
  K4 intrusion: positive-volume overlap of candidate with wall-01 end piece and wall-02 end piece (grid 0.05 m) <= 0.001 m3
     and max depth <= 0.005 m; reported separately from K3 contact
  K5 gap open: straight clear width between candidate free cap and wall-02 cap >= min clear (default 6.0 m, C param from LY-010);
     candidate free cap faces wall-02 cap (angle <= 0.05 deg, lateral offset <= 0.005 m)
  K6 section and levels: base y = 0.17 +-1 mm, top = 6.20 (A) / 8.00 (B) +-1 mm; free-cap bottom/top width = section +-2 mm
  K7 domain: arm1 == 2.423 +-0.002 m (measured), deflection == 64.166 +-0.01 deg; arm2 within the tested domain
"""
import sys, json, math, hashlib, struct
import numpy as np

BOUND = {'A': {'wall-01': 'cfbbc45a874a32a0501ea6e57dbd58aefcb2c2e42c943ad34f9704e3b7453a95',
               'wall-02': '8a17587a995e6851a1c4c7e0844f79cb880cf70348edb55dfb62891434b2afa9', 'top': 6.2, 'b': 8.0, 't': 5.6},
         'B': {'wall-01': '91eefa47f86de7a2e36be2003a8302cd7b91ac14569d48f0aad671f9bae14c32',
               'wall-02': 'b363a1155d1d278eee3865e4455f839f196678da1701310d087481903c6e4715', 'top': 8.0, 'b': 10.0, 't': 6.5}}
BASE = 0.17
COMP = {5123: np.uint16, 5125: np.uint32, 5126: np.float32, 5121: np.uint8}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}


def read_tris(p):
    d = open(p, 'rb').read(); off = 12; js = bc = None
    while off < len(d):
        L, T = struct.unpack_from('<II', d, off); c = d[off + 8: off + 8 + L]
        if T == 0x4E4F534A: js = json.loads(c)
        elif T == 0x004E4942: bc = c
        off += 8 + L

    def acc(i):
        a = js['accessors'][i]; bv = js['bufferViews'][a['bufferView']]
        o = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
        return np.frombuffer(bc, COMP[a['componentType']], a['count'] * NC[a['type']], o).reshape(a['count'], NC[a['type']]).astype(float)
    out = []
    for n in js['nodes']:
        if 'mesh' not in n: continue
        assert 'matrix' not in n and 'rotation' not in n and 'scale' not in n, 'checker expects identity/translation-only nodes'
        t = np.array(n.get('translation', [0, 0, 0]))
        for pr in js['meshes'][n['mesh']]['primitives']:
            P = acc(pr['attributes']['POSITION']) + t
            I = acc(pr['indices']).astype(int).ravel()
            out.append(P[I].reshape(-1, 3, 3))
    return np.concatenate(out)


def norms(T):
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); a = np.linalg.norm(n, axis=1)
    return n / np.maximum(a, 1e-12)[:, None], a / 2


def cap_of(T, near_xz):
    """free cap (vertical full-height faces) of a wall segment nearest to near_xz -> (center_bottom, outward normal, corners)"""
    N, A = norms(T); ylo, yhi = T[:, :, 1].min(), T[:, :, 1].max()
    idx = np.where((np.abs(N[:, 1]) < 1e-3) & (A > 1e-3))[0]
    best = None
    for i in idx:
        P = T[i]; c = P.mean(0)
        d = math.hypot(c[0] - near_xz[0], c[2] - near_xz[1])
        if best is None or d < best[0]: best = (d, i)
    n = N[best[1]]
    sel = [i for i in idx if np.dot(N[i], n) > 0.999 and abs(np.dot(T[i].mean(0) - T[best[1]].mean(0), n)) < 0.01]
    P = np.unique(np.round(T[sel].reshape(-1, 3), 4), axis=0)
    b = P[np.abs(P[:, 1] - ylo) < 1e-3]; t = P[np.abs(P[:, 1] - yhi) < 1e-3]
    return (b.max(0) + b.min(0)) / 2, n, b, t


def end_piece_planes(T, cap_c, cap_n, depth=60.0):
    """convex half-spaces of the last loft piece behind a cap: all wall triangles whose centroid is within `depth` of the cap"""
    N, A = norms(T)
    planes = []
    for i in range(len(T)):
        c = T[i].mean(0)
        if np.dot(c - cap_c, -cap_n) <= depth and A[i] > 1e-3:
            n = N[i]; d = float(n @ T[i, 0])
            if not any(np.dot(n, q[0]) > 0.9999 and abs(q[1] - d) < 0.01 for q in planes): planes.append((n, d))
    planes.append((cap_n, float(cap_n @ cap_c)))
    planes.append((-cap_n, float(-cap_n @ cap_c) + depth))  # far clip
    return planes


def inside_convex(P, planes, eps=0.0):
    m = np.ones(len(P), bool)
    for n, d in planes: m &= (P @ n - d) <= eps
    return m


def inside_mesh(P, T):
    """ray parity along +x (perturbed) for a closed mesh"""
    dirv = np.array([1.0, 1e-4, 2e-4]); dirv /= np.linalg.norm(dirv)
    cnt = np.zeros(len(P), int)
    for tri in T:
        e1 = tri[1] - tri[0]; e2 = tri[2] - tri[0]; h = np.cross(dirv, e2); a = e1 @ h
        if abs(a) < 1e-12: continue
        f = 1 / a; s = P - tri[0]; u = f * (s @ h); q = np.cross(s, e1); v = f * (q @ dirv); t = f * (q @ e2)
        cnt += ((u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)).astype(int)
    return cnt % 2 == 1


def shell(T):
    ec = {}
    for t in T:
        for a, b in ((0, 1), (1, 2), (2, 0)):
            ka, kb = tuple(np.round(t[a], 3)), tuple(np.round(t[b], 3))
            if ka == kb: continue
            k = (ka, kb) if ka < kb else (kb, ka); ec[k] = ec.get(k, 0) + 1
    vol = float(np.einsum('ij,ij->i', T[:, 0], np.cross(T[:, 1], T[:, 2])).sum() / 6)
    _, A = norms(T)
    return {'finite': bool(np.isfinite(T).all()), 'open_edges': sum(v == 1 for v in ec.values()), 'nonmanifold': sum(v > 2 for v in ec.values()),
            'volume': vol, 'degenerate': int((A < 1e-8).sum())}


def run_checks(T, w1, w2, sec, min_clear=6.0, sha1=None, sha2=None, arm2_domain=(0.0, 30.0)):
    S = BOUND[sec]; R = {}
    R['K1'] = {'pass': sha1 == S['wall-01'] and sha2 == S['wall-02'], 'wall01': sha1, 'wall02': sha2}
    sh = shell(T)
    R['K2'] = dict(sh, **{'pass': sh['finite'] and sh['open_edges'] == 0 and sh['nonmanifold'] == 0 and sh['volume'] > 0 and sh['degenerate'] == 0})
    c1, n1, b1, t1 = cap_of(w1, (2469.36, -2604.46)); c2, n2, b2, t2 = cap_of(w2, (2496.15, -2589.45))
    N, A = norms(T)
    on = [i for i in range(len(T)) if np.abs((T[i] - c1) @ n1).max() <= 0.001 and np.dot(N[i], n1) < -0.999]
    area = float(A[on].sum()); cap_area = (S['b'] + S['t']) / 2 * (S['top'] - BASE)
    V = np.unique(np.round(T.reshape(-1, 3), 4), axis=0)
    corners = np.vstack([b1, t1]); resid = float(max(np.min(np.linalg.norm(V - c, axis=1)) for c in corners))
    R['K3'] = {'pass': area >= 0.99 * cap_area and resid <= 0.001, 'contact_area_m2': round(area, 4), 'cap_area_m2': round(cap_area, 4), 'corner_residual_m': round(resid, 5)}
    # K4 intrusion
    worst = {}
    for name, (W, cc, nn) in {'wall-01': (w1, c1, n1), 'wall-02': (w2, c2, n2)}.items():
        planes = end_piece_planes(W, cc, nn)
        lo, hi = T.reshape(-1, 3).min(0), T.reshape(-1, 3).max(0)
        g = 0.05
        xs, ys, zs = [np.arange(lo[i] + g / 2, hi[i], g) for i in range(3)]
        P = np.stack(np.meshgrid(xs, ys, zs, indexing='ij'), -1).reshape(-1, 3)
        P = P[inside_convex(P, planes, eps=-1e-4)]  # strictly inside the wall piece
        P = P[inside_mesh(P, T)] if len(P) else P
        depth = float(((P - cc) @ -nn).max()) if len(P) else 0.0
        worst[name] = {'intrusion_m3': round(len(P) * g ** 3, 5), 'max_depth_m': round(depth, 4)}
    R['K4'] = {'pass': all(v['intrusion_m3'] <= 0.001 and v['max_depth_m'] <= 0.005 for v in worst.values()), **worst}
    # K5 free cap facing wall-02
    idx = np.where((np.abs(N[:, 1]) < 1e-3) & (A > 1e-3) & (np.abs(((T - c1) @ n1)).max(1) > 0.01))[0]
    fc = None
    for i in idx:
        if np.dot(N[i], n2) < -0.999:
            fc = (T[i].mean(0), N[i]); break
    if fc is None:
        R['K5'] = {'pass': False, 'reason': 'no free cap facing wall-02'}
    else:
        Pf = np.unique(np.round(T[[i for i in idx if np.dot(N[i], n2) < -0.999]].reshape(-1, 3), 4), axis=0)
        bf = Pf[np.abs(Pf[:, 1] - BASE) < 1e-3]; cf = (bf.max(0) + bf.min(0)) / 2
        v = cf - c2; clear = float(v @ n2); lat = float(np.linalg.norm((v - (v @ n2) * n2)[[0, 2]]))
        ang = math.degrees(math.acos(min(1, -float(fc[1] @ n2))))
        R['K5'] = {'pass': clear >= min_clear and ang <= 0.05 and lat <= 0.005, 'clear_width_m': round(clear, 4), 'min_clear_m': min_clear,
                   'facing_angle_deg': round(ang, 4), 'lateral_offset_m': round(lat, 4)}
    yl, yh = T[:, :, 1].min(), T[:, :, 1].max()
    fw = None
    if fc is not None:
        h = np.array([-n2[2], 0, n2[0]]); tf = Pf[np.abs(Pf[:, 1] - yh) < 1e-3]
        fw = (float(np.ptp(bf @ h)), float(np.ptp(tf @ h)) if len(tf) else -1)
    R['K6'] = {'pass': abs(yl - BASE) <= 0.001 and abs(yh - S['top']) <= 0.001 and fw is not None and abs(fw[0] - S['b']) <= 0.002 and abs(fw[1] - S['t']) <= 0.002,
               'base_y': round(float(yl), 4), 'top_y': round(float(yh), 4), 'free_cap_widths': None if fw is None else [round(x, 4) for x in fw]}
    # K7 domain (vertex X from cap lines)
    M = np.array([n1[[0, 2]], -n2[[0, 2]]]).T; t = np.linalg.solve(M, (c2 - c1)[[0, 2]])
    defl = math.degrees(math.acos(min(1, -float(n1 @ n2)))); defl = 180 - defl if defl > 90 else defl
    arm2 = None if fc is None else float(t[1] - (cf - c2) @ n2)
    R['K7'] = {'pass': abs(t[0] - 2.423) <= 0.002 and abs(defl - 64.166) <= 0.01 and arm2 is not None and arm2_domain[0] - 1e-3 <= arm2 <= arm2_domain[1] + 1e-3,
               'arm1_m': round(float(t[0]), 4), 'deflection_deg': round(defl, 4), 'arm2_m': None if arm2 is None else round(arm2, 4), 'domain': arm2_domain}
    R['allPass'] = all(v['pass'] for k, v in R.items() if k.startswith('K'))
    return R


# ---------------- in-memory fixtures (TEST ONLY, never exported) ----------------
def frustum_from_polys(bot, top):
    """closed polyhedron from matching bottom/top convex-ish polygons (CCW seen from above in x,-z)"""
    n = len(bot); T = []
    cb = bot.mean(0); ct = top.mean(0)
    for i in range(n):
        j = (i + 1) % n
        T.append([cb, bot[j], bot[i]]); T.append([ct, top[i], top[j]])
        T.append([bot[i], bot[j], top[j]]); T.append([bot[i], top[j], top[i]])
    T = np.array(T)
    if shell(T)['volume'] < 0: T = T[:, ::-1]
    return T


def fixture(w1, w2, sec, arm2, mode='chamfer', shift=0.0):
    S = BOUND[sec]
    c1, n1, b1, t1 = cap_of(w1, (2469.36, -2604.46)); c2, n2, _, _ = cap_of(w2, (2496.15, -2589.45))
    M = np.array([n1[[0, 2]], -n2[[0, 2]]]).T; tt = np.linalg.solve(M, (c2 - c1)[[0, 2]])
    X = c1 + tt[0] * n1
    d1 = n1; d2 = -n2

    def perp(d): return np.array([-d[2], 0, d[0]])
    def sec_pts(c, d, y, hw): p = perp(d); return c + p * hw + np.array([0, y - c[1], 0]), c - p * hw + np.array([0, y - c[1], 0])
    S2 = X + d2 * arm2
    out = {}
    for lvl, y, hw in (('b', BASE, S['b'] / 2), ('t', S['top'], S['t'] / 2)):
        a0, a1 = sec_pts(c1, d1, y, hw); e0, e1 = sec_pts(S2, d2, y, hw)
        # miter points: intersection of rails
        def inter(p, dp, q, dq):
            A = np.array([dp[[0, 2]], -dq[[0, 2]]]).T; s = np.linalg.solve(A, (q - p)[[0, 2]]); return p + s[0] * dp
        m0 = inter(a0, d1, e0, d2); m1 = inter(a1, d1, e1, d2)
        # outer rail = the one whose miter point lies ahead of the cap (positive along d1)
        out0 = (m0 - c1) @ d1 > (m1 - c1) @ d1
        if mode == 'miter':
            poly = [a0, m0, e0, e1, m1, a1]
        else:  # chamfer: keep outer miter point, cut inner corner with a straight chord a_inner -> e_inner
            poly = [a0, m0, e0, e1, a1] if out0 else [a0, e0, e1, m1, a1]
        out[lvl] = np.array(poly)
    bot, top = out['b'], out['t']
    if mode == 'miter':
        T = frustum_from_polys(bot, top)
    else:
        T = frustum_from_polys(bot, top)
    T = T + n1 * shift
    return T


def main():
    mode = sys.argv[1]; LAB = sys.argv[2]
    W = LAB + '/docs/cities/luoyang/assets/city-wall/'
    if mode == 'selftest':
        OUT = sys.argv[3]; res = {'note': 'fixtures are in-memory test geometry only; nothing exported', 'cases': {}}
        for sec in ('A', 'B'):
            p1, p2 = W + sec + '/wall-01.glb', W + sec + '/wall-02.glb'
            w1, w2 = read_tris(p1), read_tris(p2)
            s1 = hashlib.sha256(open(p1, 'rb').read()).hexdigest(); s2 = hashlib.sha256(open(p2, 'rb').read()).hexdigest()
            # sweep arm2 for the chamfer form to find the smallest arm2 with zero intrusion (domain lower bound)
            sweep = []
            for arm2 in np.round(np.arange(1.0, 8.01, 0.25), 3):
                r = run_checks(fixture(w1, w2, sec, arm2), w1, w2, sec, sha1=s1, sha2=s2)
                sweep.append({'arm2': float(arm2), 'K4': r['K4']['pass'], 'w01_depth': r['K4']['wall-01']['max_depth_m'], 'w01_m3': r['K4']['wall-01']['intrusion_m3'], 'K2': r['K2']['pass']})
            ok = [s['arm2'] for s in sweep if s['K4'] and s['K2']]
            lo = min(ok) if ok else None
            res['cases'][sec + '-sweep-chamfer'] = sweep
            if lo is None:
                continue
            dom = (lo, 29.577 - 6.0)
            cases = {
                'P1-chamfer-at-domain-min': (fixture(w1, w2, sec, lo), s1, s2, True),
                'P2-chamfer-arm2-6m': (fixture(w1, w2, sec, 6.0), s1, s2, True),
                'N1-full-miter-arm2-min (fold/intrusion expected)': (fixture(w1, w2, sec, lo, mode='miter'), s1, s2, False),
                'N2-closes-gap (arm2=29.0, clear<6)': (fixture(w1, w2, sec, 29.0), s1, s2, False),
                'N3-shifted-5mm-off-cap': (fixture(w1, w2, sec, 6.0, shift=0.005), s1, s2, False),
                'N4-shifted-20mm-into-wall': (fixture(w1, w2, sec, 6.0, shift=-0.02), s1, s2, False),
                'N5-wrong-input-sha': (fixture(w1, w2, sec, 6.0), '0' * 64, s2, False),
                'N6-below-domain (arm2=lo-0.5)': (fixture(w1, w2, sec, max(0.25, lo - 0.5)), s1, s2, False),
            }
            for name, (T, a, b, expect) in cases.items():
                r = run_checks(T, w1, w2, sec, sha1=a, sha2=b, arm2_domain=dom)
                res['cases'][sec + '-' + name] = {'expectPass': expect, 'gotPass': r['allPass'], 'ok': r['allPass'] == expect,
                                                  'failed': [k for k, v in r.items() if k.startswith('K') and not v['pass']], 'detail': r}
        res['selftestOk'] = all(v['ok'] for k, v in res['cases'].items() if isinstance(v, dict) and 'ok' in v)
        json.dump(res, open(OUT, 'w'), indent=1, default=float)
        print('selftestOk', res['selftestOk'])
    else:
        cand, sec, OUT = sys.argv[3], sys.argv[4], sys.argv[5]
        mc = float(sys.argv[sys.argv.index('--min-clear') + 1]) if '--min-clear' in sys.argv else 6.0
        p1, p2 = W + sec + '/wall-01.glb', W + sec + '/wall-02.glb'
        r = run_checks(read_tris(cand), read_tris(p1), read_tris(p2), sec, mc,
                       hashlib.sha256(open(p1, 'rb').read()).hexdigest(), hashlib.sha256(open(p2, 'rb').read()).hexdigest())
        r['candidate'] = {'path': cand, 'sha256': hashlib.sha256(open(cand, 'rb').read()).hexdigest()}
        json.dump(r, open(OUT, 'w'), indent=1, default=float); print('allPass', r['allPass'])


if __name__ == '__main__':
    main()
