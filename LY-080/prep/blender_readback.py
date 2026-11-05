# LY-080 prep: independent Blender import readback of the three published northern-altar GLBs.
# Usage: D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P blender_readback.py -- <glb>... <out_json>
import bpy, bmesh, sys, json, hashlib
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
glbs, out = argv[:-1], argv[-1]
res = []
for p in glbs:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=p)
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    r = {'path': p, 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest(), 'meshObjects': len(objs), 'objects': []}
    for o in objs:
        bm = bmesh.new(); bm.from_mesh(o.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        bm.transform(o.matrix_world)
        ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
        mn = [min(v[i] for v in ws) for i in range(3)]; mx = [max(v[i] for v in ws) for i in range(3)]
        r['objects'].append({
            'name': o.name,
            'blenderBBoxMin_Zup': [round(x, 5) for x in mn], 'blenderBBoxMax_Zup': [round(x, 5) for x in mx],
            'dims': [round(x, 5) for x in o.dimensions],
            'faces': len(bm.faces), 'verts': len(bm.verts),
            'nonManifoldEdges': sum(1 for e in bm.edges if not e.is_manifold),
            'boundaryEdges': sum(1 for e in bm.edges if e.is_boundary),
            'volume_m3': round(bm.calc_volume(signed=True), 4),
            'materials': [m.name for m in o.data.materials if m],
            'uvLayers': [u.name for u in o.data.uv_layers],
            'matrixIsIdentityScale': [round(x, 6) for x in o.matrix_world.to_scale()],
        })
        bm.free()
    res.append(r)
json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE', out)
