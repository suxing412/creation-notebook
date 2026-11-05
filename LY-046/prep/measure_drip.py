# LY-046 prep: eave drip line / drain stone / front-wall opening / city ground measurement.
# Read-only on the lab repo. Surface heightfield only (not solid collision, not water simulation).
# usage: python measure_drip.py <lab_root> <out_json> [grid_m]
import sys, os, json
import numpy as np
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbio import nodes_tris, raster, sha256, col_major

LAB, OUT = sys.argv[1], sys.argv[2]
H = float(sys.argv[3]) if len(sys.argv) > 3 else 0.05
CITY = os.path.join(LAB, 'docs/cities/luoyang')
VAR = {
    'A2': ('assets/c02v/A2-LOD0-prototype.glb', 'assets/c02v/A2-LOD1-prototype.glb', ['site_lot', 'site_neutral_lane', 'designed_hardpacked_activity_ground']),
    'TC03-2': ('assets/c02v/TC03-2-LOD0-prototype.glb', 'assets/c02v/TC03-2-LOD1-prototype.glb', ['site_lot', 'site_neutral_lane', 'designed_front_apron', 'designed_side_passage', 'designed_rear_work_ground']),
    'TC03': ('assets/d08/TC03-LOD0-prototype.glb', 'assets/d08/TC03-LOD1-prototype.glb', ['site_lot', 'site_neutral_lane']),
    'A': ('assets/r01/R01-A-LOD0-prototype.glb', 'assets/r01/R01-A-LOD1-prototype.glb', ['site_lot', 'site_neutral_lane', 'designed_hardpacked_activity_ground']),
    'B': ('assets/r01/R01-B-LOD0-prototype.glb', 'assets/r01/R01-B-LOD1-prototype.glb', ['site_lot', 'site_neutral_lane', 'designed_loading_yard']),
    'B2': ('assets/c02v/B2-LOD0-prototype.glb', 'assets/c02v/B2-LOD1-prototype.glb', ['site_lot', 'site_neutral_lane', 'designed_loading_yard']),
}
CASES = {'C02-010': 'A2', 'C02-012': 'TC03-2', 'C02-003': 'TC03-2', 'C02-008': 'TC03', 'C02-020': 'TC03'}
MATS = {'C02-010': [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 531, 0, -818.45, 1],
        'C02-012': [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 570, 0, -805.45, 1],
        'C02-003': [0, 0, -1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 615.8, 0, -1164.95544, 1],
        'C02-008': [-1, 0, 0, 0, 0, 1, 0, 0, 0, 0, -1, 0, 658, 0, -794.55, 1],
        'C02-020': [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 738.98936, 0, -1004.2, 1]}
GROUNDS = [('ground-network-ground-stitched', 'assets/ground-atomic/network-ground-stitched.glb', (0, 0, 0)),
           ('ground-retained', 'assets/ground-atomic/retained.glb', (0, 0, 0)),
           ('ground-south', 'assets/ground-atomic/south.glb', (0, 0, 0)),
           ('ground-D08', 'assets/ground-atomic/D08.glb', (580, 0, -960))]
rep = {'tool': 'measure_drip.py', 'grid_m': H, 'scope': 'surface heightfield at cell centres + edge splats; drip edge = roof-projection boundary cell; no water simulation, no solid collision', 'inputs': {}, 'variants': {}, 'city': {}}


def kind(n):
    n = n.lower()
    for k in ('roof', 'drain', 'wall', 'timber', 'plinth'):
        if k in n:
            return k
    if n.startswith('designed_'):
        return 'designed_ground'
    if n.startswith('site_'):
        return 'site'
    return 'other'


def grid_for(tris_list, pad=1.0):
    P = np.concatenate([t.reshape(-1, 3) for t in tris_list if len(t)])
    x0, z0 = P[:, 0].min() - pad, P[:, 2].min() - pad
    nx = int(np.ceil((P[:, 0].max() + pad - x0) / H)); nz = int(np.ceil((P[:, 2].max() + pad - z0) / H))
    return x0, z0, nx, nz


