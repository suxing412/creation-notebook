# LY-033 prep: verify that split A/B (local) + group offset == the A/B part of the city GLB, per tier.
# This fixes the transform LY-033 must use to place LY-031/032 door parts (local) into the city GLB.
# python -I frame_check.py <lab-docs-root> <out.json>
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbread as R

D = sys.argv[1]
U = os.path.join(D, 'model-library/updates/m-storage-functional/files')
C = os.path.join(D, 'cities/luoyang/progress-assets/granary-city-v1')
CITY = np.array([2285.714111328125, 0.0, -3673.468994140625])
OFF = {'A': np.array([-12.0, 0, -6.0]), 'B': np.array([12.0, 0, -6.0])}
out = []
for lod in (0, 1, 2):
    _, cps = R.prims(os.path.join(C, 'granary-city-LOD%d.glb' % lod))
    _, gps = R.prims(os.path.join(U, 'granary-group-LOD%d.glb' % lod))
    for wh in 'AB':
        _, sps = R.prims(os.path.join(U, 'granary-%s-LOD%d.glb' % (wh, lod)))
        S = np.concatenate([p['pos'][p['tris']] for p in sps]) + OFF[wh]
        lo, hi = S.reshape(-1, 3).min(0) - 1e-3, S.reshape(-1, 3).max(0) + 1e-3
        for label, ps, shift in (('group', gps, np.zeros(3)), ('city', cps, CITY)):
            T = np.concatenate([p['pos'][p['tris']] for p in ps if 'ground' not in (p['node'] or '')]) - shift
            inside = ((T.reshape(-1, 3) >= lo) & (T.reshape(-1, 3) <= hi)).all(1).reshape(-1, 3).all(1)
            Tin = T[inside]
            key = lambda X: np.sort(np.round(X.reshape(-1, 9), 3).view([('', float)] * 9).reshape(-1), axis=0)
            a, b = key(S), key(Tin)
            same = len(a) == len(b) and bool((a == b).all())
            # max vertex residual via nearest match on sorted triangles (only when counts equal)
            res = float(np.abs(np.sort(S.reshape(-1, 9), 0) - np.sort(Tin.reshape(-1, 9), 0)).max()) if len(a) == len(b) else None
            out.append(dict(lod=lod, warehouse=wh, target=label, splitTris=int(len(S)), targetTrisInBox=int(len(Tin)),
                            sameTriangleSetMm=same, maxSortedResidual=res))
            print(out[-1])
json.dump(out, open(sys.argv[2], 'w'), indent=1)
