# LY-085 prep (read-only measurement; produces no deliverable geometry).
# Measures, for the Kaiyang and Pingcheng south-wall gates, the gap between each gate's
# outer (south) opening and the nearest actually-loaded city ground / existing road end.
#
#   D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P measure_south_ends.py -- <lab_root> <out.json>
#
# Frames: Blender world = glTF (x, -z, y). Gate local frame = Blender import of the gate GLB;
# world = T @ local, T = Translation(origin) @ RotZ(rotation_z_rad) from
# docs/cities/luoyang/progress-assets/north13-gates/source.json (activation=false; hidden-trial placement).
# Outer side = local -y (verified below by mapping local -y to world -y, i.e. away from the city).
import bpy, sys, json, hashlib, math
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index('--') + 1:]
LAB = Path(a[0]); OUT = Path(a[1])
D = LAB / 'docs'
CITY = D / 'cities/luoyang'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def import_glb(path, M=Matrix.Identity(4)):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    new = [o for o in bpy.data.objects if o not in before]
    dg = bpy.context.evaluated_depsgraph_get()
    out = []
    for o in new:
        if o.type != 'MESH':
            continue
        me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles()
        mw = M @ o.matrix_world
        vs = [mw @ v.co for v in me.vertices]
        fs = [tuple(t.vertices) for t in me.loop_triangles]
        out.append({'name': o.name, 'v': vs, 'f': fs})
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    return out


def combined(objs):
    vs, fs, owner = [], [], []
    for i, o in enumerate(objs):
        off = len(vs); vs += o['v']; fs += [tuple(off + k for k in t) for t in o['f']]; owner += [i] * len(o['f'])
    return BVHTree.FromPolygons(vs, fs, epsilon=0.0), owner


def bbox(vs):
    xs = [v.x for v in vs]; ys = [v.y for v in vs]; zs = [v.z for v in vs]
    return [[round(min(xs), 4), round(min(ys), 4), round(min(zs), 4)], [round(max(xs), 4), round(max(ys), 4), round(max(zs), 4)]]


R = lambda x, n=4: round(float(x), n)
src = json.loads((CITY / 'progress-assets/north13-gates/source.json').read_text(encoding='utf-8'))
PL = {p['package']: p['placement'] for p in src['packages'] if 'placement' in p}

bpy.ops.wm.read_factory_settings(use_empty=True)
res = {'inputs': {}, 'frame_note': 'Blender world = glTF (x,-z,y); gate local -y = outer/south', 'gates': {}}

# ---------------- city ground (exactly the four terrain-chapter atomics) ----------------
GROUND = [('ground-network-ground-stitched', 'assets/ground-atomic/network-ground-stitched.glb', (0, 0, 0)),
          ('ground-retained', 'assets/ground-atomic/retained.glb', (0, 0, 0)),
          ('ground-south', 'assets/ground-atomic/south.glb', (0, 0, 0)),
          ('ground-D08', 'assets/ground-atomic/D08.glb', (580, 0, -960))]   # glTF translation from city-data node
gobjs = []
for gid, rel, t in GROUND:
    p = CITY / rel
    M = Matrix.Translation(Vector((t[0], -t[2], t[1])))
    objs = import_glb(p, M)
    for o in objs:
        o['file'] = gid
    gobjs += objs
    res['inputs'][rel] = {'sha256': sha(p), 'objects': {o['name']: len(o['f']) for o in objs}}
GB, GOWN = combined(gobjs)
gname = [o['file'] + ':' + o['name'] for o in gobjs]


def ground_hit(wx, wy, top=60.0):
    h = GB.ray_cast(Vector((wx, wy, top)), Vector((0, 0, -1)), 200.0)
    if h[0] is None:
        return None
    return gname[GOWN[h[2]]], h[0].z


