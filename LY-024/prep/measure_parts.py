"""LY-024 prep: import a GLB (read-only), split every mesh into loose parts,
dump per-part AABB in glTF coordinates (Y-up, metres) + material + node name.
Usage: blender -b --factory-startup --python-exit-code 1 -P measure_parts.py -- in.glb out.json
"""
import bpy, bmesh, sys, json, hashlib
from mathutils import Vector
argv = sys.argv[sys.argv.index('--')+1:]
src, out = argv[0], argv[1]
sha = hashlib.sha256(open(src,'rb').read()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
def to_gltf(v):  # Blender Z-up -> glTF Y-up
    return [round(v.x,4), round(v.z,4), round(-v.y,4)]
parts = []
for ob in bpy.context.scene.objects:
    if ob.type != 'MESH': continue
    me = ob.data
    bm = bmesh.new(); bm.from_mesh(me); bm.transform(ob.matrix_world)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)  # weld split-normal seams so loose parts = solids
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    seen = set()
    for f0 in bm.faces:
        if f0.index in seen: continue
        stack=[f0]; comp=[]; seen.add(f0.index)
        while stack:
            f=stack.pop(); comp.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in seen:
                        seen.add(g.index); stack.append(g)
        vs = {v for f in comp for v in f.verts}
        pts=[to_gltf(v.co) for v in vs]
        mn=[min(p[i] for p in pts) for i in range(3)]; mx=[max(p[i] for p in pts) for i in range(3)]
        mats = sorted({(me.materials[f.material_index].name if me.materials else None) for f in comp})
        area = sum(f.calc_area() for f in comp)
        parts.append({'node':ob.name,'mat':mats,'tris':sum(len(f.verts)-2 for f in comp),
                      'min':mn,'max':mx,'size':[round(mx[i]-mn[i],4) for i in range(3)],'area':round(area,4)})
    bm.free()
json.dump({'src':src,'sha256':sha,'nParts':len(parts),'parts':parts}, open(out,'w',encoding='utf-8'), ensure_ascii=False, indent=0)
print('OK', src, len(parts))
