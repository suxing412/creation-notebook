# LY-082 prep: K9 write-zone / ownership check against LY-006 registry v1 (read-only).
# usage: python -I zone_check82.py <workpacks_root> <corridor.json> <crossing.json> <out.json>
import hashlib, json, sys

root, corr_p, cross_p, out = sys.argv[1].rstrip('/'), sys.argv[2], sys.argv[3], sys.argv[4]
reg = root + '/LY-006/registry/'


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def load(p):
    return json.load(open(p, encoding='utf-8'))


Z, O, P, S = (load(reg + n) for n in ('zones.json', 'ownership.json', 'ports.json', 'seams.json'))
corr, cross = load(corr_p), load(cross_p)
M = corr['matrix']  # column-major; C02-010 has no rotation
tx, tz = M[12], M[14]
assert M[0] == 1 and M[10] == 1 and M[2] == 0 and M[8] == 0, 'rotation present: extend transform'


def world_box(e):
    b = e['box']
    if e.get('frame') == 'world':
        return b
    if e.get('frame') == 'court:' + corr['court']:
        return [[b[0][0] + tx, b[0][1], b[0][2] + tz], [b[1][0] + tx, b[1][1], b[1][2] + tz]]
    return None


def inter_vol(a, b):
    v = 1.0
    for i in range(3):
        d = min(a[1][i], b[1][i]) - max(a[0][i], b[0][i])
        if d <= 0:
            return 0.0, d
        v *= d
    return v, None


mine = [e for e in Z['zones'] if e['seat'] == 'LY-082']
zbox = world_box(mine[0])
res = {'registrySha256': {n: sha(reg + n) for n in ('zones.json', 'ownership.json', 'ports.json', 'seams.json')},
       'corridorFile': corr_p, 'corridorSha256': sha(corr_p), 'myZones': mine, 'checks': []}


def chk(name, ok, **kw):
    res['checks'].append(dict(name=name, pass_=bool(ok), **kw))


# K9a gate segment inside my zone (x) and on its z-min face
g = corr['gateWorld']
gx = sorted([g['p0'][0], g['p1'][0]])
chk('K9a_gate_on_zone_face', zbox[0][0] <= gx[0] and gx[1] <= zbox[1][0] and abs(g['p0'][2] - zbox[0][2]) < 1e-6,
    gateX=gx, gateZ=g['p0'][2], zoneX=[zbox[0][0], zbox[1][0]], zoneZmin=zbox[0][2])
# K9b crossing flat band inside zone x
rows = cross['rows']  # {z: {flatWithin_2mm: [x0, x1, width]}}
bands = {z: r['flatWithin_2mm'] for z, r in rows.items()}
okb = bool(bands) and all(zbox[0][0] <= b[0] and b[1] <= zbox[1][0] and zbox[0][2] <= float(z) <= zbox[1][2]
                          for z, b in bands.items())
chk('K9b_crossing_in_zone', okb, flatWithin_2mm=bands)
# K9c zero-volume overlap with every other seat's zone (write/cut/etc.)
hits = []
for e in Z['zones']:
    if e['seat'] == 'LY-082':
        continue
    wb = world_box(e)
    if wb is None:
        continue
    v, gap = inter_vol(zbox, wb)
    if v > 0:
        hits.append({'zoneId': e['zoneId'], 'vol_m3': v})
    elif gap is not None and gap > -1e-9 and gap <= 1e-6:
        res.setdefault('faceContacts', []).append({'zoneId': e['zoneId'], 'class': e['class'], 'box': wb})
chk('K9c_zone_volume_overlap_0', not hits, overlaps=hits)
# K9d ground-south ownership: only LY-090 may emit a diff
gs = O['ownership']['groundPieces'].get('gp:city-node:ground-south', {})
chk('K9d_ground_south_owner_is_LY-090', gs.get('owner') == 'LY-090', entry=gs)
# K9e port declared, producer LY-049, consumer includes LY-082, values filled?
pt = P['ports'].get('C02-010:gate-boundary:road-end') if isinstance(P['ports'], dict) else None
filled = bool(pt and pt.get('world') is not None)
chk('K9e_port_declared', bool(pt) and pt['producer'] == 'LY-049' and 'LY-082' in pt['consumers'], port=pt,
    valuesFilled=filled, note='values null until LY-049 delivers; K4 uses y 0.200 until then')
res['namespaceRule'] = O['ownership']['newGroundNamespaceRule']
res['allPass'] = all(c['pass_'] for c in res['checks'])
json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps({'allPass': res['allPass'], 'checks': [(c['name'], c['pass_']) for c in res['checks']],
                  'faceContacts': res.get('faceContacts', [])}, ensure_ascii=False))
