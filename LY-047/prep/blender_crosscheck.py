# LY-047 prep: independent cross-check with Blender's own glTF importer (read-only; nothing is saved).
# usage: blender -b --factory-startup --python-exit-code 1 -P blender_crosscheck.py -- <lab_root> <out.json>
# Blender frame: X = glTF x, Y = -glTF z, Z = glTF y.
import bpy, sys, json, os
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
LAB, OUT = argv[0], argv[1]
D = os.path.join(LAB, 'docs')
FILES = {
    'B-LOD0': 'cities/luoyang/assets/r01/R01-B-LOD0-prototype.glb',
    'B2-LOD0': 'cities/luoyang/assets/c02v/B2-LOD0-prototype.glb',
    'A2-LOD0': 'cities/luoyang/assets/c02v/A2-LOD0-prototype.glb',
    'workshed-LOD0': 'library/models/m-luoyang-workyard-shed/files/workshed-LOD0.glb',
}
SHED = {'B-LOD0': (-7.2, -4.4, -0.4, 5.4), 'B2-LOD0': (-4.75, -0.3, 0.85, 4.15)}  # glTF x0,x1,z0,z1
res = {'tool': 'blender_crosscheck.py', 'blender': bpy.app.version_string, 'files': {}}
for key, relp in FILES.items():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(D, relp))
    dg = bpy.context.evaluated_depsgraph_get()
    ent = {'objects': {}}
    floor_verts, beam_low, bin_tops = 0, None, []
    for ob in bpy.context.scene.objects:
        if ob.type != 'MESH':
            continue
        me = ob.evaluated_get(dg).to_mesh()
        W = ob.matrix_world
        vs = [W @ v.co for v in me.vertices]
        if not vs:
            continue
        mn = [min(v[i] for v in vs) for i in range(3)]; mx = [max(v[i] for v in vs) for i in range(3)]
        ent['objects'][ob.name] = {'verts': len(vs), 'tris': sum(len(p.vertices) - 2 for p in me.polygons),
                                   'min_gltf': [round(mn[0], 4), round(mn[2], 4), round(-mx[1], 4)],
                                   'max_gltf': [round(mx[0], 4), round(mx[2], 4), round(-mn[1], 4)]}
        if key in SHED and 'roof' not in ob.name and 'site' not in ob.name and 'designed' not in ob.name:
            x0, x1, z0, z1 = SHED[key]
            inside = [v for v in vs if x0 <= v[0] <= x1 and z0 <= -v[1] <= z1]
            floor_verts += sum(1 for v in inside if abs(v[2] - 0.2) < 1e-4)
            hi = [v[2] for v in inside if v[2] > 2.0]
            if hi:
                beam_low = min(hi) if beam_low is None else min(beam_low, min(hi))
        ob.evaluated_get(dg).to_mesh_clear()
    if key in SHED:
        ent['shed_box_gltf'] = SHED[key]
        ent['shed_floor_vertices_y0.2'] = floor_verts
        ent['shed_lowest_overhead_vertex_y'] = None if beam_low is None else round(beam_low, 4)
    res['files'][key] = ent
json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
print('wrote', OUT)