GATES = {
    'kaiyang': {'pkg': 'luoyang-kaiyang-gate-study-v1',
                'lods': ['library/models/m-luoyang-kaiyang-gate/files/kaiyang-K-LOD0.glb',
                         'cities/luoyang/progress-assets/north13-gates/luoyang-kaiyang-gate-study-v1/models/kaiyang-K-LOD1.glb',
                         'cities/luoyang/progress-assets/north13-gates/luoyang-kaiyang-gate-study-v1/models/kaiyang-K-LOD2.glb'],
                'cityflat': 'cities/luoyang/progress-assets/flat/study-north13-kaiyang-K-94693c58dd63.glb',
                'ground': ['library/models/m-luoyang-kaiyang-gate/files/kaiyang-ground-LOD%d.glb' % i for i in range(3)]},
    'pingcheng': {'pkg': 'luoyang-pingcheng-gate-study-v1',
                  'lods': ['library/models/m-luoyang-pingcheng-gate/files/pingcheng-P-LOD0.glb',
                           'cities/luoyang/progress-assets/north13-gates/luoyang-pingcheng-gate-study-v1/models/pingcheng-P-LOD1.glb',
                           'cities/luoyang/progress-assets/north13-gates/luoyang-pingcheng-gate-study-v1/models/pingcheng-P-LOD2.glb'],
                  'cityflat': 'cities/luoyang/progress-assets/flat/study-north13-pingcheng-P-c8ab88f4b326.glb',
                  'ground': ['library/models/m-luoyang-pingcheng-gate/files/pingcheng-ground-LOD%d.glb' % i for i in range(3)]},
}

