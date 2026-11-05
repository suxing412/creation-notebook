# LY-017 prep: sample support surfaces of the city-visible handoff chunks (mother 1e8c4d) in the Pingcheng gate-local frame.
#   blender -b --factory-startup --python-exit-code 1 -P probe_visible_chunks.py -- <chunks_dir> <pkg_root> <out.json>
# Prints per-chunk coverage maps (0.5 m grid, gate-local x[-24,24], y[-40,40]) and top z (relative to gate origin z 0.17).
import bpy, sys, json, hashlib
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]; CH = Path(a[0]); PKG = Path(a[1]); OUT = Path(a[2])
pl = json.loads((PKG / 'city/placement.json').read_text()); O = Vector(pl['engineering_origin_from_existing_wall_caps'])
T = Matrix.Translation(O) @ Matrix.Rotation(pl['rotation_z_rad'], 4, 'Z'); TI = T.inverted()
res = {}
names = ['C_gate_local_ground', 'C_ground_network__C_stitch_primary', 'C_ground_network__conditional_link_A', 'city_gate_pingcheng-P', 'city_wall_C_profiles']
trees = {}
bpy.ops.wm.read_factory_settings(use_empty=True)
for n in names:
    f = CH / (n + '.glb'); before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=str(f))
    new = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']; bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); vs = []; fs = []; objs = {}
    for o in new:
        me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); off = len(vs)
        vs += [o.matrix_world @ v.co for v in me.vertices]; fs += [tuple(off + i for i in t.vertices) for t in me.loop_triangles]
        objs[o.name] = len(me.loop_triangles)
    trees[n] = BVHTree.FromPolygons(vs, fs)
    loc = [TI @ v for v in vs if abs((TI @ v).x) < 40 and abs((TI @ v).y) < 60]
    res[n] = {'sha256': hashlib.sha256(f.read_bytes()).hexdigest(), 'objects': objs,
              'local_vertices_within_40x60': len(loc),
              'local_vertex_sample': [[round(c, 3) for c in v] for v in sorted(loc, key=lambda v: (round(v.y, 1), v.x))[:60]] if n != 'city_gate_pingcheng-P' else None}
def top(n, x, y):
    w = T @ Vector((x, y, 30)); h = trees[n].ray_cast(w, Vector((0, 0, -1)), 60)
    return None if h[0] is None else h[0].z - O.z
xs = [x * 0.5 for x in range(-48, 49)]; ys = [y * 0.5 for y in range(-80, 81)]
for n in ['C_gate_local_ground', 'C_ground_network__C_stitch_primary', 'C_ground_network__conditional_link_A']:
    rows = []; zs = []
    for y in ys[::2]:
        r = ''
        for x in xs:
            z = top(n, x, y)
            if z is None: r += '.'
            else: zs.append(z); r += '#' if z > 0.03 else ('-' if z > -0.03 else 'v')
        rows.append(f'{y:6.1f} ' + r)
    res[n]['map_1m_rows_y_cols_x_-24..24_step0.5'] = rows
    res[n]['top_rel_minmax'] = [round(min(zs), 4), round(max(zs), 4)] if zs else None
# combined support along the two side-passage centrelines and a closing loop
def sup(x, y):
    v = [z for z in (top(n, x, y) for n in ['C_gate_local_ground', 'C_ground_network__C_stitch_primary', 'C_ground_network__conditional_link_A']) if z is not None]
    return max(v) if v else None
prof = {}
for x in [-7.9, 0.0, 7.9]:
    prof[str(x)] = [[y, None if sup(x, y) is None else round(sup(x, y), 4)] for y in [i * 0.25 for i in range(-160, 161)]]
res['support_profiles_rel'] = prof
OUT.write_text(json.dumps(res, indent=1)); print('VIS_OK')
