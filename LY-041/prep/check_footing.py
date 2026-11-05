# LY-041 rerunnable checker (prep version). Read-only on the lab repo; writes only the --out JSON.
# Checks one placed courtyard's city-rendered bottom against the city ground set, and (optionally)
# a candidate footing/ground diff GLB in world coordinates against the measured gap mask.
#   python check_footing.py --lab D:/GitHub/creation-notebook-lab --id C02-010 [--layout calt]
#        [--candidate new.glb] [--dy-ground 0] [--drop-ground ground-south] [--matrix-shift 0] [--out r.json]
#   python check_footing.py --lab ... --selftest      (positive + 5 injected negatives, must all behave)
# Exit code 0 = all checks PASS, 1 = some FAIL. Heightfield on a grid (default 0.1 m) + edge splats:
# surface-level only, not solid collision, not GPU, not walking simulation.
import sys, os, json, argparse, hashlib
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbio import nodes_tris, raster, sha256, col_major

VAR = {'A': ('assets/r01/R01-A-LOD1-prototype.glb', 'assets/r01/R01-A-LOD0-prototype.glb', ['site_lot', 'site_neutral_lane', 'designed_hardpacked_activity_ground']),
       'B': ('assets/r01/R01-B-LOD1-prototype.glb', 'assets/r01/R01-B-LOD0-prototype.glb', ['site_lot', 'site_neutral_lane', 'designed_loading_yard']),
       'TC03': ('assets/d08/TC03-LOD1-prototype.glb', 'assets/d08/TC03-LOD0-prototype.glb', ['site_lot', 'site_neutral_lane']),
       'A2': ('assets/c02v/A2-LOD1-prototype.glb', 'assets/c02v/A2-LOD0-prototype.glb', ['site_lot', 'site_neutral_lane', 'designed_hardpacked_activity_ground']),
       'B2': ('assets/c02v/B2-LOD1-prototype.glb', 'assets/c02v/B2-LOD0-prototype.glb', ['site_lot', 'site_neutral_lane', 'designed_loading_yard']),
       'TC03-2': ('assets/c02v/TC03-2-LOD1-prototype.glb', 'assets/c02v/TC03-2-LOD0-prototype.glb', ['site_lot', 'site_neutral_lane', 'designed_front_apron', 'designed_side_passage', 'designed_rear_work_ground'])}
GROUNDS = [('ground-network-ground-stitched', 'assets/ground-atomic/network-ground-stitched.glb', (0, 0, 0)),
           ('ground-retained', 'assets/ground-atomic/retained.glb', (0, 0, 0)),
           ('ground-south', 'assets/ground-atomic/south.glb', (0, 0, 0)),
           ('ground-D08', 'assets/ground-atomic/D08.glb', (580, 0, -960))]
BASELINE = {  # bce3211 values this prep was measured against
    'C02-010': {'matrix': [1.0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1.0, 0, 531, 0, -818.45, 1],
                'LOD1': '277e9e73e8f2d8b8e07ec828671d37cc7c9e3f1653dcebfe4290c51de412d85d',
                'LOD0': '19b052022b2f6955e4a72f1a48280f7f8c229e11f001aa02ac95e357b890d9c7',
                'ground-south': '4313826ddf5fbe0c0d8dcb4983d6cdbd647713d49faa1980cd34f587a3273a0e'}}


