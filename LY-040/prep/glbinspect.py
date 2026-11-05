# LY-040 prep: read-only GLB inspector (numpy only). Never writes to input paths.
# Usage: python -I glbinspect.py <out.json> <label=path> [<label=path> ...]
# Output per file: sha256, bytes, per-mesh-node world bbox (glTF Y-up and native Z-up),
# triangle count, material names, degenerate-triangle count, non-finite count,
# and a tolerance-quantised geometry fingerprint (sorted world triangle centroids, 1 mm).
import json, struct, hashlib, sys
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
    assert length == len(data), 'length mismatch %d vs %d' % (length, len(data))
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
    if 'bufferView' not in a:
        return np.zeros((a['count'], NC[a['type']]), dtype=CT[a['componentType']])
    bv = js['bufferViews'][a['bufferView']]
    if bv.get('extensions'):
        raise RuntimeError('compressed bufferView (meshopt) not supported by this reader')
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


def local(n):
    if 'matrix' in n:
        return np.array(n['matrix'], dtype=float).reshape(4, 4).T
    M = np.eye(4)
    R = qmat(n.get('rotation', [0, 0, 0, 1]))
    S = np.diag(n.get('scale', [1, 1, 1]))
    M[:3, :3] = R @ S
    M[:3, 3] = n.get('translation', [0, 0, 0])
    return M


def walk(js):
    out = []
    scene = js['scenes'][js.get('scene', 0)]
    stack = [(i, np.eye(4), []) for i in scene['nodes']]
    while stack:
        i, P, path = stack.pop()
        n = js['nodes'][i]
        W = P @ local(n)
        name = n.get('name', 'node%d' % i)
        out.append((i, n, W, path + [name]))
        for c in n.get('children', []):
            stack.append((c, W, path + [name]))
    return out


def inspect(path):
    js, binc = load(path)
    res = {'path': path, 'bytes': len(open(path, 'rb').read()), 'sha256': sha256(path),
           'extensionsUsed': js.get('extensionsUsed', []), 'images': len(js.get('images', [])),
           'materials': [m.get('name') for m in js.get('materials', [])], 'nodes': []}
    allc = []
    tot = 0
    for i, n, W, path_ in walk(js):
        if 'mesh' not in n:
            continue
        mesh = js['meshes'][n['mesh']]
        pmin = np.array([np.inf] * 3); pmax = -pmin
        tris = 0; degen = 0; nonfinite = 0; mats = []
        for p in mesh['primitives']:
            pos = acc(js, binc, p['attributes']['POSITION']).astype(float)
            nonfinite += int((~np.isfinite(pos)).sum())
            wp = (W[:3, :3] @ pos.T).T + W[:3, 3]
            if 'indices' in p:
                idx = acc(js, binc, p['indices']).reshape(-1).astype(np.int64)
            else:
                idx = np.arange(len(pos))
            t = wp[idx].reshape(-1, 3, 3)
            area = np.linalg.norm(np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]), axis=1) / 2
            degen += int((area < 1e-10).sum())
            tris += len(t)
            pmin = np.minimum(pmin, wp.min(0)); pmax = np.maximum(pmax, wp.max(0))
            allc.append(t.mean(1))
            if 'material' in p:
                mats.append(js['materials'][p['material']].get('name'))
        tot += tris
        res['nodes'].append({'name': n.get('name'), 'path': '/'.join(path_), 'triangles': tris,
                             'degenerate': degen, 'nonfinite': nonfinite, 'materials': mats,
                             'bbox_gltf': [pmin.round(4).tolist(), pmax.round(4).tolist()],
                             'bbox_native_Zup': [[pmin[0], -pmax[2], pmin[1]], [pmax[0], -pmin[2], pmax[1]]]})
    res['triangles'] = tot
    if allc:
        c = np.concatenate(allc)
        q = np.round(c * 1000).astype(np.int64)
        q = q[np.lexsort(q.T[::-1])]
        res['centroid_fingerprint_1mm'] = hashlib.sha256(q.tobytes()).hexdigest()
        res['bbox_gltf'] = [c.min(0).round(4).tolist(), c.max(0).round(4).tolist()]
    return res


if __name__ == '__main__':
    out = sys.argv[1]
    allr = {}
    for arg in sys.argv[2:]:
        label, p = arg.split('=', 1)
        allr[label] = inspect(p)
        r = allr[label]
        print(label, r['bytes'], r['sha256'][:16], 'tris', r['triangles'], 'nodes', len(r['nodes']),
              'fp', r.get('centroid_fingerprint_1mm', '')[:16])
        for n in r['nodes']:
            print('   ', n['path'], n['triangles'], 'deg', n['degenerate'], 'nf', n['nonfinite'],
                  [round(v, 3) for v in n['bbox_native_Zup'][0]], [round(v, 3) for v in n['bbox_native_Zup'][1]])
    json.dump(allr, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
