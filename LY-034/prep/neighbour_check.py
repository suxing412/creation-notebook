# LY-034 prep: pure-python neighbour fingerprint around the storage slab (read-only).
# python -I neighbour_check.py <lab docs/cities/luoyang dir>
import json, struct, sys, hashlib, math, subprocess, os
root = sys.argv[1]
SLAB = (2249.714111328125, -3699.468994140625, 2321.714111328125, -3647.468994140625)  # x0,z0,x1,z1 world glTF

def glb_positions(p):
    b = open(p, 'rb').read()
    cl = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + cl])
    off = 20 + cl; bl = struct.unpack('<I', b[off:off + 4])[0]; bin_ = b[off + 8:off + 8 + bl]
    out = []
    global tris
    tris = []
    def mat(n):
        t = n.get('translation', [0, 0, 0]); s = n.get('scale', [1, 1, 1])
        assert 'rotation' not in n or n['rotation'] == [0, 0, 0, 1], 'rotation not handled'
        return t, s
    for n in j.get('nodes', []):
        if 'mesh' not in n: continue
        t, s = mat(n)
        for pr in j['meshes'][n['mesh']]['primitives']:
            a = j['accessors'][pr['attributes']['POSITION']]; bv = j['bufferViews'][a['bufferView']]
            st = bv.get('byteStride', 12); o = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
            base = len(out)
            for k in range(a['count']):
                x, y, z = struct.unpack('<fff', bin_[o + k * st:o + k * st + 12])
                out.append((x * s[0] + t[0], y * s[1] + t[1], z * s[2] + t[2]))
            ia = j['accessors'][pr['indices']]; ib = j['bufferViews'][ia['bufferView']]
            fmt = {5123: ('H', 2), 5125: ('I', 4), 5121: ('B', 1)}[ia['componentType']]
            io = ib.get('byteOffset', 0) + ia.get('byteOffset', 0)
            idx = struct.unpack('<%d%s' % (ia['count'], fmt[0]), bin_[io:io + ia['count'] * fmt[1]])
            for k in range(0, len(idx), 3):
                tris.append((base + idx[k], base + idx[k + 1], base + idx[k + 2]))
    return out, hashlib.sha256(b).hexdigest()

def seg_rect_dist(p, q):  # 2D distance from segment pq to slab rectangle
    x0, z0, x1, z1 = SLAB
    best = 1e18
    for k in range(5001):
        t = k / 5000; x = p[0] + (q[0] - p[0]) * t; z = p[1] + (q[1] - p[1]) * t
        dx = max(x0 - x, 0, x - x1); dz = max(z0 - z, 0, z - z1)
        best = min(best, math.hypot(dx, dz))
    return best

res = {}
p = os.path.join(root, 'assets/city-wall/A/wall-01.glb')
pts, sha = glb_positions(p)
d = min(math.hypot(max(SLAB[0] - x, 0, x - SLAB[2]), max(SLAB[1] - z, 0, z - SLAB[3])) for x, y, z in pts)
near = sorted(pts, key=lambda v: math.hypot(max(SLAB[0] - v[0], 0, v[0] - SLAB[2]), max(SLAB[1] - v[2], 0, v[2] - SLAB[3])))[:4]
de = min(seg_rect_dist((pts[a][0], pts[a][2]), (pts[b][0], pts[b][2])) for t3 in tris for a, b in ((t3[0], t3[1]), (t3[1], t3[2]), (t3[2], t3[0])))
res['wall-A-wall-01'] = {'minPlanDistanceEdgesToSlab_m': round(de, 3), 'triangles': len(tris),'path': 'assets/city-wall/A/wall-01.glb', 'sha256': sha, 'vertices': len(pts),
                         'minPlanDistanceToSlab_m': round(d, 3), 'nearestVertices': [[round(c, 3) for c in v] for v in near]}
json.dump(res, sys.stdout, indent=1)