def analyse(nt, excl):
    by = {}
    for k, t in nt.items():
        by.setdefault(kind(k), []).append((k, t))
    x0, z0, nx, nz = grid_for(list(nt.values()))
    def R(kd, edge=None):
        ts = [t for _, t in by.get(kd, [])]
        if not ts:
            return None
        return raster(np.concatenate(ts), x0, z0, H, nx, nz, edge_step=edge)
    roof = R('roof'); wall = R('wall', H / 2); drain = R('drain', H / 2); plinth = R('plinth'); timber = R('timber', H / 2)
    cityg = [t for k, t in nt.items() if kind(k) == 'designed_ground' and k not in excl]
    site = [t for k, t in nt.items() if k in excl]
    rt, rb, rh = roof
    cov = rh > 0
    cov = ndimage.binary_closing(cov, iterations=2)
    edge = cov & ~ndimage.binary_erosion(cov)
    # outside neighbour of each edge cell = cell where water falls (1 cell beyond)
    out = ndimage.binary_dilation(cov) & ~cov
    wt = wall[0]
    walltop = np.where(np.isfinite(wt), wt, -np.inf)
    lot = [t for k, t in nt.items() if k == 'site_lot'][0].reshape(-1, 3)
    lx0, lx1, lz0, lz1 = lot[:, 0].min(), lot[:, 0].max(), lot[:, 2].min(), lot[:, 2].max()
    gx = x0 + (np.arange(nx) + .5) * H; gz = z0 + (np.arange(nz) + .5) * H
    X, Z = np.meshgrid(gx, gz)
    inlot = (X > lx0 + 1e-6) & (X < lx1 - 1e-6) & (Z > lz0 + 1e-6) & (Z < lz1 - 1e-6)
    fall_wall = out & (walltop > 0.5)
    fall_open_in = out & ~(walltop > 0.5) & inlot
    fall_out = out & ~inlot
    eave = rb[edge & np.isfinite(rb)]
    res = {'gridOrigin': [round(x0, 3), round(z0, 3)], 'grid': [nx, nz],
           'lotBounds_xz': [round(lx0, 3), round(lz0, 3), round(lx1, 3), round(lz1, 3)],
           'roofCoveredM2': round(float(cov.sum()) * H * H, 2), 'dripEdgeCells': int(edge.sum()),
           'eaveBottomY': {'min': round(float(eave.min()), 3), 'median': round(float(np.median(eave)), 3), 'max': round(float(eave.max()), 3)},
           'dripLandingCells': {'onWallTop_gt0.5m': int(fall_wall.sum()), 'openGroundInsideLot': int(fall_open_in.sum()), 'outsideLot': int(fall_out.sum())},
           'dripLandingOpenInsideLotM': round(float(fall_open_in.sum()) * H, 1)}
    # landing surface heights inside lot (non-roof surfaces: designed grounds kept in city, plinth, drain, else lot top 0.2)
    land = np.full((nz, nx), 0.2)
    for r in (plinth, drain, timber):
        if r is not None:
            land = np.where(np.isfinite(r[0]) & (r[0] < 0.6), np.maximum(land, r[0]), land)
    if cityg:
        g = raster(np.concatenate(cityg), x0, z0, H, nx, nz)
        land = np.where(np.isfinite(g[0]), np.maximum(land, g[0]), land)
    lv = land[fall_open_in]
    res['dripLandingSurfaceY_insideLot'] = {'min': round(float(lv.min()), 4), 'max': round(float(lv.max()), 4)} if lv.size else None
    res['dripFallHeight_m'] = round(float(np.median(eave) - 0.2), 3)
    # overhang: distance from open-ground landing cells to nearest wall cell
    wallmask = walltop > 0.5
    dist = ndimage.distance_transform_edt(~wallmask) * H
    dv = dist[fall_open_in]
    res['dripToNearestWall_m'] = {'p05': round(float(np.percentile(dv, 5)), 3), 'median': round(float(np.median(dv)), 3), 'p95': round(float(np.percentile(dv, 95)), 3)} if dv.size else None
    # drain stone
    if drain is not None:
        dt_ = [t for k, t in nt.items() if kind(k) == 'drain'][0]
        P = dt_.reshape(-1, 3)
        dm = np.isfinite(drain[0])
        ddist = ndimage.distance_transform_edt(~dm) * H
        dd = ddist[edge]
        nrm = np.cross(dt_[:, 1] - dt_[:, 0], dt_[:, 2] - dt_[:, 0]); nrm /= np.linalg.norm(nrm, axis=1)[:, None]
        bed = dt_[(nrm[:, 1] > 0.99) & (dt_[:, :, 1].max(1) < 0.285)].reshape(-1, 3)
        zA, zB = bed[:, 2].min(), bed[:, 2].max()
        yA = bed[bed[:, 2] == zA][:, 1].mean(); yB = bed[bed[:, 2] == zB][:, 1].mean()
        L = zB - zA
        # roof directly above drain cells
        above = dm & cov
        # wall at drain downstream end, front wall gap check along z = lot front
        endz = zB; frontz = lz1
        xs = (gx >= P[:, 0].min()) & (gx <= P[:, 0].max())
        zs = (gz > endz) & (gz < frontz + 0.5)
        col = walltop[np.ix_(zs, xs)]
        res['drainStone'] = {
            'bbox': [P.min(0).round(3).tolist(), P.max(0).round(3).tolist()], 'tris': int(len(dt_)),
            'section': 'U channel: two curbs 0.08 m x 0.09 m, bed width 0.24 m (from vertices)',
            'bedY_rear': round(float(yA), 4), 'bedY_front': round(float(yB), 4), 'lengthAlongZ_m': round(float(L), 3),
            'bedFallPercent': round(float((yA - yB) / L * 100), 4), 'flowDirection': '+z (toward lot front / lane)' if yA > yB else '-z',
            'channelDepthRear_m': round(0.29 - float(yA), 4), 'channelDepthFront_m': round(0.29 - float(yB), 4),
            'bedAboveLotTopAtFrontEnd_m': round(float(yB) - 0.2, 4),
            'downstreamEndZ': round(float(endz), 3), 'lotFrontZ': round(float(frontz), 3), 'gapEndToFront_m': round(float(frontz - endz), 3),
            'wallBetweenEndAndFront_maxTop': round(float(col.max()), 3) if col.size else None,
            'wallCellsBetweenEndAndFront': int((col > 0.5).sum()) if col.size else 0,
            'roofCoversDrainCellsFraction': round(float(above.sum() / max(dm.sum(), 1)), 3),
            'dripEdgeDistanceToDrain_m': {'min': round(float(dd.min()), 3), 'p10': round(float(np.percentile(dd, 10)), 3)},
            'dripEdgeCellsWithin0.3mOfDrain': int((dd <= 0.3).sum()),
        }
    # front wall openings along lot front line (z = lz1 - 0.1 .. lz1)
    fr = (gz > lz1 - 0.4) & (gz < lz1 + 0.05)
    row = (walltop[fr, :] > 0.5).any(0) & (gx > lx0) & (gx < lx1)
    gaps = []; inx = (gx > lx0 + H) & (gx < lx1 - H); cur = None
    for i in range(nx):
        if inx[i] and not row[i]:
            cur = [gx[i], gx[i]] if cur is None else [cur[0], gx[i]]
        elif cur is not None:
            gaps.append([round(cur[0] - H / 2, 3), round(cur[1] + H / 2, 3)]); cur = None
    if cur: gaps.append([round(cur[0] - H / 2, 3), round(cur[1] + H / 2, 3)])
    res['frontWallGaps_x'] = [g + [round(g[1] - g[0], 3)] for g in gaps]
    return res, (x0, z0, nx, nz, cov, edge, fall_open_in)


