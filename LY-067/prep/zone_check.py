"""LY-067 prep: check gallery-A feet and future support pieces against the
LY-006 registry v1 (write zone LY-067:write:001, port gallery-A:feet:ground).
Read-only; writes only the <out.json> given.

Usage:
  python -I zone_check.py measure <out.json> <LY-006/registry> <gallery-A-LOD0.glb> <access-A-LOD0.glb>
      baseline facts: zone vs plinths, margins, max pad size, slab-vs-plinth area,
      port status, whether access-A has a registered frame.
  python -I zone_check.py gate <out.json> <LY-006/registry> <gallery-A-LOD0.glb> <support.glb> [<support_to_gallery.json>]
      production gate for a delivered support GLB (expressed in local:gallery-A,
      or mapped by a 4x4 row-major matrix {"support_to_gallery": [...]}).
  python -I zone_check.py selftest <out.json> <LY-006/registry> <gallery-A-LOD0.glb>
      synthetic AABB pieces (nothing written) proving PASS / FAIL paths.

Gate rules (G1..G5), all in local:gallery-A metres, tolerance EPS = 1e-4 m:
  G1 every support component AABB lies inside zone LY-067:write:001
  G2 no support component rises above y = 0 (zone top = plinth bottom = local grade)
  G3 per-component XZ area <= PAD_CAP_M2 (one plinth + 0.20 m each side = 0.90 x 0.90)
  G4 no component's XZ footprint overlaps >= 2 plinth footprints (anti display plate)
  G5 union XZ area of all components <= 16 * PAD_CAP_M2
G1-G5 only bound what LY-067 may write; actual support contact is check_feet.py.
"""
import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, __file__.replace('\\', '/').rsplit('/', 1)[0])
import measure_footings as mf  # noqa: E402

EPS = 1e-4
PAD_EXT = 0.20
ZONE_ID = 'LY-067:write:001'
PORT_ID = 'gallery-A:feet:ground'


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def registry(rdir):
    files = {k: os.path.join(rdir, k + '.json') for k in ('zones', 'ports', 'seats', 'ownership')}
    data = {k: json.load(open(v, encoding='utf-8')) for k, v in files.items()}
    zone = next(z for z in data['zones']['zones'] if z['zoneId'] == ZONE_ID)
    port = data['ports']['ports'][PORT_ID]
    seat = data['seats']['seats']['LY-067']
    frames = data['zones']['frames']
    hashes = {k: {'path': v.replace('\\', '/'), 'sha256': sha(v)} for k, v in files.items()}
    return zone, port, seat, frames, hashes


def plinths(glb):
    r = mf.analyse(glb)
    return r, [(f['foot_id'], np.array(f['plinth']['min']), np.array(f['plinth']['max'])) for f in r['feet']]


def xz_overlap(a0, a1, b0, b1):
    return (min(a1[0], b1[0]) - max(a0[0], b0[0]) > EPS) and (min(a1[2], b1[2]) - max(a0[2], b0[2]) > EPS)


def union_area(boxes, step=0.01):
    if not boxes:
        return 0.0
    mn = np.min([b[0] for b in boxes], 0); mx = np.max([b[1] for b in boxes], 0)
    xs = np.arange(mn[0] + step / 2, mx[0], step); zs = np.arange(mn[2] + step / 2, mx[2], step)
    X, Z = np.meshgrid(xs, zs)
    m = np.zeros(X.shape, bool)
    for b0, b1 in boxes:
        m |= (X >= b0[0]) & (X <= b1[0]) & (Z >= b0[2]) & (Z <= b1[2])
    return float(m.sum() * step * step)


