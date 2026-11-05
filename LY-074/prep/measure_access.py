"""LY-074 prep: measure the four-side stairs and the ground in front of them on the
existing mingtang A/B GLBs (read-only). Pure numpy GLB reader, no Blender needed.

usage: python -I measure_access.py <out.json> <glb> [<glb> ...]

Frame: glTF Y-up, metres, as stored (all node TRS are identity in these files; the
script asserts that). Sides: +X (east?), -X, +Z, -Z -- compass names are NOT asserted,
the model has no north marker; LY-005/006 must freeze which axis is north.

Vertical support test = vertical ray hit against faces whose winding normal has
ny > 0.5 (walkable-ish).  Clearance test = any face (either orientation) between
support+0.02 m and support+H above the same xz point.  These are discrete point
probes, not continuous body motion.
"""
import json, struct, sys, hashlib
import numpy as np

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def load(path):
    b = open(path, 'rb').read()
    magic, ver, length = struct.unpack('<III', b[:12])
    assert magic == 0x46546C67 and ver == 2 and length == len(b), 'bad GLB header'
    jl = struct.unpack('<I', b[12:16])[0]
    js = json.loads(b[20:20 + jl])
    off = 20 + jl
    bl = struct.unpack('<I', b[off:off + 4])[0]
    bin_ = b[off + 8:off + 8 + bl]
    return js, bin_, hashlib.sha256(b).hexdigest(), len(b)


def acc(js, bin_, i):
    a = js['accessors'][i]
    bv = js['bufferViews'][a['bufferView']]
    dt = np.dtype(CT[a['componentType']])
    n = NC[a['type']]
    start = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = bv.get('byteStride', 0)
    if stride and stride != dt.itemsize * n:
        raw = np.frombuffer(bin_, np.uint8, count=stride * a['count'], offset=start).reshape(a['count'], stride)
        return raw[:, :dt.itemsize * n].copy().view(dt).reshape(a['count'], n)
    return np.frombuffer(bin_, dt, count=a['count'] * n, offset=start).reshape(a['count'], n) if n > 1 else \
        np.frombuffer(bin_, dt, count=a['count'], offset=start)


def meshes(js, bin_):
    out = {}
    for nd in js['nodes']:
        for k in ('translation', 'rotation', 'scale', 'matrix'):
            assert k not in nd, f'node {nd.get("name")} has {k}; script assumes identity TRS'
        if 'mesh' not in nd:
            continue
        tris = []
        for pr in js['meshes'][nd['mesh']]['primitives']:
            P = acc(js, bin_, pr['attributes']['POSITION']).astype(np.float64)
            I = acc(js, bin_, pr['indices']).reshape(-1, 3).astype(np.int64)
            tris.append(P[I])
        out[nd['name']] = np.concatenate(tris)
    return out


class Field:
    """bucketed vertical-ray caster over a triangle soup"""

    def __init__(self, T, cell=0.5):
        self.T = T
        A, B, C = T[:, 0], T[:, 1], T[:, 2]
        n = np.cross(B - A, C - A)
        self.ny = n[:, 1] / np.maximum(np.linalg.norm(n, axis=1), 1e-12)
        lo = T[:, :, [0, 2]].min(1); hi = T[:, :, [0, 2]].max(1)
        self.cell = cell
        self.o = lo.min(0) - cell
        self.buckets = {}
        for t in range(len(T)):
            i0, j0 = np.floor((lo[t] - self.o) / cell).astype(int)
            i1, j1 = np.floor((hi[t] - self.o) / cell).astype(int)
            for i in range(i0, i1 + 1):
                for j in range(j0, j1 + 1):
                    self.buckets.setdefault((i, j), []).append(t)
        self.buckets = {k: np.array(v) for k, v in self.buckets.items()}

    def hits(self, x, z):
        k = tuple(np.floor((np.array([x, z]) - self.o) / self.cell).astype(int))
        ids = self.buckets.get(k)
        if ids is None:
            return np.zeros(0), np.zeros(0)
        T = self.T[ids]
        a, b, c = T[:, 0], T[:, 1], T[:, 2]
        v0 = b[:, [0, 2]] - a[:, [0, 2]]; v1 = c[:, [0, 2]] - a[:, [0, 2]]; v2 = np.array([x, z]) - a[:, [0, 2]]
        den = v0[:, 0] * v1[:, 1] - v1[:, 0] * v0[:, 1]
        ok = np.abs(den) > 1e-12
        den = np.where(ok, den, 1)
        u = (v2[:, 0] * v1[:, 1] - v1[:, 0] * v2[:, 1]) / den
        v = (v0[:, 0] * v2[:, 1] - v2[:, 0] * v0[:, 1]) / den
        e = -1e-7
        m = ok & (u >= e) & (v >= e) & (u + v <= 1 - e)
        y = a[m, 1] + u[m] * (b[m, 1] - a[m, 1]) + v[m] * (c[m, 1] - a[m, 1])
        return y, self.ny[ids][m]


