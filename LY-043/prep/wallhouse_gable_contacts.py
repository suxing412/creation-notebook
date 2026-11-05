# LY-043 prep: in the wall-house study, count the closed opposite-facing contacts between the non-box
# gable pieces and the wall-box tops (the card's "wall top vs gable bottom" internal interfaces).
# usage: python -I wallhouse_gable_contacts.py <docs_root>
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from nodegeo import node_geometry
from boxes import boxes_from, rects
from glbio import sha256
out = {}
for lod in ('LOD0', 'LOD1', 'LOD2'):
    rel = 'library/models/m-luoyang-wall-house-court/files/wall-house-%s.glb' % lod
    t, n = node_geometry(os.path.join(sys.argv[1], rel))['wall-house_earth']
    b, left, res, fl = boxes_from(t, n)
    boxed = set(i for x in b for i in x['tris'])
    rest = np.array([i for i in range(len(t)) if i not in boxed])
    fr, _, _ = rects(t[rest])                       # axis-aligned rectangles among non-box pieces
    bottoms = [f for f in fr if f['axis'] == 1 and f['sign'] == -1]
    tops = [(x, x['max'][1]) for x in b]
    pairs = []
    for f in bottoms:
        for x, ytop in tops:
            if abs(ytop - f['c']) > 1e-4:
                continue
            lo = np.maximum(f['lo'], x['min'][[0, 2]]); hi = np.minimum(f['hi'], x['max'][[0, 2]])
            if (hi - lo > 1e-4).all():
                pairs.append({'y': round(f['c'], 4), 'gableBottom': [f['lo'].round(4).tolist(), f['hi'].round(4).tolist()],
                              'wallTop': [x['min'].round(4).tolist(), x['max'].round(4).tolist()], 'area_m2': round(float(np.prod(hi - lo)), 4),
                              'fullyCovered': bool(np.allclose(lo, f['lo'], atol=1e-4) and np.allclose(hi, f['hi'], atol=1e-4))})
    out[lod] = {'sha256': sha256(os.path.join(sys.argv[1], rel)), 'boxes': len(b), 'nonBoxTriangles': int(len(rest)),
                'nonBoxBottomRects': len(bottoms), 'gableBottomOnWallTopPairs': len(pairs), 'pairs': pairs}
    print(lod, len(b), len(rest), len(bottoms), len(pairs), [ (p['area_m2'], p['fullyCovered']) for p in pairs])
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wallhouse-gable-contacts.json'), 'w', encoding='utf-8'), indent=1)
