# LY-072 prep (read-only): measure the existing city trial-fit of the Biyong group as exported in
# the tracked city-visible handoff chunk (biyong_C_relationship.glb), and compare it with the public
# library GLBs. Writes only <out.json>.
#
# Usage:
#   blender -b --factory-startup --python-exit-code 1 -P measure_trialfit.py -- \
#       <out.json> <chunk.glb> <hall-LOD0.glb> <encl-L-LOD0.glb> <encl-L-LOD1.glb>
#
# Frame: Blender Z-up (glTF -Z = +Y). Local frame = chunk world minus the shared trial-fit
# translation C=(2183.673095703125, -938.7760009765625, 0) read from source-node-manifest.
import bpy, bmesh, sys, json, hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
OUT, CHUNK, HALL0, ENCL0, ENCL1 = argv[:5]
C = Vector((2183.673095703125, -938.7760009765625, 0.0))
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
r3 = lambda v: [round(float(x), 4) for x in v]


def load(p):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=p)
    return {o.name: o for o in bpy.context.scene.objects if o.type == 'MESH'}


def bm_of(objs, shift=Vector((0, 0, 0)), weld=False):
    bm = bmesh.new()
    for o in objs:
        t = bmesh.new(); t.from_mesh(o.data); t.transform(o.matrix_world)
        for v in t.verts: v.co -= shift
        me = bpy.data.meshes.new('tmp'); t.to_mesh(me); t.free(); bm.from_mesh(me)
    if weld: bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    return bm


def bbox(bm):
    vs = [v.co for v in bm.verts]
    return [r3([min(v[k] for v in vs) for k in range(3)]), r3([max(v[k] for v in vs) for k in range(3)])]


def down(bvh, x, y, z0=30.0):
    h = bvh.ray_cast(Vector((x, y, z0)), Vector((0, 0, -1)), 100.0)
    return None if h[0] is None else round(h[0].z, 4)


def walk(bvh, axis, sign, lat, t0, t1, step=0.02, z0=30.0):
    rs = []
    n = int(round((t1 - t0) / step))
    for i in range(n + 1):
        t = round(t0 + i * step, 4)
        x, y = ((sign * t, lat) if axis == 'x' else (lat, sign * t))
        z = down(bvh, x, y, z0)
        if rs and ((z is None and rs[-1]['z'] is None) or (z is not None and rs[-1]['z'] is not None and abs(z - rs[-1]['z']) < 1e-3)):
            rs[-1]['t1'] = t
        else:
            rs.append({'t0': t, 't1': t, 'z': z})
    return rs


rep = {'chunk': {'path': CHUNK, 'sha256': sha(CHUNK)}, 'C_translation': r3(C), 'frame': 'local = chunk world - C; Z up'}
objs = load(CHUNK)
by = lambda key: [o for n, o in objs.items() if key in n]
groups = {'hall_earth': by('biyong-A-static_earth'), 'hall_timber': by('biyong-A-static_timber'), 'hall_tile': by('biyong-A-static_tile'),
          'enclosure': by('enclosure-A-v2'), 'island': by('A_island'), 'water': by('A_square_water_symbol'),
          'crossing_0_1': by('A_crossing_0_1'), 'crossing_0_-1': by('A_crossing_0_-1'),
          'crossing_1_1': by('A_crossing_1_1'), 'crossing_1_-1': by('A_crossing_1_-1')}
rep['objectNames'] = sorted(objs.keys())
rep['groups'] = {}
for g, os_ in groups.items():
    bm = bm_of(os_, C, weld=True)
    rep['groups'][g] = {'objects': [o.name for o in os_], 'materials': sorted({m.name for o in os_ for m in o.data.materials if m}),
                        'faces': len(bm.faces), 'bbox': bbox(bm),
                        'boundaryEdges': sum(1 for e in bm.edges if e.is_boundary),
                        'nonManifoldEdges': sum(1 for e in bm.edges if not e.is_manifold)}
    bm.free()

# support surfaces: everything except roof tile and timber (and water separately)
solid = groups['hall_earth'] + groups['enclosure'] + groups['island'] + [o for k in groups if k.startswith('crossing') for o in groups[k]]
bms = bm_of(solid, C); bvh_s = BVHTree.FromBMesh(bms)
bmw = bm_of(groups['water'], C); bvh_w = BVHTree.FromBMesh(bmw)
bmi = bm_of(groups['island'], C); bvh_i = BVHTree.FromBMesh(bmi)
bmx = bm_of([o for k in groups if k.startswith('crossing') for o in groups[k]], C); bvh_x = BVHTree.FromBMesh(bmx)
bmn = bm_of(groups['hall_earth'] + groups['enclosure'] + groups['island'] + groups['water'], C); bvh_n = BVHTree.FromBMesh(bmn)

