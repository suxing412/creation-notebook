# LY-035 prep: independent Blender import of the in-city granary LOD0 (read-only).
# D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P blender_crosscheck.py -- <glb> <out_json>
# Blender converts glTF Y-up to Z-up: blender (x, y, z) = glTF (x, -z, y). We report back in glTF axes.
import bpy, sys, json, bmesh
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
glb, out = argv[0], argv[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
dg = bpy.context.evaluated_depsgraph_get()
res = {'glb': glb, 'blender': bpy.app.version_string, 'objects': []}
tot = 0
gmin = [1e18] * 3
gmax = [-1e18] * 3
for ob in bpy.context.scene.objects:
    if ob.type != 'MESH':
        continue
    me = ob.evaluated_get(dg).to_mesh()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=bm.faces[:])
    ntri = len(bm.faces)
    ws = [ob.matrix_world @ v.co for v in bm.verts]
    lo = [min(w[i] for w in ws) for i in range(3)]
    hi = [max(w[i] for w in ws) for i in range(3)]
    # glTF axes
    glo = [lo[0], lo[2], -hi[1]]
    ghi = [hi[0], hi[2], -lo[1]]
    islands = 0
    seen = set()
    for f in bm.faces:
        if f.index in seen:
            continue
        islands += 1
        stack = [f]
        seen.add(f.index)
        while stack:
            g = stack.pop()
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index); stack.append(h)
    res['objects'].append({'name': ob.name, 'tris': ntri, 'islandsByTopology': islands,
                           'materials': [s.material.name for s in ob.material_slots if s.material],
                           'bboxMin_gltf': [round(v, 4) for v in glo], 'bboxMax_gltf': [round(v, 4) for v in ghi]})
    tot += ntri
    for i in range(3):
        gmin[i] = min(gmin[i], glo[i]); gmax[i] = max(gmax[i], ghi[i])
    bm.free(); ob.evaluated_get(dg).to_mesh_clear()
res['totalTris'] = tot
res['bboxMin_gltf'] = [round(v, 4) for v in gmin]
res['bboxMax_gltf'] = [round(v, 4) for v in gmax]
json.dump(res, open(out, 'w', encoding='utf-8'), indent=1)
print(json.dumps({k: res[k] for k in ('totalTris', 'bboxMin_gltf', 'bboxMax_gltf')}))
