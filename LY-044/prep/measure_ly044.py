# LY-044 prep measurement (read-only on inputs).
# D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P measure_ly044.py -- <lab_root> <out.json>
# All reported coordinates are glTF axes (x east, y up, z = -local north), metres.
# Scope: surface ray casting / vertex comparison. NOT solid collision, NOT GPU, NOT walking simulation,
# NOT combustion/smoke/fire safety.
import bpy, sys, os, json, math, hashlib
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
LAB, OUT = argv[0], argv[1]
CITY = os.path.join(LAB, 'docs/cities/luoyang')
LIB = os.path.join(LAB, 'docs/library/models')

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()

SHAS = {}
def load(path):
    """Import a GLB into an empty scene; return {node_name: (verts Nx3 glTF world, tris Mx3)}."""
    SHAS[os.path.relpath(path, LAB).replace('\\', '/')] = sha(path)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    dg = bpy.context.evaluated_depsgraph_get()
    out = {}
    for o in bpy.context.scene.objects:
        if o.type != 'MESH': continue
        # original glTF node name: importer keeps it as object name (possibly with .001 suffix kept from file)
        me = o.evaluated_get(dg).to_mesh()
        me.calc_loop_triangles()
        mw = o.matrix_world
        v = np.array([tuple(mw @ x.co) for x in me.vertices], dtype=np.float64).reshape(-1, 3)
        v = np.stack([v[:, 0], v[:, 2], -v[:, 1]], axis=1)  # Blender -> glTF axes
        t = np.array([tuple(lt.vertices) for lt in me.loop_triangles], dtype=np.int64).reshape(-1, 3)
        name = o.get('glTF_node_name') or o.name
        out[name] = (v, t)
        o.evaluated_get(dg).to_mesh_clear()
    return out

def apply_m(v, m):  # m column-major 16
    M = np.array(m, dtype=np.float64).reshape(4, 4).T
    h = np.c_[v, np.ones(len(v))]
    return (h @ M.T)[:, :3]

def bbox(v):
    return [list(map(float, v.min(0))), list(map(float, v.max(0)))]

def bvh(parts, region=None):
    V, T, off = [], [], 0
    for v, t in parts:
        if region is not None and len(t):
            (x0, z0, x1, z1) = region
            c = v[t].mean(1)
            lo = v[t].min(1); hi = v[t].max(1)
            keep = (hi[:, 0] >= x0) & (lo[:, 0] <= x1) & (hi[:, 2] >= z0) & (lo[:, 2] <= z1)
            t = t[keep]
        if not len(t): continue
        V.append(v); T.append(t + off); off += len(v)
    if not V: return None, 0
    V = np.vstack(V); T = np.vstack(T)
    return BVHTree.FromPolygons([Vector(p) for p in V], [tuple(map(int, x)) for x in T], all_triangles=True), len(T)

R = {'tool': 'measure_ly044.py', 'scope': 'surface ray casts on a grid + vertex comparison; not solid collision, not GPU, not gait, not combustion/smoke/fire safety', 'inputs': SHAS}

