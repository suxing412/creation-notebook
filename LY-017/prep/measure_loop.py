# LY-017 prep: joint gate + wings + old oblique road + side-gate ground, measured in the gate-local frame.
#   blender -b --factory-startup --python-exit-code 1 -P measure_loop.py -- <chunks_dir> <pkg_root> <lab_root> <out.json>
# Inputs (read-only):
#   city-visible handoff chunks (mother 1e8c4d): city_gate_pingcheng-P.glb (gate+two wings), C_stitch_primary (old road),
#   C_gate_local_ground (pingcheng_ground_trial_v1 = LOD0 attachment), conditional_link_A.
#   docs/library pingcheng-ground-LOD0/1/2.glb (public attachments), docs city wall-05/06.glb.
# Outputs: road edges at the gate, intrusion areas/volumes (road slab vs piers/jambs/closed leaves),
#   patch-vs-road overlap/gap, grid BFS loop test with a 0.3 m body half-width and 1.9 m head clearance
#   (positive and negative cases). Discrete grid, not continuous body motion.
import bpy, sys, json, hashlib, math
from pathlib import Path
from collections import deque
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]; CH = Path(a[0]); PKG = Path(a[1]); LAB = Path(a[2]); OUT = Path(a[3])
pl = json.loads((PKG / 'city/placement.json').read_text()); O = Vector(pl['engineering_origin_from_existing_wall_caps'])
T = Matrix.Translation(O) @ Matrix.Rotation(pl['rotation_z_rad'], 4, 'Z'); TI = T.inverted()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
res = {'inputs': {}}
bpy.ops.wm.read_factory_settings(use_empty=True)
def load(path, M=None, only=None):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=str(path))
    new = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    if M is not None:
        for o in new: o.matrix_world = M @ o.matrix_world
    bpy.context.view_layer.update(); res['inputs'][path.name] = {'sha256': sha(path), 'bytes': path.stat().st_size}
    if only: new = [o for o in new if only in o.name]
    return new
def tree(objs, local=True):
    dg = bpy.context.evaluated_depsgraph_get(); vs = []; fs = []
    for o in objs:
        me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); off = len(vs)
        vs += [(TI @ (o.matrix_world @ v.co)) if local else (o.matrix_world @ v.co) for v in me.vertices]
        fs += [tuple(off + i for i in t.vertices) for t in me.loop_triangles]
    return BVHTree.FromPolygons(vs, fs), vs
gate = load(CH / 'city_gate_pingcheng-P.glb'); road = load(CH / 'C_ground_network__C_stitch_primary.glb')
att = load(CH / 'C_gate_local_ground.glb', only='pingcheng'); cond = load(CH / 'C_ground_network__conditional_link_A.glb')
pub = {k: load(LAB / f'docs/library/models/m-luoyang-pingcheng-gate/files/pingcheng-ground-LOD{k}.glb', T) for k in range(3)}
walls = load(LAB / 'docs/cities/luoyang/assets/city-wall/A/wall-05.glb') + load(LAB / 'docs/cities/luoyang/assets/city-wall/A/wall-06.glb')
docs_stitched = load(LAB / 'docs/cities/luoyang/assets/ground-atomic/network-ground-stitched.glb')
G, gv = tree(gate); Rd, rv = tree(road); A, av = tree(att); C, cv = tree(cond); W, wv = tree(walls); DS, dsv = tree(docs_stitched)
PUB = {k: tree(v)[0] for k, v in pub.items()}
earth = [o for o in gate if 'earth' in o.name]; E, ev = tree(earth)
res['gate_chunk_earth_local_x'] = [round(min(v.x for v in ev), 4), round(max(v.x for v in ev), 4)]
res['gate_chunk_matrix_vs_T_maxdiff'] = max(abs(x - y) for o in gate for r1, r2 in zip(TI @ o.matrix_world, Matrix.Identity(4)) for x, y in zip(r1, r2))
# wing outer face vs docs wall caps: distance from wing vertices with |x|>15.9 to nearest docs wall vertex
wing = [v for v in ev if abs(v.x) > 15.9]
res['wing_outer_vertices'] = len(wing)
res['wing_to_docs_wall_vertex_maxdist_m'] = round(max(min((v - w).length for w in wv if abs(w.x) < 20 and abs(w.y) < 10) for v in wing), 6) if wing else None
def top(t, x, y, z0=3.0):
    h = t.ray_cast(Vector((x, y, z0)), Vector((0, 0, -1)), 6.0)
    return None if h[0] is None else h[0].z
# old road edges near the gate
edges = []
for y in [-30, -20, -10, -5, 0, 5, 10, 13]:
    xs = [i * 0.01 for i in range(-600, 601)]; hit = [x for x in xs if top(Rd, x, y) is not None]
    edges.append([y, round(min(hit), 3), round(max(hit), 3)] if hit else [y, None, None])
