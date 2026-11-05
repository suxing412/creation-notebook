# LY-012 prep: read-only measurement of Kaiyang K-v1 door leaves / jambs / heads from the actual GLB exports.
# Usage:
#   blender -b --factory-startup --python-exit-code 1 -P measure_k_v1_doors.py -- <gate.glb> <ground.glb|-> <out.json> <source-object-ranges.json> <LOD0|LOD1|LOD2>
# Nothing is written except <out.json>. Inputs are opened read-only by the glTF importer.
# Coordinates: Blender Z-up after glTF import (the K-v1 generator itself was authored Z-up, front face y=-5).
# Hinge axis is an INFERENCE (C engineering): vertical line through leaf thickness centre at the leaf's
# front (min-y) end. It is checked, not assumed correct: see "hinge_inference".
import bpy, bmesh, sys, json, math, hashlib
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
gate_path, ground_path, out_path = argv[0], argv[1], argv[2]
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=gate_path)
gate_objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
nodes = [{'name': o.name, 'mesh': o.data.name, 'triangles': sum(len(p.vertices) - 2 for p in o.data.polygons),
          'materials': [m.name for m in o.data.materials if m]} for o in gate_objs]

def world_bm(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world); bmesh.ops.triangulate(bm, faces=bm.faces[:]); return bm

def islands(bm):
    bm.faces.ensure_lookup_table(); seen = set(); out = []
    for f in bm.faces:
        if f.index in seen: continue
        stack = [f]; comp = []; seen.add(f.index)
        while stack:
            g = stack.pop(); comp.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen: seen.add(h.index); stack.append(h)
        vs = {v for g in comp for v in g.verts}
        co = [v.co.copy() for v in vs]
        mn = Vector([min(c[i] for c in co) for i in range(3)]); mx = Vector([max(c[i] for c in co) for i in range(3)])
        tris = [[v.co.copy() for v in g.verts] for g in comp]
        out.append({'min': mn, 'max': mx, 'dim': mx - mn, 'tris': tris, 'verts': co})
    return out

def bvh_from_tris(tris):
    verts = []; polys = []
    for t in tris:
        b = len(verts); verts.extend(t); polys.append(tuple(range(b, b + len(t))))
    return BVHTree.FromPolygons(verts, polys, all_triangles=True, epsilon=0.0)

role_of = {}
for o in gate_objs:
    mat = (o.data.materials[0].name if o.data.materials else '').lower()
    role_of[o.name] = 'timber' if 'timber' in mat else 'earth' if 'earth' in mat else 'tile' if 'tile' in mat else 'other'
timber = [o for o in gate_objs if role_of[o.name] == 'timber']
earth = [o for o in gate_objs if role_of[o.name] == 'earth']
assert timber and earth, 'expected LY_P01 timber/earth meshes'
ranges_path = argv[3]; lod_key = argv[4]  # e.g. qa/source-object-ranges.json from the K-v1 source ZIP, 'LOD0'
ranges = json.load(open(ranges_path))
def tri_list(o):
    me = o.data; M = o.matrix_world
    return [[M @ me.vertices[i].co for i in p.vertices] for p in me.polygons]
def part(tris, name, rng):
    tt = tris[rng[0]:rng[1]]; co = [v for t in tt for v in t]
    mn = Vector([min(c[i] for c in co) for i in range(3)]); mx = Vector([max(c[i] for c in co) for i in range(3)])
    return {'name': name, 'min': mn, 'max': mx, 'dim': mx - mn, 'tris': tt}
