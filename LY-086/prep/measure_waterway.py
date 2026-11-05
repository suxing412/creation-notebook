# LY-086 prep: read-only measurement of the palace waterway interface GLBs.
# Usage:
#   D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P measure_waterway.py -- <lab_root> <out.json>
# Reports everything in the glTF frame (X along channel, Y up, Z across) = Blender (x, -y, z) -> glTF (x, z, -y).
# Nothing is written back to any GLB.
import bpy, bmesh, sys, json, os, hashlib, math
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
LAB, OUT = argv[0], argv[1]
D = os.path.join(LAB, 'docs/library/models/m-luoyang-palace-waterway-interface/files')
FILES = {
    'near': 'palace-waterway-interface-near.glb',
    'mid': 'palace-waterway-interface-mid.glb',
    'far': 'palace-waterway-interface-far.glb',
    'inspection': 'palace-waterway-interface-inspection-near.glb',
}
WALLS = os.path.join(LAB, 'docs/library/models/m-luoyang-earthwall-family/files')
WALL_FILES = ['earthwall-A-LOD0.glb', 'earthwall-B-LOD0.glb', 'earthwall-C-LOD0.glb']

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        h.update(f.read())
    return h.hexdigest()

def g2b(x, y, z):  # glTF -> Blender
    return Vector((x, -z, y))

def b2g(v):
    return [round(v.x, 4), round(v.z, 4), round(-v.y, 4)]

def load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.context.scene.objects if o.type == 'MESH']

def world_bm(objs):
    bm = bmesh.new()
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        me = o.evaluated_get(dg).to_mesh()
        tmp = bmesh.new(); tmp.from_mesh(me); tmp.transform(o.matrix_world)
        me2 = bpy.data.meshes.new('t'); tmp.to_mesh(me2); bm.from_mesh(me2); tmp.free()
        o.evaluated_get(dg).to_mesh_clear()
    return bm

def bbox(objs):
    lo = Vector((1e18,) * 3); hi = Vector((-1e18,) * 3)
    for o in objs:
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    g_lo = [lo.x, lo.z, -hi.y]; g_hi = [hi.x, hi.z, -lo.y]
    return {'min': [round(a, 4) for a in g_lo], 'max': [round(a, 4) for a in g_hi],
            'size': [round(b - a, 4) for a, b in zip(g_lo, g_hi)]}

def multihit(bvh, o_g, d_g, maxd=50.0):
    o = g2b(*o_g); d = g2b(*d_g).normalized(); hits = []; t = 0.0; p = o.copy()
    for _ in range(64):
        loc, nrm, idx, dist = bvh.ray_cast(p, d, maxd - t)
        if loc is None:
            break
        t += dist
        hits.append(round(t, 4))
        p = loc + d * 1e-4; t += 1e-4
    return hits

def islands(bm):
    bm.verts.ensure_lookup_table(); seen = set(); out = []
    for v in bm.verts:
        if v.index in seen: continue
        stack = [v]; seen.add(v.index); comp = []
        while stack:
            a = stack.pop(); comp.append(a)
            for e in a.link_edges:
                b = e.other_vert(a)
                if b.index not in seen:
                    seen.add(b.index); stack.append(b)
        out.append(comp)
    return out

def signed_volume(bm):
    vol = 0.0
    for f in bm.faces:
        vs = [l.vert.co for l in f.loops]
        for i in range(1, len(vs) - 1):
            vol += vs[0].dot(vs[i].cross(vs[i + 1])) / 6.0
    return vol

def nonmanifold(bm):
    return sum(1 for e in bm.edges if not e.is_manifold)

R = {'tool': 'LY-086 prep measure_waterway.py', 'blender': bpy.app.version_string, 'frame': 'glTF (X channel axis, Y up, Z across)', 'files': {}}

