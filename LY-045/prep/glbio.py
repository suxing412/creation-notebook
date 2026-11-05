# LY-045 prep: copy of LY-041 prep glbio.py (read-only GLB reader, numpy). Never writes to its inputs.
# Returns per-node world-space triangles in glTF axes (x right, y up, z toward viewer).
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
        return np.frombuffer(binc, dtype=dt, count=cnt * n, offset=base).reshape(cnt, n).astype(np.float64 if dt == np.float32 else np.int64)
    out = np.empty((cnt, n), dtype=np.float64)
    for i in range(cnt):
        out[i] = np.frombuffer(binc, dtype=dt, count=n, offset=base + i * stride)
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


def nodes_tris(path, root=None):
    """dict name -> (N,3,3) world tris (glTF axes), after optional root 4x4 matrix."""
    js, binc = load(path)
    out = {}
    scene = js['scenes'][js.get('scene', 0)]
    stack = [(i, np.eye(4) if root is None else root) for i in scene['nodes']]
    while stack:
        i, P = stack.pop()
        n = js['nodes'][i]
        M = P @ trs(n)
        if 'mesh' in n:
            tris = []
            for prim in js['meshes'][n['mesh']]['primitives']:
                if prim.get('mode', 4) != 4:
                    continue
                pos = acc(js, binc, prim['attributes']['POSITION'])
                idx = acc(js, binc, prim['indices']).reshape(-1) if 'indices' in prim else np.arange(len(pos))
                p = np.c_[pos, np.ones(len(pos))] @ M.T
                tris.append(p[:, :3][idx.reshape(-1, 3)])
            name = n.get('name', 'node%d' % i)
            out[name] = np.concatenate(tris) if tris else np.zeros((0, 3, 3))
        for c in n.get('children', []):
            stack.append((c, M))
    return out


def col_major(m16):
    return np.array(m16, dtype=np.float64).reshape(4, 4).T


def raster(tris, x0, z0, h, nx, nz, edge_step=None):
    """Heightfield of triangles on a world xz grid (cell centres x0+(i+.5)h, z0+(j+.5)h).
    Returns top (max y), bot (min y), hits (number of covering triangles) arrays shape (nz,nx).
    Interior coverage uses barycentric test at cell centres; edge_step additionally splats points
    along triangle edges (captures bottom edges of vertical walls)."""
    top = np.full((nz, nx), -np.inf); bot = np.full((nz, nx), np.inf); hits = np.zeros((nz, nx), np.int32)
    if len(tris) == 0:
        return top, bot, hits
    xs = tris[:, :, 0]; zs = tris[:, :, 2]
    i0 = np.floor((xs.min(1) - x0) / h - 0.5).astype(int); i1 = np.ceil((xs.max(1) - x0) / h - 0.5).astype(int)
    j0 = np.floor((zs.min(1) - z0) / h - 0.5).astype(int); j1 = np.ceil((zs.max(1) - z0) / h - 0.5).astype(int)
    keep = (i1 >= 0) & (i0 < nx) & (j1 >= 0) & (j0 < nz)
    for t in np.nonzero(keep)[0]:
        a, b, c = tris[t]
        d = (b[0] - a[0]) * (c[2] - a[2]) - (c[0] - a[0]) * (b[2] - a[2])
        if abs(d) > 1e-12:
            ia, ib = max(i0[t], 0), min(i1[t], nx - 1); ja, jb = max(j0[t], 0), min(j1[t], nz - 1)
            if ia <= ib and ja <= jb:
                gx = x0 + (np.arange(ia, ib + 1) + 0.5) * h; gz = z0 + (np.arange(ja, jb + 1) + 0.5) * h
                X, Z = np.meshgrid(gx, gz)
                l1 = ((b[0] - X) * (c[2] - Z) - (c[0] - X) * (b[2] - Z)) / d
                l2 = ((c[0] - X) * (a[2] - Z) - (a[0] - X) * (c[2] - Z)) / d
                l3 = 1 - l1 - l2
                m = (l1 >= -1e-9) & (l2 >= -1e-9) & (l3 >= -1e-9)
                if m.any():
                    Y = l1 * a[1] + l2 * b[1] + l3 * c[1]
                    sub_t = top[ja:jb + 1, ia:ib + 1]; sub_b = bot[ja:jb + 1, ia:ib + 1]; sub_h = hits[ja:jb + 1, ia:ib + 1]
                    np.maximum(sub_t, np.where(m, Y, -np.inf), out=sub_t)
                    np.minimum(sub_b, np.where(m, Y, np.inf), out=sub_b)
                    sub_h += m
        if edge_step:
            for p, q in ((a, b), (b, c), (c, a)):
                L = np.hypot(q[0] - p[0], q[2] - p[2]); n = max(int(L / edge_step) + 1, 2)
                s = np.linspace(0, 1, n)
                P = p[None] + s[:, None] * (q - p)[None]
                ii = np.floor((P[:, 0] - x0) / h).astype(int); jj = np.floor((P[:, 2] - z0) / h).astype(int)
                ok = (ii >= 0) & (ii < nx) & (jj >= 0) & (jj < nz)
                np.minimum.at(bot, (jj[ok], ii[ok]), P[ok, 1])
                np.maximum.at(top, (jj[ok], ii[ok]), P[ok, 1])
    return top, bot, hits