T_tris = tri_list(timber[0]); E_tris = []
for o in earth: E_tris += tri_list(o)
earth_tris = E_tris
tparts = [part(T_tris, x['source_object'], x['triangle_range']) for x in ranges[lod_key + '_timber']]
eparts = [part(E_tris, x['source_object'], x['triangle_range']) for x in ranges[lod_key + '_earth']]
assert ranges[lod_key + '_timber'][-1]['triangle_range'][1] == len(T_tris), 'timber triangle count differs from range table'
assert ranges[lod_key + '_earth'][-1]['triangle_range'][1] == len(E_tris), 'earth triangle count differs from range table'
leaves = [q for q in tparts if q['name'].startswith('C_open_leaf_')]
jambs = [q for q in tparts if q['name'].startswith('C_jamb_')]
heads = [q for q in tparts if q['name'].startswith('C_door_head_')]
battens = [q for q in tparts if q['name'].startswith('C_leaf_batten_')]
piers = sorted([q for q in eparts if q['name'].startswith('C_earth_pier_')], key=lambda i: i['min'].x)
openings = [(piers[k]['max'].x, piers[k + 1]['min'].x) for k in range(len(piers) - 1)]
# validation: every leaf/jamb/head range must be a closed 12-triangle box of the generator's dimensions
def is_box(q, dims, tol=1e-4): return len(q['tris']) == 12 and all(abs(q['dim'][i] - dims[i]) < tol for i in range(3))
range_validation = {
  'leaves_box_ok': all(is_box(q, (0.14, q['dim'].y, 4.3)) and q['dim'].y > 1 for q in leaves),
  'jambs_box_ok': all(is_box(q, (0.2, 0.32, 5.0)) for q in jambs),
  'heads_box_ok': all(is_box(q, (q['dim'].x, 0.32, 0.3)) for q in heads),
  'piers_box_ok': all(is_box(q, (2.8, 10.0, 5.0)) for q in piers)}
r = lambda v, n=4: round(float(v), n)
vec = lambda v: [r(x) for x in v]

ground = None; ground_bvh = None; ground_info = None
if ground_path != '-':
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=ground_path)
    gobjs = [o for o in bpy.context.scene.objects if o not in before and o.type == 'MESH']
    gtris = []
    for o in gobjs:
        b = world_bm(o); gtris += [[v.co.copy() for v in f.verts] for f in b.faces]
    ground_bvh = bvh_from_tris(gtris)
    gis = []
    for o in gobjs: gis += islands(world_bm(o))
    gis.sort(key=lambda i: i['min'].x); strips = []
    for i in gis:
        if strips and i['min'].x <= strips[-1]['max'][0] + 0.3:
            st = strips[-1]; st['min'] = [min(st['min'][k], i['min'][k]) for k in range(3)]; st['max'] = [max(st['max'][k], i['max'][k]) for k in range(3)]
        else: strips.append({'min': list(i['min']), 'max': list(i['max'])})
    ground_info = {'sha256': sha(ground_path), 'meshes': [o.name for o in gobjs], 'triangles': len(gtris), 'islands': len(gis),
                   'strips': [{'min': vec(st['min']), 'max': vec(st['max'])} for st in strips]}

def ground_top(x, y):
    if not ground_bvh: return None
    hit = ground_bvh.ray_cast(Vector((x, y, 3.0)), Vector((0, 0, -1)), 10)
    return None if hit[0] is None else hit[0].z

earth_bvh = bvh_from_tris(earth_tris)
result = {'gate_glb': gate_path, 'gate_sha256': sha(gate_path), 'ground': ground_info, 'nodes': nodes,
          'leaf_independent_node': any('leaf' in n['name'].lower() for n in nodes),
          'range_validation': range_validation, 'counts': {'timber_parts': len(tparts), 'leaves': len(leaves), 'jambs': len(jambs), 'heads': len(heads),
                     'battens': len(battens), 'piers': len(piers)},
          'openings_x': [[r(a), r(b), r(b - a)] for a, b in openings], 'passages': []}

ANGLES = [0, 5, 15, 30, 45, 60, 75, 85, 90, 95, 100]  # degrees of closing; 0 = exported open state, 90 = closed; >90 = overshoot negative case

def leaf_group(leaf):
    bs = [b for b in battens if leaf['min'].y - 0.01 <= b['min'].y and b['max'].y <= leaf['max'].y + 0.01
          and abs((b['min'].x + b['max'].x) / 2 - (leaf['min'].x + leaf['max'].x) / 2) < 0.15]
    return bs

def rot_tris(tris, hinge, ang_deg):
    M = Matrix.Translation(hinge) @ Matrix.Rotation(math.radians(ang_deg), 4, 'Z') @ Matrix.Translation(-hinge)
    return [[M @ v for v in t] for t in tris]