# ---------- A. stove A/B and W2 ----------
stoves = {}
for fam in ('A', 'B'):
    for lod in (0, 1, 2):
        p = os.path.join(LIB, f'm-luoyang-cooking-stove/files/stove-{fam}-LOD{lod}.glb')
        nodes = load(p)
        rec = {'file': os.path.relpath(p, LAB).replace('\\', '/'), 'nodes': {}}
        allv = np.vstack([v for v, t in nodes.values()])
        ymin = allv[:, 1].min()
        for n, (v, t) in nodes.items():
            bot = v[v[:, 1] < ymin + 0.002]
            rec['nodes'][n] = {'tris': int(len(t)), 'bbox': bbox(v),
                               'bottomVerts': int(len(bot)),
                               'bottomFootprint': bbox(bot) if len(bot) else None}
        rec['bbox'] = bbox(allv)
        # fire-mouth / opening probe on earth body faces (horizontal rays inward)
        earth = [k for k in nodes if k.endswith('earth')][0]
        ev, et = nodes[earth]
        tree, _ = bvh([(ev, et)])
        (x0, y0, z0), (x1, y1, z1) = ev.min(0), ev.max(0)
        probes = {}
        for side, (n_out, lat_axis) in {'+x': ((1, 0, 0), 2), '-x': ((-1, 0, 0), 2), '+z': ((0, 0, 1), 0), '-z': ((0, 0, -1), 0)}.items():
            n_out = np.array(n_out, float)
            face = {'+x': x1, '-x': x0, '+z': z1, '-z': z0}[side]
            lat = np.arange((z0 if lat_axis == 2 else x0) + 0.0125, (z1 if lat_axis == 2 else x1), 0.025)
            hs = np.arange(y0 + 0.0125, y1 - 0.12, 0.025)  # exclude top-surface skim and pot rims
            deep = []
            for a in lat:
                for h in hs:
                    o = np.zeros(3); o[1] = h; o[lat_axis] = a
                    ax = 0 if side[1] == 'x' else 2
                    o[ax] = face + n_out[ax] * 0.3
                    hit = tree.ray_cast(Vector(o), Vector(-n_out), 5.0)
                    d = (hit[3] - 0.3) if hit[0] is not None else 9.9
                    if d > 0.08: deep.append((float(a), float(h), float(min(d, 9.9))))
            probes[side] = {'openCells_0.025m': len(deep),
                            'openArea_m2': round(len(deep) * 0.025 * 0.025, 4),
                            'lateralRange': [min(d[0] for d in deep), max(d[0] for d in deep)] if deep else None,
                            'heightRange': [min(d[1] for d in deep), max(d[1] for d in deep)] if deep else None,
                            'maxDepth_m': max(d[2] for d in deep) if deep else 0}
        rec['earthOpeningsByFace'] = probes
        rec['fireMouthFace'] = max(probes, key=lambda s: probes[s]['openArea_m2'])
        stoves[f'{fam}-LOD{lod}'] = rec
        if fam == 'A':
            stoves[f'{fam}-LOD{lod}']['_verts'] = {n: v for n, (v, t) in nodes.items()}
# W2 vs stove-A
w2 = {}
for lod in (0, 1, 2):
    p = os.path.join(LIB, f'm-luoyang-residential-preparation/files/W2-stove-A-LOD{lod}.glb')
    nodes = load(p)
    allv = np.vstack([v for v, t in nodes.values()])
    base = stoves[f'A-LOD{lod}'].pop('_verts')
    cmp = {}
    for n, (v, t) in nodes.items():
        src = [k for k in base if n.endswith(k)][0]
        from mathutils.kdtree import KDTree
        kd = KDTree(len(base[src]))
        for i, q in enumerate(base[src]): kd.insert(Vector(q), i)
        kd.balance()
        vv = v - np.array([489.4, 0.2, -1003.8])
        dmax = max(kd.find(Vector(q))[2] for q in vv)
        cmp[n] = {'source': src, 'tris': int(len(t)), 'sourceTris': None, 'sameVertexCount': len(base[src]) == len(v),
                  'maxNearestVertexDist_m_after_offset': float(dmax)}
    w2[f'LOD{lod}'] = {'file': os.path.relpath(p, LAB).replace('\\', '/'), 'bbox': bbox(allv), 'nodes': cmp,
                       'assumedOffset': [489.4, 0.2, -1003.8]}
for k in stoves: stoves[k].pop('_verts', None)
R['stoves'] = stoves
R['W2'] = w2

# ---------- B. W2 support on its own life-block ground (13-yard block, read only) ----------
w2v = None
nodes = load(os.path.join(LIB, 'm-luoyang-residential-preparation/files/W2-stove-A-LOD0.glb'))
w2bot = []
for n, (v, t) in nodes.items():
    w2bot.append(v[v[:, 1] < 0.2 + 0.002])
w2bot = np.vstack(w2bot)
lb = load(os.path.join(LIB, 'm-luoyang-residential-life/files/life-block-LOD0.glb'))
reg = (486.0, -1007.0, 493.0, -1000.5)
tree, ntri = bvh(list(lb.values()), reg)
gaps = []
for p in w2bot:
    hit = tree.ray_cast(Vector((p[0], p[1] + 0.5, p[2])), Vector((0, -1, 0)), 3.0) if tree else (None,)
    gaps.append(float(p[1] - hit[0][1]) if hit[0] is not None else None)
near = []
for n, (v, t) in lb.items():
    m = (v[:, 0] > reg[0]) & (v[:, 0] < reg[2]) & (v[:, 2] > reg[1]) & (v[:, 2] < reg[3])
    if m.any(): near.append(n)
