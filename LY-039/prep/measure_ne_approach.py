# LY-039 prep: measure the existing C_NE_APPROACH_LOCAL road chunk against the
# current in-city granary ground (storage-main) and nearby city wall chunk.
# Read-only: imports GLBs, writes one JSON report. Never exports geometry.
#
# blender -b --factory-startup --python-exit-code 1 -P measure_ne_approach.py -- \
#     road.glb granary.glb wall.glb out.json [extra_granary.glb]
#
# Coordinates: Blender glTF importer maps glTF Y-up back to native Z-up
# (native x, y=north, z=up), which is the frame used by source-node-manifest.json.
import bpy, sys, json, math, hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
road_p, gran_p, wall_p, out_p = argv[:4]
extra_p = argv[4] if len(argv) > 4 else None


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def load(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before and o.type == 'MESH']


def world_tris(objs):
    verts, tris, owner = [], [], []
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        base = len(verts)
        M = o.matrix_world
        verts.extend([M @ v.co for v in me.vertices])
        for t in me.loop_triangles:
            tris.append(tuple(base + i for i in t.vertices))
            owner.append(o.name)
        ev.to_mesh_clear()
    return verts, tris, owner


def bbox(vs):
    return [[min(v[i] for v in vs) for i in range(3)], [max(v[i] for v in vs) for i in range(3)]]


bpy.ops.wm.read_factory_settings(use_empty=True)
rep = {'inputs': {}, 'frame': 'native Z-up metres (Blender import of glTF Y-up)'}

road = load(road_p)
rv, rt, ro = world_tris(road)
rep['inputs']['road'] = {'path': road_p, 'sha256': sha(road_p), 'objects': [o.name for o in road],
                         'triangles': len(rt), 'vertices': len(rv), 'bbox': bbox(rv),
                         'materials': sorted({s.material.name for o in road for s in o.material_slots if s.material})}
# full vertex dump (small mesh)
uniq = sorted({(round(v.x, 4), round(v.y, 4), round(v.z, 4)) for v in rv}, key=lambda p: (-p[1], p[0], p[2]))
rep['road_unique_vertices'] = uniq
faces = []
for (a, b, c) in rt:
    n = (rv[b] - rv[a]).cross(rv[c] - rv[a])
    area = n.length / 2
    n = n.normalized() if n.length > 0 else n
    faces.append({'v': [[round(x, 4) for x in rv[i]] for i in (a, b, c)], 'n': [round(x, 4) for x in n], 'area': round(area, 4)})
rep['road_faces'] = faces
up = [f for f in faces if f['n'][2] > 0.5]
rep['road_top_area_m2'] = round(sum(f['area'] for f in up), 3)
rep['road_top_tris'] = len(up)
rep['road_side_or_cap_tris'] = len(faces) - len(up)

road_bvh = BVHTree.FromPolygons(rv, rt)

gran = load(gran_p)
gv, gt, go = world_tris(gran)
rep['inputs']['granary'] = {'path': gran_p, 'sha256': sha(gran_p), 'objects': [o.name for o in gran],
                            'triangles': len(gt), 'bbox': bbox(gv)}
per = {}
for o in gran:
    vs, ts, _ = world_tris([o])
    per[o.name] = {'triangles': len(ts), 'bbox': bbox(vs)}
rep['granary_objects'] = per
gran_bvh = BVHTree.FromPolygons(gv, gt)


def down_hit(bvh, x, y, z0=50.0):
    hit = bvh.ray_cast(Vector((x, y, z0)), Vector((0, 0, -1)), 200.0)
    return None if hit[0] is None else round(hit[0].z, 5)


def top_hit(bvh, x, y):
    return down_hit(bvh, x, y)

# Road north edge -> granary ground seam
rb = rep['inputs']['road']['bbox']
y_n = rb[1][1]
y_s = rb[0][1]
# sample along x across the road at its northern end
north_pts = [v for v in rv if abs(v.y - y_n) < 0.01]
xs_n = sorted({round(v.x, 4) for v in north_pts})
rep['road_north_end'] = {'y': round(y_n, 5), 'x_values': xs_n, 'z_values': sorted({round(v.z, 4) for v in north_pts})}
south_pts = [v for v in rv if abs(v.y - y_s) < 0.01]
rep['road_south_end'] = {'y': round(y_s, 5), 'x_values': sorted({round(v.x, 4) for v in south_pts}),
                         'z_values': sorted({round(v.z, 4) for v in south_pts})}

