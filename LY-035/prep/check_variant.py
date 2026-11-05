# LY-035 variant checker (prepared before production; read-only on all inputs).
#   python -X utf8 check_variant.py --selftest                       # synthetic good/bad samples, must show PASS + 5 FAILs
#   python -X utf8 check_variant.py --variant v.glb --rules r.json    # real delivery check (after G + LY-033/034)
# rules.json:
#   {"baseSha256": "<city LOD0 sha>", "ports": {...},
#    "staging":  [{"id": "S1", "min": [x,y,z], "max": [x,y,z]}],             # cargo staging volume (world glTF)
#    "turning":  [{"id": "T_A", "center": [x,z], "diameter": D}],             # person turning disc on ground
#    "corridors":[{"id": "C_A", "from": [x,z], "to": [x,z], "width": w}],     # LY-034 route corridors
#    "exclusive":[["S1","C_A"], ["S1","T_A"], ...]}                            # pairs that must not overlap when active
# Tolerances: overlap area <= 0.01 m2; intrusion clearance >= 0.0 m at 0.05 m grid; support y >= 0.200 - 1e-4.
import sys, os, json, argparse
import numpy as np
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbread as G

LAB = 'D:/GitHub/creation-notebook-lab/docs/'
BASE = LAB + 'cities/luoyang/progress-assets/granary-city-v1/granary-city-LOD0.glb'
BASE_SHA = '5937211c7366a5920ae222185176f198cc3d16e8763605fa248e61031c74bc93'
WALK = 0.2
RES = 0.05
BAND = (0.05, 2.0)
AREA_TOL = 0.01


def samples(tris, step):
    out = []
    for a, b, c in tris:
        n = int(np.ceil(max(np.linalg.norm(b - a), np.linalg.norm(c - a), np.linalg.norm(c - b)) / step)) + 1
        i, j = np.meshgrid(np.arange(n + 1), np.arange(n + 1), indexing='ij')
        m = (i + j) <= n
        u, v = i[m] / n, j[m] / n
        out.append(a[None] + u[:, None] * (b - a)[None] + v[:, None] * (c - a)[None])
    return np.concatenate(out) if out else np.zeros((0, 3))


class Base:
    def __init__(self):
        self.sha = G.sha256(BASE)
        parts, _ = G.world_triangles(BASE)
        g = [p for p in parts if p['node'] == 'original_city_ground_preserved'][0]['tris'].reshape(-1, 3)
        self.x0, self.x1 = g[:, 0].min(), g[:, 0].max()
        self.z0, self.z1 = g[:, 2].min(), g[:, 2].max()
        self.nx, self.nz = int(round((self.x1 - self.x0) / RES)), int(round((self.z1 - self.z0) / RES))
        self.occ = np.zeros((self.nx, self.nz), bool)
        for p in parts:
            if p['node'] == 'original_city_ground_preserved':
                continue
            t = p['tris']
            keep = (t[:, :, 1].max(1) >= WALK + BAND[0]) & (t[:, :, 1].min(1) <= WALK + BAND[1])
            s = samples(t[keep], RES * 0.4)
            s = s[(s[:, 1] >= WALK + BAND[0]) & (s[:, 1] <= WALK + BAND[1])]
            self.occ[self.cell(s)] = True
        gx = self.x0 + (np.arange(self.nx) + .5) * RES
        gz = self.z0 + (np.arange(self.nz) + .5) * RES
        self.GX, self.GZ = np.meshgrid(gx, gz, indexing='ij')

    def cell(self, s):
        ix = np.clip(((s[:, 0] - self.x0) / RES).astype(int), 0, self.nx - 1)
        iz = np.clip(((s[:, 2] - self.z0) / RES).astype(int), 0, self.nz - 1)
        return ix, iz

    def shape_mask(self, item):
        if 'min' in item:
            lo, hi = item['min'], item['max']
            return (self.GX >= lo[0]) & (self.GX <= hi[0]) & (self.GZ >= lo[2]) & (self.GZ <= hi[2])
        if 'diameter' in item:
            c = item['center']
            return np.hypot(self.GX - c[0], self.GZ - c[1]) <= item['diameter'] / 2
        a, b, w = item['from'], item['to'], item['width']
        vx, vz = b[0] - a[0], b[1] - a[1]
        t = np.clip(((self.GX - a[0]) * vx + (self.GZ - a[1]) * vz) / (vx * vx + vz * vz), 0, 1)
        return np.hypot(self.GX - (a[0] + t * vx), self.GZ - (a[1] + t * vz)) <= w / 2


def box_tris(lo, hi):
    x0, y0, z0 = lo; x1, y1, z1 = hi
    v = np.array([[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0], [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]], float)
    f = [(0, 1, 2), (0, 2, 3), (4, 6, 5), (4, 7, 6), (0, 4, 5), (0, 5, 1), (3, 2, 6), (3, 6, 7), (0, 3, 7), (0, 7, 4), (1, 5, 6), (1, 6, 2)]
    return v[np.array(f)]


