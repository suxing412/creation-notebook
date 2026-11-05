# LY-047 prep self-test: proves the checks in measure_ly047.py fail on known-bad inputs. Read-only.
# usage: python -I selftest_ly047.py <lab_root> <out.json>
import sys, os, json
LAB, OUT = sys.argv[1], sys.argv[2]
sys.argv = [sys.argv[0], LAB, OUT]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import measure_ly047 as m
import glbio, citydata

cd = citydata.load(os.path.join(m.CITY, 'city-data.mjs'))
G = m.ground_tris()
grid = m.Grid()
res = {'tool': 'selftest_ly047.py', 'cases': {}}

W0 = glbio.node_tris(m.rel(m.WORKSHED[0]))
WT = np.concatenate([T for T, ml in W0.values()])
eav = (WT[:, :, 0].min(), WT[:, :, 0].max(), WT[:, :, 2].min(), WT[:, :, 2].max())
postc = [c.reshape(-1, 3) for c in m.comps(W0['workshed_timber'][0]) if c.reshape(-1, 3)[:, 1].min() < 1e-4]
c010 = [n for n in cd['nodes'] if n['id'] == 'C02-010'][0]
M010 = glbio.matrix_from_city(c010['matrix'])
keepA, _ = m.load_proto(m.PROTO['A2'][0], m.EXCLUDE['A2'])
occ_any = grid.raster(np.concatenate(list(keepA.values())), m.FLOOR + 0.05, None)


def post_gaps(origin, yoff):
    gaps = []
    for c in postc:
        b = c[np.abs(c[:, 1] - c[:, 1].min()) < 1e-5]
        for p in b:
            w = M010 @ np.array([p[0] + origin[0], p[1] + yoff, p[2] + origin[1], 1.0])
            y, _ = m.ground_y(G, w[0], w[2])
            gaps.append(None if y is None else float(w[1] - y))
    return gaps


def eaves_hit(origin):
    e = (eav[0] + origin[0], eav[1] + origin[0], eav[2] + origin[1], eav[3] + origin[1])
    return bool((m.rect_mask(grid, e) & occ_any).any()), [round(float(x), 3) for x in e]


REF = (-4.5, 7.5)  # a feasible yaw-0 placement from measure-ly047.json (no LY-044 stove conflict)
g_ok = post_gaps(REF, 0.2); g_bad = post_gaps(REF, 0.0)
res['cases']['P1_ref_placement_offset_0.2'] = {'expect': 'pass', 'gap_min': min(g_ok), 'gap_max': max(g_ok), 'eaves_hit': eaves_hit(REF)[0],
                                               'pass': max(abs(x) for x in g_ok) <= 0.005 and not eaves_hit(REF)[0]}
res['cases']['N1_no_y_offset'] = {'expect': 'fail(buried)', 'gap_min': min(g_bad), 'gap_max': max(g_bad),
                                  'detected': min(g_bad) < -0.005}
hit, rect = eaves_hit((-4.5, 0.0))
res['cases']['N2_eaves_into_west_house'] = {'expect': 'fail(eaves hit)', 'eaves_rect': rect, 'detected': hit}

# N3: co-loading workshed into a B court whose own shed already exists
keepB, _ = m.load_proto(m.PROTO['B'][0], m.EXCLUDE['B'])
occB = grid.raster(np.concatenate(list(keepB.values())), m.FLOOR + 0.05, None)
best = None
for cx in np.arange(-9, 9.01, 0.5):
    for cz in np.arange(-12, 12.01, 0.5):
        e = (eav[0] + cx, eav[1] + cx, eav[2] + cz, eav[3] + cz)
        if e[0] < -8.7 or e[1] > 8.7 or e[2] < -11.7 or e[3] > 11.7:
            continue
        if not (m.rect_mask(grid, e) & occB).any():
            best = (cx, cz)
            break
    if best:
        break
sb = m.SHED_BOX['B']
res['cases']['N3_coload_second_shed_in_B'] = {
    'expect': 'fail(rule: one shed candidate per court; B already has in-place shed)',
    'free_slot_found_for_geometry': best is not None, 'slot': best,
    'in_place_shed_present': True,
    'exclusivity_ok': None,
    'note': 'geometry alone may fit; the exclusivity rule (test-plan T5) must reject it, not the clearance test'}


def exclusivity_ok(variant, added_sheds):
    # one shed/storage candidate per court: B/B2 already carry an in-place shed merged into their nodes
    return (1 if variant in ('B', 'B2') else 0) + len(added_sheds) <= 1


res['cases']['N3_coload_second_shed_in_B']['exclusivity_ok'] = exclusivity_ok('B', ['workshed'])
res['cases']['N3_coload_second_shed_in_B']['detected'] = not exclusivity_ok('B', ['workshed'])
res['cases']['P2_workshed_alone_in_A2'] = {'expect': 'pass', 'pass': exclusivity_ok('A2', ['workshed'])}
res['cases']['P3_B_inplace_only'] = {'expect': 'pass', 'pass': exclusivity_ok('B', [])}

# N4: block a bin front with a 0.6 m box -> access distance on that side must exceed REACH
els = m.shed_elements(keepB, sb)
binv = [e for e in els if e['kind'] == 'storage_bin'][0]
allT = np.concatenate(list(keepB.values()))
band = grid.raster(allT, *m.BAND)
mn, mx = binv['min'], binv['max']
blk = m.rect_mask(grid, (mx[0], mx[0] + 0.9, mn[2] - 0.3, mx[2] + 0.3))
band2 = band | blk
r0, _, _ = m.reachable(grid, band, m.R_WALK, m.GATE['B'])
r1, _, _ = m.reachable(grid, band2, m.R_WALK, m.GATE['B'])
a0 = m.face_access(grid, r0, binv)['+x']; a1 = m.face_access(grid, r1, binv)['+x']
res['cases']['N4_bin_front_blocked'] = {'expect': 'fail(+x access > REACH)', 'before': a0, 'after': a1,
                                        'detected': (a1 is None) or (a1 > m.REACH)}
ok = all(v['pass'] for k, v in res['cases'].items() if k.startswith('P')) and all(v.get('detected') for k, v in res['cases'].items() if k.startswith('N'))
res['allBehaved'] = bool(ok)
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=float)
print(json.dumps(res, ensure_ascii=False, indent=1, default=float))
