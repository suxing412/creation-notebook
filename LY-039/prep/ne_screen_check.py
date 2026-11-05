# LY-039 prep: recheck the measured road footprint against LY-003's NE-C-SCREEN rule
# and hold zones (LY-003 asked LY-039 to do this once the real GLB is known).
# Footprint = the L strip measured from northeast_C_access.glb (glb_raw_check.py):
#   north leg x[2284.2141,2287.2141] y[3484.5,3647.469]; east leg x[2284.2141,2317.8269]
#   y[3484.5,3487.5]; stub x[2314.8269,2317.8269] y[3487.5,3490.0]. Sampled every 0.25 m.
# python -I ne_screen_check.py <evidence-geometry.json> <LY-003/tables/hold-zones.json> <out.json>
import sys, json, math
ev, hz, outp = sys.argv[1:4]
F = {f['id']: f for f in json.load(open(ev, encoding='utf-8'))['features']}
Z = json.load(open(hz, encoding='utf-8'))['zones']
rects = [(2284.2141, 2287.2141, 3484.5, 3647.469), (2284.2141, 2317.8269, 3484.5, 3487.5), (2314.8269, 2317.8269, 3487.5, 3490.0)]
pts = set()
for x0, x1, y0, y1 in rects:
    nx, ny = int(round((x1 - x0) / 0.25)), int(round((y1 - y0) / 0.25))
    for i in range(nx + 1):
        for j in range(ny + 1):
            pts.add((round(x0 + (x1 - x0) * i / nx, 4), round(y0 + (y1 - y0) * j / ny, 4)))
pts = sorted(pts)
def seg_d(p, a, b):
    ax, ay = a; bx, by = b; dx, dy = bx - ax, by - ay
    t = max(0, min(1, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy or 1)))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)
def inside(p, ring):
    c = False
    for k in range(len(ring) - 1):
        (x1, y1), (x2, y2) = ring[k], ring[k + 1]
        if (y1 > p[1]) != (y2 > p[1]) and p[0] < x1 + (p[1] - y1) * (x2 - x1) / (y2 - y1): c = not c
    return c
def dist(p, g):
    t, c = g['type'], g['coordinates']
    if t == 'Point': return math.hypot(p[0] - c[0], p[1] - c[1])
    if t == 'LineString': return min(seg_d(p, c[k], c[k + 1]) for k in range(len(c) - 1))
    if t == 'Polygon':
        r = c[0]
        return 0.0 if inside(p, r) else min(seg_d(p, r[k], r[k + 1]) for k in range(len(r) - 1))
    raise ValueError(t)
NP = F['north_palace_extent_gao2023_B']['geometry']['coordinates'][0]
NPx_max, NPy_min = max(v[0] for v in NP), min(v[1] for v in NP)
W = F['city_wall_schematic_B']['geometry']['coordinates'][0]
res = {'samples': len(pts), 'rule': 'inside city_wall_schematic_B, x >= %.3f, y >= %.3f, outside all LY-003 hold zones' % (NPx_max, NPy_min)}
res['inside_city_wall_B'] = sum(inside(p, W) for p in pts)
res['min_dist_to_city_wall_line_m'] = round(min(min(seg_d(p, W[k], W[k + 1]) for k in range(len(W) - 1)) for p in pts), 2)
res['x_ge_np_east'] = sum(p[0] >= NPx_max for p in pts)
res['y_ge_np_south'] = sum(p[1] >= NPy_min for p in pts)
zr = []
for z in Z:
    d = min(dist(p, F[z['base']]['geometry']) for p in pts)
    zr.append({'zone': z['id'], 'base': z['base'], 'buffer_m': z['buffer_m'], 'min_dist_to_base_m': round(d, 2), 'margin_m': round(d - z['buffer_m'], 2), 'inside_zone': d <= z['buffer_m']})
res['hold_zones'] = zr
res['samples_in_NE_C_SCREEN'] = sum(1 for p in pts if inside(p, W) and p[0] >= NPx_max and p[1] >= NPy_min and all(dist(p, F[z['base']]['geometry']) > z['buffer_m'] for z in Z))
res['all_in_NE_C_SCREEN'] = res['samples_in_NE_C_SCREEN'] == len(pts)
for k in ('region_taicang_B', 'region_wuku_B', 'north_palace_extent_gao2023_B', 'region_yongan_B', 'road_east_north_link_B'):
    res['min_dist_%s_m' % k] = round(min(dist(p, F[k]['geometry']) for p in pts), 2)
res['meaning'] = 'C screening only (LY-003 NE-C-SCREEN). Not proof of being outside the palace, not historical location, not city admission.'
json.dump(res, open(outp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
