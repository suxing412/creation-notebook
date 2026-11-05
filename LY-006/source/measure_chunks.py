# LY-006: read two public chunks extracted from origin/luoyang-content
#   modeling-lab/review-batches/2026-11-04-city-visible/city-visible-web-handoff-v1-public.zip.part01..05
# (ZIP sha256 5895ef23...; extraction = plain concatenation + zipfile) and record:
#  * C_NE_APPROACH_LOCAL world extent and its two end ports (LY-039 / LY-084 consume them)
#  * mother-scene placement of the v2.1 frontage and the well (verifies frame local:frontage-v2.1)
# Also probes ground-network-ground-stitched in front of Pingcheng / Kaiyang (old ramp evidence).
# Usage: python -I measure_chunks.py <ne chunk> <market chunk> <lab docs> <out json>
import json, sys, os, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from glbio import read_glb, mesh_items, apply
from vray import VSampler

ne, mk, DOCS, OUT = sys.argv[1:5]
res = {}
g = read_glb(ne)
for i, n, w, p, t, a in mesh_items(g):
    if n == 'C_NE_APPROACH_LOCAL':
        V = apply(w, p)
        mn, mx = V.min(0), V.max(0)
        top = V[:, 1].max()
        s_end = V[np.isclose(V[:, 2], mn[2], atol=1e-3)]
        e_end = V[np.isclose(V[:, 0], mx[0], atol=1e-3)]
        res['ne'] = {'file_sha256': g['sha256'], 'bytes': g['size'], 'triangles': int(len(t)), 'aabb': [mn.round(4).tolist(), mx.round(4).tolist()],
                     'start': {'xRange': [float(s_end[:, 0].min()), float(s_end[:, 0].max())], 'z': float(mn[2]), 'topY': float(s_end[:, 1].max())},
                     'endE': {'zRange': [float(e_end[:, 2].min()), float(e_end[:, 2].max())], 'x': float(mx[0]), 'topY': float(e_end[:, 1].max())}}
g = read_glb(mk)
nodes = {}
for i, n, w, p, t, a in mesh_items(g):
    V = apply(w, p)
    if n.startswith('C_MARKET_ENTRY_V21_LOD0') or n.startswith('C_market_ground') or n == 'A_LOD0__short_liner':
        nodes[n] = [V.min(0).round(4).tolist(), V.max(0).round(4).tolist()]
res['motherScene'] = {'file_sha256': g['sha256'], 'bytes': g['size'], 'nodes': nodes,
                      'frontageLocalLOD0_aabb': 'x[-22.7,22.15] y[0,4.93] z[-12.3,11.45] (qa/glb-node-index.json street_frontage-LOD0)',
                      'impliedTranslation': None}
tile = nodes.get('C_MARKET_ENTRY_V21_LOD0__layout__LY_P01_tile__PBR')
if tile:
    res['motherScene']['impliedTranslation'] = [round(tile[0][0] + 22.7, 4), round(tile[1][1] - 4.93, 4), round(tile[0][2] + 12.3, 4)]
liner = nodes.get('A_LOD0__short_liner')
if liner:
    res['motherScene']['wellCentreWorld'] = [round((liner[0][0] + liner[1][0]) / 2, 4), round((liner[0][2] + liner[1][2]) / 2, 4)]
# old ramp probe on network ground in front of the two south gates
gn = read_glb(os.path.join(DOCS, 'cities/luoyang/assets/ground-atomic/network-ground-stitched.glb'))
T = np.concatenate([apply(w, p)[t] for i, n, w, p, t, a in mesh_items(gn)]); vs = VSampler(T, 4.0)
def W(tx, tz, yaw, x, z):
    c, s = np.cos(yaw), np.sin(yaw)
    return tx + c * x + s * z, tz - s * x + c * z
probes = []
for gate, (tx, tz, yaw) in {'pingcheng': (1622.80908203125, 13.259963035583496, -0.0207437532713328), 'kaiyang': (2010.3973388671875, 21.3011474609375, -0.020743634087871412)}.items():
    for xl in (-3.0, 0.0, 3.0, -7.9, 7.9):
        for zl in (-12.0, -8.0, 6.0, 8.0, 12.0, 20.0):
            wx, wz = W(tx, tz, yaw, xl, zl)
            hs = [y for y, ny in vs.heights(wx, wz) if ny > 0.5]
            probes.append({'gate': gate, 'local_xz': [xl, zl], 'world_xz': [round(wx, 4), round(wz, 4)], 'topY': round(max(hs), 5) if hs else None})
res['networkGroundProbes'] = {'file': 'docs/cities/luoyang/assets/ground-atomic/network-ground-stitched.glb', 'sha256': gn['sha256'], 'probes': probes}
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(res['ne'], indent=0)); print(res['motherScene']['impliedTranslation'], res['motherScene'].get('wellCentreWorld'))
for p in probes: print(p['gate'], p['local_xz'], p['topY'])
