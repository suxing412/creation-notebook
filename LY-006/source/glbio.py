# LY-005 read-only GLB reader (numpy). Reads glTF 2.0 binary/embedded buffers,
# computes node world matrices exactly as three.js GLTFLoader + updateMatrixWorld
# (column-major glTF matrices, TRS = T*R*S), and returns float32 positions/indices.
import json, struct, os, hashlib
import numpy as np

COMP = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NCOMP = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def read_glb(path):
    raw = open(path, 'rb').read()
    magic, ver, length = struct.unpack('<4sII', raw[:12])
    assert magic == b'glTF' and ver == 2, path
    off = 12
    js = None
    bins = None
    while off < length:
        clen, ctype = struct.unpack('<II', raw[off:off + 8])
        chunk = raw[off + 8:off + 8 + clen]
        if ctype == 0x4E4F534A:
            js = json.loads(chunk.decode('utf-8'))
        elif ctype == 0x004E4942:
            bins = chunk
        off += 8 + clen
    buffers = []
    base = os.path.dirname(path)
    for i, b in enumerate(js.get('buffers', [])):
        if 'uri' in b:
            buffers.append(open(os.path.join(base, b['uri']), 'rb').read())
        else:
            buffers.append(bins)
    return {'json': js, 'buffers': buffers, 'bytes': raw, 'sha256': sha256_bytes(raw), 'size': len(raw)}


def accessor(g, idx):
    js = g['json']
    a = js['accessors'][idx]
    bv = js['bufferViews'][a['bufferView']]
    buf = g['buffers'][bv['buffer']]
    dt = np.dtype(COMP[a['componentType']])
    n = NCOMP[a['type']]
    start = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = bv.get('byteStride', 0) or dt.itemsize * n
    count = a['count']
    if stride == dt.itemsize * n:
        arr = np.frombuffer(buf, dtype=dt, count=count * n, offset=start).reshape(count, n)
    else:
        arr = np.stack([np.frombuffer(buf, dtype=dt, count=n, offset=start + i * stride) for i in range(count)])
    if a.get('normalized'):
        raise NotImplementedError('normalized accessor')
    return arr.copy()


def quat_to_mat(q):
    x, y, z, w = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def local_matrix(node):
    if 'matrix' in node:
        return np.array(node['matrix'], dtype=np.float64).reshape(4, 4).T
    m = np.eye(4)
    s = node.get('scale', [1, 1, 1])
    r = node.get('rotation', [0, 0, 0, 1])
    t = node.get('translation', [0, 0, 0])
    m[:3, :3] = quat_to_mat(r) @ np.diag(s)
    m[:3, 3] = t
    return m


def world_matrices(g):
    js = g['json']
    nodes = js.get('nodes', [])
    scene = js['scenes'][js.get('scene', 0)]
    world = {}
    parent = {}

    def walk(i, pm):
        w = pm @ local_matrix(nodes[i])
        world[i] = w
        for c in nodes[i].get('children', []):
            parent[c] = i
            walk(c, w)
    for r in scene['nodes']:
        parent[r] = None
        walk(r, np.eye(4))
    return world, parent


def ancestors_names(g, parent, i):
    nodes = g['json']['nodes']
    out = []
    while i is not None:
        out.append(nodes[i].get('name', ''))
        i = parent.get(i)
    return out


def mesh_items(g):
    """yield (node_index, node_name, world4x4, positions Nx3 float64 local, triangles Mx3 int)"""
    js = g['json']
    world, parent = world_matrices(g)
    for i, w in world.items():
        node = js['nodes'][i]
        if 'mesh' not in node:
            continue
        for p in js['meshes'][node['mesh']]['primitives']:
            if p.get('mode', 4) != 4:
                continue
            pos = accessor(g, p['attributes']['POSITION']).astype(np.float64)
            if 'indices' in p:
                idx = accessor(g, p['indices']).reshape(-1).astype(np.int64)
            else:
                idx = np.arange(len(pos), dtype=np.int64)
            yield i, node.get('name', ''), w, pos, idx.reshape(-1, 3), ancestors_names(g, parent, i)


def apply(m, pts):
    return pts @ m[:3, :3].T + m[:3, 3]


def gltf_col_major_to_np(arr16):
    return np.array(arr16, dtype=np.float64).reshape(4, 4).T


def compose_three(position, rotation_y, scale):
    """three.js Matrix4.compose(position, quaternion(axis Y, angle), scale)"""
    c, s = np.cos(rotation_y), np.sin(rotation_y)
    r = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    m = np.eye(4)
    m[:3, :3] = r @ np.diag(scale)
    m[:3, 3] = position
    return m
