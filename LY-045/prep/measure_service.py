# LY-045 prep: measure service-A (raised privy + pen + stair) GLB with BVH ray casts.
# Reports in glTF axes (x, y-up, z), metres. Read-only on input.
# D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P measure_service.py -- in.glb out.json
# Scope: surface BVH ray casts on a grid; not solid collision, not continuous body motion, not GPU.
import bpy, bmesh, sys, json, math, hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
src, out = argv[0], argv[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)


def B(x, y, z):  # glTF -> blender
    return Vector((x, -z, y))


def G(v):  # blender -> glTF
    return [round(v.x, 4), round(v.z, 4), round(-v.y, 4)]


objs = {}
allbm = bmesh.new()
for o in bpy.context.scene.objects:
    if o.type != 'MESH':
        continue
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    objs[o.name.replace('service-A-static_', '')] = (BVHTree.FromBMesh(bm), bm)
    tmp = o.data.copy(); tmp.transform(o.matrix_world); allbm.from_mesh(tmp)
bmesh.ops.triangulate(allbm, faces=allbm.faces[:])
ALL = BVHTree.FromBMesh(allbm)
R = {'file': src.replace('\\', '/'), 'sha256': hashlib.sha256(open(src, 'rb').read()).hexdigest(),
     'axes': 'glTF x, y-up, z; metres; model origin, no city matrix applied',
     'scope': 'surface BVH ray casts on grids; not solid collision, not continuous body motion, not GPU'}


def down_hits(x, z, top=6.0, bot=-5.0, tree=ALL):
    hs = []; y = top
    while y > bot:
        h = tree.ray_cast(B(x, y, z), Vector((0, 0, -1)), y - bot)
        if h[0] is None:
            break
        hy = h[0].z; hs.append(round(hy, 4)); y = hy - 1e-4
    return hs


def ray(o, d, dist, tree=ALL):
    h = tree.ray_cast(o, d, dist)
    return None if h[0] is None else h[3]


# 1 privy floor slab and hole (slab bbox from inventory: x -0.95..0.95, z -4.4..-1.9, top 1.40)
step = 0.02
fx0, fx1, fz0, fz1 = -0.95, 0.95, -4.4, -1.9
open_cells = []; floor_cells = 0
for i in range(int(round((fx1 - fx0) / step))):
    for k in range(int(round((fz1 - fz0) / step))):
        x = fx0 + (i + .5) * step; z = fz0 + (k + .5) * step
        hs = [h for h in down_hits(x, z, top=3.2) if h <= 3.2]
        if any(1.395 <= h <= 1.405 for h in hs):
            floor_cells += 1
        else:
            open_cells.append((x, z, hs[:4]))
hole = [(x, z, hs) for x, z, hs in open_cells if not any(0.96 < h < 1.41 for h in hs)]
R['floorSlab'] = {'topY': 1.40, 'raster_m': step, 'floorCells': floor_cells, 'floorArea_m2': round(floor_cells * step * step, 3),
                  'openCellsNotHole': len(open_cells) - len(hole)}
if hole:
    hx = [c[0] for c in hole]; hz = [c[1] for c in hole]
    cx = (min(hx) + max(hx)) / 2; cz = (min(hz) + max(hz)) / 2
    R['floorHole'] = {'cells': len(hole), 'area_m2': round(len(hole) * step * step, 4),
                      'xRange': [round(min(hx) - step / 2, 3), round(max(hx) + step / 2, 3)],
                      'zRange': [round(min(hz) - step / 2, 3), round(max(hz) + step / 2, 3)],
                      'centre_xz': [round(cx, 3), round(cz, 3)],
                      'radialDistFromPenCentre': round(math.hypot(cx, cz), 3),
                      'hitsBelowHoleCentre_from1.39_to-5': down_hits(cx, cz, top=1.39, bot=-5.0),
                      'hitsBelowHoleCorners': {f'{round(a,2)},{round(b,2)}': down_hits(a, b, top=1.39, bot=-5.0)
                                               for a in (min(hx), max(hx)) for b in (min(hz), max(hz))}}

# 2 pen ring: horizontal rays from (0, 0.5, 0) outward, 0.5 deg steps (angle in glTF xz: x=cos, z=sin)
ring = []; gap = []
for a10 in range(0, 3600, 5):
    a = math.radians(a10 / 10)
    d = B(math.cos(a), 0, math.sin(a)); o = B(0, 0.5, 0)
    t1 = ray(o, d, 10)
    if t1 is None or t1 > 3.5:
        gap.append(a10 / 10); continue
    t2 = ray(o + d * (t1 + 1e-3), d, 2)
    ring.append((a10 / 10, t1, (t1 + 1e-3 + t2) if t2 is not None else None))
inner = [r[1] for r in ring]; outer = [r[2] for r in ring if r[2]]
R['penRing'] = {'centre_assumed_xz': [0, 0], 'sampleY': 0.5,
                'innerRadius': [round(min(inner), 3), round(max(inner), 3)],
                'outerRadius': [round(min(outer), 3), round(max(outer), 3)] if outer else None,
                'gapAnglesDeg_glTFxz': [gap[0], gap[-1]] if gap else None, 'gapSamples_0.5deg': len(gap)}
# opening chord: march along +x at z = 2.80..2.95 (glTF) at y=0.5, list surface crossings
cross = {}
for zz in (2.70, 2.80, 2.85, 2.90):
    xs = []; x = -3.6
    while x < 3.6:
        t = ray(B(x, 0.5, zz), B(1, 0, 0), 3.6 - x)
        if t is None:
            break
        x = x + t + 1e-4; xs.append(round(x, 3))
    cross[str(zz)] = xs
