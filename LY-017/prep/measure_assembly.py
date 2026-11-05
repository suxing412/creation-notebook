# LY-017 prep measurement (read-only on inputs). Blender 5.2, run:
#   D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P measure_assembly.py -- <lab_root> <extract_pkg_root> <out.json>
# Measures, in the hidden-trial world frame (Blender Z-up, metres):
#  A. gate P-v1 LOD0/1/2 local: side/central passage open intervals at several heights, central block,
#     clear height in side passages, earth x-extent (wings present or not).
#  B. ground attachment LOD0/1/2: top-surface coverage map, components, z range; ground vs gate-earth intrusion.
#  C. city context (in-repo GLBs walls A-05/A-06 + ground-atomic): wall caps vs gate earth ends, city ground
#     heights under/around the gate, the route corridor heights and step jumps.
#  D. hidden-trial .blend: objects, earth x-extent with terminal adapters (the two "wings").
# KNOWN LIMITS (found during prep, superseded by measure_loop.py / probe_city_ground.py):
#  - ground_top_points_inside_gate_solid uses ray parity on a mesh of touching/overlapping closed shells
#    (door head top z5.0 == deck bottom z5.0) -> false positives at y=-4.9; ground_vertices_inside_gate_solid=0 is the reliable figure.
#  - section D reads matrix_world before depsgraph update (identity), so its local_x_extent is wrong;
#    its world_bounds are in fact gate-local bounds (earth -16..16 = gate + two wings). See probe-result.json for matrix_basis == T.
#  - section C city ground: docs city has no ground at the gate (all None) - this is a real finding, re-checked in measure_loop.py.
import bpy, sys, json, math, hashlib
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
LAB = Path(argv[0]); PKG = Path(argv[1]); OUT = Path(argv[2])
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
CITY = LAB / 'docs/cities/luoyang'
CARD = LAB / 'docs/library/models/m-luoyang-pingcheng-gate/files'
GATE = {0: CARD / 'pingcheng-P-LOD0.glb',
        1: CITY / 'progress-assets/north13-gates/luoyang-pingcheng-gate-study-v1/models/pingcheng-P-LOD1.glb',
        2: CITY / 'progress-assets/north13-gates/luoyang-pingcheng-gate-study-v1/models/pingcheng-P-LOD2.glb'}
GROUND = {k: CARD / f'pingcheng-ground-LOD{k}.glb' for k in range(3)}
WALLS = {'A05': CITY / 'assets/city-wall/A/wall-05.glb', 'A06': CITY / 'assets/city-wall/A/wall-06.glb'}
CGROUND = {'stitched': CITY / 'assets/ground-atomic/network-ground-stitched.glb',
           'south': CITY / 'assets/ground-atomic/south.glb',
           'retained': CITY / 'assets/ground-atomic/retained.glb'}
