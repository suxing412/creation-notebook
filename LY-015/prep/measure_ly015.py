# LY-015 prep measurement (read-only on inputs). Blender 5.2:
#   blender -b --factory-startup --python-exit-code 1 -P measure_ly015.py -- <pkg_dir> <lab_docs_dir> <out_json>
# pkg_dir  = reassembled luoyang-kaiyang-gate-study-v1 (from modeling-lab/review-batches/2026-11-04-north13-gates, zip bad99bb9...)
# lab_docs = D:/GitHub/creation-notebook-lab/docs
# All coordinates are Blender Z-up gate-local metres (glTF X, -Z, Y). Front (y<0) = glTF +Z = south/outside.
import bpy, bmesh, sys, json, hashlib, math
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
PKG, DOCS, OUT = Path(argv[0]), Path(argv[1]), Path(argv[2])
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
R = {}

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def imp(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    return [o for o in bpy.data.objects if o not in before and o.type == 'MESH']

def world_bm(o):
    bm = bmesh.new(); dg = bpy.context.evaluated_depsgraph_get()
    bm.from_object(o, dg); bm.transform(o.matrix_world); return bm

def bvh_of(objs):
    vs, fs = [], []
    for o in objs:
        bm = world_bm(o); bmesh.ops.triangulate(bm, faces=bm.faces[:]); off = len(vs)
        vs += [v.co.copy() for v in bm.verts]; fs += [tuple(off + v.index for v in f.verts) for f in bm.faces]; bm.free()
    return BVHTree.FromPolygons(vs, fs), vs, fs

def bbox(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    return [[round(min(p[k] for p in pts), 4) for k in range(3)], [round(max(p[k] for p in pts), 4) for k in range(3)]]

def glb_info(path, objs):
    tris = 0; mats = set()
    for o in objs:
        o.data.calc_loop_triangles(); tris += len(o.data.loop_triangles); mats |= {m.name for m in o.data.materials if m}
    vol = {}
    for o in objs:
        bm = world_bm(o); vol[o.name] = round(bm.calc_volume(signed=True), 4); bm.free()
    return {'path': str(path).replace('\\', '/'), 'bytes': Path(path).stat().st_size, 'sha256': sha(path), 'objects': sorted(o.name for o in objs),
            'triangles': tris, 'materials': sorted(mats), 'bbox_local_zup': bbox(objs), 'signed_volume_m3': vol}

def ray(bvh, o, d, dist=100.0):
    hit = bvh.ray_cast(Vector(o), Vector(d).normalized(), dist)
    return None if hit[0] is None else hit[3]

def frange(a, b, s):
    n = int(round((b - a) / s)); return [a + i * s for i in range(n + 1)]

GATE = {0: DOCS / 'library/models/m-luoyang-kaiyang-gate/files/kaiyang-K-LOD0.glb',
        1: DOCS / 'cities/luoyang/progress-assets/north13-gates/luoyang-kaiyang-gate-study-v1/models/kaiyang-K-LOD1.glb',
        2: DOCS / 'cities/luoyang/progress-assets/north13-gates/luoyang-kaiyang-gate-study-v1/models/kaiyang-K-LOD2.glb'}
GROUND = {k: DOCS / f'library/models/m-luoyang-kaiyang-gate/files/kaiyang-ground-LOD{k}.glb' for k in range(3)}
FLAT = DOCS / 'cities/luoyang/progress-assets/flat/study-north13-kaiyang-K-94693c58dd63.glb'
PASS = [(-9.6, -5.6), (-2.8, 2.8), (5.6, 9.6)]  # from build.py: 2.8 piers, 4/5.6/4 openings, total 24.8

R['gate'] = {}; R['ground'] = {}; R['pairing'] = {}
for lod in range(3):
    reset(); g = imp(GATE[lod]); gi = glb_info(GATE[lod], g); bvh, _, _ = bvh_of(g)
    # passage clearances: clear height at passage centre line, clear width at several heights, full-depth see-through
    pas = []
    for (l, r) in PASS:
        xc = (l + r) / 2; ch = []; widths = {}
        for y in frange(-6.0, 6.0, 0.25):
            h = ray(bvh, (xc, y, 0.01), (0, 0, 1)); ch.append(None if h is None else round(h + 0.01, 3))
        for z in [0.1, 1.0, 1.8, 2.5, 3.5, 4.4, 4.65, 4.9]:
            wmin = 99; ymin = None
            for y in frange(-5.5, 5.5, 0.05):
                a = ray(bvh, (xc, y, z), (-1, 0, 0)); b = ray(bvh, (xc, y, z), (1, 0, 0))
                w = (a if a is not None else 50) + (b if b is not None else 50)
                if w < wmin: wmin, ymin = w, y
            widths[str(z)] = {'min_clear_width_m': round(wmin, 3), 'at_y': round(ymin, 2)}
        thru = {}
        for z in [0.3, 1.8, 4.5]:
            thru[str(z)] = ray(bvh, (xc, -8.0, z), (0, 1, 0), 16.0) is None
        under = [c for c in ch if c is not None]
        pas.append({'passage_x': [l, r], 'nominal_width_m': round(r - l, 2), 'clear_height_min_m': min(under) if under else None,
                    'clear_height_max_m': max(under) if under else None, 'clear_width_by_height': widths, 'see_through_full_depth': thru})
    gi['passages'] = pas
    # top surfaces (downward rays) over gate footprint -> upper deck height / any stair or ramp surfaces
    tops = {}; mids = []
    for x in frange(-13.4, 13.4, 0.2):
        for y in frange(-6.2, 6.2, 0.2):
            # first hit from above, then continue to collect any upward-facing surface between 0.3 and 5.2 (stair/ramp candidates)
            z0 = 30.0
            while True:
                hit = bvh.ray_cast(Vector((x, y, z0)), Vector((0, 0, -1)), z0 + 1)
                if hit[0] is None: break
                z = hit[0].z
                if hit[1].z > 0.5:
                    key = round(z, 2); tops[key] = tops.get(key, 0) + 1
                    if 0.3 < z < 5.2 and not (abs(z - 5.0) < 0.02): mids.append((round(x, 1), round(y, 1), round(z, 3)))
                z0 = z - 1e-4
                if z0 < -1: break
    gi['upward_surface_height_histogram'] = {str(k): v for k, v in sorted(tops.items()) if v >= 5}
    xs = sorted({m[0] for m in mids}); zs = sorted({m[2] for m in mids})
    gi['upward_surfaces_between_0.3_and_5.2_m'] = {'samples': len(mids), 'heights': zs[:40], 'x_values_sample': xs[:20],
        'note': 'candidates for stairs/ramps; door-leaf/batten/door-head tops are expected here, they are not access'}
    # deck edge guarding: horizontal rays at 0.9 m above deck top, from deck interior outward
    deck_top = 5.34; guard = {}
    for name, o, d in [('front_y-', (0, -4.0, deck_top + 0.9), (0, -1, 0)), ('rear_y+', (0, 4.0, deck_top + 0.9), (0, 1, 0)),
                       ('end_x-', (-11.0, 0, deck_top + 0.9), (-1, 0, 0)), ('end_x+', (11.0, 0, deck_top + 0.9), (1, 0, 0))]:
        hits = 0; tot = 0
        rng = frange(-12.0, 12.0, 0.5) if 'y' in name.split('_')[1] else frange(-4.8, 4.8, 0.4)
        for s in rng:
            oo = list(o)
            if 'y' in name.split('_')[1]: oo[0] = s
            else: oo[1] = s
            tot += 1; hits += ray(bvh, oo, d, 3.0) is not None
        guard[name] = {'rays': tot, 'blocked_within_3m': hits}
    gi['deck_edge_rays_at_0.9m_above_5.34'] = guard
    R['gate'][f'LOD{lod}'] = gi
    # ground attachment paired with same LOD
    gr = imp(GROUND[lod]); gri = glb_info(GROUND[lod], gr)
    bm = world_bm(gr[0]); islands = []; seen = set()
    for f in bm.faces:
        if f.index in seen: continue
        stack = [f]; comp = []
        while stack:
            ff = stack.pop()
            if ff.index in seen: continue
            seen.add(ff.index); comp.append(ff)
            for e in ff.edges:
                for nf in e.link_faces:
                    if nf.index not in seen: stack.append(nf)
        pts = [v.co for ff in comp for v in ff.verts]
        islands.append({'faces': len(comp), 'min': [round(min(p[k] for p in pts), 3) for k in range(3)], 'max': [round(max(p[k] for p in pts), 3) for k in range(3)]})
    bm.free(); gri['islands'] = sorted(islands, key=lambda i: i['min'][0])
    R['ground'][f'LOD{lod}'] = gri
    gbvh, _, _ = bvh_of(gr)
    over = bvh.overlap(gbvh)
    # support coverage of each full passage footprint (passage width x 14 m) by the ground strips
    cov = []
    for (l, r) in PASS:
        tot = sup = 0
        for x in frange(l + 0.05, r - 0.05, 0.1):
            for y in frange(-6.95, 6.95, 0.1):
                tot += 1; sup += ray(gbvh, (x, y, 1.0), (0, 0, -1), 2.0) is not None
        cov.append({'passage_x': [l, r], 'samples': tot, 'supported': sup, 'fraction': round(sup / tot, 4)})
    R['pairing'][f'LOD{lod}'] = {'gate_ground_triangle_overlap_pairs': len(over), 'passage_footprint_support': cov}

# flat (city-site projection) readback vs LOD1
reset(); f = imp(FLAT); R['flat_projection'] = glb_info(FLAT, f)

# hidden trial blend: connector (wall adapter) geometry only exists here, joined into earth of LOD1
TB = PKG / 'city/kaiyang-K-mid-hidden-trial.blend'
bpy.ops.wm.open_mainfile(filepath=str(TB))
tr = {'path': 'luoyang-kaiyang-gate-study-v1/city/kaiyang-K-mid-hidden-trial.blend', 'sha256': sha(TB), 'objects': []}
earth = None
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    o.data.calc_loop_triangles()
    mw = o.matrix_world
    tr['objects'].append({'name': o.name, 'triangles': len(o.data.loop_triangles), 'hide_viewport': o.hide_viewport, 'hide_render': o.hide_render,
                          'translation': [round(c, 4) for c in mw.translation], 'rotation_z_rad': round(mw.to_euler().z, 6),
                          'local_bbox': [[round(min(v.co[k] for v in o.data.vertices), 4) for k in range(3)], [round(max(v.co[k] for v in o.data.vertices), 4) for k in range(3)]]})
    if o.name.startswith('kaiyang-K-static_earth'): earth = o
if earth:
    me = earth.data; ext = [v.co.copy() for v in me.vertices if abs(v.co.x) > 12.41]
    side = {}
    for s in (-1, 1):
        pts = [p for p in ext if p.x * s > 0]
        if pts:
            side[str(s)] = {'vertices': len(pts), 'x_range': [round(min(p.x for p in pts), 4), round(max(p.x for p in pts), 4)],
                            'y_range': [round(min(p.y for p in pts), 4), round(max(p.y for p in pts), 4)],
                            'z_range': [round(min(p.z for p in pts), 4), round(max(p.z for p in pts), 4)],
                            'outer_top_z': round(max(p.z for p in pts if abs(p.x) > 15), 4) if any(abs(p.x) > 15 for p in pts) else None}
    tr['connector_vertices_beyond_x12.41'] = side
    # walkable top of connector vs deck top: sample downward along centre line y=0
    bvh = BVHTree.FromPolygons([v.co for v in earth.data.vertices], [tuple(pp.vertices) for pp in earth.data.polygons])  # library-only blend: objects not in a scene, use local mesh data
    prof = []
    for x in frange(10.0, 16.6, 0.2):
        h = bvh.ray_cast(Vector((x, 0, 30)), Vector((0, 0, -1)), 40)
        prof.append([round(x, 2), None if h[0] is None else round(h[0].z, 3)])
    tr['earth_top_profile_y0_x10_to_16.6'] = prof
    tim = next((o for o in bpy.data.objects if o.name.startswith('kaiyang-K-static_timber')), None)
    if tim:
        tb = BVHTree.FromPolygons([v.co for v in tim.data.vertices], [tuple(pp.vertices) for pp in tim.data.polygons])
        tr['timber_top_y0'] = [[round(x, 2), (lambda h: None if h[0] is None else round(h[0].z, 3))(tb.ray_cast(Vector((x, 0, 7.0)), Vector((0, 0, -1)), 10))] for x in frange(10.0, 13.0, 0.4)]
R['trial'] = tr

# wall caps from interface-input (world, Blender z-up) mapped into gate-local through placement
q = json.loads((PKG / 'qa/interface-input.json').read_text()); pl = json.loads((PKG / 'city/placement.json').read_text())
T = Matrix.Translation(Vector(pl['engineering_origin_from_existing_wall_caps'])) @ Matrix.Rotation(pl['rotation_z_rad'], 4, 'Z'); inv = T.inverted()
caps = []
for row in q['rows']:
    vs = {tuple(v) for f in row['faces'] for v in f['v']}
    loc = [inv @ Vector(v) for v in vs]
    near = sorted(loc, key=lambda p: abs(p.x))[:4]
    caps.append({'wall': row['name'], 'cap_local_x': [round(min(p.x for p in near), 4), round(max(p.x for p in near), 4)],
                 'cap_local_y': [round(min(p.y for p in near), 4), round(max(p.y for p in near), 4)],
                 'cap_local_z': [round(min(p.z for p in near), 4), round(max(p.z for p in near), 4)]})
R['wall_caps_local'] = caps
OUT.write_text(json.dumps(R, indent=1, ensure_ascii=False)); print('LY015_MEASURE_OK', OUT)