def support(F, x, z, ceil):
    """highest upward-facing hit at or below `ceil`; None = no support (void)"""
    y, ny = F.hits(x, z)
    s = y[(ny > 0.5) & (y <= ceil + 1e-6)]
    return float(s.max()) if len(s) else None


def clearance(F, x, z, ys, H):
    y, ny = F.hits(x, z)
    obs = y[(y > ys + 0.02) & (y < ys + H)]
    return float(obs.min() - ys) if len(obs) else None


SIDES = {'+X': (1, 0), '-X': (-1, 0), '+Z': (0, 1), '-Z': (0, -1)}


def analyse(path, H=2.0):
    js, bin_, sha, nbytes = load(path)
    M = meshes(js, bin_)
    allT = np.concatenate(list(M.values()))
    F = Field(allT)
    lo = allT.reshape(-1, 3).min(0); hi = allT.reshape(-1, 3).max(0)
    half = float(max(abs(lo[0]), hi[0], abs(lo[2]), hi[2]))
    # platform top: walkable height at centre-ish of each quadrant ray just inside the door
    up = allT[F.ny > 0.5]
    hy, cnt = np.unique(np.round(up[:, :, 1].mean(1), 3), return_counts=True)
    res = {'file': path.replace('\\', '/').split('/')[-1], 'sha256': sha, 'bytes': nbytes,
           'meshes': {k: {'tris': int(len(v)), 'bboxMin': v.reshape(-1, 3).min(0).round(4).tolist(),
                          'bboxMax': v.reshape(-1, 3).max(0).round(4).tolist()} for k, v in M.items()},
           'bboxMin': lo.round(4).tolist(), 'bboxMax': hi.round(4).tolist(), 'sides': {}}
    step = 0.02
    for name, (dx, dz) in SIDES.items():
        # centreline profile from r=0 to half+3m; ceiling = 1.2 m above previous support to stay under roofs
        prof = []
        prev = None
        for r in np.arange(0.0, half + 3.0 + 1e-9, step):
            x, z = dx * r, dz * r
            ceil = (prev + 0.6) if prev is not None else 3.0
            s = support(F, x, z, ceil)
            if s is None and prev is not None:
                s2 = support(F, x, z, 99)  # anything at all above? (record only)
            prof.append((round(float(r), 3), s))
            if s is not None:
                prev = s
        # segment profile into flat runs
        runs = []
        for r, s in prof:
            key = None if s is None else round(s, 3)
            if runs and runs[-1]['y'] == key:
                runs[-1]['r1'] = r
            else:
                runs.append({'y': key, 'r0': r, 'r1': r})
        # stair = runs between the last run whose y>=platform-ish and the first void
        last_support = max((r for r, s in prof if s is not None), default=None)
        foot_y = next((s for r, s in reversed(prof) if s is not None), None)
        # lateral width of each run at its midpoint
        def lateral(r, y0):
            ws = []
            for t in np.arange(-12, 12 + 1e-9, 0.02):
                x, z = dx * r - dz * t, dz * r + dx * t
                s = support(F, x, z, y0 + 0.05)
                ws.append(s is not None and abs(s - y0) < 0.03)
            ws = np.array(ws); ts = np.arange(-12, 12 + 1e-9, 0.02)
            # contiguous block containing t=0
            c = len(ts) // 2
            if not ws[c]:
                return None
            a = c
            while a > 0 and ws[a - 1]: a -= 1
            b = c
            while b < len(ws) - 1 and ws[b + 1]: b += 1
            return [round(float(ts[a]), 3), round(float(ts[b]), 3)]
        for rr in runs:
            if rr['y'] is not None:
                rr['lateral'] = lateral((rr['r0'] + rr['r1']) / 2, rr['y'])
                rr['depth'] = round(rr['r1'] - rr['r0'] + step, 3)
                rr['clear_at_mid'] = clearance(F, dx * (rr['r0'] + rr['r1']) / 2, dz * (rr['r0'] + rr['r1']) / 2, rr['y'], H)
        # apron probe: band outside the last support point, 0..3 m outward, across +-6 m
        apron = {'probes': 0, 'supported': 0, 'max_supported_out_m': None}
        if last_support is not None:
            pts = 0; sup = 0
            for o in np.arange(0.05, 3.0 + 1e-9, 0.1):
                for t in np.arange(-6, 6 + 1e-9, 0.25):
                    r = last_support + o
                    x, z = dx * r - dz * t, dz * r + dx * t
                    pts += 1
                    if support(F, x, z, 0.5) is not None:
                        sup += 1
            apron = {'probes': pts, 'supported': sup, 'band': 'r in (foot, foot+3m], lateral +-6 m, ceiling y<=0.5'}
        risers = []
        ys = [rr for rr in runs if rr['y'] is not None]
        for a_, b_ in zip(ys, ys[1:]):
            risers.append({'at_r': b_['r0'], 'from_y': a_['y'], 'to_y': b_['y'], 'rise': round(b_['y'] - a_['y'], 3)})
        # min clearance along the whole centreline (door headers etc.)
        cl = []
        for r, sy in prof:
            if sy is None: continue
            c = clearance(F, dx * r, dz * r, sy, H)
            if c is not None: cl.append((r, round(c, 3)))
        # cheek / side-obstruction check on every tread: walkable/blocking faces higher than the tread
        # in the 0.9 m band just outside the tread's lateral edge
        cheeks = []
        for rr in runs:
            if rr['y'] is None or rr.get('lateral') is None or rr['depth'] > 2: continue
            rm = (rr['r0'] + rr['r1']) / 2
            for sgn in (-1, 1):
                edge = rr['lateral'][1] if sgn > 0 else rr['lateral'][0]
                hs = []
                for t in np.arange(0.04, 0.9, 0.04):
                    x, z = dx * rm - dz * (edge + sgn * t), dz * rm + dx * (edge + sgn * t)
                    y, ny = F.hits(x, z)
                    hs.append(float(y.max()) if len(y) else None)
                cheeks.append({'tread_y': rr['y'], 'side': sgn, 'outside_heights_max': max([h for h in hs if h is not None], default=None),
                               'outside_void_fraction': round(sum(h is None for h in hs) / len(hs), 3)})
        res['sides'][name] = {'runs': runs, 'centreline_clearance_lt_H': cl[:50], 'centreline_min_clearance': (min(cl, key=lambda a: a[1]) if cl else None), 'cheeks': cheeks, 'risers': risers, 'last_support_r': last_support, 'foot_y': foot_y,
                              'void_from_r': (round(last_support + step, 3) if last_support is not None else None),
                              'apron': apron}
    # perimeter probe at y<=0.5: ground ring outside the bbox?
    ring = 0; ringsup = 0
    for t in np.arange(-half - 2, half + 2 + 1e-9, 0.5):
        for x, z in ((half + 1, t), (-half - 1, t), (t, half + 1), (t, -half - 1)):
            ring += 1
            if support(F, x, z, 0.5) is not None:
                ringsup += 1
    res['outside_ring_1m'] = {'probes': ring, 'supported': ringsup}
    # platform extent along each axis direction measured on the diagonal-free line t=half/2 (off the stair)
    plat = {}
    for name, (dx, dz) in SIDES.items():
        t = 6.0
        last = None
        for r in np.arange(0, half + 0.5, 0.01):
            x, z = dx * r - dz * t, dz * r + dx * t
            s_ = support(F, x, z, 3.0)
            if s_ is not None: last = (round(float(r), 3), round(s_, 3))
        plat[name] = {'offaxis_t_m': t, 'last_support': last}
    res['platform_edge_offaxis'] = plat
    # base faces at y=0
    dn = allT[(F.ny < -0.5) & (np.abs(allT[:, :, 1]).max(1) < 1e-4)]
    res['y0_downward_faces'] = {'count': int(len(dn)), 'area_m2': float(np.linalg.norm(np.cross(dn[:, 1] - dn[:, 0], dn[:, 2] - dn[:, 0]), axis=1).sum() / 2) if len(dn) else 0.0}
    # exact stair vertex data (+X side): distinct tread heights and nosing positions from upward faces in the stair band
    band = up[(up[:, :, 0].min(1) > half - 4.0) & (np.abs(up[:, :, 2]).max(1) < 3.0)]
    res['stair_plusX_vertices'] = sorted({(round(float(v[1]), 4), round(float(v[0]), 4)) for tri in band for v in tri})
    # where is y=0 support at all? (footprint of ground-level walkable faces)
    g = up[np.abs(up[:, :, 1]).max(1) < 1e-4]
    res['y0_walkable_faces'] = {'count': int(len(g)),
                                'xzMin': (g.reshape(-1, 3).min(0)[[0, 2]].round(4).tolist() if len(g) else None),
                                'xzMax': (g.reshape(-1, 3).max(0)[[0, 2]].round(4).tolist() if len(g) else None),
                                'area_m2': float(np.linalg.norm(np.cross(g[:, 1] - g[:, 0], g[:, 2] - g[:, 0]), axis=1).sum() / 2) if len(g) else 0.0}
    return res


if __name__ == '__main__':
    out = [analyse(p) for p in sys.argv[2:]]
    json.dump(out, open(sys.argv[1], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for r in out:
        print('=====', r['file'], r['sha256'][:12], r['bboxMin'], r['bboxMax'])
        print('  y0 walkable faces', r['y0_walkable_faces'], ' outside ring', r['outside_ring_1m'])
        for s, d in r['sides'].items():
            print(f"  {s}: foot_y {d['foot_y']} last_support_r {d['last_support_r']} apron {d['apron'].get('supported')}/{d['apron'].get('probes')}")
            print('     min centreline clearance <H:', d['centreline_min_clearance'])
            print('     treads:', [(rr['y'], rr['r0'], rr.get('depth'), rr.get('lateral')) for rr in d['runs']])
            print('     cheeks:', d['cheeks'][:4])
        print('  platform edge', r['platform_edge_offaxis'])
        print('  y0 down faces', r['y0_downward_faces'])
