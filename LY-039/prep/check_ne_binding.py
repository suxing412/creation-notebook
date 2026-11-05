# LY-039 prep: rerunnable binding / connectivity check for C_NE_APPROACH_LOCAL.
# Read-only on inputs; writes one JSON. Discrete grid only, NOT continuous body motion.
#
# blender -b --factory-startup --python-exit-code 1 -P check_ne_binding.py -- \
#   --road road.glb --ground g1.glb [--ground g2.glb] [--support wuku_support.glb] \
#   --out out.json [--drop-road] [--offset dx,dy,dz] [--cell 0.25] [--radius 0.45] \
#   [--step 0.02] [--start x,y] [--goal name:x,y ...]
#
# Frame: native Z-up metres (Blender glTF import). Walkable cell = top surface hit
# with normal.z >= cos(slope_max). Cells are eroded by --radius (half body width).
# Neighbour cells connect when |dz| <= --step. Reports reachability start->goals,
# seam steps at the road ends and the per-file SHA256 actually measured.
import bpy, sys, json, math, hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index('--') + 1:]
opt = {'ground': [], 'goal': [], 'support': [], 'drop-road': False, 'offset': '0,0,0', 'cell': '0.25',
       'radius': '0.45', 'step': '0.02', 'slope': '8', 'start': '2285.714,3652.0', 'road': None, 'out': None}
i = 0
while i < len(a):
    k = a[i][2:]
    if k == 'drop-road':
        opt[k] = True; i += 1; continue
    v = a[i + 1]
    if isinstance(opt.get(k), list):
        opt[k].append(v)
    else:
        opt[k] = v
    i += 2
if not opt['goal']:
    # stub end goal sits 0.75 m inside the y=3490 cap so the eroded (r=0.45 -> 2 cells) grid can stand there
    opt['goal'] = ['north_leg_mid:2285.714,3567.0', 'road_stub_end:2316.327,3489.25',
                   'wuku_port_B_point_side:2316.327,3491.0', 'wuku_B_point:2316.327,3500.0']