for g, cfg in GATES.items():
    pl = PL[cfg['pkg']]
    O = Vector(pl['engineering_origin_from_existing_wall_caps']); rot = pl['rotation_z_rad']
    T = Matrix.Translation(O) @ Matrix.Rotation(rot, 4, 'Z')
    W = lambda x, y, z=0.0: T @ Vector((x, y, z))
    gr = {'placement': {'origin': [R(c) for c in O], 'rotation_z_rad': rot, 'activation': pl.get('activation'),
                        'B_point_unchanged': pl.get('B_point_unchanged')},
          'outer_dir_world': [R(c) for c in (T.to_3x3() @ Vector((0, -1, 0)))]}
    # ---------- gate body: passages per LOD ----------
    lodinfo = []
    for rel in cfg['lods'] + [cfg['cityflat']]:
        p = D / rel
        objs = import_glb(p)
        res['inputs'][rel] = {'sha256': sha(p), 'objects': {o['name']: len(o['f']) for o in objs}}
        B, _ = combined(objs)
        allv = [v for o in objs for v in o['v']]
        info = {'file': rel, 'bbox_local': bbox(allv)}
        ymin = info['bbox_local'][0][1] - 2
        for z in (0.3, 1.0, 1.8):
            clear = []
            x = -15.0
            while x <= 15.0001:
                h = B.ray_cast(Vector((x, ymin, z)), Vector((0, 1, 0)), 40.0)
                clear.append((round(x, 2), h[0] is None)); x += 0.02
            rng = []; s = None
            for xx, c in clear:
                if c and s is None: s = xx
                if not c and s is not None: rng.append([s, round(xx - 0.02, 2)]); s = None
            if s is not None: rng.append([s, 15.0])
            info['through_clear_x_at_z%.1f' % z] = rng
        # lowest geometry z near the outer face (threshold / base)
        lodinfo.append(info)
    gr['gate_lods'] = lodinfo
    # ---------- gate ground strips ----------
    ginfo = []
    for rel in cfg['ground']:
        p = D / rel
        objs = import_glb(p)
        res['inputs'][rel] = {'sha256': sha(p), 'objects': {o['name']: len(o['f']) for o in objs}}
        ginfo.append({'file': rel, 'bbox_local': bbox([v for o in objs for v in o['v']]),
                      'objects': {o['name']: bbox(o['v']) for o in objs}})
        if rel.endswith('LOD0.glb'):
            SB, SOWN = combined(objs); sobjs = objs
    gr['gate_ground_lods'] = ginfo
    strip_ymin = min(o['bbox_local'][0][1] for o in ginfo)
    strip_top = max(o['bbox_local'][1][2] for o in ginfo)
    gr['outer_port_local_y'] = strip_ymin
    gr['strip_top_local_z'] = strip_top
    gr['strip_top_world_z'] = R(W(0, strip_ymin, strip_top).z)

    def supported_local(x, y):
        """support from LOD0 gate ground strip (local) or any city ground (world)"""
        h = SB.ray_cast(Vector((x, y, 20)), Vector((0, 0, -1)), 40)
        if h[0] is not None:
            return 'strip:' + sobjs[SOWN[h[2]]]['name'], W(x, y, h[0].z).z
        wp = W(x, y)
        return ground_hit(wp.x, wp.y)

    # ---------- local raster of actual city ground (0.5 m) ----------
    per = {}; cells = []
    y = -140.0
    while y <= 40.0001:
        x = -60.0
        while x <= 60.0001:
            wp = W(x, y); h = ground_hit(wp.x, wp.y)
            if h:
                d = per.setdefault(h[0], {'n': 0, 'x': [1e9, -1e9], 'y': [1e9, -1e9], 'z': [1e9, -1e9]})
                d['n'] += 1; d['x'] = [min(d['x'][0], x), max(d['x'][1], x)]; d['y'] = [min(d['y'][0], y), max(d['y'][1], y)]
                d['z'] = [R(min(d['z'][0], h[1])), R(max(d['z'][1], h[1]))]
                cells.append((x, y, h[0], h[1]))
            x += 0.5
        y += 0.5
    gr['city_ground_local_raster_0.5m_x-60..60_y-140..40'] = per
    # ascii map 2 m
    occ = {(round(x), round(y)) for x, y, _, _ in cells}
    amap = {}
    for yy in range(40, -141, -4):
        amap[str(yy)] = ''.join('#' if any((xx + dx, yy + dy) in occ for dx in (-1, 0, 1) for dy in (-1, 0, 1)) else '.' for xx in range(-60, 61, 2))
    gr['ascii_4m_rows_y40..-140_cols_x-60..60_step2'] = amap
    # nearest city ground cell to outer port centre
    if cells:
        c = min(cells, key=lambda c: (c[0]) ** 2 + (c[1] - strip_ymin) ** 2)
        gr['nearest_city_ground_to_outer_port_centre'] = {'local': [c[0], c[1]], 'obj': c[2], 'world_z': R(c[3]),
                                                           'dist_m': R(math.hypot(c[0], c[1] - strip_ymin), 3)}
        ci = min(cells, key=lambda c: (c[0]) ** 2 + (c[1] - (-strip_ymin)) ** 2)
        gr['nearest_city_ground_to_inner_port_centre'] = {'local': [ci[0], ci[1]], 'obj': ci[2], 'world_z': R(ci[3]),
                                                           'dist_m': R(math.hypot(ci[0], ci[1] + strip_ymin), 3)}
    # ---------- road-end profile: northernmost supported y per x column, south of the gate ----------
    prof = {}
    for x, y, o, z in cells:
        if y < strip_ymin and (x not in prof or y > prof[x][0]):
            prof[x] = (y, o, R(z))
    if prof:
        ys = sorted(set(v[0] for v in prof.values()))
        top = max(v[0] for v in prof.values())
        end_cols = sorted(x for x, v in prof.items() if v[0] >= top - 1.0)
        gr['south_road_end'] = {'northmost_local_y': top, 'cols_within_1m_of_end_x': [end_cols[0], end_cols[-1]] if end_cols else None,
                                'objects_at_end': sorted(set(prof[x][1] for x in end_cols)),
                                'z_at_end': sorted(set(prof[x][2] for x in end_cols)),
                                'width_at_end_m': R(end_cols[-1] - end_cols[0] + 0.5, 2) if end_cols else None}
    # ---------- straight-line support along each passage (current state = negative baseline) ----------
    P = lodinfo[0]['through_clear_x_at_z1.0']
    lanes = []
    for x0, x1 in P:
        if x1 - x0 < 0.6: continue
        xc = (x0 + x1) / 2
        line = []; first = None
        y = strip_ymin + 1.0
        while y >= -140:
            row = [supported_local(xc + dx, y) for dx in (-0.3, -0.15, 0, 0.15, 0.3)]
            ok = all(r is not None for r in row)
            line.append(ok)
            if first is None and y < strip_ymin and ok:
                first = (R(y, 2), sorted(set(r[0] for r in row)), [R(r[1]) for r in row])
            y -= 0.1
        unsup = sum(1 for k in line if not k)
        lanes.append({'passage_x': [x0, x1], 'centre_x': R(xc, 2),
                      'samples_0.1m_from_y=%.2f' % (strip_ymin + 1.0): len(line), 'rows_without_full_0.6m_band_support': unsup,
                      'first_fully_supported_row_south_of_port': first,
                      'gap_from_outer_port_m': R(strip_ymin - first[0], 2) if first else None})
    gr['passage_straight_south_check'] = lanes
    res['gates'][g] = gr

