# LY-077 prep measurement: Taixue A front entrance / outer-ground gap.
# Read-only on inputs. Usage:
#   blender -b --factory-startup --python-exit-code 1 -P measure_taixue_a_entry.py -- <glb> <out.json> [label]
# All reported coordinates are glTF frame (X east, Y up, Z south), metres.
# Blender import maps glTF (x,y,z) -> Blender (x,-z,y); we convert back.
import bpy, sys, json, hashlib, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
src, out = argv[0], argv[1]
label = argv[2] if len(argv) > 2 else src
sha = hashlib.sha256(open(src, 'rb').read()).hexdigest()

bpy.ops.wm.read_factory_settings(use_empty=True)
if src.lower().endswith(('.glb', '.gltf')):
    bpy.ops.import_scene.gltf(filepath=src)
else:
    raise SystemExit('unsupported')

def g(v):  # blender -> glTF
    return [round(v.x, 5), round(v.z, 5), round(-v.y, 5)]
def b(x, y, z):  # glTF -> blender
    return Vector((x, -z, y))

verts_all, faces_all, meshes = [], [], []
tri_hash = hashlib.sha256()
tri_keys = []
for o in sorted([o for o in bpy.data.objects if o.type == 'MESH'], key=lambda o: o.name):
    me = o.data
    me.calc_loop_triangles()
    base = len(verts_all)
    ws = [o.matrix_world @ v.co for v in me.vertices]
    verts_all += ws
    tris = [tuple(t.vertices) for t in me.loop_triangles]
    faces_all += [tuple(base + i for i in t) for t in tris]
    mn = [min(g(v)[k] for v in ws) for k in range(3)] if ws else None
    mx = [max(g(v)[k] for v in ws) for k in range(3)] if ws else None
    mats = [m.name for m in me.materials if m]
    meshes.append({'object': o.name, 'mesh': me.name, 'materials': mats, 'triangles': len(tris),
                   'vertices': len(ws), 'min': mn, 'max': mx})
    for t in tris:
        k = tuple(sorted(tuple(round(c, 4) for c in g(ws[i])) for i in t))
        tri_keys.append(k)
tri_keys.sort()
for k in tri_keys:
    tri_hash.update(repr(k).encode())

bvh = BVHTree.FromPolygons(verts_all, faces_all, all_triangles=True)
gmin = [min(g(v)[k] for v in verts_all) for k in range(3)]
gmax = [max(g(v)[k] for v in verts_all) for k in range(3)]

def down(x, z, y0=1.2, dist=3.0):
    loc, nor, idx, d = bvh.ray_cast(b(x, y0, z), Vector((0, 0, -1)), dist)
    return None if loc is None else round(loc.z, 4)

def up(x, y, z, dist=12.0):
    loc, nor, idx, d = bvh.ray_cast(b(x, y, z), Vector((0, 0, 1)), dist)
    return None if loc is None else round(d, 4)

def horiz_north(x, y, zstart=12.0, dist=30.0):
    # ray travelling toward glTF -Z (north) from the south
    loc, nor, idx, d = bvh.ray_cast(b(x, y, zstart), Vector((0, 1, 0)), dist)
    return None if loc is None else round(-loc.y, 4)

R = {'label': label, 'file': src, 'sha256': sha, 'bytes': len(open(src, 'rb').read()),
     'frame': 'glTF X east / Y up / Z south, metres', 'boundsMin': gmin, 'boundsMax': gmax,
     'meshes': meshes, 'triangles': len(faces_all),
     'geometryHash_sortedTriangles_4dp': tri_hash.hexdigest()}

# 1. front profile lines (heights seen from 1.2 m down)
prof = {}
for zz in [5.5, 4.9, 4.84, 4.675, 4.325, 3.975, 3.85, 3.75, 0.0, -3.75, -3.85]:
    row = []
    x = math.floor(gmin[0]) - 2.0
    while x <= math.ceil(gmax[0]) + 2.0 + 1e-9:
        row.append(down(round(x, 3), zz))
        x += 0.02
    # compress into runs
    runs = []
    x0 = math.floor(gmin[0]) - 2.0
    for i, h in enumerate(row):
        xx = round(x0 + i * 0.02, 3)
        key = None if h is None else round(h, 2)
        if runs and runs[-1]['h'] == key:
            runs[-1]['x1'] = xx
        else:
            runs.append({'x0': xx, 'x1': xx, 'h': key})
    prof[str(zz)] = runs
