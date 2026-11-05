# LY-041 prep: exact (non-raster) check for the candidate courtyard C02-010 (A2).
# Every retained bottom vertex (y <= lotTop + 0.05) is mapped to world with the delivered matrix and
# tested against every ground triangle by exact 2D point-in-triangle; reports ground height under it.
# Also runs the same test at the 'original' layout matrix (negative / layout-dependence case),
# and lists lot-edge samples to show the lot is not a hole patch.
# usage: python measure_c02010_exact.py <lab_root> <out_json> [courtyard_id]
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbio import nodes_tris, sha256, col_major

LAB, OUT = sys.argv[1], sys.argv[2]; CID = sys.argv[3] if len(sys.argv) > 3 else 'C02-010'
CITY = os.path.join(LAB, 'docs/cities/luoyang')
VAR = {'A2': ('assets/c02v/A2-LOD0-prototype.glb', 'assets/c02v/A2-LOD1-prototype.glb', ['site_lot', 'site_neutral_lane', 'designed_hardpacked_activity_ground']),
       'A': ('assets/r01/R01-A-LOD0-prototype.glb', 'assets/r01/R01-A-LOD1-prototype.glb', ['site_lot', 'site_neutral_lane', 'designed_hardpacked_activity_ground']),
       'B': ('assets/r01/R01-B-LOD0-prototype.glb', 'assets/r01/R01-B-LOD1-prototype.glb', ['site_lot', 'site_neutral_lane', 'designed_loading_yard']),
       'B2': ('assets/c02v/B2-LOD0-prototype.glb', 'assets/c02v/B2-LOD1-prototype.glb', ['site_lot', 'site_neutral_lane', 'designed_loading_yard'])}
GROUNDS = [('ground-network-ground-stitched', 'assets/ground-atomic/network-ground-stitched.glb', (0, 0, 0)),
           ('ground-retained', 'assets/ground-atomic/retained.glb', (0, 0, 0)),
           ('ground-south', 'assets/ground-atomic/south.glb', (0, 0, 0)),
           ('ground-D08', 'assets/ground-atomic/D08.glb', (580, 0, -960))]


def heights_under(pts, tris):
    """for each world point (x,z) return list of y of every triangle covering it (exact barycentric)."""
    out = [[] for _ in range(len(pts))]
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    d = (b[:, 0] - a[:, 0]) * (c[:, 2] - a[:, 2]) - (c[:, 0] - a[:, 0]) * (b[:, 2] - a[:, 2])
    ok = np.abs(d) > 1e-12
    a, b, c, d = a[ok], b[ok], c[ok], d[ok]
    xmn = np.minimum(np.minimum(a[:, 0], b[:, 0]), c[:, 0]); xmx = np.maximum(np.maximum(a[:, 0], b[:, 0]), c[:, 0])
    zmn = np.minimum(np.minimum(a[:, 2], b[:, 2]), c[:, 2]); zmx = np.maximum(np.maximum(a[:, 2], b[:, 2]), c[:, 2])
    for i, (X, Z) in enumerate(pts):
        k = (xmn <= X + 1e-9) & (xmx >= X - 1e-9) & (zmn <= Z + 1e-9) & (zmx >= Z - 1e-9)
        if not k.any():
            continue
        A, B, C, D = a[k], b[k], c[k], d[k]
        l1 = ((B[:, 0] - X) * (C[:, 2] - Z) - (C[:, 0] - X) * (B[:, 2] - Z)) / D
        l2 = ((C[:, 0] - X) * (A[:, 2] - Z) - (A[:, 0] - X) * (C[:, 2] - Z)) / D
        l3 = 1 - l1 - l2
        m = (l1 >= -1e-9) & (l2 >= -1e-9) & (l3 >= -1e-9)
        out[i] = (l1[m] * A[m, 1] + l2[m] * B[m, 1] + l3[m] * C[m, 1]).tolist()
    return out


