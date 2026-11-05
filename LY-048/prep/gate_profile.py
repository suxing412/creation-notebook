# LY-048 prep: clear-width profile through the front gate of one prototype, and city ground
# under the gate for one placed courtyard. Read-only. usage:
#   python gate_profile.py <lab_root> <courtyard_id> <out_json>
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure_closure as mc
from glb_read import node_tris, sha256, col_major

LAB, CID, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
CITY = os.path.join(LAB, 'docs/cities/luoyang')
REC = json.load(open(os.path.join(mc.HERE, 'city-courtyards.json'), encoding='utf-8'))
c = next(r for r in REC['courtyards'] if r['id'] == CID)
a = next(r for r in REC['assets'] if r['id'] == c['asset'])
M = col_major(c['matrix'])
mc.H = 0.02
res = {'courtyard': CID, 'asset': a['id'], 'matrix': c['matrix'], 'cell_m': mc.H, 'lods': {}}
for lod, rel in (('LOD0', a['nearPath']), ('LOD1', a['path'])):
    p = os.path.join(CITY, rel); nt = node_tris(p)
    keepl = [t for k, t in nt.items() if k not in a['excludeNodes']]
    keep = np.concatenate(keepl)
    lx0, lx1, lz0, lz1 = mc.lot_rect(nt)
    # gate mid from the 0.05 m run (front edge)
    full, _ = mc.analyse_nt(nt, a['excludeNodes'])
    g = [o for o in full['heights']['0.953']['openings'] if o['connectsYard']][0]
    gx = g['mid_xz'][0]
    prof = {}
    for h in (0.233, 0.953, 1.953):
        x0, z0 = gx - 4, lz1 - 4
        nx, nz = int(8 / mc.H), int(5 / mc.H)
        blk = mc.raster_block(keep, h, x0, z0, nx, nz)
        cx = x0 + (np.arange(nx) + 0.5) * mc.H; cz = z0 + (np.arange(nz) + 0.5) * mc.H
        blk, _ = mc.fill_solid_interiors(blk, keepl, h, cx, cz)
        rows = []
        for depth in (0.05, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0):
            k = int(np.argmin(abs(cz - (lz1 - depth))))
            i = int(np.argmin(abs(cx - gx)))
            if blk[i, k]:
                rows.append({'depth_in_m': depth, 'clear': 0.0}); continue
            l = i; r = i
            while l > 0 and not blk[l - 1, k]: l -= 1
            while r < nx - 1 and not blk[r + 1, k]: r += 1
            rows.append({'depth_in_m': depth, 'from_x': round(float(cx[l] - mc.H / 2), 3), 'to_x': round(float(cx[r] + mc.H / 2), 3),
                         'clear': round(float((r - l + 1) * mc.H), 3), 'hitsDomainEdge': bool(l == 0 or r == nx - 1)})
        prof[str(h)] = rows
    vh = mc.vertical_hits(keep, gx, lz1 - 0.25)
    res['lods'][lod] = {'file': rel, 'sha256': sha256(p), 'gateRun_0.05': g, 'clearWidthProfile': prof,
                        'verticalHits_gateMid_0.25in': vh,
                        'clearHeightAboveLotTop': round(min([y for y in vh if y > 0.25] or [float('nan')]) - 0.2, 3)}
# city ground under the gate (all ground atomics, positions applied)
gt = {}
for gnode in REC['grounds']:
    ga = next(r for r in REC['assets'] if r['id'] == gnode['asset'])
    t = np.concatenate(list(node_tris(os.path.join(CITY, ga['path'])).values())) + np.array(gnode['position'], float)
    gt[gnode['id']] = t
g = res['lods']['LOD0']['gateRun_0.05']
samples = []
for dx in (-1.2, -0.6, 0.0, 0.6, 1.2):
    for dz in (-2.0, -1.0, -0.25, 0.25, 1.0, 2.0, 4.0):
        lx, lz = g['mid_xz'][0] + dx, 12.0 + dz if a['id'] in ('courtyard-A', 'courtyard-B', 'courtyard-A2', 'courtyard-B2') else 0.0 + dz
        w = M @ np.array([lx, 0, lz, 1])
        top = mc.ground_top(gt, w[0], w[2])
        samples.append({'local_xz': [round(lx, 3), round(lz, 3)], 'world_xz': [round(float(w[0]), 3), round(float(w[2]), 3)],
                        'ground': None if top is None else {'supplier': top[0], 'top_y': round(top[1], 4)}})
res['groundUnderGate'] = samples
res['groundLoadedIn'] = {gn['id']: {'chapter': gn['chapter'], 'initial': gn['initial']} for gn in REC['grounds']}
json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
for lod, v in res['lods'].items():
    print(lod, 'clearH', v['clearHeightAboveLotTop'], 'vh', v['verticalHits_gateMid_0.25in'])
    for h, rows in v['clearWidthProfile'].items():
        print('  h', h, [(r['depth_in_m'], r['clear']) for r in rows])
print('ground', sorted(set((s['ground'] or {}).get('supplier', 'NONE') + '@' + str((s['ground'] or {}).get('top_y')) for s in samples)))
