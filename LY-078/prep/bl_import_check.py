# LY-078 prep: Blender read-back of stoneclassic GLBs (no export, no save).
# D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P bl_import_check.py -- out.json glb1 [glb2 ...]
import bpy, sys, json, mathutils
argv = sys.argv[sys.argv.index('--') + 1:]
out_path, glbs = argv[0], argv[1:]
res = {'blender': bpy.app.version_string, 'files': []}
for g in glbs:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=g)
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    rec = {'path': g, 'meshObjects': len(objs), 'objects': []}
    lo = mathutils.Vector((1e9,)*3); hi = mathutils.Vector((-1e9,)*3)
    for o in objs:
        me = o.data
        ws = [o.matrix_world @ v.co for v in me.vertices]
        olo = mathutils.Vector([min(w[i] for w in ws) for i in range(3)]); ohi = mathutils.Vector([max(w[i] for w in ws) for i in range(3)])
        for i in range(3): lo[i] = min(lo[i], olo[i]); hi[i] = max(hi[i], ohi[i])
        me.calc_loop_triangles()
        rec['objects'].append({'name': o.name, 'verts': len(me.vertices), 'tris': len(me.loop_triangles),
                               'materials': [m.name for m in me.materials if m], 'uvLayers': len(me.uv_layers),
                               'matrixIsIdentity': o.matrix_world == mathutils.Matrix.Identity(4),
                               'extrasKeys': sorted(k for k in o.keys() if not k.startswith('_'))})
    # Blender Z-up: glTF (x,y,z) -> Blender (x,-z,y)
    rec['blenderBounds'] = {'min': [round(v, 4) for v in lo], 'max': [round(v, 4) for v in hi]}
    res['files'].append(rec)
json.dump(res, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('OK', out_path)
