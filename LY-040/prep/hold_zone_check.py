# LY-040 prep: read-only check of the region's real GLB footprints against LY-003 frozen tables
# (hold zones, NE-C-SCREEN 5 m cells, city wall B polygon). numpy only; never writes next to inputs.
# Usage:
#   python -I hold_zone_check.py <out.json> <evidence-geometry.json> <LY-003 dir> <label=glb> [<label=glb> ...]
# Plan coordinates: native X east, Y north  (= glTF x, -z).
# Footprint = every triangle edge of every mesh node, sampled every 0.5 m (plus vertices).
# Distances are to the frozen base geometry of each hold zone; margin = distance - buffer_m (negative = inside zone).
# Negative controls (built in): a probe point placed 1 m inside HZ-Y must report margin < 0, and a probe
# point outside the city wall polygon must report outside; if either fails the script exits 1.
import sys, os, json, hashlib
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbinspect as gi

out_path, ev_path, ly003 = sys.argv[1], sys.argv[2], sys.argv[3]
inputs = [a.split('=', 1) for a in sys.argv[4:]]


def sha(p):
    return gi.sha256(p)


ev = json.load(open(ev_path, encoding='utf-8'))
feat = {f.get('id'): f for f in ev['features']}
hz = json.load(open(os.path.join(ly003, 'tables', 'hold-zones.json'), encoding='utf-8'))
cells = json.load(open(os.path.join(ly003, 'tables', 'ne-screening-cells.json'), encoding='utf-8'))
step = cells['step_m']
cell_set = set((round(x, 1), round(y, 1)) for x, y in cells['cell_centers_xy'])
cx0, cy0 = cells['cell_centers_xy'][0]


def seg_dist(P, a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    ab = b - a; L2 = float(ab @ ab)
    t = np.clip(((P - a) @ ab) / L2, 0, 1) if L2 > 0 else np.zeros(len(P))
    Q = a + t[:, None] * ab
    return np.linalg.norm(P - Q, axis=1)


def in_poly(P, ring):
    x, y = P[:, 0], P[:, 1]; inside = np.zeros(len(P), bool)
    for i in range(len(ring) - 1):
        x1, y1 = ring[i]; x2, y2 = ring[i + 1]
        c = ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-300) + x1)
        inside ^= c
    return inside


def dist_geom(P, g):
    t = g['type']; c = g['coordinates']
    if t == 'Point':
        return np.linalg.norm(P - np.asarray(c, float), axis=1)
    if t == 'LineString':
        return np.min([seg_dist(P, c[i], c[i + 1]) for i in range(len(c) - 1)], axis=0)
    if t == 'Polygon':
        ring = c[0]
        d = np.min([seg_dist(P, ring[i], ring[i + 1]) for i in range(len(ring) - 1)], axis=0)
        d[in_poly(P, ring)] = 0.0
        return d
    if t == 'MultiLineString':
        return np.min([dist_geom(P, {'type': 'LineString', 'coordinates': l}) for l in c], axis=0)
    raise ValueError(t)


def cell_of(P):
    i = np.round((P[:, 0] - cx0) / step); j = np.round((P[:, 1] - cy0) / step)
    return [(round(cx0 + a * step, 1), round(cy0 + b * step, 1)) for a, b in zip(i, j)]


def footprint(path):
    js, binc = gi.load(path)
    objs = {}
    for i, n, W, p_ in gi.walk(js):
        if 'mesh' not in n:
            continue
        pts = []
        for pr in js['meshes'][n['mesh']]['primitives']:
            pos = gi.acc(js, binc, pr['attributes']['POSITION']).astype(float)
            wp = (W[:3, :3] @ pos.T).T + W[:3, 3]
            idx = gi.acc(js, binc, pr['indices']).reshape(-1).astype(np.int64) if 'indices' in pr else np.arange(len(pos))
            t = wp[idx].reshape(-1, 3, 3)
            plan = np.stack([t[..., 0], -t[..., 2]], -1)  # (n,3,2)
            for a, b in ((0, 1), (1, 2), (2, 0)):
                A = plan[:, a]; B = plan[:, b]
                L = np.linalg.norm(B - A, axis=1)
                k = np.maximum(1, np.ceil(L / 0.5)).astype(int)
                for kk in np.unique(k):
                    m = k == kk
                    s = np.linspace(0, 1, kk + 1)
                    pts.append((A[m][:, None, :] + s[None, :, None] * (B[m] - A[m])[:, None, :]).reshape(-1, 2))
        P = np.unique(np.round(np.concatenate(pts), 3), axis=0)
        objs[n.get('name', 'node%d' % i)] = P
    return objs


