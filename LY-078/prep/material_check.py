# LY-078 prep: read-only. Compares the stone-classic GLB materials with the LY-007 frozen LY_P01 baseline.
#   python -I material_check.py <LY-007 LY_P01-material-semantics.json> <glb> [<glb> ...] --out qa/material-check.json
import sys, json, argparse, struct, hashlib
import numpy as np

TIER = {'near': 'LOD0', 'middle': 'LOD1', 'far': 'LOD2'}


def glb_json(path):
    b = open(path, 'rb').read(); n = struct.unpack('<I', b[12:16])[0]
    return json.loads(b[20:20 + n]), hashlib.sha256(b).hexdigest()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('semantics'); ap.add_argument('glbs', nargs='+'); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    sem = json.load(open(a.semantics, encoding='utf-8'))
    base = {m['material']: m for m in sem['materials']}
    rep = {'baseline': a.semantics, 'baselineSha256': hashlib.sha256(open(a.semantics, 'rb').read()).hexdigest(), 'files': []}
    for g in a.glbs:
        js, sha = glb_json(g)
        tier = next((v for k, v in TIER.items() if f'_{k}.glb' in g), None)
        rows = []
        for m in js['materials']:
            nm = m['name']; role = nm.replace('LY_P01_', '').split('__')[0]
            pbr = m.get('pbrMetallicRoughness', {})
            r = {'name': nm, 'role': role, 'doubleSided': m.get('doubleSided', False),
                 'baseColorFactor': pbr.get('baseColorFactor'), 'roughness': pbr.get('roughnessFactor'),
                 'hasTextures': any(k in pbr for k in ('baseColorTexture', 'metallicRoughnessTexture')) or 'normalTexture' in m}
            b = base.get(role)
            if b is None:
                r['verdict'] = 'not in LY-007 five-material baseline (P-NEWMAT pending)'
            else:
                want = b['names'][tier] if tier else None
                bf = np.array(b['flat']['baseColorFactor_linear'], np.float32)
                gf = np.array(r['baseColorFactor'][:3], np.float32) if r['baseColorFactor'] else None
                r.update({'expectedName': want, 'nameOK': nm == want,
                          'baseColorEqualsFlatFloat32': bool(gf is not None and np.array_equal(gf, bf)),
                          'baseColorMaxAbsDiff': float(np.abs(gf.astype(np.float64) - np.array(b['flat']['baseColorFactor_linear'])).max()) if gf is not None else None,
                          'expectedRoughnessFlat': b['flat']['roughness'], 'doubleSidedExpected': True,
                          'doubleSidedOK': r['doubleSided'] is True})
            rows.append(r)
        rep['files'].append({'path': g, 'sha256': sha, 'tier': tier, 'textures': len(js.get('textures', [])),
                             'images': len(js.get('images', [])), 'materials': rows})
    json.dump(rep, open(a.out, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    for f in rep['files']:
        print(f['tier'], 'tex', f['textures'], [(r['name'], r.get('expectedName'), r.get('baseColorEqualsFlatFloat32'), r['roughness'], r['doubleSided']) for r in f['materials']])


main()
