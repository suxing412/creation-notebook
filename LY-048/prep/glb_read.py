# LY-048 prep: minimal read-only GLB reader (numpy). Opens inputs 'rb' only.
# Returns {node_name: (N,3,3) float64 triangles} in glTF axes (x right, y up, z toward viewer),
# with the node hierarchy transforms applied (prototype-local space, no city matrix).
import json, struct, hashlib
import numpy as np

_CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
_NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def _load(path):
    data = open(path, 'rb').read()
    magic, _ver, length = struct.unpack_from('<III', data, 0)
    assert magic == 0x46546C67, 'not a GLB: ' + path
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


def _acc(js, binc, idx):
    a = js['accessors'][idx]
    bv = js['bufferViews'][a['bufferView']]
    dt = np.dtype(_CT[a['componentType']]); n = _NC[a['type']]; cnt = a['count']
    stride = bv.get('byteStride', 0) or dt.itemsize * n
    base = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    if stride == dt.itemsize * n:
        return np.frombuffer(binc, dtype=dt, count=cnt * n, offset=base).reshape(cnt, n).astype(np.float64)
    out = np.empty((cnt, n), dtype=np.float64)
    for i in range(cnt):
        out[i] = np.frombuffer(binc, dtype=dt, count=n, offset=base + i * stride)
    return out


def _local(node):
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


def node_tris(path):
    js, binc = _load(path)
    out = {}
    scene = js['scenes'][js.get('scene', 0)]

    def walk(ni, parent):
        nd = js['nodes'][ni]
        M = parent @ _local(nd)
        if 'mesh' in nd:
            name = nd.get('name', 'node%d' % ni)
            parts = []
            for pr in js['meshes'][nd['mesh']]['primitives']:
                if pr.get('mode', 4) != 4:
                    continue
                P = _acc(js, binc, pr['attributes']['POSITION'])
                I = _acc(js, binc, pr['indices']).astype(np.int64).reshape(-1) if 'indices' in pr else np.arange(len(P))
                Pw = (np.c_[P, np.ones(len(P))] @ M.T)[:, :3]
                parts.append(Pw[I.reshape(-1, 3)])
            if parts:
                t = np.concatenate(parts)
                out[name] = np.concatenate([out[name], t]) if name in out else t
        for c in nd.get('children', []):
            walk(c, M)

    for r in scene['nodes']:
        walk(r, np.eye(4))
    return out


def col_major(m16):
    return np.array(m16, dtype=np.float64).reshape(4, 4).T
