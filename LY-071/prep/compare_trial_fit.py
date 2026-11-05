# LY-071 prep: compare the existing local trial fit (city-visible chunk biyong_C_relationship.glb)
# against the public card GLBs (hall A LOD0-2, enclosure-L LOD0-2), and run origin/overlay negatives.
# blender -b --factory-startup --python-exit-code 1 -P compare_trial_fit.py -- <out.json> <chunk.glb> <cardFilesDir>
# All coordinates reported in glTF frame (x, y up, z). Blender (X,Y,Z) -> glTF (X, Z, -Y).
import bpy, sys, json, hashlib, os, math
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
out_path, chunk_path, card_dir = argv[0], argv[1], argv[2]


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def G(v):
    return Vector((v.x, v.z, -v.y))


def import_glb(p):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=p)
    out = {}
    for o in bpy.context.scene.objects:
        if o.type != 'MESH':
            continue
        mw = o.matrix_world
        verts = [G(mw @ v.co) for v in o.data.vertices]
        tris = []
        o.data.calc_loop_triangles()
        for t in o.data.loop_triangles:
            tris.append(tuple(t.vertices))
        out[o.name] = {'verts': verts, 'tris': tris, 'loc': G(mw.to_translation()),
                       'rotIdentity': all(abs(mw[i][j] - (1 if i == j else 0)) < 1e-6 for i in range(3) for j in range(3))}
    return out


def bbox(vs):
    return ([round(min(v[i] for v in vs), 4) for i in range(3)], [round(max(v[i] for v in vs), 4) for i in range(3)])


def kd(vs):
    t = KDTree(len(vs))
    for i, v in enumerate(vs):
        t.insert(v, i)
    t.balance()
    return t


def hausdorff(a, b):
    ta, tb = kd(a), kd(b)
    ab = max(tb.find(v)[2] for v in a)
    ba = max(ta.find(v)[2] for v in b)
    return round(ab, 6), round(ba, 6)


