# LY-047 prep measurement (read-only). Storage/shed install + operation clearance candidates.
# usage: python -I measure_ly047.py <lab_root> <out.json>
# Units: glTF metres, Y up. Court-local frame = prototype GLB frame (lot centre, floor top y=0.2).
# All clearance values are C engineering envelopes chosen here, not historical or code requirements.
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy import ndimage
import glbio, citydata

LAB = sys.argv[1]
OUT = sys.argv[2]
DOCS = os.path.join(LAB, 'docs')
CITY = os.path.join(DOCS, 'cities', 'luoyang')

FLOOR = 0.2
CELL = 0.05
BAND = (FLOOR + 0.25, FLOOR + 1.90)      # body band (C): above 0.25 m (steps/plinths <=0.22 m treated as walkable) to 1.90 m head
R_WALK = 0.30                             # unladen body radius (C)
R_LADEN = 0.45                            # person carrying a 0.6 m load (C)
REACH = 0.70                              # max body-centre distance to a storage face for pick/place (C)
OP_DEPTH = 0.90                           # operating strip depth in front of an open storage face (C)

SHED_BOX = {  # court-local AABB used only to pick the shed sub-elements out of shared nodes
    'B': (-7.2, -4.4, -0.4, 5.4),
    'B2': (-4.75, -0.25, 0.85, 4.15),
    'B2-north': (-4.75, -0.25, 0.05, 3.35),
    'B2-south': (-4.75, -0.25, 1.65, 4.95),
}
PROTO = {
    'B': {0: 'cities/luoyang/assets/r01/R01-B-LOD0-prototype.glb', 1: 'cities/luoyang/assets/r01/R01-B-LOD1-prototype.glb'},
    'B2': {0: 'cities/luoyang/assets/c02v/B2-LOD0-prototype.glb', 1: 'cities/luoyang/assets/c02v/B2-LOD1-prototype.glb'},
    'A2': {0: 'cities/luoyang/assets/c02v/A2-LOD0-prototype.glb', 1: 'cities/luoyang/assets/c02v/A2-LOD1-prototype.glb'},
}
EXCLUDE = {'B': ['site_lot', 'site_neutral_lane', 'designed_loading_yard'],
           'B2': ['site_lot', 'site_neutral_lane', 'designed_loading_yard'],
           'A2': ['site_lot', 'site_neutral_lane', 'designed_hardpacked_activity_ground']}
WORKSHED = {k: f'library/models/m-luoyang-workyard-shed/files/workshed-LOD{k}.glb' for k in (0, 1, 2)}
GROUNDS = [('ground-south', 'cities/luoyang/assets/ground-atomic/south.glb', (0, 0, 0)),
           ('ground-retained', 'cities/luoyang/assets/ground-atomic/retained.glb', (0, 0, 0)),
           ('ground-network-ground-stitched', 'cities/luoyang/assets/ground-atomic/network-ground-stitched.glb', (0, 0, 0)),
           ('ground-D08', 'cities/luoyang/assets/ground-atomic/D08.glb', (580, 0, -960))]
GATE = {'B': (-4.8, 11.75), 'B2': (-4.8, 11.75), 'A2': (-3.5, 11.75)}  # between gatehouse posts, inside lot
A2_DOORS = {'west_house_step': (-3.0, -0.6), 'north_house_step': (0.6, -3.8)}  # just outside each door step
LY044_STOVE_TRIAL_LOCAL = (533.0 - 531.0, -815.0 + 818.45)  # LY-044 prep probe-place.json trial, C02-010 local


def rel(p):
    return os.path.join(DOCS, p)


