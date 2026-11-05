# LY-041 prep measurement: courtyard bottoms (as the city renders them, excludeNodes removed)
# versus the city ground-atomic set, for all 44 placed courtyards. Read-only on the lab repo.
# usage: python measure_footing.py <lab_root> <out_json> [grid_m]
import sys, json, os, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbio import nodes_tris, raster, sha256, col_major

LAB = sys.argv[1]; OUT = sys.argv[2]; H = float(sys.argv[3]) if len(sys.argv) > 3 else 0.1
CITY = os.path.join(LAB, 'docs/cities/luoyang')
TOL = 0.005          # m, contact tolerance
BASE_BAND = 0.05     # m above the lot top that still counts as a footing element

VARIANTS = {  # from city-data.mjs assetRecords (bce3211)
    'A': ('assets/r01/R01-A-LOD1-prototype.glb', 'assets/r01/R01-A-LOD0-prototype.glb', ['site_lot', 'site_neutral_lane', 'designed_hardpacked_activity_ground']),
    'B': ('assets/r01/R01-B-LOD1-prototype.glb', 'assets/r01/R01-B-LOD0-prototype.glb', ['site_lot', 'site_neutral_lane', 'designed_loading_yard']),
    'TC03': ('assets/d08/TC03-LOD1-prototype.glb', 'assets/d08/TC03-LOD0-prototype.glb', ['site_lot', 'site_neutral_lane']),
    'A2': ('assets/c02v/A2-LOD1-prototype.glb', 'assets/c02v/A2-LOD0-prototype.glb', ['site_lot', 'site_neutral_lane', 'designed_hardpacked_activity_ground']),
    'B2': ('assets/c02v/B2-LOD1-prototype.glb', 'assets/c02v/B2-LOD0-prototype.glb', ['site_lot', 'site_neutral_lane', 'designed_loading_yard']),
    'TC03-2': ('assets/c02v/TC03-2-LOD1-prototype.glb', 'assets/c02v/TC03-2-LOD0-prototype.glb', ['site_lot', 'site_neutral_lane', 'designed_front_apron', 'designed_side_passage', 'designed_rear_work_ground']),
}
GROUNDS = [  # city-data.mjs nodes chapter 'terrain' (initial:false); D08 placed at [580,0,-960]
    ('ground-network-ground-stitched', 'assets/ground-atomic/network-ground-stitched.glb', (0, 0, 0)),
    ('ground-retained', 'assets/ground-atomic/retained.glb', (0, 0, 0)),
    ('ground-south', 'assets/ground-atomic/south.glb', (0, 0, 0)),
    ('ground-D08', 'assets/ground-atomic/D08.glb', (580, 0, -960)),
]


def bbox(t):
    if len(t) == 0:
        return None
    p = t.reshape(-1, 3); return [p.min(0).round(4).tolist(), p.max(0).round(4).tolist()]


def stats(a):
    a = a[np.isfinite(a)]
    if a.size == 0:
        return None
    return {'n': int(a.size), 'min': round(float(a.min()), 4), 'p05': round(float(np.percentile(a, 5)), 4), 'median': round(float(np.median(a)), 4), 'p95': round(float(np.percentile(a, 95)), 4), 'max': round(float(a.max()), 4)}


t0 = time.time()
report = {'tool': 'measure_footing.py', 'grid_m': H, 'contactTol_m': TOL, 'baseBand_m': BASE_BAND,
          'scope': 'surface heightfield on a %.2f m grid at cell centres plus edge splats; not solid collision, not GPU, not walking simulation' % H,
          'inputs': {}, 'prototypes': {}, 'courtyards': []}

