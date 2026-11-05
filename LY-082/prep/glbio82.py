# LY-082 prep: read-only GLB reader (numpy only). Never writes to inputs.
# glTF axes: x east, y up, z = -north (city-data convention).
import json, struct, hashlib
import numpy as np

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def load(path):
    data = open(path, 'rb').read()
    magic, ver, length = struct.unpack_from('<III', data, 0)
    assert magic == 0x46546C67, 'not glb'
    off, js, binc = 12, None, b''
    while off < length:
        clen, ctype = struct.unpack_from('<II', data, off)
        chunk = data[off + 8: off + 8 + clen]
        if ctype == 0x4E4F534A:
            js = json.loads(chunk.decode('utf8'))
        elif ctype == 0x004E4942:
            binc = chunk
        off += 8 + clen
    return js, binc


def acc(js, binc, idx):
    a = js['accessors'][idx]
    bv = js['bufferViews'][a['bufferView']]
    dt = np.dtype(CT[a['componentType']]); n = NC[a['type']]; cnt = a['count']
    stride = bv.get('byteStride', 0) or dt.itemsize * n
    base = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    if stride == dt.itemsize * n:
        return np.frombuffer(binc, dtype=dt, count=cnt * n, offset=base).reshape(cnt, n).astype(np.float64)
    arr = np.lib.stride_tricks.as_strided(
        np.frombuffer(binc, dtype=np.uint8, offset=base), shape=(cnt, dt.itemsize * n), strides=(stride, 1))
    return np.frombuffer(arr.copy().tobytes(), dtype=dt).reshape(cnt, n).astype(np.float64)


def trs(node):
    if 'matrix' in node:
        return np.array(node['matrix'], dtype=np.float64).reshape(4, 4).T
    t = np.array(node.get('translation', [0, 0, 0]), dtype=np.float64)
    x, y, z, w = node.get('rotation', [0, 0, 0, 1])
    R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    s = np.array(node.get('scale', [1, 1, 1]), dtype=np.float64)
    M = np.eye(4); M[:3, :3] = R * s; M[:3, 3] = t
    return M


def prim_tris(path, outer=None, skip=()):
    """List of dicts {node, mesh, prim, material, tris (N,3,3) world}."""
    js, binc = load(path)
    outer = np.eye(4) if outer is None else outer
    out = []
    scene = js['scenes'][js.get('scene', 0)]
    mats = js.get('materials', [])

    def walk(i, P):
        nd = js['nodes'][i]; M = P @ trs(nd); name = nd.get('name', f'node{i}')
        if 'mesh' in nd and name not in skip:
            for k, pr in enumerate(js['meshes'][nd['mesh']]['primitives']):
                if pr.get('mode', 4) != 4:
                    continue
                V = acc(js, binc, pr['attributes']['POSITION'])
                I = acc(js, binc, pr['indices']).astype(np.int64).reshape(-1) if 'indices' in pr else np.arange(len(V))
                Vw = (M @ np.c_[V, np.ones(len(V))].T).T[:, :3]
                mi = pr.get('material')
                out.append({'node': name, 'mesh': js['meshes'][nd['mesh']].get('name'), 'prim': k,
                            'material': mats[mi].get('name') if mi is not None else None,
                            'tris': Vw[I.reshape(-1, 3)]})
        for c in nd.get('children', []):
            walk(c, M)
    for r in scene['nodes']:
        walk(r, outer)
    return out


def translation(t):
    M = np.eye(4); M[:3, 3] = t; return M
