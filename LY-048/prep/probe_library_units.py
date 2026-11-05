# LY-048 prep: run the same closure ring detector on library (not in city) units that could already
# provide service openings / low-wall closure, so they are not re-made. Read-only.
# Units with base y=0 are lifted by +0.2 so the shared slice heights apply. A synthetic site_lot
# (bbox of the unit's earth node) is injected; it is only the ring reference, not geometry.
# usage: python probe_library_units.py <lab_root> <out_json>
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure_closure as mc
from glb_read import node_tris, sha256

LAB, OUT = sys.argv[1], sys.argv[2]
LIB = os.path.join(LAB, 'docs/library/models')
UNITS = [('m-luoyang-household-service/files/service-enclosure-LOD0.glb', 'service-enclosure_earth', 0.2),
         ('m-luoyang-household-service/files/service-enclosure-LOD1.glb', 'service-enclosure_earth', 0.2),
         ('m-luoyang-wall-house-court/files/wall-house-LOD0.glb', 'wall-house_earth', 0.0),
         ('m-luoyang-wall-house-court/files/wall-house-LOD1.glb', 'wall-house_earth', 0.0),
         ('m-luoyang-service-court/files/service-A-LOD0.glb', 'service-A-static_earth', 0.2)]
mc.H = 0.025


def box(x0, x1, y0, y1, z0, z1):
    v = np.array([[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
                  [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]], float)
    f = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4),
         (2, 3, 7), (2, 7, 6), (1, 2, 6), (1, 6, 5), (3, 0, 4), (3, 4, 7)]
    return v[np.array(f)]

out = {'tool': 'probe_library_units.py', 'cell_m': mc.H, 'units': {}}
for rel, earth, lift in UNITS:
    p = os.path.join(LIB, rel); nt = node_tris(p)
    nt = {k: t + np.array([0, lift, 0]) for k, t in nt.items()}
    e = nt[earth].reshape(-1, 3)
    x0, x1, z0, z1 = e[:, 0].min(), e[:, 0].max(), e[:, 2].min(), e[:, 2].max()
    nt['site_lot'] = box(x0, x1, 0.0, 0.2, z0, z1)
    res, _ = mc.analyse_nt(nt, ['site_lot'])
    summ = {h: [(o['side'], o['from'], o['to'], o['width'], o['connectsYard']) for o in v['openings'] if o['connectsYard']]
            for h, v in res['heights'].items()}
    out['units'][rel] = {'sha256': sha256(p), 'lift_y': lift, 'ringRect_xz': [round(float(v), 3) for v in (x0, x1, z0, z1)],
                         'yardRunsByHeight': summ,
                         'yardArea_m2_at_0.953': res['heights']['0.953']['yardArea_m2']}
    print(rel, 'ring', [round(float(v), 2) for v in (x0, x1, z0, z1)])
    for h, v in summ.items():
        print('   ', h, v)
json.dump(out, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
