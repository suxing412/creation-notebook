# LY-084 prep: screen R1/R2/R3 (out/routes.json) against LY-003 delivered constraints.
# Read-only. Inputs:
#   lab repo (git show <commit>:evidence-geometry.json, no worktree reads),
#   LY-003/tables/hold-zones.json, LY-003/tables/ne-screening-cells.json, LY-003/tables/admission.json,
#   LY-084/prep/out/routes.json (polyline_to_contact per candidate).
# Output: one JSON report (stdout or path). No geometry is produced.
# usage: python -I ly003_screen.py <lab> <commit> <LY-003 dir> <routes.json> <out.json>
import hashlib, json, math, subprocess, sys

LAB, COMMIT, L3, ROUTES, OUT = sys.argv[1:6]
EV_PATH = 'docs/cities/luoyang/data/evidence/evidence-geometry.json'
STEP = 1.0


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    with open(p, 'rb') as f:
        return sha_bytes(f.read())


ev_bytes = subprocess.run(['git', '-C', LAB, 'show', f'{COMMIT}:{EV_PATH}'],
                          capture_output=True, check=True).stdout
ev = json.loads(ev_bytes.decode('utf-8'))
F = {f['id']: f for f in ev['features']}
hz = json.load(open(f'{L3}/tables/hold-zones.json', encoding='utf-8'))
cells = json.load(open(f'{L3}/tables/ne-screening-cells.json', encoding='utf-8'))
routes = json.load(open(ROUTES, encoding='utf-8'))


def seg_dist(p, a, b):
    (ax, ay), (bx, by), (px, py) = a, b, p
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def inside(p, ring):
    x, y = p; c = False
    for i in range(len(ring) - 1):
        (x1, y1), (x2, y2) = ring[i], ring[i + 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def dist_to(fid, p):
    g = F[fid]['geometry']
    if g is None:
        return None
    t, c = g['type'], g['coordinates']
    if t == 'Point':
        return math.hypot(p[0] - c[0], p[1] - c[1])
    if t == 'LineString':
        return min(seg_dist(p, c[i], c[i + 1]) for i in range(len(c) - 1))
    if t == 'Polygon':
        ring = c[0]
        if inside(p, ring):
            return 0.0
        return min(seg_dist(p, ring[i], ring[i + 1]) for i in range(len(ring) - 1))
    raise ValueError(t)


# NE-C-SCREEN membership: point lies in a 5 m cell whose centre is listed.
cellset = {(round(x, 1), round(y, 1)) for x, y in cells['cell_centers_xy']}
cx0, cy0 = cells['cell_centers_xy'][0]
cstep = cells['step_m']


def in_screen(p):
    i = math.floor((p[0] - (cx0 - cstep / 2)) / cstep)
    j = math.floor((p[1] - (cy0 - cstep / 2)) / cstep)
    key = (round(cx0 + i * cstep, 1), round(cy0 + j * cstep, 1))
    return key in cellset


def stations(pts):
    out = []
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(math.ceil(L / STEP)))
        for k in range(n):
            t = (k + 0.5) / n
            out.append(((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])), L / n))
    return out


def runs(flags):
    best = cur = 0.0
    for f, w in flags:
        cur = cur + w if f else 0.0
        best = max(best, cur)
    return best


def screen(pts):
    st = stations(pts)
    total = sum(w for _, w in st)
    zones = {}
    any_zone = []
    for z in hz['zones']:
        d = [(dist_to(z['base'], p), w, p) for p, w in st]
        inz = [(dd <= z['buffer_m'], w) for dd, w, _ in d]
        L_in = sum(w for f, w in inz if f)
        ys = [p[1] for (dd, w, p) in d if dd <= z['buffer_m']]
        zones[z['id']] = {'base': z['base'], 'buffer_m': z['buffer_m'],
                          'min_dist_to_base_m': round(min(x[0] for x in d), 2),
                          'length_inside_m': round(L_in, 1),
                          'longest_inside_run_m': round(runs(inz), 1),
                          'y_range_inside': [round(min(ys), 1), round(max(ys), 1)] if ys else None}
    for p, w in st:
        hit = any(dist_to(z['base'], p) <= z['buffer_m'] for z in hz['zones'])
        any_zone.append((hit, w))
    scr = [(in_screen(p), w) for p, w in st]
    L_any = sum(w for f, w in any_zone if f)
    L_scr = sum(w for f, w in scr if f)
    return {'length_m': round(total, 1),
            'inside_any_hold_zone_m': round(L_any, 1),
            'inside_any_hold_zone_share': round(L_any / total, 4),
            'inside_NE_C_SCREEN_m': round(L_scr, 1),
            'outside_NE_C_SCREEN_m': round(total - L_scr, 1),
            'outside_NE_C_SCREEN_share': round((total - L_scr) / total, 4),
            'zones': zones}


rep = {'what': 'LY-084 prep screen of reconstructed R1-R3 against LY-003 hold zones and NE-C-SCREEN',
       'not': 'outside a hold zone is not proof of being outside the palace (LY-003: e3/e4 unquantified); '
              'this is plan-only 2D screening, not support, collision, structure or history',
       'inputs': {'evidence_geometry_commit_blob': {'commit': COMMIT, 'path': EV_PATH, 'sha256': sha_bytes(ev_bytes)},
                  'LY-003/tables/hold-zones.json': sha_file(f'{L3}/tables/hold-zones.json'),
                  'LY-003/tables/ne-screening-cells.json': sha_file(f'{L3}/tables/ne-screening-cells.json'),
                  'LY-003/tables/admission.json': sha_file(f'{L3}/tables/admission.json'),
                  'LY-003/qa/ne-checks.json': sha_file(f'{L3}/qa/ne-checks.json'),
                  'routes.json': sha_file(ROUTES)},
       'step_m': STEP, 'candidates': {}, 'selftest': {}}

for cid, c in routes['candidates'].items():
    rep['candidates'][cid] = screen(c['polyline_to_contact'])

# Self-tests: must come out as expected or the screen is invalid.
yong = F['region_yongan_B']['geometry']['coordinates']
tests = {
    # granary hull bbox centre: LY-003 says inside NE-C-SCREEN and outside all zones
    'POS_granary_centre_in_screen': (in_screen((2285.7, 3673.5)), True),
    'POS_granary_centre_outside_zones': (all(dist_to(z['base'], (2285.7, 3673.5)) > z['buffer_m'] for z in hz['zones']), True),
    'NEG_yongan_label_in_HZ_Y': (dist_to('region_yongan_B', tuple(yong)) <= 400, True),
    'NEG_yongan_label_not_in_screen': (in_screen(tuple(yong)), False),
    'NEG_north_palace_inside_point_dist0': (dist_to('north_palace_extent_gao2023_B', (1100.0, 2800.0)) == 0.0, True),
    'NEG_south_of_y2051_not_in_screen': (in_screen((2316.3, 2000.0)), False),
}
for k, (got, want) in tests.items():
    rep['selftest'][k] = {'got': got, 'want': want, 'ok': got == want}
rep['selftest_all_ok'] = all(v['ok'] for v in rep['selftest'].values())

txt = json.dumps(rep, ensure_ascii=False, indent=1)
open(OUT, 'w', encoding='utf-8', newline='\n').write(txt)
print(txt)
sys.exit(0 if rep['selftest_all_ok'] else 1)
