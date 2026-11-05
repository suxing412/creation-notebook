# LY-080 prep: read-only geometry measurement of the published northern altar GLBs
# and of the city's loaded ground GLBs. Pure numpy GLB reader (no Blender), writes JSON.
# Usage: python -I measure_altar.py <lab_repo_root> <out_json>
import sys, json, struct, hashlib, os
from collections import Counter, defaultdict
import numpy as np

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def load(path):
    b = open(path, 'rb').read()
    magic, ver, length = struct.unpack_from('<III', b, 0)
    assert magic == 0x46546C67, 'not glb'
    assert length == len(b), 'glb length mismatch'
    off = 12; js = binc = None
    while off < length:
        clen, ctype = struct.unpack_from('<II', b, off); off += 8
        chunk = b[off:off + clen]; off += clen
        if ctype == 0x4E4F534A: js = json.loads(chunk.decode('utf-8'))
        elif ctype == 0x004E4942: binc = chunk
    return js, binc


def acc(js, binc, i):
    a = js['accessors'][i]; bv = js['bufferViews'][a['bufferView']]
    dt = CT[a['componentType']]; n = NC[a['type']]
    start = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = bv.get('byteStride', 0); isz = np.dtype(dt).itemsize * n
    if stride and stride != isz:
        raw = np.frombuffer(binc, np.uint8, stride * a['count'], start).reshape(a['count'], stride)[:, :isz]
        return np.frombuffer(raw.tobytes(), dt).reshape(a['count'], n)
    return np.frombuffer(binc, dt, a['count'] * n, start).reshape(a['count'], n)


