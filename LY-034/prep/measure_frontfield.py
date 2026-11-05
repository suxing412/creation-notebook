# LY-034 prep: read-only measurement of the granary front field (receiving -> A/B stair foot).
# blender -b --factory-startup --python-exit-code 1 -P measure_frontfield.py -- in.glb out.json [anchorX anchorZ]
# Coordinates reported in glTF-local metres: x east, y up, z = glTF Z (negative = north),
# relative to anchor (default 2285.714111328125, -3673.468994140625 from storage-origin-contract).
# Nothing is written back to the GLB. No names are used for port finding: ports come from geometry.
import bpy, sys, json, math, hashlib
from collections import deque
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
src, out = argv[0], argv[1]
AX = float(argv[2]) if len(argv) > 2 else 2285.714111328125
AZ = float(argv[3]) if len(argv) > 3 else -3673.468994140625

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
dg = bpy.context.evaluated_depsgraph_get()

def to_local(v):  # blender world -> glTF local (x, y_up, z)
    return (v.x - AX, v.z, -v.y - AZ)

def to_bl(x, y, z):  # glTF local -> blender world
    return Vector((x + AX, -(z + AZ), y))

verts_all, tris_all, tri_owner = [], [], []
objects = []
islands = []
for o in bpy.context.scene.objects:
    if o.type != 'MESH':
        continue
    me = o.evaluated_get(dg).to_mesh()
    me.calc_loop_triangles()
    mw = o.matrix_world
    base = len(verts_all)
    wv = [mw @ v.co for v in me.vertices]
    verts_all.extend(wv)
    mats = [m.name if m else None for m in me.materials]
    # union-find on position-welded vertices (1e-4 m) -> loose parts
    key = {}
    parent = list(range(len(wv)))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    def uni(a, b):
        ra, rb = find(a), find(b)
        if ra != rb: parent[ra] = rb
    for i, v in enumerate(wv):
        k = (round(v.x, 4), round(v.y, 4), round(v.z, 4))
        if k in key: uni(i, key[k])
        else: key[k] = i
    tri_mat = []
    for t in me.loop_triangles:
        a, b, c = t.vertices
        uni(a, b); uni(b, c)
        tris_all.append((base + a, base + b, base + c))
        tri_owner.append(o.name)
        tri_mat.append(mats[t.material_index] if t.material_index < len(mats) else None)
    groups = {}
    for ti, t in enumerate(me.loop_triangles):
        groups.setdefault(find(t.vertices[0]), []).append(ti)
    for r, tl in groups.items():
        vids = sorted({vi for ti in tl for vi in me.loop_triangles[ti].vertices})
        pts = [to_local(wv[i]) for i in vids]
        lo = [min(p[k] for p in pts) for k in range(3)]
        hi = [max(p[k] for p in pts) for k in range(3)]
        h = hashlib.sha256(json.dumps(sorted({tuple(round(c, 3) for c in p) for p in pts})).encode()).hexdigest()[:16]
        islands.append({'object': o.name, 'material': tri_mat[tl[0]], 'tris': len(tl), 'min': [round(x, 4) for x in lo], 'max': [round(x, 4) for x in hi], 'geomHash3mm': h})
    objects.append({'name': o.name, 'verts': len(wv), 'tris': len(me.loop_triangles)})
    o.evaluated_get(dg).to_mesh_clear()

bvh = BVHTree.FromPolygons(verts_all, tris_all, all_triangles=True)

def column(x, z, top=12.0):
    """all surface hits straight down at local (x,z): list of (y, owner, normal_up)"""
    hits = []
    d = Vector((0, 0, -1))
    y = top
    for _ in range(40):
        loc, nrm, idx, dist = bvh.ray_cast(to_bl(x, y, z), d, 50)
        if loc is None: break
        ly = loc.z
        hits.append((round(ly, 4), tri_owner[idx], round(nrm.z, 3)))
        y = ly - 1e-4
    return hits

