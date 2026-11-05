# LY-035 prep: minimal read-only GLB reader (numpy). Returns world-space triangles per node.
# glTF axes kept: +X east, +Y up, -Z north (city contract). No writes to any input.
import json, struct, hashlib
import numpy as np

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def load(path):
    b = open(path, 'rb').read()
    magic, ver, length = struct.unpack('<III', b[:12])
    assert magic == 0x46546C67 and ver == 2 and length == len(b), 'bad GLB header'
    jl = struct.unpack('<I', b[12:16])[0]
    js = json.loads(b[20:20 + jl])
    off = 20 + jl
    bl = struct.unpack('<I', b[off:off + 4])[0]
    binc = b[off + 8: off + 8 + bl]
    return js, binc


def accessor(js, binc, i):
    a = js['accessors'][i]
    bv = js['bufferViews'][a['bufferView']]
    n = NC[a['type']]
    dt = np.dtype(CT[a['componentType']])
    start = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = bv.get('byteStride', 0) or n * dt.itemsize
    raw = np.frombuffer(binc, dtype=np.uint8, count=stride * (a['count'] - 1) + n * dt.itemsize, offset=start)
    if stride == n * dt.itemsize:
        out = np.frombuffer(raw.tobytes(), dtype=dt).reshape(a['count'], n)
    else:
        idx = np.arange(a['count'])[:, None] * stride + np.arange(n * dt.itemsize)[None, :]
        out = np.frombuffer(raw[idx].tobytes(), dtype=dt).reshape(a['count'], n)
    return out.astype(np.float64) if dt == np.float32 else out


def local_matrix(node):
    if 'matrix' in node:
        return np.array(node['matrix'], dtype=np.float64).reshape(4, 4).T
    t = np.array(node.get('translation', [0, 0, 0]), dtype=np.float64)
    q = node.get('rotation', [0, 0, 0, 1])
    s = np.array(node.get('scale', [1, 1, 1]), dtype=np.float64)
    x, y, z, w = q
    R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    M = np.eye(4)
    M[:3, :3] = R * s[None, :]
    M[:3, 3] = t
    return M


def world_triangles(path):
    """Return list of dict(node, mesh, material, tris[N,3,3] world) and json."""
    js, binc = load(path)
    nodes = js['nodes']
    parent = {}
    for i, n in enumerate(nodes):
        for c in n.get('children', []):
            parent[c] = i
    cache = {}

    def wm(i):
        if i in cache:
            return cache[i]
        M = local_matrix(nodes[i])
        if i in parent:
            M = wm(parent[i]) @ M
        cache[i] = M
        return M
    out = []
    mats = js.get('materials', [])
    for i, n in enumerate(nodes):
        if 'mesh' not in n:
            continue
        M = wm(i)
        mesh = js['meshes'][n['mesh']]
        for p in mesh['primitives']:
            assert p.get('mode', 4) == 4
            pos = accessor(js, binc, p['attributes']['POSITION'])
            if 'indices' in p:
                idx = accessor(js, binc, p['indices']).reshape(-1).astype(np.int64)
            else:
                idx = np.arange(len(pos))
            wp = (np.c_[pos, np.ones(len(pos))] @ M.T)[:, :3]
            tris = wp[idx.reshape(-1, 3)]
            mi = p.get('material')
            out.append(dict(node=n.get('name'), mesh=mesh.get('name'),
                            material=mats[mi].get('name') if mi is not None else None,
                            tris=tris, det=float(np.linalg.det(M[:3, :3]))))
    return out, js