def roty(deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    # glTF rotation about +Y
    return lambda v: Vector((c * v.x + s * v.z, v.y, -s * v.x + c * v.z))


res = {'tool': 'compare_trial_fit.py', 'blender': bpy.app.version_string,
       'chunk': {'path': chunk_path, 'sha256': sha(chunk_path)}, 'card': {}}

ch = import_glb(chunk_path)
res['chunk']['nodes'] = {k: {'loc_gltf': [round(x, 4) for x in v['loc']], 'rotIdentity': v['rotIdentity'],
                             'verts': len(v['verts']), 'tris': len(v['tris']),
                             'bbox_gltf': bbox(v['verts'])} for k, v in ch.items()}
# group origin = enclosure node translation (ground datum)
enc_name = [k for k in ch if 'enclosure' in k][0]
hall_names = [k for k in ch if 'biyong-A-static' in k]
O = ch[enc_name]['loc'].copy()
res['groupOrigin_gltf'] = [round(x, 4) for x in O]
res['hallNodeOffsetsFromGroupOrigin'] = {k: [round(x, 4) for x in (ch[k]['loc'] - O)] for k in hall_names}

hall_trial = {k.split('biyong-A-static_')[-1]: [v - O for v in ch[k]['verts']] for k in hall_names}
enc_trial = [v - O for v in ch[enc_name]['verts']]

layout = {k: [v - O for v in ch[k]['verts']] for k in ch if 'layout' in k}
res['layoutLocal_bbox'] = {k: bbox(v) for k, v in layout.items()}

cmp = {}
for lod in ('LOD0', 'LOD1', 'LOD2'):
    p = os.path.join(card_dir, f'biyong-A-{lod}.glb')
    card = import_glb(p)
    res['card'][f'biyong-A-{lod}.glb'] = sha(p)
    r = {}
    for k, v in card.items():
        part = k.split('biyong-A-static_')[-1]
        if part not in hall_trial:
            continue
        for dy in (0.0, 1.2, 2.4):
            moved = [w + Vector((0, dy, 0)) for w in v['verts']]
            r[f'{part}@dy={dy}'] = {'cardVerts': len(v['verts']), 'trialVerts': len(hall_trial[part]),
                                    'cardTris': len(v['tris']),
                                    'hausdorff_card->trial,trial->card_m': hausdorff(moved, hall_trial[part])}
    cmp[f'hall-{lod}'] = r
for lod in ('LOD0', 'LOD1', 'LOD2'):
    p = os.path.join(card_dir, f'enclosure-L-{lod}.glb')
    card = import_glb(p)
    res['card'][f'enclosure-L-{lod}.glb'] = sha(p)
    v = list(card.values())[0]['verts']
    tris = len(list(card.values())[0]['tris'])
    four = []
    for d in (0, 90, 180, 270):
        f = roty(d)
        four += [f(w) for w in v]
    cmp[f'enclosureL-{lod}x4'] = {'cardVertsx4': len(four), 'cardTrisx4': tris * 4,
                                  'trialVerts': len(enc_trial), 'trialTris': len(ch[enc_name]['tris']),
                                  'hausdorff_m': hausdorff(four, enc_trial),
                                  'single_L_only_hausdorff_m': hausdorff(v, enc_trial)}
res['compare'] = cmp

# negatives / interface on reconstructed group using LOD0 hall + LOD1x4 enclosure in group frame
def ground_y_under(vs, pred):
    sel = [w.y for w in vs if pred(w)]
    return (round(min(sel), 4) if sel else None)

hall_earth = hall_trial['earth']
res['interface'] = {
    'hallFootMinY_trial': ground_y_under(hall_earth, lambda w: True),
    'enclosureBaseMinY_trial': ground_y_under(enc_trial, lambda w: True),
    'islandTopMaxY_trial': max(w.y for w in layout.get('biyong-layout__A_island', [Vector((0, 0, 0))])),
    'hallStairOuterReach_m': round(max(abs(w.x) for w in hall_earth), 4),
    'enclosureInnerFaceMin_abs_m': round(min(max(abs(w.x), abs(w.z)) for w in enc_trial), 4),
}
res['interface']['clearHall_to_enclosure_m'] = round(
    min(max(abs(w.x), abs(w.z)) for w in enc_trial if w.y < 0.01) - res['interface']['hallStairOuterReach_m'], 4)

# opening widths on the four axes (gap between adjacent quadrant arm ends at centreline |coord|~68)
def gap_on_axis(axis):
    # axis 'x+': opening crossing +x axis -> enclosure verts with x>60, look at |z| min
    if axis in ('x+', 'x-'):
        sel = [abs(w.z) for w in enc_trial if (w.x > 60 if axis == 'x+' else w.x < -60)]
    else:
        sel = [abs(w.x) for w in enc_trial if (w.z > 60 if axis == 'z+' else w.z < -60)]
    return round(2 * min(sel), 4)
res['interface']['axisOpeningWidth_m'] = {a: gap_on_axis(a) for a in ('x+', 'x-', 'z+', 'z-')}
# stair width at hall (earth verts outside platform |coord|>18.01)
def stair_width(axis):
    if axis in ('x+', 'x-'):
        sel = [w.z for w in hall_earth if (w.x > 18.01 if axis == 'x+' else w.x < -18.01)]
    else:
        sel = [w.x for w in hall_earth if (w.z > 18.01 if axis == 'z+' else w.z < -18.01)]
    return [round(min(sel), 4), round(max(sel), 4)] if sel else None
res['interface']['hallStairLateralExtent_m'] = {a: stair_width(a) for a in ('x+', 'x-', 'z+', 'z-')}

res['negatives'] = {
    'N1_sameOriginDirectStack': 'hall card at identity: foot y=-1.2 vs enclosure base y=0 -> 1.2 m step (hall sunk); expected FAIL',
    'N1_measured_footMinusBase_m': round(min(w.y for w in hall_earth) - 1.2 - min(w.y for w in enc_trial), 4),
    'N2_doubleApplied_dy2.4_footMinusBase_m': round(min(w.y for w in hall_earth) + 1.2 - min(w.y for w in enc_trial), 4),
    'N3_singleL_only_coversQuadrants': 1,
}
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print('WROTE', out_path)