res['old_road_local_x_edges_by_y'] = edges
res['docs_city_stitched_has_ground_at_gate'] = any(top(DS, x * 0.5, y * 0.5) is not None for x in range(-20, 21) for y in range(-40, 41))
# intrusion of old-road slab (top 0.04, bottom -0.01) into gate solids above gate base z=0
step = 0.02
def area(mask_fn, t, region):
    (x0, x1), (y0, y1) = region; n = 0
    nx = int(round((x1 - x0) / step)); ny = int(round((y1 - y0) / step))
    for i in range(nx):
        for j in range(ny):
            x = x0 + (i + .5) * step; y = y0 + (j + .5) * step
            if top(t, x, y) is not None and mask_fn(x, y): n += 1
    return round(n * step * step, 4)
solids = {'pier_W(-5.8..-3)': ((-5.8, -3.0), (-5.0, 5.0)), 'pier_E(3..5.8)': ((3.0, 5.8), (-5.0, 5.0)),
          'central_jamb_W': ((-3.0, -2.8), (-4.96, -4.64)), 'central_jamb_E': ((2.8, 3.0), (-4.96, -4.64)),
          'closed_leaves(-3..3)': ((-3.0, 3.0), (-4.64, -4.46))}
intr = {}
for k, reg in solids.items():
    ar = area(lambda x, y: True, Rd, reg); intr[k] = {'road_area_m2': ar, 'embed_depth_m': 0.04, 'volume_m3': round(ar * 0.04, 5)}
res['old_road_slab_inside_gate_solids'] = intr
# attachment (mother LOD0 instance) vs old road: coplanar overlap and gaps along patch rows
ov = []; gaps = []
for y in [-9.9, -9.0, -8.0, -7.2, 7.2, 8.0, 9.0, 9.9]:
    xs = [i * 0.01 for i in range(-900, 901)]
    a_ = [x for x in xs if top(A, x, y) is not None]; r_ = [x for x in xs if top(Rd, x, y) is not None]
    both = [x for x in xs if top(A, x, y) is not None and top(Rd, x, y) is not None]
    aW = [x for x in a_ if x < 0]; aE = [x for x in a_ if x > 0]
    row = {'y': y, 'patch_W_inner_x': round(max(aW), 3) if aW else None, 'patch_E_inner_x': round(min(aE), 3) if aE else None,
           'road_x': [round(min(r_), 3), round(max(r_), 3)] if r_ else None, 'overlap_width_m': round(len(both) * 0.01, 3)}
    if aW and r_: row['gap_W_m'] = round(min(r_) - max(aW), 3)
    if aE and r_: row['gap_E_m'] = round(min(aE) - max(r_), 3)
    ov.append(row)
res['patch_vs_old_road_rows'] = ov
# vertical overlap of attachment slab (-0.16..0.04) and road slab (-0.01..0.04) where both exist
res['attachment_vs_old_road_overlap_area_m2'] = area(lambda x, y: top(A, x, y) is not None, Rd, ((-9, 9), (-10.2, 10.2)))
# public attachment LOD0/1/2 vs mother instance coverage equality
cmp = {}
for k, t in PUB.items():
    d = 0; n = 0; zmax = 0
    for i in range(-90, 91, 2):
        for j in range(-102, 103, 2):
            x = i * 0.1; y = j * 0.1; p = top(t, x, y); m = top(A, x, y)
            n += 1
            if (p is None) != (m is None): d += 1
            elif p is not None: zmax = max(zmax, abs(p - m))
    cmp[f'LOD{k}'] = {'samples': n, 'coverage_mismatch': d, 'max_top_dz_m': round(zmax, 5)}
res['public_attachment_vs_mother_instance'] = cmp
# ---------- grid BFS loop test ----------
GX = (-12.0, 12.0); GY = (-30.0, 22.0); s = 0.1
nx = int((GX[1] - GX[0]) / s); ny = int((GY[1] - GY[0]) / s)
def build(use_road=True, use_att=True, use_cond=True, block_leaf=True, att_tree=None):
    att_t = att_tree or A; free = [[False] * ny for _ in range(nx)]
    for i in range(nx):
        x = GX[0] + (i + .5) * s
        for j in range(ny):
            y = GY[0] + (j + .5) * s; zs = []
            if use_road: zs.append(top(Rd, x, y))
            if use_att: zs.append(top(att_t, x, y))
            if use_cond: zs.append(top(C, x, y))
            zs = [z for z in zs if z is not None and -0.05 <= z <= 0.1]
            if not zs: continue
            z = max(zs); z0 = min(z, 0.0) - 0.1; h = G.ray_cast(Vector((x, y, z0)), Vector((0, 0, 1)), (z + 1.9) - z0)  # start below gate base so embedded leaves/piers count
            if h[0] is not None:
                # optional: treat closed central leaves as removed (negative test) -> ignore hits in leaf slab
                if not block_leaf and -3.0 <= x <= 3.0 and -4.70 <= y <= -4.40 and h[0].z < 0.05:
                    pass  # leaf removed (negative-control sanity case): the only hit above this cell is the leaf itself
                else: continue
            free[i][j] = True
    return free
