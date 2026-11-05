# LY-058 prep: read-only route / clearance survey of a courtyard GLB.
# Blender: blender -b --factory-startup --python-exit-code 1 -P measure_yard.py -- <glb> <out.json> [step] [pad]
# All reported coordinates are glTF (x, y-up, z). Nothing is saved back to the GLB.
#
# Per grid column (step m) it records every surface crossed by a vertical line and classifies:
#   floor      highest up-facing hit (n_y>0.7) below FLOOR_MAX; None = no floor geometry in the GLB
#   blocked    any solid between floor+FOOT and floor+HEAD (segment hit OR inside-volume test)
#   sky        no geometry above floor+HEAD at all (open to sky)
#   roofed     geometry exists above floor+HEAD (roof / eave / beam)
# Walkable = floor (or assumed external ground) & not blocked & >= BODY_R from any blocked cell.
# Connectivity: 4-neighbour flood from the outer pad ring, step <= STEP_MAX.
import bpy, sys, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
GLB, OUT = argv[0], argv[1]
STEP = float(argv[2]) if len(argv) > 2 else 0.1
PAD = float(argv[3]) if len(argv) > 3 else 1.5
FLOOR_MAX = 1.2      # m, floors above this are not walking surfaces in this survey
FOOT = 0.15          # m, clearance above floor ignored (sills / tile seams count separately)
HEAD = 2.0           # m, C body height envelope (1.75 m person + 0.25 m load/hat)
BODY_R = 0.30        # m, C shoulder half-width + tolerance
STEP_MAX = 0.20      # m, single step without explicit stair
EXT_GROUND = None    # set from GLB min y (assumed external ground plane where no floor exists)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
dg = bpy.context.evaluated_depsgraph_get()
objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
trees = []
gmin = [1e9] * 3; gmax = [-1e9] * 3
for o in objs:
    me = o.evaluated_get(dg).to_mesh()
    M = o.matrix_world
    verts = [M @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    for v in verts:
        g = (v.x, v.z, -v.y)
        for k in range(3):
            gmin[k] = min(gmin[k], g[k]); gmax[k] = max(gmax[k], g[k])
    trees.append((o.name, BVHTree.FromPolygons(verts, polys)))
EXT_GROUND = gmin[1]

def g2b(x, y, z): return Vector((x, -z, y))

def column_hits(x, z, top=20.0, bottom=-5.0):
    hits = []
    for name, t in trees:
        o = g2b(x, top, z); d = Vector((0, 0, -1)); dist = top - bottom
        while dist > 0:
            r = t.ray_cast(o, d, dist)
            if r[0] is None: break
            loc, nrm = r[0], r[1]
            y = loc.z
            hits.append((y, nrm.z, name))
            step = (o.z - y) + 1e-4
            o = Vector((o.x, o.y, y - 1e-4)); dist -= step
    hits.sort(key=lambda h: -h[0])
    return hits

def inside(x, y, z):
    # first hit straight down from (x,y,z): back-face (normal pointing down) means we start inside a volume
    for name, t in trees:
        r = t.ray_cast(g2b(x, y, z), Vector((0, 0, -1)), 30.0)
        if r[0] is not None and r[1].z < -0.2:
            r2 = t.ray_cast(g2b(x, y, z), Vector((0, 0, 1)), 30.0)
            if r2[0] is not None and r2[1].z > 0.2:
                return name
    return None

xs = np.arange(gmin[0] - PAD, gmax[0] + PAD + 1e-9, STEP)
zs = np.arange(gmin[2] - PAD, gmax[2] + PAD + 1e-9, STEP)
NX, NZ = len(xs), len(zs)
floor = np.full((NX, NZ), np.nan); has_floor = np.zeros((NX, NZ), bool)
blocked = np.zeros((NX, NZ), bool); sky = np.zeros((NX, NZ), bool)
roof_h = np.full((NX, NZ), np.nan); block_by = {}
for i, x in enumerate(xs):
    for j, z in enumerate(zs):
        hs = column_hits(float(x), float(z))
        f = None
        for (y, ny, n) in hs:
            if ny > 0.7 and y <= FLOOR_MAX:
                f = y; break
        if f is not None:
            # a floor under a solid body (e.g. wall bottom face sits below) still counts; blocked test handles it
            has_floor[i, j] = True; floor[i, j] = f
        base = f if f is not None else EXT_GROUND
        seg = [h for h in hs if base + FOOT < h[0] < base + HEAD]
        if seg:
            blocked[i, j] = True; block_by[(i, j)] = seg[-1][2]
        else:
            for hh in (0.4, 1.0, 1.6):
                n = inside(float(x), base + hh, float(z))
                if n:
                    blocked[i, j] = True; block_by[(i, j)] = n; break
        above = [h for h in hs if h[0] >= base + HEAD]
        if above:
            roof_h[i, j] = min(h[0] for h in above) - base
        else:
            sky[i, j] = True

# erode by body radius
r = int(math.ceil(BODY_R / STEP))
near = blocked.copy()
for di in range(-r, r + 1):
    for dj in range(-r, r + 1):
        if di * di + dj * dj > (BODY_R / STEP) ** 2 + 1e-9: continue
        sh = np.zeros_like(blocked)
        si = slice(max(0, di), NX + min(0, di)); ti = slice(max(0, -di), NX + min(0, -di))
        sj = slice(max(0, dj), NZ + min(0, dj)); tj = slice(max(0, -dj), NZ + min(0, -dj))
        sh[si, sj] = blocked[ti, tj]
        near |= sh
ground = np.where(has_floor, floor, EXT_GROUND)
walk = ~near
inside_fp = np.zeros((NX, NZ), bool)
for i, x in enumerate(xs):
    for j, z in enumerate(zs):
        inside_fp[i, j] = (gmin[0] <= x <= gmax[0]) and (gmin[2] <= z <= gmax[2])

# flood from outer ring
from collections import deque
reach = np.zeros((NX, NZ), bool); dq = deque()
for i in range(NX):
    for j in range(NZ):
        if (i in (0, NX - 1) or j in (0, NZ - 1)) and walk[i, j]:
            reach[i, j] = True; dq.append((i, j))
stepfail = 0
while dq:
    i, j = dq.popleft()
    for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        a, b = i + di, j + dj
        if 0 <= a < NX and 0 <= b < NZ and walk[a, b] and not reach[a, b]:
            if abs(ground[a, b] - ground[i, j]) <= STEP_MAX + 1e-6:
                reach[a, b] = True; dq.append((a, b))
            else:
                stepfail += 1

def cell(x, z):
    return int(round((x - xs[0]) / STEP)), int(round((z - zs[0]) / STEP))

# boundary crossings: reachable cells on the footprint edge band that connect inside
openings = []
for i in range(NX):
    for j in range(NZ):
        if reach[i, j] and inside_fp[i, j]:
            x, z = xs[i], zs[j]
            if min(x - gmin[0], gmax[0] - x, z - gmin[2], gmax[2] - z) < STEP * 1.5:
                openings.append((round(float(x), 3), round(float(z), 3)))

uniq_floor = {}
for v in floor[has_floor]:
    k = round(float(v), 2); uniq_floor[k] = uniq_floor.get(k, 0) + 1

res = {
    'glb': GLB, 'step_m': STEP, 'pad_m': PAD, 'params': {'FLOOR_MAX': FLOOR_MAX, 'FOOT': FOOT, 'HEAD': HEAD, 'BODY_R': BODY_R, 'STEP_MAX': STEP_MAX},
    'objects': [n for n, _ in trees], 'bbox_gltf': {'min': gmin, 'max': gmax}, 'assumed_external_ground_y': EXT_GROUND,
    'grid': {'x0': float(xs[0]), 'z0': float(zs[0]), 'nx': NX, 'nz': NZ},
    'counts': {
        'footprint_cells': int(inside_fp.sum()),
        'footprint_with_floor_geometry': int((inside_fp & has_floor).sum()),
        'footprint_blocked': int((inside_fp & blocked).sum()),
        'footprint_walk_after_erosion': int((inside_fp & walk).sum()),
        'footprint_reachable_from_outside': int((inside_fp & reach).sum()),
        'footprint_reachable_sky': int((inside_fp & reach & sky).sum()),
        'footprint_reachable_roofed': int((inside_fp & reach & ~sky).sum()),
        'step_rejections': stepfail,
    },
    'floor_height_histogram': dict(sorted(uniq_floor.items())),
    'boundary_reach_cells': openings,
}
np.savez_compressed(OUT.replace('.json', '.npz'), xs=xs, zs=zs, floor=floor, has_floor=has_floor, blocked=blocked,
                    sky=sky, roof_h=roof_h, walk=walk, reach=reach, inside_fp=inside_fp)
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('LY058 done', json.dumps(res['counts']))
