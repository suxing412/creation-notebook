# LY-072 prep: per-side water / crossing coverage in the trial-fit chunk, checked against LY-002 E-R05
# ("东西南有水，北无"; 车驾从北门入). Read-only on inputs.
#
#   blender -b --factory-startup --python-exit-code 1 -P measure_side_water.py -- <biyong_C_relationship.glb> <out.json>
#
# Frame: Blender Z-up after glTF import. LY-005: Blender +Y = 图面北, +X = 图面东.
# Local = world - C, C = (2183.673095703125, -938.7760009765625, 0).
# Side bands (1 m cell centres, rays straight down from z=+5):
#   N: y in (70,78), x in (-78,78)   S: y in (-78,-70)   E: x in (70,78), y in (-78,78)   W: x in (-78,-70)
# Corners are counted in both adjoining bands (reported separately as corner cells).
import bpy, bmesh, sys, json, hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
GLB, OUT = argv[0], argv[1]
C = Vector((2183.673095703125, -938.7760009765625, 0.0))
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)


def bvh_of(pred):
    bm = bmesh.new(); names = []
    for o in bpy.context.scene.objects:
        if o.type != 'MESH' or not pred(o.name):
            continue
        t = bmesh.new(); t.from_mesh(o.data); t.transform(o.matrix_world)
        for v in t.verts:
            v.co -= C
        me = bpy.data.meshes.new('tmp'); t.to_mesh(me); t.free(); bm.from_mesh(me); names.append(o.name)
    bm.verts.ensure_lookup_table()
    return BVHTree.FromBMesh(bm), names


water, wn = bvh_of(lambda n: 'water' in n)
cross, cn = bvh_of(lambda n: 'A_crossing' in n)
island, inn = bvh_of(lambda n: 'A_island' in n)

bands = {'N': ((-78, 78), (70, 78)), 'S': ((-78, 78), (-78, -70)),
         'E': ((70, 78), (-78, 78)), 'W': ((-78, -70), (-78, 78))}
down = Vector((0, 0, -1))
res = {'tool': 'measure_side_water.py', 'glb': GLB, 'sha256': sha(GLB), 'C': list(C),
       'objects': {'water': wn, 'crossing': cn, 'island': inn}, 'bands': {}}
for k, ((x0, x1), (y0, y1)) in bands.items():
    cells = wet = crossed = isl = corner = 0
    wz = set()
    for xi in range(int(x0), int(x1)):
        for yi in range(int(y0), int(y1)):
            p = Vector((xi + 0.5, yi + 0.5, 5.0))
            cells += 1
            if abs(p.x) > 70 and abs(p.y) > 70:
                corner += 1
            h = water.ray_cast(p, down, 20)
            if h[0] is not None:
                wet += 1; wz.add(round(h[0].z, 3))
            if cross.ray_cast(p, down, 20)[0] is not None:
                crossed += 1
            if island.ray_cast(p, down, 20)[0] is not None:
                isl += 1
    res['bands'][k] = {'x': [x0, x1], 'y': [y0, y1], 'cells_1m': cells, 'cornerCells': corner,
                       'waterCells': wet, 'waterFraction': round(wet / cells, 4), 'waterTopZ': sorted(wz),
                       'crossingCells': crossed, 'islandCells': isl}
res['E-R05_check'] = {
    'rule': 'LY-002 E-R05: 东西南有水，北无 -> north band should carry no water and no water crossing (C basis)',
    'northWaterCells': res['bands']['N']['waterCells'],
    'northCrossingCells': res['bands']['N']['crossingCells'],
    'conflict': res['bands']['N']['waterCells'] > 0 or res['bands']['N']['crossingCells'] > 0}
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for k, v in res['bands'].items():
    print(k, v['waterCells'], '/', v['cells_1m'], 'crossing', v['crossingCells'])
print('E-R05 conflict', res['E-R05_check']['conflict'])
