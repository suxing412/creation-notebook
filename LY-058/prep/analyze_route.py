# LY-058 prep: route / zone analysis on a measure_yard.py grid (pure numpy, read-only).
# usage: python analyze_route.py <grid.npz> <out.json> [step_max ...]
# Zones below are C working hypotheses in the workyard LOCAL glTF frame; they are probes, not a design.
import sys, json, math, heapq
import numpy as np
from collections import deque

d = np.load(sys.argv[1]); OUT = sys.argv[2]
STEPS = [float(s) for s in sys.argv[3:]] or [0.20, 0.25]
xs, zs = d['xs'], d['zs']; NX, NZ = len(xs), len(zs); S = float(xs[1] - xs[0])
blocked, walk, sky, fp, hf = d['blocked'], d['walk'], d['sky'], d['inside_fp'], d['has_floor']
EXT = float(np.nanmin(d['floor'])) if False else 0.2
ground = np.where(hf, d['floor'], 0.19999992847442627)

def cell(x, z): return int(round((x - xs[0]) / S)), int(round((z - zs[0]) / S))
def xz(c): return round(float(xs[c[0]]), 3), round(float(zs[c[1]]), 3)

# distance (m) from each cell to nearest blocked cell (brute force BFS on 8-neighbourhood, chamfer)
INF = 1e9
dist = np.full((NX, NZ), INF); pq = []
for i in range(NX):
    for j in range(NZ):
        if blocked[i, j]: dist[i, j] = 0; pq.append((0.0, i, j))
heapq.heapify(pq)
while pq:
    dv, i, j = heapq.heappop(pq)
    if dv > dist[i, j]: continue
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == dj == 0: continue
            a, b = i + di, j + dj
            if 0 <= a < NX and 0 <= b < NZ:
                nd = dv + S * math.hypot(di, dj)
                if nd < dist[a, b]: dist[a, b] = nd; heapq.heappush(pq, (nd, a, b))

def flood(step_max):
    reach = np.zeros((NX, NZ), bool); par = {}
    dq = deque()
    for i in range(NX):
        for j in range(NZ):
            if (i in (0, NX - 1) or j in (0, NZ - 1)) and walk[i, j]:
                reach[i, j] = True; dq.append((i, j))
    while dq:
        i, j = dq.popleft()
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = i + di, j + dj
            if 0 <= a < NX and 0 <= b < NZ and walk[a, b] and not reach[a, b] and abs(ground[a, b] - ground[i, j]) <= step_max + 1e-6:
                reach[a, b] = True; dq.append((a, b))
    return reach

def path(reach, step_max, A, B):
    # Dijkstra over reachable cells, 8-neighbour, cost=length; returns length and min clearance along path
    sa, sb = cell(*A), cell(*B)
    if not (reach[sa] and reach[sb]): return None
    D = {sa: 0.0}; P = {}; pq = [(0.0, sa)]
    while pq:
        dv, c = heapq.heappop(pq)
        if c == sb: break
        if dv > D.get(c, INF): continue
        i, j = c
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == dj == 0: continue
                a, b = i + di, j + dj
                if 0 <= a < NX and 0 <= b < NZ and reach[a, b] and abs(ground[a, b] - ground[i, j]) <= step_max + 1e-6:
                    if di and dj and not (reach[i + di, j] and reach[i, j + dj]): continue
                    nd = dv + S * math.hypot(di, dj)
                    if nd < D.get((a, b), INF): D[(a, b)] = nd; P[(a, b)] = c; heapq.heappush(pq, (nd, (a, b)))
    if sb not in D: return None
    pts = [sb]
    while pts[-1] != sa: pts.append(P[pts[-1]])
    pts.reverse()
    clr = min(dist[p] for p in pts); rises = [round(float(ground[pts[k + 1]] - ground[pts[k]]), 3) for k in range(len(pts) - 1) if abs(ground[pts[k + 1]] - ground[pts[k]]) > 0.01]
    roofed = sum(1 for p in pts if not sky[p])
    return {'length_m': round(D[sb], 2), 'cells': len(pts), 'min_clearance_to_obstacle_m': round(float(clr), 3),
            'min_clear_width_est_m': round(2 * float(clr), 3), 'rises_m': rises, 'roofed_cells': roofed,
            'polyline_every_1m': [xz(pts[k]) for k in range(0, len(pts), max(1, int(round(1.0 / S))))] + [xz(pts[-1])]}

