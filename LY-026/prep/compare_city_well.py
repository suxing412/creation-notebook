"""LY-026 prep: read-only comparison of the well A nodes inside the city-visible chunk
(market_frontage_well_routes.glb, extracted in memory from the 2026-11-04-city-visible ZIP parts)
against the library asset well-A-LOD0.glb. Compares node sets, world-offsets and well-local
triangle geometry (5-decimal rounded oriented triangle sets). Writes JSON to stdout.
Usage: python -I compare_city_well.py <library_glb> <chunk_glb> <out_json>
"""
import sys, json, hashlib
sys.path.insert(0, 'D:/GitHub/creation-notebook-workpacks/LY-001/source')
import numpy as np
from glbinfo import read_glb, walk, accessor


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def tri_world(js, binc):
    out = {}
    for i, W, anc in walk(js):
        n = js['nodes'][i]
        if 'mesh' not in n:
            continue
        tris = []
        for p in js['meshes'][n['mesh']]['primitives']:
            pos = accessor(js, binc, p['attributes']['POSITION'])
            ind = accessor(js, binc, p['indices']).astype(np.int64).ravel() if 'indices' in p else np.arange(len(pos))
            P = (W[:3, :3] @ pos.T).T + W[:3, 3]
            tris.append(P[ind].reshape(-1, 3, 3))
        out[anc[-1]] = (W, np.concatenate(tris) if tris else np.zeros((0, 3, 3)))
    return out


def canon(T):
    # oriented triangle canonical: rotate so lexicographically smallest vertex first
    r = np.round(T, 5)
    res = set()
    for t in r:
        k = [tuple(v) for v in t]
        m = min(range(3), key=lambda j: k[j])
        res.add(tuple(k[m:] + k[:m]))
    return res


lib, chunk, outp = sys.argv[1:4]
jl, bl, _, _ = read_glb(lib)
jc, bc, _, _ = read_glb(chunk)
L = tri_world(jl, bl)
C = tri_world(jc, bc)
lib_names = set(L)
city_A = {k for k in C if k.startswith('A_LOD0__')}
# estimate offset from a root-level part with identity local in library
ref = 'A_LOD0__short_liner'
off = C[ref][0][:3, 3] - L[ref][0][:3, 3]
rows = []
for k in sorted(lib_names | city_A):
    r = {'node': k, 'inLibrary': k in L, 'inCity': k in C}
    if k in L and k in C:
        Tl = L[k][1] + off
        Tc = C[k][1]
        r['triangles'] = [len(Tl), len(Tc)]
        r['rotScaleEqual'] = bool(np.allclose(L[k][0][:3, :3], C[k][0][:3, :3], atol=1e-6))
        sl, sc = canon(Tl), canon(Tc)
        r['orientedTriSetEqual_1e-5'] = sl == sc
        if sl != sc:
            r['onlyLibrary'] = len(sl - sc)
            r['onlyCity'] = len(sc - sl)
            if len(Tl) == len(Tc):
                r['maxVertexDelta'] = float(np.abs(np.sort(Tl.reshape(-1, 3), 0) - np.sort(Tc.reshape(-1, 3), 0)).max())
    rows.append(r)
res = {
    'library': {'path': lib, 'sha256': sha(lib)},
    'chunk': {'path': chunk, 'sha256': sha(chunk)},
    'worldOffsetGLB_Yup': off.tolist(),
    'worldOffsetBlender_Zup': [off[0], -off[2], off[1]],
    'libraryNodes': len(lib_names), 'cityANodes': len(city_A),
    'missingInCity': sorted(lib_names - city_A),
    'extraInCity': sorted(city_A - lib_names),
    'geometryMismatch': [r['node'] for r in rows if r.get('orientedTriSetEqual_1e-5') is False],
    'rows': rows,
}
json.dump(res, open(outp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'rows'}, ensure_ascii=False, indent=1))
