"""LY-026 prep measurement (read-only on inputs).
blender -b --factory-startup --python-exit-code 1 -P measure_well_ops.py -- <glb> <prefix> <out.json> [ox oy oz [place city1.glb city2.glb ...]]
  prefix  : node-name prefix of the well parts, e.g. A_LOD0__ / B_LOD1__
  ox oy oz: well origin in Blender Z-up world (city chunk: 196.286 1952.184 0.2); default 0 0 0
Measures, in well-local coordinates (Z up, metres):
  1 part inventory (bbox)
  2 every operating part (wheel/axle/cheek/rope/container) vs every other mesh:
    surface overlap (BVH tri-tri), vertex containment, vertex-sampled min distance,
    exact-boolean intersection volume for overlapping pairs
  3 container stroke sweep (rigid vertical translation of the container group)
  4 wheel finite rotation sweep about the axle axis
  5 rope strand decomposition, ends, clearances
  6 (city) non-well meshes intruding into the operating envelope; vertical bore rays
All numbers are geometry of the exported GLB; no dynamics, load or water level is modelled.
"""
import bpy, bmesh, sys, json, math, hashlib
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, PFX, OUT = argv[0], argv[1], argv[2]
ORG = Vector([float(v) for v in argv[3:6]]) if len(argv) >= 6 else Vector((0, 0, 0))

PLACE = len(argv) >= 7 and argv[6] == 'place'
EXTRA = argv[7:] if PLACE else []
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
if PLACE:
    # library well at its own origin: move it to ORG once (translation only), then load city GLBs unchanged
    for o in list(bpy.context.scene.objects):
        if o.parent is None:
            o.location = o.location + ORG
    for e in EXTRA:
        bpy.ops.import_scene.gltf(filepath=e)
    bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
T0 = Matrix.Translation(-ORG)


def world_mesh(o, extra=Matrix()):
    """vertices/polys in well-local coords"""
    me = o.evaluated_get(dg).to_mesh()
    M = extra @ T0 @ o.matrix_world
    vs = [M @ v.co for v in me.vertices]
    ps = [tuple(p.vertices) for p in me.polygons]
    o.evaluated_get(dg).to_mesh_clear()
    return vs, ps


objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
well = [o for o in objs if o.name.startswith(PFX)]
other = [o for o in objs if not o.name.startswith(PFX)]
short = lambda o: o.name[len(PFX):] if o.name.startswith(PFX) else o.name
GEO = {o.name: world_mesh(o) for o in objs}


def bvh(name, extra=None):
    vs, ps = GEO[name]
    if extra is not None:
        vs = [extra @ v for v in vs]
    return BVHTree.FromPolygons(vs, ps, epsilon=0.0), vs


BV = {n: bvh(n) for n in GEO}


def bbox(vs):
    xs, ys, zs = zip(*vs)
    return [[min(xs), min(ys), min(zs)], [max(xs), max(ys), max(zs)]]


def r6(x):
    return round(float(x), 6)


def inside_count(tree, vs, step=1):
    """vertices of another mesh lying inside closed mesh `tree` (nearest-face normal test)"""
    c = 0
    for v in vs[::step]:
        loc, nor, idx, d = tree.find_nearest(v)
        if loc is not None and d > 1e-6 and (v - loc).dot(nor) < 0:
            c += 1
    return c


def min_dist(ta, va, tb, vb):
    best = 1e9
    for v in va:
        r = tb.find_nearest(v)
        if r[0] is not None:
            best = min(best, r[3])
    for v in vb:
        r = ta.find_nearest(v)
        if r[0] is not None:
            best = min(best, r[3])
    return best