def runs_along(fixed_axis, fixed_val, lo, hi):
    # unblocked runs (before erosion) along a line; returns list of (start,end,width)
    out = []; cur = None
    vals = np.arange(lo, hi + 1e-9, S)
    for v in vals:
        c = cell(v, fixed_val) if fixed_axis == 'z' else cell(fixed_val, v)
        free = not blocked[c]
        if free and cur is None: cur = v
        if not free and cur is not None: out.append((round(cur, 2), round(v - S, 2), round(v - cur, 2))); cur = None
    if cur is not None: out.append((round(cur, 2), round(vals[-1], 2), round(vals[-1] - cur + S, 2)))
    return out

def largest_clear_square(mask):
    # largest axis-aligned square (side m) fully inside mask
    best = (0, None); dp = np.zeros((NX + 1, NZ + 1), int)
    for i in range(NX):
        for j in range(NZ):
            if mask[i, j]:
                dp[i + 1, j + 1] = 1 + min(dp[i, j + 1], dp[i + 1, j], dp[i, j])
                if dp[i + 1, j + 1] > best[0]: best = (dp[i + 1, j + 1], (i, j))
    n, (i, j) = best[0], best[1]
    return {'side_m': round(n * S, 2), 'x': [round(float(xs[i - n + 1]), 2), round(float(xs[i]), 2)], 'z': [round(float(zs[j - n + 1]), 2), round(float(zs[j]), 2)]}

# C probe points in the workyard local frame (derived from the measured layout, not from any source plan)
PROBES = {
    'outside_gate': (-4.8, 13.4),
    'gate_inner': (-4.8, 10.6),
    'pestle_mortar_side': (5.0, -0.9),     # feeding / emptying the mortar, north of mortar block
    'pestle_treadle_platform': (5.0, 3.15), # operator standing on 0.92 m treadle deck, behind beam end (beam ends z=2.85)
    'pestle_stair_foot': (5.0, 4.3),
    'west_house_inside': (-5.4, 2.6),
    'north_hall_inside': (0.0, -8.2),
    'east_shed_free': (7.2, 0.0),
}
def widest(reach, step_max, A, B):
    # bottleneck (max-min clearance) path; returns the best achievable min clearance and its length
    sa, sb = cell(*A), cell(*B)
    if not (reach[sa] and reach[sb]): return None
    best = {sa: dist[sa]}; P = {}; pq = [(-dist[sa], sa)]; done = set()
    while pq:
        nv, c = heapq.heappop(pq)
        if c in done: continue
        done.add(c)
        if c == sb: break
        i, j = c
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = i + di, j + dj
            if 0 <= a < NX and 0 <= b < NZ and reach[a, b] and (a, b) not in done and abs(ground[a, b] - ground[i, j]) <= step_max + 1e-6:
                v = min(-nv, dist[a, b])
                if v > best.get((a, b), -1):
                    best[(a, b)] = v; P[(a, b)] = c; heapq.heappush(pq, (-v, (a, b)))
    if sb not in best: return None
    pts = [sb]
    while pts[-1] != sa: pts.append(P[pts[-1]])
    pts.reverse()
    rh = [float(d['roof_h'][p]) for p in pts if not sky[p]]
    # bottleneck location
    k = min(range(len(pts)), key=lambda q: dist[pts[q]] if q not in (0, len(pts) - 1) else INF) if len(pts) > 2 else 0
    return {'bottleneck_clearance_m': round(float(best[sb]), 3), 'bottleneck_width_est_m': round(2 * float(best[sb]), 3),
            'bottleneck_at': xz(pts[k]), 'cells': len(pts), 'manhattan_length_m': round(len(pts) * S, 2),
            'min_headroom_roofed_m': round(min(rh), 3) if rh else None, 'pts': pts}