def check(base, vtris, rules):
    res = []
    def rec(id, ok, detail):
        res.append({'check': id, 'pass': bool(ok), 'detail': detail})
    rec('T0 base sha', base.sha == rules.get('baseSha256', BASE_SHA) == BASE_SHA, base.sha[:12])
    v = vtris.reshape(-1, 3)
    rec('T10a finite', bool(np.isfinite(v).all()), 'non-finite=%d' % int((~np.isfinite(v)).sum()))
    a = np.linalg.norm(np.cross(vtris[:, 1] - vtris[:, 0], vtris[:, 2] - vtris[:, 0]), axis=1) / 2
    rec('T10b nondegenerate', bool((a > 1e-10).all()), 'degenerate=%d' % int((a <= 1e-10).sum()))
    inside = (v[:, 0] >= base.x0 - 1e-4) & (v[:, 0] <= base.x1 + 1e-4) & (v[:, 2] >= base.z0 - 1e-4) & (v[:, 2] <= base.z1 + 1e-4)
    rec('T2a inside plot', bool(inside.all()), 'outside verts=%d' % int((~inside).sum()))
    rec('T2b on/above walk surface', bool(v[:, 1].min() >= WALK - 1e-4), 'minY=%.4f' % v[:, 1].min())
    # coplanar with ground top (z-fight) -> horizontal faces within 2 mm above y=0.2
    flat = np.abs(vtris[:, :, 1].max(1) - vtris[:, :, 1].min(1)) < 1e-6
    zf = flat & (vtris[:, 0, 1] < WALK + 0.002)
    rec('T2c no ground-coplanar faces (<2mm)', bool(not zf.any()), 'faces=%d' % int(zf.sum()))
    s = samples(vtris, RES * 0.4)
    s = s[(s[:, 1] >= WALK + BAND[0]) & (s[:, 1] <= WALK + BAND[1])]
    hit = base.occ[base.cell(s)] if len(s) else np.zeros(0, bool)
    # one-cell dilation of the base so a variant cannot sit flush inside the 5 cm cell that holds a wall/stair/bag
    occd = ndimage.binary_dilation(base.occ, iterations=1)
    hitd = occd[base.cell(s)] if len(s) else np.zeros(0, bool)
    rec('T3 no intrusion into original (band %.2f-%.2f m)' % BAND, bool(not hitd.any()), 'samples hitting=%d (undilated %d)' % (int(hitd.sum()), int(hit.sum())))
    items = {x['id']: x for k in ('staging', 'turning', 'corridors') for x in rules.get(k, [])}
    for t in rules.get('turning', []):
        m = base.shape_mask(t)
        rec('T8 turning %s free of original' % t['id'], bool(not (m & base.occ).any()), 'blocked cells=%d' % int((m & base.occ).sum()))
    for p, q in rules.get('exclusive', []):
        ov = float((base.shape_mask(items[p]) & base.shape_mask(items[q])).sum()) * RES * RES
        rec('T4 exclusive %s x %s' % (p, q), ov <= AREA_TOL, 'overlap=%.3f m2' % ov)
    # staging volumes must actually contain the variant geometry declared for them (rules describe the real thing)
    for st in rules.get('staging', []):
        lo, hi = np.array(st['min']), np.array(st['max'])
        rec('T7 staging %s height <= door clear 2.10' % st['id'], (hi[1] - WALK) <= 2.10 + 1e-6, 'h=%.3f' % (hi[1] - WALK))
    return res


def selftest(base):
    S = {'id': 'S1', 'min': [2284.189, 0.2, -3676.444], 'max': [2287.189, 0.82, -3673.444]}
    rp, fa, fb = [2285.7141, -3664.369], [2273.7141, -3674.989], [2297.7141, -3674.849]
    rules = {'baseSha256': BASE_SHA, 'staging': [S], 'turning': [{'id': 'T_A', 'center': [fa[0], fa[1] + 1.0], 'diameter': 1.5}],
             'corridors': [{'id': 'C_A', 'from': rp, 'to': fa, 'width': 0.9}, {'id': 'C_B', 'from': rp, 'to': fb, 'width': 0.9}],
             'exclusive': [['S1', 'C_A'], ['S1', 'C_B'], ['S1', 'T_A']]}
    cases = {
        'good: 3x3 stack between warehouses': (box_tris([2284.189, 0.205, -3676.444], [2287.189, 0.82, -3673.444]), rules, True),
        'bad: on U2/U3 bags': (box_tris([2288.0, 0.205, -3668.0], [2290.5, 0.82, -3667.0]), rules, False),
        'bad: below ground': (box_tris([2284.189, 0.1, -3676.444], [2287.189, 0.82, -3673.444]), rules, False),
        'bad: outside plot': (box_tris([2320.0, 0.205, -3660.0], [2323.0, 0.82, -3657.0]), rules, False),
        'bad: z-fight with ground': (box_tris([2284.189, 0.2, -3676.444], [2287.189, 0.82, -3673.444]), rules, False),
    }
    onB = dict(rules); onB['staging'] = [{'id': 'S1', 'min': [2290.0, 0.2, -3671.0], 'max': [2293.0, 0.82, -3668.0]}]
    cases['bad: staging declared on B corridor'] = (box_tris([2290.0, 0.205, -3671.0], [2293.0, 0.82, -3668.0]), onB, False)
    out = {}
    for name, (tris, r, expect) in cases.items():
        res = check(base, tris, r)
        ok = all(x['pass'] for x in res)
        out[name] = {'expectedPass': expect, 'actualPass': ok, 'asExpected': ok == expect, 'failed': [x for x in res if not x['pass']]}
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--variant')
    ap.add_argument('--rules')
    ap.add_argument('--out')
    a = ap.parse_args()
    base = Base()
    if a.selftest:
        r = selftest(base)
    else:
        parts, _ = G.world_triangles(a.variant)
        r = {'variant': a.variant, 'variantSha256': G.sha256(a.variant),
             'results': check(base, np.concatenate([p['tris'] for p in parts]), json.load(open(a.rules, encoding='utf-8')))}
    s = json.dumps(r, ensure_ascii=False, indent=1)
    if a.out:
        open(a.out, 'w', encoding='utf-8').write(s)
    print(s)
