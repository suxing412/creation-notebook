# LY-031 prep measurement (read-only). Usage: python -I measure_A.py <lab_repo_root> <out_json>
# Measures granary A doorway, stair, floor, lintel, interior clearances and swing envelopes from the actual
# public GLBs, and fingerprints the A region in every LOD of standalone/group/city files.
import sys, os, json, hashlib
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbread as G

ROOT = sys.argv[1].rstrip('/\\')
OUT = sys.argv[2]
D = ROOT + '/docs/'
UPD = 'model-library/updates/m-storage-functional/files/'
CITY = 'cities/luoyang/progress-assets/granary-city-v1/'
FILES = {
    'A0': UPD + 'granary-A-LOD0.glb', 'A1': UPD + 'granary-A-LOD1.glb', 'A2': UPD + 'granary-A-LOD2.glb',
    'B0': UPD + 'granary-B-LOD0.glb',
    'R0': UPD + 'granary-receiving-LOD0.glb',
    'G0': UPD + 'granary-group-LOD0.glb', 'G1': UPD + 'granary-group-LOD1.glb', 'G2': UPD + 'granary-group-LOD2.glb',
    'C0': CITY + 'granary-city-LOD0.glb', 'C1': CITY + 'granary-city-LOD1.glb', 'C2': CITY + 'granary-city-LOD2.glb',
}
# A placement: local -> group offset, group -> city node translation (read from the city GLB nodes below)
A_IN_GROUP = np.array([-12.0, 0.0, -6.0])

out = {'inputs': {}, 'notes': []}
for k, f in FILES.items():
    p = D + f
    out['inputs'][k] = {'path': 'docs/' + f, 'bytes': os.path.getsize(p), 'sha256': G.sha256(p)}

cache = {k: G.prims(D + f) for k, f in FILES.items()}
city_T = np.array(cache['C0'][0]['nodes'][0]['translation'])
out['cityNodeTranslation'] = city_T.tolist()


def a_offset(key):
    if key.startswith('A') or key.startswith('B') or key.startswith('R'):
        return np.zeros(3)
    if key.startswith('G'):
        return A_IN_GROUP
    return A_IN_GROUP + city_T


def faces(pos, tris):
    n = np.cross(pos[tris[:, 1]] - pos[tris[:, 0]], pos[tris[:, 2]] - pos[tris[:, 0]])
    a = np.linalg.norm(n, axis=1)
    return n / np.maximum(a, 1e-30)[:, None], a / 2


def a_region_mask(pos, tris, off):
    lo = np.array([-5.0, -0.001, -3.5]) + off - 1e-3
    hi = np.array([5.0, 4.71, 4.48]) + off + 1e-3
    v = pos[tris]
    return np.all((v >= lo) & (v <= hi), axis=(1, 2))


# ---------- 1. fingerprint the A region in every file ----------
fp = {}
for key in ['A0', 'A1', 'A2', 'G0', 'G1', 'G2', 'C0', 'C1', 'C2']:
    js, res = cache[key]
    off = a_offset(key)
    rec = {}
    for r in res:
        if r['node'] == 'original_city_ground_preserved':
            continue
        m = a_region_mask(r['pos'], r['tris'], off)
        T = r['tris'][m]
        loc = r['pos'][T.reshape(-1)] - off
        uv = r['uv'][T.reshape(-1)] if r['uv'] is not None else np.zeros((len(loc), 2))
        rows = np.round(np.hstack([loc, uv]), 4).reshape(-1, 3, 5)
        # order-independent fingerprint: sort corner tuples inside tri (keep winding by rotating to min), then sort tris
        keys = []
        for t in rows:
            i = min(range(3), key=lambda j: tuple(t[j]))
            keys.append(tuple(np.roll(t, -i, axis=0).reshape(-1)))
        keys.sort()
        h = hashlib.sha256(repr(keys).encode()).hexdigest()
        _, area = faces(r['pos'], T) if len(T) else (None, np.zeros(0))
        rec[r['material']] = {'tris': int(len(T)), 'area_m2': round(float(area.sum()), 4), 'fp': h[:16]}
    fp[key] = rec