def erode(free, r=0.3):
    k = int(math.ceil(r / s)); out = [[False] * ny for _ in range(nx)]
    for i in range(nx):
        for j in range(ny):
            if not free[i][j]: continue
            ok = True
            for di in range(-k, k + 1):
                ii = i + di
                if ii < 0 or ii >= nx or not free[ii][j]: ok = False; break
            if ok:
                for dj in range(-k, k + 1):
                    jj = j + dj
                    if jj < 0 or jj >= ny or not free[i][jj]: ok = False; break
            out[i][j] = ok
    return out
def cell(x, y): return int((x - GX[0]) / s), int((y - GY[0]) / s)
def reach(free, start, goal, forbid=None):
    si, sj = cell(*start); gi, gj = cell(*goal)
    if not free[si][sj]: return 'START_UNSUPPORTED'
    seen = {(si, sj)}; q = deque([(si, sj)])
    while q:
        i, j = q.popleft()
        if (i, j) == (gi, gj): return True
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ii, jj = i + di, j + dj
            if 0 <= ii < nx and 0 <= jj < ny and free[ii][jj] and (ii, jj) not in seen:
                x = GX[0] + (ii + .5) * s; y = GY[0] + (jj + .5) * s
                if forbid and forbid(x, y): continue
                seen.add((ii, jj)); q.append((ii, jj))
    return False
OUTSIDE = (0.0, -25.0); INSIDE = (-0.4, 11.0); FAR_IN = (-0.6, 21.8)
west_only = lambda x, y: (-5 <= y <= 5) and x > -5.8
east_only = lambda x, y: (-5 <= y <= 5) and x < 5.8
centre_only = lambda x, y: (-5 <= y <= 5) and (x < -3 or x > 3)
cases = {}
base = erode(build())
cases['P1_out_to_in_via_west'] = reach(base, OUTSIDE, INSIDE, west_only)
cases['P2_in_to_out_via_east'] = reach(base, INSIDE, OUTSIDE, east_only)
cases['P3_loop_closed(P1 and P2)'] = cases['P1_out_to_in_via_west'] is True and cases['P2_in_to_out_via_east'] is True
cases['N1_centre_only_must_fail'] = reach(base, OUTSIDE, INSIDE, centre_only)
cases['N2_no_old_road_must_fail'] = reach(erode(build(use_road=False)), (-7.9, -9.5), (7.9, -9.5))
cases['N3_attachment_only_no_road_out_to_in_west'] = reach(erode(build(use_road=False)), (-7.9, -9.5), (-7.9, 9.5), west_only)
cases['N4_leaf_removed_centre_passes(sanity)'] = reach(erode(build(block_leaf=False)), OUTSIDE, INSIDE, centre_only)
cases['R1_inside_to_conditional_link_A'] = reach(base, INSIDE, FAR_IN)
for k, t in PUB.items():
    cases[f'P3_loop_with_public_LOD{k}_attachment'] = (reach(erode(build(att_tree=t)), OUTSIDE, INSIDE, west_only) is True and
                                                    reach(erode(build(att_tree=t)), INSIDE, OUTSIDE, east_only) is True)
cases['_expect'] = {'P1': True, 'P2': True, 'P3': True, 'N1': False, 'N2': False, 'N4': True}
cases['_verdict_all_as_expected'] = (cases['P1_out_to_in_via_west'] is True and cases['P2_in_to_out_via_east'] is True and
    cases['N1_centre_only_must_fail'] is False and cases['N2_no_old_road_must_fail'] is False and cases['N4_leaf_removed_centre_passes(sanity)'] is True)
res['grid_loop_cases'] = cases
res['grid_params'] = {'cell_m': s, 'body_half_width_m': 0.3, 'head_clearance_m': 1.9, 'support_z_window_rel_gate_base': [-0.05, 0.1],
                      'region_local': [GX, GY], 'outside': OUTSIDE, 'inside': INSIDE, 'far_inside': FAR_IN,
                      'note': '4-connected discrete grid with square erosion; not continuous body motion, not vehicles, not structural'}
fr = sum(map(sum, base)); res['grid_free_cells_eroded'] = fr
OUT.write_text(json.dumps(res, indent=1)); print('LOOP_OK')
