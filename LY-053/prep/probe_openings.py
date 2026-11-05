# LY-053 prep: measure the firebox mouth (operation opening) and flue outlets of a tile-kiln GLB
# by ray grids, and the depth that terrain must keep clear.  Read-only.
# D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P probe_openings.py -- out.json kiln.glb
import bpy, sys, json, os
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
out, src = argv[0], argv[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
objs = {o.name: o for o in bpy.context.scene.objects if o.type == 'MESH'}
pre = os.path.basename(src)[5]


def bvh(o):
    mw = o.matrix_world
    return BVHTree.FromPolygons([mw @ v.co for v in o.data.vertices], [tuple(p.vertices) for p in o.data.polygons])


trees = {k: bvh(v) for k, v in objs.items()}


def cast(org, d, maxd=50.0, skip=()):
    best = None
    for k, t in trees.items():
        if k in skip:
            continue
        loc, n, i, dist = t.ray_cast(Vector(org), Vector(d), maxd)
        if loc is not None and (best is None or dist < best[1]):
            best = (k, round(dist, 4), [round(c, 4) for c in loc])
    return best


res = {'file': os.path.basename(src)}

# 1) Firebox mouth: rays +Y from y=-2.4 (inside the pit, in front of the hood face y=-2.1).
#    A ray that travels deeper than 0.35 m past the hood face is "open".
step = 0.05
grid = []
open_cells = []
x = -0.9
while x <= 0.9001:
    z = -0.8 + 0.01
    while z <= 0.95:
        h = cast((x, -2.4, z), (0, 1, 0), skip=())
        depth = None if h is None else h[2][1]
        grid.append({'x': round(x, 3), 'z': round(z, 3), 'hit': h})
        if h is None or depth > -2.1 + 0.35:
            open_cells.append((round(x, 3), round(z, 3), h[0] if h else None, depth))
        z += step
    x += step
xs = sorted({c[0] for c in open_cells}); zs = sorted({c[1] for c in open_cells})
res['firebox_mouth'] = {
    'method': 'rays +Y from y=-2.4, 5 cm grid over hood face x[-0.9,0.9] z[-0.79,0.95]; open = travels >0.35 m beyond y=-2.1',
    'open_cells': len(open_cells), 'cells_total': len(grid),
    'open_x_range': [xs[0], xs[-1]] if xs else None, 'open_z_range': [zs[0], zs[-1]] if zs else None,
    'per_z_open_x': {str(z): [min(c[0] for c in open_cells if c[1] == z), max(c[0] for c in open_cells if c[1] == z),
                              sum(1 for c in open_cells if c[1] == z)] for z in zs},
    'first_blocker_of_open_rays': sorted({(c[2], c[3]) for c in open_cells}, key=lambda t: (str(t[0]), t[1] or 0))[:12],
}

# Along the centre line: what stops a horizontal ray at several heights (does the bed block the passage?)
res['firebox_centreline'] = [{'z': z, 'hit': cast((0.0, -2.4, z), (0, 1, 0))} for z in (-0.75, -0.6, -0.5, -0.3, -0.1, 0.05, 0.2, 0.4, 0.6)]

# 2) Flue outlets: rays -Z from z=3 at each flue's centre and on a small grid; report hit z.
flues = []
for k, o in sorted(objs.items()):
    if 'short_flue' not in k:
        continue
    vs = [o.matrix_world @ v.co for v in o.data.vertices]
    lo = [min(v[i] for v in vs) for i in range(3)]; hi = [max(v[i] for v in vs) for i in range(3)]
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    pts = []
    for dx in (-0.2, -0.1, 0, 0.1, 0.2):
        for dy in (-0.2, -0.1, 0, 0.1, 0.2):
            h = cast((cx + dx, cy + dy, 3.0), (0, 0, -1), skip=(f'{pre}_detachable_roof_C',))
            pts.append({'dx': dx, 'dy': dy, 'hit': h})
    flues.append({'name': k, 'bbox_min': [round(c, 3) for c in lo], 'bbox_max': [round(c, 3) for c in hi],
                  'centre_down_hit_without_roof': cast((cx, cy, 3.0), (0, 0, -1), skip=(f'{pre}_detachable_roof_C',)),
                  'centre_down_hit_with_roof': cast((cx, cy, 3.0), (0, 0, -1)),
                  'grid': pts})
    # rear face exposure: ray -Y from behind
    flues[-1]['rear_face_hit'] = cast((cx, hi[1] + 1.0, 0.6), (0, -1, 0))
res['flues'] = flues
json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE', out)