out['A_region_fingerprint'] = fp

# ---------- 2. doorway, wall, lintel, floor, stair geometry in A local coordinates ----------
js, res = cache['A0']
timber = [r for r in res if 'timber' in r['material']][0]
P, T = timber['pos'], timber['tris']
comps = G.components(P, T)
info = []
for c in comps:
    v = P[T[c].reshape(-1)]
    info.append((c, v.min(0), v.max(0)))
wall = [x for x in info if len(x[0]) == 128][0]
stair = [x for x in info if len(x[0]) == 48 and x[1][2] > 3.0][0]
floor = [x for x in info if x[2][0] - x[1][0] > 9 and x[2][1] - x[1][1] < 0.2][0]
WT = T[wall[0]]
n, a = faces(P, WT)
# front wall outer face z=3.0 normal +z ; jamb faces at x=+-0.75 inside z 2.8..3.0
jamb = []
for i, t in enumerate(WT):
    if abs(abs(n[i][0]) - 1) < 1e-6:
        x = P[t[0]][0]
        vs = P[t]
        if abs(abs(x) - 0.75) < 1e-6:
            jamb.append({'x': round(float(x), 4), 'normal_x': round(float(n[i][0]), 3), 'ymin': round(float(vs[:, 1].min()), 4),
                         'ymax': round(float(vs[:, 1].max()), 4), 'zmin': round(float(vs[:, 2].min()), 4), 'zmax': round(float(vs[:, 2].max()), 4),
                         'area': round(float(a[i]), 4)})
soffit = [i for i, t in enumerate(WT) if n[i][1] < -0.99 and abs(P[t[0]][1] - 2.95) < 1e-4]
sv = P[WT[soffit].reshape(-1)]
bottom = [i for i, t in enumerate(WT) if n[i][1] < -0.99 and abs(P[t[0]][1] - 0.85) < 1e-4]
bottom_area = float(a[bottom].sum())
# expected perimeter footprint area minus opening (9.0x6.0 outer, 8.6x5.6 inner, opening 1.5x0.2)
expected_bottom = 9.0 * 6.0 - 8.6 * 5.6 - 1.5 * 0.2
door = {
    'opening_x': [-0.75, 0.75], 'clear_width_m': 1.5,
    'sill_y_floor_top': round(float(floor[2][1]), 4),
    'soffit_y': round(float(sv[:, 1].max()), 4),
    'clear_height_m': round(float(sv[:, 1].max() - floor[2][1]), 4),
    'wall_z': [round(float(sv[:, 2].min()), 4), round(float(sv[:, 2].max()), 4)],
    'wall_thickness_m': round(float(sv[:, 2].max() - sv[:, 2].min()), 4),
    'faces_direction': '+Z local / +Z world (south, since glTF -Z is north)',
    'threshold_present': bool(abs(bottom_area - (9.0 * 6.0 - 8.6 * 5.6)) < 1e-3),
    'wall_bottom_area_m2': round(bottom_area, 4), 'expected_without_threshold_m2': round(expected_bottom, 4),
    'jamb_faces': jamb,
    'door_frame_or_leaf_nodes_present': [nd.get('name') for nd in js['nodes'] if any(s in nd.get('name', '').lower() for s in ('door', 'leaf', 'frame', 'pivot'))],
}
# lintel block coincident faces (inherited): faces at x=+-0.75 between y 2.95-3.15 whose normal points away from opening
door['lintel_end_faces_coplanar_with_jamb'] = [j for j in jamb if j['ymin'] >= 2.95 - 1e-4]
out['doorway_A_local'] = door