def gate(zone, feet, pieces):
    z0, z1 = np.array(zone['box'][0]), np.array(zone['box'][1])
    cap = (0.5 + 2 * PAD_EXT) ** 2
    rows = []
    for name, b0, b1 in pieces:
        area = float((b1[0] - b0[0]) * (b1[2] - b0[2]))
        under = [fid for fid, p0, p1 in feet if xz_overlap(b0, b1, p0, p1)]
        r = {'piece': name, 'min': np.round(b0, 4).tolist(), 'max': np.round(b1, 4).tolist(),
             'xz_area_m2': round(area, 4), 'under_feet': under,
             'G1_in_zone': bool(np.all(b0 >= z0 - EPS) and np.all(b1 <= z1 + EPS)),
             'G2_below_grade': bool(b1[1] <= 0 + EPS),
             'G3_pad_cap': area <= cap + 1e-6,
             'G4_not_shared': len(under) <= 1}
        r['ok'] = r['G1_in_zone'] and r['G2_below_grade'] and r['G3_pad_cap'] and r['G4_not_shared']
        rows.append(r)
    ua = union_area([(b0, b1) for _, b0, b1 in pieces])
    g5 = ua <= 16 * cap + 1e-3
    feet_covered = sorted({f for r in rows for f in r['under_feet']})
    return {'pad_cap_m2': round(cap, 4), 'union_xz_area_m2': round(ua, 3), 'G5_union_cap_ok': g5,
            'pieces': rows, 'piece_fail_count': sum(not r['ok'] for r in rows),
            'feet_with_a_piece': len(feet_covered),
            'gate_ok': g5 and all(r['ok'] for r in rows)}


def comps_of(glb, M=None):
    js, binc, _, _ = mf.load(glb)
    out = []
    for ni, NM in mf.node_matrices(js).items():
        node = js['nodes'][ni]
        for pi, p in enumerate(js['meshes'][node['mesh']]['primitives']):
            P = mf.acc(js, binc, p['attributes']['POSITION']).astype(float)
            W = NM if M is None else np.array(M, float) @ NM
            P = (np.c_[P, np.ones(len(P))] @ W.T)[:, :3]
            I = mf.acc(js, binc, p['indices']).reshape(-1, 3).astype(np.int64)
            for r, tl in mf.components(P, I).items():
                vs = P[I[np.array(tl)].reshape(-1)]
                out.append((f"{node.get('name')}#{pi}.{r}", vs.min(0), vs.max(0)))
    return out


def measure(rdir, gallery, access):
    zone, port, seat, frames, hashes = registry(rdir)
    info, feet = plinths(gallery)
    z0, z1 = np.array(zone['box'][0]), np.array(zone['box'][1])
    pmin = np.min([p0 for _, p0, _ in feet], 0); pmax = np.max([p1 for _, _, p1 in feet], 0)
    xs = sorted({round(float((p0[0] + p1[0]) / 2), 4) for _, p0, p1 in feet})
    zs = sorted({round(float((p0[2] + p1[2]) / 2), 4) for _, p0, p1 in feet})
    acc_info = mf.analyse(access)
    pads_low = [{'part': n, 'min': b0.round(4).tolist(), 'max': b1.round(4).tolist()}
                for n, b0, b1 in comps_of(access) if b0[1] < -EPS]
    return {
        'registry': hashes,
        'zone': zone, 'port': port,
        'seat_frames': seat.get('frames'), 'seat_components': seat.get('components'),
        'frame_gallery_A': frames.get('local:gallery-A'),
        'frame_for_access_A_registered': any('access' in k for k in frames),
        'gallery': {'path': gallery.replace('\\', '/'), 'sha256': info['sha256'], 'feet': len(feet),
                    'plinth_union_min': pmin.round(4).tolist(), 'plinth_union_max': pmax.round(4).tolist(),
                    'post_x': xs, 'post_z': zs},
        'all_plinths_inside_zone_xz': bool(np.all(pmin[[0, 2]] >= z0[[0, 2]] - EPS) and np.all(pmax[[0, 2]] <= z1[[0, 2]] + EPS)),
        'zone_margin_beyond_plinths_m': {'x_neg': round(float(pmin[0] - z0[0]), 4), 'x_pos': round(float(z1[0] - pmax[0]), 4),
                                         'z_neg': round(float(pmin[2] - z0[2]), 4), 'z_pos': round(float(z1[2] - pmax[2]), 4)},
        'zone_y_range_m': [float(z0[1]), float(z1[1])],
        'zone_top_equals_plinth_bottom': abs(float(z1[1]) - float(pmin[1])) <= EPS,
        'plinth_edge_gap_m': {'x': round(xs[1] - xs[0] - 0.5, 4), 'z': round(zs[1] - zs[0] - 0.5, 4)},
        'pad_ext_used_m': PAD_EXT,
        'neighbour_pads_clear_m': {'x': round(xs[1] - xs[0] - 0.5 - 2 * PAD_EXT, 4), 'z': round(zs[1] - zs[0] - 0.5 - 2 * PAD_EXT, 4)},
        'zone_xz_area_m2': round(float((z1[0] - z0[0]) * (z1[2] - z0[2])), 3),
        'plinth_total_area_m2': round(float(sum((p1[0] - p0[0]) * (p1[2] - p0[2]) for _, p0, p1 in feet)), 3),
        'access_A': {'path': access.replace('\\', '/'), 'sha256': acc_info['sha256'],
                     'bbox_min': acc_info['bbox_min'], 'bbox_max': acc_info['bbox_max'],
                     'parts_below_y0': pads_low,
                     'relative_transform_to_gallery_A': None,
                     'note': 'no frame for access-A in LY-006 zones.frames; no node/extras transform in either GLB'},
    }


