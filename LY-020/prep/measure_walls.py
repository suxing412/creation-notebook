"""LY-020 prep: read-only measurement of the city-wall segments as loaded by the Luoyang city scene.

Reads GLBs from the lab repo (read-only), writes JSON to this prep folder only.
Measures:
  1. per-segment cross-section stations (bottom/top width, height, turn angle, miter ratio)
  2. free end caps (vertical termination faces) and the gap between facing caps of adjacent segments
     (distance, angle, lateral/vertical misalignment), matched to gate C-projection points
  3. foot-line vs ground: vertical ray from every sample on the wall's bottom boundary to the
     topmost ground triangle of the 4 city ground GLBs -> floating gap / buried depth / no-ground
  4. pairwise wall-wall contact (bottom footprint overlap) between different segments
Usage: python -I measure_walls.py <lab_root> <out.json>
"""
import sys, json, struct, hashlib, math
import numpy as np

LAB = sys.argv[1] if len(sys.argv) > 1 else 'D:/GitHub/creation-notebook-lab'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'measure-walls.json'
CITY = LAB + '/docs/cities/luoyang/'
COMP = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def read_glb(p):
    d = open(p, 'rb').read()
    assert d[:4] == b'glTF'
    off, js, bc = 12, None, None
    while off < len(d):
        L, T = struct.unpack_from('<II', d, off)
        c = d[off + 8: off + 8 + L]
        if T == 0x4E4F534A:
            js = json.loads(c)
        elif T == 0x004E4942:
            bc = c
        off += 8 + L
    return js, bc


def acc(js, bc, i):
    a = js['accessors'][i]
    bv = js['bufferViews'][a['bufferView']]
    assert 'extensions' not in bv, 'compressed buffer not supported'
    dt, n = COMP[a['componentType']], NC[a['type']]
    st = bv.get('byteStride', 0)
    base = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    isz = np.dtype(dt).itemsize
    if st and st != isz * n:
        raw = np.frombuffer(bc, np.uint8, st * (a['count'] - 1) + isz * n, base)
        arr = np.lib.stride_tricks.as_strided(raw, (a['count'], isz * n), (st, 1)).copy().view(dt)
    else:
        arr = np.frombuffer(bc, dt, a['count'] * n, base)
    return arr.reshape(a['count'], n).astype(float)


def local(n):
    if 'matrix' in n:
        return np.array(n['matrix'], float).reshape(4, 4).T
    t, r, s = n.get('translation', [0, 0, 0]), n.get('rotation', [0, 0, 0, 1]), n.get('scale', [1, 1, 1])
    x, y, z, w = r
    R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    M = np.eye(4); M[:3, :3] = R @ np.diag(s); M[:3, 3] = t
    return M


def tris(p):
    js, bc = read_glb(p)
    out = []
    sc = js['scenes'][js.get('scene', 0)]
    st = [(i, np.eye(4)) for i in sc['nodes']]
    while st:
        i, P = st.pop()
        n = js['nodes'][i]; W = P @ local(n)
        if 'mesh' in n:
            for pr in js['meshes'][n['mesh']]['primitives']:
                if pr.get('mode', 4) != 4:
                    continue
                pos = acc(js, bc, pr['attributes']['POSITION'])
                ind = acc(js, bc, pr['indices']).astype(int).ravel() if 'indices' in pr else np.arange(len(pos))
                Pw = (np.c_[pos, np.ones(len(pos))] @ W.T)[:, :3]
                out.append(Pw[ind].reshape(-1, 3, 3))
        st += [(c, W) for c in n.get('children', [])]
    return np.concatenate(out)


def tri_normals(T):
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    a = np.linalg.norm(n, axis=1)
    return n / np.maximum(a, 1e-12)[:, None], a / 2


# ---------------- inputs ----------------
data = json.load(open(CITY + 'data/west/city-wall-interface.json', encoding='utf-8'))
cons = json.load(open(CITY + 'data/west/city-wall-constraints.json', encoding='utf-8'))
gates = [{'id': g['feature_id'], 'name': g['name'], 'xz': [g['C_projection_only'][0], -g['C_projection_only'][1]],
          'B_xz': [g['B_point'][0], -g['B_point'][1]], 'seg0': g['nearest_segment_zero_based']}
         for g in cons['gate_projection_diagnostics']]
CITY_A = ['A/wall-00', 'A/wall-01', 'A/wall-02', 'A/wall-03', 'A/wall-04', 'A/wall-05', 'A/wall-06', 'A/wall-07',
          'direct/wall-08', 'direct/wall-09', 'A/wall-10', 'A/wall-11']
