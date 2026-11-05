# LY-053 prep / future QA: bottom-support and opening-clearance check for a kiln GLB,
# optionally with the presentation ground excluded and a candidate pit/base GLB co-loaded.
# D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P support_check.py -- \
#     out.json kiln.glb --exclude A_presentation_ground [--add pit.glb ...] [--tol 0.02]
# For every kept mesh part: sample a 4x4 grid on its lowest-z footprint and cast -Z rays from 1 mm
# above the part's min z; a sample is "supported" if another part's surface lies within tol below
# (or coplanar).  Also reports: flue shaft floors, firebox-mouth clearance in front of the hood face,
# and pit wall presence (horizontal rays from inside the pit towards +-X / -Y).  Read-only.
import bpy, sys, json, os
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
out, src = argv[0], argv[1]
rest = argv[2:]
exclude, adds, tol = set(), [], 0.02
i = 0
while i < len(rest):
    if rest[i] == '--exclude':
        exclude.add(rest[i + 1]); i += 2
    elif rest[i] == '--add':
        adds.append(rest[i + 1]); i += 2
    elif rest[i] == '--tol':
        tol = float(rest[i + 1]); i += 2
    else:
        raise SystemExit('bad arg ' + rest[i])

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
for a in adds:
    bpy.ops.import_scene.gltf(filepath=a)
objs = {o.name: o for o in bpy.context.scene.objects if o.type == 'MESH' and o.name not in exclude}
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
        loc, n, idx, dist = t.ray_cast(Vector(org), Vector(d), maxd)
        if loc is not None and (best is None or dist < best[1]):
            best = (k, round(dist, 4), [round(c, 4) for c in loc])
    return best


def bbox(o):
    vs = [o.matrix_world @ v.co for v in o.data.vertices]
    return [min(v[i] for v in vs) for i in range(3)], [max(v[i] for v in vs) for i in range(3)]


support = {}
for k, o in sorted(objs.items()):
    lo, hi = bbox(o)
    n = 4; ok = 0; tot = 0; misses = []
    for a in range(n):
        for b in range(n):
            x = lo[0] + (hi[0] - lo[0]) * (a + 0.5) / n
            y = lo[1] + (hi[1] - lo[1]) * (b + 0.5) / n
            # only sample where this part actually has its bottom: ray up from below must hit self first near lo z
            self_hit = trees[k].ray_cast(Vector((x, y, lo[2] - 0.5)), Vector((0, 0, 1)), 0.5 + 0.01)
            if self_hit[0] is None:
                continue
            tot += 1
            h = cast((x, y, lo[2] + 0.001), (0, 0, -1), maxd=tol + 0.001, skip=(k,))
            if h is not None:
                ok += 1
            else:
                misses.append([round(x, 3), round(y, 3)])
    support[k] = {'minZ': round(lo[2], 4), 'samples': tot, 'supported': ok, 'unsupported_xy': misses[:6]}

res = {'file': os.path.basename(src), 'excluded': sorted(exclude), 'added': [os.path.basename(a) for a in adds],
       'tol_m': tol, 'support': support}

# flue shaft floors: ray down along each flue centre (roof removed from consideration)
fl = []
for k, o in sorted(objs.items()):
    if 'short_flue' in k:
        lo, hi = bbox(o)
        c = ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2)
        fl.append({'flue': k, 'outlet_top_z': round(hi[2], 4),
                   'shaft_floor_hit': cast((c[0], c[1], hi[2] + 1.0), (0, 0, -1), skip=(f'{pre}_detachable_roof_C',))})
res['flue_shafts'] = fl

# firebox mouth clearance: from 0.05 m in front of hood face (y=-2.15) cast -Y (into the pit) at mouth heights;
# the distance to the first obstacle is the free working depth in front of the mouth.
hood = objs.get(f'{pre}_fire_hood')
if hood:
    lo, hi = bbox(hood)
    rows = []
    for z in (-0.7, -0.4, -0.1, 0.2, 0.5, 0.8):
        for x in (-0.6, 0.0, 0.6):
            rows.append({'x': x, 'z': z, 'hit': cast((x, lo[1] - 0.05, z), (0, -1, 0), maxd=20)})
    res['mouth_front_clearance'] = rows

# pit wall presence: from pit centre at mid-depth cast +-X and -Y
pit = objs.get(f'{pre}_operation_pit_floor')
if pit:
    lo, hi = bbox(pit)
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    walls = {}
    for nm, d in (('+X', (1, 0, 0)), ('-X', (-1, 0, 0)), ('-Y', (0, -1, 0))):
        walls[nm] = [cast((cx, cy, z), d, maxd=20) for z in (-0.6, -0.3, -0.05)]
    res['pit_walls_from_centre'] = walls
    res['pit_floor_underside'] = cast((cx, cy, lo[2] - 0.001), (0, 0, -1), maxd=20)

unsup = [k for k, v in support.items() if v['samples'] and v['supported'] < v['samples']]
res['summary'] = {'parts': len(support), 'parts_not_fully_supported': unsup}
json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE', out, 'unsupported:', len(unsup))
