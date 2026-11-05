# LY-082 prep: independent Blender cross-check of the gate->lane ground probe (read-only).
# D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P blender_xcheck82.py -- <lab_root> <out.json>
# Imports the four ground atoms (D08 offset +[580,0,-960] glTF = Blender (580, 960, 0)), then casts rays straight
# down at points on the C02-010 gate axis (x=527.5) and at the C02-021 gate axis (z=-897.13), reporting hit height
# and the object hit. glTF (x,y,z) -> Blender (x,-z,y).
import bpy, sys, json, mathutils
argv = sys.argv[sys.argv.index('--') + 1:]
lab, out = argv[0].rstrip('/'), argv[1]
G = lab + '/docs/cities/luoyang/assets/ground-atomic/'
bpy.ops.wm.read_factory_settings(use_empty=True)
objs = {}
for name, off in [('network-ground-stitched', (0, 0, 0)), ('retained', (0, 0, 0)), ('south', (0, 0, 0)), ('D08', (580, 960, 0))]:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=G + name + '.glb')
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.parent is None:
            o.location = mathutils.Vector(o.location) + mathutils.Vector(off)
        objs[o.name] = name
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
scene = bpy.context.scene
res = {'objects': {}, 'rays': []}
for o in bpy.data.objects:
    if o.type == 'MESH':
        me = o.evaluated_get(dg).to_mesh()
        me.calc_loop_triangles()
        bb = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
        res['objects'][o.name] = {'file': objs.get(o.name), 'triangles': len(me.loop_triangles),
                                  'bboxBlender_min': [round(min(v[i] for v in bb), 3) for i in range(3)],
                                  'bboxBlender_max': [round(max(v[i] for v in bb), 3) for i in range(3)]}
pts = []
for zg in [-806.40, -805.0, -804.4, -803.7, -803.0, -802.0, -800.0, -798.0, -797.2, -796.2, -795.0, -793.8]:
    for xg in [526.1, 527.5, 528.9]:
        pts.append(('C02-010', xg, zg))
for xg in [705.4, 704.0, 703.4, 702.0, 700.0, 697.0, 695.5]:
    pts.append(('C02-021', xg, -897.13))
for tag, xg, zg in pts:
    o = mathutils.Vector((xg, -zg, 10.0))
    hit, loc, nrm, idx, ob, mtx = scene.ray_cast(dg, o, mathutils.Vector((0, 0, -1)))
    res['rays'].append({'court': tag, 'gltf_x': xg, 'gltf_z': zg, 'hit': bool(hit),
                        'y_gltf': round(loc.z, 4) if hit else None, 'object': ob.name if hit else None,
                        'file': objs.get(ob.name) if hit else None,
                        'normal_up': round(nrm.z, 4) if hit else None})
res['blender'] = bpy.app.version_string
json.dump(res, open(out, 'w', encoding='utf-8'), indent=1)
print('LY082_XCHECK_OK', len(res['rays']))