placement = json.loads((PKG / 'city/placement.json').read_text())
O = Vector(placement['engineering_origin_from_existing_wall_caps']); ROT = placement['rotation_z_rad']
T = Matrix.Translation(O) @ Matrix.Rotation(ROT, 4, 'Z'); TI = T.inverted()
R = {'inputs': {}, 'placement_T': {'origin': list(O), 'rot_z': ROT}}

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def imp(path, tag, M=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    new = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    for o in new:
        o['tag'] = tag
        if M is not None:
            o.matrix_world = M @ o.matrix_world
    bpy.context.view_layer.update()
    R['inputs'][str(path.relative_to(LAB)) if LAB in path.parents else str(path)] = {'sha256': sha(path), 'bytes': path.stat().st_size}
    return new

def bvh(objs):
    dg = bpy.context.evaluated_depsgraph_get(); vs = []; fs = []
    for o in objs:
        e = o.evaluated_get(dg); me = e.to_mesh(); me.calc_loop_triangles(); off = len(vs)
        vs += [o.matrix_world @ v.co for v in me.vertices]; fs += [tuple(off + i for i in t.vertices) for t in me.loop_triangles]
        e.to_mesh_clear()
    return BVHTree.FromPolygons(vs, fs), vs

def wbounds(objs):
    lo = Vector((1e18,) * 3); hi = Vector((-1e18,) * 3)
    for o in objs:
        for v in o.data.vertices:
            w = o.matrix_world @ v.co; lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    return [round(c, 4) for c in lo], [round(c, 4) for c in hi]

def intervals(xs, flags):
    out = []; start = None
    for x, f in zip(xs, flags):
        if f and start is None: start = x
        if not f and start is not None: out.append([round(start, 3), round(prev, 3)]); start = None
        prev = x
    if start is not None: out.append([round(start, 3), round(prev, 3)])
    return out

def inside(tree, p, d=Vector((0.0123, 0.0071, 1.0)).normalized()):
    # ray parity
    n = 0; q = p.copy()
    for _ in range(64):
        h = tree.ray_cast(q, d)
        if h[0] is None: break
        n += 1; q = h[0] + d * 1e-4
    return n % 2 == 1

# ---------- A + B: local gate / ground ----------
local = {}
for lod in range(3):
    reset(); g = imp(GATE[lod], 'gate'); gr = imp(GROUND[lod], 'ground')
    names = {o.name: (len(o.data.vertices), len(o.data.polygons)) for o in g}
    earth = [o for o in g if 'earth' in o.name]; timber = [o for o in g if 'timber' in o.name]
    gt, _ = bvh(g); et, _ = bvh(earth); grt, grv = bvh(gr)
    xs = [round(-14.5 + 0.02 * i, 3) for i in range(int(29 / 0.02) + 1)]
    passes = {}
    for z in [0.1, 0.3, 1.0, 1.75, 2.5, 4.0, 4.5]:
        flags = []
        for x in xs:
            p = Vector((x, -7.0, z)); h = gt.ray_cast(p, Vector((0, 1, 0)), 14.0)
            flags.append(h[0] is None)
        passes[str(z)] = intervals(xs, flags)
    # clear height at side passage centres and central
    clear = {}
    for x in [-7.9, 0.0, 7.9]:
        rows = []
        for y in [-4.9, -4.5, -3.5, 0.0, 3.5, 4.9]:
            h = gt.ray_cast(Vector((x, y, 0.05)), Vector((0, 0, 1)), 20)
            rows.append([y, None if h[0] is None else round(h[0].z, 4)])
        clear[str(x)] = rows
    # ground top-surface sampling grid (local, Blender: x across, y through depth)
    step = 0.1; cov = []; top = {}
    gx = [round(-9.0 + step * i, 3) for i in range(int(18 / step) + 1)]
    gy = [round(-10.2 + step * i, 3) for i in range(int(20.4 / step) + 1)]
    for y in gy:
        row = ''
        for x in gx:
            h = grt.ray_cast(Vector((x, y, 5.0)), Vector((0, 0, -1)), 10)
            if h[0] is None: row += '.'
            else:
                row += '#'; top[(x, y)] = h[0].z
        cov.append(row)
    zs = list(top.values())
    # ground top inside gate solid (earth/timber) = intrusion of the walking surface into gate
    intr = []
    for (x, y), z in top.items():
        if abs(y) <= 5.2 and inside(gt, Vector((x, y, z - 0.005))):
            intr.append([x, y, round(z, 4)])
    # ground vertices inside gate solids
    gv_in = sum(1 for v in grv if inside(gt, v))
    # gate earth minimum z and earth x extent
    eb = wbounds(earth)
    local[f'LOD{lod}'] = {
        'gate_objects': names, 'ground_objects': {o.name: len(o.data.polygons) for o in gr},
        'gate_bounds': wbounds(g), 'earth_bounds': eb, 'ground_bounds': wbounds(gr),
        'open_x_intervals_ray_through_y_-7_to_+7': passes, 'first_hit_above_z0.05': clear,
        'ground_cov_step_m': step, 'ground_cov_samples': len(gx) * len(gy), 'ground_cov_hits': len(top),
        'ground_top_z_minmax': [round(min(zs), 4), round(max(zs), 4)] if zs else None,
        'ground_top_points_inside_gate_solid': len(intr), 'ground_top_inside_examples': intr[:12],
        'ground_vertices_inside_gate_solid': gv_in, 'ground_vertex_count': len(grv),
    }
    if lod == 1:
        local['LOD1']['ground_cov_map_rows_y_-10.2_to_10.2_x_-9_to_9'] = cov[::5]
R['local'] = local

# ---------- C: city context ----------
reset()
walls = {k: imp(p, k) for k, p in WALLS.items()}
cg = {k: imp(p, k) for k, p in CGROUND.items()}
g1 = imp(GATE[1], 'gate', T); gr1 = imp(GROUND[1], 'ground', T)
city = {'wall_bounds': {k: wbounds(v) for k, v in walls.items()}, 'cityground_bounds': {k: wbounds(v) for k, v in cg.items()}}
# wall end caps nearest the gate in gate-local frame
caps = {}
for k, objs in walls.items():
    pts = []
    for o in objs:
        for v in o.data.vertices:
            w = o.matrix_world @ v.co; l = TI @ w
            if abs(l.x) < 30 and abs(l.y) < 30: pts.append([round(l.x, 4), round(l.y, 4), round(l.z, 4)])
    caps[k] = pts
city['wall_vertices_within_30m_gate_local'] = caps
earth1 = [o for o in g1 if 'earth' in o.name]
city['gate_earth_local_x_extent'] = [round(min((TI @ (o.matrix_world @ v.co)).x for o in earth1 for v in o.data.vertices), 4),
                                    round(max((TI @ (o.matrix_world @ v.co)).x for o in earth1 for v in o.data.vertices), 4)]
for k in caps:
    if caps[k]:
        xs_ = [p[0] for p in caps[k]]
        city[f'gap_gate_earth_to_{k}_cap_m'] = round(min(abs(x) for x in xs_) - 12.8, 4)
# city ground heights in gate-local window
groundtrees = {k: bvh(v)[0] for k, v in cg.items()}
gtt, _ = bvh(g1); grt1, _ = bvh(gr1); wt, _ = bvh([o for v in walls.values() for o in v])
def topz(tree, x, y):
    w = T @ Vector((x, y, 50.0)); h = tree.ray_cast(w, Vector((0, 0, -1)), 100)
    return None if h[0] is None else round(h[0].z - O.z, 4)  # relative to gate origin z (0.17)
win = {}
for k, t in groundtrees.items():
    rows = []
    for y in [-30, -20, -15, -10, -7.5, -5, -2.5, 0, 2.5, 5, 7.5, 10, 15, 20, 30]:
        rows.append([y, [topz(t, x, y) for x in [-20, -14, -10, -7.9, -5, -3, 0, 3, 5, 7.9, 10, 14, 20]]])
    win[k] = rows
city['cityground_top_rel_gate_z0_rows_y_cols_x[-20,-14,-10,-7.9,-5,-3,0,3,5,7.9,10,14,20]'] = win
# route profile: south outside (y=-30) -> west side passage (x=-7.9) -> north inside (y=+30) -> across -> east passage -> south
def support(x, y):
    a = topz(grt1, x, y); b = max([z for z in (topz(t, x, y) for t in groundtrees.values()) if z is not None], default=None)
    return a, b
prof = []
for x in [-7.9, 7.9]:
    for i in range(0, 121):
        y = -30 + 0.5 * i; a, b = support(x, y)
        prof.append([x, y, a, b])
city['route_profile_x_y_attachTop_cityTop_rel'] = prof
# step jumps along the route on the supporting surface max(attach, city)
jumps = []
for x in [-7.9, 7.9]:
    seq = [(p[1], max([z for z in p[2:] if z is not None], default=None)) for p in prof if p[0] == x]
    for (y0, z0), (y1, z1) in zip(seq, seq[1:]):
        if z0 is None or z1 is None: jumps.append([x, y0, y1, 'NO_SUPPORT']); continue
        if abs(z1 - z0) > 0.05: jumps.append([x, y0, y1, round(z1 - z0, 4)])
city['route_jumps_gt_0.05m'] = jumps
nosup = [[p[0], p[1]] for p in prof if p[2] is None and p[3] is None]
city['route_points_no_support'] = len(nosup); city['route_points_total'] = len(prof)
R['city'] = city

# ---------- D: hidden-trial blend ----------
reset()
bl = PKG / 'city/pingcheng-P-mid-hidden-trial.blend'
with bpy.data.libraries.load(str(bl), link=False) as (src, dst):
    dst.objects = list(src.objects)
for o in dst.objects:
    if o is not None: bpy.context.scene.collection.objects.link(o)
bpy.context.view_layer.update()
hid = {}
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    lx = [(TI @ (o.matrix_world @ v.co)).x for v in o.data.vertices]
    hid[o.name] = {'verts': len(o.data.vertices), 'faces': len(o.data.polygons), 'local_x_extent': [round(min(lx), 4), round(max(lx), 4)],
                   'world_bounds': wbounds([o]), 'hide_render': o.hide_render, 'matrix_matches_T': max(abs(a - b) for ra, rb in zip(o.matrix_world, T) for a, b in zip(ra, rb)) < 1e-4}
R['hidden_trial'] = {'file': str(bl.relative_to(PKG)), 'sha256': sha(bl), 'objects': hid}
OUT.write_text(json.dumps(R, indent=1, ensure_ascii=False)); print('MEASURE_OK', OUT)
