# LY-086 prep: along-axis probes at the cover/shaft and shell/shaft joints, per assembled inspection part (read-only).
# D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P probe_joint.py -- <lab_root> <out.json>
import bpy, bmesh, sys, os, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
p = os.path.join(a[0], 'docs/library/models/m-luoyang-palace-waterway-interface/files/palace-waterway-interface-inspection-near.glb')
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=p)
R = {}
for o in [x for x in bpy.context.scene.objects if x.type == 'MESH']:
    o.location = (0, 0, 0)
bpy.context.view_layer.update()
for o in [x for x in bpy.context.scene.objects if x.type == 'MESH']:
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world); bvh = BVHTree.FromBMesh(bm)
    out = {}
    for (y, z) in [(0.68, 0.0), (0.68, 0.4), (0.3, 0.4), (0.3, 0.6), (1.2, 0.6), (0.05, 0.0)]:
        hits = []; org = Vector((-10, -z, y)); d = Vector((1, 0, 0)); t = 0
        for _ in range(40):
            loc, n, i, dist = bvh.ray_cast(org, d, 30 - t)
            if loc is None: break
            hits.append(round(loc.x, 4)); org = loc + d * 1e-4; t = loc.x + 10
        out[f'y{y}_z{z}'] = hits
    R[o.name] = out
json.dump(R, open(a[1], 'w'), indent=1); print('WROTE')
