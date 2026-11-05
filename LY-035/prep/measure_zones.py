# LY-035 prep (read-only): existing modern explanatory zones (optional overlay, not physical paving)
# vs provisional straight route corridors and existing cargo proxies.
# Usage: python -X utf8 measure_zones.py qa/forecourt-measure.json qa/zones-measure.json
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbread as G

LAB = 'D:/GitHub/creation-notebook-lab/docs/'
OV = LAB + 'model-library/assets/optional-functional-overlay-local.glb'
CON = LAB + 'model-library/assets/storage-origin-contract.json'
F = json.load(open(sys.argv[1], encoding='utf-8'))
out = sys.argv[2]
anchor = json.load(open(CON, encoding='utf-8'))['anchorFromActualGLB']
parts, js = G.world_triangles(OV)
zones = {}
for p in parts:
    t = p['tris'].reshape(-1, 3)
    lo, hi = t.min(0), t.max(0)
    zones[p['node']] = {'local': [lo.round(4).tolist(), hi.round(4).tolist()],
                        'world_xz': [[round(lo[0] + anchor[0], 4), round(lo[2] + anchor[2], 4)], [round(hi[0] + anchor[0], 4), round(hi[2] + anchor[2], 4)]],
                        'size_m': [round(float(hi[0] - lo[0]), 3), round(float(hi[2] - lo[2]), 3)], 'yRange': [round(float(lo[1]), 4), round(float(hi[1]), 4)]}
RES = 0.05
rp = F['receiving']['northPort_provisional']


def seg_dist(px, pz, a, b):
    vx, vz = b[0] - a[0], b[2] - a[2]
    t = np.clip(((px - a[0]) * vx + (pz - a[2]) * vz) / (vx * vx + vz * vz), 0, 1)
    return np.hypot(px - (a[0] + t * vx), pz - (a[2] + t * vz))
R = {'overlay': {'path': OV, 'sha256': G.sha256(OV), 'anchor': anchor, 'meaning': 'modern explanatory zones only (storage-interface.json overlayMeaning); not loaded in city'},
     'zones': zones, 'corridorOverlap': {}}
for name, z in zones.items():
    (x0, z0), (x1, z1) = z['world_xz']
    gx, gz = np.meshgrid(np.arange(x0 + RES / 2, x1, RES), np.arange(z0 + RES / 2, z1, RES), indexing='ij')
    row = {}
    for width in (0.9, 1.8):
        inA = seg_dist(gx, gz, rp, F['A']['footPort_provisional']) <= width / 2
        inB = seg_dist(gx, gz, rp, F['B']['footPort_provisional']) <= width / 2
        row['corridor%.1f' % width] = {'zoneArea_m2': round(gx.size * RES * RES, 2),
                                       'overlapA_m2': round(float(inA.sum()) * RES * RES, 2),
                                       'overlapB_m2': round(float(inB.sum()) * RES * RES, 2),
                                       'freeOfBothCorridors_m2': round(float((~inA & ~inB).sum()) * RES * RES, 2)}
    bags = []
    for bn, (blo, bhi) in F['receiving']['bags'].items():
        if blo[0] >= x0 - 1e-6 and bhi[0] <= x1 + 1e-6 and blo[2] >= z0 - 1e-6 and bhi[2] <= z1 + 1e-6:
            bags.append(bn)
    row['cargoProxiesInside'] = bags
    R['corridorOverlap'][name] = row
json.dump(R, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(R, ensure_ascii=False, indent=1))
