# LY-005 aggregate checks, each bound to the SHA256 of the files it reads. python -I checks.py <LY-005 dir>
import sys, os, json, hashlib, subprocess
import numpy as np

B = sys.argv[1]
q = lambda p: os.path.join(B, p)
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
J = lambda p: json.load(open(q(p), encoding='utf-8'))
checks = []


def add(cid, title, ok, evidence, files):
    checks.append({'id': cid, 'title': title, 'pass': bool(ok), 'evidence': evidence,
                   'files': {f: sha(q(f)) if not os.path.isabs(f) else sha(f) for f in files}})


# C1 snapshot identity
a, b = sha(q('qa/city-data.dump.json')), sha(os.path.join(B, '..', 'LY-001', 'qa', 'city-data.dump.json'))
add('C1', 'city-data dump equals LY-001 snapshot dump', a == b, {'LY005': a, 'LY001': b}, ['qa/city-data.dump.json'])

# C2 placement rules R1-R5 on every node
fr = J('qa/frames-bce3211.json'); s = fr['summary']
ok = (s['nodeMaxScaleDeviation'] <= 1e-6 and s['nodeMaxTilt'] <= 1e-6 and s['nodeMinDeterminant'] > 0 and s['nodeMaxAxisDot'] <= 1e-6
      and not s['nodesMatrixAndTRS'] and not s['nodesDoubleApplicationRisk'] and s['nodeDeclaredBoundsMaxDiff_m'] <= 1e-3
      and s['assetDeclaredBoundsMaxDiff_m'] <= 1e-3 and not s['shaMismatch'] and not s['excludeIncomplete'] and not s['assetsWithNonUnitNodeScale'])
add('C2', 'all 80 nodes satisfy R1-R5; all 48 GLB files match declared SHA and bounds', ok,
    {k: s[k] for k in ('nodes', 'assetFiles', 'nodeMaxScaleDeviation', 'nodeMaxTilt', 'nodeMinDeterminant', 'nodeMaxAxisDot', 'nodesMatrixAndTRS',
                       'nodesDoubleApplicationRisk', 'nodeDeclaredBoundsMaxDiff_m', 'assetDeclaredBoundsMaxDiff_m', 'shaMismatch', 'excludeIncomplete', 'yawValuesDeg')},
    ['qa/frames-bce3211.json', 'source/measure.py', 'source/glbio.py'])

# C3 Blender round trip
rt = J('qa/roundtrip-results.json')['results']
pos = [r for r in rt if not r['node'].startswith('NEG')]
neg = [r for r in rt if r['node'].startswith('NEG')]
files = ['qa/roundtrip-results.json', 'source/bl_roundtrip.py', 'source/compare_roundtrip.py']
for r in rt:
    files += [f"qa/roundtrip/out/{r['node']}.local-roundtrip.glb", f"qa/roundtrip/out/{r['node']}.placed-roundtrip.glb", f"qa/roundtrip/cases/{r['node']}.json", f"qa/roundtrip/out/{r['node']}.blender-report.json"]
add('C3', 'Blender 5.2.1 GLB import->export->re-import keeps units, axes and world matrix (5 nodes); wrong-asset negative fails', all(r['allChecks'] for r in pos) and all(not r['allChecks'] for r in neg),
    {r['node']: {'source': r['sourceGlb'], 'sourceSha256': r['sourceSha256'], 'checks': r['checks'], 'import1_vs_raw_m': r['import1_vs_raw_maxDist_m'], 'local_vs_raw_m': r['reimportLocal_vs_raw_maxDist_m'],
                 'placed_vs_world_m': r['reimportPlaced_vs_cityWorld_maxDist_m'], 'exportedNodeMatrixDiff': r['export_placed']['cityNodeMatrixVsCityData_maxAbsDiff'],
                 'placedBoundsVsCityData_m': r['export_placed'].get('worldBoundsVsCityDataNodeBounds_maxDiff_m'), 'nativeBlenderMatrixDiff': r['placementVsDeclaredNativeBlender_maxAbsDiff']} for r in rt}, files)

# C4 negatives
nd = J('qa/negatives-and-drift.json')
add('C4', 'contract checks reject double application, silent scale, x-stretch, re-translated absolute asset, unconverted Z-up, mirror; controls pass', nd['summary']['negativesAllBehaveAsExpected'],
    [{'case': n['case'], 'expect': n['expect'], 'failed': [k for k, v in n['checks'].items() if not v], 'boundsDiff_m': n['boundsDiff_m']} for n in nd['negatives']],
    ['qa/negatives-and-drift.json', 'source/negatives_drift.py'])

