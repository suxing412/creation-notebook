# LY-052 prep: measure operating floor / trough-front interface of m-luoyang-stable A/B.
# Read-only measurement. Usage:
#   D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P measure_stable_floor.py -- <glb> <out.json> <variant A|B>
# Coordinates reported in Blender Z-up metres (glTF +Y up -> Blender +Z up; glTF +Z -> Blender -Y).
import bpy, sys, json, hashlib, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
glb, out, var = argv[0], argv[1], argv[2]
sha = hashlib.sha256(open(glb, 'rb').read()).hexdigest()

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
dg = bpy.context.evaluated_depsgraph_get()

objs = {}
for o in bpy.context.scene.objects:
    if o.type != 'MESH':
        continue
    m = o.evaluated_get(dg).to_mesh()
    vs = [o.matrix_world @ v.co for v in m.vertices]
    tris = []
    m.calc_loop_triangles()
    for t in m.loop_triangles:
        tris.append(tuple(t.vertices))
    objs[o.name] = {'v': vs, 't': tris}

def bbox(vs):
    lo = [min(v[i] for v in vs) for i in range(3)]
    hi = [max(v[i] for v in vs) for i in range(3)]
    return lo, hi

def r(x, n=4):
    return round(x, n)

res = {'glb': glb.replace('\\', '/'), 'sha256': sha, 'variant': var, 'nodes': {}}
for n, d in objs.items():
    lo, hi = bbox(d['v'])
    res['nodes'][n] = {'lo': [r(x) for x in lo], 'hi': [r(x) for x in hi], 'verts': len(d['v']), 'tris': len(d['t'])}

def find(sub):
    return sorted(k for k in objs if sub in k)

plat = find('earth_platform')[0]
troughs = find('hollow_trough')
posts = find('_post_')
wall = find('rear_wall')[0]
plates = find('wallplate')
roofb = find('roof_board')
tiles = find('tile_shells')[0]

# 1. platform top flatness / slope / drainage
pv = objs[plat]['v']
plo, phi = bbox(pv)
top = [v for v in pv if abs(v.z - phi[2]) < 1e-4]
topz = [v.z for v in top]
res['platform'] = {
    'lo': [r(x) for x in plo], 'hi': [r(x) for x in phi],
    'thickness': r(phi[2] - plo[2]),
    'topVertexCount': len(top), 'topZmin': r(min(topz), 6), 'topZmax': r(max(topz), 6),
    'topSlopePercent': r((max(topz) - min(topz)) / max(1e-9, (phi[0] - plo[0])) * 100, 4),
    'vertexCountTotal': len(pv),
    'note': 'a 12-tri box: perfectly flat top, no fall, no gutter, no outlet, no threshold/ramp at any edge',
}

# 2. troughs: rim, inner floor, wall thickness, clearances
tr = []
wlo, whi = bbox(objs[wall]['v'])
for t in troughs:
    vs = objs[t]['v']
    lo, hi = bbox(vs)
    zs = sorted(set(r(v.z, 4) for v in vs))
    xs = sorted(set(r(v.x, 4) for v in vs))
    ys = sorted(set(r(v.y, 4) for v in vs))
    inner_floor = [z for z in zs if 1e-3 < z < hi[2] - 1e-3]
    tr.append({
        'name': t, 'lo': [r(x) for x in lo], 'hi': [r(x) for x in hi],
        'distinctZ': zs, 'distinctX': xs, 'distinctY': ys,
        'rimHeightAboveFloor': r(hi[2] - phi[2]),
        'innerFloorZ': inner_floor[0] if inner_floor else None,
        'gapToRearWall': r(wlo[1] - hi[1]),
        'frontFaceY': r(lo[1]),
        'workDepthToPlatformFront': r(lo[1] - plo[1]),
    })
res['troughs'] = tr

# 3. posts: bays, clear widths, post vs wall overlap
pp = []
for p in posts:
    lo, hi = bbox(objs[p]['v'])
    pp.append({'name': p, 'lo': [r(x) for x in lo], 'hi': [r(x) for x in hi]})
front = sorted([p for p in pp if p['lo'][1] < 0], key=lambda p: p['lo'][0])
rear = sorted([p for p in pp if p['lo'][1] > 0], key=lambda p: p['lo'][0])
res['frontBaysClearWidth'] = [r(front[i + 1]['lo'][0] - front[i]['hi'][0]) for i in range(len(front) - 1)]
res['frontPostFaceToPlatformFront'] = r(front[0]['lo'][1] - plo[1])
res['postEndToPlatformSide'] = r(front[0]['lo'][0] - plo[0])

def ovl(a, b):
    d = [max(0.0, min(a['hi'][i], b['hi'][i]) - max(a['lo'][i], b['lo'][i])) for i in range(3)]
    return d, d[0] * d[1] * d[2]