def comps(T):
    V = np.round(T.reshape(-1, 3), 4)
    _, inv = np.unique(V, axis=0, return_inverse=True)
    inv = inv.reshape(-1, 3)
    par = np.arange(inv.max() + 1)

    def f(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    for t in inv:
        a = f(t[0]); par[f(t[1])] = a; par[f(t[2])] = a
    roots = np.array([f(t[0]) for t in inv])
    return [T[roots == r] for r in np.unique(roots)]


def load_proto(path, excl):
    nodes = glbio.node_tris(rel(path))
    keep = {n: T for n, (T, ml) in nodes.items() if n not in excl}
    dropped = {n: T for n, (T, ml) in nodes.items() if n in excl}
    return keep, dropped


def classify(c):
    mn, mx = c.reshape(-1, 3).min(0), c.reshape(-1, 3).max(0)
    dx, dy, dz = mx - mn
    if mx[1] <= 0.29 and mn[1] <= FLOOR + 1e-4:
        return 'post_plinth'
    if dy > 1.5 and min(dx, dz) < 0.25:
        return 'post'
    if mn[1] > 2.0:
        return 'beam'
    if mx[1] < 0.8 and dx > 0.5 and dz > 0.5:
        return 'storage_bin'
    if 0.85 < mn[1] < 1.0 and mx[1] < 1.0:
        return 'bench_top'
    if mx[1] <= 0.95 and dx <= 0.11 and dz <= 0.11:
        return 'bench_leg'
    return 'other'


def shed_elements(keep, box):
    x0, x1, z0, z1 = box
    out = []
    for n, T in keep.items():
        if 'roof' in n:
            c = T.mean(1)
            m = (c[:, 0] > x0 - 0.9) & (c[:, 0] < x1 + 0.9) & (c[:, 2] > z0 - 0.9) & (c[:, 2] < z1 + 0.9) & (c[:, 1] < 3.6) & (c[:, 1] > 2.5)
            if m.any():
                S = T[m].reshape(-1, 3)
                out.append({'node': n, 'kind': 'shed_roof_part', 'tris': int(m.sum()), 'min': S.min(0).round(4).tolist(), 'max': S.max(0).round(4).tolist(), '_T': T[m]})
            continue
        for c in comps(T):
            V = c.reshape(-1, 3)
            mn, mx = V.min(0), V.max(0)
            if mn[0] >= x0 and mx[0] <= x1 and mn[2] >= z0 and mx[2] <= z1:
                out.append({'node': n, 'kind': classify(c), 'tris': int(len(c)), 'min': mn.round(4).tolist(), 'max': mx.round(4).tolist(), '_T': c})
    return out


class Grid:
    def __init__(self, x0=-9.0, x1=9.0, z0=-12.0, z1=12.0, cell=CELL):
        self.x0, self.z0, self.cell = x0, z0, cell
        self.nx = int(round((x1 - x0) / cell)); self.nz = int(round((z1 - z0) / cell))
        xs = x0 + (np.arange(self.nx) + 0.5) * cell; zs = z0 + (np.arange(self.nz) + 0.5) * cell
        self.X, self.Z = np.meshgrid(xs, zs, indexing='ij')

    def idx(self, x, z):
        return int((x - self.x0) / self.cell), int((z - self.z0) / self.cell)

    def raster(self, T, ylo=None, yhi=None):
        occ = np.zeros((self.nx, self.nz), bool)
        if len(T) == 0:
            return occ
        ymin, ymax = T[:, :, 1].min(1), T[:, :, 1].max(1)
        m = np.ones(len(T), bool)
        if ylo is not None:
            m &= ymax > ylo
        if yhi is not None:
            m &= ymin < yhi
        for t in T[m]:
            p = t[:, [0, 2]]
            lo = np.floor((p.min(0) - [self.x0, self.z0]) / self.cell).astype(int) - 1
            hi = np.ceil((p.max(0) - [self.x0, self.z0]) / self.cell).astype(int) + 1
            lo = np.maximum(lo, 0); hi = np.minimum(hi, [self.nx, self.nz])
            if hi[0] <= lo[0] or hi[1] <= lo[1]:
                continue
            X = self.X[lo[0]:hi[0], lo[1]:hi[1]]; Z = self.Z[lo[0]:hi[0], lo[1]:hi[1]]
            a, b, c = p
            d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(d) > 1e-12:
                l1 = ((b[1] - c[1]) * (X - c[0]) + (c[0] - b[0]) * (Z - c[1])) / d
                l2 = ((c[1] - a[1]) * (X - c[0]) + (a[0] - c[0]) * (Z - c[1])) / d
                l3 = 1 - l1 - l2
                occ[lo[0]:hi[0], lo[1]:hi[1]] |= (l1 >= -1e-9) & (l2 >= -1e-9) & (l3 >= -1e-9)
            for u, v in ((a, b), (b, c), (c, a)):
                L = np.hypot(*(v - u)); n = max(2, int(L / (self.cell * 0.4)) + 2)
                s = np.linspace(0, 1, n)[:, None]
                P = u + (v - u) * s
                ix = ((P[:, 0] - self.x0) / self.cell).astype(int); iz = ((P[:, 1] - self.z0) / self.cell).astype(int)
                ok = (ix >= 0) & (ix < self.nx) & (iz >= 0) & (iz < self.nz)
                occ[ix[ok], iz[ok]] = True
        return occ


def disc(r, cell=CELL):
    k = int(math.ceil(r / cell))
    y, x = np.mgrid[-k:k + 1, -k:k + 1]
    return (x * x + y * y) * cell * cell <= r * r + 1e-12


def reachable(grid, occ_band, r, seed):
    blocked = ndimage.binary_dilation(occ_band, structure=disc(r))
    free = ~blocked
    # lot edge is not walkable beyond the wall ring; the ring itself is in occ_band
    lab, _ = ndimage.label(free)
    i, j = grid.idx(*seed)
    if not free[i, j]:
        # nudge seed to nearest free cell within 0.5 m
        best = None
        for di in range(-10, 11):
            for dj in range(-10, 11):
                a, b = i + di, j + dj
                if 0 <= a < grid.nx and 0 <= b < grid.nz and free[a, b]:
                    d = di * di + dj * dj
                    if best is None or d < best[0]:
                        best = (d, a, b)
        if best is None:
            return np.zeros_like(free), free, False
        i, j = best[1], best[2]
    return lab == lab[i, j], free, True


def face_access(grid, reach, el):
    """For each vertical side of an element AABB: min distance from face to a reachable body centre within the face span."""
    mn, mx = el['min'], el['max']
    res = {}
    sides = {'-x': (0, mn[0], -1), '+x': (0, mx[0], +1), '-z': (2, mn[2], -1), '+z': (2, mx[2], +1)}
    for name, (ax, val, sgn) in sides.items():
        if ax == 0:
            span = (grid.Z >= mn[2]) & (grid.Z <= mx[2]); dist = (grid.X - val) * sgn
        else:
            span = (grid.X >= mn[0]) & (grid.X <= mx[0]); dist = (grid.Z - val) * sgn
        m = reach & span & (dist > 0)
        res[name] = round(float(dist[m].min()), 3) if m.any() else None
    return res


def headroom_over(T_all, x0, x1, z0, z1, floor=FLOOR, n=7):
    """Lowest geometry hit by vertical rays (n x n samples inside the xz rectangle) above floor+0.3; returned relative to floor."""
    T = np.concatenate(T_all)
    best = None
    for x in np.linspace(x0, x1, n)[1:-1]:
        for z in np.linspace(z0, z1, n)[1:-1]:
            a, b, c = T[:, 0, [0, 2]], T[:, 1, [0, 2]], T[:, 2, [0, 2]]
            d = (b[:, 1] - c[:, 1]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 1] - c[:, 1])
            ok = np.abs(d) > 1e-12
            dd = np.where(ok, d, 1.0)
            l1 = ((b[:, 1] - c[:, 1]) * (x - c[:, 0]) + (c[:, 0] - b[:, 0]) * (z - c[:, 1])) / dd
            l2 = ((c[:, 1] - a[:, 1]) * (x - c[:, 0]) + (a[:, 0] - c[:, 0]) * (z - c[:, 1])) / dd
            l3 = 1 - l1 - l2
            hit = ok & (l1 >= -1e-9) & (l2 >= -1e-9) & (l3 >= -1e-9)
            if not hit.any():
                continue
            y = l1 * T[:, 0, 1] + l2 * T[:, 1, 1] + l3 * T[:, 2, 1]
            y = y[hit & (y > floor + 0.3)]
            if len(y):
                v = float(y.min())
                best = v if best is None else min(best, v)
    return None if best is None else round(best - floor, 4)


