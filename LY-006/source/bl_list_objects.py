# LY-006: list mesh objects of a .blend with world AABB converted to glTF axes (x, z_b, -y_b). Read-only.
import bpy, sys, json, hashlib
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
out = []
for ob in bpy.data.objects:
    if ob.type != 'MESH': continue
    vs = [ob.matrix_world @ v.co for v in ob.data.vertices]
    if not vs: continue
    g = [(v.x, v.z, -v.y) for v in vs]
    mn = [min(c[i] for c in g) for i in range(3)]; mx = [max(c[i] for c in g) for i in range(3)]
    out.append({'name': ob.name, 'collections': [c.name for c in ob.users_collection], 'hide_render': ob.hide_render,
                'verts': len(vs), 'aabb_gltf': [[round(x, 4) for x in mn], [round(x, 4) for x in mx]]})
json.dump({'blend': bpy.data.filepath, 'objects': out}, open(args[0], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(out), 'mesh objects')