W = {'lo': list(wlo), 'hi': list(whi)}
pw = []
for p in rear:
    d, vol = ovl(p, W)
    if vol > 0:
        pw.append({'post': p['name'], 'overlapXYZ': [r(x) for x in d], 'volume_m3': r(vol, 5)})
res['rearPostWallInterpenetration'] = pw
# trough vs post / wall / each other (positive volume)
tv = []
for t in tr:
    for o in pp + [dict(name=wall, lo=list(wlo), hi=list(whi))]:
        d, vol = ovl(t, o)
        if vol > 1e-9:
            tv.append({'a': t['name'], 'b': o['name'], 'volume_m3': r(vol, 6)})
res['troughOverlaps'] = tv
res['troughSpacingX'] = [r(tr[i + 1]['lo'][0] - tr[i]['hi'][0]) for i in range(len(tr) - 1)] if len(tr) > 1 else []
res['troughEndToPostX'] = []
for t in tr:
    near = min(abs(t['lo'][0] - p['hi'][0]) if p['hi'][0] <= t['lo'][0] else abs(p['lo'][0] - t['hi'][0]) for p in rear)
    res['troughEndToPostX'].append(r(near))
res['troughToRearPostY'] = r(rear[0]['lo'][1] - tr[0]['hi'][1])

# 4. rear ledge behind wall, wall height
res['rearWall'] = {'lo': [r(x) for x in wlo], 'hi': [r(x) for x in whi], 'height': r(whi[2] - wlo[2]),
                   'ledgeBehindWall': r(phi[1] - whi[1]), 'wallEndToPlatformSide': r(wlo[0] - plo[0])}

# 5. eave drip line vs platform edges; headroom
tlo, thi = bbox(objs[tiles]['v'])
blo = min(bbox(objs[b]['v'])[0][2] for b in roofb)
plate_lo = min(bbox(objs[p]['v'])[0][2] for p in plates)
res['roof'] = {'tileYmin': r(tlo[1]), 'tileYmax': r(thi[1]), 'tileXmin': r(tlo[0]), 'tileXmax': r(thi[0]),
               'eaveZlow_tiles': r(tlo[2]), 'roofBoardZlow': r(blo),
               'dripLineInsideFrontEdge': r(tlo[1] - plo[1]), 'dripLineInsideRearEdge': r(phi[1] - thi[1]),
               'gableOverhangX': r(plo[0] - tlo[0]),
               'headroomUnderFrontWallplate': r(plate_lo - phi[2])}

# 6. support raster: rays down from z=3.0 (roof, tiles, wallplates excluded from BVH; above post tops 2.76) on a 0.05 m grid over the platform footprint
allv, allt = [], []
for n, d in objs.items():
    if n in (tiles,) or n in roofb or n in plates:
        continue
    base = len(allv)
    allv += d['v']
    allt += [(a + base, b + base, c + base) for a, b, c in d['t']]
owner = []
for n, d in objs.items():
    if n in (tiles,) or n in roofb or n in plates:
        continue
    owner += [n] * len(d['t'])
bvh = BVHTree.FromPolygons(allv, allt)
step = 0.05
nx = int(round((phi[0] - plo[0]) / step))
ny = int(round((phi[1] - plo[1]) / step))
cnt = {}
free = 0
free_front_of_trough = 0
for i in range(nx):
    for j in range(ny):
        x = plo[0] + (i + 0.5) * step
        y = plo[1] + (j + 0.5) * step
        hit = bvh.ray_cast(Vector((x, y, 3.0)), Vector((0, 0, -1)), 10)
        if hit[0] is None:
            k = 'NONE'
        else:
            k = owner[hit[2]]
            k = k.split('_')[1] if '_' in k else k
            if owner[hit[2]] == plat:
                free += 1
                if y < tr[0]['lo'][1]:
                    free_front_of_trough += 1
        cnt[k] = cnt.get(k, 0) + 1
res['supportRaster'] = {'gridStep_m': step, 'cells': nx * ny, 'hitsByKind': cnt,
                        'freeFloor_m2': r(free * step * step, 3),
                        'freeFloorFrontOfTroughLine_m2': r(free_front_of_trough * step * step, 3),
                        'platformTop_m2': r((phi[0] - plo[0]) * (phi[1] - plo[1]), 3)}

# 7. off-platform probe: anything outside platform footprint at floor level (would be unsupported)
outside = []
for n, d in objs.items():
    lo, hi = bbox(d['v'])
    if lo[2] < phi[2] + 0.5 and (lo[0] < plo[0] - 1e-4 or hi[0] > phi[0] + 1e-4 or lo[1] < plo[1] - 1e-4 or hi[1] > phi[1] + 1e-4):
        outside.append(n)
res['lowGeometryOutsidePlatform'] = outside
res['minZ'] = r(min(v.z for d in objs.values() for v in d['v']))

json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE', out)