def ground_tris():
    out = []
    for gid, p, tr in GROUNDS:
        for n, (T, ml) in glbio.node_tris(rel(p)).items():
            T2 = T + np.array(tr, float)
            out.append((gid, n, T2))
    return out


def ground_y(G, x, z):
    hits = []
    for gid, n, T in G:
        mnx, mxx = T[:, :, 0].min(1), T[:, :, 0].max(1)
        mnz, mxz = T[:, :, 2].min(1), T[:, :, 2].max(1)
        m = (mnx <= x + 1e-6) & (mxx >= x - 1e-6) & (mnz <= z + 1e-6) & (mxz >= z - 1e-6)
        for t in T[m]:
            a, b, c = t[:, [0, 2]]
            d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(d) < 1e-12:
                continue
            l1 = ((b[1] - c[1]) * (x - c[0]) + (c[0] - b[0]) * (z - c[1])) / d
            l2 = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (z - c[1])) / d
            l3 = 1 - l1 - l2
            if l1 >= -1e-7 and l2 >= -1e-7 and l3 >= -1e-7:
                hits.append((gid, float(l1 * t[0, 1] + l2 * t[1, 1] + l3 * t[2, 1])))
    if not hits:
        return None, None
    top = max(h[1] for h in hits)
    return top, sorted({h[0] for h in hits if abs(h[1] - top) < 1e-4})