CITY_B = ['B/wall-%02d' % i for i in range(12)]
GROUND = ['network-ground-stitched', 'retained', 'south', 'D08']
GROUND_POS = {'D08': [580.0, 0.0, -960.0]}  # city-data.mjs node ground-D08 position; others [0,0,0]
YB = 0.17
report = {'schema': 'LY-020/measure-walls-1', 'lab': LAB, 'inputs': {}, 'gates': gates}


def seg_analysis(name):
    p = CITY + 'assets/city-wall/' + name + '.glb'
    T = tris(p)
    report['inputs'][name] = {'path': 'docs/cities/luoyang/assets/city-wall/' + name + '.glb', 'sha256': sha(p), 'triangles': int(len(T))}
    N, A = tri_normals(T)
    V = np.unique(np.round(T.reshape(-1, 3), 4), axis=0)
    ylo, yhi = V[:, 1].min(), V[:, 1].max()
    # stations: cluster bottom verts (y==ylo) pairwise into foot pairs across the wall
    bot = V[np.abs(V[:, 1] - ylo) < 1e-3]
    top = V[np.abs(V[:, 1] - yhi) < 1e-3]
    # free caps: vertical triangles (|ny|<1e-4) spanning full height
    caps = []
    vert = np.abs(N[:, 1]) < 1e-3  # float32 at |coord|~4000 m gives ~1e-4 normal noise
    full = (T[:, :, 1].min(1) <= ylo + 1e-3) | (T[:, :, 1].max(1) >= yhi - 1e-3)
    idx = np.where(vert & full & (A > 1e-3))[0]
    # group cap triangles by shared vertices + parallel normal (plane offset is unreliable in float32
    # at |coord|~4000 m, so connectivity is used instead of n.p)
    groups = []
    for i in idx:
        n = N[i]; ks = {tuple(np.round(p, 3)) for p in T[i]}
        hit = [g for g in groups if np.dot(g['n'], n) > 0.999 and g['k'] & ks]
        if hit:
            g = hit[0]
            for o in hit[1:]:
                g['t'] += o['t']; g['k'] |= o['k']; groups.remove(o)
            g['t'].append(i); g['k'] |= ks
        else:
            groups.append({'n': n, 'k': ks, 't': [i]})
    for g in groups:
        P = T[g['t']].reshape(-1, 3)
        b = P[np.abs(P[:, 1] - ylo) < 1e-3]
        t = P[np.abs(P[:, 1] - yhi) < 1e-3]
        if len(b) < 2 or len(t) < 2:
            continue
        # horizontal extent along the cap plane
        hz = np.array([-g['n'][2], 0, g['n'][0]])
        bw = float(np.ptp(b @ hz)); tw = float(np.ptp(t @ hz))
        area = float(A[g['t']].sum())
        c = (b.max(0) + b.min(0)) / 2
        caps.append({'center_bottom': c.round(4).tolist(), 'outward_normal': g['n'].round(5).tolist(),
                     'bottom_width': round(bw, 4), 'top_width': round(tw, 4), 'height': round(float(yhi - ylo), 4),
                     'area': round(area, 3), 'expected_trapezoid_area': round((bw + tw) / 2 * (yhi - ylo), 3)})
    # bottom footprint boundary edges (edges used once among bottom-facing triangles)
    downs = np.where((N[:, 1] < -0.999) & (np.abs(T[:, :, 1] - ylo).max(1) < 1e-3))[0]
    edges = {}
    for i in downs:
        for a, b in ((0, 1), (1, 2), (2, 0)):
            ka = tuple(np.round(T[i, a], 3)); kb = tuple(np.round(T[i, b], 3))
            k = (ka, kb) if ka < kb else (kb, ka)
            edges[k] = edges.get(k, 0) + 1
    boundary = [k for k, c in edges.items() if c == 1]
    foot_area = float(A[downs].sum())
    # closedness: every edge shared by exactly 2 triangles (position-welded)
    ec = {}
    for t in T:
        for a, b in ((0, 1), (1, 2), (2, 0)):
            ka = tuple(np.round(t[a], 3)); kb = tuple(np.round(t[b], 3))
            if ka == kb:
                continue
            k = (ka, kb) if ka < kb else (kb, ka)
            ec[k] = ec.get(k, 0) + 1
    open_edges = sum(1 for v in ec.values() if v == 1)
    nonman = sum(1 for v in ec.values() if v > 2)
    # signed volume (divergence theorem); meaningful only if closed and consistently wound
    vol = float(np.einsum('ij,ij->i', T[:, 0], np.cross(T[:, 1], T[:, 2])).sum() / 6)
    # tiny / sliver triangles
    e = np.stack([np.linalg.norm(T[:, 1] - T[:, 0], axis=1), np.linalg.norm(T[:, 2] - T[:, 1], axis=1), np.linalg.norm(T[:, 0] - T[:, 2], axis=1)], 1)
    sliver = int(((e.min(1) < 0.01) & (A > 0)).sum())
    return {'name': name, 'T': T, 'boundary': boundary, 'summary': {
        'y_bottom': round(float(ylo), 4), 'y_top': round(float(yhi), 4), 'bottom_vertices': int(len(bot)), 'top_vertices': int(len(top)),
        'triangles': int(len(T)), 'footprint_area_m2': round(foot_area, 2), 'open_edges': open_edges, 'nonmanifold_edges': nonman,
        'signed_volume_m3': round(vol, 2), 'sliver_tris_minEdge_lt_1cm': sliver, 'free_caps': caps}}


