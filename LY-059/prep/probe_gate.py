# LY-059 prep: detailed probe of the gate passage + wall/pier slits of a courtyard GLB.
# Usage: blender -b --factory-startup --python-exit-code 1 -P probe_gate.py -- in.glb out.json gx0 gx1 side
#   gx0,gx1: gate span along X (Blender coords) from measure_enclosure.py; side: S (Blender -Y) or N.
import bpy, bmesh, sys, json, hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
src, out, gx0, gx1, side = argv[0], argv[1], float(argv[2]), float(argv[3]), argv[4]
sha = hashlib.sha256(open(src, 'rb').read()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
dg = bpy.context.evaluated_depsgraph_get()
trees = {}
lo = Vector((1e18,) * 3); hi = Vector((-1e18,) * 3)
parts_near_gate = []
for o in [o for o in bpy.context.scene.objects if o.type == 'MESH']:
    bm = bmesh.new(); bm.from_object(o, dg); bm.transform(o.matrix_world)
    bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.verts.ensure_lookup_table()
    vs = [v.co.copy() for v in bm.verts]; ts = [[v.index for v in f.verts] for f in bm.faces]
    for v in vs:
        lo = Vector(map(min, lo, v)); hi = Vector(map(max, hi, v))
    trees[o.name] = BVHTree.FromPolygons(vs, ts)
    seen = set()
    for v in bm.verts:
        if v.index in seen: continue
        st = [v]; comp = []; seen.add(v.index)
        while st:
            c = st.pop(); comp.append(c.co)
            for e in c.link_edges:
                w = e.other_vert(c)
                if w.index not in seen: seen.add(w.index); st.append(w)
        plo = Vector(map(min, *comp)); phi = Vector(map(max, *comp))
        edge_y = lo.y if side == 'S' else hi.y
        if phi.x > gx0 - 1.5 and plo.x < gx1 + 1.5 and (plo.y < -8 if side == 'S' else phi.y > 8):
            parts_near_gate.append({'obj': o.name, 'lo': [round(x, 3) for x in plo], 'hi': [round(x, 3) for x in phi], 'verts': len(comp)})
    bm.free()


def cast(p, d, dist=50):
    best = None
    for n, t in trees.items():
        h = t.ray_cast(p, d, dist)
        if h[0] is not None and (best is None or h[3] < best[2]):
            best = (n, round(h[0].z if d.z else (h[0].x if d.x else h[0].y), 4), h[3])
    return best

sgn = -1 if side == 'S' else 1
edge = lo.y if side == 'S' else hi.y
gc = (gx0 + gx1) / 2
res = {'file': src.replace('\\', '/'), 'sha256': sha, 'gateSpanX': [gx0, gx1], 'side': side, 'bbox': [list(lo), list(hi)]}
# A. longitudinal section through gate centre: floor below / overhead above, every 0.1 m from 2 m outside to 4 m inside
sec = []
for i in range(61):
    y = edge + sgn * 2.0 - sgn * i * 0.1
    dn = cast(Vector((gc, y, 0.2 + 1.8)), Vector((0, 0, -1)))
    up = cast(Vector((gc, y, 0.2 + 0.05)), Vector((0, 0, 1)))
    sec.append({'y': round(y, 2), 'down_from2.0': dn[:2] if dn else None, 'up_from0.25': up[:2] if up else None})
res['gateSection'] = sec
# B. clear width across the gate at several heights, at several depths through the passage
cw = []
for depth in [0.1, 0.3, 0.5, 0.8, 1.0, 1.3, 1.6, 2.0]:
    y = edge - sgn * depth
    row = {'inward_m': depth}
    for z in [0.25, 0.5, 1.0, 1.7, 2.0]:
        L = cast(Vector((gc, y, z)), Vector((-1, 0, 0)), 5)
        R = cast(Vector((gc, y, z)), Vector((1, 0, 0)), 5)
        row[f'z{z}'] = {'left': None if not L else [L[0], round(gc - L[2], 3)], 'right': None if not R else [R[0], round(gc + R[2], 3)],
                        'width': None if not (L and R) else round(L[2] + R[2], 3)}
    cw.append(row)
res['clearWidth'] = cw
# C. see-through test across the wall line at every 0.01 m within +-1.5 m of the gate span, heights 0.3/1.0/1.8
slits = []
for i in range(int((gx1 - gx0 + 3.0) / 0.01) + 1):
    x = gx0 - 1.5 + i * 0.01
    through = []
    for z in [0.3, 1.0, 1.8]:
        h = cast(Vector((x, edge + sgn * 1.0, z)), Vector((0, -sgn, 0)), 4.0)
        through.append(h is None)
    slits.append((round(x, 3), through))
runs = []; cur = None
for x, t in slits:
    if all(t):
        if cur is None: cur = [x, x]
        else: cur[1] = x
    elif cur is not None: runs.append(cur); cur = None
if cur: runs.append(cur)
res['seeThroughRuns_allHeights_depth4m'] = [[a, b, round(b - a + 0.01, 3)] for a, b in runs]
res['partsNearGate'] = sorted(parts_near_gate, key=lambda p: p['lo'][0])
json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('OK', sha[:12], res['seeThroughRuns_allHeights_depth4m'])