R['W2_on_lifeblock'] = {'bottomVerts': int(len(w2bot)), 'unsupported': sum(g is None for g in gaps),
                        'gap_min': min(g for g in gaps if g is not None) if any(g is not None for g in gaps) else None,
                        'gap_max': max(g for g in gaps if g is not None) if any(g is not None for g in gaps) else None,
                        'lifeblockTrisInRegion': ntri, 'lifeblockNodesNearW2': sorted(near)[:40],
                        'note': 'first surface below each bottom vertex; a negative gap means the vertex is below that surface'}

# ---------- C. candidate yards in the city (calt matrices) on the actual city ground ----------
gcache = {}
def ground_parts():
    if gcache: return gcache
    for gid, rel, tr in (('ground-network', 'assets/ground-atomic/network-ground-stitched.glb', (0, 0, 0)),
                         ('ground-retained', 'assets/ground-atomic/retained.glb', (0, 0, 0)),
                         ('ground-south', 'assets/ground-atomic/south.glb', (0, 0, 0)),
                         ('ground-D08', 'assets/ground-atomic/D08.glb', (580, 0, -960))):
        nd = load(os.path.join(CITY, rel))
        gcache[gid] = [(v + np.array(tr, float), t) for v, t in nd.values()]
    return gcache

layout = json.load(open(os.path.join(CITY, 'data/c02v/layout.json'), encoding='utf-8'))
calt = json.load(open(os.path.join(CITY, 'data/far44/instances-calt.json'), encoding='utf-8'))
SHAS['docs/cities/luoyang/data/c02v/layout.json'] = sha(os.path.join(CITY, 'data/c02v/layout.json'))
SHAS['docs/cities/luoyang/data/far44/instances-calt.json'] = sha(os.path.join(CITY, 'data/far44/instances-calt.json'))
EXCL = {'site_lot', 'site_neutral_lane', 'designed_hardpacked_activity_ground', 'designed_loading_yard',
        'designed_front_apron', 'designed_side_passage', 'designed_rear_work_ground'}
CASES = [('C02-010', 'assets/c02v/A2-LOD0-prototype.glb', 'assets/c02v/A2-LOD1-prototype.glb',
          ['site_lot', 'site_neutral_lane', 'designed_hardpacked_activity_ground']),
         ('C02-012', 'assets/c02v/TC03-2-LOD0-prototype.glb', 'assets/c02v/TC03-2-LOD1-prototype.glb', None)]
# city-data excludeNodes for courtyard-TC03-2 are read from city-data.mjs text
cd = open(os.path.join(CITY, 'city-data.mjs'), encoding='utf-8').read()
def city_excl(asset_id):
    i = cd.find(f'"id": "{asset_id}"'); j = cd.find('"excludeNodes"', i); k = cd.find(']', j)
    return json.loads(cd[j + len('"excludeNodes": '):k + 1])

BAND = (0.03, 2.0)   # C body band above ground (m)
GRID = 0.1
ROUTE_HALF = 0.45    # C corridor half-width
WORK_DEPTH = 0.9     # C stance strip in front of the fire mouth
TURN_R = 0.75        # C turning disk radius (1.5 m dia), centred 0.75 m in front of mouth centre
FLAT_TOL = 0.01

