# LY-023 prep: 2D plan clearance between stall feet/canopies and route ribbons (read-only).
# blender -b --factory-startup --python-exit-code 1 -P measure_route_clearance.py -- CLUSTER.glb OUT.json [EXTRA_ROUTES.glb ...]
# Feet = ^T\d_(leg|canopypost); canopies = ^T\d_canopy$; routes = every mesh whose material is C_routes
# (route_* in the cluster, plus every mesh of the extra GLBs, e.g. flowB-routes.glb).
import bpy, sys, json, re, math, hashlib
argv = sys.argv[sys.argv.index('--') + 1:]; GLB, OUT, EXTRA = argv[0], argv[1], argv[2:]
bpy.ops.wm.read_factory_settings(use_empty=True)
def imp(p):
    b = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=p); return [o for o in bpy.data.objects if o not in b and o.type == 'MESH']
main = imp(GLB); extra = []
for e in EXTRA: extra += [(e, o) for o in imp(e)]
def tris2d(o):
    M = o.matrix_world; me = o.data; me.calc_loop_triangles()
    V = [M @ v.co for v in me.vertices]
    return [[(float(V[i].x), float(V[i].y)) for i in t.vertices] for t in me.loop_triangles], max(float(v.z) for v in V)
def rect(o):
    M = o.matrix_world; xs = [float((M @ v.co).x) for v in o.data.vertices]; ys = [float((M @ v.co).y) for v in o.data.vertices]
    return (min(xs), min(ys), max(xs), max(ys))
def pt_seg(px, py, a, b):
    ax, ay = a; bx, by = b; dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L)); return math.hypot(px - ax - t * dx, py - ay - t * dy)
def in_tri(px, py, t):
    (x1, y1), (x2, y2), (x3, y3) = t
    d1 = (px - x2) * (y1 - y2) - (x1 - x2) * (py - y2); d2 = (px - x3) * (y2 - y3) - (x2 - x3) * (py - y3); d3 = (px - x1) * (y3 - y1) - (x3 - x1) * (py - y1)
    return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))
def rect_tri_dist(r, t):
    x0, y0, x1, y1 = r; corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    if any(in_tri(cx, cy, t) for cx, cy in corners): return 0.0
    if any(x0 <= px <= x1 and y0 <= py <= y1 for px, py in t): return 0.0
    edges = [(corners[i], corners[(i + 1) % 4]) for i in range(4)]; te = [(t[i], t[(i + 1) % 3]) for i in range(3)]
    d = min(pt_seg(p[0], p[1], a, b) for p in corners for a, b in te)
    return min(d, min(pt_seg(p[0], p[1], a, b) for p in t for a, b in edges))
routes = [('cluster', o) for o in main if o.material_slots and any(s.material and s.material.name == 'C_routes' for s in o.material_slots)] + extra
targets = [o for o in main if re.match(r'^T\d_(leg|canopypost|canopy|table)', o.name) and not o.name.endswith('container')]
rows = []
for src, ro in routes:
    T, rz = tris2d(ro)
    for o in targets:
        r = rect(o); d = min(rect_tri_dist(r, t) for t in T)
        rows.append(dict(route=ro.name, route_src=src.split('/')[-1], target=o.name, plan_clearance_m=round(d, 4), route_top_z=round(rz, 4)))
best = {}
for r in rows:
    k = (r['route'], r['target'].split('_')[0]); best[k] = min(best.get(k, 9e9), r['plan_clearance_m'])
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
out = dict(tool='LY-023/prep/measure_route_clearance.py', inputs=[dict(path=p, sha256=sha(p)) for p in [GLB] + EXTRA],
           note='plan (XY) distance between route ribbon triangles and member AABB; 0 = ribbon overlaps member footprint; not a body sweep',
           min_by_route_and_stall=[dict(route=k[0], stall=k[1], min_plan_clearance_m=v) for k, v in sorted(best.items())], rows=rows)
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE', OUT, len(routes), 'routes', len(targets), 'targets')
for k, v in sorted(best.items()): print(' ', k, v)