def bool_volume(na, nb, ea=None):
    """exact boolean intersection volume of two meshes in well-local coords"""
    def mk(n, extra):
        vs, ps = GEO[n]
        if extra is not None:
            vs = [extra @ v for v in vs]
        me = bpy.data.meshes.new('tmp_' + n)
        me.from_pydata([tuple(v) for v in vs], [], ps)
        ob = bpy.data.objects.new('tmp_' + n, me)
        bpy.context.scene.collection.objects.link(ob)
        return ob
    a, b = mk(na, ea), mk(nb, None)
    m = a.modifiers.new('b', 'BOOLEAN'); m.operation = 'INTERSECT'; m.solver = 'EXACT'; m.object = b
    d2 = bpy.context.evaluated_depsgraph_get()
    me = a.evaluated_get(d2).to_mesh()
    bm = bmesh.new(); bm.from_mesh(me)
    vol = bm.calc_volume(signed=False) if len(bm.faces) else 0.0
    nf = len(bm.faces)
    bm.free(); a.evaluated_get(d2).to_mesh_clear()
    for ob in (a, b):
        me_ = ob.data; bpy.data.objects.remove(ob); bpy.data.meshes.remove(me_)
    return vol, nf


def is_op(n):
    s = n[len(PFX):] if n.startswith(PFX) else ''
    return any(k in s for k in ('wheel', 'rope', 'container', 'drawing'))


res = {'extraGLB': [{'path': e, 'sha256': hashlib.sha256(open(e, 'rb').read()).hexdigest()} for e in EXTRA],
       'source': SRC, 'sha256': hashlib.sha256(open(SRC, 'rb').read()).hexdigest(), 'prefix': PFX,
       'wellOriginBlenderZup': list(ORG), 'blender': bpy.app.version_string,
       'meshCount': len(objs), 'wellMeshCount': len(well)}

# 1 inventory
res['parts'] = {short(o): [[r6(c) for c in p] for p in bbox(GEO[o.name][0])] for o in well}

# 2 operating pairs
ops = [o.name for o in well if is_op(o.name)]
pairs = []
for a in ops:
    ta, va = BV[a]
    for o in objs:
        b = o.name
        if b == a or (is_op(b) and b < a):
            continue
        tb, vb = BV[b]
        ba, bb = bbox(va), bbox(vb)
        gap = max(max(ba[0][i] - bb[1][i], bb[0][i] - ba[1][i]) for i in range(3))
        if gap > 0.25:
            continue
        ov = len(ta.overlap(tb))
        ins_ab = inside_count(tb, va)
        ins_ba = inside_count(ta, vb)
        md = min_dist(ta, va, tb, vb)
        row = {'a': short(o) if False else a[len(PFX):], 'b': short(o), 'bboxGap': r6(gap),
               'overlapTriPairs': ov, 'aVertsInsideB': ins_ab, 'bVertsInsideA': ins_ba,
               'minDistVertexSampled': r6(md)}
        if ov or ins_ab or ins_ba:
            vol, nf = bool_volume(a, b)
            row['intersectVolume_m3'] = float('%.6g' % vol)
            row['intersectFaces'] = nf
        pairs.append(row)
res['opPairs'] = pairs

# 3 container stroke
G = [o.name for o in well if any(k in o.name for k in ('container', 'drawing'))]
rope = [o.name for o in well if 'rope' in o.name]
static = [o.name for o in objs if o.name not in G and o.name not in rope]
liner = [o.name for o in well if 'short_liner' in o.name]
gvs = [v for n in G for v in GEO[n][0]]
gb = bbox(gvs)
res['containerGroup'] = {'parts': [n[len(PFX):] for n in G], 'bbox': [[r6(c) for c in p] for p in gb],
                         'maxRadialFromAxis': r6(max(math.hypot(v.x, v.y) for v in gvs))}
if liner:
    lb = bbox(GEO[liner[0]][0])
    res['containerGroup']['linerBottomZ'] = r6(lb[0][2])
