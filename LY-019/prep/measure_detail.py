# LY-019 prep measurement #2 (read-only inputs): welded topology, wing/pad profile, pier tops,
# timber bearing, wall-vs-wing section mismatch, tile duplicate/shared-edge counts.
#   blender -b --factory-startup --python-exit-code 1 -P measure_detail.py -- OUT.json key=path ...
# Same keys as measure_seam.py. Gate-local frame = inverse master placement of xia-B-static_earth.
import bpy, bmesh, sys, json, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
out_path = argv[0]
inputs = dict(a.split('=', 1) for a in argv[1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
objs = {}
for key, path in inputs.items():
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    objs[key] = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']

def find(key, sub):
    return next((o for o in objs.get(key, []) if sub in o.name), None)

M = find('mst_a', 'static_earth').matrix_world.copy(); Minv = M.inverted()
for key in ('lib1', 'lib2'):
    for o in objs.get(key, []):
        if o.parent is None: o.matrix_world = M @ o.matrix_world
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()

def welded(objlist, dist=1e-4):
    bm = bmesh.new()
    for o in objlist:
        me = o.evaluated_get(dg).to_mesh()
        tmp = bmesh.new(); tmp.from_mesh(me); tmp.transform(Minv @ o.matrix_world)
        me2 = bpy.data.meshes.new('t'); tmp.to_mesh(me2); bm.from_mesh(me2); tmp.free()
        o.evaluated_get(dg).to_mesh_clear()
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    return bm

def topo(bm):
    e_bnd = sum(1 for e in bm.edges if e.is_boundary)
    e_multi = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    keys = {}
    dup = 0
    for f in bm.faces:
        k = tuple(sorted(v.index for v in f.verts))
        if k in keys: dup += 1
        keys[k] = 1
    closed = e_bnd == 0 and e_multi == 0
    return {'verts': len(bm.verts), 'faces': len(bm.faces), 'boundaryEdges': e_bnd, 'edgesWith>2Faces': e_multi,
            'duplicateFaces': dup, 'closedManifold': closed,
            'signedVolume_m3': round(bm.calc_volume(signed=True), 4) if closed else None,
            'volumeIfTreatedClosed_m3': round(abs(bm.calc_volume(signed=True)), 4)}

res = {'inputs': inputs}
G = {}
for gk, gkey in (('lib1', 'lib1'), ('lib2', 'lib2'), ('mst', 'mst_a')):
    e = welded([find(gkey, 'static_earth')]); t = welded([find(gkey, 'static_timber')])
    tl = find(gkey, 'static_tile')
    tiles = [tl] if tl else [o for k in ('mst_t1', 'mst_t2', 'mst_t3', 'mst_t4') for o in objs.get(k, [])]
    ti = welded(tiles)
    eb = BVHTree.FromBMesh(e); tb = BVHTree.FromBMesh(t)
    g = {'earthTopo': topo(e), 'timberTopo': topo(t), 'tileTopo': topo(ti)}
    # earth top heights along x at y=0 (ray down) and pier tops
    prof = []
    for i in range(0, 69):
        x = -17 + i * 0.5
        h = eb.ray_cast(Vector((x, 0, 30)), Vector((0, 0, -1)))
        ht = tb.ray_cast(Vector((x, 0, 30)), Vector((0, 0, -1)))
        prof.append([x, round(h[0].z, 3) if h[0] else None])
    g['earthTopZ_alongX_y0'] = prof
    # timber lowest surface vs earth below at sampled points (bearing gap)
    bear = []
    for x in (-10.0, -9.5, -4.0, -3.5, 3.5, 4.0, 9.5, 10.0, -7.0, 0.0, 7.0):
        for y in (-4.25, 0.0, 4.25):
            hu = tb.ray_cast(Vector((x, y, 0.05)), Vector((0, 0, 1)))  # timber underside from below
            if hu[0] is None: continue
            he = eb.ray_cast(Vector((x, y, hu[0].z + 1e-3)), Vector((0, 0, -1)))  # earth BVH only; +1mm so a flush pier top is found
            bear.append({'x': x, 'y': y, 'timberUnderside_z': round(hu[0].z, 4),
                         'earthBelow_z': round(he[0].z, 4) if he[0] else None,
                         'verticalGap_m': round(hu[0].z - he[0].z, 4) if he[0] else None})
    g['timberBearing'] = bear
    # section of earth at x = +-13.5 (wing zone) and +-10.5 (end pier), y profile per z
    sec = {}
    for x in (-15.9, -13.5, -11.5, -10.5, 10.5, 11.5, 13.5, 15.9):
        rows = {}
        for z in (0.05, 0.1, 0.3, 1.0, 2.0, 3.0, 4.0, 5.0, 5.5, 6.0, 6.15, 6.25, 7.5):
            h1 = eb.ray_cast(Vector((x, -30, z)), Vector((0, 1, 0)))
            h2 = eb.ray_cast(Vector((x, 30, z)), Vector((0, -1, 0)))
            rows[str(z)] = [round(h1[0].y, 3) if h1[0] else None, round(h2[0].y, 3) if h2[0] else None]
        sec[str(x)] = rows
    g['earthSection_yExtent_at_x'] = sec
    # pad edge profile (master): along y at x=0 top surface
    pad = []
    for i in range(0, 49):
        y = -12 + i * 0.5
        h = eb.ray_cast(Vector((0.0, y, 30)), Vector((0, 0, -1)))
        pad.append([y, round(h[0].z, 4) if h[0] else None])
    g['earthTopZ_alongY_x0'] = pad
    # wing top height
    wt = eb.ray_cast(Vector((-13.5, 0, 30)), Vector((0, 0, -1)))
    g['wingTop_z_at_x-13.5'] = round(wt[0].z, 4) if wt[0] else None
    G[gk] = g
    e.free(); t.free(); ti.free()
res['gates'] = G

W = {}
for wk in ('wA00', 'wA11', 'wB00', 'wB11'):
    bm = welded(objs[wk]); b = BVHTree.FromBMesh(bm)
    xs = 16.5 if wk.endswith('00') else -16.5
    rows = {}
    for z in (0.2, 0.3, 1.0, 2.0, 3.0, 4.0, 5.0, 5.5, 6.0, 6.15, 6.19, 7.5, 7.99):
        h1 = b.ray_cast(Vector((xs, -30, z)), Vector((0, 1, 0)))
        h2 = b.ray_cast(Vector((xs, 30, z)), Vector((0, -1, 0)))
        rows[str(z)] = [round(h1[0].y, 3) if h1[0] else None, round(h2[0].y, 3) if h2[0] else None]
    # wall axis direction near the gate (local), from cap centre to a point 30 m along
    cen = []
    for xx in (xs, xs + (30 if xs > 0 else -30)):
        h1 = b.ray_cast(Vector((xx, -60, 1.0)), Vector((0, 1, 0))); h2 = b.ray_cast(Vector((xx, 60, 1.0)), Vector((0, -1, 0)))
        cen.append(((h1[0].y + h2[0].y) / 2) if (h1[0] and h2[0]) else None)
    W[wk] = {'topo': topo(bm), 'section_yExtent_at_x=%.1f' % xs: rows,
             'axisCentreY_at_cap_and_30m': [round(c, 4) if c is not None else None for c in cen],
             'axisAngleVsGateX_deg': round(math.degrees(math.atan2(cen[1] - cen[0], 30)), 4) if None not in cen else None}
    bm.free()
res['walls'] = W
json.dump(res, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE', out_path)
