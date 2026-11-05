# LY-023 prep: read-only foot/ground contact measurement for existing stalls/sheds.
# Usage:
#   blender -b --factory-startup --python-exit-code 1 -P measure_stall_feet.py -- \
#       --glb MAIN.glb --mode named|loose --out OUT.json [--ground G1.glb G2.glb ...] [--tol 0.005]
#       [--datum Z] [--no-sample-ground]
# named: feet = nodes matching ^T\d_(leg|canopypost); ground = *sample_ground* + every --ground GLB.
# loose: merged meshes split into connected islands; feet = slim vertical islands; ground = broad flat islands
#        + every --ground GLB; canopies = broad thin islands high above ground.
# Coordinates reported in Blender world (X east, Y north, Z up) and glTF (x, y_up, z=-north).
# Writes only OUT.json. Never saves .blend, never exports.
import bpy, bmesh, sys, json, re, math, hashlib, os
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
def arg(name, default=None, multi=False):
    if name not in argv: return default
    i = argv.index(name) + 1
    if not multi: return argv[i]
    out = []
    while i < len(argv) and not argv[i].startswith('--'): out.append(argv[i]); i += 1
    return out
GLB = arg('--glb'); MODE = arg('--mode', 'named'); OUT = arg('--out')
GROUNDS = arg('--ground', [], multi=True); TOL = float(arg('--tol', '0.005'))
NO_SAMPLE = '--no-sample-ground' in argv  # named mode: measure only against the --ground GLBs (e.g. frozen LY-022 ground)
DATUM = arg('--datum')  # loose mode with no ground mesh: horizontal plane z=DATUM (Blender Z) stands in for the selected ground
PERSON = 0.6; HEAD = 1.8   # person envelope from data/west/market-flow-plan.json; headroom = C test value

def sha(p):
    h = hashlib.sha256(); h.update(open(p, 'rb').read()); return h.hexdigest()

bpy.ops.wm.read_factory_settings(use_empty=True)
def imp(path, tag):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    objs = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    for o in objs: o['__src'] = tag
    return objs
main_objs = imp(GLB, 'main')
ground_objs = []
for g in GROUNDS: ground_objs += imp(g, os.path.basename(g))
dg = bpy.context.evaluated_depsgraph_get()

def parts_of(obj, split):
    """Return list of parts: dict(name, verts[Vector], faces[[idx]], mat)."""
    me = obj.evaluated_get(dg).to_mesh(); M = obj.matrix_world
    V = [M @ v.co for v in me.vertices]
    F = [list(p.vertices) for p in me.polygons]
    FM = [obj.material_slots[p.material_index].material.name if obj.material_slots and obj.material_slots[p.material_index].material else '' for p in me.polygons]
    if not split:
        return [dict(name=obj.name, verts=V, faces=F, mats=sorted(set(FM)))]
    # union-find over face-connected vertices, plus coincident-position welding (1e-5)
    parent = list(range(len(V)))
    def find(a):
        while parent[a] != a: parent[a] = parent[parent[a]]; a = parent[a]
        return a
    def uni(a, b):
        a, b = find(a), find(b)
        if a != b: parent[a] = b
    for f in F:
        for k in range(1, len(f)): uni(f[0], f[k])
    key = {}
    for i, v in enumerate(V):
        k = (round(v.x, 5), round(v.y, 5), round(v.z, 5))
        if k in key: uni(i, key[k])
        else: key[k] = i
    groups = {}
    for fi, f in enumerate(F): groups.setdefault(find(f[0]), []).append(fi)
    out = []
    for gi, (root, fis) in enumerate(groups.items()):
        vids = sorted({v for fi in fis for v in F[fi]}); remap = {v: i for i, v in enumerate(vids)}
        out.append(dict(name=f'{obj.name}#island{gi}', verts=[V[v] for v in vids],
                        faces=[[remap[v] for v in F[fi]] for fi in fis], mats=sorted({FM[fi] for fi in fis})))
    return out

def bbox(p):
    xs = [v.x for v in p['verts']]; ys = [v.y for v in p['verts']]; zs = [v.z for v in p['verts']]
    return [min(xs), min(ys), min(zs)], [max(xs), max(ys), max(zs)]

