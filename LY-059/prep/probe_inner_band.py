# LY-059 prep: for each enclosure wall, find inner-face intervals with >= N m free depth behind the wall
# (candidate service-door zones), plus the free run straight in from the main gate.
# Usage: blender -b --factory-startup --python-exit-code 1 -P probe_inner_band.py -- in.glb out.json [wall_thick=0.35] [need=2.0]
import bpy, bmesh, sys, json, hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
src, out = argv[0], argv[1]
th = float(argv[2]) if len(argv) > 2 else 0.35
need = float(argv[3]) if len(argv) > 3 else 2.0
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
dg = bpy.context.evaluated_depsgraph_get()
V, T = [], []
for o in [o for o in bpy.context.scene.objects if o.type == 'MESH']:
    bm = bmesh.new(); bm.from_object(o, dg); bm.transform(o.matrix_world)
    bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.verts.ensure_lookup_table()
    b = len(V); V += [v.co.copy() for v in bm.verts]; T += [[v.index + b for v in f.verts] for f in bm.faces]; bm.free()
bvh = BVHTree.FromPolygons(V, T)
X0, X1, Y0, Y1 = -9.0, 9.0, -12.0, 12.0  # outer wall faces (measured by measure_enclosure.py)
walls = {
    'south(-Y)': ('x', Y0 + th + 0.01, Vector((0, 1, 0)), X0 + th, X1 - th),
    'north(+Y)': ('x', Y1 - th - 0.01, Vector((0, -1, 0)), X0 + th, X1 - th),
    'west(-X)': ('y', X0 + th + 0.01, Vector((1, 0, 0)), Y0 + th, Y1 - th),
    'east(+X)': ('y', X1 - th - 0.01, Vector((-1, 0, 0)), Y0 + th, Y1 - th),
}
res = {'file': src.replace('\\', '/'), 'sha256': hashlib.sha256(open(src, 'rb').read()).hexdigest(),
       'wallThickness_assumed': th, 'freeDepthRequired_m': need, 'heights_m_above_0.2': [0.3, 1.0, 1.8], 'walls': {}}
for wn, (ax, fixed, d, a0, a1) in walls.items():
    rows = []
    a = a0
    while a <= a1 + 1e-6:
        depth = []
        for z in [0.5, 1.2, 2.0]:
            p = Vector((a, fixed, z)) if ax == 'x' else Vector((fixed, a, z))
            h = bvh.ray_cast(p, d, 30)
            depth.append(30.0 if h[0] is None else h[3])
        rows.append((round(a, 2), round(min(depth), 3)))
        a += 0.1
    runs = []; cur = None
    for a, dep in rows:
        if dep >= need:
            cur = [a, a] if cur is None else [cur[0], a]
        elif cur is not None: runs.append(cur); cur = None
    if cur: runs.append(cur)
    res['walls'][wn] = {'freeRuns': [[r[0], r[1], round(r[1] - r[0], 2)] for r in runs],
                        'minDepthProfile_every0.5m': [r for i, r in enumerate(rows) if i % 5 == 0]}
# straight run in from the main gate centre
g = []
for z in [0.5, 1.2, 2.0]:
    h = bvh.ray_cast(Vector((-4.8, -9.35, z)), Vector((0, 1, 0)), 30)
    g.append(None if h[0] is None else [round(h[3], 3), [round(c, 3) for c in h[0]]])
res['gateInwardRun_from_y-9.35_x-4.8'] = g
json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for wn, w in res['walls'].items(): print(wn, w['freeRuns'])
print('gate run', g)
