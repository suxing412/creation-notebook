# LY-047 prep: read-only GLB reader (numpy). Never writes to its inputs.
# World-space triangles per node, glTF axes (x right, y up, z toward viewer). Metres.
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
        arr = np.frombuffer(binc, dtype=dt, count=cnt * n, offset=base).reshape(cnt, n)
    else:
        arr = np.stack([np.frombuffer(binc, dtype=dt, count=n, offset=base + i * stride) for i in range(cnt)])
    return arr.astype(np.float64) if dt.kind == 'f' else arr.astype(np.int64)


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


def node_tris(path, root=None):
    """Return dict nodeName -> (tris Nx3x3 world, material names list). root: optional 4x4 (column-vector) applied on top."""
    js, binc = load(path)
    out = {}
    root = np.eye(4) if root is None else root
    mats = js.get('materials', [])

    def walk(ni, M):
        nd = js['nodes'][ni]
        W = M @ trs(nd)
        if 'mesh' in nd:
            name = nd.get('name', f'node{ni}')
            tl, ml = [], []
            for p in js['meshes'][nd['mesh']]['primitives']:
                P = acc(js, binc, p['attributes']['POSITION'])
                I = acc(js, binc, p['indices']).reshape(-1) if 'indices' in p else np.arange(len(P))
                Pw = (W @ np.c_[P, np.ones(len(P))].T).T[:, :3]
                tl.append(Pw[I.reshape(-1, 3)])
                ml.append(mats[p['material']].get('name', '?') if 'material' in p else None)
            T = np.concatenate(tl) if tl else np.zeros((0, 3, 3))
            if name in out:
                name = f'{name}#{ni}'
            out[name] = (T, ml)
        for c in nd.get('children', []):
            walk(c, W)

    sc = js['scenes'][js.get('scene', 0)]
    for r in sc['nodes']:
        walk(r, root)
    return out


def matrix_from_city(m16):
    """city-data matrices are column-major 16 arrays (three.js Matrix4.fromArray)."""
    return np.array(m16, dtype=np.float64).reshape(4, 4).T
