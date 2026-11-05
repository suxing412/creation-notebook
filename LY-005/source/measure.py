# LY-005 measurement: asset frames, node world transforms, bounds drift, double-application risk.
# Read-only on the lab repo. Usage:
#   python -I measure.py <city-dump.json> <lab city dir> <out.json> [label]
# Reproduces the renderer rule in docs/cities/luoyang/city-renderer.mjs:
#   loadAsset(): geometry.applyMatrix4(object.matrixWorld)   (GLB scene hierarchy baked once)
#   transformFor(): node.matrix if present, else compose(position, quatY(rotationY), scale)
#   InstancedMesh.setMatrixAt(nodeMatrix)                     (city placement applied once)
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbio

dump_path, city_dir, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
label = sys.argv[4] if len(sys.argv) > 4 else ''
d = json.load(open(dump_path, encoding='utf-8'))


def rel_from_url(u):
    key = 'docs/'
    i = u.replace('\\', '/').find('/docs/')
    return u.replace('\\', '/')[i + 1:] if i >= 0 else u


LAB = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(city_dir))))


def resolve(url):
    r = rel_from_url(url)
    return os.path.join(LAB, r)


def f32ulp(x):
    x = abs(float(x))
    if x == 0:
        return 0.0
    return float(np.spacing(np.float32(x)))


asset_out = {}
asset_geom = {}
for a in d['assets']:
    rec = {'id': a['id'], 'files': {}}
    for tag, url, sha, bounds_decl in (('far', a['url'], a.get('sha256'), a.get('bounds')),
                                       ('near', a.get('nearUrl'), a.get('nearSha256'), None)):
        if not url:
            continue
        p = resolve(url)
        g = glbio.read_glb(p)
        js = g['json']
        excluded = set(a.get('excludeNodes') or a.get('removable_site_nodes') or [])
        nodes = js.get('nodes', [])
        trs = {'translationOnly': 0, 'rotation': 0, 'nonUnitScale': 0, 'matrix': 0, 'identity': 0}
        max_scale_dev = 0.0
        for n in nodes:
            if 'matrix' in n:
                trs['matrix'] += 1
                m = np.array(n['matrix']).reshape(4, 4).T
                sc = np.linalg.norm(m[:3, :3], axis=0)
                max_scale_dev = max(max_scale_dev, float(np.max(np.abs(sc - 1))))
                continue
            s = n.get('scale', [1, 1, 1]); r = n.get('rotation', [0, 0, 0, 1])
            if any(abs(v - 1) > 0 for v in s):
                trs['nonUnitScale'] += 1
                max_scale_dev = max(max_scale_dev, max(abs(v - 1) for v in s))
            elif r != [0, 0, 0, 1] and any(abs(v) > 0 for v in r[:3]):
                trs['rotation'] += 1
            elif 'translation' in n and any(v != 0 for v in n['translation']):
                trs['translationOnly'] += 1
            else:
                trs['identity'] += 1
        allpts, keptpts, tris_keep = [], [], []
        matched = set()
        nkept_tri = 0
        for ni, name, w, pos, tri, anc in glbio.mesh_items(g):
            wp = glbio.apply(w, pos)
            allpts.append(wp)
            hit = [x for x in anc if x in excluded]
            if hit:
                matched.update(hit)
                continue
            keptpts.append(wp)
            tris_keep.append((name, wp, tri))
            nkept_tri += len(tri)
        allp = np.concatenate(allpts); kp = np.concatenate(keptpts)
        bmin, bmax = kp.min(0), kp.max(0)
        f = {
            'path': os.path.relpath(p, LAB).replace('\\', '/'),
            'bytes': g['size'], 'sha256': g['sha256'],
            'declaredSha256': sha, 'shaMatchesDeclared': sha == g['sha256'],
            'generator': js.get('asset', {}).get('generator'),
            'extensionsUsed': js.get('extensionsUsed', []),
            'nodeCount': len(nodes), 'nodeTransformKinds': trs, 'maxNodeScaleDeviation': max_scale_dev,
            'excludeNodes': sorted(excluded), 'excludeNodesMatched': sorted(matched),
            'excludeComplete': matched == excluded,
            'keptTriangles': int(nkept_tri),
            'boundsAll': {'min': allp.min(0).tolist(), 'max': allp.max(0).tolist()},
            'boundsKept': {'min': bmin.tolist(), 'max': bmax.tolist()},
            'maxAbsCoordinate': float(np.max(np.abs(kp))),
            'float32UlpAtMaxCoordinate_m': f32ulp(np.max(np.abs(kp))),
            'originClass': 'local-origin' if float(np.max(np.abs((bmin + bmax) / 2))) < 100 else 'city-absolute',
        }
        if bounds_decl:
            f['declaredBounds'] = bounds_decl
            f['declaredBoundsMaxDiff_m'] = float(max(np.max(np.abs(bmin - np.array(bounds_decl['min']))),
                                                     np.max(np.abs(bmax - np.array(bounds_decl['max'])))))
        rec['files'][tag] = f
        asset_geom[(a['id'], tag)] = kp
    asset_out[a['id']] = rec


def node_matrix(n):
    t = n.get('transform') or n
    if n.get('matrix'):
        return glbio.gltf_col_major_to_np(n['matrix']), 'matrix'
    return glbio.compose_three(t.get('position', [0, 0, 0]), t.get('rotationY', 0) or 0, t.get('scale', [1, 1, 1])), 'compose'