def run(lab, cid, layout='calt', candidate=None, dy=0.0, drop=(), mshift=0.0, H=0.1, tol=0.005, extra_tris=None):
    city = os.path.join(lab, 'docs/cities/luoyang')
    rows = json.load(open(os.path.join(city, 'data/far44/instances-%s.json' % layout), encoding='utf-8'))['rows']
    row = [r for r in rows if r['id'] == cid][0]
    m16 = list(row['matrixGLTFColumnMajor']); m16[12] += mshift
    W = col_major(m16); Winv = np.linalg.inv(W)
    res = {'id': cid, 'layout': layout, 'variant': row['variant'], 'matrix': m16, 'checks': {}, 'sha': {}, 'grid_m': H, 'tol_m': tol}
    b = BASELINE.get(cid)
    res['checks']['C4_matrix_unchanged'] = {'pass': b is None or np.allclose(m16, b['matrix'], atol=1e-9), 'baseline': b and b['matrix']}
    gt = {}
    for gid, rel, tr in GROUNDS:
        if gid in drop:
            continue
        p = os.path.join(city, rel); res['sha'][rel] = sha256(p)
        M = np.eye(4); M[:3, 3] = (tr[0], tr[1] + dy, tr[2])
        gt[gid] = np.concatenate(list(nodes_tris(p, M).values()))
    cand = None
    if candidate:
        res['sha'][candidate] = sha256(candidate); cand = np.concatenate(list(nodes_tris(candidate).values()))
    if extra_tris is not None:
        cand = extra_tris if cand is None else np.concatenate([cand, extra_tris])
    for lod, rel in (('LOD1', VAR[row['variant']][0]), ('LOD0', VAR[row['variant']][1])):
        p = os.path.join(city, rel); res['sha'][rel] = sha256(p)
        nt = nodes_tris(p); excl = VAR[row['variant']][2]
        lot = nt['site_lot']; lot_top = float(lot[:, :, 1].max())
        rt = np.concatenate([t for k, t in nt.items() if k not in excl])
        allt = np.concatenate(list(nt.values())).reshape(-1, 3)
        x0, z0 = allt[:, 0].min() - 6, allt[:, 2].min() - 6
        nx = int(np.ceil((allt[:, 0].max() - allt[:, 0].min() + 12) / H)); nz = int(np.ceil((allt[:, 2].max() - allt[:, 2].min() + 12) / H))
        _, rbot, _ = raster(rt, x0, z0, H, nx, nz, edge_step=H / 2)
        lm = raster(lot, x0, z0, H, nx, nz)[2] > 0
        lane = raster(nt['site_neutral_lane'], x0, z0, H, nx, nz)[2] > 0
        foot = lm & (rbot <= lot_top + 0.05)
        gtop = np.full((nz, nx), -np.inf); sup = {}
        for gid, g in gt.items():
            gl = (np.c_[g.reshape(-1, 3), np.ones(g.shape[0] * 3)] @ Winv.T)[:, :3].reshape(-1, 3, 3)
            k = (gl[:, :, 0].max(1) >= x0) & (gl[:, :, 0].min(1) <= x0 + nx * H) & (gl[:, :, 2].max(1) >= z0) & (gl[:, :, 2].min(1) <= z0 + nz * H)
            if not k.any():
                continue
            top, _, hh = raster(gl[k], x0, z0, H, nx, nz)
            sup[gid] = int(((hh > 0) & lm).sum()); np.maximum(gtop, top, out=gtop)
        hasg = np.isfinite(gtop); gap = rbot - gtop
        fl = foot & hasg & (gap > tol); bu = foot & hasg & (gap < -tol); ng = foot & ~hasg
        r = {'footprintCells': int(foot.sum()), 'floating': int(fl.sum()), 'buried': int(bu.sum()), 'noGround': int(ng.sum()),
             'lotCoverage': round(float((lm & hasg).sum() / lm.sum()), 4), 'lotSuppliers': {k: v for k, v in sup.items() if v}}
        gapmask = fl | ng
        res['checks']['C1_footprint_contact_' + lod] = dict(r, **{'pass': r['floating'] == 0 and r['buried'] == 0 and r['noGround'] == 0})
        res['checks']['C2_lot_single_continuous_ground_' + lod] = {'pass': r['lotCoverage'] == 1.0 and len(r['lotSuppliers']) == 1, 'lotCoverage': r['lotCoverage'], 'suppliers': r['lotSuppliers']}
        if cand is not None:
            cl = (np.c_[cand.reshape(-1, 3), np.ones(cand.shape[0] * 3)] @ Winv.T)[:, :3].reshape(-1, 3, 3)
            ctop, _, ch = raster(cl, x0, z0, H, nx, nz)
            cm = ch > 0
            dil = gapmask.copy()
            dil[1:] |= gapmask[:-1]; dil[:-1] |= gapmask[1:]; dil[:, 1:] |= gapmask[:, :-1]; dil[:, :-1] |= gapmask[:, 1:]
            outside = cm & ~dil
            res['checks']['C3_candidate_only_on_measured_gap_' + lod] = {
                'pass': int(outside.sum()) == 0, 'candidateCells': int(cm.sum()), 'outsideGapCells': int(outside.sum()),
                'onLaneOrRoadCells': int((cm & lane).sum()), 'outsideLotCells': int((cm & ~lm).sum()), 'measuredGapCells': int(gapmask.sum())}
    res['pass'] = all(c['pass'] for c in res['checks'].values())
    return res


def plate(xmin, xmax, zmin, zmax, y0, y1):
    """closed axis-aligned box as (12,3,3) tris, world coords (negative-test helper only)."""
    v = np.array([[x, y, z] for x in (xmin, xmax) for y in (y0, y1) for z in (zmin, zmax)], float)
    f = [(0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3), (0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1), (2, 3, 7), (2, 7, 6)]
    return v[np.array(f)]


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--lab', required=True); ap.add_argument('--id', default='C02-010'); ap.add_argument('--layout', default='calt')
    ap.add_argument('--candidate'); ap.add_argument('--dy-ground', type=float, default=0.0); ap.add_argument('--drop-ground', action='append', default=[])
    ap.add_argument('--matrix-shift', type=float, default=0.0); ap.add_argument('--grid', type=float, default=0.1); ap.add_argument('--out')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        cases = [('positive_baseline', dict(), True),
                 ('neg_ground_raised_20mm(buried)', dict(dy=0.02), False),
                 ('neg_ground_lowered_20mm(floating)', dict(dy=-0.02), False),
                 ('neg_drop_ground_south(no support)', dict(drop=('ground-south',)), False),
                 ('neg_big_plate_over_lot_lane_neighbours', dict(extra_tris=plate(515, 547, -832, -800, 0.2, 0.22)), False),
                 ('neg_matrix_shift_0.1m', dict(mshift=0.1), False)]
        out = []
        for name, kw, expect in cases:
            r = run(a.lab, a.id, a.layout, H=a.grid, **kw)
            failed = [k for k, c in r['checks'].items() if not c['pass']]
            out.append({'case': name, 'expectPass': expect, 'gotPass': r['pass'], 'ok': r['pass'] == expect, 'failedChecks': failed})
            print(json.dumps(out[-1], ensure_ascii=False), flush=True)
        rep = {'selftest': out, 'allBehaved': all(o['ok'] for o in out)}
        if a.out:
            json.dump(rep, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        sys.exit(0 if rep['allBehaved'] else 1)
    r = run(a.lab, a.id, a.layout, a.candidate, a.dy_ground, tuple(a.drop_ground), a.matrix_shift, a.grid)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    if a.out:
        json.dump(r, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    sys.exit(0 if r['pass'] else 1)
