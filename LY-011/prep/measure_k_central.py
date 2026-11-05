# LY-011 prep (read-only): measure the Kaiyang K-v1 central passage bearing frame from the
# actual exported GLBs. Nothing is written except the JSON report; no GLB is re-exported.
#
# Usage:
#   D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P measure_k_central.py -- \
#       <source-object-ranges.json> <out.json> <ground.glb|-> <label=lodN=glb> [<label=lodN=glb> ...]
#
# Coordinates: Blender Z-up after glTF import (glTF -Z == Blender +Y), i.e. the build.py frame.
# Central passage opening (from build.py): x in [-2.8, 2.8], y in [-5, 5], z in [0, 5].
import bpy, bmesh, sys, json, hashlib, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
RANGES, OUT, GROUND = argv[0], argv[1], argv[2]
SPECS = [a.split('=', 2) for a in argv[3:]]
ranges = json.load(open(RANGES, encoding='utf-8'))
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
EPS = 1e-4
OPEN = (-2.8, 2.8)            # central opening x range (build.py)
import os
ALL_PAIRS = os.environ.get('LY011_ALL_PAIRS') == '1'   # 1 = every component pair, not only the central bay
CENTRAL_KEYS = ['jamb_(1', 'door_head_1', 'open_leaf_(1', 'leaf_batten_(1', 'earth_pier_1', 'earth_pier_2',
                'upper_deck', 'central_room', 'gallery_post_(0', 'cross_tie_0', 'rafters_(0']


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_glb(p):
    reset(); bpy.ops.import_scene.gltf(filepath=p)
    return [o for o in bpy.context.scene.objects if o.type == 'MESH']


def tri_list(o):
    me = o.data; me.calc_loop_triangles(); mw = o.matrix_world
    # polygons are triangles after glTF import; keep polygon order (source contact-audit verified it)
    return [[mw @ me.vertices[v].co for v in p.vertices] for p in me.polygons]


def bbox(vs):
    return [min(v[k] for v in vs) for k in range(3)], [max(v[k] for v in vs) for k in range(3)]


def signed_volume(tris):
    return sum(a.dot(b.cross(c)) for a, b, c in tris) / 6.0


def is_axis_box(tris):
    vs = {tuple(round(x, 5) for x in v) for t in tris for v in t}
    if len(vs) != 8 or len(tris) != 12: return False
    lo, hi = bbox([Vector(v) for v in vs])
    return all(any(abs(v[k] - lo[k]) < 1e-5 or abs(v[k] - hi[k]) < 1e-5 for k in range(3)) and
               all(abs(v[k] - lo[k]) < 1e-5 or abs(v[k] - hi[k]) < 1e-5 for k in range(3)) for v in vs)


def make_obj(name, tris):
    me = bpy.data.meshes.new(name); vs = []; fs = []
    for t in tris:
        fs.append((len(vs), len(vs) + 1, len(vs) + 2)); vs.extend([tuple(v) for v in t])
    me.from_pydata(vs, [], fs); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); return o


def bool_intersection_volume(ta, tb):
    a = make_obj('A', ta); b = make_obj('B', tb)
    m = a.modifiers.new('x', 'BOOLEAN'); m.operation = 'INTERSECT'; m.solver = 'EXACT'; m.object = b
    dg = bpy.context.evaluated_depsgraph_get(); ev = a.evaluated_get(dg); me = ev.to_mesh()
    bm = bmesh.new(); bm.from_mesh(me); v = bm.calc_volume(signed=True); bm.free(); ev.to_mesh_clear()
    for o in (a, b):
        d = o.data; bpy.data.objects.remove(o, do_unlink=True); bpy.data.meshes.remove(d)
    return abs(v)


def split(objs, lod):
    comps = {}
    for o in objs:
        role = o.name.replace('kaiyang-K-static_', '').split('.')[0]
        key = f'LOD{lod}_{role}'
        tris = tri_list(o)
        rr = ranges.get(key)
        if rr is None or rr[-1]['triangle_range'][1] != len(tris):
            return None, f'triangle count mismatch for {key}: glb {len(tris)} vs ranges {rr[-1]["triangle_range"][1] if rr else None}'
        for r in rr:
            s, e = r['triangle_range']; comps[r['source_object']] = {'role': role, 'tris': tris[s:e]}
    return comps, None


def bvh_of(tris):
    pts = []; polys = []
    for t in tris:
        polys.append([len(pts), len(pts) + 1, len(pts) + 2]); pts.extend(t)
    return BVHTree.FromPolygons(pts, polys, epsilon=0.0)


def ray_first(bvh, o, d, dist=100.0):
    h = bvh.ray_cast(Vector(o), Vector(d), dist)
    return None if h[0] is None else h[3]


report = {'script_sha256': sha(__file__), 'ranges_sha256': sha(RANGES), 'eps_m': EPS,
          'central_opening_x_m': OPEN, 'models': [], 'ground': None}