def bvh(parts):
    V = []; F = []
    for p in parts:
        o = len(V); V += p['verts']; F += [[o + i for i in f] for f in p['faces']]
    return BVHTree.FromPolygons(V, F) if F else None

def face_area_normal(p, f):
    # float64 fan relative to first vertex (mathutils is float32; absolute city coords ~2000 m lose the area)
    vs = [tuple(float(c) for c in p['verts'][i]) for i in f]; o = vs[0]; nx = ny = nz = 0.0
    for i in range(1, len(vs) - 1):
        ax, ay, az = (vs[i][k] - o[k] for k in range(3)); bx, by, bz = (vs[i + 1][k] - o[k] for k in range(3))
        nx += ay * bz - az * by; ny += az * bx - ax * bz; nz += ax * by - ay * bx
    L = math.sqrt(nx * nx + ny * ny + nz * nz); a = L / 2
    return a, (Vector((nx / L, ny / L, nz / L)) if L > 0 else Vector((0, 0, 0)))

def pip(x, y, poly):
    c = False; j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]; xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-30) + xi: c = not c
        j = i
    return c

def r3(v): return [round(float(x), 4) for x in v]
def gltf(v): return r3([v[0], v[2], -v[1]])

# ---- classify
all_main = []
for o in main_objs: all_main += parts_of(o, MODE == 'loose')
for p in all_main: p['bb'] = bbox(p)
grounds = []
for o in ground_objs: grounds += parts_of(o, False)
feet = []; canopies = []; tables = []; routes = []
if MODE == 'named':
    for p in all_main:
        n = p['name']
        if 'sample_ground' in n:
            if not NO_SAMPLE: grounds.append(p)
        elif re.match(r'^T\d_(leg|canopypost)', n): feet.append(p)
        elif re.match(r'^T\d_canopy$', n): canopies.append(p)
        elif re.match(r'^T\d_table$', n): tables.append(p)
        elif n.startswith('route_'): routes.append(p)
else:
    for p in all_main:
        (x0, y0, z0), (x1, y1, z1) = p['bb']; dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
        if min(dx, dy) <= 0.4 and max(dx, dy) <= 2.0 and dz >= 0.35 and dz > max(dx, dy) * 0.4: feet.append(p)  # posts, legs, slab trestles
        elif dx * dy >= 4 and dz <= 0.6 and z0 <= 0.25: grounds.append(p)
        elif 1.5 <= dx * dy <= 12 and z0 >= 1.5 and dz <= 1.0: canopies.append(p)   # stall/shed canopy, not shop roofs
        elif 1.0 <= dx * dy <= 12 and 0.6 <= z0 <= 1.3 and dz <= 0.2: tables.append(p)
    # keep only feet standing under a stall canopy footprint (shop posts excluded)
    def under(f, c):
        (a0, b0, _), (a1, b1, _) = f['bb']; (c0, d0, _), (c1, d1, _) = bbox(c)
        x, y = (a0 + a1) / 2, (b0 + b1) / 2; return c0 - 0.05 <= x <= c1 + 0.05 and d0 - 0.05 <= y <= d1 + 0.05
    feet = [f for f in feet if any(under(f, c) for c in canopies)]
    for c in canopies: c['tag'] = 'C%02d@%.2f,%.2f' % (canopies.index(c), (bbox(c)[0][0] + bbox(c)[1][0]) / 2, (bbox(c)[0][1] + bbox(c)[1][1]) / 2)
if not grounds and DATUM is not None:
    z = float(DATUM); xs = [v for p in all_main for v in (p['bb'][0][0], p['bb'][1][0])]; ys = [v for p in all_main for v in (p['bb'][0][1], p['bb'][1][1])]
    grounds.append(dict(name='DATUM_PLANE_z=%s(not a mesh in the GLB)' % DATUM, verts=[Vector((min(xs) - 1, min(ys) - 1, z)), Vector((max(xs) + 1, min(ys) - 1, z)),
                    Vector((max(xs) + 1, max(ys) + 1, z)), Vector((min(xs) - 1, max(ys) + 1, z))], faces=[[0, 1, 2, 3]], mats=[]))
GB = bvh(grounds); CB = bvh(canopies); TB = bvh(tables)
groundZmin = min((bbox(g)[0][2] for g in grounds), default=None)

