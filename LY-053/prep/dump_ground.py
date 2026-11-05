# LY-053 prep: dump the presentation-ground slab polygons and the pit/firebox/kiln-bed contact gaps.
# D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P dump_ground.py -- out.json kiln.glb
# Read-only. Blender Z-up coords after glTF import.
import bpy, sys, json, os
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
out, src = argv[0], argv[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
dg = bpy.context.evaluated_depsgraph_get()
objs = {o.name: o for o in bpy.context.scene.objects if o.type == 'MESH'}
pre = os.path.basename(src)[5]  # 'A' or 'B'


def world_polys(o):
    me = o.data
    mw = o.matrix_world
    r = []
    for p in me.polygons:
        vs = [mw @ me.vertices[i].co for i in p.vertices]
        n = (mw.to_3x3() @ p.normal).normalized()
        r.append({'n': [round(x, 3) for x in n], 'area': round(p.area, 4),
                  'v': [[round(c, 4) for c in v] for v in vs]})
    return r


g = objs[f'{pre}_presentation_ground']
polys = world_polys(g)
res = {'file': os.path.basename(src), 'ground_polys': polys}

# Distinct x / y edges of vertical faces of the ground = walls of the cut-out (pit walls).
walls = []
for p in polys:
    if abs(p['n'][2]) < 0.05:
        xs = sorted({v[0] for v in p['v']}); ys = sorted({v[1] for v in p['v']}); zs = sorted({v[2] for v in p['v']})
        walls.append({'n': p['n'], 'x': [xs[0], xs[-1]], 'y': [ys[0], ys[-1]], 'z': [zs[0], zs[-1]], 'area': p['area']})
res['ground_vertical_faces'] = walls


def bvh(o):
    me = o.data
    mw = o.matrix_world
    return BVHTree.FromPolygons([mw @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons])


# Support probes: cast rays downward from the bottom face centres of selected parts, report what they hit.
def down_probe(name, pts):
    o = objs[name]
    others = {k: bvh(v) for k, v in objs.items() if k != name}
    rows = []
    for p in pts:
        hit = None
        for k, t in others.items():
            loc, nrm, idx, d = t.ray_cast(Vector(p), Vector((0, 0, -1)), 5.0)
            if loc is not None and (hit is None or d < hit[1]):
                hit = (k, round(d, 4), round(loc.z, 4))
        rows.append({'from': [round(c, 3) for c in p], 'hit': hit})
    return rows


def bottom_grid(name, z_eps=0.005, n=3):
    o = objs[name]
    vs = [o.matrix_world @ v.co for v in o.data.vertices]
    lo = [min(v[i] for v in vs) for i in range(3)]; hi = [max(v[i] for v in vs) for i in range(3)]
    pts = []
    for i in range(n):
        for j in range(n):
            x = lo[0] + (hi[0] - lo[0]) * (i + 0.5) / n
            y = lo[1] + (hi[1] - lo[1]) * (j + 0.5) / n
            pts.append((x, y, lo[2] - z_eps))
    return pts


probes = {}
for nm in [f'{pre}_kiln_bed', f'{pre}_operation_pit_floor', f'{pre}_fire_floor', f'{pre}_presentation_ground']:
    probes[nm] = down_probe(nm, bottom_grid(nm))
res['down_probes_from_bottom'] = probes

# Pairwise BVH overlap (surface-only) among structural parts.
names = [n for n in objs if not any(s in n for s in ('drying', 'board', 'interpretive', 'unfired'))]
pairs = []
trees = {n: bvh(objs[n]) for n in names}
for i, a in enumerate(names):
    for b in names[i + 1:]:
        ov = trees[a].overlap(trees[b])
        if ov:
            pairs.append({'a': a, 'b': b, 'triPairs': len(ov)})
res['surface_overlaps'] = pairs
json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE', out)