# ---- prototypes
proto = {}
for v, (far, near, excl) in VARIANTS.items():
    for lod, rel in (('LOD1', far), ('LOD0', near)):
        p = os.path.join(CITY, rel)
        report['inputs'][rel] = sha256(p)
        nt = nodes_tris(p)
        missing = [e for e in excl if e not in nt]
        ret = {k: t for k, t in nt.items() if k not in excl}
        rt = np.concatenate(list(ret.values()))
        lot = nt.get('site_lot'); lot_top = float(lot[:, :, 1].max()) if lot is not None else None
        info = {'file': rel, 'nodes': {k: {'tris': int(len(t)), 'bbox': bbox(t), 'excluded': k in excl} for k, t in nt.items()},
                'excludeNodesMissing': missing, 'retainedTris': int(len(rt)), 'retainedBBox': bbox(rt),
                'siteLotBBox': bbox(lot) if lot is not None else None, 'siteLotTop': lot_top}
        # local raster over full prototype extent
        allt = np.concatenate(list(nt.values())); bb = bbox(allt)
        x0, z0 = bb[0][0] - 1.0, bb[0][2] - 1.0
        nx = int(np.ceil((bb[1][0] - bb[0][0] + 2) / H)); nz = int(np.ceil((bb[1][2] - bb[0][2] + 2) / H))
        _, rbot, rh = raster(rt, x0, z0, H, nx, nz, edge_step=H / 2)
        ltop, _, lh = raster(lot, x0, z0, H, nx, nz) if lot is not None else (None, None, None)
        exd = {k: raster(nt[k], x0, z0, H, nx, nz)[0] for k in excl if k in nt and k != 'site_lot'}
        lotmask = lh > 0
        foot = lotmask & (rbot <= (lot_top + BASE_BAND))
        # retained elements whose base lies below the lot top (would be sunk into the old lot)
        info['footprintCells'] = int(foot.sum()); info['lotCells'] = int(lotmask.sum())
        info['retainedBottomInLot'] = stats(rbot[lotmask & np.isfinite(rbot) & (rbot < lot_top + BASE_BAND)])
        info['retainedBelowLotTopCells'] = int((lotmask & (rbot < lot_top - TOL)).sum())
        info['removedDesignedGroundTop'] = {k: stats(t[np.isfinite(t)]) for k, t in exd.items()}
        proto[(v, lod)] = dict(x0=x0, z0=z0, nx=nx, nz=nz, rbot=rbot, lotmask=lotmask, foot=foot, lot_top=lot_top, exd=exd)
        report['prototypes'][v + '/' + lod] = info
print('prototypes', round(time.time() - t0, 1), 's', flush=True)

# ---- grounds (world, glTF axes)
gtris = {}
for gid, rel, tr in GROUNDS:
    p = os.path.join(CITY, rel); report['inputs'][rel] = sha256(p)
    M = np.eye(4); M[:3, 3] = tr
    gtris[gid] = np.concatenate(list(nodes_tris(p, M).values()))
    report.setdefault('grounds', {})[gid] = {'file': rel, 'tris': int(len(gtris[gid])), 'bbox': bbox(gtris[gid]), 'translation': tr}
print('grounds', round(time.time() - t0, 1), 's', flush=True)

# ---- placements (city default layout = calt; city-data nodes use instances-calt.json)
for mode in ('calt', 'original'):
    rel = 'data/far44/instances-%s.json' % mode
    report['inputs'][rel] = sha256(os.path.join(CITY, rel))
rows = json.load(open(os.path.join(CITY, 'data/far44/instances-calt.json'), encoding='utf-8'))['rows']

