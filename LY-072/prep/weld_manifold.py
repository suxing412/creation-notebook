# LY-072 prep (read-only): per-object closure check after welding split glTF vertices.
# Usage: blender -b --factory-startup --python-exit-code 1 -P weld_manifold.py -- <out.json> <glb> [<glb> ...]
import bpy, bmesh, sys, json, hashlib
argv = sys.argv[sys.argv.index('--') + 1:]
OUT, GLBS = argv[0], argv[1:]
res = []
for p in GLBS:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=p)
    for o in [o for o in bpy.context.scene.objects if o.type == 'MESH']:
        bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
        bd = sum(1 for e in bm.edges if e.is_boundary)
        nm = sum(1 for e in bm.edges if not e.is_manifold)
        down = sum(f.calc_area() for f in bm.faces if f.normal.z < -0.99)
        minz = min(v.co.z for v in bm.verts)
        down_at_min = sum(f.calc_area() for f in bm.faces if f.normal.z < -0.99 and abs(f.calc_center_median().z - minz) < 1e-3)
        res.append({'glb': p.replace('\\', '/').split('/')[-1], 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest(),
                    'object': o.name, 'weldedVerts': len(bm.verts), 'faces': len(bm.faces),
                    'boundaryEdges': bd, 'nonManifoldEdges': nm, 'minZ': round(minz, 4),
                    'downFacingArea_m2': round(down, 3), 'downFacingAreaAtMinZ_m2': round(down_at_min, 3)})
        bm.free()
json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
print('WROTE', OUT)