stroke = []
dz = -1.0
while dz <= 2.0001:
    M = Matrix.Translation((0, 0, dz))
    hits = []
    mind = 1e9; who = None
    for n in G:
        tg, vg = bvh(n, M)
        for s in static:
            ts, vs = BV[s]
            sb = bbox(vs); gg = bbox(vg)
            gap = max(max(gg[0][i] - sb[1][i], sb[0][i] - gg[1][i]) for i in range(3))
            if gap > 0.3:
                continue
            if tg.overlap(ts):  # surface overlap only; nearest-normal containment is unreliable on hollow parts
                hits.append([n[len(PFX):], s[len(PFX):] if s.startswith(PFX) else s])
            d = min_dist(tg, vg, ts, vs)
            if d < mind:
                mind, who = d, s
    stroke.append({'dz': round(dz, 3), 'bottomZ': r6(gb[0][2] + dz), 'topZ': r6(gb[1][2] + dz),
                   'collisions': hits, 'minClear': r6(mind),
                   'nearest': (who[len(PFX):] if who and who.startswith(PFX) else who)})
    dz += 0.05
res['containerStroke'] = stroke
free = [s for s in stroke if not s['collisions']]
res['containerStrokeFree'] = {'dzMin': free[0]['dz'] if free else None, 'dzMax': free[-1]['dz'] if free else None,
                              'contiguousFromRest': None}
# contiguous interval containing dz=0
idx0 = min(range(len(stroke)), key=lambda i: abs(stroke[i]['dz']))
if not stroke[idx0]['collisions']:
    lo = hi = idx0
    while lo > 0 and not stroke[lo - 1]['collisions']:
        lo -= 1
    while hi < len(stroke) - 1 and not stroke[hi + 1]['collisions']:
        hi += 1
    res['containerStrokeFree']['contiguousFromRest'] = [stroke[lo]['dz'], stroke[hi]['dz']]
    res['containerStrokeFree']['firstBlockBelow'] = stroke[lo - 1] if lo > 0 else None
    res['containerStrokeFree']['firstBlockAbove'] = stroke[hi + 1] if hi < len(stroke) - 1 else None
else:
    res['containerStrokeFree']['restCollisions'] = stroke[idx0]['collisions']

# 3b lift-out: container raised so its bottom clears the highest rim/collar part by 0.03 m, then moved
# horizontally in four local directions; first surface overlap per direction is recorded.
rimparts = [o.name for o in well if any(k in o.name for k in ('rim', 'collar'))]
rim_top = max(v.z for n in rimparts for v in GEO[n][0]) if rimparts else 0.0
dz_exit = rim_top + 0.03 - gb[0][2]
lift = {'rimTopZ': r6(rim_top), 'dzExit': r6(dz_exit), 'directions': {}}
for lab, d in (('-y', (0, -1)), ('+y', (0, 1)), ('-x', (-1, 0)), ('+x', (1, 0))):
    first = None
    s_ = 0.0
    while s_ <= 1.8001:
        M = Matrix.Translation((d[0] * s_, d[1] * s_, dz_exit))
        hit = []
        for n in G:
            tg, vg = bvh(n, M)
            for st in static:
                ts, vs = BV[st]
                if tg.overlap(ts):
                    hit.append(st[len(PFX):] if st.startswith(PFX) else st)
        if hit:
            first = {'shift': round(s_, 3), 'hits': sorted(set(hit))}
            break
        s_ += 0.05
    lift['directions'][lab] = first or {'shift': None, 'clearTo': 1.8}
res['liftOut'] = lift

# 4 wheel rotation
axle = [o.name for o in well if 'wheel_axle' in o.name]
W = [o.name for o in well if any(k in o.name for k in ('wheel_grooved_ring', 'wheel_hub', 'wheel_spoke'))]
if axle:
    ab = bbox(GEO[axle[0]][0])
    ext = [ab[1][i] - ab[0][i] for i in range(3)]
    ax = ext.index(max(ext))
    axis = Vector([1 if i == ax else 0 for i in range(3)])
    ctr = Vector([(ab[0][i] + ab[1][i]) / 2 for i in range(3)])
    res['axle'] = {'axisIndex': ax, 'center': [r6(c) for c in ctr], 'length': r6(ext[ax]),
                   'diameter': r6(sorted(ext)[1])}
    rot = []
    targets = [o.name for o in objs if o.name not in W and o.name not in rope]
    for deg in range(0, 360, 15):
        R = Matrix.Translation(ctr) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-ctr)
        hits = []
        for n in W:
            tw, vw = bvh(n, R)
            for s in targets:
                ts, vs = BV[s]
                sb = bbox(vs); wb = bbox(vw)
                gap = max(max(wb[0][i] - sb[1][i], sb[0][i] - wb[1][i]) for i in range(3))
                if gap > 0.05:
                    continue
                if tw.overlap(ts):
                    hits.append([n[len(PFX):], s[len(PFX):] if s.startswith(PFX) else s])
        rot.append({'deg': deg, 'contacts': sorted(map(list, {tuple(h) for h in hits}))})
    res['wheelRotation'] = rot

