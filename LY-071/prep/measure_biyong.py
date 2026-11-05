# LY-071 prep: measure Biyong hall A and enclosure L GLBs (read-only inputs).
# blender -b --factory-startup --python-exit-code 1 -P measure_biyong.py -- <out.json> <glb>...
# Reports in glTF frame: x = Blender X, y = Blender Z (up), z = -Blender Y.
import bpy, bmesh, sys, json, hashlib, os
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
out_path, glbs = argv[0], argv[1:]


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def g(v):  # blender -> gltf
    return [round(v.x, 5), round(v.z, 5), round(-v.y, 5)]


def load(p):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=p)
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bm = bmesh.new()
    info = []
    for o in objs:
        me = o.data
        tmp = bmesh.new()
        tmp.from_mesh(me)
        tmp.transform(o.matrix_world)
        mw = o.matrix_world
        ident = all(abs(mw[i][j] - (1 if i == j else 0)) < 1e-9 for i in range(4) for j in range(4))
        info.append({'name': o.name, 'parent': o.parent.name if o.parent else None,
                     'verts': len(me.vertices), 'polys': len(me.polygons),
                     'materials': [m.name for m in me.materials if m],
                     'matrixWorldIsIdentity': ident,
                     'location_gltf': g(mw.to_translation())})
        me2 = bpy.data.meshes.new('t')
        tmp.to_mesh(me2)
        bm.from_mesh(me2)
        tmp.free()
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bm.normal_update()
    return bm, info


def levels(bm, sign):
    acc = {}
    for f in bm.faces:
        n = f.normal
        if n.z * sign > 0.999:
            z = round(sum(v.co.z for v in f.verts) / 3, 3)
            acc[z] = acc.get(z, 0) + f.calc_area()
    return sorted([[k, round(a, 3)] for k, a in acc.items()], key=lambda t: -t[1])


def bbox(bm):
    xs = [v.co for v in bm.verts]
    lo = Vector((min(c.x for c in xs), min(c.y for c in xs), min(c.z for c in xs)))
    hi = Vector((max(c.x for c in xs), max(c.y for c in xs), max(c.z for c in xs)))
    return lo, hi


def top_hit(tree, x, y, ztop=50.0):
    loc, nrm, idx, d = tree.ray_cast(Vector((x, y, ztop)), Vector((0, 0, -1)))
    return None if loc is None else loc.z


def scan(tree, p0, p1, n, report):
    """walk n+1 samples from p0 to p1 (blender xy); report(x,y)->coordinate label; keep changes only"""
    pts = []
    last = 'init'
    for i in range(n + 1):
        t = i / n
        x = p0[0] + (p1[0] - p0[0]) * t
        y = p0[1] + (p1[1] - p0[1]) * t
        h = top_hit(tree, x, y)
        h = None if h is None else round(h, 3)
        if h != last:
            pts.append([round(report(x, y), 3), h])
            last = h
    return pts


res = {'tool': 'measure_biyong.py', 'blender': bpy.app.version_string,
       'frame': 'glTF as stored in GLB (x, y up, z); no city N applied', 'files': {}}
trees = {}
for p in glbs:
    name = os.path.basename(p)
    bm, info = load(p)
    lo, hi = bbox(bm)
    tree = BVHTree.FromBMesh(bm)
    trees[name] = tree
    r = {'path': p, 'sha256': sha(p), 'bytes': os.path.getsize(p), 'objects': info,
         'tris': len(bm.faces),
         'bboxMin_gltf': [round(lo.x, 4), round(lo.z, 4), round(-hi.y, 4)],
         'bboxMax_gltf': [round(hi.x, 4), round(hi.z, 4), round(-lo.y, 4)],
         'upLevels_y_area': levels(bm, 1)[:25], 'downLevels_y_area': levels(bm, -1)[:12]}
    if name.startswith('biyong'):
        N = 1200
        r['axisProfiles_r_y'] = {
            '+x': scan(tree, (0, 0), (24, 0), N, lambda x, y: x),
            '-x': scan(tree, (0, 0), (-24, 0), N, lambda x, y: -x),
            '+z_gltf': scan(tree, (0, 0), (0, -24), N, lambda x, y: -y),
            '-z_gltf': scan(tree, (0, 0), (0, 24), N, lambda x, y: y)}
        r['offAxisProfile_+x_at_gltfz6'] = scan(tree, (0, -6), (24, -6), N, lambda x, y: x)
        lat = {}
        for rr in (20.6, 21.0, 21.5, 22.0, 23.0):
            lat[str(rr)] = scan(tree, (rr, -8), (rr, 8), 800, lambda x, y: -y)
        r['lateralScan_+x_report_gltfZ'] = lat
    if name.startswith('enclosure'):
        sc = {}
        for t in (3.9, 4.0, 4.05, 10.0, 36.0, 60.0, 66.0, 68.0):
            # arm along gltf x near gltf z=-68 (blender y=+68): scan blender y 58..70 at blender x=t
            a = scan(tree, (t, 58), (t, 70), 1000, lambda x, y: -y)
            # arm along gltf z near gltf x=68: scan blender x 58..70 at blender y=t
            b = scan(tree, (58, t), (70, t), 1000, lambda x, y: x)
            sc[str(t)] = {'armZ-68_scan_gltfZ_at_gltfX=t': a, 'armX68_scan_gltfX_at_gltfZ=-t': b}
        r['armCrossScans'] = sc
        # along-arm scans at mid-thickness, to find openings
        r['alongArmScans'] = {}
        for label, p0, p1, rep in (('armZ_at_blY67.5', (0, 67.5), (70, 67.5), lambda x, y: x),
                                   ('armX_at_blX67.5', (67.5, 0), (67.5, 70), lambda x, y: -y),
                                   ('diag', (0, 0), (70, 70), lambda x, y: x)):
            r['alongArmScans'][label] = scan(tree, p0, p1, 7000, rep)
        step = 0.25
        nx = int((hi.x - lo.x) / step) + 1
        ny = int((hi.y - lo.y) / step) + 1
        occ = 0
        cells = 0
        hist = {}
        for i in range(nx):
            for j in range(ny):
                h = top_hit(tree, lo.x + i * step + 0.01, lo.y + j * step + 0.01)
                cells += 1
                if h is not None:
                    occ += 1
                    k = round(h, 2)
                    hist[k] = hist.get(k, 0) + 1
        r['occupancyGrid0.25'] = {'cells': cells, 'hit': occ, 'hitArea_m2': occ * step * step,
                                  'topHeightHistogram': sorted(hist.items(), key=lambda t: -t[1])[:10]}
    res['files'][name] = r
    bm.free()

ov = {}
for a in [k for k in trees if k.startswith('biyong')]:
    for b in [k for k in trees if k.startswith('enclosure')]:
        ov[a + '|' + b] = {'triPairOverlaps': len(trees[a].overlap(trees[b]))}
res['identityOverlay'] = ov
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print('WROTE', out_path)
