# LY-071 prep: check LY-006 registry v1 S-BIYONG zones against the measured trial-fit layout.
# python -I zone_check.py <LY-006/registry/zones.json> <LY-006/registry/ports.json> <trial-fit-compare.json> <out.json>
# Frame: local:biyong = hall A local origin (registry: "hall A origin"); +X east, +Y up, -Z north (glTF).
# Trial-fit group origin O (ground y=0) sits at local:biyong (0,-1.2,0).
import json, sys, hashlib

zones_p, ports_p, trial_p, out_p = sys.argv[1:5]


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


Z = json.load(open(zones_p, encoding='utf-8'))
P = json.load(open(ports_p, encoding='utf-8'))
T = json.load(open(trial_p, encoding='utf-8'))
O_DY = -1.2  # trial group ground -> local:biyong


def box(mn, mx):
    return [list(map(float, mn)), list(map(float, mx))]


def shift(b, dy):
    return [[b[0][0], b[0][1] + dy, b[0][2]], [b[1][0], b[1][1] + dy, b[1][2]]]


def inter(a, b):
    lo = [max(a[0][i], b[0][i]) for i in range(3)]
    hi = [min(a[1][i], b[1][i]) for i in range(3)]
    d = [hi[i] - lo[i] for i in range(3)]
    if min(d) < 0:
        return 'disjoint', 0.0
    vol = d[0] * d[1] * d[2]
    return ('face-contact' if min(d) == 0 else 'volume-overlap'), round(vol, 6)


# measured parts, local:biyong
parts = {
    'hall-A (N=I)': box([-20.4, -1.2, -20.4], [20.4, 8.76, 20.4]),
}
# enclosure L quadrant: AABB of an L is a false positive, so use its two measured arm strips
# (base y=0 -> local:biyong y-1.2; centre line 68.0, base thickness 0.70: 67.65..68.35; arm ends at 4.0)
arms = [((4.0, -68.35), (68.35, -67.65)), ((67.65, -68.35), (68.35, -4.0))]


def rot_box(b, k):
    pts = [(x, z) for x in (b[0][0], b[1][0]) for z in (b[0][1], b[1][1])]
    out = []
    for x, z in pts:
        for _ in range(k):  # R_y(+90deg) in glTF: (x,z)->(z,-x)
            x, z = z, -x
        out.append((x, z))
    xs, zs = [p[0] for p in out], [p[1] for p in out]
    return (min(xs), min(zs)), (max(xs), max(zs))


for k in range(4):
    for a, arm in enumerate(arms):
        (x0, z0), (x1, z1) = rot_box(arm, k)
        parts[f'enclosure-L k={k} arm{a} (N=T(0,-1.2,0)R_y({90*k}))'] = box([x0, -1.2, z0], [x1, 0.8, z1])
# trial layout stand-ins (owned by LY-072/073), shifted into local:biyong
for n, b in T['layoutLocal_bbox'].items():
    if n.endswith('square_water_symbol'):
        y0, y1 = b[0][1] + O_DY, b[1][1] + O_DY  # ring 70..78 (LY-072 prep measurement), not a solid slab
        for i, (mn, mx) in enumerate([((70, -78), (78, 78)), ((-78, -78), (-70, 78)), ((-70, 70), (70, 78)), ((-70, -78), (70, -70))]):
            parts[f'trial {n} ring{i}'] = box([mn[0], y0, mn[1]], [mx[0], y1, mx[1]])
        continue
    parts['trial ' + n] = shift(b, O_DY)

zones = [z for z in Z['zones'] if z.get('site') == 'S-BIYONG']
rows = []
for z in zones:
    zb = z['box']
    for n, b in parts.items():
        rel, vol = inter(zb, b)
        if rel != 'disjoint':
            rows.append({'zone': z['zoneId'], 'seat': z['seat'], 'part': n, 'relation': rel, 'overlapVolume_m3': vol})

ly071_zone = [z for z in zones if z['seat'] == 'LY-071'][0]['box']
encl_in_ly071_zone = []
for n, b in parts.items():
    if n.startswith('enclosure'):
        rel, vol = inter(ly071_zone, b)
        encl_in_ly071_zone.append({'part': n, 'relation': rel})

port = P['ports']['biyong:hall-enclosure:ground']
out = {
    'tool': 'zone_check.py',
    'inputs': {'zones.json': sha(zones_p), 'ports.json': sha(ports_p), 'trial-fit-compare.json': sha(trial_p)},
    'frame': Z['frames']['local:biyong'],
    'trialGroupOrigin_in_local_biyong': [0.0, O_DY, 0.0],
    'partsBBox_local_biyong': parts,
    'S_BIYONG_zones': zones,
    'zonePartIntersections': rows,
    'enclosureVsLY071WriteZone': encl_in_ly071_zone,
    'findings': {
        'ly072_zone_x_range': [z['box'][0][0] for z in zones if z['seat'] == 'LY-072'] + [z['box'][1][0] for z in zones if z['seat'] == 'LY-072'],
        'ly073_zone_max_x': max(z['box'][1][0] for z in zones if z['seat'] == 'LY-073'),
        'enclosure_inner_face_m': 67.65,
        'trial_crossing_radial_range_m': [69.8, 78.2],
        'trial_water_symbol_ring_m': [70.0, 78.0],
        'gap_zone_to_trial_crossing_m': round(69.8 - max(z['box'][1][0] for z in zones if z['seat'] in ('LY-072', 'LY-073')), 3),
        'island_r20.4_to_67.65_owner': None,
    },
    'port_hall_enclosure_ground_v1': port,
}
json.dump(out, open(out_p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(out['findings'], ensure_ascii=False))
print(json.dumps(rows, ensure_ascii=False))
print(json.dumps(encl_in_ly071_zone, ensure_ascii=False))