# 5 rope strands
strands = []
for n in rope:
    vs, ps = GEO[n]
    # union-find over polygons
    par = list(range(len(vs)))
    # glTF export splits vertices by normal/UV: weld by position (1e-5 m) before grouping
    key = {}
    for i, v in enumerate(vs):
        k = (round(v.x, 5), round(v.y, 5), round(v.z, 5))
        if k in key:
            par[i] = key[k]
        else:
            key[k] = i
    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    for p in ps:
        for j in p[1:]:
            a, b = f(p[0]), f(j)
            if a != b:
                par[a] = b
    groups = {}
    for i in range(len(vs)):
        groups.setdefault(f(i), []).append(vs[i])
    for g in groups.values():
        b = bbox(g)
        low = min(g, key=lambda v: v.z)
        strands.append({'node': n[len(PFX):], 'verts': len(g), 'bbox': [[r6(c) for c in p] for p in b],
                        'lowestPoint': [r6(low.x), r6(low.y), r6(low.z)],
                        'lowestRadialFromAxis': r6(math.hypot(low.x, low.y))})
res['ropeStrands'] = strands

# 6 city neighbourhood
if other:
    env_r = max(abs(c) for p in res['parts'].values() for c in (p[0][0], p[0][1], p[1][0], p[1][1]))
    intr = []
    for o in other:
        t, vs = BV[o.name]
        inside = [v for v in vs if math.hypot(v.x, v.y) <= env_r and -1.0 <= v.z <= 4.0]
        b = bbox(vs)
        near = b[0][0] <= env_r and b[1][0] >= -env_r and b[0][1] <= env_r and b[1][1] >= -env_r
        if not near:
            continue
        hitsw = []
        for w in well:
            tw, vw = BV[w.name]
            if tw.overlap(t):
                hitsw.append(short(w))
        intr.append({'node': o.name, 'bbox': [[r6(c) for c in p] for p in b], 'vertsInEnvelopeCyl': len(inside),
                     'surfaceOverlapWithWellParts': hitsw})
    res['cityNeighbours'] = {'envelopeRadius': r6(env_r), 'rows': intr}

# vertical rays through bore (all hits along each ray, from z=+1.5 down 5 m; rope/container excluded)
rays = []
skip = set(G) | set(rope)
for r_ in (0.0, 0.2, 0.3, 0.4, 0.44, 0.62, 0.75, 0.9, 1.2, 1.7):
    for ang in (0, 90, 180, 270):
        x, y = r_ * math.cos(math.radians(ang)), r_ * math.sin(math.radians(ang))
        d_ = Vector((0, 0, -1))
        hits = []
        for o in objs:
            if o.name in skip:
                continue
            t, _ = BV[o.name]
            o_ = Vector((x, y, 1.5)); left = 5.0
            while left > 0:
                loc, nor, idx, dist = t.ray_cast(o_, d_, left)
                if loc is None:
                    break
                hits.append([short(o), r6(loc.z)])
                o_ = loc + d_ * 1e-5; left -= dist + 1e-5
        hits.sort(key=lambda h: -h[1])
        rays.append({'r': r_, 'deg': ang, 'hitsTopDown': hits[:8]})
        if r_ == 0.0:
            break
res['boreRays'] = rays

json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE', OUT)