for r in rows:
    W = col_major(r['matrixGLTFColumnMajor']); Winv = np.linalg.inv(W)
    row = {'id': r['id'], 'variant': r['variant'], 'position': r['position'], 'rotationDegrees': r['rotationDegrees'], 'changedByCalt': r['changedByCalt'], 'sourceGroup': r['sourceGroup'], 'lods': {}}
    for lod in ('LOD1', 'LOD0'):
        P = proto[(r['variant'], lod)]
        x0, z0, nx, nz = P['x0'], P['z0'], P['nx'], P['nz']
        xmin, xmax, zmin, zmax = x0, x0 + nx * H, z0, z0 + nz * H
        gtop = np.full((nz, nx), -np.inf); layers = np.zeros((nz, nx), np.int32); supplier = {}
        for gid, gt in gtris.items():
            # transform ground into courtyard local frame, keep tris overlapping local raster box
            g = (np.c_[gt.reshape(-1, 3), np.ones(gt.shape[0] * 3)] @ Winv.T)[:, :3].reshape(-1, 3, 3)
            k = (g[:, :, 0].max(1) >= xmin) & (g[:, :, 0].min(1) <= xmax) & (g[:, :, 2].max(1) >= zmin) & (g[:, :, 2].min(1) <= zmax)
            if not k.any():
                continue
            top, _, hh = raster(g[k], x0, z0, H, nx, nz)
            has = hh > 0
            layers += has; np.maximum(gtop, top, out=gtop)
            supplier[gid] = int((has & P['lotmask']).sum())
        lm = P['lotmask']; foot = P['foot']; rbot = P['rbot']
        hasg = np.isfinite(gtop)
        gap = rbot - gtop
        fz = foot & hasg
        L = {
            'lotCells': int(lm.sum()), 'lotArea_m2': round(float(lm.sum() * H * H), 2),
            'lotGroundCoverage': round(float((lm & hasg).sum() / lm.sum()), 4),
            'lotNoGroundCells': int((lm & ~hasg).sum()), 'lotNoGroundArea_m2': round(float((lm & ~hasg).sum() * H * H), 2),
            'lotGroundTop': stats(gtop[lm & hasg]),
            'lotGroundSuppliers': supplier,
            'lotMultiFileGroundCells': int((lm & (layers > 1)).sum()),
            'footprintCells': int(foot.sum()),
            'footprintNoGroundCells': int((foot & ~hasg).sum()),
            'footprintGap': stats(gap[fz]),
            'footprintFloatingCells_gt_tol': int((fz & (gap > TOL)).sum()),
            'footprintBuriedCells_lt_minus_tol': int((fz & (gap < -TOL)).sum()),
            'footprintContactCells': int((fz & (np.abs(gap) <= TOL)).sum()),
            'openLotVoidCells': int((lm & ~hasg & ~np.isfinite(rbot)).sum()),
        }
        for k, et in P['exd'].items():
            m = np.isfinite(et) & hasg
            L['removedDesignedGround_vs_cityGround_' + k] = stats((et - gtop)[m])
            L['removedDesignedGroundCellsWithoutCityGround_' + k] = int((np.isfinite(et) & ~hasg).sum())
        row['lods'][lod] = L
    report['courtyards'].append(row)
    print(r['id'], r['variant'], 'cov', row['lods']['LOD0']['lotGroundCoverage'], 'gap', row['lods']['LOD0']['footprintGap'], round(time.time() - t0, 1), flush=True)

# ---- lot rectangle overlaps between neighbours (world AABB of site_lot)
rects = []
for r in rows:
    W = col_major(r['matrixGLTFColumnMajor']); b = report['prototypes'][r['variant'] + '/LOD1']['siteLotBBox']
    c = np.array([[x, 0, z, 1] for x in (b[0][0], b[1][0]) for z in (b[0][2], b[1][2])]) @ W.T
    rects.append((r['id'], c[:, 0].min(), c[:, 0].max(), c[:, 2].min(), c[:, 2].max()))
ov = []
for i in range(len(rects)):
    for j in range(i + 1, len(rects)):
        a, b = rects[i], rects[j]
        dx = min(a[2], b[2]) - max(a[1], b[1]); dz = min(a[4], b[4]) - max(a[3], b[3])
        if dx > 1e-6 and dz > 1e-6:
            ov.append({'a': a[0], 'b': b[0], 'overlap_m2': round(dx * dz, 3)})
report['lotWorldRects'] = [{'id': x[0], 'xmin': round(x[1], 4), 'xmax': round(x[2], 4), 'zmin': round(x[3], 4), 'zmax': round(x[4], 4)} for x in rects]
report['lotOverlaps'] = ov
report['seconds'] = round(time.time() - t0, 1)
json.dump(report, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('done', report['seconds'])
