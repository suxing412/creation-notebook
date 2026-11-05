# LY-005 negative tests for the contract checks + old-node drift between snapshots.
# python -I negatives_drift.py <frames.json> <ports.json> <dump-bce3211-blob.json> <dump-f28d650.json> <out.json>
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbio

frames = json.load(open(sys.argv[1], encoding='utf-8'))
ports = json.load(open(sys.argv[2], encoding='utf-8'))
a = json.load(open(sys.argv[3], encoding='utf-8'))
b = json.load(open(sys.argv[4], encoding='utf-8'))
out = sys.argv[5]
nodes = {n['id']: n for n in frames['nodes']}


def corners(bmin, bmax):
    return np.array([[x, y, z] for x in (bmin[0], bmax[0]) for y in (bmin[1], bmax[1]) for z in (bmin[2], bmax[2])])


_kv = {}


def kept_vertices(asset_id):
    if asset_id not in _kv:
        f = frames['assets'][asset_id]['files']['far']
        g = glbio.read_glb('D:/GitHub/creation-notebook-lab/' + f['path'])
        ex = set(f['excludeNodes'])
        _kv[asset_id] = np.concatenate([glbio.apply(w, pos) for ni, nm_, w, pos, tri, anc in glbio.mesh_items(g) if not any(x in ex for x in anc)])
    return _kv[asset_id]


def check(M, asset_id, declared, origin_class):
    """the contract checks that LY-005 asks every placement to pass"""
    R = M[:3, :3]
    sc = np.linalg.norm(R, axis=0)
    w = glbio.apply(M, kept_vertices(asset_id))
    diff = float(max(np.max(np.abs(w.min(0) - declared['min'])), np.max(np.abs(w.max(0) - declared['max']))))
    res = {
        'scaleUnit': bool(np.max(np.abs(sc - 1)) <= 1e-6),
        'yawOnly': bool(max(abs(R[1, 0]), abs(R[1, 2]), abs(R[0, 1]), abs(R[2, 1])) <= 1e-6 and abs(R[1, 1] - 1) <= 1e-6),
        'detPositive': bool(np.linalg.det(R) > 0),
        'appliedOnceAbsolute': not (origin_class == 'city-absolute' and np.linalg.norm(M[:3, 3]) > 1e-9),
        'boundsMatchDeclared(<=1mm, exact vertices)': diff <= 1e-3,
    }
    return res, diff


def mat(rec):
    return np.array(rec['matrixColumnMajor']).reshape(4, 4).T


neg = []
# 0 controls (should pass)
for nid in ('yong-gate-body', 'C02-018', 'wall-A-wall-10', 'ground-D08'):
    r = nodes[nid]
    res, diff = check(mat(r), r['asset'], r['declaredBounds'], r['assetOriginClass'])
    neg.append({'case': 'control:' + nid, 'expect': 'pass', 'checks': res, 'boundsDiff_m': diff, 'ok': all(res.values())})
# 1 transform applied twice (local asset)
r = nodes['yong-gate-body']; M = mat(r)
res, diff = check(M @ M, r['asset'], r['declaredBounds'], r['assetOriginClass'])
neg.append({'case': 'yong-gate-body matrix applied twice', 'expect': 'fail', 'checks': res, 'boundsDiff_m': diff, 'ok': not all(res.values())})
# 2 silent 0.1% scale to close a seam
r = nodes['C02-018']; M = mat(r) @ np.diag([1.001, 1.001, 1.001, 1])
res, diff = check(M, r['asset'], r['declaredBounds'], r['assetOriginClass'])
neg.append({'case': 'C02-018 silent uniform scale 1.001', 'expect': 'fail', 'checks': res, 'boundsDiff_m': diff, 'ok': not all(res.values())})
# 3 tiny non-uniform x-stretch 1.0005 (sub-mm in bounds? no: 9 m half width -> 4.5 mm)
M = mat(r) @ np.diag([1.0005, 1, 1, 1])
res, diff = check(M, r['asset'], r['declaredBounds'], r['assetOriginClass'])
neg.append({'case': 'C02-018 x-stretch 1.0005', 'expect': 'fail', 'checks': res, 'boundsDiff_m': diff, 'ok': not all(res.values())})
# 4 city-absolute wall given its own city translation again
r = nodes['wall-A-wall-10']; M = mat(r).copy(); M[:3, 3] = [-23.0, 0, -2000.0]
res, diff = check(M, r['asset'], r['declaredBounds'], r['assetOriginClass'])
neg.append({'case': 'wall-A-wall-10 (city-absolute) re-translated', 'expect': 'fail', 'checks': res, 'boundsDiff_m': diff, 'ok': not all(res.values())})
# 5 Z-up asset imported without axis conversion (rotate -90 deg about X)
r = nodes['C02-021']; Rx = np.eye(4); Rx[1:3, 1:3] = [[0, 1], [-1, 0]]
res, diff = check(mat(r) @ Rx, r['asset'], r['declaredBounds'], r['assetOriginClass'])
neg.append({'case': 'C02-021 Z-up axis left unconverted', 'expect': 'fail', 'checks': res, 'boundsDiff_m': diff, 'ok': not all(res.values())})
# 6 mirrored (det<0)
res, diff = check(mat(r) @ np.diag([-1, 1, 1, 1]), r['asset'], r['declaredBounds'], r['assetOriginClass'])
neg.append({'case': 'C02-021 mirrored X', 'expect': 'fail', 'checks': res, 'boundsDiff_m': diff, 'ok': not all(res.values())})