for label, lod, path in SPECS:
    lod = int(lod.replace('lod', ''))
    objs = import_glb(path)
    rec = {'label': label, 'lod': lod, 'path': path, 'sha256': sha(path), 'bytes': __import__('os').path.getsize(path),
           'meshes': {o.name: len(o.data.polygons) for o in objs}}
    all_tris = [t for o in objs for t in tri_list(o)]
    whole = bvh_of(all_tris)
    comps, err = split(objs, lod)
    rec['split_error'] = err
    if comps:
        info = {}
        for n, c in comps.items():
            lo, hi = bbox([v for t in c['tris'] for v in t])
            info[n] = {'role': c['role'], 'lo': lo, 'hi': hi, 'tris': len(c['tris']),
                       'volume_m3': signed_volume(c['tris']), 'axis_box': is_axis_box(c['tris'])}
        central = [n for n in info if ALL_PAIRS or any(k in n for k in CENTRAL_KEYS)]
        rec['all_pairs_mode'] = ALL_PAIRS
        rec['central_components'] = {n: {k: (round(v, 5) if isinstance(v, float) else ([round(x, 5) for x in v] if isinstance(v, list) else v)) for k, v in info[n].items()} for n in sorted(central)}
        # pairwise: every pair with at least one central component and AABB overlap/touch
        pairs = []
        names = sorted(info)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                if not (a in central or b in central): continue
                A, B = info[a], info[b]
                ov = [min(A['hi'][k], B['hi'][k]) - max(A['lo'][k], B['lo'][k]) for k in range(3)]
                if min(ov) < -EPS: continue
                row = {'a': a, 'b': b, 'aabb_overlap_m': [round(x, 5) for x in ov]}
                if min(ov) <= EPS:
                    row['class'] = 'face/edge contact (zero-thickness AABB overlap)'
                    row['intersection_m3'] = 0.0
                else:
                    if A['axis_box'] and B['axis_box']:
                        v = ov[0] * ov[1] * ov[2]; row['method'] = 'exact axis-box product'
                    else:
                        v = bool_intersection_volume(comps[a]['tris'], comps[b]['tris']); row['method'] = 'EXACT boolean intersect'
                    row['intersection_m3'] = round(v, 6)
                    va, vb = abs(A['volume_m3']), abs(B['volume_m3'])
                    if v > 1e-7 and (abs(v - min(va, vb)) / max(min(va, vb), 1e-12) < 1e-3):
                        row['class'] = 'full containment of smaller part'
                    elif v > 1e-7:
                        row['class'] = 'positive-volume interpenetration'
                    else:
                        row['class'] = 'aabb overlap but no solid intersection'
                pairs.append(row)
        rec['central_pairs'] = pairs
        rec['central_positive_volume_total_m3'] = round(sum(p['intersection_m3'] for p in pairs if p['intersection_m3'] > 1e-7), 6)
        # loads standing on the deck top directly above the central opening
        deck = info.get('C_upper_deck')
        if deck:
            top = deck['hi'][2]; on = []
            for n, c in info.items():
                if n == 'C_upper_deck': continue
                if abs(c['lo'][2] - top) < 1e-3 and c['hi'][0] > OPEN[0] + EPS and c['lo'][0] < OPEN[1] - EPS:
                    xs = (max(c['lo'][0], OPEN[0]), min(c['hi'][0], OPEN[1]))
                    on.append({'part': n, 'lo': [round(x, 4) for x in c['lo']], 'hi': [round(x, 4) for x in c['hi']],
                               'x_inside_opening_m': [round(xs[0], 4), round(xs[1], 4)], 'volume_m3': round(abs(c['volume_m3']), 5)})
            rec['deck'] = {'lo': [round(x, 5) for x in deck['lo']], 'hi': [round(x, 5) for x in deck['hi']],
                           'clear_span_x_m': round(OPEN[1] - OPEN[0], 4), 'parts_standing_on_deck_over_opening': on}
    # clear-width and headroom sampling inside central opening using the WHOLE exported mesh
    ys = [round(-5.2 + 0.05 * i, 3) for i in range(int(10.4 / 0.05) + 1)]
    zs = [round(0.05 + 0.05 * i, 3) for i in range(98)]
    width_rows = []
    min_w = (1e9, None)
    for y in ys:
        wy = 1e9; zat = None
        for z in zs:
            r = ray_first(whole, (0, y, z), (1, 0, 0), 4.0); l = ray_first(whole, (0, y, z), (-1, 0, 0), 4.0)
            w = (r if r is not None else 4.0) + (l if l is not None else 4.0)
            if w < wy: wy, zat = w, z
        width_rows.append({'y': y, 'min_clear_width_m': round(wy, 4), 'at_z': zat})
        if -5 <= y <= 5 and wy < min_w[0]: min_w = (wy, y)
    head = []
    min_h = (1e9, None)
    for x in [round(-2.75 + 0.05 * i, 3) for i in range(111)]:
        for y in [round(-4.95 + 0.1 * i, 3) for i in range(100)]:
            h = ray_first(whole, (x, y, 0.001), (0, 0, 1), 20.0)
            hh = (h + 0.001) if h is not None else None
            if hh is not None and hh < min_h[0]: min_h = (hh, (x, y))
    # headroom profile along centre line x=0 and near jamb x=+-2.55
    prof = {}
    for x in (0.0, -2.55, 2.55):
        prof[str(x)] = [{'y': y, 'ceiling_z': (round(ray_first(whole, (x, y, 0.001), (0, 0, 1), 20.0) + 0.001, 4)
                                                if ray_first(whole, (x, y, 0.001), (0, 0, 1), 20.0) is not None else None)}
                        for y in [round(-5.0 + 0.25 * i, 3) for i in range(41)]]
    # deck underside support: BVH of every part EXCEPT the deck; from z=5.0005 look down 0.0105 m.
    # A hit means some part's top face lies within 0.01 m under the deck underside (z=5.0).
    sup = {'grid_step_m': 0.05, 'samples': 0, 'supported_from_below_within_0.01m': 0, 'supported_by': {}}
    if comps:
        nd = [n for n in comps if n != 'C_upper_deck']
        nd_tris = []; owner = []
        for n in nd:
            nd_tris.extend(comps[n]['tris']); owner.extend([n] * len(comps[n]['tris']))
        nbvh = bvh_of(nd_tris)
        for x in [round(-2.775 + 0.05 * i, 4) for i in range(112)]:
            for y in [round(-4.975 + 0.05 * i, 4) for i in range(200)]:
                sup['samples'] += 1
                h = nbvh.ray_cast(Vector((x, y, 5.0005)), Vector((0, 0, -1)), 0.0105)
                if h[0] is not None:
                    sup['supported_from_below_within_0.01m'] += 1
                    sup['supported_by'][owner[h[2]]] = sup['supported_by'].get(owner[h[2]], 0) + 1
        sup['supported_fraction'] = round(sup['supported_from_below_within_0.01m'] / sup['samples'], 4)
        sup['method'] = 'deck excluded; discrete 0.05 m grid over x(-2.8,2.8) y(-5,5); contact sampling, not load path or structural safety'
    ceil = []
    for y in [round(-4.95 + 0.05 * i, 3) for i in range(199)]:
        h = ray_first(whole, (0.0, y, 4.4), (0, 0, 1), 20.0)
        ceil.append({'y': y, 'ceiling_z_from_4.4': None if h is None else round(4.4 + h, 4)})
    lows = [c for c in ceil if c['ceiling_z_from_4.4'] is not None]
    mc = min(lows, key=lambda c: c['ceiling_z_from_4.4'])
    rec['ceiling_centerline'] = {'min_ceiling_z': mc['ceiling_z_from_4.4'], 'at_y': mc['y'],
                                 'y_ranges_below_5.0': [c['y'] for c in lows if c['ceiling_z_from_4.4'] < 4.999],
                                 'note': 'x=0 line, rays upward from z=4.4 (above leaf tops 4.35); excludes leaf undersides'}
    rec['clearance'] = {'min_clear_width_m_inside_y-5..5': round(min_w[0], 4), 'at_y': min_w[1],
                        'min_headroom_m': round(min_h[0], 4), 'at_xy': min_h[1],
                        'width_profile': width_rows, 'headroom_profile': prof,
                        'method': 'BVH ray casts on all exported triangles from x=0 (width) and from z=0.001 (headroom); discrete samples, not a continuous body sweep'}
    rec['deck_underside_support'] = sup
    report['models'].append(rec)

