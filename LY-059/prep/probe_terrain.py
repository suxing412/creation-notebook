# LY-059 prep: sample ground GLBs under a placed courtyard lot (gate route, wall line, lot interior).
# Usage: blender -b --factory-startup --python-exit-code 1 -P probe_terrain.py -- out.json cx cy gx gy ground1.glb [ground2.glb ...]
#   cx,cy: lot centre in Blender world XY (= layout.json position); gx,gy: gate point (= layout.json gate).
import bpy, bmesh, sys, json, hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
out = argv[0]; cx, cy, gx, gy = map(float, argv[1:5]); files = argv[5:]
bpy.ops.wm.read_factory_settings(use_empty=True)
res = {'lotCentre': [cx, cy], 'gate': [gx, gy], 'grounds': []}
trees = []
for f in files:
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=f)
    new = [o for o in bpy.context.scene.objects if o not in before and o.type == 'MESH']
    dg = bpy.context.evaluated_depsgraph_get()
    lo = Vector((1e18,) * 3); hi = Vector((-1e18,) * 3)
    for o in new:
        bm = bmesh.new(); bm.from_object(o, dg); bm.transform(o.matrix_world)
        bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.verts.ensure_lookup_table()
        vs = [v.co.copy() for v in bm.verts]; ts = [[v.index for v in fc.verts] for fc in bm.faces]
        for v in vs: lo = Vector(map(min, lo, v)); hi = Vector(map(max, hi, v))
        trees.append((f.split('/')[-1], o.name, BVHTree.FromPolygons(vs, ts)))
        bm.free()
    res['grounds'].append({'file': f.replace('\\', '/'), 'sha256': hashlib.sha256(open(f, 'rb').read()).hexdigest(),
                           'objects': [o.name for o in new], 'bbox': [list(lo), list(hi)]})


def top(x, y):
    best = None
    for fn, on, t in trees:
        h = t.ray_cast(Vector((x, y, 500)), Vector((0, 0, -1)), 1000)
        if h[0] is not None and (best is None or h[0].z > best[2]):
            best = (fn, on, round(h[0].z, 4))
    return best

res['gateRoute'] = [{'y': round(gy + d, 2), 'hit': top(gx, gy + d)} for d in [x * 0.25 for x in range(-24, 17)]]
pts = []
for dx in [-9, -6.3, -4.8, -3.3, 0, 4.5, 9]:
    for dy in [-14, -12.5, -12.0, -11.0, 0, 11.0, 12.0, 14]:
        pts.append({'dx': dx, 'dy': dy, 'hit': top(cx + dx, cy + dy)})
res['lotSamples'] = pts
json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for g in res['grounds']: print(g['file'].split('/')[-1], [round(v, 1) for v in g['bbox'][0]], [round(v, 1) for v in g['bbox'][1]])
for r in res['gateRoute'][::2]: print(r)
