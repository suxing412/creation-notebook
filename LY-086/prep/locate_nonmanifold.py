# LY-086 prep: locate non-manifold edges remaining after a 1e-4 m weld, per LOD (read-only).
# D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P locate_nonmanifold.py -- <lab_root> <out.json>
import bpy, bmesh, sys, os, json
argv = sys.argv[sys.argv.index('--') + 1:]
LAB, OUT = argv[0], argv[1]
D = os.path.join(LAB, 'docs/library/models/m-luoyang-palace-waterway-interface/files')
R = {}
for key in ['near', 'mid', 'far']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(D, f'palace-waterway-interface-{key}.glb'))
    o = [x for x in bpy.context.scene.objects if x.type == 'MESH'][0]
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    rows = []
    for e in bm.edges:
        if not e.is_manifold:
            a, b = e.verts[0].co, e.verts[1].co
            g = lambda v: [round(v.x, 3), round(v.z, 3), round(-v.y, 3)]
            rows.append({'a': g(a), 'b': g(b), 'faces': len(e.link_faces), 'len': round(e.calc_length(), 4)})
    R[key] = rows
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1)
print('WROTE', OUT)