# interior
inner = {'x': [-4.3, 4.3], 'z': [-2.8, 2.8], 'floor_y': 0.85, 'ceiling_slab_underside_y': 3.15}
cargo = [r for r in res if 'cargo' in r['material']][0]
cc = G.components(cargo['pos'], cargo['tris'])
boxes = []
for c in cc:
    v = cargo['pos'][cargo['tris'][c].reshape(-1)]
    boxes.append([np.round(v.min(0), 4).tolist(), np.round(v.max(0), 4).tolist()])
inner['cargo_proxies'] = boxes
out['interior_A_local'] = inner

# stair
SV = P[T[stair[0]].reshape(-1)]
ys = sorted(set(np.round(SV[:, 1], 4))); zs = sorted(set(np.round(SV[:, 2], 4)))
out['stair_A_local'] = {
    'x': [round(float(stair[1][0]), 4), round(float(stair[2][0]), 4)], 'width_m': round(float(stair[2][0] - stair[1][0]), 4),
    'levels_y': [float(y) for y in ys], 'risers': len(ys) - 1, 'riser_m': round(float(ys[1] - ys[0]), 4),
    'tread_edges_z': [float(z) for z in zs], 'tread_m': round(float(zs[1] - zs[0]), 4),
    'top_tread_is_floor_level': bool(abs(ys[-1] - floor[2][1]) < 1e-4),
    'apron_wall_face_to_stair_start_m': round(float(zs[0] - 3.0), 4),
    'floor_slab_z': [round(float(floor[1][2]), 4), round(float(floor[2][2]), 4)],
    'stair_bottom_y': float(ys[0]),
}

# roof / eave above door
tile = [r for r in res if 'tile' in r['material']][0]
tv = tile['pos'][tile['tris'].reshape(-1)]
front = tv[tv[:, 2] > 2.9]
out['eave_A_local'] = {'roof_min_y_over_z_gt_2.9': round(float(front[:, 1].min()), 4), 'eave_z_max': round(float(tv[:, 2].max()), 4),
                       'eave_minus_soffit_m': round(float(front[:, 1].min() - door['soffit_y']), 4)}

# ---------- 3. swing envelopes (C design probes, not structural) ----------
def swing(hinge_x, leaf_w, side, y0, y1, step_deg=1.0):
    # side +1 outward (+z), -1 inward (-z); hinge at wall face z=3.0 (out) or 2.8 (in); closed leaf spans toward centre
    zf = 3.0 if side > 0 else 2.8
    sign = 1 if hinge_x < 0 else -1  # leaf extends toward +x from left hinge
    pts = []
    for deg in np.arange(0, 90.0 + 1e-9, step_deg):
        t = np.radians(deg)
        pts.append((hinge_x + sign * leaf_w * np.cos(t), zf + side * leaf_w * np.sin(t)))
    pts = np.array(pts)
    return pts


def hits_box(pts, hinge, bmin, bmax, ylo, yhi):
    # sample along leaf from hinge to tip for each angle
    if yhi <= bmin[1] or ylo >= bmax[1]:
        return False
    for tip in pts:
        for s in np.linspace(0, 1, 41):
            x = hinge[0] + s * (tip[0] - hinge[0]); z = hinge[1] + s * (tip[1] - hinge[1])
            if bmin[0] - 1e-9 < x < bmax[0] + 1e-9 and bmin[2] - 1e-9 < z < bmax[2] + 1e-9:
                return True
    return False


stairs_steps = []
for i in range(len(zs) - 1):
    stairs_steps.append(([-0.75, ys[0], zs[i]], [0.75, ys[len(ys) - 1 - i], zs[i + 1]]))
