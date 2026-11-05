# LY-032 prep: import a GLB read-only and dump world-space AABB per object (Blender, metres, Blender Z-up).
# usage: blender -b --factory-startup --python-exit-code 1 -P m01_bbox.py -- <glb> <out.json> [name_prefix_filter]
import bpy, sys, json
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
glb, out = argv[0], argv[1]
flt = argv[2] if len(argv) > 2 else ''
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
res = []
dg = bpy.context.evaluated_depsgraph_get()
for o in bpy.context.scene.objects:
    if o.type != 'MESH' or not o.name.startswith(flt):
        continue
    me = o.evaluated_get(dg).to_mesh()
    vs = [o.matrix_world @ v.co for v in me.vertices]
    mn = [min(v[i] for v in vs) for i in range(3)]
    mx = [max(v[i] for v in vs) for i in range(3)]
    # report in glTF axes: X east, Y up, Z(gltf) = -Blender Y
    res.append({'name': o.name, 'tris': sum(len(p.vertices) - 2 for p in me.polygons),
                'gltf_min': [round(mn[0], 4), round(mn[2], 4), round(-mx[1], 4)],
                'gltf_max': [round(mx[0], 4), round(mx[2], 4), round(-mn[1], 4)]})
    o.evaluated_get(dg).to_mesh_clear()
json.dump(res, open(out, 'w'), indent=1)
print('LY032 objects', len(res))