# ---------- ground / support grid ----------
STEP = 0.1
X0, X1, Z0, Z1 = -36.0, 36.0, -26.0, 26.0
nx, nz = int(round((X1 - X0) / STEP)), int(round((Z1 - Z0) / STEP))
HEAD = 1.8          # body height used for headroom
MAXRISE = 0.2       # max height change between neighbouring 0.1 m cells to count as walkable (stair rise allowance)
support = [[None] * nz for _ in range(nx)]
toplayer = [[None] * nz for _ in range(nx)]
for i in range(nx):
    x = X0 + (i + 0.5) * STEP
    for j in range(nz):
        z = Z0 + (j + 0.5) * STEP
        hs = column(x, z)
        toplayer[i][j] = hs[0][0] if hs else None
        # walk-level support = LOWEST upward-facing surface with >= HEAD clear above it
        # (so roofs/cover tops are ignored and a table top only counts where the ground under it lacks headroom)
        best = None
        for k in range(len(hs) - 1, -1, -1):
            y, own, nup = hs[k]
            if nup < 0.7: continue
            above = hs[k - 1][0] if k > 0 else 1e9
            if above - y >= HEAD:
                best = y; break
        support[i][j] = best

def cell(x, z):
    return int(math.floor((x - X0) / STEP)), int(math.floor((z - Z0) / STEP))

# ground plane reference: the dominant support height
from collections import Counter
cnt = Counter(round(s, 3) for col in support for s in col if s is not None)
ground_y = cnt.most_common(1)[0][0]
unsupported = sum(1 for col in support for s in col if s is None)

# ---------- stair / entrance detection from geometry (no names) ----------
# an entrance stair = islands whose bottom sits on ground_y and whose tops step upward in a run
# an entrance stair = one loose part (steps are welded) resting on ground_y, 1.2-2.0 m wide, whose
# centreline support profile climbs in >=3 monotonic risers. Ports come from this measurement, not from names.
cands = [s for s in islands if abs(s['min'][1] - ground_y) < 0.005 and 0.3 < (s['max'][1] - s['min'][1]) < 1.5
         and 1.2 <= (s['max'][0] - s['min'][0]) <= 2.0 and 0.6 < (s['max'][2] - s['min'][2]) < 3.5]
stairs = []
for s in cands:
    xa, xb = s['min'][0], s['max'][0]; xc = (xa + xb) / 2
    zf, zb = s['max'][2], s['min'][2]
    prof = []
    z = zf + 0.6
    while z > zb - 1.0:
        i, j = cell(xc, z)
        prof.append((round(z, 2), support[i][j]))
        z -= 0.02
    prof2 = []
    for zz, yy in prof:
        if not prof2 or prof2[-1][1] != yy: prof2.append((zz, yy))
    levels = [y for _, y in prof2 if y is not None]
    rises = [round(levels[k] - levels[k - 1], 4) for k in range(1, len(levels))]
    up = [r for r in rises if r > 0.01]
    if len(up) < 3: continue
    # tread depths from the profile change points between first and last riser
    zs = [zz for zz, _ in prof2]
    treads = [round(zs[k] - zs[k + 1], 2) for k in range(1, len(zs) - 2)]
    stairs.append({'island': s, 'xMin': xa, 'xMax': xb, 'xCentre': round(xc, 4), 'width': round(xb - xa, 4),
                   'risers': len(up), 'rises': up, 'riseMax': max(up), 'treadsFromProfile_0.02m': treads,
                   'footZ': round(zf, 4), 'headZ': round(zb, 4), 'topLanding': levels[-1] if levels else None,
                   'centreProfileChanges': prof2})
stairs.sort(key=lambda s: s['xCentre'])

# floor + door opening for each stair: floor height just inside, lintel underside above head of stair
for st in stairs:
    zin = st['headZ'] - 0.6
    i, j = cell(st['xCentre'], zin)
    st['floorInside'] = support[i][j]
    hs = column(st['xCentre'], st['headZ'] - 0.3)
    st['columnAtDoor'] = hs[:6]
    # clear opening width at door line: scan x across at 1.5 m above floor
    yy = (st['floorInside'] or st['topLanding']) + 1.2
    zz = st['headZ'] - 0.3
    left = right = None
    for sgn in (-1, 1):
        o = to_bl(st['xCentre'], yy, zz)
        loc, n, idx, dist = bvh.ray_cast(o, Vector((sgn, 0, 0)), 10)
        if sgn < 0: left = round(dist, 4) if loc else None
        else: right = round(dist, 4) if loc else None
    st['doorClearWidthAt1.2m'] = round((left or 0) + (right or 0), 4) if left and right else None
    up = bvh.ray_cast(to_bl(st['xCentre'], (st['floorInside'] or st['topLanding']) + 0.01, zz), Vector((0, 0, 1)), 10)
    st['doorClearHeight'] = round(up[3], 4) if up[0] else None

# ---------- receiving shelter detection: largest roof-like island with ground clearance > 2.5 m (no names) ----------
roofs = [s for s in islands if s['min'][1] > 2.5 and (s['max'][0] - s['min'][0]) > 5 and (s['max'][2] - s['min'][2]) > 3
         and s['max'][1] < 4.0]
