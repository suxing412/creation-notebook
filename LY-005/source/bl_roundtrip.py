# LY-005 Blender GLB round trip (import -> export -> re-import), headless.
# blender -b --factory-startup --python-exit-code 1 -P bl_roundtrip.py -- <case.json> <outdir>
# case.json: {"name", "glb", "excludeNodes": [], "cityMatrixGLTFColumnMajor": [16], "nativeBlenderRowMajor": [[4]x4] | null}
# Writes into outdir: <name>.import.npz-like JSON + exported GLBs (local and placed) + report JSON.
import bpy, sys, json, os, math
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index('--') + 1:]
case = json.load(open(argv[0], encoding='utf-8'))
out = argv[1]
os.makedirs(out, exist_ok=True)
name = case['name']

# glTF (x,y,z) -> Blender (x,-z,y).  C maps glTF-frame vectors into Blender-frame vectors.
C = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
Ci = C.inverted()


def gltf_cm_to_matrix(a):
    return Matrix([[a[c * 4 + r] for c in range(4)] for r in range(4)])


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def collect(objs, ex=()):
    """unique world positions (Blender frame) of mesh objects not under excluded names; plus object records"""
    recs, pts = [], []
    for o in objs:
        if o.type != 'MESH':
            continue
        anc, p = [], o
        while p:
            anc.append(p.name.split('.')[0] if False else p.name)
            p = p.parent
        if any(a in ex for a in anc):
            continue
        mw = o.matrix_world
        vs = [mw @ v.co for v in o.data.vertices]
        pts.extend(vs)
        recs.append({'name': o.name, 'parent': o.parent.name if o.parent else None, 'verts': len(o.data.vertices),
                     'polys': len(o.data.polygons), 'matrix_world_rowmajor': [list(r) for r in mw]})
    return recs, pts


def to_gltf(v):
    return [v.x, v.z, -v.y]


def bounds(pts):
    g = [to_gltf(p) for p in pts]
    return {'min': [min(p[i] for p in g) for i in range(3)], 'max': [max(p[i] for p in g) for i in range(3)]}


def import_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before]


report = {'name': name, 'blender': bpy.app.version_string, 'case': case}
reset()
us = bpy.context.scene.unit_settings
report['sceneUnits'] = {'system': us.system, 'scale_length': us.scale_length, 'length_unit': us.length_unit}
ex = set(case.get('excludeNodes') or [])

# ---- 1. import original
objs = import_glb(case['glb'])
recs, pts = collect(objs, ex)
report['import1'] = {'objects': recs, 'uniqueVerts': len(set((round(p.x, 5), round(p.y, 5), round(p.z, 5)) for p in pts)), 'boundsGLTFFrame': bounds(pts), 'boundsBlenderFrame': {
    'min': [min(p[i] for p in pts) for i in range(3)], 'max': [max(p[i] for p in pts) for i in range(3)]}}
json.dump(sorted(set((round(p.x, 5), round(p.z, 5), round(-p.y, 5)) for p in pts)), open(os.path.join(out, name + '.import1.gltfframe.json'), 'w'))

# remove excluded subtrees so that exports match what the city renders
for o in list(objs):
    anc, p = [], o
    while p:
        anc.append(p.name); p = p.parent
    if any(a in ex for a in anc):
        bpy.data.objects.remove(o, do_unlink=True)
objs = [o for o in bpy.data.objects]

# ---- 2. export local (no placement) and re-import
local_glb = os.path.join(out, name + '.local-roundtrip.glb')
bpy.ops.export_scene.gltf(filepath=local_glb, export_format='GLB', export_yup=True, export_apply=False, export_extras=False)

# ---- 3. apply city placement as a single parent empty (applied once)
Mg = gltf_cm_to_matrix(case['cityMatrixGLTFColumnMajor'])
Mb = C @ Mg @ Ci
report['placementBlenderFrameRowMajor'] = [list(r) for r in Mb]
if case.get('nativeBlenderRowMajor'):
    nb = Matrix(case['nativeBlenderRowMajor'])
    report['placementVsDeclaredNativeBlenderMaxAbsDiff'] = max(abs(Mb[r][c] - nb[r][c]) for r in range(4) for c in range(4))
emp = bpy.data.objects.new('CITY_NODE', None)
bpy.context.scene.collection.objects.link(emp)
emp.matrix_world = Mb
roots = [o for o in objs if o.parent is None]
for o in roots:
    mw = o.matrix_world.copy()
    o.parent = emp
    o.matrix_parent_inverse = Matrix.Identity(4)
    o.matrix_world = Mb @ mw
bpy.context.view_layer.update()
recs2, pts2 = collect([o for o in bpy.data.objects])
report['placedInBlender'] = {'boundsGLTFFrame': bounds(pts2), 'emptyScale': list(emp.matrix_world.to_scale()), 'emptyEulerXYZdeg': [math.degrees(a) for a in emp.matrix_world.to_euler('XYZ')]}
placed_glb = os.path.join(out, name + '.placed-roundtrip.glb')
bpy.ops.export_scene.gltf(filepath=placed_glb, export_format='GLB', export_yup=True, export_apply=False, export_extras=False)

# ---- 4. re-import both exports in clean scenes
for tag, path in (('reimportLocal', local_glb), ('reimportPlaced', placed_glb)):
    reset()
    o2 = import_glb(path)
    r3, p3 = collect(o2)
    report[tag] = {'objects': [{k: v for k, v in r.items() if k != 'matrix_world_rowmajor'} for r in r3], 'uniqueVerts': len(set((round(p.x, 5), round(p.y, 5), round(p.z, 5)) for p in p3)), 'boundsGLTFFrame': bounds(p3)}
    json.dump(sorted(set((round(p.x, 5), round(p.z, 5), round(-p.y, 5)) for p in p3)), open(os.path.join(out, name + '.' + tag + '.gltfframe.json'), 'w'))
    if tag == 'reimportPlaced':
        e = [o for o in o2 if o.name.startswith('CITY_NODE')]
        report[tag]['cityNodeEmptyMatrixBlenderRowMajor'] = [list(r) for r in e[0].matrix_world] if e else None
json.dump(report, open(os.path.join(out, name + '.blender-report.json'), 'w', encoding='utf-8'), indent=1)
print('LY005_DONE', name)
