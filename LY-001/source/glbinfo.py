"""Minimal read-only GLB reader: JSON chunk, node world matrices, per-mesh world AABB,
and (for uncompressed files) triangle positions in world space.  No writes to inputs."""
import json, struct
import numpy as np

COMP = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NCOMP = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def read_glb(path):
    data = open(path, 'rb').read()
    magic, version, length = struct.unpack_from('<4sII', data, 0)
    if magic != b'glTF':
        raise ValueError('not glb')
    off = 12
    js = None
    binc = None
    while off < len(data):
        clen, ctype = struct.unpack_from('<II', data, off)
        chunk = data[off + 8: off + 8 + clen]
        if ctype == 0x4E4F534A:
            js = json.loads(chunk.decode('utf8'))
        elif ctype == 0x004E4942:
            binc = chunk
        off += 8 + clen
    return js, binc, version, length


def node_local(n):
    if 'matrix' in n:
        return np.array(n['matrix'], dtype=float).reshape(4, 4).T
    t = n.get('translation', [0, 0, 0])
    r = n.get('rotation', [0, 0, 0, 1])
    s = n.get('scale', [1, 1, 1])
    x, y, z, w = r
    R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    M = np.eye(4)
    M[:3, :3] = R @ np.diag(s)
    M[:3, 3] = t
    return M


def walk(js):
    """yield (node_index, world_matrix, ancestor_names) for every node in the default scene."""
    nodes = js.get('nodes', [])
    scenes = js.get('scenes', [{'nodes': list(range(len(nodes)))}])
    sc = scenes[js.get('scene', 0)] if scenes else {'nodes': []}
    stack = [(i, np.eye(4), []) for i in sc.get('nodes', [])]
    while stack:
        i, parent, anc = stack.pop()
        n = nodes[i]
        W = parent @ node_local(n)
        names = anc + [n.get('name', f'#{i}')]
        yield i, W, names
        for c in n.get('children', []):
            stack.append((c, W, names))


def accessor(js, binc, idx):
    a = js['accessors'][idx]
    if 'bufferView' not in a:
        return None
    bv = js['bufferViews'][a['bufferView']]
    if 'extensions' in bv and 'EXT_meshopt_compression' in bv['extensions']:
        return None  # compressed: caller falls back to accessor min/max
    dt = COMP[a['componentType']]
    nc = NCOMP[a['type']]
    stride = bv.get('byteStride', 0)
    base = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    cnt = a['count']
    isz = np.dtype(dt).itemsize
    if stride and stride != isz * nc:
        raw = np.frombuffer(binc, dtype=np.uint8, count=stride * (cnt - 1) + isz * nc, offset=base)
        out = np.lib.stride_tricks.as_strided(raw, shape=(cnt, isz * nc), strides=(stride, 1)).copy()
        arr = out.view(dt).reshape(cnt, nc)
    else:
        arr = np.frombuffer(binc, dtype=dt, count=cnt * nc, offset=base).reshape(cnt, nc)
    arr = arr.astype(float)
    if a.get('normalized'):
        arr = arr / float(np.iinfo(dt).max)
    return arr


def summarize(path, want_tris=False, exclude=()):
    js, binc, version, length = read_glb(path)
    ext = js.get('extensionsUsed', [])
    meshes = js.get('meshes', [])
    acc = js.get('accessors', [])
    info = {'version': js.get('asset', {}).get('version'), 'generator': js.get('asset', {}).get('generator'),
            'extUsed': ext, 'extReq': js.get('extensionsRequired', []), 'nodes': len(js.get('nodes', [])),
            'meshes': len(meshes), 'materials': len(js.get('materials', [])), 'images': len(js.get('images', [])),
            'animations': len(js.get('animations', [])), 'skins': len(js.get('skins', []))}
    names = []
    prims = tris = 0
    boxes = []  # (names, mn, mx) world
    tri_sets = []
    excluded_hit = set()
    ex = set(exclude)
    lo = np.full(3, np.inf)
    hi = np.full(3, -np.inf)
    for i, W, anc in walk(js):
        n = js['nodes'][i]
        names.append(n.get('name', f'#{i}'))
        if 'mesh' not in n:
            continue
        hidden = [a for a in anc if a in ex]
        for p in meshes[n['mesh']].get('primitives', []):
            prims += 1
            pa = p['attributes'].get('POSITION')
            if pa is None:
                continue
            a = acc[pa]
            cnt = acc[p['indices']]['count'] if 'indices' in p else a['count']
            if p.get('mode', 4) == 4:
                tris += cnt // 3
            if hidden:
                excluded_hit.update(hidden)
                continue
            mn, mx = np.array(a.get('min', [0, 0, 0])), np.array(a.get('max', [0, 0, 0]))
            corners = np.array([[x, y, z, 1] for x in (mn[0], mx[0]) for y in (mn[1], mx[1]) for z in (mn[2], mx[2])])
            wc = (W @ corners.T).T[:, :3]
            boxes.append((anc[-1], wc))
            lo = np.minimum(lo, wc.min(0))
            hi = np.maximum(hi, wc.max(0))
            if want_tris:
                pos = accessor(js, binc, pa)
                if pos is None:
                    continue
                if 'indices' in p:
                    ind = accessor(js, binc, p['indices'])
                    if ind is None:
                        continue
                    ind = ind.astype(np.int64).ravel()
                else:
                    ind = np.arange(len(pos))
                if p.get('mode', 4) != 4:
                    continue
                P = np.c_[pos, np.ones(len(pos))] @ W.T
                tri_sets.append(P[:, :3][ind].reshape(-1, 3, 3))
    info.update({'primitives': prims, 'triangles': tris, 'nodeNames': names,
                 'worldMin': lo.tolist() if np.isfinite(lo).all() else None,
                 'worldMax': hi.tolist() if np.isfinite(hi).all() else None,
                 'excludeMatched': sorted(excluded_hit)})
    return info, boxes, (np.concatenate(tri_sets) if tri_sets else None)