shelter = max(roofs, key=lambda s: (s['max'][0] - s['min'][0]) * (s['max'][2] - s['min'][2])) if roofs else None

# ---------- body-envelope reachability ----------
def free_grid(width):
    r = int(math.ceil((width / 2) / STEP))
    base = [[support[i][j] is not None for j in range(nz)] for i in range(nx)]
    # neighbour rise test is in BFS; here dilate blocked cells by half-width (square kernel)
    blocked = [[not base[i][j] for j in range(nz)] for i in range(nx)]
    out = [[True] * nz for _ in range(nx)]
    for i in range(nx):
        for j in range(nz):
            if blocked[i][j]:
                for a in range(max(0, i - r), min(nx, i + r + 1)):
                    for b in range(max(0, j - r), min(nz, j + r + 1)):
                        out[a][b] = False
    # lateral body cross-section (x axis, i.e. perpendicular to the N-S stair runs): every cell within
    # +-half-width at the same z must be supported within 0.05 m of the centre cell (catches 1.5 m stair edges)
    for i in range(nx):
        for j in range(nz):
            if not out[i][j]: continue
            c = support[i][j]
            for a in range(max(0, i - r), min(nx, i + r + 1)):
                s2 = support[a][j]
                if s2 is None or abs(s2 - c) > 0.05:
                    out[i][j] = False; break
            if i - r < 0 or i + r >= nx: out[i][j] = False
    return out

def bfs(free, sources):
    dist = [[-1] * nz for _ in range(nx)]
    prev = {}
    dq = deque()
    for s in sources:
        if free[s[0]][s[1]]:
            dist[s[0]][s[1]] = 0; dq.append(s)
    while dq:
        i, j = dq.popleft()
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = i + di, j + dj
            if 0 <= a < nx and 0 <= b < nz and dist[a][b] < 0 and free[a][b]:
                if abs(support[a][b] - support[i][j]) <= MAXRISE:
                    dist[a][b] = dist[i][j] + 1; prev[(a, b)] = (i, j); dq.append((a, b))
    return dist, prev

import heapq
def dijkstra8(free, sources):
    INF = 1e18
    dist = [[INF] * nz for _ in range(nx)]
    pq = []
    for a, b in sources:
        if free[a][b]: dist[a][b] = 0.0; pq.append((0.0, a, b))
    heapq.heapify(pq)
    while pq:
        d0, i, j = heapq.heappop(pq)
        if d0 > dist[i][j]: continue
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if not di and not dj: continue
                a, b = i + di, j + dj
                if not (0 <= a < nx and 0 <= b < nz) or not free[a][b]: continue
                if di and dj and not (free[i + di][j] and free[i][j + dj]): continue
                if abs(support[a][b] - support[i][j]) > MAXRISE: continue
                nd = d0 + (1.41421356 if di and dj else 1.0)
                if nd < dist[a][b]: dist[a][b] = nd; heapq.heappush(pq, (nd, a, b))
    return dist

