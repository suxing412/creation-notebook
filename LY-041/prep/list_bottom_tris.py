# LY-041 prep: enumerate the bottom triangles of the retained (city-rendered) nodes of one prototype.
# "bottom cap" = all 3 vertices at y <= base+eps and normal pointing down; "ground edge" = a non-cap
# triangle with >=2 vertices at the base (vertical sides standing on the ground).
# Triangle index = node-local index over its primitives in file order (same order glTF stores them).
# usage: python list_bottom_tris.py <glb> <out_json> <excluded,comma,list> [base_y]
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbio import nodes_tris, sha256

glb, out, excl = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
base = float(sys.argv[4]) if len(sys.argv) > 4 else 0.2
EPS = 1e-4
nt = nodes_tris(glb)
rep = {'file': os.path.basename(glb), 'sha256': sha256(glb), 'baseY': base, 'eps': EPS, 'excluded': excl, 'nodes': {}}
for name, t in nt.items():
    if name in excl:
        continue
    low = t[:, :, 1] <= base + EPS
    n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]); ln = np.linalg.norm(n, axis=1); ln[ln == 0] = 1
    ny = n[:, 1] / ln
    cap = low.all(1) & (ny < -0.99)
    up_at_base = low.all(1) & (ny > 0.99)
    edge = (low.sum(1) >= 2) & ~cap & ~up_at_base
    below = (t[:, :, 1] < base - EPS).any(1)
    capA = 0.5 * ln[cap].sum() if cap.any() else 0.0
    rep['nodes'][name] = {'tris': int(len(t)), 'bottomCapTris': np.nonzero(cap)[0].tolist(), 'bottomCapArea_m2': round(float(capA), 4),
                          'upFacingAtBaseTris': np.nonzero(up_at_base)[0].tolist(),
                          'groundEdgeTris': int(edge.sum()), 'trisBelowBase': int(below.sum())}
json.dump(rep, open(out, 'w', encoding='utf-8'), indent=1)
print(json.dumps({k: (v['tris'], len(v['bottomCapTris']), v['bottomCapArea_m2'], v['groundEdgeTris'], v['trisBelowBase'], len(v['upFacingAtBaseTris'])) for k, v in rep['nodes'].items()}))
