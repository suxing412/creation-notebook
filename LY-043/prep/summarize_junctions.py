# LY-043 prep: digest of junctions-all.json (exact box census) into the numbers quoted in brief-draft.md.
# usage: python -I summarize_junctions.py junctions-all.json junctions-summary.json
import sys, json
import numpy as np
r = json.load(open(sys.argv[1], encoding='utf-8'))
out = {'source': sys.argv[1], 'files': {}, 'lodIdentity': {}}
for lab, f in r['files'].items():
    B = f['boxes']
    classes = {}
    for p in f['pairs']:
        classes[p['class']] = classes.get(p['class'], 0) + 1
    ringj = []
    for p in f['pairs']:
        if p['kind'] == 'part-part':
            continue
        a, b = B[p['a']], B[p['b']]
        ringj.append({'kind': p['kind'], 'class': p['class'], 'axis': p.get('axis'), 'contactArea_m2': p.get('contactArea_m2'),
                      'gap_m': p['gap_m'], 'a': [a['node'], a['min'], a['max']], 'b': [b['node'], b['min'], b['max']]})
    # ring end faces: area of each ring box face that lies inside the lot and is touched by a contact
    endface = []
    for i in f['ringBoxes']:
        x = B[i]; mn, mx = np.array(x['min']), np.array(x['max']); ext = mx - mn
        long_ax = 0 if ext[0] > ext[2] else 2; short_ax = 2 - long_ax
        face_area = ext[1] * ext[short_ax]
        for end, coord in (('min', mn[long_ax]), ('max', mx[long_ax])):
            touched = [p for p in f['pairs'] if i in (p['a'], p['b']) and p['class'] == 'face-contact' and p.get('axis') == 'xyz'[long_ax]
                       and abs((B[p['b'] if p['a'] == i else p['a']]['max' if end == 'min' else 'min'][long_ax]) - coord) < 1e-4]
            cov = sum(p['contactArea_m2'] for p in touched)
            endface.append({'ringBox': i, 'end': 'xyz'[long_ax] + end, 'at': round(float(coord), 4), 'faceArea_m2': round(float(face_area), 4),
                            'contactArea_m2': round(float(cov), 4), 'exposedClosedArea_m2': round(float(face_area - cov), 4),
                            'partners': [B[p['b'] if p['a'] == i else p['a']]['role'] + ':' + str(p['b'] if p['a'] == i else p['a']) for p in touched]})
    house = [c for c in f['clearanceToRing'] if c['role'] in ('earth', 'plinth') and c['gapToRing_m'] > 0]
    touching = [c for c in f['clearanceToRing'] if c['gapToRing_m'] == 0]
    out['files'][lab] = {
        'sha256': f['sha256'], 'boxes': len(B), 'ringBoxes': len(f['ringBoxes']),
        'nodes': {k: {kk: v[kk] for kk in ('triangles', 'boxes', 'boxTriangles', 'unmatchedRectangles', 'nonAxisTriangles', 'openEdges',
                                             'storedNormalOpposesWinding', 'sameFacingDuplicateRects')} for k, v in f['nodes'].items()},
        'pairClassTotals': classes, 'intrusionOrContainment': classes.get('intrusion', 0) + classes.get('containment', 0),
        'ringJunctions': ringj, 'ringEndFaces': endface,
        'partsTouchingRing': [[c['role'], c['min'], c['max']] for c in touching],
        'nearestFreeStandingEarthOrPlinthGap_m': min((c['gapToRing_m'] for c in house), default=None),
        'nearestFreeStandingEarthOrPlinth': min(house, key=lambda c: c['gapToRing_m']) if house else None,
        'residual': f['residual'], 'roofVsRing': f['roofVsRing']}
# LOD identity: same box set?
def boxset(f):
    return sorted((b['role'], tuple(b['min']), tuple(b['max'])) for b in f['boxes'])
pairs = [('A/LOD0', 'A/LOD1'), ('B/LOD0', 'B/LOD1'), ('TC03/LOD0', 'TC03/LOD1'), ('A2/LOD0', 'A2/LOD1'), ('B2/LOD0', 'B2/LOD1'),
         ('TC03-2/LOD0', 'TC03-2/LOD1'), ('wallhouse/LOD0', 'wallhouse/LOD1'), ('wallhouse/LOD0', 'wallhouse/LOD2'),
         ('A2/LOD0', 'C2/A2-LOD0'), ('A2/LOD1', 'C2/A2-LOD1'), ('A/LOD0', 'A2/LOD0'), ('B/LOD0', 'B2/LOD0'), ('TC03/LOD0', 'TC03-2/LOD0')]
for a, b in pairs:
    if a in r['files'] and b in r['files']:
        A, Bb = boxset(r['files'][a]), boxset(r['files'][b])
        out['lodIdentity'][a + ' vs ' + b] = {'identicalBoxSet': A == Bb, 'onlyInFirst': len(set(A) - set(Bb)), 'onlyInSecond': len(set(Bb) - set(A))}
json.dump(out, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for lab, f in out['files'].items():
    print(lab, 'intr', f['intrusionOrContainment'], 'touch', len(f['partsTouchingRing']), 'freeGap', f['nearestFreeStandingEarthOrPlinthGap_m'],
          'open', {k[:20]: v['openEdges'] for k, v in f['nodes'].items()}, 'dup', sum(v['sameFacingDuplicateRects'] for v in f['nodes'].values()),
          'flip', sum(v['storedNormalOpposesWinding'] for v in f['nodes'].values()),
          'ends', [(e['end'], e['faceArea_m2'], e['contactArea_m2'], e['exposedClosedArea_m2']) for e in f['ringEndFaces'] if e['contactArea_m2'] > 0])
print(json.dumps(out['lodIdentity'], indent=0))
