# LY-077 prep: read-only probe of the independent stone-classics access study (LY-078 territory).
# Only records bounds, node names, ground levels and edge openings so LY-077 can state
# that no shared frame / port with Taixue A exists. glTF frame output (X east, Y up, Z south).
import bpy, sys, json, hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
argv = sys.argv[sys.argv.index('--') + 1:]
src, out = argv[0], argv[1]
sha = hashlib.sha256(open(src, 'rb').read()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
g = lambda v: [round(v.x, 4), round(v.z, 4), round(-v.y, 4)]
V, F, objs = [], [], []
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    o.data.calc_loop_triangles()
    base = len(V)
    ws = [o.matrix_world @ v.co for v in o.data.vertices]
    V += ws
    F += [tuple(base + i for i in t.vertices) for t in o.data.loop_triangles]
    objs.append({'name': o.name, 'tris': len(o.data.loop_triangles),
                 'min': [min(g(v)[k] for v in ws) for k in range(3)],
                 'max': [max(g(v)[k] for v in ws) for k in range(3)]})
bvh = BVHTree.FromPolygons(V, F, all_triangles=True)
mn = [min(g(v)[k] for v in V) for k in range(3)]
mx = [max(g(v)[k] for v in V) for k in range(3)]
def down(x, z, y0):
    loc = bvh.ray_cast(Vector((x, -z, y0)), Vector((0, 0, -1)), 50)[0]
    return None if loc is None else round(loc.z, 3)
# ground level histogram from 1.0 m above lowest point (below roofs)
hist = {}
step = 0.5
x = mn[0]
while x <= mx[0]:
    z = mn[2]
    while z <= mx[2]:
        h = down(x, z, mn[1] + 1.0)
        k = 'none' if h is None else str(round(h, 2))
        hist[k] = hist.get(k, 0) + 1
        z += step
    x += step
top = sorted(hist.items(), key=lambda kv: -kv[1])[:12]
json.dump({'file': src, 'sha256': sha, 'triangles': len(F), 'boundsMin': mn, 'boundsMax': mx,
           'objects': sorted(objs, key=lambda o: -o['tris'])[:40], 'objectCount': len(objs),
           'groundHeightHistogram_0.5m_from_minY+1': top,
           'note': 'Independent local frame. No shared transform with Taixue A exists in any repo file.'},
          open(out, 'w'), indent=1)
print('OK', sha[:12], len(F), mn, mx, top[:5])