# ---------- per LOD ----------
for key, fn in FILES.items():
    p = os.path.join(D, fn); objs = load(p)
    if key == 'inspection':
        # reassemble: drop the modern inspection translations (node translation only, verified identity rot/scale)
        insp = {}
        for o in objs:
            insp[o.name] = b2g(o.location)
            o.location = (0, 0, 0)
        bpy.context.view_layer.update()
    bm = world_bm(objs)
    bm.verts.ensure_lookup_table()
    bvh = BVHTree.FromBMesh(bm)
    rec = {'sha256': sha(p), 'bytes': os.path.getsize(p), 'objects': len(objs), 'tris': sum(len(f.verts) - 2 for f in bm.faces),
           'bbox': bbox(objs), 'nonmanifold_edges': nonmanifold(bm), 'signed_volume_m3': round(signed_volume(bm), 4)}
    isl = islands(bm)
    rec['loose_islands'] = len(isl)
    # weld split-normal vertices (1e-4 m) to judge real closure, not glTF vertex splits
    bw = bm.copy(); bmesh.ops.remove_doubles(bw, verts=bw.verts, dist=1e-4)
    rec['welded_1e-4'] = {'verts': len(bw.verts), 'nonmanifold_edges': nonmanifold(bw), 'islands': len(islands(bw))}
    bw.free()
    # vertical probes on channel centreline (gz=0) and shaft centre
    vprobe = {}
    for x in [-3.2, -3.0, -2.5, -2.0, -1.5, -1.0, -0.6, -0.3, 0.0, 0.3, 0.6, 1.0, 1.5, 2.0, 2.5, 3.0, 3.2]:
        h = multihit(bvh, (x, 10.0, 0.0), (0, -1, 0))
        vprobe[str(x)] = [round(10.0 - t, 4) for t in h]  # surface Y levels top->down
    rec['vertical_surfaces_y_at_z0'] = vprobe
    # horizontal across-channel probes at several heights
    hprobe = {}
    for x in [-2.5, -1.5, 0.0, 1.5, 2.5]:
        for y in [0.05, 0.3, 0.6, 0.9, 1.2, 1.5]:
            h = multihit(bvh, (x, y, 10.0), (0, 0, -1))
            hprobe[f'x{x}_y{y}'] = [round(10.0 - t, 4) for t in h]  # surface Z levels
    rec['across_surfaces_z'] = hprobe
    # along-axis probes: is the conduit open end to end?
    aprobe = {}
    for y in [0.05, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2]:
        h = multihit(bvh, (-10.0, y, 0.0), (1, 0, 0))
        aprobe[f'y{y}'] = [round(-10.0 + t, 4) for t in h]  # surface X positions
    rec['along_surfaces_x_at_z0'] = aprobe
    if key == 'inspection':
        rec['inspection_translations'] = insp
        parts = {}
        pbvh = {}
        for o in objs:
            b1 = world_bm([o]); pbvh[o.name] = BVHTree.FromBMesh(b1)
            parts[o.name] = {'bbox': bbox([o]), 'tris': sum(len(f.verts) - 2 for f in b1.faces),
                             'nonmanifold_edges': nonmanifold(b1), 'signed_volume_m3': round(signed_volume(b1), 5)}
            b1.free()
        rec['parts_assembled'] = parts
        ov = {}
        names = sorted(pbvh)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                n = len(pbvh[a].overlap(pbvh[b]))
                if n: ov[f'{a}|{b}'] = n
        rec['part_pair_triangle_overlaps'] = ov
    bm.free()
    R['files'][key] = rec

# ---------- candidate host wall blocks (city earthwall family, NOT palace wall) ----------
R['earthwall_candidates'] = {}
for fn in WALL_FILES:
    p = os.path.join(WALLS, fn); objs = load(p)
    bmw = world_bm(objs); bv = BVHTree.FromBMesh(bmw)
    th = {}
    for y in [0.05, 0.4, 0.76, 1.8, 4.0, 7.5]:
        h = multihit(bv, (0.0, y, 30.0), (0, 0, -1), 80.0)
        th[f'y{y}'] = [round(30.0 - t, 4) for t in h]
    R['earthwall_candidates'][fn] = {'sha256': sha(p), 'bbox': bbox(objs), 'objects': len(objs), 'across_surfaces_z_at_x0': th}
    bmw.free()

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(R, f, ensure_ascii=False, indent=1)
print('WROTE', OUT)
