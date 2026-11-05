# LY-085 prep: where are the undeployed mother-1e8c4d ritual chunks (lingtai / taixue / biyong) and the
# Kaiyang gate chunk relative to the two south gates and the Pingcheng south road?  Read-only.
#   D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P measure_mother_ritual.py -- <lab_root> <extract_dir> <out.json>
import bpy, sys, json, hashlib, math
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]; LAB = Path(a[0]); EX = Path(a[1]); OUT = Path(a[2])
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


def bb(vs):
    return [[R(min(v[i] for v in vs)) for i in range(3)], [R(max(v[i] for v in vs)) for i in range(3)]]


bpy.ops.wm.read_factory_settings(use_empty=True)
src = json.loads((CITY / 'progress-assets/north13-gates/source.json').read_text(encoding='utf-8'))
PL = {p['package']: p['placement'] for p in src['packages'] if 'placement' in p}
ports = {}
for g, pkg, yport in (('kaiyang', 'luoyang-kaiyang-gate-study-v1', -7.0), ('pingcheng', 'luoyang-pingcheng-gate-study-v1', -10.0)):
    pl = PL[pkg]; T = Matrix.Translation(Vector(pl['engineering_origin_from_existing_wall_caps'])) @ Matrix.Rotation(pl['rotation_z_rad'], 4, 'Z')
    ports[g] = T @ Vector((0, yport, 0))
road = [o for o in load(CITY / 'assets/ground-atomic/network-ground-stitched.glb') if o['name'] == 'C_stitch_primary'][0]
RB = BVHTree.FromPolygons(road['v'], road['f'], epsilon=0.0)
res = {'ports_world': {k: [R(c) for c in v] for k, v in ports.items()}, 'chunks': {}}
for f in ('lingtai_C_with_east_access.glb', 'taixue_C_with_support.glb', 'biyong_C_relationship.glb', 'city_gate_kaiyang-K.glb', 'C_gate_local_ground.glb'):
    p = EX / f; objs = load(p); rows = []
    for o in objs:
        if not o['v']: continue
        b = bb(o['v'])
        # nearest docs-road point to any vertex of this object (sampled every k-th vertex)
        k = max(1, len(o['v']) // 4000); dmin = 1e9; at = None
        for v in o['v'][::k]:
            n = RB.find_nearest(v)
            if n[0] is not None and n[3] < dmin: dmin = n[3]; at = n[0]
        cx, cy = (b[0][0] + b[1][0]) / 2, (b[0][1] + b[1][1]) / 2
        rows.append({'name': o['name'], 'tris': len(o['f']), 'bbox_world': b,
                     'nearest_to_docs_pingcheng_road_m': R(dmin, 2), 'road_point': [R(c, 2) for c in at] if at else None,
                     'centre_to_kaiyang_port_m': R(math.hypot(cx - ports['kaiyang'].x, cy - ports['kaiyang'].y), 1),
                     'centre_to_pingcheng_port_m': R(math.hypot(cx - ports['pingcheng'].x, cy - ports['pingcheng'].y), 1)})
    res['chunks'][f] = {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'objects': rows}
OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding='utf-8'); print('RITUAL_OK')