def stations(seg):
    """For pure-loft A/B segments: walk the bottom-face boundary loop L0..Ln Rn..R0, split at the two
    cap edges, pair L_k with R_k, and report bottom/top width and turn angle at every station."""
    T = seg['T']; N, A = tri_normals(T)
    ylo = T[:, :, 1].min(); yhi = T[:, :, 1].max()
    adj = {}
    for (a, b) in seg['boundary']:
        adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    if any(len(v) != 2 for v in adj.values()):
        return None
    start = next(iter(adj)); loop = [start]; prev = None
    while True:
        nx = [v for v in adj[loop[-1]] if v != prev][0] if prev is not None else adj[start][0]
        if nx == start:
            break
        prev = loop[-1]; loop.append(nx)
    # cap edges: boundary edges lying in a vertical full-height triangle
    capv = np.where((np.abs(N[:, 1]) < 1e-3) & (A > 1e-3))[0]
    capset = set()
    for i in capv:
        ks = [tuple(np.round(p, 3)) for p in T[i]]
        for a in ks:
            for b in ks:
                if a != b:
                    capset.add((a, b))
    m = len(loop)
    cut = [k for k in range(m) if (loop[k], loop[(k + 1) % m]) in capset]
    if len(cut) != 2:
        return {'error': 'cap edges found: %d' % len(cut)}
    k0 = cut[0]
    seq = loop[k0 + 1:] + loop[:k0 + 1]  # starts after cap edge 0: R0? ... ends with L0
    half = m // 2
    side1 = seq[:half]; side2 = seq[half:][::-1]
    top = np.unique(np.round(T.reshape(-1, 3), 4), axis=0); top = top[np.abs(top[:, 1] - yhi) < 1e-3][:, [0, 2]]
    out = []
    C = [((np.array(a)[[0, 2]] + np.array(b)[[0, 2]]) / 2) for a, b in zip(side1, side2)]
    for n, (a, b) in enumerate(zip(side1, side2)):
        a = np.array(a)[[0, 2]]; b = np.array(b)[[0, 2]]
        w = float(np.linalg.norm(a - b))
        tp = top[np.argsort(np.linalg.norm(top - C[n], axis=1))[:2]]
        st = {'i': n, 'center_xz': C[n].round(3).tolist(), 'bottom_width': round(w, 3), 'top_width': round(float(np.linalg.norm(tp[0] - tp[1])), 3)}
        if 0 < n < len(C) - 1:
            d0 = C[n] - C[n - 1]; d1 = C[n + 1] - C[n]
            ang = math.degrees(math.atan2(d0[0] * d1[1] - d0[1] * d1[0], d0 @ d1))
            st['turn_deg'] = round(ang, 3)
            st['miter_expected_bottom_width'] = round(8.0 / max(math.cos(math.radians(abs(ang) / 2)), 1e-6), 3)
            st['len_prev'] = round(float(np.linalg.norm(d0)), 3); st['len_next'] = round(float(np.linalg.norm(d1)), 3)
            # inner-rail fold check: miter setback on the inner side must be shorter than both adjacent pieces
            st['miter_setback_m'] = round(4.0 * math.tan(math.radians(abs(ang) / 2)), 3)
            st['inner_rail_folds'] = bool(st['miter_setback_m'] >= min(st['len_prev'], st['len_next']))
        out.append(st)
    return out


