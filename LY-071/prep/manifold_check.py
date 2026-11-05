# LY-071 prep: per-node inherited mesh defects (read-only measurement, no export).
# blender -b --factory-startup --python-exit-code 1 -P manifold_check.py -- <out.json> <glb...>
# Weld = merge-by-distance 1e-5 m on a copy in memory; counts boundary / non-manifold edges after weld.
import bpy, bmesh, sys, json, hashlib, os

argv = sys.argv[sys.argv.index('--') + 1:]
out_path, glbs = argv[0], argv[1:]


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


res = {'tool': 'manifold_check.py', 'blender': bpy.app.version_string, 'weld_m': 1e-5, 'files': {}}
for p in glbs:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=p)
    f = {'sha256': sha(p), 'nodes': {}}
    for o in bpy.context.scene.objects:
        if o.type != 'MESH':
            continue
        bm = bmesh.new()
        bm.from_mesh(o.data)
        raw_boundary = sum(1 for e in bm.edges if e.is_boundary)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        boundary = sum(1 for e in bm.edges if e.is_boundary)
        nonman = sum(1 for e in bm.edges if not e.is_manifold)
        wire = sum(1 for e in bm.edges if e.is_wire)
        f['nodes'][o.name] = {'faces': len(bm.faces), 'rawBoundaryEdges': raw_boundary,
                              'weldedBoundaryEdges': boundary, 'weldedNonManifoldEdges': nonman,
                              'wireEdges': wire}
        bm.free()
    res['files'][os.path.basename(p)] = f
json.dump(res, open(out_path, 'w', encoding='utf-8'), indent=1)
print(json.dumps(res, indent=1))
