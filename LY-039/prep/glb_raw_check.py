# LY-039 prep: Blender-independent raw GLB read of the road chunk. Applies node
# matrices (glTF Y-up) and reports unique vertices in native Z-up (x, -z, y).
# python -I glb_raw_check.py <road.glb>
import sys, json, struct, hashlib
p = sys.argv[1]
b = open(p, 'rb').read()
magic, ver, ln = struct.unpack_from('<III', b, 0)
assert magic == 0x46546C67 and ln == len(b), 'bad GLB header/length'
jl, jt = struct.unpack_from('<II', b, 12); J = json.loads(b[20:20 + jl])
bl, bt = struct.unpack_from('<II', b, 20 + jl); BIN = b[28 + jl:28 + jl + bl]
def acc(i):
    a = J['accessors'][i]; v = J['bufferViews'][a['bufferView']]
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    fmt = {5126: 'f', 5125: 'I', 5123: 'H', 5121: 'B'}[a['componentType']]
    sz = struct.calcsize(fmt); stride = v.get('byteStride', sz * n)
    return [struct.unpack_from('<' + fmt * n, BIN, off + k * stride) for k in range(a['count'])]
def mat(nd):
    if 'matrix' in nd: m = nd['matrix']; return lambda q: tuple(sum(m[c * 4 + r] * (list(q) + [1])[c] for c in range(4)) for r in range(3))
    t = nd.get('translation', [0, 0, 0]); assert 'rotation' not in nd or nd['rotation'] == [0, 0, 0, 1]
    s = nd.get('scale', [1, 1, 1]); return lambda q: tuple(q[i] * s[i] + t[i] for i in range(3))
verts, tris = set(), 0
for nd in J['nodes']:
    if 'mesh' not in nd: continue
    f = mat(nd)
    for pr in J['meshes'][nd['mesh']]['primitives']:
        P = acc(pr['attributes']['POSITION']); I = acc(pr['indices']) if 'indices' in pr else [(k,) for k in range(len(P))]
        tris += len(I) // 3
        for q in P:
            x, y, z = f(q); verts.add((round(x, 4), round(-z, 4), round(y, 4)))
vs = sorted(verts)
print(json.dumps({'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b), 'nodes': [n.get('name') for n in J['nodes']],
  'materials': [m.get('name') for m in J.get('materials', [])], 'images': len(J.get('images', [])), 'triangles': tris,
  'unique_vertices_native': len(vs), 'x': [min(v[0] for v in vs), max(v[0] for v in vs)], 'y': [min(v[1] for v in vs), max(v[1] for v in vs)],
  'z': [min(v[2] for v in vs), max(v[2] for v in vs)], 'top_vertices': [v for v in vs if v[2] > -0.01]}, ensure_ascii=False, indent=1))