segsA = [seg_analysis(n) for n in CITY_A]
segsB = [seg_analysis(n) for n in CITY_B]
gb = CITY + 'assets/city-wall/direct/gate-body-only.glb'
report['inputs']['direct/gate-body-only'] = {'path': 'docs/cities/luoyang/assets/city-wall/direct/gate-body-only.glb', 'sha256': sha(gb)}
for s in segsA + segsB:
    if s['name'].startswith(('A/', 'B/')):
        s['summary']['stations'] = stations(s)


def caps_gaps(segs):
    allc = [(s['name'], c) for s in segs for c in s['summary']['free_caps']]
    res = []
    seen = set()
    for i, (na, ca) in enumerate(allc):
        best = None
        for j, (nb, cb) in enumerate(allc):
            if nb == na:
                continue
            d = np.linalg.norm(np.array(ca['center_bottom']) - np.array(cb['center_bottom']))
            if best is None or d < best[0]:
                best = (d, j)
        d, j = best
        key = tuple(sorted((i, j)))
        if key in seen:
            continue
        seen.add(key)
        nb, cb = allc[j]
        pa, pb = np.array(ca['center_bottom']), np.array(cb['center_bottom'])
        na_, nb_ = np.array(ca['outward_normal']), np.array(cb['outward_normal'])
        facing = float(np.degrees(np.arccos(np.clip(-na_ @ nb_, -1, 1))))  # 0 = exactly facing
        v = pb - pa
        along = float(v @ na_)
        lateral = float(np.linalg.norm(v - (v @ na_) * na_ - v[1] * np.array([0, 1, 0])))
        mid = (pa + pb) / 2
        g = min(gates, key=lambda g: math.hypot(g['xz'][0] - mid[0], g['xz'][1] - mid[2]))
        gd = math.hypot(g['xz'][0] - mid[0], g['xz'][1] - mid[2])
        res.append({'a': na, 'b': nb, 'center_distance_m': round(float(d), 3), 'gap_along_normal_m': round(along, 3),
                    'lateral_offset_m': round(lateral, 3), 'cap_facing_angle_deg': round(facing, 3),
                    'width_a': ca['bottom_width'], 'width_b': cb['bottom_width'],
                    'nearest_gate': g['id'], 'nearest_gate_name': g['name'], 'gate_to_gap_mid_m': round(gd, 3),
                    'mid_xz': [round(float(mid[0]), 3), round(float(mid[2]), 3)]})
    unpaired = [(n, c) for n, c in allc]
    return res


report['segments_A'] = {s['name']: s['summary'] for s in segsA}
report['segments_B'] = {s['name']: s['summary'] for s in segsB}
report['gaps_A'] = caps_gaps(segsA)
report['gaps_B'] = caps_gaps(segsB)

# ---------------- ground ----------------
G = []
for g in GROUND:
    p = CITY + 'assets/ground-atomic/' + g + '.glb'
    T = tris(p) + np.array(GROUND_POS.get(g, [0.0, 0.0, 0.0]))
    report['inputs']['ground/' + g] = {'path': 'docs/cities/luoyang/assets/ground-atomic/' + g + '.glb', 'sha256': sha(p), 'triangles': int(len(T))}
    G.append(T)
GT = np.concatenate(G)
CELL = 10.0
mn = GT[:, :, [0, 2]].min(1); mx = GT[:, :, [0, 2]].max(1)
grid = {}
for i in range(len(GT)):
    for gx in range(int(math.floor(mn[i, 0] / CELL)), int(math.floor(mx[i, 0] / CELL)) + 1):
        for gz in range(int(math.floor(mn[i, 1] / CELL)), int(math.floor(mx[i, 1] / CELL)) + 1):
            grid.setdefault((gx, gz), []).append(i)


def ground_h(x, z):
    ids = grid.get((int(math.floor(x / CELL)), int(math.floor(z / CELL))))
    if not ids:
        return None
    best = None
    for i in ids:
        a, b, c = GT[i]
        v0 = b[[0, 2]] - a[[0, 2]]; v1 = c[[0, 2]] - a[[0, 2]]; v2 = np.array([x, z]) - a[[0, 2]]
        den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-12:
            continue
        u = (v2[0] * v1[1] - v1[0] * v2[1]) / den; w = (v0[0] * v2[1] - v2[0] * v0[1]) / den
        if u >= -1e-7 and w >= -1e-7 and u + w <= 1 + 1e-7:
            h = a[1] + u * (b[1] - a[1]) + w * (c[1] - a[1])
            best = h if best is None else max(best, h)
    return best


