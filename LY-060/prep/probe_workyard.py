# LY-060 prep: probe workyard-LOD0 ground levels by vertical ray casts (read-only).
# D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P probe_workyard.py -- workyard-LOD0.glb out.json
# For each probe XY, cast a ray from z=+10 straight down through every mesh and list all hits (object, z).
# Purpose: (1) where the walkable yard surface is, (2) whether the embedded pestle mortar base (z 0.20-0.32)
# sits in an earth opening or is enclosed inside workyard_earth (top 0.42), (3) what lies at/below z=0.20.
import bpy, sys, json
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
src, out = argv
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
dg = bpy.context.evaluated_depsgraph_get()
objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
def hits(x, y):
    res = []
    for o in objs:
        mi = o.matrix_world.inverted()
        org = Vector((x, y, 10.0)); d = Vector((0, 0, -1))
        oo = mi @ org; dd = (mi.to_3x3() @ d).normalized()
        start = oo
        for _ in range(40):
            ok, loc, nor, idx = o.ray_cast(start, dd, distance=50.0, depsgraph=dg)
            if not ok: break
            w = o.matrix_world @ loc
            res.append([o.name, round(w.z, 4)])
            start = loc + dd * 1e-4
    return sorted(res, key=lambda h: -h[1])
probes = {
  'yard_centre': (0.0, 0.0), 'yard_south': (0.0, -8.0), 'yard_north': (0.0, 8.0),
  'yard_east_free': (2.5, -6.0), 'yard_west_free': (-2.5, -6.0),
  'mortar_centre': (5.0, -0.2), 'mortar_edge': (4.6, -0.6), 'just_off_mortar': (5.0, 0.6),
  'pestle_treadle_end': (5.0, -2.6), 'corner_sw': (-8.9, -11.9), 'corner_ne': (8.9, 11.9),
  'outside_south_edge': (0.0, -12.1),
}
r = {k: {'xy': v, 'hits': hits(*v)} for k, v in probes.items()}
json.dump(r, open(out, 'w', encoding='utf-8'), indent=1)
for k, v in r.items(): print(k, v['xy'], v['hits'])
