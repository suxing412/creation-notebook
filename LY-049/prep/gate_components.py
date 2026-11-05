# LY-049 prep: exact connected components of the A2 gate (local frame, glTF axes) for both LODs.
# Usage: python gate_components.py > gate-components.json
import json, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glb49

LAB = 'D:/GitHub/creation-notebook-lab/docs/cities/luoyang/'
FILES = {'LOD0': 'assets/c02v/A2-LOD0-prototype.glb', 'LOD1': 'assets/c02v/A2-LOD1-prototype.glb'}
REG = dict(x0=-6.0, x1=-1.0, z0=8.5, z1=12.5)  # local gate region


def comps(t):
    parent = list(range(len(t))); key = {}
    def f(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for i, tri in enumerate(t.round(5)):
        for v in map(tuple, tri):
            if v in key:
                parent[f(i)] = f(key[v])
            else:
                key[v] = i
    out = {}
    for i in range(len(t)):
        out.setdefault(f(i), []).append(i)
    return list(out.values())


res = {}
for lod, f in FILES.items():
    r = glb49.node_tris(LAB + f)
    items = []
    for node, t in r.items():
        mx, mn = t.max(1), t.min(1)
        k = (mx[:, 2] > REG['z0']) & (mn[:, 2] < REG['z1']) & (mn[:, 0] < REG['x1']) & (mx[:, 0] > REG['x0'])
        t = t[k]
        if not len(t):
            continue
        for c in comps(t):
            P = t[c].reshape(-1, 3)
            items.append(dict(node=node, tris=len(c), min=P.min(0).round(4).tolist(), max=P.max(0).round(4).tolist()))
    items.sort(key=lambda d: (d['node'], d['min'][2], d['min'][0]))
    res[lod] = dict(file=f, sha256=glb49.sha256(LAB + f), regionLocal=REG, components=items)
same = [ (a['node'], a['min'], a['max']) for a in res['LOD0']['components'] if a['node'] != 'architecture_C_roof_rhythm_not_glaze_copy.001'] == \
       [ (a['node'], a['min'], a['max']) for a in res['LOD1']['components'] if a['node'] != 'architecture_C_roof_rhythm_not_glaze_copy.001']
res['nonRoofComponentsIdenticalLOD0LOD1'] = same
res['derived'] = dict(
    frontRingOpeningLocalX=[-5.0, -2.0], frontRingZ=[11.65, 12.0], openingWidthAtBoundary_m=3.0,
    cheekWallsInnerLocalX=[-4.7, -2.3], cheekWallsZ=[9.4, 11.8], cheekClear_m=2.4,
    jambPostsInnerLocalX=[-4.565, -2.435], jambPostsZ=[10.45, 11.55], postsClear_m=2.13,
    lintelBottomY=2.25, clearHeightAboveGround0p2_m=2.05, postTopY=2.2, postToLintelGap_m=0.05,
    note='postToLintelGap: jamb posts (y 0.2..2.2) do not touch lintels (y 2.25..2.65); inherited C geometry, not a route issue')
print(json.dumps(res, ensure_ascii=False, indent=1))