routes = {}
if shelter:
    sx0, sx1, sz0, sz1 = shelter['min'][0], shelter['max'][0], shelter['min'][2], shelter['max'][2]
    src_cells = []
    for i in range(nx):
        x = X0 + (i + 0.5) * STEP
        if not (sx0 < x < sx1): continue
        for j in range(nz):
            z = Z0 + (j + 0.5) * STEP
            if sz0 < z < sz1: src_cells.append((i, j))
    for width in (0.6, 0.9, 1.2, 1.5, 1.8):
        free = free_grid(width)
        dist, prev = bfs(free, src_cells)
        r = {'freeSourceCells': sum(1 for c in src_cells if free[c[0]][c[1]])}
        for k, st in enumerate(stairs):
            tag = 'stair%d_x%.2f' % (k, st['xCentre'])
            # target 1: stair foot (ground cell 0.15 m in front of first step, on centreline)
            fi, fj = cell(st['xCentre'], st['footZ'] + 0.15)
            # target 2: granary floor just inside door
            ti, tj = cell(st['xCentre'], st['headZ'] - 0.6)
            d1 = dist[fi][fj]; d2 = dist[ti][tj]
            path = []
            if d1 >= 0:
                c = (fi, fj)
                while c in prev: path.append(c); c = prev[c]
                path.append(c)
            hs = [support[a][b] for a, b in path]
            r[tag] = {'footReach': d1 >= 0, 'footRouteLen_m': round(d1 * STEP, 2) if d1 >= 0 else None,
                      'floorReach': d2 >= 0, 'floorRouteLen_m': round(d2 * STEP, 2) if d2 >= 0 else None,
                      'footRouteSupportMinMax': [min(hs), max(hs)] if hs else None,
                      'footRouteMaxNeighbourRise': round(max([abs(hs[k] - hs[k - 1]) for k in range(1, len(hs))] or [0]), 4) if hs else None,
                      'footRouteStartEnd_local': [[round(X0 + (path[-1][0] + .5) * STEP, 2), round(Z0 + (path[-1][1] + .5) * STEP, 2)],
                                                  [round(X0 + (path[0][0] + .5) * STEP, 2), round(Z0 + (path[0][1] + .5) * STEP, 2)]] if path else None}
        d8 = dijkstra8(free, src_cells)
        for k, st in enumerate(stairs):
            tag = 'stair%d_x%.2f' % (k, st['xCentre'])
            fi, fj = cell(st['xCentre'], st['footZ'] + 0.15)
            ti, tj = cell(st['xCentre'], st['headZ'] - 0.6)
            r[tag]['footRouteLen8_m'] = round(d8[fi][fj] * STEP, 2) if d8[fi][fj] < 1e17 else None
            r[tag]['floorRouteLen8_m'] = round(d8[ti][tj] * STEP, 2) if d8[ti][tj] < 1e17 else None
        # ground edge -> shelter (where an outside road would have to arrive)
        band = int(round(1.0 / STEP))  # sources: every cell within 1 m of the ground-slab edge
        edge = [(i, j) for i in range(nx) for j in range(nz) if i < band or j < band or i >= nx - band or j >= nz - band]
        de, _ = bfs(free, edge)
        reach = [de[c[0]][c[1]] for c in src_cells if de[c[0]][c[1]] >= 0]
        r['groundEdgeToShelter_minLen_m'] = round(min(reach) * STEP, 2) if reach else None
        routes['width_%.1f' % width] = r

# ---------- front-field obstacle census between shelter and stairs ----------
field = None
if shelter and stairs:
    fx0 = min(s['xMin'] for s in stairs) - 2; fx1 = max(s['xMax'] for s in stairs) + 2
    fz0 = max(s['footZ'] for s in stairs); fz1 = shelter['max'][2] + 2
    obst = [s for s in islands if s['max'][0] > fx0 and s['min'][0] < fx1 and s['max'][2] > fz0 and s['min'][2] < fz1
            and s['max'][1] > ground_y + 0.01 and s['min'][1] < ground_y + HEAD]
    sup_ok = sum(1 for i in range(nx) for j in range(nz)
                 if fx0 < X0 + (i + .5) * STEP < fx1 and fz0 < Z0 + (j + .5) * STEP < fz1 and support[i][j] is not None and abs(support[i][j] - ground_y) < 0.005)
    tot = sum(1 for i in range(nx) for j in range(nz)
              if fx0 < X0 + (i + .5) * STEP < fx1 and fz0 < Z0 + (j + .5) * STEP < fz1)
    field = {'box_local': [fx0, fz0, fx1, fz1], 'cells': tot, 'cellsOnGroundPlane': sup_ok,
             'obstacleIslands': obst}

# ---------- ground plane island ----------
ground_islands = [s for s in islands if abs(s['max'][1] - ground_y) < 0.005 and (s['max'][0] - s['min'][0]) > 50]

uns = [[round(X0 + (i + .5) * STEP, 2), round(Z0 + (j + .5) * STEP, 2)] for i in range(nx) for j in range(nz) if support[i][j] is None]
uns_box = [min(u[0] for u in uns), min(u[1] for u in uns), max(u[0] for u in uns), max(u[1] for u in uns)] if uns else None
res = {"unsupportedCells_local_xz": uns, 'unsupportedBox_local_xz': uns_box, 'src': src, 'sha256': hashlib.sha256(open(src, 'rb').read()).hexdigest(), 'anchor_gltf': [AX, 0, AZ],
       'gridStep_m': STEP, 'headroom_m': HEAD, 'maxNeighbourRise_m': MAXRISE,
       'objects': objects, 'islandCount': len(islands), 'groundY': ground_y, 'unsupportedCells': unsupported,
       'groundIslands': ground_islands, 'stairs': stairs, 'shelter': shelter, 'frontField': field, 'routes': routes,
       'islands': islands}
json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE', out, 'islands', len(islands), 'stairs', len(stairs), 'ground', ground_y)
