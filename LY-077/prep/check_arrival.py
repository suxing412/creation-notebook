# LY-077 acceptance harness (prepared before G; runs unchanged at production time).
# Read-only on all inputs. Builds NOTHING that is delivered: the "synthetic:*" patches are
# in-memory fixtures that only exist to prove the checker can tell pass from fail.
#
# blender -b --factory-startup --python-exit-code 1 -P check_arrival.py -- \
#     --a <Taixue A GLB> --a-sha <expected sha256> \
#     --patch <arrival-ground GLB | none | synthetic:ok | synthetic:raised | synthetic:gap | synthetic:intrude> \
#     [--patch-sha <sha256>] [--patch-keep NODE] [--port X,Z] [--port-y Y] [--out report.json] [--label text]
#
# Frame: Taixue A local-study frame, glTF axes (X east, Y up, Z south), metres.
# A v3.2 facts this harness relies on (measured in prep, all three LODs identical):
#   flights centred x = -10.5 / 1.5 / 10.5, width 2.2 m, foot line z = 4.85,
#   three 0.20 m risers (ground 0.00 -> 0.20 -> 0.40 -> 0.60 platform), tread depth 0.35 m.
import bpy, bmesh, sys, json, hashlib, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index('--') + 1:]
opt = {}
i = 0
while i < len(a):
    opt[a[i].lstrip('-')] = a[i + 1]
    i += 2
A_PATH = opt['a']; A_SHA = opt.get('a-sha')
PATCH = opt.get('patch', 'none'); PATCH_SHA = opt.get('patch-sha')
PX, PZ = [float(v) for v in opt.get('port', '1.5,8.0').split(',')]
PORT_Y = float(opt.get('port-y', '0.0'))
OUT = opt.get('out'); LABEL = opt.get('label', PATCH)

FLIGHTS = [(-10.5, -11.6, -9.4), (1.5, 0.4, 2.6), (10.5, 9.4, 11.6)]
FOOT_Z = 4.85; RISER = 0.20; GROUND = 0.0
TOL_Y = 0.003          # support height tolerance (m), same as v3.2 check
LOWER = 0.015          # prism floor lift above walking surface (m), same as v3.2 check
BODY_W = 0.8; BODY_H = 1.8
PAD_DEPTH = 1.2        # depth of the required support pad in front of each flight (m)
STEP = 0.1

sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
def b(x, y, z): return Vector((x, -z, y))           # glTF -> Blender
def g(v): return (v.x, v.z, -v.y)                  # Blender -> glTF

def geom_hash(objs):
    keys = []
    for o in objs:
        o.data.calc_loop_triangles()
        ws = [o.matrix_world @ v.co for v in o.data.vertices]
        for t in o.data.loop_triangles:
            keys.append(tuple(sorted(tuple(round(c, 4) for c in g(ws[j])) for j in t.vertices)))
    keys.sort()
    h = hashlib.sha256()
    for k in keys: h.update(repr(k).encode())
    return h.hexdigest(), len(keys)

def mat_snapshot(objs):
    return {o.name: [round(c, 9) for row in o.matrix_world for c in row] for o in objs}

def import_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before and o.type == 'MESH']

def box_obj(name, x0, x1, y0, y1, z0, z1):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        gx = x0 if v.co.x < 0 else x1; gy = y0 if v.co.z < 0 else y1; gz = z0 if -v.co.y < 0 else z1
        v.co = b(gx, gy, gz)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); return o

def synthetic(kind):
    # in-memory fixtures only; never exported
    if kind == 'ok':
        return [box_obj('FIXTURE_ok', -19.0, 19.0, -0.4, 0.0, 3.8, 9.5)]
    if kind == 'raised':
        return [box_obj('FIXTURE_raised', -19.0, 19.0, -0.4, 0.05, 3.8, 9.5)]
    if kind == 'gap':
        return [box_obj('FIXTURE_gapW', -19.0, 3.0, -0.4, 0.0, 3.8, 9.5),
                box_obj('FIXTURE_gapE', 9.0, 19.0, -0.4, 0.0, 3.8, 9.5)]
    if kind == 'intrude':   # ground poking 0.1 m up into the west flight volume
        return [box_obj('FIXTURE_flat', -19.0, 19.0, -0.4, 0.0, 3.8, 9.5),
                box_obj('FIXTURE_bump', -11.0, -10.0, 0.0, 0.1, 4.55, 4.8)]
    raise SystemExit('unknown synthetic ' + kind)

