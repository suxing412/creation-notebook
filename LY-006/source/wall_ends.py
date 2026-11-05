# LY-006: measure every wall-end cap of the 12 city wall nodes (city-absolute, N = identity per LY-005),
# pair caps across gaps/joints, and emit frozen wall-end ports (local == world because N = I).
# Read-only on the lab repo. Usage: python -I wall_ends.py <lab docs dir> <city-data dump> <out json>
import json, sys, os, hashlib, numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(__file__))
from glbio import read_glb, mesh_items, apply

DOCS, DUMP, OUT = sys.argv[1:4]
dump = json.load(open(DUMP, encoding='utf-8'))
assets = {a['id']: a for a in dump['assets']}
walls = [n for n in dump['nodes'] if n['chapter'] == 'walls' and n['id'].startswith('wall-') and 'gate-body' not in n['id']]
geo = {}
for n in walls:
    a = assets[n['asset']]
    p = os.path.join(DOCS, 'cities/luoyang', a['sourcePath'])
    g = read_glb(p)
    V = []; T = []; off = 0
    for i, name, w, pos, tri, anc in mesh_items(g):
        wp = apply(w, pos); V.append(wp); T.append(tri + off); off += len(wp)
    V = np.concatenate(V); T = np.concatenate(T)
    M = n.get('matrix')
    assert M is None or np.allclose(np.array(M).reshape(4, 4).T, np.eye(4)), n['id']
    geo[n['id']] = {'V': V, 'T': T, 'path': 'docs/cities/luoyang/' + a['sourcePath'], 'sha256': g['sha256'], 'bytes': g['size'],
                    'matrix': M, 'position': n.get('position'), 'rotationY': n.get('rotationY')}

def caps(nid):
    """end caps: vertical triangles (|n_y|<0.05) whose plan span is 5..12 m (wall cross-section width),
    grouped by centroid proximity (<10 m). Outward direction = mean face normal (closed prisms, CCW outward)."""
    V, T = geo[nid]['V'], geo[nid]['T']
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    nrm = np.cross(b - a, c - a); area = 0.5 * np.linalg.norm(nrm, axis=1)
    nrm = nrm / np.maximum(np.linalg.norm(nrm, axis=1)[:, None], 1e-12)
    cen = (a + b + c) / 3
    P = np.stack([a, b, c], 1)[:, :, [0, 2]]
    span = np.max(np.linalg.norm(P[:, :, None, :] - P[:, None, :, :], axis=-1), axis=(1, 2))
    out = np.where((np.abs(nrm[:, 1]) < 0.05) & (span > 5) & (span < 12))[0]
    groups = []
    lab = -np.ones(len(out), int); g = 0
    for s_ in range(len(out)):
        if lab[s_] >= 0: continue
        lab[s_] = g
        for r in range(len(out)):
            if lab[r] < 0 and np.linalg.norm(cen[out[r], [0, 2]] - cen[out[s_], [0, 2]]) < 10: lab[r] = g
        g += 1
    for gi in range(g):
        ks = out[lab == gi]
        vs = np.unique(T[ks].reshape(-1)); Q = V[vs]
        h = np.array([nrm[ks, 0], nrm[ks, 2]]).T.mean(0); h /= np.linalg.norm(h)
        bot = Q[Q[:, 1] < Q[:, 1].min() + 1e-3]; top = Q[Q[:, 1] > Q[:, 1].max() - 1e-3]
        side = np.array([-h[1], h[0]])
        def wid(R):
            s2 = (R[:, [0, 2]] - R[:, [0, 2]].mean(0)) @ side
            return float(s2.max() - s2.min())
        bc = (bot.min(0) + bot.max(0)) / 2
        plane_off = (Q[:, [0, 2]] - bc[[0, 2]]) @ h
        groups.append({'triangles': int(len(ks)), 'area_m2': round(float(area[ks].sum()), 4),
                       'outwardPlan_xz': [round(float(h[0]), 6), round(float(h[1]), 6)],
                       'baseCenter': [round(float(x), 5) for x in bc],
                       'baseY': round(float(Q[:, 1].min()), 5), 'topY': round(float(Q[:, 1].max()), 5),
                       'baseWidth': round(wid(bot), 4), 'topWidth': round(wid(top), 4),
                       'planarity_m': round(float(np.ptp(plane_off)), 6)})
    return groups

res = {'baseline': 'bce3211f818ee5a8bef1773539da70695ba37b17', 'method': 'end-cap triangles = |n_y|<0.05 and plan span 5..12 m; grouped by centroid < 10 m; outward = mean normal; seams = facing caps (dot<-0.9) of different nodes within 60 m', 'walls': {}, 'seams': []}
for nid in geo:
    res['walls'][nid] = {'glb': geo[nid]['path'], 'sha256': geo[nid]['sha256'], 'bytes': geo[nid]['bytes'], 'caps': caps(nid)}
# pair caps across nodes: nearest cap of another node within 60 m, facing each other
allcaps = [(nid, i, c) for nid, w in res['walls'].items() for i, c in enumerate(w['caps'])]
used = set()
for a in range(len(allcaps)):
    na, ia, ca = allcaps[a]
    best = None
    for b in range(len(allcaps)):
        nb, ib, cb = allcaps[b]
        if nb == na: continue
        pa = np.array(ca['baseCenter'])[[0, 2]]; pb = np.array(cb['baseCenter'])[[0, 2]]
        d = float(np.linalg.norm(pb - pa))
        if d > 60: continue
        if np.dot(ca['outwardPlan_xz'], cb['outwardPlan_xz']) > -0.9: continue
        if best is None or d < best[0]: best = (d, b)
    if best:
        key = tuple(sorted([a, best[1]]))
        if key in used: continue
        used.add(key)
        nb, ib, cb = allcaps[best[1]]
        pa = np.array(ca['baseCenter']); pb = np.array(cb['baseCenter'])
        res['seams'].append({'a': [na, ia], 'b': [nb, ib], 'gap_plan_m': round(best[0], 4),
                             'midpoint': [round(float(x), 4) for x in (pa + pb) / 2],
                             'dBaseY_m': round(cb['baseY'] - ca['baseY'], 5)})
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for nid, w in res['walls'].items():
    print(nid, [(c['baseCenter'], c['outwardPlan_xz'], c['baseWidth'], c['topWidth'], c['planarity_m']) for c in w['caps']])
for s in res['seams']: print('SEAM', s)