R['penRing']['xCrossingsAlongZ_y0.5'] = cross
R['penRing']['wallTopHits_at(-2.9,0)'] = down_hits(-2.9, 0)
R['penRing']['interiorHits_at(0,0)'] = down_hits(0, 0)
R['penRing']['interiorHits_at(1,1)'] = down_hits(1, 1)
R['penRing']['interiorHits_at(0,-2.26)_underHole'] = down_hits(0, -2.26, top=1.2)

# 3 stair: top-surface raster x 0.9..3.8, z -4.7..-1.8
treads = {}
for i in range(int((3.8 - 0.9) / 0.02)):
    x = 0.9 + (i + .5) * 0.02
    for k in range(int((4.7 - 1.8) / 0.05)):
        z = -4.7 + (k + .5) * 0.05
        hs = down_hits(x, z, top=3.0)
        if hs:
            treads.setdefault(round(hs[0], 3), []).append((round(x, 3), round(z, 3)))
st = []
for y, pts in sorted(treads.items()):
    xs = [p[0] for p in pts]; zs = [p[1] for p in pts]
    st.append({'y': y, 'n': len(pts), 'x': [min(xs), max(xs)], 'z': [min(zs), max(zs)]})
R['stairTopsRaster'] = st
# stair underside: is the flight solid to the ground? sample hits under mid-run
R['stairColumnHits'] = {f'{x},-3.65': down_hits(x, -3.65, top=3.0) for x in (1.2, 1.8, 2.4, 3.0, 3.6)}

# 4 door on the +x privy face: rays along -x starting at x=0.97, 0.5 m deep, grid (z, y)
door = []
for k in range(int((4.6 - 1.7) / 0.02)):
    z = -4.6 + (k + .5) * 0.02
    for j in range(int((3.6 - 1.3) / 0.02)):
        y = 1.3 + (j + .5) * 0.02
        if ray(B(0.97, y, z), B(-1, 0, 0), 0.5) is None:
            door.append((z, y))
if door:
    dz = [d[0] for d in door]; dy = [d[1] for d in door]
    R['doorOpening_xPlusFace'] = {'cells': len(door), 'zRange': [round(min(dz) - .01, 3), round(max(dz) + .01, 3)],
                                  'yRange': [round(min(dy) - .01, 3), round(max(dy) + .01, 3)],
                                  'width': round(max(dz) - min(dz) + .02, 3), 'height': round(max(dy) - min(dy) + .02, 3)}
# other faces: any openings?
others = {}
for name, (ox, dvec, zr, xr) in {'xMinus': (-0.97, B(1, 0, 0), (-4.4, -1.9), None),
                                 'zMinus': (None, B(0, 0, 1), None, (-0.95, 0.95)),
                                 'zPlus': (None, B(0, 0, -1), None, (-0.95, 0.95))}.items():
    n = 0
    for j in range(int((3.4 - 1.45) / 0.05)):
        y = 1.45 + (j + .5) * 0.05
        if zr:
            for k in range(int((zr[1] - zr[0]) / 0.05)):
                z = zr[0] + (k + .5) * 0.05
                if ray(B(ox, y, z), dvec, 0.5) is None:
                    n += 1
        else:
            zz = -4.42 if name == 'zMinus' else -1.88
            for i in range(int((xr[1] - xr[0]) / 0.05)):
                x = xr[0] + (i + .5) * 0.05
                if ray(B(x, y, zz), dvec, 0.5) is None:
                    n += 1
    others[name] = n
R['openCellsOtherFaces_0.05m'] = others

# 5 headroom above floor
hr = {}
for (x, z) in [(0, -3.15), (0.5, -3.6), (-0.5, -2.8), (0, -2.26), (0.7, -3.5), (0.85, -3.5)]:
    h = ALL.ray_cast(B(x, 1.401, z), B(0, 1, 0), 5)
    hr[f'{x},{z}'] = None if h[0] is None else round(h[0].z - 1.40, 3)
R['headroomAboveFloor'] = hr

# 6 supports: per-object min Y; vertices at y<0.001
R['objectsMinY'] = {n: round(min(v.co.z for v in bm.verts), 4) for n, (t, bm) in objs.items()}
R['groundContactVerts_y<0.001'] = {n: sum(1 for v in bm.verts if v.co.z < 0.001) for n, (t, bm) in objs.items()}

# 7 cross-object surface overlaps
names = list(objs); ov = {}
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        p = objs[names[i]][0].overlap(objs[names[j]][0])
        key = names[i] + '|' + names[j]
        ov[key] = {'pairs': len(p)}
        if p:
            bmA = objs[names[i]][1]; bmA.faces.ensure_lookup_table()
            cs = [bmA.faces[a].calc_center_median() for a, b in p]
            ys = [c.z for c in cs]
            ov[key]['yRange'] = [round(min(ys), 3), round(max(ys), 3)]
            ov[key]['xRange'] = [round(min(c.x for c in cs), 3), round(max(c.x for c in cs), 3)]
            ov[key]['zRange'] = [round(min(-c.y for c in cs), 3), round(max(-c.y for c in cs), 3)]
R['crossObjectSurfaceOverlap'] = ov
json.dump(R, open(out, 'w'), indent=1)
print('OK', out)
