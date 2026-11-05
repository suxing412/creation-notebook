# LY-049 prep: read-only GLB reader (numpy only). Never writes to inputs.
# World triangles in glTF axes (x east, y up, z = -north).
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
    raw = np.frombuffer(binc, dtype=np.uint8, count=stride * (cnt - 1) + dt.itemsize * n, offset=base)
    out = np.empty((cnt, n))
    for i in range(cnt):
        out[i] = np.frombuffer(raw[i * stride:i * stride + dt.itemsize * n].tobytes(), dtype=dt)
    return out


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


def node_tris(path, outer=None, skip=()):
    """Return {node_name: (N,3,3) world triangles}. outer = 4x4 applied after the scene graph."""
    js, binc = load(path)
    outer = np.eye(4) if outer is None else outer
    res = {}
    scene = js['scenes'][js.get('scene', 0)]

    def walk(i, P):
        nd = js['nodes'][i]; M = P @ trs(nd); name = nd.get('name', f'node{i}')
        if 'mesh' in nd and name not in skip:
            tl = []
            for pr in js['meshes'][nd['mesh']]['primitives']:
                if pr.get('mode', 4) != 4:
                    continue
                V = acc(js, binc, pr['attributes']['POSITION'])
                I = acc(js, binc, pr['indices']).astype(np.int64).reshape(-1) if 'indices' in pr else np.arange(len(V))
                Vw = (M @ np.c_[V, np.ones(len(V))].T).T[:, :3]
                tl.append(Vw[I.reshape(-1, 3)])
            if tl:
                res[name] = np.concatenate(tl)
        for c in nd.get('children', []):
            walk(c, M)
    for r in scene['nodes']:
        walk(r, outer)
    return res


def lot_matrix(position, rotation_deg):
    """Same as r01-assets.mjs buildDistrictAssets: makeRotationY(rot) then setPosition(x,0,-y)."""
    a = np.radians(rotation_deg); c, s = np.cos(a), np.sin(a)
    M = np.eye(4); M[0, 0] = c; M[0, 2] = s; M[2, 0] = -s; M[2, 2] = c
    M[0, 3] = position[0]; M[2, 3] = -position[1]
    return M


def clip_xz(tris, xmin, xmax, zmin, zmax):
    if len(tris) == 0:
        return tris
    mn = tris.min(1); mx = tris.max(1)
    k = (mx[:, 0] >= xmin) & (mn[:, 0] <= xmax) & (mx[:, 2] >= zmin) & (mn[:, 2] <= zmax)
    return tris[k]


def vray_hits(tris, x, z, eps=1e-9):
    """All heights where a vertical line at (x,z) crosses triangles; returns list of (y, normal_y)."""
    if len(tris) == 0:
        return []
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    # barycentric in xz
    v0x, v0z = c[:, 0] - a[:, 0], c[:, 2] - a[:, 2]
    v1x, v1z = b[:, 0] - a[:, 0], b[:, 2] - a[:, 2]
    v2x, v2z = x - a[:, 0], z - a[:, 2]
    den = v0x * v1z - v1x * v0z
    ok = np.abs(den) > eps
    den = np.where(ok, den, 1)
    u = (v2x * v1z - v1x * v2z) / den
    v = (v0x * v2z - v2x * v0z) / den
    k = ok & (u >= -1e-7) & (v >= -1e-7) & (u + v <= 1 + 1e-7)
    if not k.any():
        return []
    y = a[k, 1] + u[k] * (c[k, 1] - a[k, 1]) + v[k] * (b[k, 1] - a[k, 1])
    n = np.cross(b[k] - a[k], c[k] - a[k]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-30
    return list(zip(y.tolist(), n[:, 1].tolist()))
