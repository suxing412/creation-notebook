# LY-085 prep: compare the docs-city Pingcheng south road with the undeployed mother-1e8c4d
# city-visible chunk C_ground_network__C_stitch_primary.glb (read-only copy reassembled by LY-017
# under workpacks/LY-017/prep/_extract; source ZIP is in the lab repo modeling-lab/review-batches/2026-11-04-city-visible).
#   D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P measure_mother_chunk.py -- <lab_root> <chunk.glb> <out.json>
import bpy, sys, json, hashlib, math
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]; LAB = Path(a[0]); CH = Path(a[1]); OUT = Path(a[2])
CITY = LAB / 'docs/cities/luoyang'
R = lambda x, n=3: round(float(x), n)


def load(p):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=str(p))
    new = [o for o in bpy.data.objects if o not in before]; dg = bpy.context.evaluated_depsgraph_get(); out = []
    for o in new:
        if o.type != 'MESH': continue
        me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles()
        out.append({'name': o.name, 'v': [o.matrix_world @ v.co for v in me.vertices], 'f': [tuple(t.vertices) for t in me.loop_triangles]})
    for o in new: bpy.data.objects.remove(o, do_unlink=True)
    return out


def bvh(objs):
    vs, fs = [], []
    for o in objs:
        off = len(vs); vs += o['v']; fs += [tuple(off + k for k in t) for t in o['f']]
    return BVHTree.FromPolygons(vs, fs, epsilon=0.0)


bpy.ops.wm.read_factory_settings(use_empty=True)
src = json.loads((CITY / 'progress-assets/north13-gates/source.json').read_text(encoding='utf-8'))
pl = [p['placement'] for p in src['packages'] if p['package'] == 'luoyang-pingcheng-gate-study-v1'][0]
T = Matrix.Translation(Vector(pl['engineering_origin_from_existing_wall_caps'])) @ Matrix.Rotation(pl['rotation_z_rad'], 4, 'Z')
docs = [o for o in load(CITY / 'assets/ground-atomic/network-ground-stitched.glb') if o['name'] == 'C_stitch_primary']
mom = load(CH)
res = {'chunk_sha256': hashlib.sha256(CH.read_bytes()).hexdigest(), 'chunk_objects': {o['name']: len(o['f']) for o in mom},
       'docs_primary_tris': sum(len(o['f']) for o in docs)}
BD, BM = bvh(docs), bvh(mom)
rows = []
y = 20.0
while y >= -70.0:
    r = {'y': R(y, 1)}
    for k, B in (('docs', BD), ('mother', BM)):
        xs = []
        x = -12.0
        while x <= 12.0001:
            wp = T @ Vector((x, y, 0)); h = B.ray_cast(Vector((wp.x, wp.y, 60)), Vector((0, 0, -1)), 80)
            if h[0] is not None: xs.append((x, (T.inverted() @ h[0]).z))
            x += 0.05
        r[k] = [R(xs[0][0], 2), R(xs[-1][0], 2), R(min(z for _, z in xs), 3), R(max(z for _, z in xs), 3)] if xs else None
    rows.append(r); y -= 2.5
res['local_rows_x-12..12_step0.05_[xmin,xmax,zmin_local,zmax_local]'] = rows
# coarse whole-road equality check: sample the docs road plan and compare top z / presence
A = Vector((1622.080627017166, -73.712)); Bp = Vector((1612.245, -1224.49)); dv = (Bp - A).normalized(); L = (Bp - A).length
diff = 0; both = 0; only_docs = 0; only_mom = 0; s = 0.5
while s < L:
    q = A + dv * s
    hd = BD.ray_cast(Vector((q.x, q.y, 60)), Vector((0, 0, -1)), 80); hm = BM.ray_cast(Vector((q.x, q.y, 60)), Vector((0, 0, -1)), 80)
    if hd[0] is not None and hm[0] is not None:
        both += 1; diff = max(diff, abs(hd[0].z - hm[0].z))
    elif hd[0] is not None: only_docs += 1
    elif hm[0] is not None: only_mom += 1
    s += 1.0
res['south_of_docs_end_1m_stations'] = {'both': both, 'only_docs': only_docs, 'only_mother': only_mom, 'max_top_dz': R(diff, 5)}
OUT.write_text(json.dumps(res, indent=1), encoding='utf-8'); print('CHUNK_OK')
