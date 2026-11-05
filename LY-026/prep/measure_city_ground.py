"""LY-026 prep: city trial ground around the well (read-only).
blender -b --factory-startup --python-exit-code 1 -P measure_city_ground.py -- <chunk.glb> <out.json> ox oy oz
Reports the ground opening radius around the well axis, ground top/bottom z, exact-boolean volume of the
ground plate with the well liner/collar/post parts, and the liner length hanging below the plate.
"""
import bpy, bmesh, sys, json, math, hashlib
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT = argv[0], argv[1]
ORG = Vector([float(v) for v in argv[2:5]])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
dg = bpy.context.evaluated_depsgraph_get()
T0 = Matrix.Translation(-ORG)
G = bpy.data.objects['C_market_ground_well_A']
me = G.evaluated_get(dg).to_mesh()
vs = [T0 @ G.matrix_world @ v.co for v in me.vertices]
near = [v for v in vs if math.hypot(v.x, v.y) < 1.5]
radii = sorted({round(math.hypot(v.x, v.y), 5) for v in near})
res = {'source': SRC, 'sha256': hashlib.sha256(open(SRC, 'rb').read()).hexdigest(),
       'groundNode': G.name, 'vertsWithin1p5m': len(near), 'distinctRadiiWithin1p5m': radii[:12],
       'holeMinRadius': radii[0] if radii else None,
       'groundTopZ': max(v.z for v in vs), 'groundBottomZ': min(v.z for v in vs)}
G.evaluated_get(dg).to_mesh_clear()


def vol(a, b):
    m = a.modifiers.new('x', 'BOOLEAN'); m.operation = 'INTERSECT'; m.solver = 'EXACT'; m.object = b
    d2 = bpy.context.evaluated_depsgraph_get()
    mm = a.evaluated_get(d2).to_mesh(); bm = bmesh.new(); bm.from_mesh(mm)
    v = bm.calc_volume(signed=False) if len(bm.faces) else 0.0
    bm.free(); a.evaluated_get(d2).to_mesh_clear(); a.modifiers.remove(m)
    return v

rows = []
for n in ('A_LOD0__short_liner', 'A_LOD0__circular_collar', 'A_LOD0__post_foot_1', 'A_LOD0__post_foot_-1',
          'A_LOD0__main_post_1', 'A_LOD0__main_post_-1'):
    o = bpy.data.objects.get(n)
    if o:
        bb = [T0 @ o.matrix_world @ Vector(c) for c in o.bound_box]
        rows.append({'part': n, 'zmin': round(min(c.z for c in bb), 6), 'zmax': round(max(c.z for c in bb), 6),
                     'intersectVolumeWithGround_m3': float('%.6g' % vol(G, o))})
res['wellPartsVsGround'] = rows
liner = [r for r in rows if r['part'].endswith('short_liner')]
if liner:
    res['linerBelowGroundBottom_m'] = round(res['groundBottomZ'] - liner[0]['zmin'], 6)
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False))
