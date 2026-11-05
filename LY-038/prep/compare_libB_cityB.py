"""LY-038 prep: tolerance comparison of library wuku-B-LOD0 vs city-visible chunk B (shifted by city origin).
Blender -b --factory-startup --python-exit-code 1 -P compare_libB_cityB.py -- <out.json>
Reports per mesh: vertex count, max nearest-vertex distance both directions, and the bbox of
vertices that differ by more than 1 mm (to locate e.g. a door leaf in a different pose)."""
import bpy, sys, json
from mathutils import Vector
from mathutils.kdtree import KDTree
OUT = sys.argv[sys.argv.index("--") + 1:][0]
LIB = "D:/GitHub/creation-notebook-lab/docs/library/models/m-luoyang-wuku/files/wuku-B-LOD0.glb"
WORK = "D:/GitHub/creation-notebook-workpacks/LY-038/prep/work/"
ORIGIN = Vector((2316.326904296875, 3500.0, 0.0))
bpy.ops.wm.read_factory_settings(use_empty=True)
def imp(p):
    b = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=p)
    return [o for o in bpy.data.objects if o not in b and o.type == 'MESH']
lib = imp(LIB)
city = imp(WORK + "chunks__wuku_C_with_support-01.glb") + imp(WORK + "chunks__wuku_C_with_support-02.glb")
def verts(o, shift=Vector()):
    return [o.matrix_world @ v.co - shift for v in o.data.vertices]
def kd(vs):
    t = KDTree(len(vs))
    for i, v in enumerate(vs): t.insert(v, i)
    t.balance(); return t
res = {}
for o in lib:
    key = o.name.split("-")[-1]  # static_earth / static_timber / static_tile
    c = [x for x in city if x.name.endswith("wuku-B-" + key + ".001")][0]
    a = verts(o); b = verts(c, ORIGIN)
    ka, kb = kd(a), kd(b)
    dab = [kb.find(v)[2] for v in a]; dba = [ka.find(v)[2] for v in b]
    far_a = [a[i] for i, d in enumerate(dab) if d > 0.001]
    far_b = [b[i] for i, d in enumerate(dba) if d > 0.001]
    bb = lambda P: None if not P else [[round(min(p[i] for p in P), 4) for i in range(3)], [round(max(p[i] for p in P), 4) for i in range(3)]]
    res[key] = {"lib": o.name, "city": c.name, "lib_verts": len(a), "city_verts": len(b),
                "max_lib_to_city_m": round(max(dab), 6), "max_city_to_lib_m": round(max(dba), 6),
                "lib_verts_gt_1mm": len(far_a), "city_verts_gt_1mm": len(far_b),
                "lib_far_bbox": bb(far_a), "city_far_bbox": bb(far_b)}
json.dump(res, open(OUT, "w"), indent=1)
print(json.dumps(res, indent=1))