wall = feat['city_wall_schematic_B']['geometry']
res = {'tool': 'hold_zone_check.py', 'evidence_geometry_sha256': sha(ev_path),
       'ly003_tables_sha256': {k: sha(os.path.join(ly003, 'tables', k)) for k in ('hold-zones.json', 'ne-screening-cells.json', 'admission.json')},
       'footprint_rule': 'triangle edges sampled every 0.5 m, plan (x east, y north)', 'files': {}, 'zones': {}}
allP = {}
for label, path in inputs:
    objs = footprint(path)
    res['files'][label] = {'path': path, 'sha256': sha(path), 'objects': {k: int(len(v)) for k, v in objs.items()}}
    for k, v in objs.items():
        allP[label + ':' + k] = v

for z in hz['zones']:
    g = feat[z['base']]['geometry']
    row = {'base': z['base'], 'buffer_m': z['buffer_m'], 'per_object_margin_m': {}}
    for k, P in allP.items():
        d = dist_geom(P, g)
        j = int(np.argmin(d))
        row['per_object_margin_m'][k] = {'dist_m': round(float(d[j]), 2), 'margin_m': round(float(d[j] - z['buffer_m']), 2),
                                        'at_xy': [round(float(P[j, 0]), 3), round(float(P[j, 1]), 3)]}
    row['min_margin_m'] = min(v['margin_m'] for v in row['per_object_margin_m'].values())
    row['inside_zone'] = row['min_margin_m'] < 0
    res['zones'][z['id']] = row

res['city_wall_B'] = {}
res['ne_c_screen'] = {}
for k, P in allP.items():
    inside = in_poly(P, wall['coordinates'][0])
    dw = dist_geom(P, {'type': 'LineString', 'coordinates': wall['coordinates'][0]})
    res['city_wall_B'][k] = {'all_inside': bool(inside.all()), 'min_dist_to_wall_line_m': round(float(dw.min()), 2)}
    cs = cell_of(P)
    hit = np.array([c in cell_set for c in cs])
    res['ne_c_screen'][k] = {'points': int(len(P)), 'in_screen_cells': int(hit.sum()), 'share': round(float(hit.mean()), 4)}

# negative controls
neg = {}
yz = next(z for z in hz['zones'] if z['id'] == 'HZ-Y')
c = np.asarray(feat[yz['base']]['geometry']['coordinates'], float)
probe = np.array([[c[0], c[1] + yz['buffer_m'] - 1.0]])
m = float(dist_geom(probe, feat[yz['base']]['geometry'])[0] - yz['buffer_m'])
neg['probe_1m_inside_HZ-Y_margin_m'] = round(m, 3)
neg['probe_1m_inside_HZ-Y_detected'] = m < 0
out_probe = np.array([[2600.0, 3800.0]])
neg['probe_outside_wall_detected'] = not bool(in_poly(out_probe, wall['coordinates'][0])[0])
res['negative_controls'] = neg

os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
json.dump(res, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
summary = {z: (r['min_margin_m'], r['inside_zone']) for z, r in res['zones'].items()}
print('ZONES', summary)
print('WALL', {k: v['all_inside'] for k, v in res['city_wall_B'].items()})
print('SCREEN', {k: v['share'] for k, v in res['ne_c_screen'].items()})
print('NEG', neg)
if not (neg['probe_1m_inside_HZ-Y_detected'] and neg['probe_outside_wall_detected']):
    sys.exit(1)
