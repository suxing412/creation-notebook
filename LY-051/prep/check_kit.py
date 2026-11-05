# LY-051 prep: acceptance checker for the stable tether / partition kit (draft, run during production).
# It never writes any GLB. In --selftest mode it builds in-memory probe boxes (test fixtures, NOT delivery
# geometry, never exported) and verifies that every check fires on the intended negatives.
#
# Usage:
#   blender -b --factory-startup --python-exit-code 1 -P check_kit.py -- \
#       --host <A.glb|B.glb> --variant A|B --zones <LY-006 zones.json> --out <report.json> \
#       [--kit <kit.glb>] [--selftest]
#
# Frames: LY-006 zones / ports are in glTF-native local:stable-A|B (x, y-up, z; open front = +z).
# Blender import maps glTF (x, y, z) -> Blender (x, -z, y). All checks run in Blender coords and
# zone boxes are converted once (box_gltf_to_blender).
import bpy, bmesh, sys, json, hashlib, argparse, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument('--host', required=True); ap.add_argument('--variant', required=True, choices=['A', 'B'])
ap.add_argument('--zones', required=True); ap.add_argument('--out', required=True)
ap.add_argument('--kit'); ap.add_argument('--selftest', action='store_true')
a = ap.parse_args(argv)

HOST_SHA = {'A': '672beeb46faaee0a15f7de649099c486c639b40a39b045b89525fbe7f15b2563',
            'B': 'bd82280a76f0677821788c62c39b42e8fb2314d297bbad704a92aa7d452c2cb4'}
TOL_CONTACT = 0.002      # surface contact gap
TOL_ZONE = 0.002         # zone boundary tolerance
VOL_EPS = 1e-6           # m3, positive intrusion threshold
GRID = 0.005             # m, volume sampling step
TOL_PORT_POS, TOL_PORT_ELEV = 0.005, 0.002   # LY-006 ports.json stable:partition-footprint:mount

def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
def r(v, n=4): return round(v, n)

def box_gltf_to_blender(b):
    (x0, y0, z0), (x1, y1, z1) = b
    return [x0, -z1, y0], [x1, -z0, y1]

def world_bm(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world); return bm

def bvh(o):
    bm = world_bm(o); t = BVHTree.FromBMesh(bm); bm.free(); return t

def aabb(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return [min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)]

def inside(tree, p, lo, hi):
    if any(p[i] < lo[i] - 1e-9 or p[i] > hi[i] + 1e-9 for i in range(3)): return False
    d = Vector((1.0, 0.0137, 0.0071)).normalized(); n = 0; o = p.copy()
    for _ in range(64):
        h = tree.ray_cast(o, d)
        if h[0] is None: break
        n += 1; o = h[0] + d * 1e-6
    return n % 2 == 1

def fingerprint(objs):
    fp = {}
    for o in sorted(objs, key=lambda o: o.name):
        m = [r(v, 6) for row in o.matrix_world for v in row]
        vs = b''.join(('%.6f,%.6f,%.6f;' % tuple(v.co)).encode() for v in o.data.vertices)
        fp[o.name] = hashlib.sha256(json.dumps(m).encode() + vs + ','.join(
            s.material.name if s.material else '-' for s in o.material_slots).encode()).hexdigest()
    return fp

# ---------- load host ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
host_sha = sha(a.host)
report = {"variant": a.variant, "host": a.host, "hostSha256": host_sha,
          "hostShaBound": host_sha == HOST_SHA[a.variant], "checks": {}, "limits": [
              "surface BVH + 5 mm grid parity sampling; not an exhaustive solid collision proof",
              "geometry only: animal size, tether strength, partition load, animal suitability NOT verified",
              "no browser / GPU run"]}
bpy.ops.import_scene.gltf(filepath=a.host)
host = [o for o in bpy.context.scene.objects if o.type == 'MESH']
for o in bpy.context.scene.objects: o['ly051_host'] = 1
H = {o.name: o for o in host}
HB = {n: aabb(o) for n, o in H.items()}
HT = {n: bvh(o) for n, o in H.items()}
fp_before = fingerprint(host)
P = a.variant + '_'
posts = [n for n in H if '_post_' in n]
front = sorted([n for n in posts if HB[n][0][1] < 0], key=lambda n: HB[n][0][0])
troughs = sorted([n for n in H if 'trough' in n], key=lambda n: HB[n][0][0])
wall = [n for n in H if 'rear_wall' in n][0]
plat = [n for n in H if 'platform' in n][0]
interior_axes = [r((HB[n][0][0] + HB[n][1][0]) / 2, 3) for n in front[1:-1]]
report["hostInteriorPostAxesX"] = interior_axes

