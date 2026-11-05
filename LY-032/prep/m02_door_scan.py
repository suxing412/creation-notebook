# LY-032 prep: read-only ray-cast survey of one warehouse door bay in an exported GLB.
# All inputs/outputs in glTF axes (X east, Y up, Z south-positive). Door assumed to face +Z.
# usage: blender -b --factory-startup --python-exit-code 1 -P m02_door_scan.py -- <glb> <out.json> <cx> <z_wall_outer> <label>
#   cx            = nominal door centre X (glTF)
#   z_wall_outer  = nominal outer (south) face of front wall (glTF Z)
# Measures: opening width/height (horizontal rays through the wall), wall thickness, sill/floor height,
# stair profile on 0.9 / 1.5 / 1.8 m strips, interior/exterior swing-zone obstructions, headroom.
import bpy, sys, json, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
glb, out = argv[0], argv[1]
CX, ZW = float(argv[2]), float(argv[3])
label = argv[4] if len(argv) > 4 else ''
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
dg = bpy.context.evaluated_depsgraph_get()
verts, polys, owner = [], [], []
names = []
for o in bpy.context.scene.objects:
    if o.type != 'MESH':
        continue
    me = o.evaluated_get(dg).to_mesh()
    base = len(verts)
    verts += [o.matrix_world @ v.co for v in me.vertices]
    for p in me.polygons:
        polys.append([base + i for i in p.vertices]); owner.append(len(names))
    names.append(o.name)
    o.evaluated_get(dg).to_mesh_clear()
bvh = BVHTree.FromPolygons(verts, polys, epsilon=0.0)

def B(x, y, z):  # glTF -> Blender
    return Vector((x, -z, y))

def ray(p, d, dist=50.0):
    loc, nrm, idx, t = bvh.ray_cast(B(*p), B(*d).normalized(), dist)
    if loc is None:
        return None, None
    return t, names[owner[idx]]

def down(x, z, y0=2.5):  # start below eaves/lintel (B lintel 3.2, A 2.95) so roofs are not hit
    t, n = ray((x, y0, z), (0, -1, 0), 20)
    return (None if t is None else round(y0 - t, 4)), n

r = {'glb': glb, 'label': label, 'cx': CX, 'z_wall_outer': ZW, 'objects': names}

# 1. floor / sill height just outside the wall and just inside
r['sill_y_outside_wall'] = down(CX, ZW + 0.1)
r['floor_y_inside'] = down(CX, ZW - 0.6)
FY = r['floor_y_inside'][0]

# 2. opening scan: horizontal rays travelling north (-Z) starting 0.05 m south of nominal wall face
xs = [CX - 1.5 + i * 0.01 for i in range(301)]
open_x = []
for x in xs:
    t, n = ray((x, FY + 1.0, ZW + 0.05), (0, 0, -1), 0.6)
    if t is None:
        open_x.append(round(x, 3))
r['opening_x_at_floor+1.0'] = [min(open_x), max(open_x)] if open_x else None
ys = [FY + 0.005 + i * 0.01 for i in range(400)]
open_y = []
for y in ys:
    t, n = ray((CX, y, ZW + 0.05), (0, 0, -1), 0.6)
    if t is None:
        open_y.append(round(y, 3))
    elif open_y:
        break  # keep only the contiguous clear run starting at the floor (rays above the eave pass over the roof)