R['profilesAlongX'] = prof

# 2. tread / platform heights along each stair centre line (south->north)
stairs = {}
for sx in [-10.5, 1.5, 10.5, -12.0, 0.0, 12.0]:
    col = []
    z = 7.0
    while z >= -5.0 - 1e-9:
        col.append([round(z, 3), down(sx, round(z, 3))])
        z -= 0.025
    runs = []
    for z, h in col:
        key = None if h is None else round(h, 2)
        if runs and runs[-1]['h'] == key:
            runs[-1]['z1'] = z
        else:
            runs.append({'z0': z, 'z1': z, 'h': key})
    stairs[str(sx)] = runs
R['profilesAlongZ'] = stairs

# 3. riser faces: horizontal rays toward north at several heights at stair centres
ris = {}
for sx in [-10.5, 1.5, 10.5, -6.0, 6.0, -16.0, 16.0]:
    ris[str(sx)] = {str(y): horiz_north(sx, y) for y in [0.02, 0.1, 0.19, 0.3, 0.39, 0.5, 0.59, 0.7, 1.0]}
R['firstFaceZ_fromSouth'] = ris

# 4. outer band coverage: how many probe points beyond the footprint have any surface
def band(xr, zr, step=0.1):
    n = hit = 0
    x = xr[0]
    while x <= xr[1] + 1e-9:
        z = zr[0]
        while z <= zr[1] + 1e-9:
            n += 1
            if down(x, z, y0=0.5, dist=2.0) is not None:
                hit += 1
            z += step
        x += step
    return {'x': xr, 'z': zr, 'step': step, 'probes': n, 'withSurface': hit}
R['outerBands'] = {
    'south_front_0to4m': band([-23.0, 23.0], [4.9, 8.85]),
    'south_front_between_flights_z3.85to4.8': band([-8.0, -2.5], [3.85, 4.8]),
    'north_rear_0to4m': band([-23.0, 23.0], [-7.75, -3.85]),
    'west_end': band([-23.0, -18.9], [-3.75, 4.8]),
    'east_end': band([18.9, 23.0], [-3.75, 4.8]),
    'old_support_patch_extent_x-23to23_z-9to9': band([-23.0, 23.0], [-9.0, 9.0], 0.25),
}

# 5. lowest supporting surface anywhere (ground level) and platform top
R['lowestVertexY'] = gmin[1]

# 6. overhead clearance above stair treads and directly in front of first tread
clr = {}
for sx in [-10.5, 1.5, 10.5]:
    pts = {}
    for zz, yy in [(4.675, 0.2), (4.325, 0.4), (3.975, 0.6), (3.6, 0.6), (5.2, 0.0), (6.0, 0.0)]:
        for dx in [-0.39, 0.0, 0.39]:
            d = up(sx + dx, yy + 0.01, zz)
            pts[f'z{zz}_dx{dx}'] = None if d is None else round(d + 0.01, 3)
    clr[str(sx)] = pts
R['overheadClearanceFromStandingSurface'] = clr

# 7. lateral platform path along the front edge (z=3.6, y=0.61 standing) - does a 0.6 m platform
# connect all three flights? sample support every 0.1 m from x=-18 to 18
lat = []
x = -18.5
while x <= 18.5 + 1e-9:
    h = down(round(x, 3), 3.6)
    lat.append([round(x, 2), h])
    x += 0.1
runs = []
for x, h in lat:
    key = None if h is None else round(h, 2)
    if runs and runs[-1]['h'] == key:
        runs[-1]['x1'] = x
    else:
        runs.append({'x0': x, 'x1': x, 'h': key})
R['platformFrontStrip_z3.6'] = runs

json.dump(R, open(out, 'w'), indent=1)
print('OK', label, sha[:12], len(faces_all), gmin, gmax)
