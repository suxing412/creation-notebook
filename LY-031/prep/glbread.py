# LY-031 prep: minimal read-only GLB reader (no writes to inputs).
# Returns world-space positions/triangles/uv per primitive, honouring node TRS (no parenting in these files).
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
        return np.frombuffer(binc, dtype=dt, count=cnt * n, offset=base).reshape(cnt, n).copy()
    out = np.empty((cnt, n), dtype=dt)
    for i in range(cnt):
        out[i] = np.frombuffer(binc, dtype=dt, count=n, offset=base + i * stride)
    return out


def qmat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def prims(path):
    js, binc = load(path)
    out = []
    for n in js['nodes']:
        if 'mesh' not in n:
            continue
        R = qmat(n.get('rotation', [0, 0, 0, 1])); S = np.array(n.get('scale', [1, 1, 1])); T = np.array(n.get('translation', [0, 0, 0]))
        for pi, p in enumerate(js['meshes'][n['mesh']]['primitives']):
            pos = acc(js, binc, p['attributes']['POSITION']).astype(np.float64)
            pos = (pos * S) @ R.T + T
            tris = acc(js, binc, p['indices']).reshape(-1, 3).astype(np.int64)
            uv = acc(js, binc, p['attributes']['TEXCOORD_0']) if 'TEXCOORD_0' in p['attributes'] else None
            out.append(dict(node=n.get('name'), mesh=js['meshes'][n['mesh']].get('name'),
                            material=js['materials'][p['material']].get('name') if 'material' in p else None,
                            pos=pos, tris=tris, uv=uv, T=T))
    return js, out


def components(pos, tris, tol=1e-4):
    key = np.round(pos / tol).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    parent = np.arange(inv.max() + 1)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for t in tris:
        a = find(inv[t[0]])
        for v in (inv[t[1]], inv[t[2]]):
            b = find(v)
            if a != b:
                parent[b] = a
    comps = {}
    for ti, t in enumerate(tris):
        comps.setdefault(find(inv[t[0]]), []).append(ti)
    return list(comps.values())