STEP = 2.0
foot = {}
samples_all = []
for s in segsA:
    pts = []
    for (a, b) in s['boundary']:
        a = np.array(a); b = np.array(b)
        L = np.linalg.norm(b - a)
        n = max(1, int(L // STEP))
        for k in range(n + 1):
            pts.append(a + (b - a) * k / n)
    hs = [ground_h(p[0], p[2]) for p in pts]
    hit = np.array([h for h in hs if h is not None])
    miss = sum(1 for h in hs if h is None)
    gap = YB - hit if len(hit) else np.array([])
    entry = {'samples': len(pts), 'no_ground': miss, 'no_ground_pct': round(100 * miss / max(1, len(pts)), 1)}
    if len(hit):
        entry.update({'ground_h_min': round(float(hit.min()), 4), 'ground_h_max': round(float(hit.max()), 4),
                      'ground_h_mean': round(float(hit.mean()), 4),
                      'float_gap_max_m': round(float(gap.max()), 4), 'float_gap_gt_2cm': int((gap > 0.02).sum()),
                      'float_gap_gt_10cm': int((gap > 0.10).sum()), 'buried_max_m': round(float(-gap.min()), 4),
                      'buried_gt_2cm': int((gap < -0.02).sum())})
    # extents of no-ground stretch
    nog = np.array([p for p, h in zip(pts, hs) if h is None])
    if len(nog):
        entry['no_ground_bbox_xz'] = [round(float(nog[:, 0].min()), 2), round(float(nog[:, 2].min()), 2), round(float(nog[:, 0].max()), 2), round(float(nog[:, 2].max()), 2)]
    foot[s['name']] = entry
    samples_all += [(s['name'], p.tolist(), h) for p, h in zip(pts, hs)]
report['foot_vs_ground_A'] = {'step_m': STEP, 'wall_base_y': YB, 'ground_union_bounds': [GT.reshape(-1, 3).min(0).round(3).tolist(), GT.reshape(-1, 3).max(0).round(3).tolist()], 'per_segment': foot}

# histogram of ground heights under hit samples
H = np.array([h for _, _, h in samples_all if h is not None])
report['foot_vs_ground_A']['ground_h_hist'] = {str(k): int(v) for k, v in zip(np.round(np.linspace(0, 0.21, 8), 3), np.histogram(H, bins=7, range=(0, 0.21))[0])}


# ---------------- bent gaps (caps not facing) ----------------
from scipy.spatial import cKDTree
def bent(segs, gaps):
    capmap = {s['name']: s['summary']['free_caps'] for s in segs}
    out = []
    for g in gaps:
        if g['cap_facing_angle_deg'] < 1.0 or min(g['width_a'], g['width_b']) < 1.0:
            continue
        ca = min(capmap[g['a']], key=lambda c: abs(c['bottom_width'] - g['width_a']) + np.linalg.norm(np.array(c['center_bottom'])[[0, 2]] - np.array(g['mid_xz'])))
        cb = min(capmap[g['b']], key=lambda c: abs(c['bottom_width'] - g['width_b']) + np.linalg.norm(np.array(c['center_bottom'])[[0, 2]] - np.array(g['mid_xz'])))
        pa = np.array(ca['center_bottom'])[[0, 2]]; pb = np.array(cb['center_bottom'])[[0, 2]]
        da = np.array(ca['outward_normal'])[[0, 2]]; db = np.array(cb['outward_normal'])[[0, 2]]
        M = np.array([da, -db]).T
        t = np.linalg.solve(M, pb - pa)
        X = pa + t[0] * da
        # rails: left/right bottom corners of each cap
        def corners(c):
            p = np.array(c['center_bottom'])[[0, 2]]; n = np.array(c['outward_normal'])[[0, 2]]; h = np.array([-n[1], n[0]])
            return p + h * c['bottom_width'] / 2, p - h * c['bottom_width'] / 2
        a1, a2 = corners(ca); b1, b2 = corners(cb)
        # match rails by side of polyline: pair corners so that both pairs do not cross
        r1 = (np.linalg.norm(a1 - b2), np.linalg.norm(a2 - b1)); r2 = (np.linalg.norm(a1 - b1), np.linalg.norm(a2 - b2))
        rails = r1 if sum(r1) < sum(r2) else r2
        deflect = 180.0 - g['cap_facing_angle_deg'] if g['cap_facing_angle_deg'] > 90 else g['cap_facing_angle_deg']
        out.append({'a': g['a'], 'b': g['b'], 'gate': g['nearest_gate_name'], 'polyline_vertex_xz': X.round(3).tolist(),
                    'cap_a_to_vertex_m': round(float(t[0]), 3), 'cap_b_to_vertex_m': round(float(t[1]), 3),
                    'path_length_through_vertex_m': round(float(t[0] + t[1]), 3), 'chord_m': g['center_distance_m'],
                    'deflection_deg': round(deflect, 3), 'rail_gap_widths_m': [round(float(r), 3) for r in sorted(rails)],
                    'gate_C_projection_to_vertex_m': round(float(np.linalg.norm(X - np.array([gg['xz'] for gg in gates if gg['name'] == g['nearest_gate_name']][0]))), 3)})
    return out
report['bent_gaps_A'] = bent(segsA, report['gaps_A'])
report['bent_gaps_B'] = bent(segsB, report['gaps_B'])

# ---------------- plan distance from wall foot to nearest ground ----------------
gv = GT.reshape(-1, 3)[:, [0, 2]]
kd = cKDTree(gv)
def d2tri(p, t):
    a, b, c = t[:, [0, 2]]
    def seg(p, u, v):
        w = v - u; k = np.clip((p - u) @ w / max(w @ w, 1e-12), 0, 1); return np.linalg.norm(p - (u + k * w))
    v0 = b - a; v1 = c - a; v2 = p - a; den = v0[0] * v1[1] - v1[0] * v0[1]
    if abs(den) > 1e-12:
        u = (v2[0] * v1[1] - v1[0] * v2[1]) / den; w = (v0[0] * v2[1] - v2[0] * v0[1]) / den
        if u >= 0 and w >= 0 and u + w <= 1:
            return 0.0
    return min(seg(p, a, b), seg(p, b, c), seg(p, c, a))
near = {}
for name in report['foot_vs_ground_A']['per_segment']:
    pts = np.array([p for n, p, h in samples_all if n == name])[:, [0, 2]]
    dist, vi = kd.query(pts, k=1)
    k = int(np.argmin(dist))
    _, cand = kd.query(pts[k], k=48)
    tri_ids = np.unique(np.asarray(cand) // 3)
    exact = min(d2tri(pts[k], GT[i]) for i in tri_ids)
    near[name] = {'min_plan_distance_to_ground_m': round(float(exact), 3), 'at_xz': pts[k].round(2).tolist(),
                  'median_vertex_distance_m': round(float(np.median(dist)), 1)}
report['foot_vs_ground_A']['nearest_ground'] = near
gapfloor = {}
for g in report['gaps_A']:
    if min(g['width_a'], g['width_b']) < 1.0:
        continue
    h = ground_h(*g['mid_xz'])
    gapfloor[g['nearest_gate_name']] = {'mid_xz': g['mid_xz'], 'ground_h_at_gap_mid': None if h is None else round(float(h), 4)}
report['gap_floor_ground_A'] = gapfloor
report['first_screen_note'] = 'city-data.mjs: all 13 wall nodes initial=true (chapter walls); all 4 ground nodes initial=false (chapter terrain)'

# ---------------- earthwall family (library, not loaded in city) ----------------
fam = {}
for f in ['A-LOD0', 'B-LOD0', 'C-LOD0', 'C-LOD1', 'C-LOD2']:
    p = LAB + '/docs/library/models/m-luoyang-earthwall-family/files/earthwall-' + f + '.glb'
    T = tris(p)
    V = T.reshape(-1, 3)
    xmin = V[:, 0].min(); end = V[np.abs(V[:, 0] - xmin) < 0.05]
    fam[f] = {'sha256': sha(p), 'bytes': len(open(p, 'rb').read()), 'triangles': int(len(T)), 'bbox_min': V.min(0).round(4).tolist(), 'bbox_max': V.max(0).round(4).tolist(),
              'end_profile_x_min': {'z_span_at_bottom': round(float(np.ptp(end[end[:, 1] < 0.05][:, 2])) if (end[:, 1] < 0.05).any() else -1, 4),
                                    'z_span_at_top': round(float(np.ptp(end[end[:, 1] > end[:, 1].max() - 0.05][:, 2])), 4), 'vertices': int(len(end))}}
report['earthwall_family'] = fam

for s in segsA + segsB:
    s.pop('T', None)
json.dump(report, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('wrote', OUT)