bpy.ops.wm.read_factory_settings(use_empty=True)
R = {'checker_sha256': sha(__file__) if '__file__' in dir() else None, 'label': LABEL, 'frame': 'Taixue A local-study, glTF X east/Y up/Z south, m',
     'constants': {'flights': FLIGHTS, 'footZ': FOOT_Z, 'riser': RISER, 'groundY': GROUND, 'tolY': TOL_Y,
                   'lower': LOWER, 'body': [BODY_W, BODY_H], 'padDepth': PAD_DEPTH, 'step': STEP},
     'port': {'x': PX, 'z': PZ, 'y': PORT_Y}, 'checks': {}, 'pass': None}
C = R['checks']

# ---- 1. A identity (before install)
a_sha = sha(A_PATH)
A = import_glb(A_PATH)
C['A_sha_matches_expected'] = {'actual': a_sha, 'expected': A_SHA, 'ok': (A_SHA is None) or a_sha == A_SHA}
a_hash0, a_tris = geom_hash(A); a_mat0 = mat_snapshot(A)
R['A'] = {'path': A_PATH, 'sha256': a_sha, 'triangles': a_tris, 'geometryHash': a_hash0, 'objects': sorted(o.name for o in A)}

# ---- 2. install patch
if PATCH == 'none':
    P = []
elif PATCH.startswith('synthetic:'):
    P = synthetic(PATCH.split(':', 1)[1])
else:
    p_sha = sha(PATCH)
    C['patch_sha_matches_expected'] = {'actual': p_sha, 'expected': PATCH_SHA, 'ok': (PATCH_SHA is None) or p_sha == PATCH_SHA}
    P = import_glb(PATCH)
    keep = opt.get('patch-keep')
    if keep:   # evaluate only one named node of a multi-node source (e.g. old v1 A_presentation_ground)
        for o in [o for o in P if o.name != keep]:
            bpy.data.objects.remove(o, do_unlink=True)
        P = [o for o in bpy.data.objects if o.type == 'MESH' and o.name == keep]
        C['patch_keep'] = {'node': keep, 'found': len(P) == 1, 'ok': len(P) == 1}
R['patch'] = {'source': PATCH, 'objects': sorted(o.name for o in P)}
a_hash1, _ = geom_hash(A)
C['A_unchanged_after_install'] = {'ok': a_hash1 == a_hash0 and mat_snapshot(A) == a_mat0}

ALL = A + P
V, F, TRI = [], [], []
for o in ALL:
    o.data.calc_loop_triangles(); base = len(V)
    ws = [o.matrix_world @ v.co for v in o.data.vertices]; V += ws
    for t in o.data.loop_triangles:
        F.append(tuple(base + j for j in t.vertices))
        vv = [ws[j] for j in t.vertices]
        TRI.append((o.name, vv, [min(v[k] for v in vv) for k in range(3)], [max(v[k] for v in vv) for k in range(3)]))
bvh = BVHTree.FromPolygons(V, F, all_triangles=True) if F else None

def support(x, z, expect, y0=None, dist=0.6):
    if bvh is None: return False, None
    y0 = expect + 0.3 if y0 is None else y0
    loc = bvh.ray_cast(b(x, y0, z), Vector((0, 0, -1)), dist)[0]
    if loc is None: return False, None
    return abs(loc.z - expect) <= TOL_Y, round(loc.z, 4)

def clip(poly, ax, val, sign):
    out = []
    for p, q in zip(poly, poly[1:] + poly[:1]):
        dp = (p[ax] - val) * sign; dq = (q[ax] - val) * sign
        if dp >= 0: out.append(p)
        if (dp >= 0) != (dq >= 0): out.append(p + (q - p) * (dp / (dp - dq)))
    return out

def prism_hits(lo_g, hi_g, tris=None):
    tris = TRI if tris is None else tris
    # lo/hi in glTF -> Blender AABB
    lo = Vector((lo_g[0], -hi_g[2], lo_g[1])); hi = Vector((hi_g[0], -lo_g[2], hi_g[1]))
    hits = []
    for name, vv, mn, mx in tris:
        if any(mx[d] <= lo[d] + 1e-6 or mn[d] >= hi[d] - 1e-6 for d in range(3)): continue
        poly = vv[:]
        for d in range(3):
            poly = clip(poly, d, lo[d], 1) if poly else []
            poly = clip(poly, d, hi[d], -1) if poly else []
        if len(poly) > 2 and sum((poly[j] - poly[0]).cross(poly[j + 1] - poly[0]).length for j in range(1, len(poly) - 1)) > 1e-8:
            hits.append(name)
    return hits

