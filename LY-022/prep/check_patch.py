# LY-022 acceptance checker (prep stage). Read-only on inputs; never exports geometry.
# usage:
#   blender -b --factory-startup --python-exit-code 1 -P check_patch.py -- <chunk.glb> <frozen.json> <out.json> --selftest
#   blender -b --factory-startup --python-exit-code 1 -P check_patch.py -- <chunk.glb> <frozen.json> <out.json> --patch <patch.glb> [--ports ports.json]
# frozen.json = prep/frozen-baseline.json (fingerprints measured on chunk 0193ebc0...). Ports are PROVISIONAL until LY-006 freezes them.
# Selftest builds in-memory fixture meshes only (nothing is written to disk except the report).
import bpy, sys, json, bmesh, math, hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
chunk, frozen_p, out = a[0], a[1], a[2]
selftest = '--selftest' in a
patch_p = a[a.index('--patch') + 1] if '--patch' in a else None
CX, CZ = 214.286, -1959.184
TOL_PLAN, TOL_H = 0.005, 0.002
frozen = json.load(open(frozen_p, encoding='utf-8'))
HOLE = frozen['wellOpening']  # centreGLTF [x,z], rMax, clearance
KEEP = tuple(frozen['keptPrefixes'])

def g2b(X, Y, Z): return Vector((X, -Z, Y))
def fp(o):
    M = o.matrix_world
    vs = sorted({(round((M @ v.co).x, 4), round((M @ v.co).z, 4), round(-(M @ v.co).y, 4)) for v in o.data.vertices})
    return hashlib.sha256(json.dumps(vs).encode()).hexdigest()
def tree(objs):
    bm = bmesh.new()
    for o in objs:
        t = bmesh.new(); t.from_mesh(o.data); t.transform(o.matrix_world)
        me = bpy.data.meshes.new('tmp'); t.to_mesh(me); t.free(); bm.from_mesh(me); bpy.data.meshes.remove(me)
    tr = BVHTree.FromBMesh(bm); bm.free(); return tr

def load_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=chunk)
    return {o.name: o for o in bpy.data.objects if o.type == 'MESH'}

