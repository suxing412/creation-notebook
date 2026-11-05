# LY-048 prep: what lies just outside each lot edge of one placed courtyard (ground supplier and
# top y, other lots, own/other lanes) - read-only. usage: python boundary_strip.py <lab_root> <id> <out_json>
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure_closure as mc
from glb_read import node_tris, col_major

LAB, CID, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
CITY = os.path.join(LAB, 'docs/cities/luoyang')
REC = json.load(open(os.path.join(mc.HERE, 'city-courtyards.json'), encoding='utf-8'))
A = {r['id']: r for r in REC['assets']}
lots, lanes = {}, {}
for c in REC['courtyards']:
    nt = node_tris(os.path.join(CITY, A[c['asset']]['path']))
    M = col_major(c['matrix'])
    lots[c['id']] = mc.world_rect(mc.lot_rect(nt), M)
    p = nt['site_neutral_lane'].reshape(-1, 3)
    lanes[c['id']] = mc.world_rect((p[:, 0].min(), p[:, 0].max(), p[:, 2].min(), p[:, 2].max()), M)
gt = {}
for g in REC['grounds']:
    t = np.concatenate(list(node_tris(os.path.join(CITY, A[g['asset']]['path'])).values())) + np.array(g['position'], float)
    gt[g['id']] = t
c = next(r for r in REC['courtyards'] if r['id'] == CID)
M = col_major(c['matrix'])
nt = node_tris(os.path.join(CITY, A[c['asset']]['path']))
lx0, lx1, lz0, lz1 = mc.lot_rect(nt)
inside = lambda r, x, z: r[0] < x < r[1] and r[2] < z < r[3]
edges = {'front(+z)': [((x, lz1), (0, 1)) for x in np.linspace(lx0 + 0.5, lx1 - 0.5, 7)],
         'back(-z)': [((x, lz0), (0, -1)) for x in np.linspace(lx0 + 0.5, lx1 - 0.5, 7)],
         'left(-x)': [((lx0, z), (-1, 0)) for z in np.linspace(lz0 + 0.5, lz1 - 0.5, 9)],
         'right(+x)': [((lx1, z), (1, 0)) for z in np.linspace(lz0 + 0.5, lz1 - 0.5, 9)]}
out = {'courtyard': CID, 'lotRect_world': [round(v, 3) for v in lots[CID]], 'edges': {}}
for e, pts in edges.items():
    rows = []
    for (x, z), n in pts:
        for d in (0.25, 1.0, 2.5, 4.5):
            w = M @ np.array([x + n[0] * d, 0, z + n[1] * d, 1])
            g = mc.ground_top(gt, w[0], w[2])
            rows.append({'local_xz': [round(float(x), 2), round(float(z), 2)], 'd_out': d, 'world_xz': [round(float(w[0]), 3), round(float(w[2]), 3)],
                         'otherLot': [k for k, r in lots.items() if k != CID and inside(r, w[0], w[2])],
                         'lane': [k for k, r in lanes.items() if inside(r, w[0], w[2])],
                         'ground': None if g is None else [g[0], round(g[1], 4)]})
    out['edges'][e] = rows
    sup = sorted(set('NONE' if r['ground'] is None else '%s@%s' % tuple(r['ground']) for r in rows))
    print(e, 'ground', sup, 'otherLots', sorted(set(sum([r['otherLot'] for r in rows], []))), 'lanes', sorted(set(sum([r['lane'] for r in rows], []))))
# nearest neighbour lots and gaps
gaps = []
for k, r in lots.items():
    if k == CID: continue
    a = lots[CID]; ox = min(a[1], r[1]) - max(a[0], r[0]); oz = min(a[3], r[3]) - max(a[2], r[2])
    gaps.append((float(np.hypot(max(0, -ox), max(0, -oz))), k, round(ox, 3), round(oz, 3)))
gaps.sort(); out['nearestLots'] = [{'id': k, 'gap_m': round(g, 3), 'overlapX': ox, 'overlapZ': oz} for g, k, ox, oz in gaps[:4]]
print('nearest', out['nearestLots'])
json.dump(out, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