# ---------------- Pingcheng south road itself: vertices near north end, continuity along plan ----------------
road = [o for o in gobjs if o['name'].startswith('C_stitch_primary')]
endv = sorted({(R(v.x, 3), R(v.y, 3), R(v.z, 3)) for o in road for v in o['v'] if -90 < v.y < -55 and abs(v.x - 1622) < 12})
res['pingcheng_road_vertices_world_y-90..-55'] = endv
A = Vector((1622.080627017166, -73.712)); Bp = Vector((1612.245, -1224.49))
L = (Bp - A).length; dirv = (Bp - A).normalized(); nrm = Vector((-dirv.y, dirv.x))
miss = {'centre': 0, 'left_2.7': 0, 'right_2.7': 0}; n = 0; objs = {}
s = 0.0
while s <= L:
    pt = A + dirv * s; n += 1
    for k, off in (('centre', 0), ('left_2.7', 2.7), ('right_2.7', -2.7)):
        q = pt + nrm * off; h = ground_hit(q.x, q.y)
        if h is None: miss[k] += 1
        else: objs[h[0]] = objs.get(h[0], 0) + 1
    s += 0.5
res['pingcheng_south_road_plan_continuity_0.5m'] = {'plan_a': list(A), 'plan_b': list(Bp), 'length_m': R(L, 3), 'stations': n,
                                                    'unsupported': miss, 'hit_objects': objs}
# what is just beyond the far (south) end
far = {}
for d in (0.5, 2, 5, 10):
    q = Bp + dirv * d; far[str(d)] = ground_hit(q.x, q.y)
res['pingcheng_south_road_beyond_far_end'] = far

# ---------------- Kaiyang wide search (5 m) for ANY loaded ground south of the wall ----------------
pl = PL['luoyang-kaiyang-gate-study-v1']; O = Vector(pl['engineering_origin_from_existing_wall_caps'])
best = None; cnt = 0
for iy in range(0, 261):
    wy = O.y - 5 * iy
    for ix in range(-120, 121):
        wx = O.x + 5 * ix
        h = ground_hit(wx, wy)
        if h:
            cnt += 1
            d = math.hypot(wx - O.x, wy - O.y)
            if best is None or d < best[0]: best = (d, wx, wy, h[0], h[1])
res['kaiyang_wide_search_5m_x+-600_y0..-1300_from_origin'] = {
    'cells_with_ground': cnt, 'nearest': {'dist_m': R(best[0], 2), 'world_xy': [R(best[1], 2), R(best[2], 2)], 'obj': best[3], 'z': R(best[4])} if best else None}
OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding='utf-8')
print('MEASURE_OK')