zones = json.load(open(a.zones, encoding='utf-8'))['zones']
my_zone = [z for z in zones if z['seat'] == 'LY-051' and z['frame'] == 'local:stable-' + a.variant][0]
ZLO, ZHI = box_gltf_to_blender(my_zone['box'])
report["zone"] = {"id": my_zone['zoneId'], "gltfBox": my_zone['box'], "blenderBox": [ZLO, ZHI]}

# trough cavity boxes (measured: horizontal rays from centre at z=0.5 + downward ray)
cav = {}
for n in troughs:
    lo, hi = HB[n]; c = Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, 0.5))
    ext = []
    for d in [Vector((1, 0, 0)), Vector((-1, 0, 0)), Vector((0, 1, 0)), Vector((0, -1, 0))]:
        h = HT[n].ray_cast(c, d); ext.append(h[0])
    bot = HT[n].ray_cast(Vector((c.x, c.y, hi[2] + 1)), Vector((0, 0, -1)))[0]
    cav[n] = ([ext[1].x, ext[3].y, bot.z], [ext[0].x, ext[2].y, hi[2]])
report["troughCavities"] = {n: [[r(v) for v in b[0]], [r(v) for v in b[1]]] for n, b in cav.items()}

# entrance slabs: between front-post inner faces, through the post depth, z 0.05..2.70
slabs = []
for i in range(len(front) - 1):
    lo_a, hi_a = HB[front[i]]; lo_b, hi_b = HB[front[i + 1]]
    slabs.append(([hi_a[0] + TOL_CONTACT, lo_a[1], 0.05], [lo_b[0] - TOL_CONTACT, hi_a[1], 2.70]))

def box_hits(objlo, objhi, blo, bhi):
    return all(objlo[i] < bhi[i] and objhi[i] > blo[i] for i in range(3))

