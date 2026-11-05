# LY-043 prep: positive + negative self-test of the junction checker on in-memory copies of A2-LOD0.
# Nothing is written to the lab repo; mutations are applied to numpy arrays only.
# usage: python -I selftest_junctions.py <docs_root> <out_json>
import sys, os, json, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from glbio import sha256
from nodegeo import node_geometry
from measure_box_junctions import analyze

DOCS, OUT = sys.argv[1], sys.argv[2]
REL = 'cities/luoyang/assets/c02v/A2-LOD0-prototype.glb'
EARTH = 'architecture_C_whitebox_earth_wall.001'
base = node_geometry(os.path.join(DOCS, REL))


def summary(rec):
    s = rec.pop('_summary')
    cls = {}
    for p in rec['pairs']:
        cls.setdefault(p['kind'], {}).setdefault(p['class'], 0); cls[p['kind']][p['class']] += 1
    e = rec['nodes'][EARTH]
    intr = [p for p in rec['pairs'] if p['class'] in ('intrusion', 'containment')]
    ringearth = [p for p in rec['pairs'] if p['kind'] == 'ring-earth']
    return {'boxes': s[0], 'ringBoxes': s[1], 'pairs': cls, 'earthOpenEdges': e['openEdges'], 'earthBoxes': e['boxes'],
            'earthUnmatchedRects': e['unmatchedRectangles'], 'earthNonAxisTris': e['nonAxisTriangles'],
            'earthSameFacingDup': e['sameFacingDuplicateRects'], 'earthNormalVsWinding': e['storedNormalOpposesWinding'],
            'intrusions': [{'class': p['class'], 'overlapVolume_m3': p['overlapVolume_m3'], 'kind': p['kind']} for p in intr],
            'ringEarth': [{'class': p['class'], 'contactArea_m2': p.get('contactArea_m2'), 'gap_m': p['gap_m']} for p in ringearth]}


def sel(t, cond):
    return np.nonzero([cond(x) for x in t])[0]


def gate_pier(t):   # west gate pier x -5..-4.7, z 9.4..11.8
    return sel(t, lambda x: (x[:, 0] >= -5.0001).all() and (x[:, 0] <= -4.6999).all() and (x[:, 2] >= 9.3999).all() and (x[:, 2] <= 11.8001).all())


def ring_end_face(t):  # ring box x -8.65..-5, z 11.65..12: its +x end face at x = -5
    return sel(t, lambda x: np.allclose(x[:, 0], -5.0, atol=1e-4) and (x[:, 2] >= 11.6499).all() and (x[:, 2] <= 12.0001).all())


cases = {}
cases['P0-unmodified'] = summary(analyze(base))

g = copy.deepcopy(base); t, n = g[EARTH]
idx = ring_end_face(t); keep = np.setdiff1d(np.arange(len(t)), idx)
g[EARTH] = (t[keep], n[keep])
cases['N1-delete-ring-end-face'] = dict(summary(analyze(g)), removedTriangles=int(len(idx)))

g = copy.deepcopy(base); t, n = g[EARTH]; t = t.copy()
idx = gate_pier(t); t[idx, :, 0] -= 0.05
g[EARTH] = (t, n)
cases['N2-pier-pushed-0.05m-into-ring'] = dict(summary(analyze(g)), movedTriangles=int(len(idx)), expectedOverlap_m3=round(0.05 * 0.15 * 2.2, 6))

g = copy.deepcopy(base); t, n = g[EARTH]; t = t.copy()
idx = gate_pier(t); t[idx, :, 0] += 0.02
g[EARTH] = (t, n)
cases['N3-pier-pulled-0.02m-from-ring'] = dict(summary(analyze(g)), movedTriangles=int(len(idx)))

g = copy.deepcopy(base); t, n = g[EARTH]
idx = ring_end_face(t)
g[EARTH] = (np.concatenate([t, t[idx]]), np.concatenate([n, n[idx]]))
cases['N4-duplicate-face'] = dict(summary(analyze(g)), duplicatedTriangles=int(len(idx)))

g = copy.deepcopy(base); t, n = g[EARTH]; t = t.copy()
idx = ring_end_face(t); t[idx] = t[idx][:, ::-1, :]
g[EARTH] = (t, n)
cases['N5-flip-winding-keep-normals'] = dict(summary(analyze(g)), flippedTriangles=int(len(idx)))

P = cases['P0-unmodified']
verdict = {
    'P0': P['intrusions'] == [] and P['earthOpenEdges'] == 0 and P['ringBoxes'] == 5 and P['earthSameFacingDup'] == 0 and P['earthNormalVsWinding'] == 0
          and sorted(x['contactArea_m2'] for x in P['ringEarth']) == [0.33, 0.33],
    'N1': cases['N1-delete-ring-end-face']['earthOpenEdges'] > 0 and cases['N1-delete-ring-end-face']['earthBoxes'] < P['earthBoxes'],
    'N2': any(abs(x['overlapVolume_m3'] - 0.0165) < 1e-4 and x['kind'] == 'ring-earth' for x in cases['N2-pier-pushed-0.05m-into-ring']['intrusions']),
    'N3': any(abs(x['gap_m'] - 0.02) < 1e-4 and x['class'] == 'separate' for x in cases['N3-pier-pulled-0.02m-from-ring']['ringEarth']),
    'N4': cases['N4-duplicate-face']['earthSameFacingDup'] >= 1,
    'N5': cases['N5-flip-winding-keep-normals']['earthNormalVsWinding'] > 0 and cases['N5-flip-winding-keep-normals']['earthBoxes'] < P['earthBoxes'],
}
out = {'tool': 'selftest_junctions.py', 'input': REL, 'sha256': sha256(os.path.join(DOCS, REL)), 'cases': cases, 'verdict': verdict,
       'allPass': all(verdict.values())}
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(verdict), 'allPass', out['allPass'])
for k, v in cases.items():
    print(k, {kk: v[kk] for kk in ('ringBoxes', 'earthBoxes', 'earthOpenEdges', 'earthSameFacingDup', 'earthNormalVsWinding')}, v['intrusions'], v['ringEarth'])