cell, rad, step = float(opt['cell']), float(opt['radius']), float(opt['step'])
cos_max = math.cos(math.radians(float(opt['slope'])))
off = Vector([float(x) for x in opt['offset'].split(',')])


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def load(path, shift=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    objs = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    dg = bpy.context.evaluated_depsgraph_get()
    V, T = [], []
    for o in objs:
        ev = o.evaluated_get(dg); me = ev.to_mesh(); me.calc_loop_triangles()
        base = len(V); M = o.matrix_world
        V.extend([(M @ v.co) + (shift or Vector()) for v in me.vertices])
        T.extend([tuple(base + j for j in t.vertices) for t in me.loop_triangles])
        ev.to_mesh_clear()
    return V, T


bpy.ops.wm.read_factory_settings(use_empty=True)
rep = {'frame': 'native Z-up m', 'params': {k: opt[k] for k in opt}, 'files': {}, 'method':
       'discrete %.2fm grid, downward rays, erosion radius %.2fm, max step %.3fm; not continuous body, cart, load or structure proof' % (cell, rad, step)}
surfaces = []  # (label, bvh)
road_bbox = None
if opt['road']:
    rep['files']['road'] = sha(opt['road'])
    V, T = load(opt['road'], off)
    road_bbox = [[min(v[j] for v in V) for j in range(3)], [max(v[j] for v in V) for j in range(3)]]
    rep['road_bbox_after_offset'] = road_bbox
    if not opt['drop-road']:
        surfaces.append(('road', BVHTree.FromPolygons(V, T)))
for g in opt['ground']:
    rep['files'][g] = sha(g)
    V, T = load(g); surfaces.append(('ground:' + g.split('/')[-1], BVHTree.FromPolygons(V, T)))
for s in opt['support']:
    rep['files'][s] = sha(s)
    V, T = load(s); surfaces.append(('support:' + s.split('/')[-1], BVHTree.FromPolygons(V, T)))
rep['drop_road'] = opt['drop-road']
rep['offset'] = list(off)


def top(x, y):
    best = None
    for lab, b in surfaces:
        h = b.ray_cast(Vector((x, y, 30.0)), Vector((0, 0, -1)), 60.0)
        if h[0] is not None and (best is None or h[0].z > best[0]):
            best = (h[0].z, h[1].z, lab)
    return best

X0, X1, Y0, Y1 = 2280.0, 2322.0, 3480.0, 3660.0
nx, ny = int((X1 - X0) / cell) + 1, int((Y1 - Y0) / cell) + 1
grid = {}
for ix in range(nx):
    for iy in range(ny):
        h = top(X0 + ix * cell, Y0 + iy * cell)
        if h and h[1] >= cos_max:
            grid[(ix, iy)] = h
r = int(math.ceil(rad / cell))
ok = {}
for (ix, iy), h in grid.items():
    good = True
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            if dx * dx + dy * dy > r * r:
                continue
            n = grid.get((ix + dx, iy + dy))
            if n is None or abs(n[0] - h[0]) > step * max(1, abs(dx) + abs(dy)):
                good = False; break
        if not good:
            break
    if good:
        ok[(ix, iy)] = h
rep['cells_hit'] = len(grid); rep['cells_after_erosion'] = len(ok)


def idx(x, y):
    return (int(round((x - X0) / cell)), int(round((y - Y0) / cell)))

sx, sy = [float(v) for v in opt['start'].split(',')]
st = idx(sx, sy)
seen = set()
if st in ok:
    seen.add(st); q = [st]
    while q:
        c = q.pop()
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (c[0] + d[0], c[1] + d[1])
            if n in ok and n not in seen and abs(ok[n][0] - ok[c][0]) <= step:
                seen.add(n); q.append(n)
rep['start'] = {'xy': [sx, sy], 'walkable': st in ok, 'reachable_cells': len(seen)}
goals = []
for gdef in opt['goal']:
    name, xy = gdef.split(':'); gx, gy = [float(v) for v in xy.split(',')]
    gi = idx(gx, gy)
    goals.append({'name': name, 'xy': [gx, gy], 'walkable': gi in ok, 'surface': ok[gi][2] if gi in ok else (grid[gi][2] if gi in grid else None),
                  'reachable': gi in seen})
rep['goals'] = goals
# furthest south reachable y along the road corridor
if seen:
    rep['reachable_y_min'] = round(Y0 + min(c[1] for c in seen) * cell, 3)
    rep['reachable_x_max_at_south'] = round(X0 + max(c[0] for c in seen if Y0 + c[1] * cell < 3492) * cell, 3) if any(Y0 + c[1] * cell < 3492 for c in seen) else None

# seam steps (only meaningful with road present)
def seam(y_line, xs, dy_in, dy_out):
    out = []
    for x in xs:
        a_ = top(x, y_line + dy_in); b_ = top(x, y_line + dy_out)
        out.append({'x': x, 'in': None if not a_ else [round(a_[0], 5), a_[2]], 'out': None if not b_ else [round(b_[0], 5), b_[2]],
                    'step': None if not (a_ and b_) else round(b_[0] - a_[0], 5)})
    return out
rep['north_seam'] = seam(3647.469 + off.y, [2284.4 + k * 0.25 for k in range(11)], -0.01, 0.01)
rep['south_stub_seam'] = seam(3490.0 + off.y, [2315.0 + k * 0.25 for k in range(11)], -0.01, 0.01)
ns = [s['step'] for s in rep['north_seam'] if s['step'] is not None]
rep['north_seam_max_abs_step'] = max((abs(v) for v in ns), default=None)
rep['north_seam_missing'] = sum(1 for s in rep['north_seam'] if s['step'] is None)
rep['south_stub_missing_beyond'] = sum(1 for s in rep['south_stub_seam'] if s['out'] is None)
with open(opt['out'], 'w', encoding='utf-8') as f:
    json.dump(rep, f, ensure_ascii=False, indent=1)
print('WROTE', opt['out'], 'goals', [(g['name'], g['reachable']) for g in goals])