def node_mats(js):
    """world matrices per mesh node (column-major glTF)."""
    out = []
    def local(nd):
        if 'matrix' in nd: return np.array(nd['matrix'], float).reshape(4, 4).T
        T = np.eye(4); T[:3, 3] = nd.get('translation', [0, 0, 0])
        x, y, z, w = nd.get('rotation', [0, 0, 0, 1])
        R = np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                      [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                      [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
        S = np.diag(nd.get('scale', [1, 1, 1]))
        M = np.eye(4); M[:3, :3] = R @ S
        return T @ M
    def walk(i, P):
        nd = js['nodes'][i]; W = P @ local(nd)
        if 'mesh' in nd: out.append((i, W))
        for c in nd.get('children', []): walk(c, W)
    for r in js['scenes'][js.get('scene', 0)]['nodes']: walk(r, np.eye(4))
    return out


def tris_world(path):
    js, binc = load(path)
    Ps, Is, base = [], [], 0
    for ni, W in node_mats(js):
        for prim in js['meshes'][js['nodes'][ni]['mesh']]['primitives']:
            P = acc(js, binc, prim['attributes']['POSITION']).astype(np.float64)
            P = (np.c_[P, np.ones(len(P))] @ W.T)[:, :3]
            I = acc(js, binc, prim['indices']).astype(np.int64).reshape(-1, 3)
            Ps.append(P); Is.append(I + base); base += len(P)
    return js, np.vstack(Ps), np.vstack(Is)


def altar_metrics(path):
    js, P, I = tris_world(path)
    v0, v1, v2 = P[I[:, 0]], P[I[:, 1]], P[I[:, 2]]
    cr = np.cross(v1 - v0, v2 - v0); area = np.linalg.norm(cr, axis=1) / 2
    gn = cr / np.maximum(np.linalg.norm(cr, axis=1, keepdims=True), 1e-12)
    cen = (v0 + v1 + v2) / 3
    # weld by rounded position for topology
    key = np.round(P, 5); uniq, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
    T = inv[I]
    edges = Counter()
    for a, b, c in T:
        for e in ((a, b), (b, c), (c, a)): edges[tuple(sorted(e))] += 1
    nonman = sum(1 for v in edges.values() if v != 2)
    # directed edge consistency (orientation)
    dirc = Counter()
    for a, b, c in T:
        for e in ((a, b), (b, c), (c, a)): dirc[e] += 1
    flipped = sum(1 for e, n in dirc.items() if n > 1)
    # islands
    parent = list(range(len(uniq)))
    def f(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for a, b, c in T: parent[f(a)] = f(b); parent[f(b)] = f(c)
    islands = len({f(x) for x in set(T.ravel().tolist())})
    vol = float(np.einsum('ij,ij->i', v0, np.cross(v1, v2)).sum() / 6)
    up = np.abs(gn[:, 1] - 1) < 1e-4; dn = np.abs(gn[:, 1] + 1) < 1e-4
    bottom_y0 = float(area[dn & (np.abs(cen[:, 1]) < 1e-5)].sum())
    down_above0 = float(area[dn & (cen[:, 1] > 1e-5)].sum())
    nonaxis = int((~(up | dn | (np.abs(np.abs(gn[:, 0]) - 1) < 1e-4) | (np.abs(np.abs(gn[:, 2]) - 1) < 1e-4))).sum())
    top12 = float(area[up & (np.abs(cen[:, 1] - 1.2) < 1e-5)].sum())
    # stairs per side: up-facing faces outside core |u|>10 (outward axis)
    sides = {'+X(east)': (0, 1), '-X(west)': (0, -1), '+Z(south)': (2, 1), '-Z(north)': (2, -1)}
    stairs = {}
    for name, (ax, s) in sides.items():
        tan = 2 if ax == 0 else 0
        sel = up & (s * cen[:, ax] > 10.0 + 1e-6)
        treads = defaultdict(lambda: [1e9, -1e9, 1e9, -1e9, 0.0])
        for t in np.where(sel)[0]:
            y = round(cen[t, 1], 4); vs = np.stack([v0[t], v1[t], v2[t]])
            r = treads[y]
            r[0] = min(r[0], (s * vs[:, ax]).min()); r[1] = max(r[1], (s * vs[:, ax]).max())
            r[2] = min(r[2], vs[:, tan].min()); r[3] = max(r[3], vs[:, tan].max()); r[4] += area[t]
        levels = sorted(treads)
        tl = [{'y': y, 'outFrom': round(treads[y][0], 4), 'outTo': round(treads[y][1], 4),
               'depth': round(treads[y][1] - treads[y][0], 4), 'tanMin': round(treads[y][2], 4),
               'tanMax': round(treads[y][3], 4), 'area': round(treads[y][4], 4)} for y in levels]
        risers = [round(b - a, 4) for a, b in zip([0.0] + levels, levels + [1.2])]
        foot = s * max(t['outTo'] for t in tl)
        # support under stair footprint at y=0
        selb = dn & (np.abs(cen[:, 1]) < 1e-5) & (s * cen[:, ax] > 10.0 + 1e-6)
        sup = float(area[selb].sum())
        fp = (max(t['outTo'] for t in tl) - 10.0) * (tl[0]['tanMax'] - tl[0]['tanMin'])
        port = [0.0, 0.0, 0.0]; port[ax] = foot; port[tan] = round((tl[0]['tanMin'] + tl[0]['tanMax']) / 2, 4)
        stairs[name] = {'treads': tl, 'riserHeights_incl_last_to_1.2': risers, 'treadCount': len(tl),
                        'width': round(tl[0]['tanMax'] - tl[0]['tanMin'], 4),
                        'footPortLocal_glTF': port, 'outwardNormal_glTF': [s if i == ax else 0 for i in range(3)],
                        'supportAreaAtY0': round(sup, 4), 'stairFootprintArea_beyond_core': round(fp, 4),
                        'supportRatio': round(sup / fp, 4) if fp else None,
                        'blondel_2R_plus_T': round(2 * risers[0] + tl[0]['depth'], 4)}
    mn, mx = P.min(0), P.max(0)
    return {
        'path': path, 'sha256': sha(path), 'bytes': os.path.getsize(path),
        'triangles': int(len(I)), 'vertices': int(len(P)), 'weldedVertices': int(len(uniq)),
        'bboxMin': mn.round(5).tolist(), 'bboxMax': mx.round(5).tolist(), 'size': (mx - mn).round(5).tolist(),
        'nonManifoldEdges': nonman, 'duplicateDirectedEdges(orientation)': flipped, 'islands': islands,
        'signedVolume_m3': round(vol, 4), 'bottomAreaAtY0_m2': round(bottom_y0, 4),
        'downFacingAreaAboveY0_m2(overhang)': round(down_above0, 6), 'nonAxisAlignedTris': nonaxis,
        'topAreaAtY1.2_m2': round(top12, 4), 'stairs': stairs,
        'sceneExtras': js['scenes'][0].get('extras'), 'nodeExtras': [n.get('extras') for n in js['nodes']],
        'nodeNames': [n.get('name') for n in js['nodes']],
        'posHash': hashlib.sha256(np.round(P, 6).tobytes() + I.tobytes()).hexdigest(),
    }


def ground_metrics(path):
    js, P, I = tris_world(path)
    v0, v1, v2 = P[I[:, 0]], P[I[:, 1]], P[I[:, 2]]
    cr = np.cross(v1 - v0, v2 - v0); area = np.linalg.norm(cr, axis=1) / 2
    gn = cr / np.maximum(np.linalg.norm(cr, axis=1, keepdims=True), 1e-12)
    cen = (v0 + v1 + v2) / 3
    up = gn[:, 1] > 0.99
    hy = Counter(np.round(cen[up, 1], 3).tolist())
    return {'path': path, 'sha256': sha(path), 'triangles': int(len(I)),
            'bboxMin_local': P.min(0).round(3).tolist(), 'bboxMax_local': P.max(0).round(3).tolist(),
            'upFacingTopHeights_area_m2': {str(k): round(float(area[up][np.round(cen[up, 1], 3) == k].sum()), 1) for k in sorted(hy)},
            'minZ_upFacing': round(float(cen[up, 2].min()), 3)}


if __name__ == '__main__':
    root, out = sys.argv[1], sys.argv[2]
    md = os.path.join(root, 'docs/library/models/m-luoyang-northern-altar/files')
    res = {'altar': {}, 'ground': {}}
    for l in ('LOD0', 'LOD1', 'LOD2'):
        res['altar'][l] = altar_metrics(os.path.join(md, f'northern-altar-C-{l}.glb'))
    res['lodGeometryIdentical'] = len({res['altar'][l]['posHash'] for l in res['altar']}) == 1
    gd = os.path.join(root, 'docs/cities/luoyang/assets/ground-atomic')
    for g in ('network-ground-stitched', 'retained', 'south', 'D08'):
        res['ground'][g] = ground_metrics(os.path.join(gd, g + '.glb'))
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    a = res['altar']['LOD0']
    print('LOD0', a['size'], 'tris', a['triangles'], 'nonman', a['nonManifoldEdges'], 'islands', a['islands'],
          'vol', a['signedVolume_m3'], 'bottom', a['bottomAreaAtY0_m2'], 'overhang', a['downFacingAreaAboveY0_m2(overhang)'])
    for k, s in a['stairs'].items():
        print(k, 'treads', s['treadCount'], 'w', s['width'], 'risers', s['riserHeights_incl_last_to_1.2'],
              'depths', [t['depth'] for t in s['treads']], 'port', s['footPortLocal_glTF'], 'support', s['supportRatio'], '2R+T', s['blondel_2R_plus_T'])
    print('LOD identical', res['lodGeometryIdentical'])
    for g, m in res['ground'].items():
        print(g, m['triangles'], m['bboxMin_local'], m['bboxMax_local'], 'minZup', m['minZ_upFacing'], m['upFacingTopHeights_area_m2'])