def selftest(rdir, gallery):
    zone, *_ = registry(rdir)
    info, feet = plinths(gallery)
    E = np.array([PAD_EXT, 0, PAD_EXT])
    pad = lambda p0, p1, ext=E, top=0.0, depth=0.3: (np.array([p0[0] - ext[0], top - depth, p0[2] - ext[2]]),
                                                     np.array([p1[0] + ext[0], top, p1[2] + ext[2]]))
    cases = {}
    cases['P1_per_foot_pads_0.20'] = [(f'pad-{fid}', *pad(p0, p1)) for fid, p0, p1 in feet]
    cases['N1_pads_0.25_outer_x_leaves_zone'] = [(f'pad-{fid}', *pad(p0, p1, np.array([0.25, 0, 0.20]))) for fid, p0, p1 in feet]
    cases['N2_zone_filling_slab'] = [('slab', np.array(zone['box'][0], float), np.array(zone['box'][1], float))]
    cases['N3_pad_above_grade_2cm'] = [(f'pad-{fid}', *pad(p0, p1, top=0.02 if fid == 'A-F07' else 0.0)) for fid, p0, p1 in feet]
    cases['N4_strip_under_two_feet'] = [(f'pad-{fid}', *pad(p0, p1)) for fid, p0, p1 in feet[2:]] + \
        [('strip', np.array([-6.45, -0.3, -3.6]), np.array([-5.55, 0.0, -0.9]))]
    expect = {'P1_per_foot_pads_0.20': True, 'N1_pads_0.25_outer_x_leaves_zone': False, 'N2_zone_filling_slab': False,
              'N3_pad_above_grade_2cm': False, 'N4_strip_under_two_feet': False}
    out = {}
    for k, pcs in cases.items():
        g = gate(zone, feet, pcs)
        out[k] = {'gate_ok': g['gate_ok'], 'expected': expect[k], 'ok': g['gate_ok'] == expect[k],
                  'piece_fail_count': g['piece_fail_count'], 'union_xz_area_m2': g['union_xz_area_m2'],
                  'first_fail': next(({kk: vv for kk, vv in r.items() if kk.startswith('G') or kk == 'piece'}
                                      for r in g['pieces'] if not r['ok']), None)}
    return {'gallery_sha256': info['sha256'], 'cases': out, 'all_selftests_ok': all(v['ok'] for v in out.values())}


if __name__ == '__main__':
    mode, out, rdir = sys.argv[1], sys.argv[2], sys.argv[3]
    if mode == 'measure':
        res = measure(rdir, sys.argv[4], sys.argv[5])
    elif mode == 'selftest':
        res = selftest(rdir, sys.argv[4])
    elif mode == 'gate':
        zone, port, seat, frames, hashes = registry(rdir)
        _, feet = plinths(sys.argv[4])
        M = json.load(open(sys.argv[6]))['support_to_gallery'] if len(sys.argv) > 6 else None
        res = gate(zone, feet, comps_of(sys.argv[5], M))
        res['registry'] = hashes
        res['support'] = {'path': sys.argv[5], 'sha256': sha(sys.argv[5])}
    else:
        raise SystemExit('mode must be measure | gate | selftest')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=lambda o: o.tolist() if hasattr(o, 'tolist') else str(o))
    print(json.dumps({k: res[k] for k in res if k in ('all_selftests_ok', 'gate_ok', 'all_plinths_inside_zone_xz', 'zone_margin_beyond_plinths_m')}, ensure_ascii=False))
