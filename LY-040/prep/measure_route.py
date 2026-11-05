# LY-040 prep: Blender headless, read-only measurement of the NE storage/armory composition.
# Run:
#   D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P measure_route.py -- <out.json> <label=glb> ...
# Imports each GLB (glTF Y-up -> Blender Z-up, i.e. back to native: X east, Y north, Z up), never saves a .blend,
# never writes next to inputs. Measures:
#   1. per-object world bbox / triangle count
#   2. downward ray-cast support along the frozen candidate route (granary ground -> C road -> wuku patch -> wuku B stair foot)
#      for centre line and lateral offsets +-0.45 m (0.9 m strip) and +-0.90 m (1.8 m strip); 0.10 m step
#   3. vertical discontinuities between consecutive samples (> 0.02 m flagged, > 0.15 m = step fail for C walking strip)
#   4. upward-facing coplanar faces between different objects (z-fight candidates) at seam heights 0.0 / 0.2
#   5. seam contact classification at the two road ends (plan gap, Z offset, end-cap coplanarity)
#   6. negative control: road removed -> route must report unsupported samples
import bpy, bmesh, sys, json, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
out_path = argv[0]
inputs = [a.split('=', 1) for a in argv[1:]]

bpy.ops.wm.read_factory_settings(use_empty=True)
objs = {}
for label, path in inputs:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    for o in set(bpy.data.objects) - before:
        if o.type == 'MESH':
            objs[label + ':' + o.name] = o
dg = bpy.context.evaluated_depsgraph_get()

def world_bm(o):
    bm = bmesh.new()
    bm.from_object(o, dg)
    bm.transform(o.matrix_world)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    return bm

info = {}
bvh = {}
bms = {}
for k, o in objs.items():
    bm = world_bm(o)
    bms[k] = bm
    vs = [v.co for v in bm.verts]
    mn = [min(v[i] for v in vs) for i in range(3)]
    mx = [max(v[i] for v in vs) for i in range(3)]
    info[k] = {'triangles': len(bm.faces), 'bbox_min': [round(x, 4) for x in mn], 'bbox_max': [round(x, 4) for x in mx]}
    bvh[k] = BVHTree.FromBMesh(bm)

SUPPORT_HINTS = ('ground', 'NE_APPROACH', 'SUPPORT_PATCH', 'static_earth')
support_keys = [k for k in objs if any(h in k for h in SUPPORT_HINTS)]

def top_hit(x, y, keys):
    best = None
    for k in keys:
        loc, nrm, idx, dist = bvh[k].ray_cast(Vector((x, y, 50.0)), Vector((0, 0, -1)), 100.0)
        if loc is not None and (best is None or loc.z > best[0]):
            best = (loc.z, k, nrm.z)
    return best

# frozen candidate route (C design, from measured geometry; see brief-draft.md section 5)
ROUTE = [
    (2285.714, 3657.0),   # inside granary original ground, south of buildings
    (2285.714, 3647.469), # granary ground south edge = road north end (port P_N)
    (2285.714, 3486.0),   # road corner (road centre line)
    (2316.327, 3486.0),   # road corner east
    (2316.327, 3490.0),   # road east end = wuku patch south edge (port P_S)
    (2316.327, 3492.0),   # on patch, before wuku B earth stair foot
]