res = {'grid': sys.argv[1], 'step_m': S, 'probe_points_C': PROBES, 'per_step_max': {}}
res['gate_line_runs_z11.9'] = runs_along('z', 11.9, -9, 9)
res['gate_passage_runs_z11.0'] = runs_along('z', 11.0, -7, -2.5)
res['west_house_east_wall_runs_x-3.6'] = runs_along('x', -3.6, -1.2, 6.4)
res['west_house_east_wall_runs_x-3.7'] = runs_along('x', -3.7, -1.2, 6.4)
res['north_hall_south_wall_runs_z-6.0'] = runs_along('z', -6.0, -5.2, 5.2)
res['north_hall_south_wall_runs_z-5.9'] = runs_along('z', -5.9, -5.2, 5.2)
for sm in STEPS:
    reach = flood(sm)
    r = {'reachable_footprint_cells': int((reach & fp).sum()),
         'probe_reachable': {k: bool(reach[cell(*v)]) for k, v in PROBES.items()},
         'probe_ground_y': {k: round(float(ground[cell(*v)]), 3) for k, v in PROBES.items()},
         'probe_clearance_m': {k: round(float(dist[cell(*v)]), 3) for k, v in PROBES.items()},
         'largest_reachable_open_sky_square': largest_clear_square(reach & sky & fp & ~hf),
         'largest_reachable_roofed_square': largest_clear_square(reach & ~sky & fp),
         'legs': {}}
    legs = [('outside_gate', 'gate_inner'), ('gate_inner', 'pestle_stair_foot'), ('pestle_stair_foot', 'pestle_treadle_platform'),
            ('gate_inner', 'pestle_mortar_side'), ('pestle_mortar_side', 'west_house_inside'), ('pestle_mortar_side', 'north_hall_inside'),
            ('pestle_mortar_side', 'east_shed_free')]
    corridor = np.zeros((NX, NZ), bool); r['widest'] = {}
    for a, b in legs:
        r['legs'][a + '->' + b] = path(reach, sm, PROBES[a], PROBES[b])
        w = widest(reach, sm, PROBES[a], PROBES[b])
        if w:
            if a != 'outside_gate':
                for p in w['pts']: corridor[p] = True
            w = {k: v for k, v in w.items() if k != 'pts'}
        r['widest'][a + '->' + b] = w
    # C corridor half-width 0.6 m (1.2 m porter-with-load band) around the widest service paths
    CH = 0.6; rr = int(math.ceil(CH / S)); band = corridor.copy()
    for di in range(-rr, rr + 1):
        for dj in range(-rr, rr + 1):
            if di * di + dj * dj > (CH / S) ** 2: continue
            sh = np.zeros_like(corridor)
            sh[max(0, di):NX + min(0, di), max(0, dj):NZ + min(0, dj)] = corridor[max(0, -di):NX + min(0, -di), max(0, -dj):NZ + min(0, -dj)]
            band |= sh
    r['service_band_cells'] = int((band & fp).sum())
    r['winnow_open_sky_square_outside_band'] = largest_clear_square(reach & sky & fp & ~hf & ~band)
    r['roofed_square_outside_band'] = largest_clear_square(reach & ~sky & fp & ~band)
    r['roofed_raised_floor_square_outside_band'] = largest_clear_square(reach & ~sky & fp & hf & ~band)
    res['per_step_max'][str(sm)] = r
    np.save(OUT.replace('.json', '-band-%s.npy' % sm), band)
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps({k: (v['probe_reachable'], v['largest_reachable_open_sky_square'], v['largest_reachable_roofed_square']) for k, v in res['per_step_max'].items()}, ensure_ascii=False))
