# LY-041 independent cross-check in Blender (does not use glbio.py).
# D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P blender_crosscheck.py -- <LAB> <out.json>
# Imports A2-LOD0/LOD1 + ground-south via Blender's glTF importer, places A2 at the C-alt matrix,
# and for every bottom vertex (world y within 5 mm of the lowest retained vertex) ray-casts down/up
# against ground-south to measure the gap. Read-only on LAB.
import bpy, sys, json, hashlib, os
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
LAB, OUT = argv[0], argv[1]
CITY = os.path.join(LAB, 'docs/cities/luoyang')
EXCL = {'site_lot', 'site_neutral_lane', 'designed_hardpacked_activity_ground'}
T = (531.0, 0.0, -818.45)  # glTF world translation (Y-up); C-alt matrix is pure translation


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def imp(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before]


def gl(v):  # Blender Z-up -> glTF Y-up
    return (v.x, v.z, -v.y)


def bvh_of(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    verts, polys = [], []
    for o in objs:
        if o.type != 'MESH':
            continue
        me = o.evaluated_get(dg).to_mesh()
        off = len(verts)
        verts += [o.matrix_world @ v.co for v in me.vertices]
        polys += [[off + i for i in p.vertices] for p in me.polygons]
    return BVHTree.FromPolygons(verts, polys), len(polys)


res = {'tool': 'blender ' + bpy.app.version_string, 'sha': {}, 'lods': {}}
for f in ['assets/ground-atomic/south.glb', 'assets/c02v/A2-LOD0-prototype.glb', 'assets/c02v/A2-LOD1-prototype.glb']:
    res['sha'][f] = sha(os.path.join(CITY, f))

bpy.ops.wm.read_factory_settings(use_empty=True)
ground = imp(os.path.join(CITY, 'assets/ground-atomic/south.glb'))
gbvh, gpolys = bvh_of(ground)
res['groundPolys'] = gpolys
# lot sampling (glTF x 522..540, z -830.45..-806.45) at 0.5 m
tops = []
miss = 0
x = 522.25
while x < 540:
    z = -830.2
    while z < -806.45:
        hit = gbvh.ray_cast(Vector((x, -z, 5.0)), Vector((0, 0, -1)), 20)
        if hit[0] is None:
            miss += 1
        else:
            tops.append(round(hit[0].z, 6))
        z += 0.5
    x += 0.5
res['lotSamples'] = {'n': len(tops) + miss, 'noGround': miss, 'topMin': min(tops), 'topMax': max(tops)}

ok = True
for lod in ['LOD0', 'LOD1']:
    objs = imp(os.path.join(CITY, 'assets/c02v/A2-%s-prototype.glb' % lod))
    roots = [o for o in objs if o.parent is None]
    M = Matrix.Translation((T[0], -T[2], T[1]))  # glTF (x,y,z) -> Blender (x,-z,y)
    for r in roots:
        r.matrix_world = M @ r.matrix_world
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    kept = [o for o in objs if o.type == 'MESH' and not any(o.name.startswith(e) for e in EXCL)]
    excluded = sorted(o.name for o in objs if o.type == 'MESH' and any(o.name.startswith(e) for e in EXCL))
    pts = {}
    for o in kept:
        me = o.evaluated_get(dg).to_mesh()
        pts[o.name] = [o.matrix_world @ v.co for v in me.vertices]
    ymin = min(p.z for ps in pts.values() for p in ps)
    per = {}
    for name, ps in pts.items():
        bot = [p for p in ps if p.z <= ymin + 0.005]
        gaps, nog = [], 0
        for p in bot:
            hit = gbvh.ray_cast(p + Vector((0, 0, 1.0)), Vector((0, 0, -1)), 3.0)
            if hit[0] is None:
                nog += 1
            else:
                gaps.append(p.z - hit[0].z)
        if bot:
            per[name] = {'bottomVerts': len(bot), 'noGround': nog,
                         'gapMin': min(gaps) if gaps else None, 'gapMax': max(gaps) if gaps else None}
            if nog or (gaps and max(abs(min(gaps)), abs(max(gaps))) > 1e-5):
                ok = False
    res['lods'][lod] = {'keptMeshes': sorted(pts), 'excludedMeshes': excluded, 'worldMinY': ymin, 'bottom': per}
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
res['pass'] = ok and miss == 0
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('LY041_CROSSCHECK', 'PASS' if res['pass'] else 'FAIL')
sys.exit(0 if res['pass'] else 1)