for v, (near, far, excl) in VAR.items():
    rep['variants'][v] = {}
    for lod, rel in (('LOD0', near), ('LOD1', far)):
        p = os.path.join(CITY, rel); rep['inputs'][rel] = sha256(p)
        res, _ = analyse(nodes_tris(p), excl)
        res['file'] = rel
        rep['variants'][v][lod] = res

# city ground around the cases (world)
gts = {}
for gid, rel, off in GROUNDS:
    p = os.path.join(CITY, rel); rep['inputs'][rel] = sha256(p)
    M = np.eye(4); M[:3, 3] = off
    t = np.concatenate(list(nodes_tris(p, M).values())); gts[gid] = t
for cid, v in CASES.items():
    M = col_major(MATS[cid])
    nt = nodes_tris(os.path.join(CITY, VAR[v][0]), M)
    lot = nt['site_lot'].reshape(-1, 3)
    x0, x1 = lot[:, 0].min() - 8, lot[:, 0].max() + 8; z0, z1 = lot[:, 2].min() - 8, lot[:, 2].max() + 8
    nx, nz = int((x1 - x0) / 0.25), int((z1 - z0) / 0.25)
    top = np.full((nz, nx), -np.inf); sup = np.full((nz, nx), '', dtype=object)
    for gid, t in gts.items():
        g = raster(t, x0, z0, 0.25, nx, nz)[0]
        better = np.isfinite(g) & (g > top); sup[better] = gid; top = np.where(better, g, top)
    f = top[np.isfinite(top)]
    c = {'variant': v, 'matrix': MATS[cid], 'window_m': [round(x0, 2), round(z0, 2), round(x1, 2), round(z1, 2)],
         'cityGroundTopY': {'min': round(float(f.min()), 4), 'max': round(float(f.max()), 4), 'cellsNoGround': int((~np.isfinite(top)).sum()), 'cells': int(top.size)},
         'suppliers': {s: int((sup == s).sum()) for s in set(sup.ravel()) if s}}
    dr = [t for k, t in nt.items() if 'drain' in k]
    if dr:
        P = dr[0].reshape(-1, 3)
        c['drainWorldBBox'] = [P.min(0).round(3).tolist(), P.max(0).round(3).tolist()]
    rep['city'][cid] = c
json.dump(rep, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for v in rep['variants']:
    r = rep['variants'][v]['LOD0']
    print(v, r['eaveBottomY'], r['dripLandingCells'], r['dripLandingOpenInsideLotM'], r['dripToNearestWall_m'], r['frontWallGaps_x'])
    if 'drainStone' in r: print('  drain', r['drainStone'])
for cid, c in rep['city'].items(): print(cid, c['cityGroundTopY'], c['suppliers'], c.get('drainWorldBBox'))