rep = {'tool': 'measure_c02010_exact.py', 'courtyard': CID, 'inputs': {}, 'cases': {}}
g = {}
for gid, rel, tr in GROUNDS:
    p = os.path.join(CITY, rel); rep['inputs'][rel] = sha256(p)
    M = np.eye(4); M[:3, 3] = tr
    g[gid] = np.concatenate(list(nodes_tris(p, M).values()))

for mode in ('calt', 'original'):
    rel = 'data/far44/instances-%s.json' % mode; rep['inputs'][rel] = sha256(os.path.join(CITY, rel))
    row = [r for r in json.load(open(os.path.join(CITY, rel), encoding='utf-8'))['rows'] if r['id'] == CID][0]
    W = col_major(row['matrixGLTFColumnMajor'])
    for lodi, lod in enumerate(('LOD0', 'LOD1')):
        relp = VAR[row['variant']][lodi]; excl = VAR[row['variant']][2]
        p = os.path.join(CITY, relp); rep['inputs'][relp] = sha256(p)
        nt = nodes_tris(p, W)
        lot = nt['site_lot']; lot_top = float(lot[:, :, 1].max())
        case = {'mode': mode, 'lod': lod, 'variant': row['variant'], 'matrix': row['matrixGLTFColumnMajor'], 'lotTopWorld': lot_top, 'nodes': {}}
        for name, t in nt.items():
            if name in excl:
                continue
            v = np.unique(t.reshape(-1, 3).round(6), axis=0)
            v = v[v[:, 1] <= lot_top + 0.05]
            if len(v) == 0:
                continue
            res = {'bottomVertices': int(len(v))}
            per = {}
            allh = []
            for gid, gt in g.items():
                hs = heights_under(v[:, [0, 2]], gt)
                cov = [max(h) for h in hs if h]
                if cov:
                    per[gid] = len(cov)
                allh.append([max(h) if h else None for h in hs])
            top = []
            for i in range(len(v)):
                c = [col[i] for col in allh if col[i] is not None]
                top.append(max(c) if c else None)
            gaps = np.array([v[i, 1] - top[i] for i in range(len(v)) if top[i] is not None])
            res['verticesWithGround'] = int(len(gaps)); res['verticesWithoutGround'] = int(sum(1 for t_ in top if t_ is None))
            res['groundSuppliers'] = per
            if len(gaps):
                res['gap_min'] = round(float(gaps.min()), 6); res['gap_max'] = round(float(gaps.max()), 6)
                res['floating_gt_5mm'] = int((gaps > 0.005).sum()); res['buried_lt_-5mm'] = int((gaps < -0.005).sum())
            case['nodes'][name] = res
        # lot perimeter + interior samples (is the lot over continuous ground?)
        xs = np.linspace(lot[:, :, 0].min(), lot[:, :, 0].max(), 37); zs = np.linspace(lot[:, :, 2].min(), lot[:, :, 2].max(), 49)
        P = np.array([[x, z] for x in xs for z in zs])
        tops = []
        for gid, gt in g.items():
            tops.append([max(h) if h else None for h in heights_under(P, gt)])
        tt = [max([c[i] for c in tops if c[i] is not None], default=None) for i in range(len(P))]
        hv = np.array([x for x in tt if x is not None])
        case['lotSamples'] = {'n': len(P), 'withGround': int(len(hv)), 'without': int(len(P) - len(hv)),
                              'groundTop_min': round(float(hv.min()), 6) if len(hv) else None, 'groundTop_max': round(float(hv.max()), 6) if len(hv) else None}
        rep['cases'][mode + '/' + lod] = case
        print(mode, lod, json.dumps(case['lotSamples']), {k: (v.get('gap_min'), v.get('gap_max'), v.get('verticesWithoutGround'), v.get('groundSuppliers')) for k, v in case['nodes'].items()}, flush=True)
json.dump(rep, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