# drift: old nodes bce3211 -> f28d650
an = {n['id']: n for n in a['nodes']}; bn = {n['id']: n for n in b['nodes']}


def nm(n):
    if n.get('matrix'):
        return glbio.gltf_col_major_to_np(n['matrix'])
    return glbio.compose_three(n.get('position', [0, 0, 0]), n.get('rotationY', 0) or 0, n.get('scale', [1, 1, 1]))


drift = []
for k, x in an.items():
    y = bn.get(k)
    if y is None:
        drift.append({'node': k, 'status': 'removed'}); continue
    dm = float(np.max(np.abs(nm(x) - nm(y))))
    drift.append({'node': k, 'matrixMaxAbsDiff': dm, 'assetSame': x['asset'] == y['asset'],
                  'assetSha256Same': next(q for q in a['assets'] if q['id'] == x['asset']).get('sha256') == next(q for q in b['assets'] if q['id'] == y['asset']).get('sha256'),
                  'boundsSame': x.get('bounds') == y.get('bounds'),
                  'initial': [x.get('initial', True), y.get('initial', True)], 'replaces': [x.get('replaces'), y.get('replaces')]})
added = []
for k, y in bn.items():
    if k in an:
        continue
    rec = {'node': k, 'asset': y['asset'], 'matrixColumnMajor': nm(y).T.reshape(-1).tolist(), 'initial': y.get('initial', True)}
    for other in ('yong-gate-body', 'yong-gate-interface'):
        rec['matrixDiffVs_' + other] = float(np.max(np.abs(nm(y) - nm(an[other]))))
    sc = np.linalg.norm(nm(y)[:3, :3], axis=0)
    rec['maxScaleDeviation'] = float(np.max(np.abs(sc - 1)))
    added.append(rec)
# ports re-derived from f28d650 matrices
pdr = 0.0
for p in ports['ports']:
    y = bn[p['owner']['nodeId']]
    w = glbio.apply(nm(y), np.array([p['local']['position']]))[0]
    pdr = max(pdr, float(np.max(np.abs(w - np.array(p['world']['position'])))))
summary = {
    'negativesAllBehaveAsExpected': all(n_['ok'] for n_ in neg),
    'oldNodes': len(an), 'oldNodesPresentInF28d650': sum(1 for d_ in drift if d_.get('status') != 'removed'),
    'oldNodeMaxMatrixDiff': max(d_.get('matrixMaxAbsDiff', 0) for d_ in drift),
    'oldNodesAssetOrShaChanged': [d_['node'] for d_ in drift if not (d_.get('assetSame') and d_.get('assetSha256Same'))],
    'oldNodesBoundsChanged': [d_['node'] for d_ in drift if not d_.get('boundsSame')],
    'oldNodesInitialOrReplacesChanged': [d_['node'] for d_ in drift if d_['initial'][0] != d_['initial'][1] or d_['replaces'][0] != d_['replaces'][1]],
    'portsWorldRecomputedFromF28d650_maxDiff_m': pdr,
    'addedNodes': [x['node'] for x in added],
}
json.dump({'summary': summary, 'negatives': neg, 'drift': drift, 'addedNodesF28d650': added}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(summary, ensure_ascii=False, indent=1))
for n_ in neg:
    print(n_['case'], n_['expect'], n_['ok'], {k: v for k, v in n_['checks'].items() if not v}, round(n_['boundsDiff_m'], 6))
for x in added:
    print(x['node'], x['asset'], x['initial'], round(x['matrixDiffVs_yong-gate-body'], 6), x['matrixColumnMajor'][12:15])