seam = []
if xs_n:
    x0, x1 = min(xs_n), max(xs_n)
    n = 21
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n
        rec = {'x': round(x, 3)}
        for dy in (-0.5, -0.05, -0.005):
            rec['road_z@y%+.3f' % dy] = top_hit(road_bvh, x, y_n + dy)
        for dy in (0.005, 0.05, 0.5, 2.0):
            rec['ground_z@y%+.3f' % dy] = top_hit(gran_bvh, x, y_n + dy)
        rec['ground_z_on_seam'] = top_hit(gran_bvh, x, y_n)
        rz = rec['road_z@y-0.005']; gz = rec['ground_z@y+0.005']
        rec['step_m'] = None if (rz is None or gz is None) else round(gz - rz, 5)
        seam.append(rec)
rep['north_seam_samples'] = seam
steps = [s['step_m'] for s in seam if s['step_m'] is not None]
rep['north_seam_summary'] = {'samples': len(seam), 'with_both': len(steps),
                             'max_abs_step_m': max((abs(s) for s in steps), default=None),
                             'missing_ground': sum(1 for s in seam if s['ground_z@y+0.005'] is None),
                             'missing_road': sum(1 for s in seam if s['road_z@y-0.005'] is None)}

# granary ground edge geometry near the seam: which ground tris touch y_n
gr_edge = [v for v in gv if abs(v.y - y_n) < 0.01]
rep['granary_vertices_on_road_north_y'] = {'count': len(gr_edge),
                                           'x_range': [round(min(v.x for v in gr_edge), 4), round(max(v.x for v in gr_edge), 4)] if gr_edge else None,
                                           'z_values': sorted({round(v.z, 4) for v in gr_edge})[:20]}

# overlap road vs granary (surface BVH only)
ov = road_bvh.overlap(gran_bvh)
rep['road_vs_granary_overlap_pairs'] = len(ov)
rep['road_vs_granary_overlap_owners'] = sorted({go[j] for _, j in ov})

# centreline samples along the road: cast down on the road every 2 m along y at mid-x of road top at that y
prof = []
y = y_n - 0.25
while y > y_s + 0.25:
    # find x extent of road at this y by scanning
    hits = []
    x = rb[0][0] - 0.5
    while x <= rb[1][0] + 0.5:
        z = top_hit(road_bvh, x, y)
        if z is not None:
            hits.append((x, z))
        x += 0.1
    if hits:
        prof.append({'y': round(y, 2), 'x_min': round(hits[0][0], 2), 'x_max': round(hits[-1][0], 2),
                     'z_min': round(min(h[1] for h in hits), 4), 'z_max': round(max(h[1] for h in hits), 4),
                     'spans': None})
        # count separate spans
        sp = 1
        for k in range(1, len(hits)):
            if hits[k][0] - hits[k - 1][0] > 0.15:
                sp += 1
        prof[-1]['spans'] = sp
    else:
        prof.append({'y': round(y, 2), 'x_min': None})
    y -= 2.0
rep['road_cross_sections_every_2m'] = prof

# wall proximity
wall = load(wall_p)
wv, wt, wo = world_tris(wall)
rep['inputs']['wall'] = {'path': wall_p, 'sha256': sha(wall_p), 'triangles': len(wt), 'bbox': bbox(wv)}
wall_bvh = BVHTree.FromPolygons(wv, wt)
rep['road_vs_wall_overlap_pairs'] = len(road_bvh.overlap(wall_bvh))
best = None
for v in rv:
    loc, nrm, idx, d = wall_bvh.find_nearest(v)
    if loc is not None and (best is None or d < best[0]):
        best = (d, [round(c, 3) for c in v], [round(c, 3) for c in loc])
rep['road_to_wall_min_vertex_distance'] = None if best is None else {'d_m': round(best[0], 3), 'road_v': best[1], 'wall_pt': best[2]}
# wall geometry that lies within the road's xy box (+20 m)
near = [v for v in wv if rb[0][0] - 20 <= v.x <= rb[1][0] + 20 and rb[0][1] - 20 <= v.y <= rb[1][1] + 20]
rep['wall_vertices_within_road_bbox_plus20m'] = len(near)

if extra_p:
    ex = load(extra_p)
    ev_, et, eo = world_tris(ex)
    ebvh = BVHTree.FromPolygons(ev_, et)
    rep['inputs']['extra_granary'] = {'path': extra_p, 'sha256': sha(extra_p), 'triangles': len(et), 'bbox': bbox(ev_)}
    cmp = []
    for s in seam:
        cmp.append({'x': s['x'], 'extra_ground_z@y+0.005': top_hit(ebvh, s['x'], y_n + 0.005),
                    'city_ground_z@y+0.005': s['ground_z@y+0.005']})
    rep['extra_granary_seam_compare'] = cmp
    rep['road_vs_extra_overlap_pairs'] = len(road_bvh.overlap(ebvh))

with open(out_p, 'w', encoding='utf-8') as f:
    json.dump(rep, f, ensure_ascii=False, indent=1)
print('WROTE', out_p)