gap = 0.01
sw = {}
for name, w, hinges in [('single_1.50', 1.5, [-0.75]), ('paired_0.75x2', 0.75, [-0.75, 0.75])]:
    for side, sname in [(-1, 'inward'), (1, 'outward')]:
        res_hits = []
        for hx in hinges:
            pts = swing(hx, w, side, 0.85 + gap, 2.95 - gap)
            hinge = (hx, 3.0 if side > 0 else 2.8)
            for bi, (bmin, bmax) in enumerate(boxes):
                if hits_box(pts, hinge, bmin, bmax, 0.85 + gap, 2.95 - gap):
                    res_hits.append('cargo%d' % bi)
            for si, (smin, smax) in enumerate(stairs_steps):
                if hits_box(pts, hinge, smin, smax, 0.85 + gap, 2.95 - gap):
                    res_hits.append('stair_tread%d_top_y%.4f' % (si, smax[1]))
            # sweep radius
        max_reach = w
        sw[name + '_' + sname] = {'leaf_width_m': w, 'sweep_radius_m': max_reach,
                                  'sweep_z_extent': [2.8 - w, 2.8] if side < 0 else [3.0, 3.0 + w],
                                  'bottom_gap_m': gap, 'hits': sorted(set(res_hits))}
out['swing_probe'] = sw
# 0.9 m single-file corridor x in [-0.45,0.45] vs open leaves at 90 deg (leaf thickness 0.06 C-assumed)
lt = 0.06
out['open90_clear_width_m'] = {
    'single_1.50_hinged_left_open90': round(1.5 - lt, 4),
    'paired_open90': round(1.5 - 2 * lt, 4),
    'with_0.08_jamb_posts_inside_opening_single': round(1.5 - 2 * 0.08 - lt, 4),
    'with_0.08_jamb_posts_inside_opening_paired': round(1.5 - 2 * 0.08 - 2 * lt, 4),
    'note': 'leaf thickness 0.06 and jamb 0.08 are C placeholders for prep only; not frozen',
}
# nearest cargo to door hinge line
cz = max(b[1][2] for b in boxes)
cx = min(abs(b[0][0]) for b in boxes)
out['inward_clearance'] = {'door_inner_face_z': 2.8, 'nearest_cargo_max_z': cz, 'depth_free_m': round(2.8 - cz, 4),
                           'cargo_min_abs_x': cx, 'lateral_free_from_jamb_m': round(cx - 0.75, 4),
                           'interior_wall_inner_x': 4.3}

# ---------- 4. world coordinates of A doorway in city ----------
off = A_IN_GROUP + city_T
out['doorway_A_world'] = {
    'x': [round(float(-0.75 + off[0]), 4), round(float(0.75 + off[0]), 4)],
    'y': [0.85, 2.95],
    'z_wall': [round(float(2.8 + off[2]), 4), round(float(3.0 + off[2]), 4)],
    'stair_foot_z': round(float(4.48 + off[2]), 4),
    'city_ground_top_y': None,
}
js, res = cache['C0']
g = [r for r in res if r['node'] == 'original_city_ground_preserved'][0]
out['doorway_A_world']['city_ground_top_y'] = round(float(g['pos'][:, 1].max()), 4)

# ---------- 5. LOD presence of opening ----------
lodop = {}
for key in ['A0', 'A1', 'A2', 'C0', 'C1', 'C2']:
    js, res = cache[key]
    off = a_offset(key)
    tm = [r for r in res if 'timber' in r['material']][0]
    m = a_region_mask(tm['pos'], tm['tris'], off)
    TT = tm['tris'][m]
    nn, aa = faces(tm['pos'], TT)
    sof = [i for i, t in enumerate(TT) if nn[i][1] < -0.99 and abs(tm['pos'][t[0]][1] - 2.95) < 1e-4
           and np.all(np.abs(tm['pos'][t][:, 0] - off[0]) <= 0.7501)]
    lodop[key] = {'soffit_tris': len(sof), 'soffit_area_m2': round(float(aa[sof].sum()), 4), 'material': tm['material']}
out['opening_per_lod'] = lodop

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1, default=lambda o: o.tolist() if hasattr(o, 'tolist') else str(o))
print(json.dumps({k: out[k] for k in ['doorway_A_local', 'stair_A_local', 'eave_A_local', 'swing_probe', 'inward_clearance', 'doorway_A_world', 'opening_per_lod']}, ensure_ascii=False, indent=1, default=str))
