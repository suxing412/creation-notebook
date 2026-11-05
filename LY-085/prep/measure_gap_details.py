# LY-085 prep: detail measurements for the south-end gap (read-only; no deliverable geometry).
#   D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P measure_gap_details.py -- <lab_root> <out.json>
# - Pingcheng road north-end vertices in gate-local frame; lateral offset to the open side passages
# - outer-edge coverage of the existing gate ground strips (LOD0/1/2) at the outer port
# - city-wall geometry (A/wall-04,05,06) inside the outer-approach windows of both gates
# - locations of any unsupported stations along the Pingcheng south road plan
import bpy, sys, json, math, hashlib
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index('--') + 1:]
LAB = Path(a[0]); OUT = Path(a[1]); D = LAB / 'docs'; CITY = D / 'cities/luoyang'
R = lambda x, n=4: round(float(x), n)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def import_glb(path, M=Matrix.Identity(4)):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=str(path))
    new = [o for o in bpy.data.objects if o not in before]; dg = bpy.context.evaluated_depsgraph_get(); out = []
    for o in new:
        if o.type != 'MESH': continue
        me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); mw = M @ o.matrix_world
        out.append({'name': o.name, 'v': [mw @ v.co for v in me.vertices], 'f': [tuple(t.vertices) for t in me.loop_triangles]})
    for o in new: bpy.data.objects.remove(o, do_unlink=True)
    return out


def bvh(objs):
    vs, fs = [], []
    for o in objs:
        off = len(vs); vs += o['v']; fs += [tuple(off + k for k in t) for t in o['f']]
    return BVHTree.FromPolygons(vs, fs, epsilon=0.0)


bpy.ops.wm.read_factory_settings(use_empty=True)
src = json.loads((CITY / 'progress-assets/north13-gates/source.json').read_text(encoding='utf-8'))
PL = {p['package']: p['placement'] for p in src['packages'] if 'placement' in p}
res = {'inputs': {}}
net = import_glb(CITY / 'assets/ground-atomic/network-ground-stitched.glb')
road = [o for o in net if o['name'] == 'C_stitch_primary']; RB = bvh(road); NB = bvh(net)
walls = {}
for w in ('wall-04', 'wall-05', 'wall-06'):
    p = CITY / 'assets/city-wall/A' / (w + '.glb'); walls[w] = import_glb(p); res['inputs']['assets/city-wall/A/%s.glb' % w] = sha(p)
WB = {w: bvh(o) for w, o in walls.items()}

for g, pkg, strips in (('pingcheng', 'luoyang-pingcheng-gate-study-v1', 'm-luoyang-pingcheng-gate/files/pingcheng-ground-LOD%d.glb'),
                       ('kaiyang', 'luoyang-kaiyang-gate-study-v1', 'm-luoyang-kaiyang-gate/files/kaiyang-ground-LOD%d.glb')):
    pl = PL[pkg]; O = Vector(pl['engineering_origin_from_existing_wall_caps'])
    T = Matrix.Translation(O) @ Matrix.Rotation(pl['rotation_z_rad'], 4, 'Z'); Ti = T.inverted()
    gr = {}
    # strip outer-edge coverage (local), per LOD
    for lod in range(3):
        objs = import_glb(D / 'library/models' / (strips % lod)); SB = bvh(objs)
        ymin = min(v.y for o in objs for v in o['v'])
        cov = []; s = None; x = -12.0
        while x <= 12.0001:
            h = SB.ray_cast(Vector((x, ymin + 0.05, 5)), Vector((0, 0, -1)), 10)
            if h[0] is not None and s is None: s = R(x, 2)
            if h[0] is None and s is not None: cov.append([s, R(x - 0.02, 2)]); s = None
            x += 0.02
        if s is not None: cov.append([s, 12.0])
        # area of strip top (projected) south of the gate body face y<-6.35
        gr['strip_LOD%d_outer_edge_y' % lod] = R(ymin, 4)
        gr['strip_LOD%d_support_x_at_outer_edge' % lod] = cov
    # walls inside the outer approach window (local x +-25, y -70..-6.0) and their south face
    for w, B in WB.items():
        hits = 0; ys = []; xs = []
        y = -70.0
        while y <= -6.0001:
            x = -25.0
            while x <= 25.0001:
                wp = T @ Vector((x, y, 0))
                h = B.ray_cast(Vector((wp.x, wp.y, 60)), Vector((0, 0, -1)), 80)
                if h[0] is not None: hits += 1; ys.append(y); xs.append(x)
                x += 0.5
            y += 0.5
        gr['wall_%s_cells_in_outer_window_0.5m' % w] = {'n': hits, 'x': [min(xs), max(xs)] if xs else None, 'y': [min(ys), max(ys)] if ys else None}
    if g == 'pingcheng':
        endv = sorted({(R(v.x, 3), R(v.y, 3), R(v.z, 3)) for o in road for v in o['v'] if -90 < v.y < -55 and abs(v.x - 1622) < 12})
        loc = [[R(c, 3) for c in (Ti @ Vector(v))] for v in endv]
        gr['road_end_vertices_world'] = endv; gr['road_end_vertices_local'] = loc
        top = [p for p in loc if p[2] > 0.0]
        xl = sorted(p[0] for p in top); yl = sum(p[1] for p in top) / len(top)
        gr['road_end_edge_local'] = {'x': [xl[0], xl[-1]], 'y_mean': R(yl, 3), 'top_local_z': R(max(p[2] for p in top), 3),
                                     'bottom_local_z': R(min(p[2] for p in loc), 3), 'width_m': R(xl[-1] - xl[0], 3)}
        # distances from side-passage outer-port centres to the nearest point on the road-end edge
        for side, xc in (('W', -7.9), ('E', 7.9)):
            px = min(max(xc, xl[0]), xl[-1])
            gr['side_%s_port_to_road_end' % side] = {'port_local': [xc, -10.0], 'road_end_point_local': [R(px, 3), R(yl, 3)],
                                                     'straight_dist_m': R(math.hypot(xc - px, -10.0 - yl), 3),
                                                     'lateral_offset_m': R(abs(xc - px), 3), 'longitudinal_m': R(-10.0 - yl, 3)}
        gr['centre_lane_port_to_road_end_m'] = R(-10.0 - yl, 3)
        # road plan continuity misses
        A = Vector((1622.080627017166, -73.712)); Bp = Vector((1612.245, -1224.49)); L = (Bp - A).length
        dv = (Bp - A).normalized(); nv = Vector((-dv.y, dv.x)); miss = []
        s = 0.0
        while s <= L:
            for off in (0, 2.7, -2.7, 2.95, -2.95):
                q = A + dv * s + nv * off
                if RB.ray_cast(Vector((q.x, q.y, 60)), Vector((0, 0, -1)), 80)[0] is None:
                    miss.append([R(s, 2), off, R(q.x, 3), R(q.y, 3)])
            s += 0.1
        gr['road_plan_misses_0.1m'] = {'stations': int(L / 0.1) + 1, 'offsets': [0, 2.7, -2.7, 2.95, -2.95], 'misses': miss[:60], 'n_miss': len(miss)}
        # how far east/west the road edge sits from plan centreline at the north end
        gr['road_far_end_world'] = sorted({(R(v.x, 3), R(v.y, 3), R(v.z, 3)) for o in road for v in o['v'] if v.y < -1220})
    res[g] = gr
OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding='utf-8'); print('DETAIL_OK')