# ---- 3. pad support in front of every flight + riser match
pads = []
for cx, x0, x1 in FLIGHTS:
    n = fail = 0; heights = set()
    z = FOOT_Z + 0.01
    while z <= FOOT_Z + PAD_DEPTH + 1e-9:
        x = x0 + 0.05
        while x <= x1 - 0.05 + 1e-9:
            ok, h = support(x, z, GROUND); n += 1; fail += (not ok)
            if h is not None: heights.add(round(h, 3))
            x += STEP
        z += STEP
    t_ok, t_h = support(cx, FOOT_Z - 0.175, RISER)       # first tread top
    first_riser = None if (t_h is None or not heights) else round(t_h - max(heights), 4)
    pads.append({'flight_cx': cx, 'probes': n, 'failures': fail, 'groundHeights': sorted(heights),
                 'firstTreadTop': t_h, 'firstRiser': first_riser,
                 'riserOk': first_riser is not None and abs(first_riser - RISER) <= TOL_Y})
C['pads'] = {'items': pads, 'ok': all(p['failures'] == 0 and p['riserOk'] for p in pads)}

# ---- 4. port support and lateral convergence routes (port -> each flight foot), L-shaped
routes = []
pk, ph = support(PX, PZ, PORT_Y)
C['port_support'] = {'ok': pk, 'height': ph, 'expected': PORT_Y}
for cx, x0, x1 in FLIGHTS:
    foot = (cx, FOOT_Z + 0.05)
    legs = [((PX, PZ), (cx, PZ)), ((cx, PZ), foot)]
    probes = fail = 0; hits = []; maxjump = 0.0; prev = None
    for (ax_, az_), (bx_, bz_) in legs:
        L = math.hypot(bx_ - ax_, bz_ - az_)
        if L < 1e-9: continue
        lo = [min(ax_, bx_) - BODY_W / 2, GROUND + LOWER, min(az_, bz_) - BODY_W / 2]
        hi = [max(ax_, bx_) + BODY_W / 2, GROUND + LOWER + BODY_H, max(az_, bz_) + BODY_W / 2]
        # clip the prism at the foot line so it does not count the first riser itself
        hi[2] = max(hi[2], lo[2]); lo[2] = max(lo[2], FOOT_Z + 0.0001)
        hits += prism_hits(lo, hi)
        nx, nz = -(bz_ - az_) / L, (bx_ - ax_) / L
        steps = math.ceil(L / STEP)
        for s in range(steps + 1):
            t = s / steps
            for lat in (-0.39, 0.0, 0.39):
                x = ax_ + (bx_ - ax_) * t + nx * lat; z = az_ + (bz_ - az_) * t + nz * lat
                ok, h = support(x, z, GROUND); probes += 1; fail += (not ok)
                if lat == 0.0 and h is not None:
                    if prev is not None: maxjump = max(maxjump, abs(h - prev))
                    prev = h
    routes.append({'flight_cx': cx, 'legs': legs, 'supportProbes': probes, 'supportFailures': fail,
                   'prismIntrusions': len(hits), 'intrudingObjects': sorted(set(hits)), 'maxCentreHeightJump': round(maxjump, 4)})
C['routes'] = {'items': routes, 'ok': pk and all(r['supportFailures'] == 0 and r['prismIntrusions'] == 0 and r['maxCentreHeightJump'] <= TOL_Y for r in routes)}

# ---- 5. patch must not enter A's solid (positive-volume intrusion into platform / flights)
solids = [([-18.8, 0.0, -3.8], [18.8, 0.6, 3.8])]
for cx, x0, x1 in FLIGHTS:
    for k in range(3):
        solids.append(([x0, 0.0, FOOT_Z - 0.35 * (k + 1)], [x1, RISER * (k + 1), FOOT_Z - 0.35 * k]))
TRI_P = [t for t in TRI if t[0] in {o.name for o in P}]
inset = 0.001
intr = 0
for lo, hi in solids:
    lo2 = [lo[0] + inset, lo[1] + inset, lo[2] + inset]; hi2 = [hi[0] - inset, hi[1] - inset, hi[2] - inset]
    intr += len(prism_hits(lo2, hi2, TRI_P))
C['patch_into_A_solid'] = {'trianglesInside': intr, 'ok': intr == 0,
                           'note': 'Face contact at y=0 under footprint / at riser faces is legal contact; only clipped area strictly inside (1 mm inset) counts.'}

# ---- 6. withdraw: delete patch, A must be byte-identical in geometry and matrices
for o in P: bpy.data.objects.remove(o, do_unlink=True)
a_hash2, _ = geom_hash(A)
C['A_unchanged_after_withdraw'] = {'ok': a_hash2 == a_hash0 and mat_snapshot(A) == a_mat0}

R['pass'] = all(v.get('ok') for v in C.values())
s = json.dumps(R, indent=1)
if OUT: open(OUT, 'w').write(s)
print('RESULT', LABEL, 'PASS' if R['pass'] else 'FAIL', {k: v.get('ok') for k, v in C.items()})