def surf_below(x, y, ztop):
    if GB is None: return None
    hit = GB.ray_cast(Vector((x, y, ztop)), Vector((0, 0, -1)), 50)
    return hit[0].z if hit[0] is not None else None

res = []
for p in feet:
    (x0, y0, z0), (x1, y1, z1) = p['bb']
    bfaces = []; barea = 0.0
    for f in p['faces']:
        a, n = face_area_normal(p, f)
        if n.z < -0.9 and all(abs(p['verts'][i].z - z0) < 1e-3 for i in f): bfaces.append(f); barea += a
    polys = [[(p['verts'][i].x, p['verts'][i].y) for i in f] for f in bfaces]
    N = 9; samples = []
    for i in range(N):
        for j in range(N):
            x = x0 + (x1 - x0) * (i + 0.5) / N; y = y0 + (y1 - y0) * (j + 0.5) / N
            if any(pip(x, y, q) for q in polys): samples.append((x, y))
    gaps = []
    for (x, y) in samples:
        gz = surf_below(x, y, z0 + 3.0)
        gaps.append(None if gz is None else z0 - gz)
    valid = [g for g in gaps if g is not None]
    inside = [g for g in valid if abs(g) <= TOL]
    frac = len(inside) / len(samples) if samples else 0.0
    cls = ('no_ground' if not valid else 'contact' if frac >= 0.999 else 'partial_contact' if inside
           else 'floating' if min(valid) > TOL else 'embedded' if max(valid) < -TOL else 'mixed_no_contact')
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    top = None
    if CB is not None or TB is not None:
        B = TB if (TB is not None and ('_leg' in p['name'] or (MODE == 'loose' and z1 - z0 < 1.5))) else CB
        if B is not None:
            ups = []
            for i in range(5):
                for j in range(5):
                    x = x0 + (x1 - x0) * (i + 0.5) / 5; y = y0 + (y1 - y0) * (j + 0.5) / 5
                    h = B.ray_cast(Vector((x, y, z1 - 0.01)), Vector((0, 0, 1)), 10)
                    ups.append(None if h[0] is None else h[0].z - z1)
            v = [u for u in ups if u is not None]
            top = dict(member='table' if B is TB else 'canopy', samples=25, hits=len(v),
                       up_gap_min=None if not v else round(min(v), 4), up_gap_max=None if not v else round(max(v), 4),
                       touch_fraction=round(sum(1 for u in v if abs(u) <= TOL) / 25, 4))
    res.append(dict(name=p['name'], mats=p['mats'], bbox_min=r3(p['bb'][0]), bbox_max=r3(p['bb'][1]),
                    gltf_center_bottom=gltf((cx, cy, z0)), height=round(z1 - z0, 4),
                    bottom_z=round(z0, 4), bottom_face_area_m2=round(barea, 5), samples=len(samples),
                    gap_min=None if not valid else round(min(valid), 4), gap_max=None if not valid else round(max(valid), 4),
                    contact_fraction=round(frac, 4), contact_area_m2=round(barea * frac, 5), status=cls, top=top))

# ---- under-canopy passage (named mode: per stall prefix; loose: per canopy island)
passage = []
def seg_rect_dist(a, b, r):
    # min 2D distance between segment ab and axis rect r=(x0,y0,x1,y1) (sampled)
    best = 1e9
    for k in range(41):
        t = k / 40; x = a[0] + (b[0] - a[0]) * t; y = a[1] + (b[1] - a[1]) * t
        dx = max(r[0] - x, 0, x - r[2]); dy = max(r[1] - y, 0, y - r[3]); best = min(best, math.hypot(dx, dy))
    return best
