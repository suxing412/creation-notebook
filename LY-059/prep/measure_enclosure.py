# LY-059 prep: measure a courtyard GLB's outer enclosure, openings, thresholds and clearances.
# Read-only on inputs. Usage:
#   D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P measure_enclosure.py -- in.glb out.json [label]
# Coordinates reported in Blender Z-up after glTF import: X = gltf X, Y = -gltf Z, Z = gltf Y (height).
import bpy, bmesh, sys, json, hashlib, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
src, out = argv[0], argv[1]
label = argv[2] if len(argv) > 2 else src

sha = hashlib.sha256(open(src, 'rb').read()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
dg = bpy.context.evaluated_depsgraph_get()
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']

objs = []
allverts, alltris = [], []
per_obj_bvh = {}
lo = Vector((1e18,) * 3); hi = Vector((-1e18,) * 3)
for o in meshes:
    bm = bmesh.new(); bm.from_object(o, dg); bm.transform(o.matrix_world)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.verts.ensure_lookup_table()
    vs = [v.co.copy() for v in bm.verts]
    ts = [[v.index for v in f.verts] for f in bm.faces]
    olo = Vector(map(min, *[v for v in vs])) if vs else Vector()
    ohi = Vector(map(max, *[v for v in vs])) if vs else Vector()
    lo = Vector(map(min, lo, olo)); hi = Vector(map(max, hi, ohi))
    mats = [m.name for m in o.data.materials if m]
    # loose parts
    parts = []
    seen = set()
    for v in bm.verts:
        if v.index in seen: continue
        stack = [v]; comp = []
        seen.add(v.index)
        while stack:
            c = stack.pop(); comp.append(c.co)
            for e in c.link_edges:
                w = e.other_vert(c)
                if w.index not in seen:
                    seen.add(w.index); stack.append(w)
        plo = Vector(map(min, *comp)) if len(comp) > 1 else comp[0].copy()
        phi = Vector(map(max, *comp)) if len(comp) > 1 else comp[0].copy()
        parts.append({'lo': [round(x, 3) for x in plo], 'hi': [round(x, 3) for x in phi], 'n': len(comp)})
    objs.append({'name': o.name, 'materials': mats, 'tris': len(ts),
                 'lo': [round(x, 4) for x in olo], 'hi': [round(x, 4) for x in ohi],
                 'looseParts': len(parts), 'partsSample': sorted(parts, key=lambda p: -p['n'])[:40]})
    per_obj_bvh[o.name] = BVHTree.FromPolygons(vs, ts)
    base = len(allverts)
    allverts += vs; alltris += [[a + base, b + base, c + base] for a, b, c in ts]
    bm.free()

bvh = BVHTree.FromPolygons(allverts, alltris)


def hit_obj(p, d, dist):
    best = None
    for n, t in per_obj_bvh.items():
        h = t.ray_cast(p, d, dist)
        if h[0] is not None and (best is None or h[3] < best[1]):
            best = (n, h[3], h[0])
    return best


floor_z = lo.z
res = {'label': label, 'file': src.replace('\\', '/'), 'sha256': sha, 'bbox': {'lo': list(lo), 'hi': list(hi)},
       'objects': objs, 'note': 'Blender Z-up; heights are absolute Z of the GLB (gltf Y).'}

# ---- 1. perimeter opening scan: horizontal rays from 1.0 m outside the bbox, inward, depth <= 1.5 m
heights = [0.15, 0.5, 1.0, 1.6, 2.0, 2.4]
step = 0.05
sides = {
    'south(-Y)': (Vector((0, -1, 0)), 'x', lo.y),
    'north(+Y)': (Vector((0, 1, 0)), 'x', hi.y),
    'west(-X)': (Vector((-1, 0, 0)), 'y', lo.x),
    'east(+X)': (Vector((1, 0, 0)), 'y', hi.x),
}
scan = {}
for sname, (nrm, axis, edge) in sides.items():
    a0, a1 = (lo.x, hi.x) if axis == 'x' else (lo.y, hi.y)
    n = int((a1 - a0) / step) + 1
    rows = []
    for i in range(n):
        a = a0 + i * step
        col = []
        for h in heights:
            z = floor_z + h
            if axis == 'x':
                p = Vector((a, edge + nrm.y * 1.0, z))
            else:
                p = Vector((edge + nrm.x * 1.0, a, z))
            d = -nrm
            hh = bvh.ray_cast(p, d, 2.5)  # 1.0 outside + 1.5 into the enclosure band
            col.append(hh[0] is not None)
        rows.append((round(a, 3), col))
    # openings: runs where all heights below 2.0 m are clear (pass-through band)
    gaps = []
    run = None
    for a, col in rows:
        clear = not any(col[:4])  # 0.15..1.6 m clear
        if clear and run is None: run = [a, a]
        elif clear: run[1] = a
        elif run is not None: gaps.append(run); run = None
    if run is not None: gaps.append(run)
    # discard gaps that are just bbox overhang at ends (edge rows where nothing exists)
    scan[sname] = {'samples': n, 'clearRuns_0.15to1.6m': [[g[0], g[1], round(g[1] - g[0] + step, 3)] for g in gaps]}
res['perimeterScan'] = scan

# ---- 2. outer wall band: where does the outermost solid sit on each side (1.0 m height)
band = {}
for sname, (nrm, axis, edge) in sides.items():
    a0, a1 = (lo.x, hi.x) if axis == 'x' else (lo.y, hi.y)
    ds = []
    for i in range(1, 40):
        a = a0 + (a1 - a0) * i / 40
        p = Vector((a, edge + nrm.y * 1.0, floor_z + 1.0)) if axis == 'x' else Vector((edge + nrm.x * 1.0, a, floor_z + 1.0))
        h = hit_obj(p, -nrm, 30)
        if h: ds.append((round(a, 2), h[0], round(h[1] - 1.0, 3)))
    band[sname] = ds
res['outerFaceInsetFromBbox_at1m'] = band

# ---- 3. ground sampling: vertical rays on a 0.5 m grid incl. 2 m apron outside
grid = []
x = lo.x - 2.0
while x <= hi.x + 2.0 + 1e-6:
    y = lo.y - 2.0
    while y <= hi.y + 2.0 + 1e-6:
        h = bvh.ray_cast(Vector((x, y, hi.z + 5)), Vector((0, 0, -1)), 100)
        grid.append((round(x, 2), round(y, 2), None if h[0] is None else round(h[0].z, 4)))
        y += 0.5
    x += 0.5
outside = [g for g in grid if (g[0] < lo.x or g[0] > hi.x or g[1] < lo.y or g[1] > hi.y)]
res['apron2m'] = {'samples': len(outside), 'hits': sum(1 for g in outside if g[2] is not None)}
lowest = {}
for g in grid:
    if g[2] is not None:
        k = round(g[2], 2); lowest[k] = lowest.get(k, 0) + 1
res['topSurfaceHeightHistogram'] = sorted(lowest.items())[:30]

# ---- 4. per-opening probe: threshold, inner/outer ground, head clearance, clear width at 1.0 m
probes = []
for sname, info in scan.items():
    nrm, axis, edge = sides[sname]
    for g in info['clearRuns_0.15to1.6m']:
        mid = (g[0] + g[1]) / 2
        rec = {'side': sname, 'from': g[0], 'to': g[1], 'width_scan': g[2], 'mid': round(mid, 3)}
        prof = []
        for t in [-1.5, -1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0]:
            # t measured inward from bbox edge; negative = outside
            if axis == 'x':
                p = Vector((mid, edge - nrm.y * t, hi.z + 5))
            else:
                p = Vector((edge - nrm.x * t, mid, hi.z + 5))
            h = bvh.ray_cast(p, Vector((0, 0, -1)), 100)
            # floor = lowest surface: cast from just above floor_z+2.5 down for local floor under lintel
            p2 = p.copy(); p2.z = floor_z + 2.2
            h2 = bvh.ray_cast(p2, Vector((0, 0, -1)), 10)
            up = None
            if h2[0] is not None:
                u = bvh.ray_cast(h2[0] + Vector((0, 0, 0.02)), Vector((0, 0, 1)), 20)
                up = None if u[0] is None else round(u[0].z - h2[0].z, 3)
            prof.append({'inward_m': t, 'top': None if h[0] is None else round(h[0].z, 3),
                         'floorBelow2.2': None if h2[0] is None else round(h2[0].z, 3), 'headroom': up})
        rec['profile'] = prof
        probes.append(rec)
res['openingProbes'] = probes
json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('OK', label, sha[:12], 'bbox', [round(v, 3) for v in lo], [round(v, 3) for v in hi])
for s, i in scan.items(): print(s, i['clearRuns_0.15to1.6m'])