def surface_samples(tris, step=0.05):
    pts = []
    for t in tris:
        a, b, c = t[0], t[1], t[2]
        n1 = max(1, int((b - a).length / step)); n2 = max(1, int((c - a).length / step))
        for i in range(n1 + 1):
            for j in range(n2 + 1):
                u, v = i / n1, j / n2
                if u + v <= 1: pts.append(a + (b - a) * u + (c - a) * v)
    return pts

for k, (l, rr) in enumerate(openings):
    w = rr - l; cx = (l + rr) / 2
    pl = [lf for lf in leaves if l - 0.01 <= lf['min'].x and lf['max'].x <= rr + 0.01]
    pj = [j for j in jambs if l - 0.01 <= j['min'].x and j['max'].x <= rr + 0.01]
    ph = [h for h in heads if l - 0.01 <= h['min'].x and h['max'].x <= rr + 0.01]
    pb = [b for b in battens if l - 0.01 <= b['min'].x and b['max'].x <= rr + 0.01]
    P = {'index': k, 'x_range': [r(l), r(rr)], 'width_m': r(w), 'leaves': [], 'jambs': [], 'heads': []}
    for j in pj: P['jambs'].append({'min': vec(j['min']), 'max': vec(j['max'])})
    for h in ph: P['heads'].append({'min': vec(h['min']), 'max': vec(h['max']), 'soffit_z': r(h['min'].z)})
    soffit = min((h['min'].z for h in ph), default=None)
    jamb_back_y = max((j['max'].y for j in pj), default=None)
    # obstacles: earth + jambs + heads (static), ground separately, partner leaf separately
    static_tris = list(earth_tris)
    for j in pj + ph: static_tris += j['tris']
    static_bvh = bvh_from_tris(static_tris)
    groups = []
    for lf in sorted(pl, key=lambda i: i['min'].x):
        side = -1 if (lf['min'].x + lf['max'].x) / 2 < cx else 1
        bs = leaf_group(lf)
        tris = lf['tris'] + [t for b in bs for t in b['tris']]
        hinge = Vector(((lf['min'].x + lf['max'].x) / 2, lf['min'].y, 0))
        sign = -1 if side == -1 else 1  # left leaf closes +y -> +x (clockwise, -), right leaf +y -> -x (+)
        groups.append({'leaf': lf, 'side': side, 'battens': bs, 'tris': tris, 'hinge': hinge, 'sign': sign})
    inner_faces = []
    for g in groups:
        lf = g['leaf']
        bx = [b['max'].x if g['side'] == -1 else b['min'].x for b in g['battens']]
        inner = (max(bx) if g['side'] == -1 else min(bx)) if bx else (lf['max'].x if g['side'] == -1 else lf['min'].x)
        inner_faces.append(inner)
        gt = [ground_top(x, y) for x in (lf['min'].x, lf['max'].x) for y in (lf['min'].y, (lf['min'].y + lf['max'].y) / 2, lf['max'].y)]
        gt = [z for z in gt if z is not None]
        jy = [j for j in pj if abs(((j['min'].x + j['max'].x) / 2) - lf['min'].x) < 0.4]
        P['leaves'].append({
            'side': g['side'], 'min': vec(lf['min']), 'max': vec(lf['max']), 'leaf_length_m': r(lf['dim'].y),
            'thickness_m': r(lf['dim'].x), 'height_m': r(lf['dim'].z), 'battens': len(g['battens']),
            'bottom_above_z0_m': r(lf['min'].z), 'ground_top_under_leaf_m': [r(min(gt)), r(max(gt))] if gt else None,
            'bottom_gap_to_ground_m': r(lf['min'].z - max(gt)) if gt else None,
            'top_gap_to_head_soffit_m': r(soffit - lf['max'].z) if soffit else None,
            'front_end_gap_to_jamb_back_m': r(lf['min'].y - jamb_back_y) if jamb_back_y is not None else None,
            'side_gap_to_pier_face_m': r(lf['min'].x - l) if g['side'] == -1 else r(rr - lf['max'].x),
            'hinge_inferred_xy': vec(g['hinge'][:2]), 'contact_or_pivot_found': False})
    if len(inner_faces) == 2:
        P['open_clear_width_between_leaves_m'] = r(abs(inner_faces[1] - inner_faces[0]))
    if len(groups) == 2:
        a, b = groups
        # hinge inference check: closed leaves should meet near opening centre
        reach = [g['hinge'].x + (-g['sign']) * g['leaf']['dim'].y for g in groups]
        P['hinge_inference'] = {'left_closed_tip_x': r(reach[0]), 'right_closed_tip_x': r(reach[1]),
                                'meeting_gap_m': r(reach[1] - reach[0]), 'opening_centre_x': r(cx)}
        sweep = []
        for ang in ANGLES:
            row = {'closing_deg': ang}
            ta = rot_tris(a['tris'], a['hinge'], a['sign'] * ang); tb_ = rot_tris(b['tris'], b['hinge'], b['sign'] * ang)
            for nm, tt in (('left', ta), ('right', tb_)):
                lb = bvh_from_tris(tt)
                row[nm + '_vs_static_pairs'] = len(lb.overlap(static_bvh))
                row[nm + '_vs_ground_pairs'] = len(lb.overlap(ground_bvh)) if ground_bvh else None
                pts = surface_samples(tt)
                ds = [static_bvh.find_nearest(p)[3] for p in pts]
                row[nm + '_min_clear_static_m'] = r(min(ds))
                if ground_bvh:
                    dg = [ground_bvh.find_nearest(p)[3] for p in pts]
                    row[nm + '_min_clear_ground_m'] = r(min(dg))
            row['leaf_vs_leaf_pairs'] = len(bvh_from_tris(ta).overlap(bvh_from_tris(tb_)))
            sweep.append(row)
        P['swing_sweep'] = sweep
        # blocking test: body box 0.5w x 0.3d x 1.7h, centred on passage axis, translated through the leaf plane
        def body(y, x0=cx, wdt=0.5, dep=0.3, hgt=1.7, z0=0.06):
            c = [Vector((x0 + sx * wdt / 2, y + sy * dep / 2, z0 + sz * hgt)) for sx in (-1, 1) for sy in (-1, 1) for sz in (0, 1)]
            idx = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
            return BVHTree.FromPolygons(c, idx, epsilon=0.0)
        ys = [-6.0 + 0.05 * i for i in range(81)]
        res = {}
        for state, ang in (('open_0deg', 0), ('closed_90deg', 90), ('half_45deg', 45)):
            lbvh = bvh_from_tris(rot_tris(a['tris'], a['hinge'], a['sign'] * ang) + rot_tris(b['tris'], b['hinge'], b['sign'] * ang))
            hits = [y for y in ys if body(y).overlap(lbvh) or body(y).overlap(static_bvh)]
            res[state] = {'samples': len(ys), 'blocked_samples': len(hits), 'first_block_y': r(hits[0]) if hits else None}
        # widest centred body that passes in the open state (0.05 m steps)
        lbvh0 = bvh_from_tris(a['tris'] + b['tris']); wmax = 0
        for i in range(1, 140):
            wd = 0.05 * i
            if any(body(y, wdt=wd).overlap(lbvh0) or body(y, wdt=wd).overlap(static_bvh) for y in ys): break
            wmax = wd
        res['open_widest_centred_body_m'] = r(wmax)
        P['passage_tests'] = res
        # closed-state light slots (orthographic, along y): side slot between jamb inner face and leaf hinge-side face
        P['closed_slots'] = {
            # closed (90 deg): leaf length runs along x from the hinge; thickness now along y
            'left_side_slot_x_m': r(a['hinge'].x - max(j['max'].x for j in pj if j['max'].x < cx)) if pj else None,
            'right_side_slot_x_m': r(min(j['min'].x for j in pj if j['min'].x > cx) - b['hinge'].x) if pj else None,
            'closed_leaf_front_face_y': r(a['hinge'].y - a['leaf']['dim'].x / 2),
            'jamb_back_face_y': r(jamb_back_y) if jamb_back_y is not None else None,
            'closed_leaf_to_jamb_back_gap_y_m': r((a['hinge'].y - a['leaf']['dim'].x / 2) - jamb_back_y) if jamb_back_y is not None else None,
            'closed_leaf_bottom_z': r(a['leaf']['min'].z),
            'top_slot_z_m': r(soffit - a['leaf']['max'].z) if soffit else None,
            'note': 'leaf closes behind the jamb plane (y>jamb back face); no rebate/stop overlaps the leaf edge'}
    result['passages'].append(P)

json.dump(result, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('MEASURE_OK', out_path)