if GROUND != '-':
    objs = import_glb(GROUND)
    tris = [t for o in objs for t in tri_list(o)]
    lo, hi = bbox([v for t in tris for v in t])
    bvh = bvh_of(tris)
    # top surface z under the central opening
    tops = []; cover = 0; n = 0
    for x in [round(-2.75 + 0.05 * i, 3) for i in range(111)]:
        for y in [round(-4.95 + 0.1 * i, 3) for i in range(100)]:
            n += 1
            d = ray_first(bvh, (x, y, 1.0), (0, 0, -1), 2.0)
            if d is not None: cover += 1; tops.append(1.0 - d)
    # strips: x extents of ground under passage y=0
    xs = []
    prev = None
    for i in range(int(17.2 / 0.01) + 1):
        x = round(-8.6 + 0.01 * i, 3); hit = ray_first(bvh, (x, 0.0, 1.0), (0, 0, -1), 2.0) is not None
        if hit != prev: xs.append((x, hit)); prev = hit
    report['ground'] = {'path': GROUND, 'sha256': sha(GROUND), 'meshes': {o.name: len(o.data.polygons) for o in objs},
                        'lo': [round(x, 4) for x in lo], 'hi': [round(x, 4) for x in hi],
                        'central_opening_samples': n, 'covered_samples': cover,
                        'covered_fraction': round(cover / n, 4),
                        'top_z_min': round(min(tops), 4) if tops else None, 'top_z_max': round(max(tops), 4) if tops else None,
                        'x_transitions_at_y0': xs,
                        'volume_m3': round(abs(signed_volume(tris)), 4)}

json.dump(report, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('LY011_MEASURE_OK', OUT)
