"""Summarise results/ops-*.json into results/summary.json (read-only on inputs)."""
import json, glob, os
out = {}
for f in sorted(glob.glob('results/ops-*.json')):
    d = json.load(open(f, encoding='utf-8'))
    k = os.path.basename(f)[4:-5]
    solid = [{'a': p['a'], 'b': p['b'], 'vol': p['intersectVolume_m3']} for p in d['opPairs']
             if p.get('intersectVolume_m3', 0) and p['intersectVolume_m3'] > 1e-12]
    near = [{'a': p['a'], 'b': p['b'], 'minDist': p['minDistVertexSampled']} for p in d['opPairs']
            if not p.get('intersectVolume_m3') and p['minDistVertexSampled'] < 0.03 and not p['overlapTriPairs']]
    st = d['containerStroke']
    cf = d['containerStrokeFree']
    hi = cf.get('contiguousFromRest')
    rest = min(st, key=lambda s: abs(s['dz']))
    out[k] = {
        'sha256': d['sha256'], 'meshCount': d['meshCount'], 'wellMeshCount': d['wellMeshCount'],
        'axle': d.get('axle'),
        'container': d['containerGroup'],
        'restMinClear': rest['minClear'], 'restNearest': rest['nearest'],
        'strokeFreeDzFromRest': hi,
        'firstBlockAbove': (cf.get('firstBlockAbove') or {}).get('collisions'),
        'firstBlockAboveDz': (cf.get('firstBlockAbove') or {}).get('dz'),
        'firstBlockBelowDz': (cf.get('firstBlockBelow') or {}).get('dz'),
        'restCollisions': cf.get('restCollisions'),
        'minClearInsideBoreStroke': min((s['minClear'] for s in st if s['topZ'] < 0.68 and s['bottomZ'] > d['containerGroup'].get('linerBottomZ', -9)), default=None),
        'liftOut': d.get('liftOut'),
        'wheelRotationContactsUnion': sorted({tuple(c) for r in d.get('wheelRotation', []) for c in r['contacts']}),
        'ropeStrands': [{'bbox': s['bbox'], 'lowest': s['lowestPoint']} for s in d['ropeStrands']],
        'boreRaysWithHits': [r for r in d['boreRays'] if r['hitsTopDown']],
        'solidIntersections': solid,
        'nearPairsUnder3cm': near,
    }
    if 'cityNeighbours' in d:
        out[k]['cityNeighbours'] = d['cityNeighbours']
json.dump(out, open('results/summary.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for k, v in out.items():
    print('==', k, v['sha256'][:12], 'meshes', v['meshCount'], v['wellMeshCount'])
    print(' axle', v['axle'], ' container', v['container'])
    print(' rest', v['restMinClear'], v['restNearest'], 'stroke', v['strokeFreeDzFromRest'], 'blockAbove', v['firstBlockAboveDz'], v['firstBlockAbove'], 'below', v['firstBlockBelowDz'], v['restCollisions'])
    print(' minClear in bore', v['minClearInsideBoreStroke'])
    print(' lift', json.dumps(v['liftOut']))
    print(' wheelRot', v['wheelRotationContactsUnion'])
    print(' rope', v['ropeStrands'])
    print(' rays', v['boreRaysWithHits'][:5])
    print(' solid', [(s['a'], s['b'], s['vol']) for s in v['solidIntersections']])
    print(' near', [(s['a'], s['b'], s['minDist']) for s in v['nearPairsUnder3cm']])
