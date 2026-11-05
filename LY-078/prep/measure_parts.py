# LY-078 prep: read-only GLB measurement (numpy). Usage: python -I measure_parts.py <glb> [out.json]
import sys, json, struct, hashlib, collections
import numpy as np

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}

def load(path):
    b = open(path, 'rb').read()
    assert b[:4] == b'glTF'
    off = 12; js = None; binc = None
    while off < len(b):
        ln, ty = struct.unpack_from('<II', b, off); off += 8
        c = b[off:off + ln]; off += ln
        if ty == 0x4E4F534A: js = json.loads(c)
        elif ty == 0x004E4942: binc = c
    return js, binc, hashlib.sha256(b).hexdigest(), len(b)

def acc(js, binc, i):
    a = js['accessors'][i]; bv = js['bufferViews'][a['bufferView']]
    n = NC[a['type']]; dt = np.dtype(CT[a['componentType']])
    start = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = bv.get('byteStride', 0)
    if stride and stride != dt.itemsize * n:
        raw = np.frombuffer(binc, np.uint8, count=stride * a['count'], offset=start).reshape(a['count'], stride)
        return raw[:, :dt.itemsize * n].copy().view(dt).reshape(a['count'], n)
    return np.frombuffer(binc, dt, count=a['count'] * n, offset=start).reshape(a['count'], n)

def parts(pos, tris):
    key = np.round(pos, 4)
    _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.reshape(-1)
    parent = np.arange(len(tris))
    def find(a):
        r = a
        while parent[r] != r: r = parent[r]
        while parent[a] != r: parent[a], a = r, parent[a]
        return r
    first = {}
    for t in range(len(tris)):
        for v in tris[t]:
            k = inv[v]
            if k in first:
                ra, rb = find(t), find(first[k])
                if ra != rb: parent[ra] = rb
            else: first[k] = t
    g = collections.defaultdict(list)
    for t in range(len(tris)): g[find(t)].append(t)
    return list(g.values())

def main():
    path = sys.argv[1]
    js, binc, sha, n = load(path)
    out = {'path': path, 'sha256': sha, 'bytes': n, 'nodes': [x.get('name') for x in js['nodes']],
           'nodeExtras': [x.get('extras') for x in js['nodes']], 'meshes': len(js['meshes']), 'materials': {}}
    for p in js['meshes'][0]['primitives']:
        name = js['materials'][p['material']]['name']
        pos = acc(js, binc, p['attributes']['POSITION']).astype(np.float64)
        tris = acc(js, binc, p['indices']).reshape(-1, 3).astype(np.int64)
        gs = parts(pos, tris)
        plist = []
        for g in gs:
            v = pos[tris[g].reshape(-1)]
            plist.append({'tris': len(g), 'lo': np.round(v.min(0), 4).tolist(), 'hi': np.round(v.max(0), 4).tolist()})
        out['materials'][name] = {'tris': int(len(tris)), 'parts': len(gs), 'lo': np.round(pos.min(0), 4).tolist(),
                                   'hi': np.round(pos.max(0), 4).tolist(), 'partList': plist}
    s = json.dumps(out, ensure_ascii=False, indent=1)
    if len(sys.argv) > 2: open(sys.argv[2], 'w', encoding='utf-8').write(s)
    for k, m in out['materials'].items():
        print(k, m['tris'], 'parts', m['parts'], m['lo'], m['hi'])

main()
