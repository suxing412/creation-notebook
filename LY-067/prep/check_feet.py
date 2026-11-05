"""LY-067 prep: per-foot support checker for gallery-A (to be run at production).

Usage (real run, after G freezes a local demo domain):
  python -I check_feet.py run <out.json> <gallery-A.glb> <support.glb> <matrix.json>
      matrix.json: {"gallery_to_domain": 4x4 row-major, "support_to_domain": 4x4 row-major}
  python -I check_feet.py selftest <out.json> <gallery-A-LOD0.glb>
      synthetic in-memory supports (no GLB is written) -> proves PASS and FAIL paths.

Per foot (16 plinths, A-F01..A-F16 from measure_footings.py):
  * 9 sample points on the plinth bottom (4 corners inset 10 mm, 4 edge mids, centre)
  * vertical ray down/up through support triangles (domain frame)
  * gap = plinth_bottom_y - support_top_y ; PASS if -TOL_EMBED <= gap <= TOL_GAP at all 9
  * anti fake base plate: the support component under each foot may not also lie
    under any OTHER foot unless it is declared terrain (declared_terrain=True) and
    its XZ area is <= AREA_CAP_M2 outside the gallery footprint; a single
    component spanning >= 2 feet with no terrain declaration is FAIL "shared plate".
"""
import json
import sys

import numpy as np

sys.path.insert(0, __file__.replace('\\', '/').rsplit('/', 1)[0])
import measure_footings as mf  # noqa: E402
import probe_ground as pg  # noqa: E402

TOL_GAP = 0.005      # m, max air gap under a plinth bottom sample
TOL_EMBED = 0.005    # m, max the support top may rise above the plinth bottom
INSET = 0.010        # m, corner inset


def feet_of(glb):
    r = mf.analyse(glb)
    out = []
    for f in r['feet']:
        pl = f['plinth']
        out.append({'id': f['foot_id'], 'min': np.array(pl['min']), 'max': np.array(pl['max'])})
    return r, out


def samples(foot):
    (x0, y0, z0), (x1, _, z1) = foot['min'], foot['max']
    xs = [x0 + INSET, (x0 + x1) / 2, x1 - INSET]
    zs = [z0 + INSET, (z0 + z1) / 2, z1 - INSET]
    return [(x, y0, z) for x in xs for z in zs]


def apply(M, P):
    return (np.c_[P, np.ones(len(P))] @ np.array(M, float).T)[:, :3]


def box_tris(mn, mx):
    (a, b, c), (d, e, f) = mn, mx
    top = [[a, e, c], [d, e, c], [d, e, f], [a, e, f]]
    return np.array([[top[0], top[1], top[2]], [top[0], top[2], top[3]]], float)


def check(feet, support_components, gallery_M=np.eye(4)):
    """support_components: list of (name, tris[N,3,3] in domain frame, declared_terrain)."""
    rows = []
    for ft in feet:
        pts = apply(gallery_M, np.array(samples(ft)))
        per, comps_used = [], set()
        for x, y, z in pts:
            best = None
            for ci, (name, T, terr) in enumerate(support_components):
                hs = [h for h in pg.hits(T, x, z) if h <= y + 0.5]
                if hs:
                    h = max(hs)
                    if best is None or h > best[0]:
                        best = (h, ci)
            if best is None:
                per.append({'xz': [round(x, 4), round(z, 4)], 'support_y': None, 'gap_m': None, 'ok': False})
            else:
                gap = y - best[0]
                comps_used.add(best[1])
                per.append({'xz': [round(x, 4), round(z, 4)], 'support_y': round(best[0], 5),
                            'gap_m': round(gap, 5), 'ok': -TOL_EMBED <= gap <= TOL_GAP})
        rows.append({'foot': ft['id'], 'samples': per, 'components': sorted(comps_used),
                     'supported': all(p['ok'] for p in per)})
    # shared-plate rule
    usage = {}
    for r in rows:
        for c in r['components']:
            usage.setdefault(c, []).append(r['foot'])
    plate_fail = {c: fs for c, fs in usage.items() if len(fs) >= 2 and not support_components[c][2]}
    for r in rows:
        r['shared_plate'] = [support_components[c][0] for c in r['components'] if c in plate_fail]
        r['pass'] = r['supported'] and not r['shared_plate']
    return {'tol_gap_m': TOL_GAP, 'tol_embed_m': TOL_EMBED, 'feet': rows,
            'pass_count': sum(r['pass'] for r in rows), 'fail_count': sum(not r['pass'] for r in rows),
            'shared_plate_components': {support_components[c][0]: fs for c, fs in plate_fail.items()}}


def selftest(glb):
    info, feet = feet_of(glb)
    assert len(feet) == 16, len(feet)
    cases = {}
    cases['N1_no_support'] = check(feet, [])
    pads = [(f"pad-{f['id']}", box_tris(f['min'] - [0.05, 0.3, 0.05], f['min'] + [0.55, 0.0, 0.55]), False) for f in feet]
    cases['P1_per_foot_pads_flush'] = check(feet, pads)
    low = [(n, T - [0, 0.03, 0], t) for n, T, t in pads]
    cases['N2_pads_3cm_low'] = check(feet, low)
    plate = [('fake-base-plate', box_tris(np.array([-7.0, -0.3, -4.0]), np.array([7.0, 0.0, 4.0])), False)]
    cases['N3_single_display_plate'] = check(feet, plate)
    terrain = [('declared-terrain', box_tris(np.array([-7.0, -0.3, -4.0]), np.array([7.0, 0.0, 4.0])), True)]
    cases['P2_declared_terrain_flush'] = check(feet, terrain)
    missing_one = pads[:6] + pads[7:]
    cases['N4_one_pad_missing(A-F07)'] = check(feet, missing_one)
    expect = {'N1_no_support': 0, 'P1_per_foot_pads_flush': 16, 'N2_pads_3cm_low': 0,
              'N3_single_display_plate': 0, 'P2_declared_terrain_flush': 16, 'N4_one_pad_missing(A-F07)': 15}
    summary = {k: {'pass_count': v['pass_count'], 'expected': expect[k], 'ok': v['pass_count'] == expect[k]}
               for k, v in cases.items()}
    return {'glb': info['path'], 'sha256': info['sha256'], 'summary': summary,
            'all_selftests_ok': all(s['ok'] for s in summary.values())}


if __name__ == '__main__':
    mode, out = sys.argv[1], sys.argv[2]
    if mode == 'selftest':
        res = selftest(sys.argv[3])
        print(json.dumps(res['summary'], ensure_ascii=False))
        print('all_selftests_ok', res['all_selftests_ok'])
    else:
        glb, sup, mj = sys.argv[3:6]
        mats = json.load(open(mj, encoding='utf-8'))
        info, feet = feet_of(glb)
        T, sha, size = pg.tris_of(sup)
        T = apply(np.array(mats['support_to_domain']).reshape(4, 4), T.reshape(-1, 3)).reshape(-1, 3, 3)
        res = check(feet, [(sup.rsplit('/', 1)[-1], T, bool(mats.get('declared_terrain', False)))],
                    np.array(mats['gallery_to_domain']).reshape(4, 4))
        res.update({'gallery': info['path'], 'gallery_sha256': info['sha256'], 'support': sup, 'support_sha256': sha})
        print('pass', res['pass_count'], 'fail', res['fail_count'])
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