for c in canopies:
    (cx0, cy0, cz0), (cx1, cy1, cz1) = bbox(c)
    mine = [f for f in res if cx0 - 0.05 <= (f['bbox_min'][0] + f['bbox_max'][0]) / 2 <= cx1 + 0.05
            and cy0 - 0.05 <= (f['bbox_min'][1] + f['bbox_max'][1]) / 2 <= cy1 + 0.05]
    if MODE == 'named': mine = [f for f in res if f['name'].split('_')[0] == c['name'].split('_')[0]]
    posts = [f for f in mine if ('leg' not in f['name'] if MODE == 'named' else f['height'] >= 1.5)]
    if MODE == 'named': tb = [t for t in tables if t['name'].split('_')[0] == c['name'].split('_')[0]]
    else: tb = [t for t in tables if cx0 - 0.05 <= (bbox(t)[0][0] + bbox(t)[1][0]) / 2 <= cx1 + 0.05 and cy0 - 0.05 <= (bbox(t)[0][1] + bbox(t)[1][1]) / 2 <= cy1 + 0.05]
    gz = surf_below((cx0 + cx1) / 2, (cy0 + cy1) / 2, cz0 - 0.01)
    # canopy underside at centre
    hu = CB.ray_cast(Vector(((cx0 + cx1) / 2, (cy0 + cy1) / 2, (gz or 0) + 0.05)), Vector((0, 0, 1)), 10) if CB else (None,)
    entry = dict(canopy=c.get('tag', c['name']), posts=len(posts), legs=len(mine) - len(posts), canopy_bbox=[r3([cx0, cy0, cz0]), r3([cx1, cy1, cz1])], feet=[f['name'] for f in mine],
                 ground_z_centre=None if gz is None else round(gz, 4),
                 headroom_centre=None if (hu[0] is None or gz is None) else round(hu[0].z - gz, 4))
    # clear gaps from table rectangle to each post footprint (x and y), opening widths between adjacent posts
    if tb:
        (tx0, ty0, _), (tx1, ty1, tz1) = bbox(tb[0]); entry['table_bbox'] = [r3([tx0, ty0]), r3([tx1, ty1])]
        gaps = []
        for f in posts:
            fx0, fy0, _ = f['bbox_min']; fx1, fy1, _ = f['bbox_max']
            gx = max(tx0 - fx1, fx0 - tx1, 0); gy = max(ty0 - fy1, fy0 - ty1, 0)
            gaps.append(dict(foot=f['name'], clear_dx=round(gx, 4), clear_dy=round(gy, 4)))
        entry['table_to_post_clear'] = gaps
        sides = dict(west=round(tx0 - cx0, 4), east=round(cx1 - tx1, 4), south=round(ty0 - cy0, 4), north=round(cy1 - ty1, 4))
        entry['table_to_canopy_edge'] = sides
    if len(posts) >= 2:
        xs = sorted({round((f['bbox_min'][0] + f['bbox_max'][0]) / 2, 3) for f in posts})
        ys = sorted({round((f['bbox_min'][1] + f['bbox_max'][1]) / 2, 3) for f in posts})
        w = max(f['bbox_max'][0] - f['bbox_min'][0] for f in posts); d = max(f['bbox_max'][1] - f['bbox_min'][1] for f in posts)
        entry['post_column_x'] = xs; entry['post_row_y'] = ys
        entry['clear_between_posts_x'] = [round(xs[i + 1] - xs[i] - w, 4) for i in range(len(xs) - 1)]
        entry['clear_between_posts_y'] = [round(ys[i + 1] - ys[i] - d, 4) for i in range(len(ys) - 1)]
    if routes:
        rd = []
        for r in routes:
            # route mesh vertices projected; centreline approximated by its bbox long axis
            (rx0, ry0, _), (rx1, ry1, _) = bbox(r)
            for f in mine:
                rect = (f['bbox_min'][0], f['bbox_min'][1], f['bbox_max'][0], f['bbox_max'][1])
                ov = not (rx1 < rect[0] or rx0 > rect[2] or ry1 < rect[1] or ry0 > rect[3])
                if ov: rd.append(dict(route=r['name'], foot=f['name'], route_bbox_overlaps_foot=True))
        entry['route_bbox_overlaps'] = rd
    passage.append(entry)

summary = {}
for f in res: summary[f['status']] = summary.get(f['status'], 0) + 1
out = dict(tool='LY-023/prep/measure_stall_feet.py', blender=bpy.app.version_string, mode=MODE, tol_m=TOL,
           person_envelope_m=PERSON, headroom_test_m=HEAD,
           inputs=[dict(path=GLB, sha256=sha(GLB), role='main')] + [dict(path=g, sha256=sha(g), role='ground') for g in GROUNDS],
           ground_parts=[dict(name=g['name'], bbox=[r3(bbox(g)[0]), r3(bbox(g)[1])]) for g in grounds],
           feet_count=len(res), status_summary=summary, feet=res, canopies=passage)
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE', OUT, summary, 'feet', len(res), 'canopies', len(passage), 'grounds', len(grounds))
