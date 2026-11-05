# LY-031 prep: independent Blender-importer cross-check of granary A doorway by BVH ray casts (read-only).
# D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P blender_ray_check.py -- <glb> <out.json>
# Blender converts glTF Y-up to Z-up: glTF (x, y, z) -> Blender (x, -z, y). Results are reported back in glTF axes.
import bpy, sys, json, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
glb, out = argv[0], argv[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
bm = bmesh.new()
for ob in bpy.context.scene.objects:
    if ob.type != 'MESH':
        continue
    me = ob.data.copy(); me.transform(ob.matrix_world)
    bm.from_mesh(me)
bvh = BVHTree.FromBMesh(bm)


def g2b(x, y, z):
    return Vector((x, -z, y))


res = {'glb': glb, 'objects': [o.name for o in bpy.context.scene.objects], 'tris': sum(len(f.verts) - 2 for f in bm.faces)}
# 1) clear width: from x=0 inside the doorway plane (glTF z=2.9) cast +x and -x at several heights
w = []
for y in [0.9, 1.2, 1.8, 2.5, 2.9]:
    hp = bvh.ray_cast(g2b(0, y, 2.9), Vector((1, 0, 0)), 10)
    hn = bvh.ray_cast(g2b(0, y, 2.9), Vector((-1, 0, 0)), 10)
    w.append({'y': y, 'plus_x': round(hp[0].x, 4) if hp[0] else None, 'minus_x': round(hn[0].x, 4) if hn[0] else None})
res['width_rays'] = w
# 2) clear height: cast up (+glTF y = +Blender z) and down at x in {-0.7,0,0.7}
h = []
for x in [-0.7, 0.0, 0.7]:
    up = bvh.ray_cast(g2b(x, 1.5, 2.9), Vector((0, 0, 1)), 10)
    dn = bvh.ray_cast(g2b(x, 1.5, 2.9), Vector((0, 0, -1)), 10)
    h.append({'x': x, 'soffit_y': round(up[0].z, 4) if up[0] else None, 'sill_y': round(dn[0].z, 4) if dn[0] else None})
res['height_rays'] = h
# 3) wall depth at doorway: cast along glTF -z from outside at y=3.05 (through lintel) and y=1.5 (through opening)
d = []
for y in [1.5, 3.05]:
    hit = bvh.ray_cast(g2b(0, y, 5.0), Vector((0, 1, 0)), 10)  # glTF -z == Blender +y
    d.append({'y': y, 'first_hit_gltf_z': round(-hit[0].y, 4) if hit[0] else None})
res['depth_rays'] = d
json.dump(res, open(out, 'w'), indent=1)
print(json.dumps(res))