r['opening_y_at_cx'] = [min(open_y), max(open_y)] if open_y else None
# wall thickness from jamb: ray north at x just outside opening
if open_x:
    xj = min(open_x) - 0.05
    t1, n1 = ray((xj, FY + 1.0, ZW + 0.3), (0, 0, -1), 2)
    t2, n2 = ray((xj, FY + 1.0, ZW - 1.5), (0, 0, 1), 2)
    r['wall_outer_z'] = None if t1 is None else round(ZW + 0.3 - t1, 4)
    r['wall_inner_z'] = None if t2 is None else round(ZW - 1.5 + t2, 4)
    r['wall_hit_names'] = [n1, n2]
    # jamb faces: ray east/west inside the wall thickness
    zm = (r['wall_outer_z'] + r['wall_inner_z']) / 2 if t1 and t2 else ZW - 0.1
    tl, nl = ray((CX, FY + 1.0, zm), (-1, 0, 0), 3)
    tr, nr = ray((CX, FY + 1.0, zm), (1, 0, 0), 3)
    r['jamb_x'] = [None if tl is None else round(CX - tl, 4), None if tr is None else round(CX + tr, 4)]
    tu, nu = ray((CX, FY + 0.2, zm), (0, 1, 0), 5)
    r['lintel_underside_y'] = None if tu is None else round(FY + 0.2 + tu, 4)
    r['lintel_name'] = nu

# 3. stair / approach profile along Z on several strips (heights from downward rays)
prof = {}
for half in [0.0, 0.45, 0.75, 0.9]:
    for side in ([0] if half == 0 else [-1, 1]):
        x = CX + side * half
        key = f'x{side*half:+.2f}'
        pts = []
        for i in range(0, 361):
            z = ZW + 3.0 - i * 0.01
            y, n = down(x, z)
            pts.append([round(z, 3), y, n])
        prof[key] = pts
r['profiles'] = prof
# summarise risers on centreline
def risers(pts, thr=0.02):
    out_ = []
    for a, b in zip(pts, pts[1:]):
        if a[1] is not None and b[1] is not None and abs(b[1] - a[1]) > thr:
            out_.append([a[0], a[1], b[1], round(b[1] - a[1], 4)])
    return out_
r['risers'] = {k: risers(v) for k, v in prof.items()}

# 4. swing-zone obstruction sampling (point-in-free-space via 6-direction short rays)
def blocked(p, eps=0.02):
    for d in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
        t, n = ray(p, d, eps)
        if t is not None:
            return n
    return None
if open_x and r.get('wall_inner_z') is not None:
    w = (max(open_x) - min(open_x))
    leaf = w / 2.0
    zi, zo = r['wall_inner_z'], r['wall_outer_z']
    res = {}
    for nm, zbase, sgn in [('inward', zi, -1), ('outward', zo, +1)]:
        hits = []
        n = 0
        for hx, hs in [(min(open_x), +1), (max(open_x), -1)]:   # two hinge lines, leaves swing toward wall
            for ri in range(1, 16):
                rad = leaf * ri / 15.0
                for ai in range(0, 19):
                    a = math.radians(ai * 5)
                    x = hx + hs * rad * math.cos(a)
                    z = zbase + sgn * (0.03 + rad * math.sin(a))
                    for y in [FY + 0.03, FY + 0.5, FY + 1.0, FY + 1.5, FY + 2.0]:
                        n += 1
                        b = blocked((x, y, z))
                        if b:
                            hits.append([round(x, 3), round(y, 3), round(z, 3), b])
        res[nm] = {'samples': n, 'blocked': len(hits), 'first': hits[:12]}
    r['swing_zone'] = res
    # 0.9 m candidate strip vs leaf open positions (leaf lies along jamb, thickness 0.06 assumed)
    strip = [CX - 0.45, CX + 0.45]
    r['strip_0.9'] = strip
    r['clearance_jamb_to_strip'] = [round(strip[0] - min(open_x), 4), round(max(open_x) - strip[1], 4)]

# 5. headroom inside near door: upward rays from floor
hr = []
for dz in [0.3, 0.6, 1.0, 1.5]:
    t, n = ray((CX, FY + 0.01, (r.get('wall_inner_z') or ZW - 0.2) - dz), (0, 1, 0), 10)
    hr.append([dz, None if t is None else round(t, 4), n])
r['headroom_inside'] = hr

json.dump(r, open(out, 'w'), indent=1)
print('LY032 done', label, r.get('opening_x_at_floor+1.0'), r.get('opening_y_at_cx'), FY)
