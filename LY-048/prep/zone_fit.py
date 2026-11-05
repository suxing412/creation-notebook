# LY-048 prep: fit the host prototype's wall ring / gate frame against the LY-006 registry v1
# write zones (court:C02-010 frame = prototype-local, +z = front/south). Read-only.
# Surface triangles only (no solid test). Reports, per node, how many triangle vertices fall
# inside LY-048 zones, inside other seats' zones, or in no zone; plus wall-band z/x extents.
# usage: python zone_fit.py <lab_root> <ly006_zones_json> <out_json> [asset=courtyard-A2]
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glb_read import node_tris, sha256

PROTO = {
    'courtyard-A2': 'docs/cities/luoyang/assets/c02v/A2-LOD0-prototype.glb',
}
EXCL = {'site_lot', 'site_neutral_lane', 'designed_hardpacked_activity_ground'}


def inbox(p, b, eps=1e-6):
    lo, hi = np.array(b[0]), np.array(b[1])
    return np.all((p >= lo - eps) & (p <= hi + eps), axis=1)


def main():
    lab, zpath, out = sys.argv[1], sys.argv[2], sys.argv[3]
    asset = sys.argv[4] if len(sys.argv) > 4 else 'courtyard-A2'
    glb = os.path.join(lab, PROTO[asset])
    zones = [z for z in json.load(open(zpath, encoding='utf-8'))['zones'] if z.get('frame') == 'court:C02-010']
    own = [z for z in zones if z['seat'] == 'LY-048']
    nt = node_tris(glb)
    res = {'tool': 'zone_fit.py', 'glb': PROTO[asset], 'glbSha256': sha256(glb),
           'zonesFile': zpath.replace('\\', '/'), 'zonesSha256': sha256(zpath),
           'ly048Zones': [{'id': z['zoneId'], 'box': z['box'], 'label': z['label']} for z in own],
           'otherZonesInFrame': [{'id': z['zoneId'], 'box': z['box'], 'label': z['label']} for z in zones if z['seat'] != 'LY-048'],
           'nodes': {}}
    for name, tris in nt.items():
        if name in EXCL:
            continue
        p = tris.reshape(-1, 3)
        p = np.unique(np.round(p, 5), axis=0)
        m48 = np.zeros(len(p), bool)
        for z in own:
            m48 |= inbox(p, z['box'])
        other = {}
        mo = np.zeros(len(p), bool)
        for z in zones:
            if z['seat'] == 'LY-048':
                continue
            m = inbox(p, z['box']) & ~m48
            if m.any():
                other[z['zoneId']] = int(m.sum())
            mo |= m
        none = ~(m48 | mo)
        nonep = p[none]
        res['nodes'][name] = {
            'uniqueVerts': int(len(p)),
            'bbox': [p.min(0).round(4).tolist(), p.max(0).round(4).tolist()],
            'inLY048': int(m48.sum()), 'inOtherSeatOnly': other, 'inNoZone': int(none.sum()),
            'noZoneBBox': [nonep.min(0).round(4).tolist(), nonep.max(0).round(4).tolist()] if len(nonep) else None,
        }
    # wall-band probes: wall node verts near each lot edge
    w = nt.get('architecture_C_whitebox_earth_wall.001')
    if w is not None:
        p = np.unique(np.round(w.reshape(-1, 3), 5), axis=0)
        bands = {}
        bands['front_z_range_x_outside_gate'] = [float(p[(p[:, 2] > 9) & ((p[:, 0] < -5.5) | (p[:, 0] > -1.5))][:, 2].min()),
                                                 float(p[(p[:, 2] > 9) & ((p[:, 0] < -5.5) | (p[:, 0] > -1.5))][:, 2].max())]
        bands['back_z_range'] = [float(p[p[:, 2] < -9][:, 2].min()), float(p[p[:, 2] < -9][:, 2].max())]
        bands['west_x_range'] = [float(p[p[:, 0] < -7][:, 0].min()), float(p[p[:, 0] < -7][:, 0].max())]
        bands['east_x_range'] = [float(p[p[:, 0] > 7][:, 0].min()), float(p[p[:, 0] > 7][:, 0].max())]
        bands['wall_y_range'] = [float(p[:, 1].min()), float(p[:, 1].max())]
        res['wallBands'] = bands
    t = nt.get('architecture_C_plain_timber.001')
    if t is not None:
        p = np.unique(np.round(t.reshape(-1, 3), 5), axis=0)
        g = p[(p[:, 2] > 9)]
        res['gateTimberNearFront'] = {'count': int(len(g)), 'bbox': [g.min(0).round(4).tolist(), g.max(0).round(4).tolist()] if len(g) else None}
    # gaps in LY-048 ring coverage: sample the 1 m outer band at 0.25 m and list points in no LY-048 zone
    ring = []
    for x in np.arange(-8.875, 9, 0.25):
        for z in (-11.5, 11.5):
            ring.append((x, 1.0, z))
    for z in np.arange(-11.875, 12, 0.25):
        for x in (-8.5, 8.5):
            ring.append((x, 1.0, z))
    ring = np.array(ring)
    cov = np.zeros(len(ring), bool)
    for z in own:
        cov |= inbox(ring, z['box'])
    unc = ring[~cov]
    owners = {}
    for q in unc:
        hit = [z['zoneId'] for z in zones if inbox(q[None], z['box'])[0]]
        owners.setdefault(','.join(hit) or 'none', []).append(q.round(3).tolist())
    res['ringBandNotLY048'] = {k: {'n': len(v), 'xRange': [min(a[0] for a in v), max(a[0] for a in v)],
                                   'zRange': [min(a[2] for a in v), max(a[2] for a in v)]} for k, v in owners.items()}
    res['ly048YFloor'] = min(z['box'][0][1] for z in own)
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({k: res[k] for k in ('wallBands', 'gateTimberNearFront', 'ringBandNotLY048', 'ly048YFloor')}, ensure_ascii=False, indent=1))
    for n, v in res['nodes'].items():
        print(n, v['uniqueVerts'], 'in048', v['inLY048'], 'other', v['inOtherSeatOnly'], 'none', v['inNoZone'], v['noZoneBBox'])


if __name__ == '__main__':
    main()
