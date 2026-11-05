# LY-087 prep: minimal read-only glTF 2.0 binary reader (numpy).
# Uncompressed GLB only (all LY-087 inputs have extensionsUsed == []).
# Returns per-node world-space triangles in the glTF frame (+X east, +Y up, -Z north),
# node world = parent chain of T*R*S (or matrix), column-major, as three.js does.
import json, struct, hashlib
import numpy as np

COMP = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def load(path):
    raw = open(path, 'rb').read()
    magic, ver, length = struct.unpack('<4sII', raw[:12])
    assert magic == b'glTF' and ver == 2, path
    off, js, bins = 12, None, None
    while off < length:
        clen, ctype = struct.unpack('<II', raw[off:off + 8])
        chunk = raw[off + 8: off + 8 + clen]
        if ctype == 0x4E4F534A:
            js = json.loads(chunk.decode('utf-8'))
        elif ctype == 0x004E4942:
            bins = chunk
        off += 8 + clen
    assert not js.get('extensionsUsed'), (path, js.get('extensionsUsed'))
    return {'json': js, 'bin': bins, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw), 'path': path}


def acc(g, i):
    js = g['json']; a = js['accessors'][i]; bv = js['bufferViews'][a['bufferView']]
    dt = COMP[a['componentType']]; n = NC[a['type']]
    start = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = bv.get('byteStride', 0); isz = np.dtype(dt).itemsize * n
    if stride and stride != isz:
        buf = np.frombuffer(g['bin'], dtype=np.uint8, count=stride * (a['count'] - 1) + isz, offset=start)
        rows = np.lib.stride_tricks.as_strided(buf, shape=(a['count'], isz), strides=(stride, 1))
        out = np.frombuffer(rows.copy().tobytes(), dtype=dt).reshape(a['count'], n)
    else:
        out = np.frombuffer(g['bin'], dtype=dt, count=a['count'] * n, offset=start).reshape(a['count'], n)
    return out.astype(np.float64) if dt == np.float32 else out.astype(np.int64)


def quat_mat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def local_m(n):
    if 'matrix' in n:
        return np.array(n['matrix'], dtype=np.float64).reshape(4, 4).T
    M = np.eye(4)
    R = quat_mat(n.get('rotation', [0, 0, 0, 1])); S = np.diag(n.get('scale', [1, 1, 1]))
    M[:3, :3] = R @ S; M[:3, 3] = n.get('translation', [0, 0, 0])
    return M


def colmajor_to_m(cm):
    return np.array(cm, dtype=np.float64).reshape(4, 4).T


def nodes_world(g, root=np.eye(4)):
    js = g['json']; nodes = js['nodes']
    parent = {}
    for i, n in enumerate(nodes):
        for c in n.get('children', []):
            parent[c] = i
    W = {}

    def w(i):
        if i in W:
            return W[i]
        m = local_m(nodes[i])
        W[i] = (w(parent[i]) @ m) if i in parent else (root @ m)
        return W[i]
    for i in range(len(nodes)):
        w(i)
    return W


def node_tris(g, root=np.eye(4), exclude=()):
    """yield (node_index, node_name, material_names, V(N,3) world, F(M,3))"""
    js = g['json']; W = nodes_world(g, root)
    for i, n in enumerate(js['nodes']):
        if 'mesh' not in n or n.get('name') in exclude:
            continue
        Vs, Fs, mats, base = [], [], [], 0
        for pr in js['meshes'][n['mesh']]['primitives']:
            if pr.get('mode', 4) != 4:
                continue
            P = acc(g, pr['attributes']['POSITION'])
            I = acc(g, pr['indices']).reshape(-1) if 'indices' in pr else np.arange(len(P))
            Ph = np.c_[P, np.ones(len(P))] @ W[i].T
            Vs.append(Ph[:, :3]); Fs.append(I.reshape(-1, 3) + base); base += len(P)
            if 'material' in pr:
                mats.append(js['materials'][pr['material']].get('name'))
        if Vs:
            yield i, n.get('name'), mats, np.vstack(Vs), np.vstack(Fs)
