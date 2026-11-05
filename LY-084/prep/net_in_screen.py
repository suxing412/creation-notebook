# LY-084 prep: which loaded walkable ground lies inside LY-003's NE-C-SCREEN?
# Read-only: imports the city's ground GLBs (+ storage-main ground, + the not-in-city
# 196 m road chunk as a separate layer), raycasts each 5 m screening-cell centre, writes JSON.
#
#   blender -b --factory-startup --python-exit-code 1 -P net_in_screen.py -- \
#       <lab_root> <city-nodes-ne.json> <northeast_C_access.glb> <ne-screening-cells.json> <out.json>
#
# Cell-centre sampling: area = hits * 25 m2 (resolution 5 m). Not a support, collision,
# continuity or historical test; it only answers "is there network ground in the area at all".
import bpy, sys, json, os, hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
lab, nodes_p, road_p, cells_p, out_p = argv[:5]
LUO = os.path.join(lab, 'docs', 'cities', 'luoyang')


def sha(p):
    with open(p, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def load(path, t=(0, 0, 0)):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for r in [o for o in new if o.parent is None]:
        r.location = Vector(r.location) + Vector(t)
    bpy.context.view_layer.update()
    return [o for o in new if o.type == 'MESH']


def bvh(objs):
    verts, tris = [], []
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        ev = o.evaluated_get(dg); me = ev.to_mesh(); me.calc_loop_triangles()
        b = len(verts); M = o.matrix_world
        verts.extend([M @ v.co for v in me.vertices])
        tris.extend([tuple(b + i for i in t.vertices) for t in me.loop_triangles])
        ev.to_mesh_clear()
    return (BVHTree.FromPolygons(verts, tris) if tris else None), len(tris)


bpy.ops.wm.read_factory_settings(use_empty=True)
cn = json.load(open(nodes_p, encoding='utf-8'))
cells = json.load(open(cells_p, encoding='utf-8'))
layers, inputs = {}, {}
for n in cn['nodes']:
    if not (n['id'].startswith('ground-') or n['id'] == 'storage-main'):
        continue
    p = os.path.join(LUO, n['sourcePath'])
    px, py, pz = n.get('position') or [0, 0, 0]
    objs = load(p, (px, -pz, py))
    inputs[n['id']] = {'sha256': sha(p), 'expected_sha256': n['sha256'], 'native_translation': [px, -pz, py]}
    if n['id'] == 'storage-main':
        objs = [o for o in objs if 'ground' in o.name.lower()]
        layers['taicang_ground'] = layers.get('taicang_ground', []) + objs
    elif n['id'] == 'ground-network-ground-stitched':
        layers['network'] = objs
    else:
        layers['ground_other'] = layers.get('ground_other', []) + objs
layers['ne_road_not_in_city'] = load(road_p)
inputs['ne_road_chunk'] = {'sha256': sha(road_p), 'in_city': False}

B, rep = {}, {'inputs': inputs, 'cells_sha256': sha(cells_p), 'cell_step_m': cells['step_m'],
             'cells_total': len(cells['cell_centers_xy']), 'layers': {}}
for k, objs in layers.items():
    B[k], nt = bvh(objs)
    rep['layers'][k] = {'objects': sorted(o.name for o in objs), 'triangles': nt}

cell_a = cells['step_m'] ** 2
for k, tree in B.items():
    hits = []
    for x, y in cells['cell_centers_xy']:
        loc, _, _, _ = tree.ray_cast(Vector((x, y, 40.0)), Vector((0, 0, -1)), 50.0) if tree else (None,) * 4
        if loc is not None:
            hits.append((x, y, loc.z))
    r = rep['layers'][k]
    r['cells_hit'] = len(hits)
    r['area_m2_cell_centre'] = len(hits) * cell_a
    if hits:
        r['hit_bbox_xy'] = [min(h[0] for h in hits), min(h[1] for h in hits), max(h[0] for h in hits), max(h[1] for h in hits)]
        r['hit_z_range'] = [round(min(h[2] for h in hits), 3), round(max(h[2] for h in hits), 3)]
cy = [c[1] for c in cells['cell_centers_xy']]; cx = [c[0] for c in cells['cell_centers_xy']]
rep['screen_bbox_xy'] = [min(cx), min(cy), max(cx), max(cy)]
txt = json.dumps(rep, ensure_ascii=False, indent=1)
open(out_p, 'w', encoding='utf-8', newline='\n').write(txt)
print('LY084_DONE')