axes = [('E+x', 'x', 1, 'crossing_0_1'), ('W-x', 'x', -1, 'crossing_0_-1'), ('N+y', 'y', 1, 'crossing_1_1'), ('S-y', 'y', -1, 'crossing_1_-1')]
rep['axes'] = {}
for name, ax, sg, cr in axes:
    e = {'crossingGroup': cr}
    e['solidProfile_lat0'] = walk(bvh_s, ax, sg, 0.0, 0.0, 90.0)
    e['solidProfile_lat+1.9'] = walk(bvh_s, ax, sg, 1.9, 15.0, 90.0)
    e['solidProfile_lat-3.9'] = walk(bvh_s, ax, sg, -3.9, 15.0, 90.0)
    e['waterProfile_lat0'] = [r for r in walk(bvh_w, ax, sg, 0.0, 0.0, 90.0) if r['z'] is not None]
    e['waterProfile_lat30'] = [r for r in walk(bvh_w, ax, sg, 30.0, 0.0, 90.0) if r['z'] is not None]
    e['islandProfile_lat0'] = [r for r in walk(bvh_i, ax, sg, 0.0, 0.0, 90.0) if r['z'] is not None]
    e['crossingProfile_lat0'] = [r for r in walk(bvh_x, ax, sg, 0.0, 0.0, 90.0) if r['z'] is not None]
    # what is under the crossing (excluding the crossing itself): ray down from z=0.29 (inside slab is avoided by
    # starting just below its bottom face at z=-0.001)
    under = walk(bvh_n, ax, sg, 0.0, 69.0, 79.0, 0.02, z0=-0.001)
    e['underCrossing_lat0_from_z-0.001'] = under
    under_top = walk(bvh_n, ax, sg, 0.0, 69.0, 79.0, 0.02, z0=0.0005)
    e['underCrossing_lat0_from_z+0.0005'] = under_top
    # wall opening: walk laterally along the wall centreline (t=68.0)
    lat_rs = []
    for i in range(0, 1001):
        lat = round(-10 + i * 0.02, 3)
        x, y = ((sg * 68.0, lat) if ax == 'x' else (lat, sg * 68.0))
        z = down(bvh_s, x, y)
        if lat_rs and ((z is None and lat_rs[-1]['z'] is None) or (z is not None and lat_rs[-1]['z'] is not None and abs(z - lat_rs[-1]['z']) < 1e-3)):
            lat_rs[-1]['l1'] = lat
        else:
            lat_rs.append({'l0': lat, 'l1': lat, 'z': z})
    e['wallCentreline_t68_lateral'] = lat_rs
    rep['axes'][name] = e

# library vs city comparisons (vertex-set match after translation)
def vset(bm, nd=3):
    return {tuple(round(c, nd) for c in v.co) for v in bm.verts}

cmp = {}
lib = load(HALL0)
bm_lib = bm_of([o for n, o in lib.items() if 'earth' in n], Vector((0, 0, -1.2)), weld=True)
objs = load(CHUNK)
bm_city = bm_of([o for n, o in objs.items() if 'biyong-A-static_earth' in n], C, weld=True)
a, b = vset(bm_lib), vset(bm_city)
cmp['hallEarth_lib+1.2z_vs_city'] = {'lib_sha256': sha(HALL0), 'libVerts': len(a), 'cityVerts': len(b), 'common': len(a & b),
                                    'libOnly': len(a - b), 'cityOnly': len(b - a), 'libBBox+1.2': bbox(bm_lib), 'cityBBox': bbox(bm_city)}
for lab, p in [('enclL_LOD0', ENCL0), ('enclL_LOD1', ENCL1)]:
    lib = load(p)
    bm_lib = bm_of(list(lib.values()), Vector((0, 0, 0)), weld=True)
    objs = load(CHUNK)
    bm_city = bm_of([o for n, o in objs.items() if 'enclosure-A-v2' in n], C, weld=True)
    q = [v for v in bm_city.verts if v.co.x > 1.0 and v.co.y > 1.0]
    qa = {tuple(round(c, 3) for c in v.co) for v in q}
    la = vset(bm_lib)
    qf = [f for f in bm_city.faces if all(v.co.x > 1.0 and v.co.y > 1.0 for v in f.verts)]
    cmp['%s_vs_city_enclosure_quadrant(+x,+y)' % lab] = {'lib_sha256': sha(p), 'libFaces': len(bm_lib.faces), 'cityQuadrantFaces': len(qf),
                                                         'libVerts': len(la), 'cityQuadVerts': len(qa), 'common': len(la & qa),
                                                         'libBBox': bbox(bm_lib),
                                                         'cityQuadBBox': [r3([min(v.co[k] for v in q) for k in range(3)]), r3([max(v.co[k] for v in q) for k in range(3)])]}
rep['libraryVsCity'] = cmp
json.dump(rep, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE', OUT)