def check_kit(kit_objs, footprints=None):
    res = {"parts": {}, "fail": []}
    kit_trees = {o.name: bvh(o) for o in kit_objs}
    kit_boxes = {o.name: aabb(o) for o in kit_objs}
    contacts = {o.name: set() for o in kit_objs}
    for o in kit_objs:
        lo, hi = kit_boxes[o.name]; part = {"aabb": [[r(v) for v in lo], [r(v) for v in hi]]}
        # C3 zone containment (all vertices)
        bad = [tuple(r(x) for x in (o.matrix_world @ v.co)) for v in o.data.vertices
               if any((o.matrix_world @ v.co)[i] < ZLO[i] - TOL_ZONE or (o.matrix_world @ v.co)[i] > ZHI[i] + TOL_ZONE for i in range(3))]
        part["outsideZoneVerts"] = len(bad)
        if bad: res["fail"].append(f"{o.name}: {len(bad)} vertices outside {my_zone['zoneId']} (e.g. {bad[0]})")
        # C4 contact / intrusion / containment vs host
        part["host"] = {}
        for n, t in HT.items():
            hlo, hhi = HB[n]
            if not box_hits([lo[i] - TOL_CONTACT for i in range(3)], [hi[i] + TOL_CONTACT for i in range(3)], hlo, hhi): continue
            ov = len(kit_trees[o.name].overlap(t))
            # nearest distance from kit verts to host surface
            dmin = min((t.find_nearest(o.matrix_world @ v.co)[3] for v in o.data.vertices), default=9)
            # volume sampling in intersection of boxes
            ilo = [max(lo[i], hlo[i]) for i in range(3)]; ihi = [min(hi[i], hhi[i]) for i in range(3)]
            vol = 0.0; kin = 0; tot = 0
            if all(ihi[i] - ilo[i] > GRID for i in range(3)):
                nx, ny, nz = [max(1, int((ihi[i] - ilo[i]) / GRID)) for i in range(3)]
                for ix in range(nx):
                    for iy in range(ny):
                        for iz in range(nz):
                            p = Vector((ilo[0] + (ix + .5) * (ihi[0] - ilo[0]) / nx, ilo[1] + (iy + .5) * (ihi[1] - ilo[1]) / ny,
                                        ilo[2] + (iz + .5) * (ihi[2] - ilo[2]) / nz))
                            if inside(kit_trees[o.name], p, lo, hi):
                                tot += 1
                                if inside(t, p, hlo, hhi): kin += 1
                cell = (ihi[0] - ilo[0]) * (ihi[1] - ilo[1]) * (ihi[2] - ilo[2]) / (nx * ny * nz); vol = kin * cell
            cls = None
            if vol > VOL_EPS:
                cls = "positive-intrusion"
            elif dmin <= TOL_CONTACT or ov:
                cls = "surface-contact"
            if cls:
                part["host"][n] = {"class": cls, "bvhPairs": ov, "minDist": r(dmin, 5), "intrusionVol_m3": r(vol, 7)}
                if cls == "surface-contact": contacts[o.name].add(n)
                else: res["fail"].append(f"{o.name} x {n}: positive intrusion {vol:.6f} m3")
        # full containment inside a host object (kit vertices all inside)
        for n, t in HT.items():
            hlo, hhi = HB[n]
            if box_hits(lo, hi, hlo, hhi) and all(inside(t, o.matrix_world @ v.co, hlo, hhi) for v in o.data.vertices):
                res["fail"].append(f"{o.name}: fully contained in {n}")
        # C6 trough cavity
        for n, (clo, chi) in cav.items():
            if box_hits(lo, hi, [clo[0] + 1e-4, clo[1] + 1e-4, clo[2] + 1e-4], [chi[0] - 1e-4, chi[1] - 1e-4, chi[2] - 1e-4]):
                res["fail"].append(f"{o.name}: enters cavity of {n}")
        # C7 entrance slab
        for i, (slo, shi) in enumerate(slabs):
            if box_hits(lo, hi, slo, shi): res["fail"].append(f"{o.name}: blocks entrance of bay {i}")
        res["parts"][o.name] = part
    # kit-kit contacts (support chain)
    names = list(kit_trees)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            if kit_trees[names[i]].overlap(kit_trees[names[j]]) or min(
                    (kit_trees[names[j]].find_nearest(bpy.data.objects[names[i]].matrix_world @ v.co)[3]
                     for v in bpy.data.objects[names[i]].data.vertices), default=9) <= TOL_CONTACT:
                contacts[names[i]].add('kit:' + names[j]); contacts[names[j]].add('kit:' + names[i])
    # C5 support: every part must reach a host support through contacts
    anchors = {n for n in H if n != plat}   # platform top is LY-052's floor layer (y<0.05): not reachable by LY-051
    supported = {k for k, c in contacts.items() if c & anchors}
    changed = True
    while changed:
        changed = False
        for k, c in contacts.items():
            if k not in supported and any(x.startswith('kit:') and x[4:] in supported for x in c):
                supported.add(k); changed = True
    for k in contacts:
        res["parts"][k]["supports"] = sorted(contacts[k])
        if k not in supported: res["fail"].append(f"{k}: floating (no contact chain to host post / rear wall / trough)")
    # C11 partition axes must sit on host interior post axes
    for o in kit_objs:
        if 'partition' in o.name:
            lo, hi = kit_boxes[o.name]; cx = (lo[0] + hi[0]) / 2
            if min(abs(cx - x) for x in interior_axes) > TOL_PORT_POS:
                res["fail"].append(f"{o.name}: axis x={cx:.3f} not on host interior post axes {interior_axes} (port mismatch)")
    # C9 footprint port values (if supplied): x, z(local gltf) and elevation y
    if footprints is not None:
        for fpt in footprints:
            o = bpy.data.objects.get(fpt['part'])
            if o is None: res["fail"].append(f"footprint {fpt['part']}: part missing"); continue
            lo, hi = aabb(o)
            gx, gz, gy = (lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, lo[2]
            if abs(gx - fpt['x']) > TOL_PORT_POS or abs(gz - fpt['z']) > TOL_PORT_POS or abs(gy - fpt['y']) > TOL_PORT_ELEV:
                res["fail"].append(f"footprint {fpt['part']}: declared {fpt} vs measured x={gx:.3f} z={gz:.3f} y={gy:.3f}")
    res["pass"] = not res["fail"]
    return res

def mkbox(name, lo, hi, root):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0);
    for v in bm.verts:
        v.co = Vector([lo[i] + (v.co[i] + 0.5) * (hi[i] - lo[i]) for i in range(3)])
    bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    o.parent = root; return o

def mkroot(name):
    e = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(e); e['requires'] = 'm-luoyang-stable/' + a.variant; return e