# C5 old nodes do not drift
s5 = nd['summary']
add('C5', 'old 66 nodes keep identical N, asset SHA and bounds from bce3211 to f28d650; port world coords recompute identically', s5['oldNodesPresentInF28d650'] == 66 and s5['oldNodeMaxMatrixDiff'] == 0 and not s5['oldNodesAssetOrShaChanged'] and not s5['oldNodesBoundsChanged'] and s5['portsWorldRecomputedFromF28d650_maxDiff_m'] == 0,
    s5, ['qa/negatives-and-drift.json', 'qa/f28d650/dump-f28d650.json', 'qa/f28d650/dump-bce3211-blob.json', 'qa/f28d650/city-data.mjs', 'qa/f28d650/city-data.bce3211.mjs'])

# C6 ports: required fields + invariant world = N local
P = J('qa/ports-bce3211.json')
schema = J('port-schema.json')
bad = []
for p in P['ports']:
    miss = [k for k in schema['required'] if k not in p]
    N = np.array(p['nodeMatrixColumnMajor']).reshape(4, 4).T
    w = N[:3, :3] @ np.array(p['local']['position']) + N[:3, 3]
    r = float(np.max(np.abs(w - np.array(p['world']['position']))))
    up = float(np.max(np.abs(N[:3, :3] @ np.array(p['local']['up']) - np.array(p['world']['up']))))
    if miss or r > 1e-6 or up > 1e-6 or p['kind'] not in schema['properties']['kind']['enum']:
        bad.append({'port': p['portId'], 'missing': miss, 'residual': r, 'upResidual': up})
dump = J('qa/city-data.dump.json'); nodes = {n['id']: n for n in dump['nodes']}
mm = 0.0
for p in P['ports']:
    n = nodes[p['owner']['nodeId']]
    if n.get('matrix'):
        mm = max(mm, float(np.max(np.abs(np.array(n['matrix']) - np.array(p['nodeMatrixColumnMajor'])))))
add('C6', 'every port carries local+world, schema fields, and world = N*local with N equal to city-data', not bad and mm == 0,
    {'ports': len(P['ports']), 'bad': bad, 'maxMatrixVsCityData': mm}, ['qa/ports-bce3211.json', 'port-schema.json', 'qa/city-data.dump.json', 'source/elevation_ports.py', 'source/vray.py'])

# C7 elevation
E = J('qa/elevation-survey.json')
cy = E['courtyards']
add('C7', '44 courtyard bases sit on delivered terrain within 2 mm (220 vertical samples)', all(c['samplesWithTerrain'] == 5 and abs(c['gapMin_m']) <= 2e-3 and abs(c['gapMax_m']) <= 2e-3 for c in cy),
    {'courtyards': len(cy), 'gapMin_m': min(c['gapMin_m'] for c in cy), 'gapMax_m': max(c['gapMax_m'] for c in cy), 'groundNodes': E['groundNodes']}, ['qa/elevation-survey.json'])

# C8 f28d650 consumes the frozen apron port without a step
F = J('qa/f28d650-port-consumption.json')
add('C8', 'f28d650 yong-road-link starts on port yong-gate:apron-edge-inner:ground with |step| <= 2 mm and identical N', abs(F['elevationStep_m']) <= 2e-3 and F['consumer']['nodeMatrixEqualsPortOwnerMatrix'] == 0,
    F, ['qa/f28d650-port-consumption.json', 'qa/f28d650/glb/yong-road-link-LOD0.glb'])

# C9 lab untouched
after = subprocess.run(['git', '-C', 'D:/GitHub/creation-notebook-lab', 'status', '--porcelain'], capture_output=True, text=True).stdout
head = subprocess.run(['git', '-C', 'D:/GitHub/creation-notebook-lab', 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
before = open(q('qa/lab-status-before.txt'), encoding='utf-8').read().splitlines()
open(q('qa/lab-status-after.txt'), 'w', encoding='utf-8').write(head + '\n' + after)
add('C9', 'lab repo HEAD and working-tree status unchanged by LY-005', head == before[0] and sorted(after.splitlines()) == sorted(before[2:]),
    {'headBefore': before[0], 'headAfter': head, 'statusBefore': before[2:], 'statusAfter': after.splitlines()}, ['qa/lab-status-before.txt', 'qa/lab-status-after.txt'])

out = {'seat': 'LY-005', 'baseline': 'bce3211f818ee5a8bef1773539da70695ba37b17', 'allPass': all(c['pass'] for c in checks), 'checks': checks}
json.dump(out, open(q('qa/checks.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for c in checks:
    print(c['id'], c['pass'], c['title'])
