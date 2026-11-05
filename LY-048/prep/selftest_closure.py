# LY-048 prep: self-test of the closure detector on synthetic closed boxes (no lab input).
# Cases (lot 18 x 24 m, lot top y=0.2, walls 0.5 m thick, 3.0 m high):
#   closed        : four walls, no gap                      -> expect yard NOT reachable, 0 yard runs
#   front_gate    : 2.95 m gap on +z                        -> expect exactly 1 yard run, width 2.95 +- 2 cells
#   side_slit_4cm : closed + 0.04 m slit on -x              -> documents the resolution limit: a gap <= 2 cells is
#                   NOT reported (outline rasterisation fills both cells). Expect 0 runs at 0.05 and 0.025.
#   side_gap_12cm : closed + 0.12 m gap on -x               -> expect 1 yard run at 0.05 and 0.025 (> 2 cells)
#   low_wall      : 1.2 m gap on +x filled by a 0.9 m high low wall -> expect yard run at y<=0.553 absent, present at y>=0.953
#   threshold     : 2.95 m gate with a 0.15 m high sill     -> expect run absent at 0.233/0.353? (sill top 0.35 -> absent at 0.233, present at 0.353)
#   leaf_closed   : 2.95 m gate closed by a 0.06 m leaf leaving a 0.01 m gap -> expect 0 runs at 0.05; at 0.025 also 0 (gap < cell)
# usage: python selftest_closure.py <out_json>
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure_closure as mc


def box(x0, x1, y0, y1, z0, z1):
    v = np.array([[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
                  [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]], float)
    f = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4),
         (2, 3, 7), (2, 7, 6), (1, 2, 6), (1, 6, 5), (3, 0, 4), (3, 4, 7)]
    return v[np.array(f)]


def walls(front_gap=None, left_gap=None, right_gap=None):
    t = []
    # back (-z) and the three others; gaps given as (a, b) along the edge
    t.append(box(-9, 9, 0.2, 3.2, -12, -11.5))
    def split(axis_lo, axis_hi, gap, mk):
        if gap is None:
            t.append(mk(axis_lo, axis_hi)); return
        a, b = gap
        if a > axis_lo: t.append(mk(axis_lo, a))
        if b < axis_hi: t.append(mk(b, axis_hi))
    split(-9, 9, front_gap, lambda a, b: box(a, b, 0.2, 3.2, 11.5, 12))
    split(-11.5, 11.5, left_gap, lambda a, b: box(-9, -8.5, 0.2, 3.2, a, b))
    split(-11.5, 11.5, right_gap, lambda a, b: box(8.5, 9, 0.2, 3.2, a, b))
    return np.concatenate(t)


def proto(extra):
    return {'site_lot': box(-9, 9, 0, 0.2, -12, 12), 'w': extra}


CASES = {
    'closed': (walls(), {}),
    'front_gate': (walls(front_gap=(-4.95, -2.0)), {}),
    'side_slit_4cm': (walls(left_gap=(0.0, 0.04)), {}),
    'side_gap_12cm': (walls(left_gap=(0.0, 0.12)), {}),
    'low_wall': (np.concatenate([walls(right_gap=(-1.0, 0.2)), box(8.5, 9, 0.2, 0.9 + 0.2, -1.0, 0.2)]), {}),
    'threshold': (np.concatenate([walls(front_gap=(-4.95, -2.0)), box(-4.95, -2.0, 0.2, 0.35, 11.5, 12)]), {}),
    'leaf_closed': (np.concatenate([walls(front_gap=(-4.95, -2.0)), box(-4.94, -2.01, 0.2, 2.6, 11.7, 11.76)]), {}),
}


def yard_runs(res):
    return {h: [(o['side'], o['from'], o['to'], o['width']) for o in v['openings'] if o['connectsYard']]
            for h, v in res['heights'].items()}


def main():
    out = {'tool': 'selftest_closure.py', 'results': {}}
    ok_all = True
    for cell in (0.05, 0.025):
        mc.H = cell
        for name, (tris, _) in CASES.items():
            res, _ = mc.analyse_nt(proto(tris), ['site_lot'])
            yr = yard_runs(res)
            n = {h: len(v) for h, v in yr.items()}
            if name == 'closed':
                ok = all(v == 0 for v in n.values())
            elif name == 'front_gate':
                ok = all(v == 1 for v in n.values()) and all(abs(r[0][3] - 2.95) <= 2 * cell for r in yr.values())
            elif name == 'side_slit_4cm':
                ok = all(v == 0 for v in n.values())  # expected miss: documents the limit, not a closure proof
            elif name == 'side_gap_12cm':
                ok = all(v == 1 for v in n.values())
            elif name == 'low_wall':
                ok = n['0.233'] == 0 and n['0.553'] == 0 and n['0.953'] == 0 + 0 and n['1.453'] == 1 and n['1.953'] == 1
            elif name == 'threshold':
                ok = n['0.233'] == 0 and n['0.353'] == 1 and n['0.953'] == 1
            elif name == 'leaf_closed':
                ok = all(v == 0 for v in n.values())
            ok_all &= ok
            out['results']['%s@%.3f' % (name, cell)] = {'pass': ok, 'yardRunCountByHeight': n, 'yardRuns': yr}
            print(name, cell, 'PASS' if ok else 'FAIL', n, flush=True)
    out['allPass'] = ok_all
    json.dump(out, open(sys.argv[1], 'w', encoding='utf-8'), indent=1)
    print('ALL PASS' if ok_all else 'SOME FAIL')


if __name__ == '__main__':
    main()