def remove_root(root):
    for c in list(root.children): bpy.data.objects.remove(c, do_unlink=True)
    bpy.data.objects.remove(root, do_unlink=True)

if a.kit:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=a.kit)
    kit = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    report["kit"] = {"path": a.kit, "sha256": sha(a.kit), "bytes": len(open(a.kit, 'rb').read()), "meshes": len(kit)}
    report["checks"]["kit"] = check_kit(kit)
    report["checks"]["hostUnchangedAfterImport"] = fingerprint(host) == fp_before

if a.selftest:
    # probe geometry derived from measured host numbers; Blender coords (x bay, y depth with +y rear, z up)
    ax = interior_axes[len(interior_axes) // 2] if len(interior_axes) % 2 else interior_axes[-1]
    fy_in = HB[front[0]][1][1]                      # front post inner face y (A -1.85, B -2.15)
    ry_in = -fy_in                                   # rear post inner face y
    wy = HB[wall][0][1]                              # rear wall front face
    tb = sorted(troughs, key=lambda n: abs((HB[n][0][0] + HB[n][1][0]) / 2 - (ax - 1.4 if a.variant == 'A' else ax - 1.5)))[0]
    tcx = (HB[tb][0][0] + HB[tb][1][0]) / 2
    other = 'B' if a.variant == 'A' else 'A'
    cases = {
        "P1_partition_post_to_post": ([("partition_P1", [ax - .05, fy_in, .05], [ax + .05, ry_in, 1.2])], True),
        "P2_tether_peg_on_rear_wall": ([("tether_P2", [tcx - .04, wy - .06, .95], [tcx + .04, wy, 1.03])], True),
        "P3_peg_plus_ring_chain": ([("tether_P3a", [tcx - .04, wy - .06, .95], [tcx + .04, wy, 1.03]),
                                    ("tether_P3b", [tcx - .02, wy - .10, .97], [tcx + .02, wy - .06, 1.01])], True),
        "N1_peg_in_trough_cavity": ([("tether_N1", [tcx - .04, HB[tb][0][1] + .25, .30], [tcx + .04, HB[tb][0][1] + .33, .40])], False),
        "N2_floating_partition": ([("partition_N2", [ax - .05, fy_in + .05, .05], [ax + .05, ry_in - .05, 1.2])], False),
        "N3_thick_partition_intrudes_posts": ([("partition_N3", [ax - .15, fy_in - .05, .05], [ax + .15, ry_in + .05, 1.2])], False),
        "N4_partition_below_zone_on_platform": ([("partition_N4", [ax - .05, fy_in, 0.0], [ax + .05, ry_in, 1.2])], False),
        "N5_bar_across_entrance": ([("tether_N5", [HB[front[0]][1][0], fy_in - .12, 1.0], [HB[front[1]][0][0], fy_in - .06, 1.1])], False),
        "N6_wrong_variant_axis": ([("partition_N6", [(1.4 if a.variant == 'B' else 3.0) - .05, fy_in, .05],
                                   [(1.4 if a.variant == 'B' else 3.0) + .05, ry_in, 1.2])], False),
        "N7_bad_footprint_port": ([("partition_N7", [ax - .05, fy_in, .05], [ax + .05, ry_in, 1.2])], False),
    }
    st = {}
    for k, (boxes, expect) in cases.items():
        root = mkroot('LY051_probe_' + k)
        objs = [mkbox(n, lo, hi, root) for n, lo, hi in boxes]
        fps = [{"part": "partition_N7", "x": ax, "z": 0.0, "y": 0.0}] if k.startswith('N7') else None
        res = check_kit(objs, fps)
        remove_root(root)
        st[k] = {"expectPass": expect, "pass": res["pass"], "ok": res["pass"] == expect, "fail": res["fail"]}
    # N8 host mutation must be detected
    o = H[wall]; m0 = o.matrix_world.copy(); o.location.z += 0.001; bpy.context.view_layer.update()
    st["N8_host_matrix_change_detected"] = {"ok": fingerprint(host) != fp_before}
    o.matrix_world = m0; bpy.context.view_layer.update()
    st["T4.3_host_restored_after_probe_removal"] = {"ok": fingerprint(host) == fp_before}
    report["selftest"] = st
    report["selftestAllOk"] = all(v["ok"] for v in st.values())

report["hostFingerprint"] = fp_before
json.dump(report, open(a.out, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('CHECKED', a.out, 'selftestAllOk=%s' % report.get('selftestAllOk'))
