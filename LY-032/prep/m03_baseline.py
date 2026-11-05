# LY-032 prep: pure-Python (numpy) read-only GLB baseline for "old warehouse geometry/UV unchanged" checks.
# usage: python -I m03_baseline.py <out.json> <glb> [<glb> ...]
# For each primitive: triangle count, SHA256 of index/POSITION/NORMAL/TEXCOORD_0 accessor bytes,
# and an order-independent SHA of the world-space triangles (pos+uv rounded 1e-5) whose centroid lies in the
# B-warehouse bay box (city absolute coords, or B-local when the file is the standalone granary-B part).
import sys, json, struct, hashlib
import numpy as np

B_BOX_CITY = ((2291.0, -0.01, -3682.6), (2304.5, 5.3, -3674.7))   # glTF x,y,z min/max
B_BOX_LOCAL_B = ((-6.6, -0.01, -3.1), (6.6, 5.3, 4.8))
B_BOX_GROUP = ((5.2, -0.01, -9.2), (18.6, 5.3, -1.2))
CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}

def load(p):
    b = open(p, 'rb').read()
    jl = struct.unpack('<I', b[12:16])[0]
    j = json.loads(b[20:20 + jl])
    off = 20 + jl
    bl = struct.unpack('<I', b[off:off + 4])[0]
    return j, b[off + 8:off + 8 + bl]

def acc(j, bin_, i):
    a = j['accessors'][i]; bv = j['bufferViews'][a['bufferView']]
    n = NC[a['type']]; dt = np.dtype(CT[a['componentType']])
    start = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = bv.get('byteStride', 0) or n * dt.itemsize
    raw = bin_[start:start + stride * (a['count'] - 1) + n * dt.itemsize]
    if stride == n * dt.itemsize:
        arr = np.frombuffer(raw, dtype=dt, count=a['count'] * n).reshape(a['count'], n)
    else:
        arr = np.stack([np.frombuffer(raw[k * stride:k * stride + n * dt.itemsize], dtype=dt) for k in range(a['count'])])
    return arr, hashlib.sha256(arr.tobytes()).hexdigest()

def node_mats(j):
    out = {}
    def T(n):
        m = np.eye(4)
        if 'matrix' in n:
            return np.array(n['matrix']).reshape(4, 4).T
        t = n.get('translation', [0, 0, 0]); s = n.get('scale', [1, 1, 1]); q = n.get('rotation', [0, 0, 0, 1])
        x, y, z, w = q
        R = np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
        m[:3, :3] = R * np.array(s); m[:3, 3] = t
        return m
    def walk(i, P):
        n = j['nodes'][i]; M = P @ T(n); out[i] = M
        for c in n.get('children', []): walk(c, M)
    for sc in j.get('scenes', [{'nodes': list(range(len(j['nodes'])))}]):
        for i in sc['nodes']: walk(i, np.eye(4))
    return out

res = {}
for p in sys.argv[2:]:
    j, bin_ = load(p)
    fb = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    box = B_BOX_LOCAL_B if 'granary-B-' in p else (B_BOX_GROUP if 'granary-group-' in p else B_BOX_CITY)
    lo, hi = np.array(box[0]), np.array(box[1])
    mats = node_mats(j)
    prims = []
    for ni, M in mats.items():
        n = j['nodes'][ni]
        if 'mesh' not in n: continue
        for pi, pr in enumerate(j['meshes'][n['mesh']]['primitives']):
            pos, hp = acc(j, bin_, pr['attributes']['POSITION'])
            idx, hi_ = acc(j, bin_, pr['indices']) if 'indices' in pr else (np.arange(len(pos)).reshape(-1, 1), None)
            uv, hu = acc(j, bin_, pr['attributes']['TEXCOORD_0']) if 'TEXCOORD_0' in pr['attributes'] else (None, None)
            nm, hn = acc(j, bin_, pr['attributes']['NORMAL']) if 'NORMAL' in pr['attributes'] else (None, None)
            W = (np.c_[pos.astype(np.float64), np.ones(len(pos))] @ M.T)[:, :3]
            tri = idx.reshape(-1, 3)
            cen = W[tri].mean(axis=1)
            inb = np.all((cen >= lo) & (cen <= hi), axis=1)
            sel = tri[inb]
            keys = []
            for t in sel:
                v = [tuple(np.round(W[k], 5)) + (tuple(np.round(uv[k], 5)) if uv is not None else ()) for k in t]
                keys.append(repr(sorted(v)))
            keys.sort()
            prims.append({'node': n.get('name'), 'mesh': n['mesh'], 'prim': pi, 'material': j['materials'][pr['material']].get('name') if 'material' in pr else None,
                          'tris': int(len(tri)), 'verts': int(len(pos)), 'sha_indices': hi_, 'sha_position': hp, 'sha_normal': hn, 'sha_uv0': hu,
                          'B_bay_tris': int(inb.sum()), 'B_bay_sha_world_pos_uv': hashlib.sha256('\n'.join(keys).encode()).hexdigest()})
    res[p] = {'file_sha256': fb, 'bytes': len(open(p, 'rb').read()), 'B_box': box, 'primitives': prims,
              'total_tris': sum(x['tris'] for x in prims), 'total_B_bay_tris': sum(x['B_bay_tris'] for x in prims)}
    print(p.split('/')[-1], fb[:12], res[p]['total_tris'], res[p]['total_B_bay_tris'])
json.dump(res, open(sys.argv[1], 'w'), indent=1)