def top_y_at(T, x, z):
    best = None
    for t in T:
        a, b, c = t[:, [0, 2]]
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-12:
            continue
        l1 = ((b[1] - c[1]) * (x - c[0]) + (c[0] - b[0]) * (z - c[1])) / d
        l2 = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (z - c[1])) / d
        l3 = 1 - l1 - l2
        if l1 >= -1e-7 and l2 >= -1e-7 and l3 >= -1e-7:
            y = float(l1 * t[0, 1] + l2 * t[1, 1] + l3 * t[2, 1])
            best = y if best is None else max(best, y)
    return best


def strip(el, side, depth=OP_DEPTH):
    mn, mx = el['min'], el['max']
    if side == '+x': return (mx[0], mx[0] + depth, mn[2], mx[2])
    if side == '-x': return (mn[0] - depth, mn[0], mn[2], mx[2])
    if side == '+z': return (mn[0], mx[0], mx[2], mx[2] + depth)
    return (mn[0], mx[0], mn[2] - depth, mn[2])


def rect_mask(grid, r):
    x0, x1, z0, z1 = r
    return (grid.X > x0) & (grid.X < x1) & (grid.Z > z0) & (grid.Z < z1)


def store_house(keep, grid):
    """East raised store-house of B/B2 (plinth top 0.65): steps, door, interior usable floor and headroom."""
    pl = [n for n in keep if 'floor_plinth' in n][0]
    tb = [n for n in keep if 'plain_timber' in n][0]
    pcs = comps(keep[pl])
    def bb(c):
        V = c.reshape(-1, 3); return V.min(0), V.max(0)
    house = [c for c in pcs if abs(bb(c)[1][1] - 0.65) < 1e-3 and (bb(c)[1][0] - bb(c)[0][0]) * (bb(c)[1][2] - bb(c)[0][2]) > 10]
    steps = [c for c in pcs if abs(bb(c)[1][1] - 0.65) < 1e-3 and (bb(c)[1][0] - bb(c)[0][0]) * (bb(c)[1][2] - bb(c)[0][2]) <= 10]
    if not house:
        return None
    hmn, hmx = bb(house[0])
    out = {'plinth_min': hmn.round(4).tolist(), 'plinth_max': hmx.round(4).tolist(), 'floor_y': round(float(hmx[1]), 4),
           'rise_above_yard_m': round(float(hmx[1] - FLOOR), 4)}
    if steps:
        V = np.unique(np.round(steps[0].reshape(-1, 3), 4), axis=0)
        ys = sorted(set(V[:, 1].tolist())); xs = sorted(set(V[:, 0].tolist()))
        out['steps'] = {'min': V.min(0).tolist(), 'max': V.max(0).tolist(), 'levels_y': ys,
                        'risers_m': [round(b - a, 4) for a, b in zip(ys, ys[1:])], 'treads_m': [round(b - a, 4) for a, b in zip(xs, xs[1:])],
                        'width_m': round(float(V[:, 2].max() - V[:, 2].min()), 4),
                        'bottom_on_floor': bool(abs(V[:, 1].min() - FLOOR) < 1e-4)}
    frames = []
    for c in comps(keep[tb]):
        mn, mx = bb(c)
        if abs(mn[1] - hmx[1]) < 1e-3 and (mx[0] - mn[0]) <= 0.11 and (mx[2] - mn[2]) > 1.5:
            V = np.unique(np.round(c.reshape(-1, 3), 4), axis=0)
            zs = sorted(set(V[:, 2].tolist())); ys = sorted(set(V[:, 1].tolist()))
            frames.append({'min': mn.round(4).tolist(), 'max': mx.round(4).tolist(), 'z_levels': zs, 'y_levels': ys,
                           'clear_width_m': round(zs[-2] - zs[1], 4) if len(zs) >= 4 else None,
                           'clear_height_m': round(ys[-2] - mn[1], 4) if len(ys) >= 3 else None})
    out['door_frames'] = frames
    # interior usable floor: body band relative to raised floor, seed just inside the door
    allT = np.concatenate(list(keep.values()))
    band = grid.raster(allT, hmx[1] + 0.25, hmx[1] + 1.90)
    inside = (grid.X > hmn[0]) & (grid.X < hmx[0]) & (grid.Z > hmn[2]) & (grid.Z < hmx[2])
    if frames:
        f = frames[0]; seed = (f['max'][0] + 0.45, (f['min'][2] + f['max'][2]) / 2)
        for r, key in ((R_WALK, 'walk'), (R_LADEN, 'laden')):
            rc, _, ok = reachable(grid, band, r, seed)
            out[f'interior_reachable_m2_{key}'] = round(float((rc & inside).sum()) * CELL * CELL, 2)
            out[f'yard_connected_{key}'] = bool((rc & ~inside).any())
    out['interior_plinth_area_m2'] = round(float(inside.sum()) * CELL * CELL, 2)
    out['interior_headroom_m'] = headroom_over(list(keep.values()), hmn[0] + 0.5, hmx[0] - 0.5, hmn[2] + 0.5, hmx[2] - 0.5, floor=hmx[1])
    out['plinth_bottom_on_floor'] = bool(abs(hmn[1] - FLOOR) < 1e-4)
    return out