node_out = []
for n in d['nodes'] + d.get('researchModels', []):
    m, src = node_matrix(n)
    R = m[:3, :3]
    sc = np.linalg.norm(R, axis=0)
    ortho = max(abs(float(R[:, i] @ R[:, j])) for i, j in ((0, 1), (0, 2), (1, 2)))
    yaw = math.degrees(math.atan2(R[0, 2], R[0, 0]))  # rotation about +Y: col0=(c,0,-s); atan2(s,c)=atan2(-R[2,0],R[0,0])
    yaw = math.degrees(math.atan2(-R[2, 0], R[0, 0]))
    tilt = float(max(abs(R[1, 0]), abs(R[1, 2]), abs(R[0, 1]), abs(R[2, 1])))
    both = bool(n.get('matrix')) and any(k in (n.get('transform') or n) for k in ('position', 'rotationY', 'scale'))
    rec = {
        'id': n['id'], 'asset': n['asset'], 'space': n.get('space', 'city'), 'initial': n.get('initial', True),
        'replaces': n.get('replaces'), 'transformSource': src, 'matrixAndTRSBothPresent': both,
        'matrixColumnMajor': m.T.reshape(-1).tolist(), 'translation': m[:3, 3].tolist(),
        'yawDegAboutY': yaw, 'tiltComponentMax': tilt, 'axisScale': sc.tolist(),
        'maxScaleDeviation': float(np.max(np.abs(sc - 1))), 'determinant': float(np.linalg.det(R)),
        'maxAxisDotProduct': ortho,
    }
    kp = asset_geom[(n['asset'], 'far')]
    wp = glbio.apply(m, kp)
    wmin, wmax = wp.min(0), wp.max(0)
    rec['worldBoundsComputed'] = {'min': wmin.tolist(), 'max': wmax.tolist()}
    rec['worldBaseY'] = float(wmin[1])
    if n.get('bounds'):
        b = n['bounds']
        rec['declaredBounds'] = b
        rec['declaredBoundsMaxDiff_m'] = float(max(np.max(np.abs(wmin - np.array(b['min']))), np.max(np.abs(wmax - np.array(b['max'])))))
    af = asset_out[n['asset']]['files']['far']
    rec['assetOriginClass'] = af['originClass']
    tnorm = float(np.linalg.norm(m[:3, 3]))
    rec['doubleApplicationRisk'] = bool(af['originClass'] == 'city-absolute' and tnorm > 1e-9)
    rec['float32UlpAtWorldMax_m'] = f32ulp(np.max(np.abs(wp)))
    if (n['asset'], 'near') in asset_geom:
        np_ = glbio.apply(m, asset_geom[(n['asset'], 'near')])
        rec['nearWorldBounds'] = {'min': np_.min(0).tolist(), 'max': np_.max(0).tolist()}
        rec['nearVsFarBaseYDiff_m'] = float(np_.min(0)[1] - wmin[1])
    node_out.append(rec)

summary = {
    'label': label,
    'assets': len(asset_out), 'assetFiles': sum(len(v['files']) for v in asset_out.values()),
    'nodes': len(node_out),
    'shaMismatch': [ (k, t) for k, v in asset_out.items() for t, f in v['files'].items() if f['declaredSha256'] and not f['shaMatchesDeclared']],
    'excludeIncomplete': [k for k, v in asset_out.items() for f in v['files'].values() if not f['excludeComplete']],
    'assetsWithNonUnitNodeScale': [k for k, v in asset_out.items() for f in v['files'].values() if f['maxNodeScaleDeviation'] > 0],
    'assetsWithNodeRotation': [k for k, v in asset_out.items() for f in v['files'].values() if f['nodeTransformKinds']['rotation'] or f['nodeTransformKinds']['matrix']],
    'assetDeclaredBoundsMaxDiff_m': max(f.get('declaredBoundsMaxDiff_m', 0) for v in asset_out.values() for f in v['files'].values()),
    'nodeMaxScaleDeviation': max(r['maxScaleDeviation'] for r in node_out),
    'nodeMaxAxisDot': max(r['maxAxisDotProduct'] for r in node_out),
    'nodeMaxTilt': max(r['tiltComponentMax'] for r in node_out),
    'nodeMinDeterminant': min(r['determinant'] for r in node_out),
    'nodesMatrixAndTRS': [r['id'] for r in node_out if r['matrixAndTRSBothPresent']],
    'nodesDoubleApplicationRisk': [r['id'] for r in node_out if r['doubleApplicationRisk']],
    'nodeDeclaredBoundsMaxDiff_m': max(r.get('declaredBoundsMaxDiff_m', 0) for r in node_out),
    'nodeDeclaredBoundsWorst': max(node_out, key=lambda r: r.get('declaredBoundsMaxDiff_m', 0))['id'],
    'maxFloat32UlpWorld_m': max(r['float32UlpAtWorldMax_m'] for r in node_out),
    'cityAbsoluteAssets': sorted(k for k, v in asset_out.items() if v['files']['far']['originClass'] == 'city-absolute'),
    'localOriginAssets': sorted(k for k, v in asset_out.items() if v['files']['far']['originClass'] == 'local-origin'),
    'yawValuesDeg': sorted(set(round(r['yawDegAboutY'], 4) for r in node_out)),
}
json.dump({'summary': summary, 'assets': asset_out, 'nodes': node_out}, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(summary, ensure_ascii=False, indent=1))
