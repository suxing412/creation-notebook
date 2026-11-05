# LY-071 prep: surface deviation between LODs (vertex -> nearest surface of the other LOD), both directions.
# blender -b --factory-startup --python-exit-code 1 -P lod_surface_dev.py -- <out.json> <a.glb> <b.glb> [<a.glb> <b.glb> ...]
import bpy, bmesh, sys, json, os
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
out_path, pairs = argv[0], argv[1:]


def load(p):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=p)
    bm = bmesh.new()
    for o in bpy.context.scene.objects:
        if o.type != 'MESH':
            continue
        t = bmesh.new()
        t.from_mesh(o.data)
        t.transform(o.matrix_world)
        m = bpy.data.meshes.new('t')
        t.to_mesh(m)
        bm.from_mesh(m)
        t.free()
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    vs = [v.co.copy() for v in bm.verts]
    tree = BVHTree.FromBMesh(bm)
    bm.free()
    return vs, tree


def dev(vs, tree):
    ds = sorted(tree.find_nearest(v)[3] for v in vs)
    return {'max': round(ds[-1], 5), 'p99': round(ds[int(0.99 * (len(ds) - 1))], 5), 'mean': round(sum(ds) / len(ds), 5)}


res = {}
for i in range(0, len(pairs), 2):
    a, b = pairs[i], pairs[i + 1]
    va, ta = load(a)
    vb, tb = load(b)
    res[os.path.basename(a) + '|' + os.path.basename(b)] = {'a->b_surface': dev(va, tb), 'b->a_surface': dev(vb, ta)}
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(res, f, indent=1)
print('WROTE', out_path)
