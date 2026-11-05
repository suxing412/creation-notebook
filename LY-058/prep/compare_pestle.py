# LY-058 prep: does the workyard embed the published foot-pestle module unchanged (pure translation)?
# usage: python compare_pestle.py <workyard.glb> <foot-pestle.glb>
import json, struct, sys
import numpy as np
CT = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}

def load(p):
    b = open(p, 'rb').read(); off = 12; js = bn = None
    while off < len(b):
        cl, ct = struct.unpack('<II', b[off:off + 8]); off += 8
        if ct == 0x4E4F534A: js = json.loads(b[off:off + cl])
        elif ct == 0x004E4942: bn = b[off:off + cl]
        off += cl
    return js, bn

def acc(js, bn, i):
    a = js['accessors'][i]; bv = js['bufferViews'][a['bufferView']]
    dt = CT[a['componentType']]; n = NC[a['type']]; o = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    st = bv.get('byteStride', 0); isz = np.dtype(dt).itemsize * n
    if st and st != isz:
        raw = np.frombuffer(bn, np.uint8, st * a['count'], o).reshape(a['count'], st)[:, :isz]
        return np.frombuffer(raw.tobytes(), dt).reshape(a['count'], n)
    return np.frombuffer(bn, dt, a['count'] * n, o).reshape(a['count'], n)

def meshes(p):
    js, bn = load(p); out = {}
    for nd in js['nodes']:
        if 'mesh' not in nd: continue
        me = js['meshes'][nd['mesh']]; V = []; T = []
        for pr in me['primitives']:
            v = acc(js, bn, pr['attributes']['POSITION']).astype(np.float64)
            t = acc(js, bn, pr['indices']).reshape(-1, 3).astype(np.int64)
            T.append(t + sum(len(x) for x in V)); V.append(v)
        V = np.concatenate(V); T = np.concatenate(T)
        for k in ('translation',):
            if k in nd: V = V + np.array(nd[k])
        out[nd['name']] = (V, T)
    return out

Y = meshes(sys.argv[1]); P = meshes(sys.argv[2])
res = {}
def tri_set(V, T, off=np.zeros(3), nd=4):
    return sorted(tuple(sorted(tuple(np.round(V[i] + off, nd)) for i in t)) for t in T)
pairs = [('pestle__pestle_timber_moving', 'pestle_timber_moving'), ('workyard_stone', 'pestle_stone_static')]
for a, b in pairs:
    Va, Ta = Y[a]; Vb, Tb = P[b]
    off = Va.min(0) - Vb.min(0)
    sa = tri_set(Va, Ta); sb = tri_set(Vb, Tb, off)
    res[a + ' vs ' + b] = {'offset': off.round(5).tolist(), 'tris': [len(Ta), len(Tb)], 'identical_tri_sets_1e-4': sa == sb}
# static timber of the module: are its triangles a subset of workyard_timber after the same offset?
off = np.array(res['workyard_stone vs pestle_stone_static']['offset'])
Vs, Ts = P['pestle_timber_static']; Vw, Tw = Y['workyard_timber']
sw = set(tri_set(Vw, Tw)); ss = tri_set(Vs, Ts, off)
hit = sum(1 for t in ss if t in sw)
res['pestle_timber_static subset of workyard_timber'] = {'offset': off.tolist(), 'module_tris': len(ss), 'found_in_workyard_timber': hit}
print(json.dumps(res, indent=1))
