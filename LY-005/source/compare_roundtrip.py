# LY-005 compare Blender round-trip outputs against raw GLB bytes and city-data node matrices.
# python -I compare_roundtrip.py <cases dir> <out dir> <result.json>
import sys, os, json, glob
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbio

cases_dir, out_dir, res_path = sys.argv[1:4]


def nearest_max(a, b):
    """max over a of distance to nearest point in b, and vice versa"""
    def one(x, y):
        m = 0.0
        for i in range(0, len(x), 512):
            dd = np.sqrt(((x[i:i + 512, None, :] - y[None, :, :]) ** 2).sum(-1)).min(1)
            m = max(m, float(dd.max()))
        return m
    return max(one(a, b), one(b, a))


def raw_points(path, ex):
    g = glbio.read_glb(path)
    pts = []
    for ni, name, w, pos, tri, anc in glbio.mesh_items(g):
        if any(x in ex for x in anc):
            continue
        pts.append(glbio.apply(w, pos))
    p = np.concatenate(pts)
    return np.unique(np.round(p, 5), axis=0), g


results = []
for cp in sorted(glob.glob(os.path.join(cases_dir, '*.json'))):
    c = json.load(open(cp, encoding='utf-8'))
    n = c['name']
    rep = json.load(open(os.path.join(out_dir, n + '.blender-report.json'), encoding='utf-8'))
    raw, g = raw_points(c['glb'], set(c['excludeNodes']))
    M = glbio.gltf_col_major_to_np(c['cityMatrixGLTFColumnMajor'])
    rawW = glbio.apply(M, raw)
    load = lambda tag: np.array(json.load(open(os.path.join(out_dir, f'{n}.{tag}.gltfframe.json'))), dtype=float)
    imp1, rl, rp = load('import1'), load('reimportLocal'), load('reimportPlaced')
    r = {'node': n, 'asset': c['asset'], 'sourceGlb': c['glb'].replace('D:/GitHub/creation-notebook-lab/', ''),
         'sourceSha256': g['sha256'], 'sourceShaMatchesCityData': g['sha256'] == c['sha256'],
         'blender': rep['blender'], 'sceneUnits': rep['sceneUnits'],
         'uniqueVerts': {'raw': len(raw), 'import1': len(imp1), 'reimportLocal': len(rl), 'reimportPlaced': len(rp)}}
    r['import1_vs_raw_maxDist_m'] = nearest_max(imp1, raw)
    r['reimportLocal_vs_raw_maxDist_m'] = nearest_max(rl, raw)
    r['reimportPlaced_vs_cityWorld_maxDist_m'] = nearest_max(rp, rawW)
    # axis check: Blender-frame bounds of first import must equal (x, -z, y) of raw glTF bounds
    bb = rep['import1']['boundsBlenderFrame']
    exp_min = [raw[:, 0].min(), -raw[:, 2].max(), raw[:, 1].min()]
    exp_max = [raw[:, 0].max(), -raw[:, 2].min(), raw[:, 1].max()]
    r['blenderAxisMapping'] = 'Blender(X,Y,Z) = glTF(x,-z,y)'
    r['blenderFrameBoundsVsAxisMappedRaw_maxDiff_m'] = float(max(np.max(np.abs(np.array(bb['min']) - exp_min)), np.max(np.abs(np.array(bb['max']) - exp_max))))
    # exported placed GLB: node matrix of CITY_NODE vs city-data matrix
    for tag in ('local', 'placed'):
        eg = glbio.read_glb(os.path.join(out_dir, f'{n}.{tag}-roundtrip.glb'))
        js = eg['json']
        world, parent = glbio.world_matrices(eg)
        info = {'bytes': eg['size'], 'sha256': eg['sha256'], 'generator': js['asset'].get('generator'), 'nodes': len(js['nodes'])}
        if tag == 'placed':
            idx = [i for i, nd in enumerate(js['nodes']) if nd.get('name', '').startswith('CITY_NODE')]
            em = world[idx[0]]
            info['cityNodeTRS'] = {k: js['nodes'][idx[0]].get(k) for k in ('translation', 'rotation', 'scale', 'matrix')}
            info['cityNodeMatrixVsCityData_maxAbsDiff'] = float(np.max(np.abs(em - M)))
            info['cityNodeScale'] = np.linalg.norm(em[:3, :3], axis=0).tolist()
            pts = np.concatenate([glbio.apply(w, pos) for ni, name, w, pos, tri, anc in glbio.mesh_items(eg)])
            wb = {'min': pts.min(0).tolist(), 'max': pts.max(0).tolist()}
            info['worldBounds'] = wb
            if c.get('declaredNodeBounds'):
                db = c['declaredNodeBounds']
                info['worldBoundsVsCityDataNodeBounds_maxDiff_m'] = float(max(np.max(np.abs(np.array(wb['min']) - db['min'])), np.max(np.abs(np.array(wb['max']) - db['max']))))
        else:
            # local export keeps original per-node transforms (no extra root introduced)
            orig = {nd.get('name'): glbio.local_matrix(nd) for nd in g['json']['nodes'] if nd.get('name') not in set(c['excludeNodes'])}
            diffs = []
            for i, nd in enumerate(js['nodes']):
                if nd.get('name') in orig:
                    diffs.append(float(np.max(np.abs(glbio.local_matrix(nd) - orig[nd['name']]))))
            info['matchedNodes'] = len(diffs)
            info['nodeLocalMatrixVsSource_maxAbsDiff'] = max(diffs) if diffs else None
            info['rootsAddedByExport'] = [nd.get('name') for i, nd in enumerate(js['nodes']) if parent.get(i, 'x') is None and nd.get('name') not in orig]
        r['export_' + tag] = info
    r['placementVsDeclaredNativeBlender_maxAbsDiff'] = rep.get('placementVsDeclaredNativeBlenderMaxAbsDiff')
    r['blenderPlacementRowMajor'] = rep['placementBlenderFrameRowMajor']
    r['blenderEmptyScale'] = rep['placedInBlender']['emptyScale']
    r['blenderEmptyEulerXYZdeg'] = rep['placedInBlender']['emptyEulerXYZdeg']
    tol = 1e-4
    r['checks'] = {
        'unitsMetricScale1': rep['sceneUnits']['system'] == 'METRIC' and abs(rep['sceneUnits']['scale_length'] - 1) < 1e-12,
        'importMatchesRaw': r['import1_vs_raw_maxDist_m'] <= tol,
        'axisMappingExact': r['blenderFrameBoundsVsAxisMappedRaw_maxDiff_m'] <= tol,
        'localRoundTripMatchesRaw': r['reimportLocal_vs_raw_maxDist_m'] <= tol,
        'placedRoundTripMatchesCityWorld': r['reimportPlaced_vs_cityWorld_maxDist_m'] <= max(tol, 4 * float(np.spacing(np.float32(np.abs(rawW).max())))),
        'exportedNodeMatrixEqualsCityData': r['export_placed']['cityNodeMatrixVsCityData_maxAbsDiff'] <= 1e-6 * max(1, float(np.abs(M[:3, 3]).max())),
        'exportedNodeScaleUnit': max(abs(s - 1) for s in r['export_placed']['cityNodeScale']) <= 1e-6,
        'noExtraRootFromLocalExport': not r['export_local']['rootsAddedByExport'],
    }
    if c.get('declaredNodeBounds'):
        r['checks']['placedBoundsEqualCityDataBounds'] = r['export_placed']['worldBoundsVsCityDataNodeBounds_maxDiff_m'] <= 1e-3
    if r['placementVsDeclaredNativeBlender_maxAbsDiff'] is not None:
        r['checks']['blenderMatrixEqualsDeclaredNative'] = r['placementVsDeclaredNativeBlender_maxAbsDiff'] <= 1e-6
    r['allChecks'] = all(r['checks'].values())
    results.append(r)
    print(n, r['allChecks'], {k: v for k, v in r['checks'].items() if not v}, 'imp', r['import1_vs_raw_maxDist_m'], 'loc', r['reimportLocal_vs_raw_maxDist_m'], 'placed', r['reimportPlaced_vs_cityWorld_maxDist_m'],
          'M', r['export_placed']['cityNodeMatrixVsCityData_maxAbsDiff'], 'B', r['export_placed'].get('worldBoundsVsCityDataNodeBounds_maxDiff_m'), 'nb', r['placementVsDeclaredNativeBlender_maxAbsDiff'])
json.dump({'tolerance_m': 1e-4, 'results': results}, open(res_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