yards = {}
for lot_id, lod0, lod1, excl in CASES:
    row = [r for r in calt['rows'] if r['id'] == lot_id][0]
    lay = [l for l in layout['lots'] if l['id'] == lot_id][0]
    asset_id = 'courtyard-' + row['variant']
    excl = city_excl(asset_id)
    M = row['matrixGLTFColumnMajor']
    yrec = {'lot': lot_id, 'variant': row['variant'], 'calt_matrix': M, 'cityExcludeNodes': excl, 'lods': {}}
    for lodname, rel in (('LOD0', lod0), ('LOD1', lod1)):
        nd = load(os.path.join(CITY, rel))
        kept = {n: (apply_m(v, M), t) for n, (v, t) in nd.items() if n not in excl}
        yrec['lods'][lodname] = {'file': rel, 'keptNodes': {n: bbox(v) for n, (v, t) in kept.items()},
                                 'excludedNodesPresent': sorted(n for n in nd if n in excl)}
        if lodname == 'LOD0': kept0 = kept
    allv = np.vstack([v for v, t in kept0.values()])
    (bx0, _, bz0), (bx1, _, bz1) = allv.min(0), allv.max(0)
    reg = (bx0 - 1, bz0 - 1, bx1 + 1, bz1 + 1)
    gp = ground_parts()
    gtrees = {g: bvh(parts, reg) for g, parts in gp.items()}
    btree, bn = bvh(list(kept0.values()), reg)
    node_trees = [t for t in (bvh([vt], reg)[0] for vt in kept0.values()) if t is not None]
    xs = np.arange(bx0 + GRID / 2, bx1, GRID); zs = np.arange(bz0 + GRID / 2, bz1, GRID)
    G = np.full((len(zs), len(xs)), np.nan); SUP = np.full(G.shape, -1, int); OBS = np.zeros(G.shape, bool)
    gnames = list(gtrees)
    for iz, z in enumerate(zs):
        for ix, x in enumerate(xs):
            best = None
            for gi, g in enumerate(gnames):
                tr = gtrees[g][0]
                if tr is None: continue
                h = tr.ray_cast(Vector((x, 20.0, z)), Vector((0, -1, 0)), 40.0)
                if h[0] is not None and (best is None or h[0][1] > best[0]): best = (h[0][1], gi)
            # topmost building surface could also be "ground" (plinth top) -> treat building as obstruction only
            if best is None: continue
            G[iz, ix], SUP[iz, ix] = best
            g0 = best[0]
            # collect all building surface crossings on the vertical line (top -> down), pair them as solid
            # intervals (parity; meshes treated as closed shells), occupied if any interval or crossing
            # intersects the body band [g+0.03, g+2.0]
            lo_b, hi_b = g0 + BAND[0], g0 + BAND[1]
            occ = False
            for ntree in node_trees:   # parity per node (each node treated as its own closed shell)
                hy, y = [], 20.0
                while len(hy) <= 64:
                    h = ntree.ray_cast(Vector((x, y, z)), Vector((0, -1, 0)), y - (g0 - 0.5))
                    if h[0] is None: break
                    hy.append(h[0][1]); y = h[0][1] - 1e-4
                if any(lo_b <= q <= hi_b for q in hy): occ = True; break
                for k in range(0, len(hy), 2):
                    top = hy[k]; bot = hy[k + 1] if k + 1 < len(hy) else g0
                    if top >= lo_b and bot <= hi_b: occ = True; break
                if occ: break
            OBS[iz, ix] = occ
    # routes (local -> world through the calt matrix)
    def to_world(pt):
        return apply_m(np.array([[pt[0], 0.0, -pt[1]]]), M)[0]
    routes = {k: [list(map(float, to_world(p)[[0, 2]])) for p in pts] for k, pts in lay.get('localRoutes', {}).items()}
    RT = np.zeros(G.shape, bool)
    XX, ZZ = np.meshgrid(xs, zs)
    for pts in routes.values():
        for (ax, az), (cx, cz) in zip(pts[:-1], pts[1:]):
            dx, dz = cx - ax, cz - az; L2 = dx * dx + dz * dz or 1e-9
            tt = np.clip(((XX - ax) * dx + (ZZ - az) * dz) / L2, 0, 1)
            RT |= np.hypot(XX - (ax + tt * dx), ZZ - (az + tt * dz)) <= ROUTE_HALF
    FREE = ~np.isnan(G) & ~OBS
    # plinth / building footprint cells = obstruction
    yrec['grid'] = {'cell_m': GRID, 'x': [float(xs[0]), float(xs[-1])], 'z': [float(zs[0]), float(zs[-1])],
                    'cells': int(G.size), 'groundCells': int((~np.isnan(G)).sum()),
                    'groundSupplierCells': {gnames[i]: int((SUP == i).sum()) for i in range(len(gnames))},
                    'groundHeight_min_max': [float(np.nanmin(G)), float(np.nanmax(G))],
                    'obstructedCells_band_0.03_2.0': int(OBS.sum()), 'freeCells': int(FREE.sum()),
                    'routeCells': int(RT.sum()), 'freeNonRouteCells': int((FREE & ~RT).sum()),
                    'buildingTrisInRegion': bn}
    yrec['routesWorldXZ'] = routes
    # chessboard distance (cells) from obstruction/no-ground, capped at 40 cells
    OB = ~FREE
    D = np.where(OB, 0, 999).astype(int)
    cur = OB.copy()
    for k in range(1, 41):
        nb = cur.copy()
        nb[1:, :] |= cur[:-1, :]; nb[:-1, :] |= cur[1:, :]; nb[:, 1:] |= cur[:, :-1]; nb[:, :-1] |= cur[:, 1:]
        nb[1:, 1:] |= cur[:-1, :-1]; nb[:-1, :-1] |= cur[1:, 1:]; nb[1:, :-1] |= cur[:-1, 1:]; nb[:-1, 1:] |= cur[1:, :-1]
        D[(nb & ~cur)] = k; cur = nb
    D[D == 999] = 41
    # connected components of free & not-route & clearance>=3 cells (0.3 m)
    U = FREE & ~RT
    lab = np.zeros(U.shape, int); comps = []
    for (iz, ix) in zip(*np.nonzero(U)):
        if lab[iz, ix]: continue
        cid = len(comps) + 1; stack = [(iz, ix)]; lab[iz, ix] = cid; cells = []
        while stack:
            a, b = stack.pop(); cells.append((a, b))
            for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                c2, d2 = a + da, b + db
                if 0 <= c2 < U.shape[0] and 0 <= d2 < U.shape[1] and U[c2, d2] and not lab[c2, d2]:
                    lab[c2, d2] = cid; stack.append((c2, d2))
        cz_, cx_ = np.array(cells).T
        comps.append({'id': cid, 'area_m2': round(len(cells) * GRID * GRID, 2),
                      'x': [round(float(xs[cx_.min()]), 2), round(float(xs[cx_.max()]), 2)],
                      'z': [round(float(zs[cz_.min()]), 2), round(float(zs[cz_.max()]), 2)],
                      'maxClearance_m': round(float(D[cz_, cx_].max()) * GRID, 2)})
    comps.sort(key=lambda c: -c['area_m2'])
    yrec['freeNonRouteComponents'] = [c for c in comps if c['area_m2'] >= 0.5][:12]
    yrec['freeNonRouteComponentsTiny'] = sum(1 for c in comps if c['area_m2'] < 0.5)
    # endpoint probes (route ends)
    ends = {}
    btop, _ = bvh(list(kept0.values()), reg)
    for k, pts in routes.items():
        ex, ez = pts[-1]
        ix = int(np.clip(np.searchsorted(xs, ex), 0, len(xs) - 1)); iz = int(np.clip(np.searchsorted(zs, ez), 0, len(zs) - 1))
        h = btop.ray_cast(Vector((ex, 20.0, ez)), Vector((0, -1, 0)), 40.0)
        ends[k] = {'xz': [ex, ez], 'groundY': None if np.isnan(G[iz, ix]) else float(G[iz, ix]), 'obstructedBand': bool(OBS[iz, ix]),
                   'buildingTopY': float(h[0][1]) if h[0] is not None else None}
    yrec['routeEndpoints'] = ends
    # PNG mask: white free, grey route, black obstructed
    try:
        img = np.where(FREE, 255, 30).astype(np.uint8); img[RT & FREE] = 150
        import zlib, struct as st
        hgt, wid = img.shape
        raw = b''.join(bytes([0]) + img[r].tobytes() for r in range(hgt))
        def chunk(tag, data): return st.pack('>I', len(data)) + tag + data + st.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
        png = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]) + chunk(b'IHDR', st.pack('>IIBBBBB', wid, hgt, 8, 0, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')
        mp = os.path.join(os.path.dirname(OUT), f'mask-{lot_id}.png'); open(mp, 'wb').write(png)
        yrec['maskPNG'] = {'file': os.path.basename(mp), 'rows': 'z ascending top->bottom (row0 = z min = local north far side)', 'cols': 'x ascending', 'legend': '255 free, 150 route corridor, 30 obstructed/no ground'}
    except Exception as e:
        yrec['maskPNG'] = str(e)
    # candidate placements: stove A/B LOD0 footprint, 4 yaws, fire mouth side from probe
    cands = {}
    for fam in ('A', 'B'):
        s = stoves[f'{fam}-LOD0']
        (sx0, _, sz0), (sx1, _, sz1) = s['bbox']
        mouth = s['fireMouthFace']
        ok_list = []; tested = 0
        for yaw in (0, 90, 180, 270):
            c, si = round(math.cos(math.radians(yaw))), round(math.sin(math.radians(yaw)))
            # rotation about +y (glTF): x' = c*x + s*z ; z' = -s*x + c*z
            def rot(x, z): return c * x + si * z, -si * x + c * z
            corners = [rot(x, z) for x in (sx0, sx1) for z in (sz0, sz1)]
            fx0, fx1 = min(p[0] for p in corners), max(p[0] for p in corners)
            fz0, fz1 = min(p[1] for p in corners), max(p[1] for p in corners)
            mo = {'+x': (1, 0), '-x': (-1, 0), '+z': (0, 1), '-z': (0, -1)}[mouth]
            mn = rot(*mo)
            def sl(lo, hi, arr):
                i0 = int(np.searchsorted(arr, lo, 'left')); i1 = int(np.searchsorted(arr, hi, 'right'))
                return slice(i0, i1)
            for cx in np.arange(bx0 + 0.5, bx1 - 0.5, 0.2):
                for cz in np.arange(bz0 + 0.5, bz1 - 0.5, 0.2):
                    tested += 1
                    fsx = sl(cx + fx0 - 0.05, cx + fx1 + 0.05, xs); fsz = sl(cz + fz0 - 0.05, cz + fz1 + 0.05, zs)
                    if fsx.stop - fsx.start < round((fx1 - fx0 + 0.1) / GRID) - 1 or fsz.stop - fsz.start < round((fz1 - fz0 + 0.1) / GRID) - 1: continue
                    if fsx.start == 0 or fsz.start == 0 or fsx.stop >= len(xs) or fsz.stop >= len(zs): continue
                    fF = FREE[fsz, fsx]
                    if fF.size == 0 or not fF.all() or RT[fsz, fsx].any(): continue
                    gf = G[fsz, fsx]
                    if gf.max() - gf.min() > FLAT_TOL: continue
                    if mn[0]:
                        face = cx + (fx1 if mn[0] > 0 else fx0)
                        wsx = sl(min(face, face + mn[0] * WORK_DEPTH), max(face, face + mn[0] * WORK_DEPTH), xs); wsz = sl(cz + fz0, cz + fz1, zs)
                        mcx, mcz = face + mn[0] * TURN_R, cz
                    else:
                        face = cz + (fz1 if mn[1] > 0 else fz0)
                        wsz = sl(min(face, face + mn[1] * WORK_DEPTH), max(face, face + mn[1] * WORK_DEPTH), zs); wsx = sl(cx + fx0, cx + fx1, xs)
                        mcx, mcz = cx, face + mn[1] * TURN_R
                    tsx = sl(mcx - TURN_R, mcx + TURN_R, xs); tsz = sl(mcz - TURN_R, mcz + TURN_R, zs)
                    disk = np.hypot(XX[tsz, tsx] - mcx, ZZ[tsz, tsx] - mcz) <= TURN_R
                    wF = FREE[wsz, wsx]; tF = FREE[tsz, tsx][disk]
                    if wF.size == 0 or tF.size == 0 or not wF.all() or not tF.all(): continue
                    if disk.sum() < 0.9 * math.pi * TURN_R ** 2 / GRID ** 2: continue  # disk clipped by grid edge
                    gz = np.concatenate([G[wsz, wsx].ravel(), G[tsz, tsx][disk]])
                    if gz.max() - gz.min() > 0.05: continue
                    rc = int(RT[wsz, wsx].sum() + RT[tsz, tsx][disk].sum())
                    ok_list.append({'yaw': yaw, 'origin_xz': [round(float(cx), 3), round(float(cz), 3)],
                                    'groundY': round(float(gf.mean()), 4), 'workZoneRouteCells': rc,
                                    'minClearanceFootprint_m': round(float(D[fsz, fsx].min()) * GRID, 2),
                                    'yawsMouthNormal_xz': list(mn)})
        cands[fam] = {'tested': tested, 'feasible': len(ok_list),
                      'feasibleWithoutRouteOverlapInWorkZone': sum(1 for o in ok_list if o['workZoneRouteCells'] == 0),
                      'byYaw': {y: sum(1 for o in ok_list if o['yaw'] == y and o['workZoneRouteCells'] == 0) for y in (0, 90, 180, 270)},
                      'mostClear': sorted([o for o in ok_list if o['workZoneRouteCells'] == 0], key=lambda o: -o['minClearanceFootprint_m'])[:5]}
    yrec['placementSearch'] = {'params': {'grid_m': GRID, 'band_m': BAND, 'routeHalfWidth_m': ROUTE_HALF,
                                          'workDepth_m': WORK_DEPTH, 'turnRadius_m': TURN_R, 'footFlatTol_m': FLAT_TOL,
                                          'footInflate_m': 0.05, 'step_m': 0.2, 'class': 'C engineering design, not historical'},
                               'results': cands}
    yards[lot_id] = yrec
R['yards'] = yards
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(R, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE', OUT)
