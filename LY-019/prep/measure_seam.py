# LY-019 prep measurement (read-only inputs). Blender 4.x headless:
#   blender -b --factory-startup --python-exit-code 1 -P measure_seam.py -- OUT.json key=path.glb [key=path.glb ...]
# Keys used: lib1, lib2 (B-library-v1 LOD1/LOD2, origin-centred), mst_a (city_gate_xia-B-01 chunk,
# world-placed), mst_t1..mst_t4 (xia-B static_tile fragments), wA00, wA11, wB00, wB11 (city wall segments).
# All measurement is done in Blender Z-up after the glTF importer's (x,y,z)->(x,-z,y) conversion.
# Gate-local frame = inverse of the master placement of xia-B (translation + Z rotation) read from the
# master chunk itself, so lib LOD1/LOD2 are tested at exactly the same C placement.
import bpy, bmesh, sys, json, math, hashlib
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
out_path = argv[0]
inputs = dict(a.split('=', 1) for a in argv[1:])

bpy.ops.wm.read_factory_settings(use_empty=True)
objs = {}
for key, path in inputs.items():
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    objs[key] = new
dg = bpy.context.evaluated_depsgraph_get()

def find(key, sub):
    for o in objs.get(key, []):
        if sub in o.name:
            return o
    return None

# --- gate placement from master earth node -------------------------------------------------
mst_earth = find('mst_a', 'static_earth')
M = mst_earth.matrix_world.copy()
loc, rot, scl = M.decompose()
ang = rot.to_euler().z
Minv = M.inverted()
res = {'placement': {'translation_blender_zup': list(loc), 'rot_z_deg': math.degrees(ang), 'scale': list(scl),
                     'note': 'taken from master chunk city_gate_xia-B-01 xia-B-static_earth world matrix'}}
# put library gate at the same placement
for key in ('lib1', 'lib2'):
    for o in objs.get(key, []):
        if o.parent is None:
            o.matrix_world = M @ o.matrix_world
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()