def box(name, x0, x1, y0, y1, z0, z1):
    """glTF-coordinate axis box fixture (x east, y up, z)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        X = x0 if v.co.x < 0 else x1; Y = y0 if v.co.z < 0 else y1; Z = z0 if v.co.y < 0 else z1
        v.co = g2b(X, Y, Z)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)  # mapping mirrors handedness; restore outward normals
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); return o

def check(scene, patch, ports, mutate=None):
    if mutate: mutate(scene)
    R = {}
    # 1 fingerprints of kept nodes
    bad = [n for n, h in frozen['fingerprints'].items() if n not in scene or fp(scene[n]) != h]
    R['F1_keptFingerprintsUnchanged'] = {'pass': not bad, 'changedOrMissing': bad}
    pt = tree(patch)
    # 2 well opening: no patch surface within rMax+clearance column
    cx, cz = HOLE['centreGLTF']; rr = HOLE['rMax'] + HOLE['clearance']
    hits = []
    for ang in range(0, 360, 10):
        for r in (0.0, rr * 0.5, rr):
            X = cx + r * math.cos(math.radians(ang)); Z = cz + r * math.sin(math.radians(ang))
            h = pt.ray_cast(g2b(X, 5.0, Z), Vector((0, 0, -1)), 10)
            if h[0] is not None: hits.append([round(X, 3), round(Z, 3), round(h[0].z, 3)])
    R['F2_wellOpeningClear'] = {'pass': not hits, 'hits': hits[:10]}
    # 3 no paving over existing route tops / no stacked layer; support on ground
    rt = tree([o for n, o in scene.items() if n.startswith('route_')])
    gt = tree([scene['C_market_ground_well_A']])
    ft = tree([o for n, o in scene.items() if n.startswith('C_MARKET_ENTRY')])
    over_route, floating, over_ground, into_front = [], [], 0, []
    for o in patch:
        M = o.matrix_world
        for f in o.data.polygons:
            c = M @ f.center; nrm = (M.to_3x3() @ f.normal).normalized()
            if nrm.z < -0.99:  # bottom faces: support + overlay class
                h = rt.ray_cast(c + Vector((0, 0, 0.001)), Vector((0, 0, -1)), 0.05)
                if h[0] is not None: over_route.append([round(c.x, 3), round(-c.y, 3), round(c.z, 4)])
                g = gt.ray_cast(c + Vector((0, 0, 0.001)), Vector((0, 0, -1)), 0.5)
                if g[0] is None or c.z - g[0].z > TOL_H:
                    if h[0] is None: floating.append([round(c.x, 3), round(-c.y, 3), round(c.z, 4)])
                elif h[0] is None: over_ground += 1
            for v in f.vertices:
                w = M @ o.data.vertices[v].co
                hit = ft.ray_cast(Vector((w.x, w.y, max(w.z, 0.2) + 0.6)), Vector((0, 0, -1)), 0.6 + max(w.z, 0.2) - 0.2)
                if hit[0] is not None and hit[0].z > 0.205 and hit[0].z <= w.z + 0.001:
                    into_front.append([round(w.x, 3), round(-w.y, 3)])
    R['F3_noRoutePaving'] = {'pass': not over_route, 'bottomFacesOverRoute': over_route[:10]}
    R['F4_supportedNoFloat'] = {'pass': not floating, 'floatingBottomFaces': floating[:10]}
    R['F5_groundOverlayFaces'] = {'count': over_ground, 'note': 'overlay-on-ground class; allowed only if LY-006 rule says so', 'pass': over_ground == 0 or frozen.get('allowGroundOverlay', False)}
    R['F6_noShopFrontIntrusion'] = {'pass': not into_front, 'verts': into_front[:10]}
    # 7 port endpoints: each port segment must be matched by patch edge verts within tol (plan) and top height
    pr = []
    for p in ports:
        (x0, z0), (x1, z1), y = p['a'], p['b'], p['topY']
        L = math.hypot(x1 - x0, z1 - z0); ok = 0; n = max(2, int(L / 0.25))
        for i in range(n + 1):
            t = TOL_PLAN / L + (1 - 2 * TOL_PLAN / L) * i / n  # endpoints inset by plan tolerance
            X = x0 + (x1 - x0) * t; Z = z0 + (z1 - z0) * t
            h = pt.ray_cast(g2b(X - p['inward'][0] * 0.01, y + 0.5, Z - p['inward'][1] * 0.01), Vector((0, 0, -1)), 1.0)
            if h[0] is not None and abs(h[0].z - y) <= TOL_H: ok += 1
        pr.append({'id': p['id'], 'samples': n + 1, 'matched': ok, 'pass': ok == n + 1})
    R['F7_portsMatched'] = {'pass': all(x['pass'] for x in pr) if pr else None, 'ports': pr}
    R['pass'] = all(v.get('pass') in (True, None) for k, v in R.items() if isinstance(v, dict))
    return R

PORTS = frozen['provisionalPorts']
report = {'chunk': chunk, 'frozen': frozen_p, 'tolerances': {'plan': TOL_PLAN, 'height': TOL_H}}
if selftest:
    cases = {}
    # positive: flush 0.01 m filler band on ground between route_public north edge and shop row, top 0.21, outside hole
    def pos(): return [box('LY022_fix_pos', CX - 20, CX + 20, 0.20, 0.21, CZ + 2.0, CZ + 2.6)]
    def neg_hole(): return [box('LY022_fix_hole', CX - 18.6, CX - 17.4, 0.20, 0.21, CZ + 6.4, CZ + 7.6)]
    def neg_route(): return [box('LY022_fix_route', CX - 20, CX + 20, 0.21, 0.22, CZ + 1.0, CZ + 2.6)]
    def neg_float(): return [box('LY022_fix_float', CX - 20, CX + 20, 0.25, 0.26, CZ + 2.0, CZ + 2.6)]
    def neg_port(): return [box('LY022_fix_port', CX - 20, CX + 20, 0.20, 0.21, CZ + 2.05, CZ + 2.6)]
    def neg_front(): return [box('LY022_fix_front', CX - 10, CX - 9, 0.20, 0.45, CZ + 4.5, CZ + 5.6)]
    def mut_route(s):
        o = s['route_public']; o.data.vertices[0].co.x += 0.01
    for name, mk, mut in [('positive', pos, None), ('neg_well_cover', neg_hole, None), ('neg_route_paving', neg_route, None),
                          ('neg_floating', neg_float, None), ('neg_port_gap_5cm', neg_port, None), ('neg_shop_intrusion', neg_front, None),
                          ('neg_route_fingerprint_moved', pos, mut_route)]:
        sc = load_scene(); P = mk(); bpy.context.view_layer.update()
        ports = [p for p in PORTS if p['id'] == 'P-route_public-N-edge-x[-20,20]']
        cases[name] = check(sc, P, ports, mut)
        cases[name]['expect'] = 'pass' if name == 'positive' else 'fail'
        cases[name]['asExpected'] = cases[name]['pass'] == (name == 'positive')
    report['selftest'] = cases
    report['selftestAllAsExpected'] = all(c['asExpected'] for c in cases.values())
elif patch_p:
    sc = load_scene(); before = set(bpy.data.objects.keys())
    bpy.ops.import_scene.gltf(filepath=patch_p)
    P = [o for o in bpy.data.objects if o.name not in before and o.type == 'MESH']
    ports = json.load(open(a[a.index('--ports') + 1], encoding='utf-8')) if '--ports' in a else PORTS
    report['patch'] = patch_p
    report['patchSha256'] = hashlib.sha256(open(patch_p, 'rb').read()).hexdigest()
    report['result'] = check(sc, P, ports)
json.dump(report, open(out, 'w', encoding='utf-8'), indent=1)
print('OK', report.get('selftestAllAsExpected', report.get('result', {}).get('pass')))
