# LY-043 prep: exact junction census of courtyard-wall / house / gate parts (read-only on inputs).
# 1. Every earth / plinth / timber node is decomposed into exact axis-aligned closed boxes (boxes.py);
#    non-box leftovers (gable triangles, sloped or rotated pieces) are kept as residual triangles.
# 2. Enclosure ("ring") boxes = earth boxes that reach the lot's outer boundary.
# 3. Every box pair closer than NEAR is classified exactly: containment / intrusion (positive volume)
#    / face-contact (closed faces coincide: a legal closed interface) / edge-or-corner contact / gap.
# 4. Residual triangles are tested exactly (triangle-vs-box separating-axis test) against the interior
#    of every ring box shrunk by 1 mm, and their nearest vertex distance to the ring is reported.
# 5. Closure: per node, welded edges with odd use count (open boundary) and same-facing coincident
#    rectangles (duplicate faces / z-fight) are counted.
# usage: python -I measure_box_junctions.py <docs_root> <out_json> [labels,comma,separated]
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from glbio import sha256
from nodegeo import node_geometry
from boxes import boxes_from, rects, box_relation

DOCS = sys.argv[1] if __name__ == '__main__' else None
OUT = sys.argv[2] if __name__ == '__main__' else None
NEAR = 0.60       # m: report box pairs with a gap below this
SHRINK = 0.001    # m: ring interior shrink for residual intrusion test
CITY = 'cities/luoyang/assets/'
TARGETS = [
    ('A/LOD1', CITY + 'r01/R01-A-LOD1-prototype.glb'), ('A/LOD0', CITY + 'r01/R01-A-LOD0-prototype.glb'),
    ('B/LOD1', CITY + 'r01/R01-B-LOD1-prototype.glb'), ('B/LOD0', CITY + 'r01/R01-B-LOD0-prototype.glb'),
    ('TC03/LOD1', CITY + 'd08/TC03-LOD1-prototype.glb'), ('TC03/LOD0', CITY + 'd08/TC03-LOD0-prototype.glb'),
    ('A2/LOD1', CITY + 'c02v/A2-LOD1-prototype.glb'), ('A2/LOD0', CITY + 'c02v/A2-LOD0-prototype.glb'),
    ('B2/LOD1', CITY + 'c02v/B2-LOD1-prototype.glb'), ('B2/LOD0', CITY + 'c02v/B2-LOD0-prototype.glb'),
    ('TC03-2/LOD1', CITY + 'c02v/TC03-2-LOD1-prototype.glb'), ('TC03-2/LOD0', CITY + 'c02v/TC03-2-LOD0-prototype.glb'),
    ('wallhouse/LOD0', 'library/models/m-luoyang-wall-house-court/files/wall-house-LOD0.glb'),
    ('wallhouse/LOD1', 'library/models/m-luoyang-wall-house-court/files/wall-house-LOD1.glb'),
    ('wallhouse/LOD2', 'library/models/m-luoyang-wall-house-court/files/wall-house-LOD2.glb'),
    ('C2/A2-LOD0', 'model-library/updates/m-courtyard-family/files/A2-LOD0-C2.glb'),
    ('C2/A2-LOD1', 'model-library/updates/m-courtyard-family/files/A2-LOD1-C2.glb'),
]
if __name__ == '__main__' and len(sys.argv) > 3:
    keep = sys.argv[3].split(',')
    TARGETS = [t for t in TARGETS if t[0] in keep]


def role_of(name):
    for key, r in (('earth', 'earth'), ('plinth', 'plinth'), ('timber', 'timber')):
        if key in name:
            return r
    return None


def tri_box_overlap(tri, bmin, bmax):
    """exact SAT test: does triangle intersect the open box?"""
    c = (bmin + bmax) / 2; h = (bmax - bmin) / 2
    v = tri - c
    if (v.min(0) > h).any() or (v.max(0) < -h).any():
        return False
    e = [v[1] - v[0], v[2] - v[1], v[0] - v[2]]
    n = np.cross(e[0], e[1])
    if abs(n @ v[0]) > np.abs(n) @ h:
        return False
    for ei in e:
        for k in range(3):
            a = np.zeros(3); a[k] = 1
            ax = np.cross(a, ei)
            if np.linalg.norm(ax) < 1e-12:
                continue
            p = v @ ax; r = np.abs(ax) @ h
            if p.min() > r or p.max() < -r:
                return False
    return True