def sample_route(keys, offsets=(0.0, -0.45, 0.45, -0.9, 0.9), step=0.10):
    res = {}
    for off in offsets:
        pts = []
        for (x0, y0), (x1, y1) in zip(ROUTE[:-1], ROUTE[1:]):
            L = math.hypot(x1 - x0, y1 - y0)
            ux, uy = (x1 - x0) / L, (y1 - y0) / L
            nx, ny = -uy, ux
            n = max(1, int(L / step))
            for i in range(n):
                t = i * step
                pts.append((x0 + ux * t + nx * off, y0 + uy * t + ny * off))
        pts.append((ROUTE[-1][0], ROUTE[-1][1]))
        unsupported = []
        steps = []
        prev = None
        for (x, y) in pts:
            h = top_hit(x, y, keys)
            if h is None:
                unsupported.append([round(x, 3), round(y, 3)])
                prev = None
                continue
            if prev is not None and abs(h[0] - prev[0]) > 0.02:
                steps.append({'at': [round(x, 3), round(y, 3)], 'dz': round(h[0] - prev[0], 4), 'from': prev[1], 'to': h[1]})
            prev = h
        res['offset_%+.2f' % off] = {'samples': len(pts), 'unsupported': len(unsupported),
                                     'unsupported_first': unsupported[:10], 'steps_gt_0.02': steps}
    return res

route_all = sample_route(support_keys)
neg_keys = [k for k in support_keys if 'NE_APPROACH' not in k]
route_neg = sample_route(neg_keys, offsets=(0.0,))

# upward coplanar faces across objects (z-fight candidates): faces with n.z>0.999 at the same height whose
# plan-AABBs overlap; report overlap area of AABBs (upper bound), heights 0.0 and 0.2 only.
def up_faces(bm, z, tol=1e-3):
    out = []
    for f in bm.faces:
        if f.normal.z > 0.999 and all(abs(v.co.z - z) < tol for v in f.verts):
            xs = [v.co.x for v in f.verts]; ys = [v.co.y for v in f.verts]
            out.append((min(xs), max(xs), min(ys), max(ys)))
    return out

def union_overlap(A, B):
    tot = 0.0
    for a in A:
        for b in B:
            w = min(a[1], b[1]) - max(a[0], b[0]); h = min(a[3], b[3]) - max(a[2], b[2])
            if w > 1e-4 and h > 1e-4:
                tot += w * h
    return tot

coplanar = []
keys = list(objs)
for z in (0.0, 0.2):
    F = {k: up_faces(bms[k], z) for k in keys}
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            if F[keys[i]] and F[keys[j]]:
                a = union_overlap(F[keys[i]], F[keys[j]])
                if a > 0:
                    coplanar.append({'z': z, 'a': keys[i], 'b': keys[j], 'aabb_overlap_m2_upper_bound': round(a, 3)})

# seam check: road ends vs neighbours
def k_of(h):
    return [k for k in objs if h in k]
seams = {}
road = k_of('NE_APPROACH')
gr = [k for k in objs if 'ground' in k.lower()]
patch = k_of('SUPPORT_PATCH')
if road and gr:
    rb = info[road[0]]; gb = info[gr[0]]
    seams['P_N_road_to_granary_ground'] = {
        'plan_gap_y_m': round(gb['bbox_min'][1] - rb['bbox_max'][1], 5),
        'road_top_z_at_end': round(top_hit(2285.714, 3647.40, road)[0], 4),
        'ground_top_z_at_edge': round(top_hit(2285.714, 3647.54, gr)[0], 4),
    }
if road and patch:
    seams['P_S_road_to_wuku_patch'] = {
        'plan_gap_y_m': round(info[patch[0]]['bbox_min'][1] - 3490.0, 5),
        'road_top_z_at_end': round(top_hit(2316.327, 3489.93, road)[0], 4),
        'patch_top_z_at_edge': round(top_hit(2316.327, 3490.07, patch)[0], 4),
    }

json.dump({'objects': info, 'support_keys': support_keys, 'route': ROUTE, 'route_support': route_all,
           'negative_no_road': route_neg, 'coplanar_up_faces': coplanar, 'seams': seams},
          open(out_path, 'w', encoding='utf-8'), indent=1)
print('WROTE', out_path)
for k, v in route_all.items():
    print(k, 'samples', v['samples'], 'unsupported', v['unsupported'], 'steps', len(v['steps_gt_0.02']))
print('NEG', {k: v['unsupported'] for k, v in route_neg.items()})
print('COPLANAR', coplanar)
print('SEAMS', seams)