def local_mesh(o):
    """vertices/polys in gate-local frame"""
    me = o.evaluated_get(dg).to_mesh()
    T = Minv @ o.matrix_world
    verts = [T @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    bm = bmesh.new(); bm.from_mesh(me); bm.transform(T)
    o.evaluated_get(dg).to_mesh_clear()
    return verts, polys, bm

def bm_stats(bm):
    nm = sum(1 for e in bm.edges if not e.is_manifold)
    bnd = sum(1 for e in bm.edges if e.is_boundary)
    vol = abs(bm.calc_volume(signed=True)) if nm == 0 else None
    return {'verts': len(bm.verts), 'faces': len(bm.faces), 'nonManifoldEdges': nm, 'boundaryEdges': bnd,
            'closedVolume_m3': vol}

def bbox(vs):
    return [[round(min(v[i] for v in vs), 4) for i in range(3)], [round(max(v[i] for v in vs), 4) for i in range(3)]]

def vhash(vs):
    s = sorted((round(v.x, 3), round(v.y, 3), round(v.z, 3)) for v in vs)
    return hashlib.sha256(json.dumps(s).encode()).hexdigest()[:16]

def intervals(hits_bool, xs):
    out = []; cur = None
    for x, h in zip(xs, hits_bool):
        if h and cur is None: cur = [x, x]
        elif h: cur[1] = x
        elif cur is not None: out.append(cur); cur = None
    if cur: out.append(cur)
    return [[round(a, 3), round(b, 3)] for a, b in out]

def inside_count(bvh, p, d=Vector((0, 0, 1))):
    n = 0; q = p.copy()
    for _ in range(64):
        h = bvh.ray_cast(q, d)
        if h[0] is None: break
        n += 1; q = h[0] + d * 1e-4
    return n

gates = {}
for gk in ('lib1', 'lib2', 'mst'):
    gkey = 'mst_a' if gk == 'mst' else gk
    e = find(gkey, 'static_earth'); t = find(gkey, 'static_timber')
    tile = find(gkey, 'static_tile')
    tiles = [tile] if tile else [o for k in ('mst_t1', 'mst_t2', 'mst_t3', 'mst_t4') for o in objs.get(k, [])]
    ev, ep, ebm = local_mesh(e)
    tv, tp, tbm = local_mesh(t)
    tiv = []
    for o in tiles:
        v, p, b = local_mesh(o); tiv += v; b.free()
    ebvh = BVHTree.FromBMesh(ebm)
    g = {'earth': {'bbox_local': bbox(ev), 'vhash': vhash(ev), **bm_stats(ebm)},
         'timber': {'bbox_local': bbox(tv), 'vhash': vhash(tv), **bm_stats(tbm)},
         'tile': {'bbox_local': bbox(tiv) if tiv else None, 'verts': len(tiv)}}
    # bottom support footprint: downward faces at z ~ min
    zmin = min(v.z for v in ev)
    area = sum(f.calc_area() for f in ebm.faces if f.normal.z < -0.99 and abs(f.calc_center_median().z - zmin) < 1e-3)
    g['earth']['zmin'] = round(zmin, 4); g['earth']['bottomFaceArea_m2'] = round(area, 3)
    # openings: rays along local +Y through the depth at heights z, sweep x
    xs = [round(-17 + i * 0.05, 3) for i in range(int(34 / 0.05) + 1)]
    op = {}
    for z in (0.3, 1.0, 2.5, 4.0, 5.0):
        solid = []
        for x in xs:
            h = ebvh.ray_cast(Vector((x, -30, z)), Vector((0, 1, 0)))
            solid.append(h[0] is not None)
        op[str(z)] = {'solidX': intervals(solid, xs),
                      'openX': intervals([not s for s in solid], xs)}
    g['openingsSweep'] = op
    # clearance at opening centres measured at z=1.0
    opens = [iv for iv in op['1.0']['openX'] if iv[0] > -16.9 and iv[1] < 16.9]
    clr = []
    for a, b in opens:
        xc = (a + b) / 2
        h = ebvh.ray_cast(Vector((xc, 0, 0.01)), Vector((0, 0, 1)))
        hd = ebvh.ray_cast(Vector((xc, -30, 1.0)), Vector((0, 1, 0)))
        clr.append({'x': [a, b], 'width_m': round(b - a + 0.05, 3), 'soffit_z_at_centre': round(h[0].z, 4) if h[0] else None,
                    'firstHitDepthY': round(hd[0].y, 3) if hd[0] else None})
    g['openings'] = clr
    # outer side faces of earth: x extent per z band
    side = {}
    for z in (0.3, 3.0, 6.0, 7.0, 8.0, 9.5, 10.3):
        ys = [round(-11 + i * 0.25, 3) for i in range(89)]
        wmin = []; emax = []
        for y in ys:
            h1 = ebvh.ray_cast(Vector((-60, y, z)), Vector((1, 0, 0)))
            h2 = ebvh.ray_cast(Vector((60, y, z)), Vector((-1, 0, 0)))
            if h1[0]: wmin.append((y, h1[0].x))
            if h2[0]: emax.append((y, h2[0].x))
        side[str(z)] = {'westFace_x': [round(min(x for _, x in wmin), 3), round(max(x for _, x in wmin), 3)] if wmin else None,
                        'westFace_y': [min(y for y, _ in wmin), max(y for y, _ in wmin)] if wmin else None,
                        'eastFace_x': [round(min(x for _, x in emax), 3), round(max(x for _, x in emax), 3)] if emax else None}
    g['earthSideProfile'] = side
    gates[gk] = g
    gates[gk]['_bvh'] = ebvh
    gates[gk]['_bm'] = ebm
    tbm.free()

# --- walls -----------------------------------------------------------------------------
walls = {}
for wk in ('wA00', 'wA11', 'wB00', 'wB11'):
    o = objs[wk][0]
    v, p, bm = local_mesh(o)
    near = sorted(v, key=lambda q: abs(q.x))[:12]
    side = 'west' if wk.endswith('11') else 'east'
    # end-cap vertices: those within 0.05 m (local x) of the extreme-near end
    if side == 'west':
        xe = max(q.x for q in v if q.x < 5)
        cap = [q for q in v if abs(q.x - xe) < 0.6 and q.x < 5]
    else:
        xe = min(q.x for q in v if q.x > -5)
        cap = [q for q in v if abs(q.x - xe) < 0.6 and q.x > -5]
    walls[wk] = {'side': side, 'stats': bm_stats(bm), 'nearestVertsLocal': [[round(c, 4) for c in q] for q in near],
                 'capVertsLocal': [[round(c, 4) for c in q] for q in cap], 'cap_bbox': bbox(cap),
                 'zmin_all': round(min(q.z for q in v), 4), 'zmax_all': round(max(q.z for q in v), 4)}
    walls[wk]['_bvh'] = BVHTree.FromBMesh(bm); walls[wk]['_bm'] = bm

# --- seam sampling ---------------------------------------------------------------------
step = 0.25
seams = {}
for gk in ('lib1', 'mst'):
    G = gates[gk]['_bvh']
    for wk in ('wA11', 'wA00', 'wB11', 'wB00'):
        W = walls[wk]['_bvh']; west = walls[wk]['side'] == 'west'
        dgx = Vector((1, 0, 0)) if west else Vector((-1, 0, 0))
        far = -60 if west else 60
        both = []; wallOnly = 0; gateOnly = 0; overlap = 0
        for iy in range(int(24 / step) + 1):
            y = -12 + iy * step
            for iz in range(int(11 / step)):
                z = 0.125 + iz * step
                hg = G.ray_cast(Vector((far, y, z)), dgx)            # outer face of gate on this side
                hw = W.ray_cast(Vector((0, y, z)), -dgx)             # wall end face seen from gate centre
                if hw[0] is not None and abs(hw[0].x) > 40: hw = (None,)
                if hg[0] is not None and hw[0] is not None:
                    gap = (hg[0].x - hw[0].x) if west else (hw[0].x - hg[0].x)
                    both.append((y, z, gap))
                elif hw[0] is not None: wallOnly += 1
                elif hg[0] is not None: gateOnly += 1
        cell = step * step
        gaps = sorted(g for _, _, g in both)
        rec = {'cell_m': step, 'bothHit_cells': len(both),
               'gap_m': {'min': round(gaps[0], 4), 'median': round(gaps[len(gaps) // 2], 4), 'max': round(gaps[-1], 4)} if gaps else None,
               'overlapCells(gap<-1mm)': sum(1 for g in gaps if g < -0.001),
               'openGapCells(gap>1mm)': sum(1 for g in gaps if g > 0.001),
               'flushCells(|gap|<=1mm)': sum(1 for g in gaps if abs(g) <= 0.001),
               'wallEndExposed_m2': round(wallOnly * cell, 3),
               'gateSideExposed_m2(on wall line band)': round(gateOnly * cell, 3)}
        if both:
            zs = [z for _, z, _ in both]; ys = [y for y, _, _ in both]
            rec['contactBand_y'] = [min(ys), max(ys)]; rec['contactBand_z'] = [min(zs), max(zs)]
        seams[gk + '|' + wk] = rec

# --- volumetric overlap between gate earth and wall (boolean intersect, exact) --------------
def bm_to_obj(bm, name):
    me = bpy.data.meshes.new(name); bm.to_mesh(me)
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); return ob
inter = {}
for gk in ('lib1', 'mst'):
    for wk in ('wA11', 'wA00', 'wB11', 'wB00'):
        a = bm_to_obj(gates[gk]['_bm'].copy(), 'A_' + gk + wk)
        b = bm_to_obj(walls[wk]['_bm'].copy(), 'B_' + gk + wk)
        m = a.modifiers.new('x', 'BOOLEAN'); m.operation = 'INTERSECT'; m.solver = 'EXACT'; m.object = b
        bpy.context.view_layer.update()
        d2 = bpy.context.evaluated_depsgraph_get()
        me = a.evaluated_get(d2).to_mesh()
        bm = bmesh.new(); bm.from_mesh(me)
        vol = abs(bm.calc_volume(signed=True)) if len(bm.faces) else 0.0
        inter[gk + '|' + wk] = {'intersectVolume_m3': round(vol, 4), 'faces': len(bm.faces),
                                'bbox': bbox([v.co for v in bm.verts]) if bm.verts else None}
        bm.free(); a.evaluated_get(d2).to_mesh_clear()

# --- timber/tile support relative to earth top (local) ------------------------------------
for gk in ('lib1', 'lib2', 'mst'):
    g = gates[gk]
    g.pop('_bvh'); g.pop('_bm')
for wk in walls:
    walls[wk].pop('_bvh'); walls[wk].pop('_bm')

res.update({'inputs': inputs, 'gates': gates, 'walls': walls, 'seams': seams, 'intersections': inter,
            'lod_earth_identical_lib1_lib2': gates['lib1']['earth']['vhash'] == gates['lib2']['earth']['vhash'],
            'lod_timber_identical_lib1_lib2': gates['lib1']['timber']['vhash'] == gates['lib2']['timber']['vhash'],
            'earth_identical_lib1_master': gates['lib1']['earth']['vhash'] == gates['mst']['earth']['vhash']})
json.dump(res, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE', out_path)
