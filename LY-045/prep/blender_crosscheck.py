# LY-045 prep: Blender import cross-check of the numpy reader (read-only on inputs).
# D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P blender_crosscheck.py -- <lab_root> <out.json>
# Imports each service-court GLB with the official glTF importer and records per-object triangle
# count, world bbox (converted back to glTF axes), and the privy floor hole probe by BVH ray cast.
import bpy, sys, os, json, hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
LAB, OUT = argv[0], argv[1]
LIB = os.path.join(LAB, 'docs/library/models/m-luoyang-service-court/files')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


res = {}
for f in ['service-A-LOD0.glb', 'service-A-LOD1.glb', 'service-A-LOD2.glb']:
    p = os.path.join(LIB, f)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=p)
    dg = bpy.context.evaluated_depsgraph_get()
    objs = {}
    verts, polys = [], []
    for o in bpy.context.scene.objects:
        if o.type != 'MESH':
            continue
        me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles()
        mw = o.matrix_world
        ws = [mw @ v.co for v in me.vertices]
        gl = [(v.x, v.z, -v.y) for v in ws]
        xs, ys, zs = zip(*gl)
        objs[o.name] = {'tris': len(me.loop_triangles), 'bboxMin': [round(min(xs), 4), round(min(ys), 4), round(min(zs), 4)],
                        'bboxMax': [round(max(xs), 4), round(max(ys), 4), round(max(zs), 4)]}
        base = len(verts)
        verts += ws
        polys += [tuple(base + i for i in lt.vertices) for lt in me.loop_triangles]
        o.evaluated_get(dg).to_mesh_clear()
    tree = BVHTree.FromPolygons(verts, polys)
    # hole centre (glTF x 0, z -2.26) -> Blender (x, y=-z) = (0, 2.26); cast down from y_gl 1.3 (just under floor top)
    hits = []
    for gx, gz in [(0.0, -2.26), (-0.15, -2.40), (0.15, -2.12)]:
        loc, nrm, idx, dist = tree.ray_cast(Vector((gx, -gz, 1.39)), Vector((0, 0, -1)), 10.0)
        hits.append({'xz': [gx, gz], 'downHit': None if loc is None else round(loc.z, 4)})
    # solid floor point for contrast
    loc, nrm, idx, dist = tree.ray_cast(Vector((0.5, 3.5, 2.0)), Vector((0, 0, -1)), 10.0)
    res[f] = {'sha256': sha(p), 'objects': objs, 'totalTris': sum(o['tris'] for o in objs.values()),
              'holeDownRays_fromY1.39': hits, 'solidFloorDownRay_from2.0_at(0.5,-3.5)': None if loc is None else round(loc.z, 4),
              'blender': bpy.app.version_string}
json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
print(json.dumps({k: {'totalTris': v['totalTris'], 'hole': v['holeDownRays_fromY1.39'], 'solid': v['solidFloorDownRay_from2.0_at(0.5,-3.5)']} for k, v in res.items()}))
