# LY-046 prep: (1) per-0.5 m segment along the TC03-2 / TC03 drain: distance to nearest roof drip edge;
# (2) A2 / TC03-2 front door gap: roof cover over the gap and the drip edge position in front of the door.
# Read-only. usage: python probe_door_drain.py <lab_root> <out_json>
import sys, os, json
import numpy as np
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbio import nodes_tris, raster, sha256
LAB, OUT = sys.argv[1], sys.argv[2]
C = os.path.join(LAB, 'docs/cities/luoyang')
H = 0.05
rep = {'tool': 'probe_door_drain.py', 'grid_m': H, 'inputs': {}}
def prep(rel):
    p = os.path.join(C, rel); rep['inputs'][rel] = sha256(p)
    nt = nodes_tris(p)
    P = np.concatenate([t.reshape(-1, 3) for t in nt.values()])
    x0, z0 = P[:, 0].min() - 1, P[:, 2].min() - 1
    nx, nz = int((P[:, 0].max() + 1 - x0) / H) + 1, int((P[:, 2].max() + 1 - z0) / H) + 1
    roof = np.concatenate([t for k, t in nt.items() if 'roof' in k])
    rt, rb, rh = raster(roof, x0, z0, H, nx, nz)
    cov = ndimage.binary_closing(rh > 0, iterations=2)
    edge = cov & ~ndimage.binary_erosion(cov)
    gx = x0 + (np.arange(nx) + .5) * H; gz = z0 + (np.arange(nz) + .5) * H
    return nt, x0, z0, nx, nz, rb, cov, edge, gx, gz
for rel in ('assets/c02v/TC03-2-LOD0-prototype.glb', 'assets/d08/TC03-LOD0-prototype.glb', 'assets/c02v/TC03-2-LOD1-prototype.glb'):
    nt, x0, z0, nx, nz, rb, cov, edge, gx, gz = prep(rel)
    d = [t for k, t in nt.items() if 'drain' in k][0].reshape(-1, 3)
    dist = ndimage.distance_transform_edt(~edge) * H
    xi = (gx >= d[:, 0].min()) & (gx <= d[:, 0].max())
    segs = []
    for za in np.arange(d[:, 2].min(), d[:, 2].max(), 0.5):
        zi = (gz >= za) & (gz < za + 0.5)
        sub = dist[np.ix_(zi, xi)]; c = cov[np.ix_(zi, xi)]
        segs.append([round(float(za), 2), round(float(sub.min()), 3), round(float(c.mean()), 2)])
    near = [s for s in segs if s[1] <= 0.3]
    # where is the nearest drip edge overall to drain centreline x=26.8: x of edge cells per z band
    rep[rel] = {'drainSegments_zStart_minDistToDripEdge_roofCoverFrac': segs,
                'segmentsWithDripEdgeWithin0.3m': len(near), 'segments': len(segs),
                'zWithDripWithin0.3m': [near[0][0], near[-1][0] + 0.5] if near else None}
for rel, front in (('assets/c02v/A2-LOD0-prototype.glb', 12.0), ('assets/c02v/TC03-2-LOD0-prototype.glb', 0.0), ('assets/c02v/A2-LOD1-prototype.glb', 12.0)):
    nt, x0, z0, nx, nz, rb, cov, edge, gx, gz = prep(rel)
    gap = (-4.65, -2.3) if 'A2' in rel else (7.85, 10.2)
    xi = (gx > gap[0]) & (gx < gap[1])
    col = cov[:, xi].any(1)
    # front-most covered z near the door, and eave bottom there
    zc = gz[col & (gz > front - 6) & (gz < front + 3)]
    rows = []
    for zz in np.arange(front - 3, front + 2.01, 0.25):
        j = int((zz - z0) / H)
        c = cov[j, xi]; b = rb[j, xi]
        rows.append([round(float(zz), 2), round(float(c.mean()), 2), round(float(np.nanmin(np.where(np.isfinite(b), b, np.nan))), 3) if np.isfinite(b).any() else None])
    rep[rel + '#door'] = {'doorGap_x': gap, 'lotFront_z': front, 'zProfile_coverFrac_eaveBottomY': rows,
                           'roofCoverMaxZ_overDoor': round(float(zc.max()), 3) if zc.size else None}
json.dump(rep, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for k, v in rep.items():
    if k in ('tool', 'grid_m', 'inputs'): continue
    if '#door' in k: print(k, v['roofCoverMaxZ_overDoor'], v['zProfile_coverFrac_eaveBottomY'])
    else: print(k, v['segmentsWithDripEdgeWithin0.3m'], '/', v['segments'], v['zWithDripWithin0.3m'], v['drainSegments_zStart_minDistToDripEdge_roofCoverFrac'][::6])
