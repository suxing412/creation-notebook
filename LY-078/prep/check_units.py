# LY-078 prep test harness (read-only; writes only a JSON report).
# Checks that a set of per-unit GLBs (cover / enclosure / south_gate / ground) is a lossless,
# non-overlapping partition of the bound original GLB, that each unit stays inside its spatial rule,
# and that the empty epigraph reserve stays empty in every unit.
#   python -I check_units.py --original <orig.glb> --units cover=a.glb enclosure=b.glb ... --out report.json
#   python -I check_units.py --original <orig.glb> --selftest --out selftest.json   (virtual split + negatives)
# Note: the virtual split exists only in memory for the self-test; it is not a delivered model.
import sys, json, argparse, collections
import numpy as np

_src = open(__file__.replace('check_units.py', 'measure_parts.py'), encoding='utf-8').read().replace('\nmain()\n', '\n')
P = {}
exec(compile(_src, 'mp', 'exec'), P)

RES = 1e-4  # 0.1 mm quantisation (the card's stated numeric tolerance)
UNITS = {
    'ground':     dict(mats={'LY_P01_earth'}, box=None),
    'cover':      dict(mats={'LY_P01_tile', 'LY_P01_plaster', 'LY_P01_timber'}, box=([-12.2, 0, -7.1], [12.2, 6.6, 7.1])),
    'south_gate': dict(mats={'LY_P01_timber'}, box=([-2.4, 0, 9.7], [2.4, 3.6, 10.4])),
    'enclosure':  dict(mats={'LY_P01_timber'}, box=([-14.2, 0, -10.2], [14.2, 1.8, 10.4])),
}
RESERVE = ([-8, 0.0, -3], [8, 3.9, 3])   # glTF frame; card extras say Blender x[-8,8], y[-3,3]


def tris_of(path):
    js, binc, sha, n = P['load'](path)
    out = []
    nonident = [x.get('name') for x in js['nodes'] if any(k in x for k in ('matrix', 'translation', 'rotation', 'scale'))]
    for node in js['nodes']:
        if 'mesh' not in node:
            continue
        for p in js['meshes'][node['mesh']]['primitives']:
            name = js['materials'][p['material']]['name']
            pos = P['acc'](js, binc, p['attributes']['POSITION']).astype(float)
            idx = P['acc'](js, binc, p['indices']).reshape(-1, 3).astype(int)
            for t in idx:
                out.append((name, pos[t]))
    return out, sha, n, nonident


def key(m, t):
    q = [tuple(np.round(v / RES).astype(np.int64).tolist()) for v in t]
    i = q.index(min(q))
    q = q[i:] + q[:i]  # rotation-canonical, keeps winding
    return (m, tuple(q))


def fp(tris):
    return collections.Counter(key(m, t) for m, t in tris)


def in_box(t, box, eps=1e-3):
    lo, hi = box
    return bool((t.min(0) >= np.array(lo) - eps).all() and (t.max(0) <= np.array(hi) + eps).all())


def tri_overlaps(t, box):
    lo, hi = box
    return bool((t.min(0) < np.array(hi) - 1e-6).all() and (t.max(0) > np.array(lo) + 1e-6).all())


def evaluate(orig_tris, units):
    rep = {'checks': {}}
    of = fp(orig_tris)
    uf = collections.Counter()
    for tl in units.values():
        uf.update(fp(tl))
    missing = of - uf
    extra = uf - of
    rep['checks']['C1_lossless_partition'] = {'pass': not missing and not extra,
                                              'missingTris': sum(missing.values()), 'extraTris': sum(extra.values())}
    seen = collections.Counter()
    for tl in units.values():
        for k in set(fp(tl)):
            seen[k] += 1
    dup = sum(1 for c in seen.values() if c > 1)
    rep['checks']['C2_no_triangle_in_two_units'] = {'pass': dup == 0, 'sharedKeys': dup}
    viol = {}
    for u, tl in units.items():
        r = UNITS.get(u)
        if r is None:
            continue
        viol[u] = sum(1 for m, t in tl if m not in r['mats'] or (r['box'] and not in_box(t, r['box'])))
    rep['checks']['C3_units_within_rules'] = {'pass': all(v == 0 for v in viol.values()), 'violations': viol}
    hits = {u: sum(1 for m, t in tl if m != 'LY_P01_earth' and tri_overlaps(t, RESERVE)) for u, tl in units.items()}
    rep['checks']['C4_epigraph_reserve_empty'] = {'pass': all(v == 0 for v in hits.values()), 'hits': hits, 'box': RESERVE}
    rep['checks']['C5_required_units_present'] = {'pass': all(len(units.get(u, [])) > 0 for u in UNITS),
                                                  'present': {u: len(units.get(u, [])) for u in UNITS}}
    rep['pass'] = all(c['pass'] for c in rep['checks'].values())
    return rep