def open_edges(t):
    q = np.round(t.reshape(-1, 3) / 1e-4).astype(np.int64)
    _, inv = np.unique(q, axis=0, return_inverse=True); inv = inv.reshape(-1, 3)
    e = np.sort(np.concatenate([inv[:, [0, 1]], inv[:, [1, 2]], inv[:, [2, 0]]]), axis=1)
    _, cnt = np.unique(e, axis=0, return_counts=True)
    return int((cnt % 2 == 1).sum()), int((cnt > 2).sum())


def same_facing_dupes(tris):
    fs, _, _ = rects(tris)
    by = {}
    for f in fs:
        by.setdefault((f['axis'], f['sign'], round(f['c'], 4)), []).append(f)
    dup, area = 0, 0.0
    for L in by.values():
        for i in range(len(L)):
            for j in range(i + 1, len(L)):
                d = np.minimum(L[i]['hi'], L[j]['hi']) - np.maximum(L[i]['lo'], L[j]['lo'])
                if (d > 1e-4).all():
                    dup += 1; area += float(np.prod(d))
    return dup, round(area, 4)


def analyze(g):
    """g: node name -> (triangles, stored normals). Returns the per-file record (without path/sha)."""
    lot = g.get('site_lot')
    allsel = np.concatenate([t for k, (t, n) in g.items() if role_of(k)])
    if lot is not None:
        lmin, lmax = lot[0].reshape(-1, 3).min(0), lot[0].reshape(-1, 3).max(0)
    else:
        e = np.concatenate([t for k, (t, n) in g.items() if role_of(k) == 'earth']).reshape(-1, 3)
        lmin, lmax = e.min(0), e.max(0)
    boxes, residual, nodeinfo = [], [], {}
    for k, (t, n) in g.items():
        r = role_of(k)
        if not r:
            continue
        b, left, res, flipped = boxes_from(t, n)
        oe, nm = open_edges(t)
        dup, duparea = same_facing_dupes(t)
        nodeinfo[k] = {'role': r, 'triangles': int(len(t)), 'boxes': len(b), 'boxTriangles': int(sum(len(x['tris']) for x in b)),
                       'unmatchedRectangles': len(left), 'nonAxisTriangles': int(len(res)),
                       'storedNormalOpposesWinding': len(flipped), 'openEdges': oe, 'edgesUsedMoreThanTwice': nm,
                       'sameFacingDuplicateRects': dup, 'sameFacingDuplicateArea_m2': duparea}
        for x in b:
            x['node'] = k; x['role'] = r
            onb = (np.abs(x['min'][[0, 2]] - lmin[[0, 2]]) < 1e-3).any() or (np.abs(x['max'][[0, 2]] - lmax[[0, 2]]) < 1e-3).any()
            x['ring'] = bool(r == 'earth' and onb)
            boxes.append(x)
        boxed = set(i for x in b for i in x['tris'])
        rest = np.array([i for i in range(len(t)) if i not in boxed], dtype=int)
        if len(rest):
            residual.append((k, r, t[rest]))
    # enclosure rule: boundary-touching earth boxes at least 1.0 m tall whose top is within 0.05 m of the lowest such top
    # (house walls that stand on the lot edge, as in the wall-house study, are taller and stay 'part')
    # (plinth-like earth slabs under 1.0 m tall are never enclosure)
    for x in boxes:
        if x['ring'] and x['max'][1] - x['min'][1] < 1.0:
            x['ring'] = False; x['onLotEdge'] = True
    tops = [x['max'][1] for x in boxes if x['ring']]
    if tops:
        low = min(tops)
        for x in boxes:
            if x['ring'] and x['max'][1] > low + 0.05:
                x['ring'] = False; x['onLotEdge'] = True
    ring = [i for i, x in enumerate(boxes) if x['ring']]
    # pairwise exact relations
    pairs = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            gap = np.maximum(0, np.maximum(a['min'] - b['max'], b['min'] - a['max']))
            if np.linalg.norm(gap) > NEAR:
                continue
            rel = box_relation(a, b)
            kind = ('ring-ring' if a['ring'] and b['ring'] else
                    'ring-' + (b['role'] if a['ring'] else a['role']) if (a['ring'] or b['ring']) else
                    'part-part')
            pairs.append({'a': i, 'b': j, 'kind': kind, 'nodes': [a['node'], b['node']], **rel})
    # residual vs ring
    resid = []
    for k, r, rt in residual:
        hits = 0; mind = np.inf
        for ri in ring:
            bmin = boxes[ri]['min'] + SHRINK; bmax = boxes[ri]['max'] - SHRINK
            for tri in rt:
                if tri_box_overlap(tri, bmin, bmax):
                    hits += 1
            p = rt.reshape(-1, 3)
            d = np.linalg.norm(np.maximum(0, np.maximum(boxes[ri]['min'] - p, p - boxes[ri]['max'])), axis=1).min()
            mind = min(mind, float(d))
        resid.append({'node': k, 'role': r, 'triangles': int(len(rt)),
                      'bboxMin': np.round(rt.reshape(-1, 3).min(0), 4).tolist(), 'bboxMax': np.round(rt.reshape(-1, 3).max(0), 4).tolist(),
                      'trianglesIntersectingRingInterior': hits, 'nearestVertexToRing_m': round(mind, 4) if np.isfinite(mind) else None})
    # roof / tile vs ring interior
    roofhits = []
    for k, (t, n) in g.items():
        if 'roof' in k or 'tile' in k:
            h = 0
            for ri in ring:
                bmin = boxes[ri]['min'] + SHRINK; bmax = boxes[ri]['max'] - SHRINK
                cand = t[(t.min(1) < bmax).all(1) & (t.max(1) > bmin).all(1)]
                h += sum(1 for tri in cand if tri_box_overlap(tri, bmin, bmax))
            roofhits.append({'node': k, 'triangles': int(len(t)), 'trianglesIntersectingRingInterior': h})
    # nearest ring gap for every non-ring cluster (house) -> by node + role
    clear = []
    for i, x in enumerate(boxes):
        if x['ring']:
            continue
        best = min((box_relation(x, boxes[r])['gap_m'], r) for r in ring) if ring else (None, None)
        clear.append({'box': i, 'node': x['node'], 'role': x['role'], 'min': np.round(x['min'], 4).tolist(), 'max': np.round(x['max'], 4).tolist(),
                      'nearestRingBox': best[1], 'gapToRing_m': best[0]})
    cnt = {}
    for p in pairs:
        cnt.setdefault(p['kind'], {}).setdefault(p['class'], 0)
        cnt[p['kind']][p['class']] += 1
    rec = {'lotMin': np.round(lmin, 4).tolist(), 'lotMax': np.round(lmax, 4).tolist(), 'nodes': nodeinfo,
        'boxes': [{'i': i, 'node': x['node'], 'role': x['role'], 'ring': x['ring'], 'onLotEdge': bool(x.get('onLotEdge')), 'min': np.round(x['min'], 4).tolist(), 'max': np.round(x['max'], 4).tolist()} for i, x in enumerate(boxes)],
        'ringBoxes': ring, 'pairCounts': cnt, 'pairs': pairs, 'residual': resid, 'roofVsRing': roofhits, 'clearanceToRing': clear}
    rec['_summary'] = (len(boxes), len(ring), cnt, [(r['node'][:22], r['triangles'], r['trianglesIntersectingRingInterior'], r['nearestVertexToRing_m']) for r in resid], [(r['node'][:12], r['trianglesIntersectingRingInterior']) for r in roofhits])
    return rec


if __name__ == '__main__':
    t0 = time.time()
    report = {'tool': 'measure_box_junctions.py', 'near_m': NEAR, 'ringShrink_m': SHRINK,
              'scope': 'exact for the axis-aligned closed boxes recovered from each node; residual (non-box) triangles '
                       'are tested exactly against ring-box interiors only. Not a Boolean of the whole scene, not GPU, '
                       'not structural or walking verification.', 'inputs': {}, 'files': {}}
    for label, rel in TARGETS:
        path = os.path.join(DOCS, rel)
        sha = sha256(path); report['inputs'][rel] = sha
        rec = analyze(node_geometry(path))
        s = rec.pop('_summary')
        report['files'][label] = {'path': rel, 'sha256': sha, **rec}
        print(label, 'boxes', s[0], 'ring', s[1], json.dumps(s[2]), 'resid', s[3], 'roof', s[4], '%.1fs' % (time.time() - t0), flush=True)
    report['elapsed_s'] = round(time.time() - t0, 1)
    json.dump(report, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

