# LY-078 prep: read-only. Measures how the three "keep" source objects (LY-006 registry v1) relate to the
# LY-078 write zone LY-078:write:001 (frame local:stoneclassic, box [-20,-0.3,18]..[20,0.5,24]) and to the
# LY-006 rule "源对象改/替换必须落在自己的写入区内（容差 0.05 m）".
#   python -I zone_check.py <glb> [<glb> ...] --out qa/zone-check.json
import sys, json, argparse
import numpy as np

_src = open(__file__.replace('zone_check.py', 'measure_parts.py'), encoding='utf-8').read().replace('\nmain()\n', '\n')
P = {}
exec(compile(_src, 'mp', 'exec'), P)

ZONE = (np.array([-20.0, -0.3, 18.0]), np.array([20.0, 0.5, 24.0]))
TOL = 0.05


def tris_of(path):
    js, binc, sha, n = P['load'](path)
    out = []
    for m in js['meshes']:
        for pr in m['primitives']:
            pos = P['acc'](js, binc, pr['attributes']['POSITION']).astype(np.float64)
            idx = P['acc'](js, binc, pr['indices']).reshape(-1, 3) if 'indices' in pr else np.arange(len(pos)).reshape(-1, 3)
            mat = js['materials'][pr['material']]['name'] if 'material' in pr else None
            out.append((mat, pos[idx]))
    return out, sha, n


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('glbs', nargs='+'); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    lo, hi = ZONE
    rep = {'zone': {'id': 'LY-078:write:001', 'frame': 'local:stoneclassic', 'box': [lo.tolist(), hi.tolist()], 'tol_m': TOL,
                    'source': 'workpacks/LY-006/registry/zones.json'}, 'files': []}
    for g in a.glbs:
        prims, sha, nbytes = tris_of(g)
        tot = inside_all = touching = 0; per = {}
        allv = []
        for mat, T in prims:
            v = T.reshape(-1, 3); allv.append(v)
            inv = np.all((v >= lo - TOL) & (v <= hi + TOL), axis=1).reshape(-1, 3)
            ia = int(inv.all(axis=1).sum()); tc = int(inv.any(axis=1).sum())
            per[mat] = {'tris': len(T), 'trisFullyInZoneTol': ia, 'trisWithAVertexInZoneTol': tc}
            tot += len(T); inside_all += ia; touching += tc
        V = np.concatenate(allv)
        rep['files'].append({'path': g, 'sha256': sha, 'bytes': nbytes, 'tris': tot,
                             'trisFullyInZoneTol': inside_all, 'fractionFullyInZone': round(inside_all / tot, 6),
                             'trisWithAVertexInZoneTol': touching,
                             'objectBounds': [V.min(0).round(4).tolist(), V.max(0).round(4).tolist()],
                             'objectOutsideZoneBy_m': {'zMin': round(float(lo[2] - V[:, 2].min()), 4), 'yMax': round(float(V[:, 1].max() - hi[1]), 4)},
                             'perMaterial': per})
    rep['conclusion'] = ('If the split into ground/cover/enclosure/south_gate counts as modify/replace of the keep source object, '
                         'it violates the LY-006 rule unless registry v2 widens the zone or adds a derived-copy class.')
    json.dump(rep, open(a.out, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    for f in rep['files']:
        print(f['path'].split('/')[-1], f['tris'], 'fullyInZone', f['trisFullyInZoneTol'], 'touch', f['trisWithAVertexInZoneTol'], 'bounds', f['objectBounds'])


main()