def main():
    res = {'tool': 'measure_ly047.py', 'lab': LAB, 'params': {'FLOOR': FLOOR, 'CELL': CELL, 'BAND': BAND, 'R_WALK': R_WALK, 'R_LADEN': R_LADEN, 'REACH': REACH, 'OP_DEPTH': OP_DEPTH,
                                                            'note': 'C engineering envelopes; discrete grid; vertical rays; not solid collision or continuous motion'}}
    res['sha256'] = {}
    for v in PROTO:
        for k, p in PROTO[v].items():
            res['sha256'][p] = glbio.sha256(rel(p))
    for k, p in WORKSHED.items():
        res['sha256'][p] = glbio.sha256(rel(p))
    for gid, p, tr in GROUNDS:
        res['sha256'][p] = glbio.sha256(rel(p))
    cd_path = os.path.join(CITY, 'city-data.mjs')
    res['sha256']['cities/luoyang/city-data.mjs'] = glbio.sha256(cd_path)
    cd = citydata.load(cd_path)

    # ---------- 1. in-place sheds of B/B2 ----------
    res['inplace'] = {}
    grid = Grid()
    runs = [(v, lod, PROTO[v][lod], v) for v in ('B', 'B2') for lod in (0, 1)]
    runs += [('B2-' + k, 0, f'model-library/updates/m-courtyard-family/files/{k}.glb', 'B2') for k in ('baseline', 'north', 'south')]
    for label, lod, path, v in runs:
        if True:
            keep, dropped = load_proto(path, EXCLUDE[v])
            box = SHED_BOX.get(label, SHED_BOX['B2'] if label == 'B2-baseline' else None) or SHED_BOX[v]
            els = shed_elements(keep, box)
            allT = np.concatenate(list(keep.values()))
            band_occ = grid.raster(allT, *BAND)
            reach_w, free_w, ok_w = reachable(grid, band_occ, R_WALK, GATE[v])
            reach_l, free_l, ok_l = reachable(grid, band_occ, R_LADEN, GATE[v])
            ly = dropped.get('designed_loading_yard', np.zeros((0, 3, 3)))
            store = [e for e in els if e['kind'] in ('storage_bin', 'bench_top')]
            entries = []
            for e in store:
                fa_w = face_access(grid, reach_w, e); fa_l = face_access(grid, reach_l, e)
                acc_sides = [s for s, d in fa_w.items() if d is not None and d <= REACH]
                strips = {}
                for s in fa_w:
                    sm = rect_mask(grid, strip(e, s))
                    strips[s] = {'cells': int(sm.sum()), 'obstructed_cells_band': int((sm & band_occ).sum())}
                mn, mx = e['min'], e['max']
                hr = headroom_over(list(keep.values()), mn[0] - 0.05, mx[0] + 0.05, mn[2] - 0.05, mx[2] + 0.05, floor=mx[1])
                entries.append({'kind': e['kind'], 'min': mn, 'max': mx, 'height_above_floor': round(mx[1] - FLOOR, 3),
                                'reach_walk_m': fa_w, 'reach_laden_m': fa_l, 'sides_within_REACH_walk': acc_sides,
                                'op_strip_0.9m': strips, 'clear_height_above_top_m': hr})
            # support: bottom vertices of shed elements at floor
            bottoms = []
            for e in els:
                if e['kind'] == 'shed_roof_part' or e['min'][1] > FLOOR + 0.01:
                    continue
                V = e['_T'].reshape(-1, 3)
                b = np.unique(np.round(V[np.abs(V[:, 1] - V[:, 1].min()) < 1e-5], 5), axis=0)
                for p in b:
                    bottoms.append((e['kind'], p))
            on_yard = []
            for kind, p in bottoms:
                yt = top_y_at(ly, p[0], p[2])
                on_yard.append(None if yt is None else round(yt - p[1], 4))
            post_bottom = [round(float(p[1]), 4) for k, p in bottoms]
            hdr_beam = headroom_over([e['_T'] for e in els if e['kind'] in ('beam', 'shed_roof_part')], *box)
            posts = [e for e in els if e['kind'] == 'post']
            plinths = [e for e in els if e['kind'] == 'post_plinth']
            post_seat = []
            for po in posts:
                cx = (po['min'][0] + po['max'][0]) / 2; cz = (po['min'][2] + po['max'][2]) / 2
                seat = [pl for pl in plinths if pl['min'][0] <= cx <= pl['max'][0] and pl['min'][2] <= cz <= pl['max'][2]]
                post_seat.append(None if not seat else round(po['min'][1] - seat[0]['max'][1], 5))
            beams = [e for e in els if e['kind'] == 'beam']
            if PROTO.get(v, {}).get(lod) == path:
                res['sha256'][path] = res['sha256'].get(path) or glbio.sha256(rel(path))
            else:
                res['sha256'][path] = glbio.sha256(rel(path))
            res['inplace'][label if label.startswith('B2-') else f'{v}-LOD{lod}'] = {
                'variant': v, 'shed_box': box,
                'post_on_plinth_gap_m': post_seat,
                'store_house': store_house(keep, grid),
                'beam_underside_above_floor_m': round(min(e['min'][1] for e in beams) - FLOOR, 4) if beams else None,
                'glb': path,
                'elements': [{k: e[k] for k in ('node', 'kind', 'tris', 'min', 'max')} for e in els],
                'element_counts': {k: sum(1 for e in els if e['kind'] == k) for k in sorted({e['kind'] for e in els})},
                'shed_tris_total': int(sum(e['tris'] for e in els)),
                'host_node_tris': {n: int(len(T)) for n, T in keep.items()},
                'separately_loadable': False,
                'separately_loadable_reason': 'shed posts/bins/bench are merged into the court-wide nodes architecture_C_plain_timber / floor_plinth / roof; no node of its own',
                'storage_access': entries,
                'shed_clear_height_m': hdr_beam,
                'bottom_vertices': len(bottoms),
                'bottom_y_min_max': [min(post_bottom), max(post_bottom)],
                'bottom_vs_loading_yard_top_m': {'on_yard': sum(1 for x in on_yard if x is not None), 'off_yard': sum(1 for x in on_yard if x is None),
                                                 'gap_values': sorted({x for x in on_yard if x is not None})},
                'gate_seed_free_walk': ok_w, 'gate_seed_free_laden': ok_l,
                'reachable_area_m2_walk': round(float(reach_w.sum()) * CELL * CELL, 2),
                'reachable_area_m2_laden': round(float(reach_l.sum()) * CELL * CELL, 2),
            }

    # ---------- 2. city support for all B/B2 instances ----------
    G = ground_tris()
    keepB = {v: shed_elements(load_proto(PROTO[v][0], EXCLUDE[v])[0], SHED_BOX[v]) for v in ('B', 'B2')}
    inst = []
    for n in cd['nodes']:
        a = n.get('asset')
        if a not in ('courtyard-B', 'courtyard-B2'):
            continue
        v = 'B' if a == 'courtyard-B' else 'B2'
        M = glbio.matrix_from_city(n['matrix'])
        pts = []
        for e in keepB[v]:
            if e['kind'] == 'shed_roof_part' or e['min'][1] > FLOOR + 0.01:
                continue
            V = e['_T'].reshape(-1, 3)
            b = np.unique(np.round(V[np.abs(V[:, 1] - V[:, 1].min()) < 1e-5], 5), axis=0)
            pts.extend(b.tolist())
        P = (M @ np.c_[np.array(pts), np.ones(len(pts))].T).T[:, :3]
        gaps, srcs, nog = [], set(), 0
        for p in P:
            y, s = ground_y(G, p[0], p[2])
            if y is None:
                nog += 1
            else:
                gaps.append(p[1] - y); srcs.update(s)
        inst.append({'id': n['id'], 'asset': a, 'line': cd['idline'].get(n['id']), 'initial': n.get('initial'), 'chapter': n.get('chapter'),
                     'translation': [n['matrix'][12], n['matrix'][13], n['matrix'][14]], 'yaw_cos_sin': [n['matrix'][0], n['matrix'][8]],
                     'shed_bottom_vertices': len(P), 'noGround': nog,
                     'gap_min': round(min(gaps), 6) if gaps else None, 'gap_max': round(max(gaps), 6) if gaps else None,
                     'floating_gt_5mm': sum(1 for g in gaps if g > 0.005), 'buried_lt_-5mm': sum(1 for g in gaps if g < -0.005),
                     'ground_sources': sorted(srcs)})
    ground_nodes = [{'id': n['id'], 'initial': n.get('initial'), 'chapter': n.get('chapter'), 'line': cd['idline'].get(n['id'])}
                    for n in cd['nodes'] if n['id'].startswith('ground-')]
    res['city_instances'] = {'count': len(inst), 'by_asset': {a: sum(1 for i in inst if i['asset'] == a) for a in ('courtyard-B', 'courtyard-B2')},
                             'instances': inst, 'ground_nodes': ground_nodes,
                             'default_view_ground_loaded': any(g['initial'] is not False for g in ground_nodes)}

    # ---------- 3. workshed as an install candidate in A2 / C02-010 ----------
    ws = {}
    for k, p in WORKSHED.items():
        nodes = glbio.node_tris(rel(p))
        T = np.concatenate([T for T, ml in nodes.values()])
        V = T.reshape(-1, 3)
        posts = [c for c in comps(nodes['workshed_timber'][0]) if c.reshape(-1, 3)[:, 1].min() < 1e-4] if 'workshed_timber' in nodes else []
        ws[f'LOD{k}'] = {'glb': p, 'nodes': {n: int(len(T)) for n, (T, ml) in nodes.items()}, 'min': V.min(0).round(4).tolist(), 'max': V.max(0).round(4).tolist(),
                         'ground_posts': len(posts), 'post_bottom_y': sorted({round(float(c.reshape(-1, 3)[:, 1].min()), 4) for c in posts}),
                         'tie_beam_underside_y': round(float(min(c.reshape(-1, 3)[:, 1].min() for c in comps(nodes['workshed_timber'][0]) if c.reshape(-1, 3)[:, 1].min() > 1.0)), 4) if 'workshed_timber' in nodes else None}
    res['workshed'] = ws
    keepA, _ = load_proto(PROTO['A2'][0], EXCLUDE['A2'])
    allA = np.concatenate(list(keepA.values()))
    occ_any = grid.raster(allA, FLOOR + 0.05, None)   # any height above floor (filled projections)
    occ_band = grid.raster(allA, *BAND)
    reachA_l, _, _ = reachable(grid, occ_band, R_LADEN, GATE['A2'])
    door_ok = {d: bool(reachA_l[grid.idx(*xy)]) for d, xy in A2_DOORS.items()}
    # workshed footprint (eaves) and posts from LOD0, origin as delivered (front edge at local z=0)
    W0 = glbio.node_tris(rel(WORKSHED[0]))
    WT = np.concatenate([T for T, ml in W0.values()])
    eav = (WT[:, :, 0].min(), WT[:, :, 0].max(), WT[:, :, 2].min(), WT[:, :, 2].max())
    postc = [c.reshape(-1, 3) for c in comps(W0['workshed_timber'][0]) if c.reshape(-1, 3)[:, 1].min() < 1e-4]
    post_boxes = [(c[:, 0].min(), c[:, 0].max(), c[:, 2].min(), c[:, 2].max()) for c in postc]
    inner = (min(b[1] for b in post_boxes), max(b[0] for b in post_boxes), min(b[3] for b in post_boxes), max(b[2] for b in post_boxes))
    feas = []
    tried = 0
    stage = {'outside_lot_inner': 0, 'eaves_hit_existing': 0, 'gate_blocked': 0, 'door_cut_off': 0, 'under_shed_unreachable': 0}
    step = 0.5
    for yaw in (0, 90):
        for cx in np.arange(-9.0, 9.0001, step):
            for cz in np.arange(-12.0, 12.0001, step):
                tried += 1
                def tf(x0, x1, z0, z1):
                    if yaw == 0:
                        return (x0 + cx, x1 + cx, z0 + cz, z1 + cz)
                    return (z0 + cx, z1 + cx, -x1 + cz, -x0 + cz)
                e = tf(*eav)
                if e[0] < -8.7 or e[1] > 8.7 or e[2] < -11.7 or e[3] > 11.7:
                    stage['outside_lot_inner'] += 1; continue
                if (rect_mask(grid, e) & occ_any).any():
                    stage['eaves_hit_existing'] += 1; continue
                pocc = occ_band.copy()
                for b in post_boxes:
                    pocc |= rect_mask(grid, tf(*b))
                r_l, _, okl = reachable(grid, pocc, R_LADEN, GATE['A2'])
                if not okl:
                    stage['gate_blocked'] += 1; continue
                if not all(r_l[grid.idx(*xy)] for xy in A2_DOORS.values()):
                    stage['door_cut_off'] += 1; continue
                r_w, _, _ = reachable(grid, pocc, R_WALK, GATE['A2'])
                inn = rect_mask(grid, tf(*inner))
                under_reach = float((inn & r_w).sum()) / max(1, int(inn.sum()))
                if under_reach < 0.5:
                    stage['under_shed_unreachable'] += 1; continue
                sx, sz = LY044_STOVE_TRIAL_LOCAL
                stove_conflict = (e[0] - 1.5 < sx < e[1] + 1.5) and (e[2] - 1.5 < sz < e[3] + 1.5)
                feas.append({'yaw': yaw, 'origin_local': [round(float(cx), 3), round(float(cz), 3)], 'eaves_rect': [round(float(x), 3) for x in e],
                             'under_shed_reachable_frac_walk': round(under_reach, 3), 'conflicts_LY044_stove_trial_1.5m': stove_conflict})
    # cross-checks on feasible placements: A2 LOD1 obstacle map, and city ground under posts at C02-010
    keepA1, _ = load_proto(PROTO['A2'][1], EXCLUDE['A2'])
    occ_any1 = grid.raster(np.concatenate(list(keepA1.values())), FLOOR + 0.05, None)
    c010 = [n for n in cd['nodes'] if n['id'] == 'C02-010'][0]
    M010 = glbio.matrix_from_city(c010['matrix'])
    lod1_ok, gnd = 0, {'posts': 0, 'noGround': 0, 'gap_min': None, 'gap_max': None, 'sources': set()}
    for f in feas:
        e = f['eaves_rect']
        if not (rect_mask(grid, e) & occ_any1).any():
            lod1_ok += 1
        cx, cz = f['origin_local']; yaw = f['yaw']
        for b in post_boxes:
            px, pz = (b[0] + b[1]) / 2, (b[2] + b[3]) / 2
            lx, lz = (px + cx, pz + cz) if yaw == 0 else (pz + cx, -px + cz)
            w = M010 @ np.array([lx, FLOOR, lz, 1.0])
            y, src = ground_y(G, w[0], w[2])
            gnd['posts'] += 1
            if y is None:
                gnd['noGround'] += 1
            else:
                g = float(w[1] - y)
                gnd['gap_min'] = g if gnd['gap_min'] is None else min(gnd['gap_min'], g)
                gnd['gap_max'] = g if gnd['gap_max'] is None else max(gnd['gap_max'], g)
                gnd['sources'].update(src)
    gnd['sources'] = sorted(gnd['sources'])
    free_any = ~occ_any & rect_mask(grid, (-8.7, 8.7, -11.7, 11.7))
    # largest axis-aligned free rectangle check by distance transform proxy
    dt = ndimage.distance_transform_edt(free_any) * CELL
    res['a2_install_option'] = {
        'court': 'C02-010 (courtyard-A2) as proposed by LY-041 prep; frame = A2 prototype local',
        'a2_glb': PROTO['A2'][0],
        'gate_seed': GATE['A2'], 'doors': A2_DOORS, 'doors_reachable_laden_before': door_ok,
        'free_area_any_height_m2': round(float(free_any.sum()) * CELL * CELL, 2),
        'max_inscribed_circle_radius_m': round(float(dt.max()), 3),
        'workshed_eaves_rect_local': [round(float(x), 3) for x in eav], 'workshed_eaves_size_m': [round(float(eav[1] - eav[0]), 3), round(float(eav[3] - eav[2]), 3)],
        'workshed_post_boxes': [[round(float(x), 3) for x in b] for b in post_boxes],
        'placements_tried': tried, 'placements_feasible': len(feas), 'rejected_by_stage': stage,
        'feasible_also_clear_on_A2_LOD1': lod1_ok,
        'C02_010_matrix_line': cd['idline'].get('C02-010'), 'C02_010_matrix': c010['matrix'],
        'city_ground_under_posts_with_y_offset_0.2': gnd,
        'feasible_without_LY044_conflict': sum(1 for f in feas if not f['conflicts_LY044_stove_trial_1.5m']),
        'feasible_sample': feas[:12],
        'feasible_origin_extent': None if not feas else {
            str(y): {'x': [min(f['origin_local'][0] for f in feas if f['yaw'] == y), max(f['origin_local'][0] for f in feas if f['yaw'] == y)],
                     'z': [min(f['origin_local'][1] for f in feas if f['yaw'] == y), max(f['origin_local'][1] for f in feas if f['yaw'] == y)],
                     'n': sum(1 for f in feas if f['yaw'] == y)} for y in (0, 90) if any(f['yaw'] == y for f in feas)},
        'y_offset_needed': 'workshed post bottoms are at y=0.0; court floor / city ground top is 0.200 -> translation y=+0.200 required (else 0.2 m buried)',
    }
    # strip internal arrays
    json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=lambda o: o.tolist() if hasattr(o, 'tolist') else str(o))
    print('wrote', OUT)


if __name__ == '__main__':
    main()