def virtual_split(orig):
    units = {u: [] for u in UNITS}
    by_mat = collections.defaultdict(list)
    for m, t in orig:
        by_mat[m].append(t)
    for m, tl in by_mat.items():
        arr = np.array(tl)
        pos = arr.reshape(-1, 3)
        tris = np.arange(len(pos)).reshape(-1, 3)
        for g in P['parts'](pos, tris):
            v = arr[g].reshape(-1, 3)
            blo, bhi = v.min(0), v.max(0)

            def inside(b):
                return (blo >= np.array(b[0]) - 1e-3).all() and (bhi <= np.array(b[1]) + 1e-3).all()
            if m == 'LY_P01_earth':
                u = 'ground'
            elif m in ('LY_P01_tile', 'LY_P01_plaster') or inside(UNITS['cover']['box']):
                u = 'cover'
            elif inside(UNITS['south_gate']['box']) and bhi[1] > 1.8:  # fence-end posts (h=1.5) stay with enclosure
                u = 'south_gate'
            else:
                u = 'enclosure'
            units[u].extend((m, arr[i]) for i in g)
    return units


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--original', required=True)
    ap.add_argument('--units', nargs='*', default=[])
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    orig, osha, on, onon = tris_of(a.original)
    report = {'original': {'path': a.original, 'sha256': osha, 'bytes': on, 'tris': len(orig), 'nodesWithTransform': onon},
              'quantisation_m': RES}
    if a.selftest:
        vs = virtual_split(orig)
        cases = {'POS_virtual_split': evaluate(orig, vs)}
        n1 = dict(vs); n1.pop('south_gate')
        cases['NEG_drop_south_gate'] = evaluate(orig, n1)
        n2 = dict(vs); n2['cover'] = vs['cover'] + vs['cover'][:12]
        cases['NEG_duplicate_12_cover_tris'] = evaluate(orig, n2)
        stele = np.array([[[-0.5, 0.0, -0.2], [0.5, 0.0, -0.2], [0.5, 2.0, -0.2]],
                          [[-0.5, 0.0, -0.2], [0.5, 2.0, -0.2], [-0.5, 2.0, -0.2]]])
        n3 = dict(vs); n3['cover'] = vs['cover'] + [('LY_P01_plaster', t) for t in stele]
        cases['NEG_stele_face_in_reserve'] = evaluate(orig, n3)
        n4 = dict(vs); n4['south_gate'] = [(m, t + np.array([0, 0, 0.5])) if i < 5 else (m, t) for i, (m, t) in enumerate(vs['south_gate'])]
        cases['NEG_gate_tris_shifted_0.5m'] = evaluate(orig, n4)
        n5 = dict(vs); n5['enclosure'] = vs['enclosure'] + vs['south_gate']; n5['south_gate'] = []
        cases['NEG_gate_merged_into_enclosure'] = evaluate(orig, n5)
        report['selftest'] = {k: {'pass': v['pass'], 'failed': [c for c, r in v['checks'].items() if not r['pass']], 'checks': v['checks']}
                              for k, v in cases.items()}
        report['selftestOK'] = bool(cases['POS_virtual_split']['pass'] and not any(v['pass'] for k, v in cases.items() if k.startswith('NEG')))
        report['virtualSplitCounts'] = {u: len(t) for u, t in vs.items()}
    else:
        units = {}
        meta = {}
        for spec in a.units:
            u, path = spec.split('=', 1)
            t, s, n, nn = tris_of(path)
            units[u] = t
            meta[u] = {'path': path, 'sha256': s, 'bytes': n, 'tris': len(t), 'nodesWithTransform': nn}
        report['units'] = meta
        report.update(evaluate(orig, units))
    json.dump(report, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1,
              default=lambda o: o.tolist() if hasattr(o, 'tolist') else str(o))
    print(json.dumps({k: report[k] for k in report if k in ('selftestOK', 'pass', 'virtualSplitCounts')}))
    for k, v in report.get('selftest', {}).items():
        print(k, v['pass'], v['failed'])


main()
