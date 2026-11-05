# LY-033 prep: minimal read-only GLB reader (world-space triangles per primitive).
# Usage as module only. Never writes any GLB.
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
    assert magic == 0x46546C67, 'not a GLB'
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
    dt = np.dtype(CT[a['componentType']])
    n = NC[a['type']]
    cnt = a['count']
    stride = bv.get('byteStride', 0) or dt.itemsize * n
    base = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    if stride == dt.itemsize * n:
        return np.frombuffer(binc, dtype=dt, count=cnt * n, offset=base).reshape(cnt, n).copy()
    out = np.empty((cnt, n), dtype=dt)
    for i in range(cnt):
        s = base + i * stride
        out[i] = np.frombuffer(binc[s:s + dt.itemsize * n], dtype=dt)
    return out


def qm(q):
    x, y, z, w = q
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])


def nmat(nd):
    if 'matrix' in nd:
        return np.array(nd['matrix'], float).reshape(4, 4).T
    M = np.eye(4)
    M[:3, :3] = qm(nd.get('rotation', [0, 0, 0, 1])) @ np.diag(nd.get('scale', [1, 1, 1]))
    M[:3, 3] = nd.get('translation', [0, 0, 0])
    return M


def prims(path, offset=(0, 0, 0)):
    js, binc = load(path)
    out = []
    sc = js['scenes'][js.get('scene', 0)]
    stack = [(i, np.eye(4)) for i in sc['nodes']]
    while stack:
        i, P = stack.pop()
        nd = js['nodes'][i]
        W = P @ nmat(nd)
        for c in nd.get('children', []):
            stack.append((c, W))
        if 'mesh' not in nd:
            continue
        for p in js['meshes'][nd['mesh']]['primitives']:
            pos = acc(js, binc, p['attributes']['POSITION']).astype(float)
            pw = (W[:3, :3] @ pos.T).T + W[:3, 3] + np.asarray(offset, float)
            idx = acc(js, binc, p['indices']).reshape(-1).astype(np.int64) if 'indices' in p else np.arange(len(pos))
            mat = js['materials'][p['material']].get('name') if 'material' in p else None
            out.append(dict(node=nd.get('name'), material=mat, pos=pw, tris=idx.reshape(-1, 3)))
    return js, out


def components(p, tol=1e-4):
    pos, tris = p['pos'], p['tris']
    key = np.round(pos / tol).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    parent = np.arange(inv.max() + 1)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for t in tris:
        a = find(inv[t[0]])
        for v in (t[1], t[2]):
            b = find(inv[v])
            if a != b:
                parent[b] = a
    comps = {}
    for ti, t in enumerate(tris):
        comps.setdefault(find(inv[t[0]]), []).append(ti)
    res = []
    for tl in comps.values():
        v = pos[tris[tl].reshape(-1)]
        res.append(dict(tris=np.array(tl), lo=v.min(0), hi=v.max(0)))
    return res
