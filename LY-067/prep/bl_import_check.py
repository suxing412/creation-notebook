"""LY-067 prep: Blender cross-check of the numpy foot measurement.
D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P bl_import_check.py -- <out.json> <glb> [...]
Imports each GLB into an empty scene, converts to Blender Z-up world coords,
splits mesh objects into loose parts and reports parts whose lowest Z is
within 1 mm of the global minimum (footing plinths) plus their XY centres.
Blender world (X, Y, Z) == glTF (X, -Z, Y).
"""
import json
import sys

import bmesh
import bpy

args = sys.argv[sys.argv.index('--') + 1:]
out, glbs = args[0], args[1:]
res = []
for g in glbs:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=g)
    parts = []
    for ob in [o for o in bpy.context.scene.objects if o.type == 'MESH']:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.transform(ob.matrix_world)
        bm.verts.ensure_lookup_table()
        seen = set()
        for v in bm.verts:
            if v.index in seen:
                continue
            stack, isl = [v], []
            seen.add(v.index)
            while stack:
                x = stack.pop()
                isl.append(x.co.copy())
                for e in x.link_edges:
                    o = e.other_vert(x)
                    if o.index not in seen:
                        seen.add(o.index)
                        stack.append(o)
            xs = [c.x for c in isl]; ys = [c.y for c in isl]; zs = [c.z for c in isl]
            parts.append({'obj': ob.name, 'min': [min(xs), min(ys), min(zs)], 'max': [max(xs), max(ys), max(zs)]})
        bm.free()
    zmin = min(p['min'][2] for p in parts)
    low = [p for p in parts if abs(p['min'][2] - zmin) < 1e-3]
    res.append({'glb': g, 'mesh_objects': sorted({p['obj'] for p in parts}), 'loose_parts': len(parts),
                'zmin': round(zmin, 5), 'zmax': round(max(p['max'][2] for p in parts), 5),
                'parts_at_zmin': len(low),
                'parts_at_zmin_centres_xy': sorted([[round((p['min'][0] + p['max'][0]) / 2, 4),
                                                     round((p['min'][1] + p['max'][1]) / 2, 4)] for p in low]),
                'parts_at_zmin_size': sorted({(round(p['max'][0] - p['min'][0], 4), round(p['max'][1] - p['min'][1], 4),
                                               round(p['max'][2] - p['min'][2], 4)) for p in low})})
    print('LY067', g.rsplit('/', 1)[-1], res[-1]['loose_parts'], res[-1]['zmin'], res[-1]['parts_at_zmin'], res[-1]['parts_at_zmin_size'])
json.dump(res, open(out, 'w', encoding='utf-8'), indent=1)
