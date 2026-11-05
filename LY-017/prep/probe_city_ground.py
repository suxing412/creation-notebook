# LY-017 prep: probe in-repo city ground GLBs around the Pingcheng gate origin, and hidden-trial blend matrices.
#   blender -b --factory-startup --python-exit-code 1 -P probe_city_ground.py -- <lab_root> <pkg_root> <out.json>
import bpy, sys, json
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]; LAB = Path(a[0]); PKG = Path(a[1]); OUT = Path(a[2])
pl = json.loads((PKG / 'city/placement.json').read_text()); O = Vector(pl['engineering_origin_from_existing_wall_caps'])
T = Matrix.Translation(O) @ Matrix.Rotation(pl['rotation_z_rad'], 4, 'Z')
res = {}
bpy.ops.wm.read_factory_settings(use_empty=True)
G = LAB / 'docs/cities/luoyang/assets/ground-atomic'
for f in sorted(G.glob('*.glb')):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=str(f))
    new = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    dg = bpy.context.evaluated_depsgraph_get(); vs = []; fs = []; per = {}
    for o in new:
        me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); off = len(vs)
        vs += [o.matrix_world @ v.co for v in me.vertices]; fs += [tuple(off + i for i in t.vertices) for t in me.loop_triangles]
        per[o.name] = len(me.loop_triangles)
    t = BVHTree.FromPolygons(vs, fs)
    # nearest ground vertex to gate origin (xy)
    near = sorted(vs, key=lambda v: (v.x - O.x) ** 2 + (v.y - O.y) ** 2)[:1]
    grid = {}
    for dy in range(-200, 201, 10):
        row = ''
        for dx in range(-200, 201, 10):
            p = Vector((O.x + dx, O.y + dy, 100)); h = t.ray_cast(p, Vector((0, 0, -1)), 300)
            row += '.' if h[0] is None else '#'
        grid[dy] = row
    res[f.name] = {'objects': per, 'nearest_vertex_to_gate_origin': [list(map(lambda c: round(c, 3), near[0]))] if near else None,
                   'nearest_xy_dist_m': round(((near[0].x - O.x) ** 2 + (near[0].y - O.y) ** 2) ** .5, 3) if near else None,
                   'grid_10m_rows_dy_-200..200_cols_dx_-200..200': grid}
    for o in new: bpy.data.objects.remove(o)
# hidden trial matrices
bpy.ops.wm.read_factory_settings(use_empty=True)
bl = PKG / 'city/pingcheng-P-mid-hidden-trial.blend'
with bpy.data.libraries.load(str(bl), link=False) as (src, dst):
    dst.objects = list(src.objects)
ht = {}
for o in dst.objects:
    if o is None: continue
    bpy.context.scene.collection.objects.link(o)
bpy.context.view_layer.update()
for o in dst.objects:
    ht[o.name] = {'matrix_world': [list(map(lambda c: round(c, 5), r)) for r in o.matrix_world],
                  'matrix_basis': [list(map(lambda c: round(c, 5), r)) for r in o.matrix_basis],
                  'parent': o.parent.name if o.parent else None, 'props': {k: str(o[k]) for k in o.keys()}}
res['hidden_trial_matrices'] = ht
res['T_expected'] = [list(map(lambda c: round(c, 5), r)) for r in T]
OUT.write_text(json.dumps(res, indent=1)); print('PROBE_OK')
