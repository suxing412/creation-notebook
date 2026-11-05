# LY-059 prep: scan the wall-top coping along each enclosure wall centreline (vertical rays, 0.05 m step);
# reports which material/object forms the top surface and runs where bare earth (wall top) is exposed.
# Usage: blender -b --factory-startup --python-exit-code 1 -P probe_coping.py -- in.glb out.json
import bpy, bmesh, sys, json, hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
src, out = argv[0], argv[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
dg = bpy.context.evaluated_depsgraph_get()
trees = []
for o in [o for o in bpy.context.scene.objects if o.type == 'MESH']:
    bm = bmesh.new(); bm.from_object(o, dg); bm.transform(o.matrix_world)
    bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.verts.ensure_lookup_table()
    trees.append((o.name, BVHTree.FromPolygons([v.co.copy() for v in bm.verts], [[v.index for v in f.verts] for f in bm.faces]))); bm.free()


def top(x, y):
    best = None
    for n, t in trees:
        h = t.ray_cast(Vector((x, y, 20)), Vector((0, 0, -1)), 40)
        if h[0] is not None and (best is None or h[0].z > best[1]): best = (n, round(h[0].z, 3))
    return best

lines = {'south(-Y)': ('x', -11.825, -9.0, 9.0), 'north(+Y)': ('x', 11.825, -9.0, 9.0),
         'west(-X)': ('y', -8.825, -12.0, 12.0), 'east(+X)': ('y', 8.825, -12.0, 12.0)}
res = {'file': src.replace('\\', '/'), 'sha256': hashlib.sha256(open(src, 'rb').read()).hexdigest(), 'lines': {}}
for ln, (ax, fixed, a0, a1) in lines.items():
    rows = []; a = a0
    while a <= a1 + 1e-6:
        h = top(a, fixed) if ax == 'x' else top(fixed, a)
        rows.append((round(a, 3), h)); a += 0.05
    bare = []; cur = None
    for a, h in rows:
        isbare = h is not None and not h[0].endswith('tile')
        if isbare: cur = [a, a, h[0], h[1]] if cur is None else [cur[0], a, cur[2], cur[3]]
        elif cur is not None: bare.append(cur); cur = None
    if cur: bare.append(cur)
    none = [a for a, h in rows if h is None]
    res['lines'][ln] = {'samples': len(rows), 'bareTopRuns': [[b[0], b[1], round(b[1] - b[0] + 0.05, 2), b[2], b[3]] for b in bare],
                        'noHitSamples': none}
json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for ln, v in res['lines'].items(): print(ln, 'bare', v['bareTopRuns'], 'nohit', v['noHitSamples'][:20])
