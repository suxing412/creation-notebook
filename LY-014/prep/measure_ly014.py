# LY-014 prep measurement (read-only on inputs). Blender 5.2:
#   blender.exe -b --factory-startup --python-exit-code 1 -P measure_ly014.py -- <lab_repo> <src_pkg_dir> <out_json>
# Measures, on the actual exported GLBs: deck/pier/ground heights, upper-deck obstacle & headroom map,
# body-envelope free space, unguarded deck edges, wall-top vs deck height, wall end caps, the hidden-trial
# terminal adapters and the city stitched ground near the gate. No geometry is created or saved.
import bpy, sys, json, hashlib, math
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
LAB = Path(argv[0]); SRC = Path(argv[1]); OUT = Path(argv[2])
D = LAB / 'docs'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

# Placement contract of the hidden city trial (city/placement.json in the K-v1 package)
PL = json.loads((SRC / 'city/placement.json').read_text())
ORG = Vector(PL['engineering_origin_from_existing_wall_caps']); ANG = PL['rotation_z_rad']
T = Matrix.Translation(ORG) @ Matrix.Rotation(ANG, 4, 'Z'); TI = T.inverted()

def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def import_glb(p):
    clear(); bpy.ops.import_scene.gltf(filepath=str(p))
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    out = []
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles()
        mw = o.matrix_world
        V = np.array([tuple(mw @ v.co) for v in me.vertices], float)
        F = np.array([tuple(t.vertices) for t in me.loop_triangles], int).reshape(-1, 3)
        mat = me.materials[0].name if me.materials else ''
        out.append({'name': o.name, 'mat': mat, 'V': V, 'F': F})
        o.evaluated_get(dg).to_mesh_clear()
    return out

def parts_of(obj, weld=1e-4):
    V, F = obj['V'], obj['F']
    key = np.round(V / weld).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.reshape(-1)
    n = inv.max() + 1; par = np.arange(n)
    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a
    for t in F:
        a, b, c = find(inv[t[0]]), find(inv[t[1]]), find(inv[t[2]])
        par[b] = a; par[find(c)] = a
    roots = np.array([find(i) for i in range(n)])
    troot = roots[inv[F[:, 0]]]
    res = []
    for r in np.unique(troot):
        tri = F[troot == r]; P = V[np.unique(tri)]
        res.append({'mat': obj['mat'], 'lo': P.min(0), 'hi': P.max(0), 'tris': int(len(tri))})
    return res

def bvh_of(objs):
    Vs = []; Fs = []; off = 0
    for o in objs:
        Vs.append(o['V']); Fs.append(o['F'] + off); off += len(o['V'])
    V = np.vstack(Vs); F = np.vstack(Fs)
    return BVHTree.FromPolygons([tuple(v) for v in V], [tuple(f) for f in F]), V, F

def r3(x): return [round(float(v), 4) for v in x]

report = {'script_sha256': sha(__file__), 'placement_json_sha256': sha(SRC / 'city/placement.json'),
          'frame': 'gate local, Blender Z-up, +Y = north/city-inner side (door leaves at y=-5 south face); metres',
          'inputs': {}, 'lods': {}}

GATES = {0: D / 'library/models/m-luoyang-kaiyang-gate/files/kaiyang-K-LOD0.glb',
         1: D / 'cities/luoyang/progress-assets/north13-gates/luoyang-kaiyang-gate-study-v1/models/kaiyang-K-LOD1.glb',
         2: D / 'cities/luoyang/progress-assets/north13-gates/luoyang-kaiyang-gate-study-v1/models/kaiyang-K-LOD2.glb'}
GROUNDS = {i: D / f'library/models/m-luoyang-kaiyang-gate/files/kaiyang-ground-LOD{i}.glb' for i in range(3)}

BODY_H = 1.9; RADII = {'person_d0.6': 0.30, 'loaded_d0.9': 0.45, 'turn_d1.5': 0.75}; G = 0.05

for lod, p in GATES.items():
    report['inputs'][f'K-LOD{lod}'] = {'path': str(p.relative_to(LAB)).replace('\\', '/'), 'sha256': sha(p), 'bytes': p.stat().st_size}
    objs = import_glb(p)
    parts = [q for o in objs for q in parts_of(o)]
    timber = [q for q in parts if 'timber' in q['mat']]
    deck = max(timber, key=lambda q: (q['hi'][0] - q['lo'][0]) * (q['hi'][1] - q['lo'][1]))
    piers = [q for q in parts if 'earth' in q['mat'] and q['lo'][2] < 0.01 and q['hi'][2] > 4]
    DT = float(deck['hi'][2])
    # any part that could be a stair/ramp: top between 0.25 and DT-0.05, outside the three passages' leaves/jambs/heads, earth piers excluded
    stairish = [q for q in parts if 0.25 < q['hi'][2] < DT - 0.05 and all(q is not pp for pp in piers) and not (q['lo'][1] < -4.0)]
    bvh, V, F = bvh_of(objs)
    # Upper deck occupancy (AABB of loose parts intersecting the body band), conservative for round posts
    x0, x1, y0, y1 = deck['lo'][0], deck['hi'][0], deck['lo'][1], deck['hi'][1]
    xs = np.arange(x0 + G / 2, x1, G); ys = np.arange(y0 + G / 2, y1, G)
    occ = np.zeros((len(ys), len(xs)), bool)
    band = (DT + 0.02, DT + BODY_H)
    obst = []
    for q in parts:
        if q is deck: continue
        if q['hi'][2] <= band[0] or q['lo'][2] >= band[1]: continue
        if q['hi'][0] < x0 or q['lo'][0] > x1 or q['hi'][1] < y0 or q['lo'][1] > y1: continue
        obst.append({'mat': q['mat'].split('__')[0], 'lo': r3(q['lo']), 'hi': r3(q['hi'])})
        occ[(ys[:, None] >= q['lo'][1]) & (ys[:, None] <= q['hi'][1]) & (xs[None, :] >= q['lo'][0]) & (xs[None, :] <= q['hi'][0])] = True
    # headroom by upward ray cast from deck top
    head = np.full(occ.shape, np.inf)
    for j, y in enumerate(ys[::2]):
        for i, x in enumerate(xs[::2]):
            hit = bvh.ray_cast(Vector((x, y, DT + 0.005)), Vector((0, 0, 1)))
            if hit[0] is not None: head[2 * j:2 * j + 2, 2 * i:2 * i + 2] = hit[0].z - DT
    lowhead = head < BODY_H + 0.1
    free = ~occ & ~lowhead
    # erode by disc (also treat deck boundary as wall: an edge with no guard is a fall edge, counted separately)
    def erode(mask, r):
        k = int(math.ceil(r / G)); m = np.pad(mask, k, constant_values=False); out = np.ones_like(mask)
        for dj in range(-k, k + 1):
            for di in range(-k, k + 1):
                if (dj * G) ** 2 + (di * G) ** 2 <= r * r:
                    out &= m[k + dj:k + dj + mask.shape[0], k + di:k + di + mask.shape[1]]
        return out
    def comps(mask):
        lab = np.zeros(mask.shape, int); n = 0
        for s in zip(*np.nonzero(mask)):
            if lab[s]: continue
            n += 1; st = [s]; lab[s] = n
            while st:
                a, b = st.pop()
                for c, d in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                    if 0 <= c < mask.shape[0] and 0 <= d < mask.shape[1] and mask[c, d] and not lab[c, d]:
                        lab[c, d] = n; st.append((c, d))
        return lab, n
    fs = {}
    for k, r in RADII.items():
        e = erode(free, r); lab, n = comps(e)
        sizes = sorted([int((lab == i).sum()) for i in range(1, n + 1)], reverse=True)
        big = (lab == (1 + int(np.argmax([(lab == i).sum() for i in range(1, n + 1)])))) if n else e
        reach_w = bool(big[:, :int(0.6 / G)].any()) if n else False
        reach_e = bool(big[:, -int(0.6 / G):].any()) if n else False
        cen = (abs(xs) < 2.7)[None, :] & ((ys > -1.0) & (ys < 3.5))[:, None]
        fs[k] = {'radius_m': r, 'centre_area_m2': round(float(e.sum() * G * G), 3), 'components': n,
                 'component_cells_desc': sizes[:6], 'largest_touches_x_min_end': reach_w, 'largest_touches_x_max_end': reach_e,
                 'central_room_interior_in_largest': bool((big & cen).any()) if n else False}
    # unguarded deck edges: perimeter cells with no obstacle within 0.35 m inward in z band [DT+0.3, DT+1.0]
    guard = np.zeros(occ.shape, bool)
    for q in parts:
        if q is deck: continue
        if q['hi'][2] > DT + 0.3 and q['lo'][2] < DT + 1.0:
            guard[(ys[:, None] >= q['lo'][1]) & (ys[:, None] <= q['hi'][1]) & (xs[None, :] >= q['lo'][0]) & (xs[None, :] <= q['hi'][0])] = True
    k = int(0.35 / G)
    def unguarded(side):
        if side == 'south': strip = guard[:k, :].any(0); L = len(xs)
        elif side == 'north': strip = guard[-k:, :].any(0); L = len(xs)
        elif side == 'west': strip = guard[:, :k].any(1); L = len(ys)
        else: strip = guard[:, -k:].any(1); L = len(ys)
        return round(float((~strip).sum() * G), 2), round(L * G, 2)
    # offset of the nearest guard line inside each long edge (rail/posts) for the record
    lodrep = {
        'deck': {'lo': r3(deck['lo']), 'hi': r3(deck['hi']), 'top_z': round(DT, 4), 'thickness': round(float(deck['hi'][2] - deck['lo'][2]), 4)},
        'piers': [{'lo': r3(q['lo']), 'hi': r3(q['hi'])} for q in sorted(piers, key=lambda q: q['lo'][0])],
        'loose_parts': len(parts),
        'stair_or_ramp_candidates_found': [{'mat': q['mat'], 'lo': r3(q['lo']), 'hi': r3(q['hi'])} for q in stairish],
        'upper_obstacles_in_body_band': obst,
        'headroom_m': {'min_over_deck': round(float(head[np.isfinite(head)].min()), 4),
                       'cells_below_2.0m_fraction': round(float((head < 2.0).mean()), 4),
                       'median': round(float(np.median(head[np.isfinite(head)])), 4)},
        'body_envelope_free_space': fs,
        'unguarded_edge_m_of_total': {s: unguarded(s) for s in ('south', 'north', 'west', 'east')},
    }
    report['lods'][f'K-LOD{lod}'] = lodrep

# ground attachments
report['ground'] = {}
for lod, p in GROUNDS.items():
    report['inputs'][f'ground-LOD{lod}'] = {'path': str(p.relative_to(LAB)).replace('\\', '/'), 'sha256': sha(p), 'bytes': p.stat().st_size}
    objs = import_glb(p); bvh, V, F = bvh_of(objs)
    parts = [q for o in objs for q in parts_of(o)]
    tops = []
    for q in parts:
        zs = []
        for x in np.linspace(q['lo'][0] + 0.02, q['hi'][0] - 0.02, 7):
            for y in np.linspace(q['lo'][1] + 0.02, q['hi'][1] - 0.02, 29):
                h = bvh.ray_cast(Vector((x, y, 50)), Vector((0, 0, -1)))
                if h[0] is not None: zs.append(h[0].z)
        tops.append({'lo': r3(q['lo']), 'hi': r3(q['hi']), 'top_z_min': round(min(zs), 4), 'top_z_max': round(max(zs), 4), 'tris': q['tris']})
    report['ground'][f'LOD{lod}'] = {'parts': tops}

# city walls (as loaded by the city scene) -> gate local frame
report['walls'] = {}
for wid in ('wall-04', 'wall-05'):
    p = D / f'cities/luoyang/assets/city-wall/A/{wid}.glb'
    report['inputs'][wid] = {'path': str(p.relative_to(LAB)).replace('\\', '/'), 'sha256': sha(p), 'bytes': p.stat().st_size}
    objs = import_glb(p)
    V = np.vstack([o['V'] for o in objs]); L = np.array([tuple(TI @ Vector(v)) for v in V])
    near = L[np.abs(L[:, 0]) < 40]
    topz = float(L[:, 2].max()); botz = float(L[:, 2].min())
    endx = float(near[:, 0].min()) if near[:, 0].mean() > 0 else float(near[:, 0].max())
    capv = near[np.abs(near[:, 0] - endx) < 0.5]
    top = capv[capv[:, 2] > topz - 0.01]; bot = capv[capv[:, 2] < botz + 0.01]
    report['walls'][wid] = {'top_z_local': round(topz, 4), 'bottom_z_local': round(botz, 4),
                            'end_cap_vertices_local': [r3(v) for v in capv],
                            'cap_top_y_range': r3([top[:, 1].min(), top[:, 1].max()]) if len(top) else None,
                            'cap_bottom_y_range': r3([bot[:, 1].min(), bot[:, 1].max()]) if len(bot) else None}

# hidden trial terminal adapters (earth merged) from the K-v1 package blend
tb = SRC / 'city/kaiyang-K-mid-hidden-trial.blend'
report['inputs']['hidden-trial-blend'] = {'path': 'modeling-lab/review-batches/2026-11-04-north13-gates/luoyang-kaiyang-gate-study-v1/content.zip :: luoyang-kaiyang-gate-study-v1/city/kaiyang-K-mid-hidden-trial.blend', 'sha256': sha(tb)}
clear()
with bpy.data.libraries.load(str(tb), link=False) as (src, dst):
    dst.objects = list(src.objects)
ad = {}
for o in dst.objects:
    if o is None or o.type != 'MESH': continue
    me = o.data; me.calc_loop_triangles()
    # appended (unlinked) objects report identity matrix_world; mesh coordinates are already gate-local (checked: x reaches +/-16.0)
    Vw = np.array([tuple(v.co) for v in me.vertices])
    ad[o.name] = {'matrix_world_identity_after_append': max(abs(a - b) for ra, rb in zip(o.matrix_world, Matrix.Identity(4)) for a, b in zip(ra, rb)) < 1e-6,
                  'mesh_x_range_local': r3([Vw[:, 0].min(), Vw[:, 0].max()])}
    if 'earth' in o.name:
        F = np.array([tuple(t.vertices) for t in me.loop_triangles])
        bv = BVHTree.FromPolygons([tuple(v) for v in Vw], [tuple(f) for f in F])
        rows = []
        for side in (-1, 1):
            out = Vw[side * Vw[:, 0] > 12.41]
            xe = float(np.abs(out[:, 0]).max())
            profs = {}
            for y in (-2.0, 0.0, 2.0):
                prof = []
                for t in np.linspace(0.0, 1, 25):
                    x = side * (12.401 + t * (xe - 12.401 - 0.01))
                    h = bv.ray_cast(Vector((x, y, 50)), Vector((0, 0, -1)))
                    prof.append([round(x, 3), round(h[0].z, 4) if h[0] is not None else None])
                profs[str(y)] = prof
            p0 = profs['0.0']; okp = [q for q in p0 if q[1] is not None]
            run = abs(okp[-1][0] - okp[0][0]); rise = okp[-1][1] - okp[0][1]
            # y extent of adapter top near the wall end
            topv = out[out[:, 2] > out[:, 2].max() - 0.01]
            rows.append({'side': side, 'outer_x_end': round(side * xe, 4), 'adapter_vertex_lo': r3(out.min(0)), 'adapter_vertex_hi': r3(out.max(0)),
                         'top_profiles_by_y': profs, 'top_rise_m_y0': round(rise, 4), 'run_m_y0': round(run, 4),
                         'slope_deg_y0': round(math.degrees(math.atan2(rise, run)), 2),
                         'top_edge_y_range_at_wall_end': r3([topv[:, 1].min(), topv[:, 1].max()])})
        ad[o.name]['terminal_adapters'] = rows
report['hidden_trial'] = ad

# city stitched ground near the gate (north/inner and south/outer approach, beyond piers)
gp = D / 'cities/luoyang/assets/ground-atomic/network-ground-stitched.glb'
report['inputs']['ground-stitched'] = {'path': str(gp.relative_to(LAB)).replace('\\', '/'), 'sha256': sha(gp), 'bytes': gp.stat().st_size}
objs = import_glb(gp)
Vs = []; Fs = []; off = 0
for o in objs:  # whole stitched ground; large triangles may have every vertex far from the gate
    Vs.append(o['V']); Fs.append(o['F'] + off); off += len(o['V'])
samp = {}
if Vs:
    V = np.vstack(Vs); F = np.vstack(Fs); bv = BVHTree.FromPolygons([tuple(v) for v in V], [tuple(f) for f in F])
    def zone(name, xr, yr):
        zs = []; miss = 0
        for x in np.arange(xr[0], xr[1] + 1e-6, 0.5):
            for y in np.arange(yr[0], yr[1] + 1e-6, 0.5):
                w = T @ Vector((x, y, 0)); h = bv.ray_cast(Vector((w.x, w.y, 50)), Vector((0, 0, -1)))
                if h[0] is None: miss += 1
                else: zs.append(h[0].z - ORG.z)
        samp[name] = {'x_local': xr, 'y_local': yr, 'samples': len(zs) + miss, 'missing': miss,
                      'top_z_local_min': round(min(zs), 4) if zs else None, 'top_z_local_max': round(max(zs), 4) if zs else None}
    zone('under_gate_footprint', (-12.4, 12.4), (-5, 5))
    zone('north_inner_east_of_gate', (12.4, 30), (4, 14))
    zone('north_inner_west_of_gate', (-30, -12.4), (4, 14))
    zone('north_inner_in_front_of_gate', (-12.4, 12.4), (5, 14))
    zone('south_outer_in_front_of_gate', (-12.4, 12.4), (-14, -5))
report['city_ground_near_gate'] = samp

# derived height gaps
l1 = report['lods']['K-LOD1']; DT = l1['deck']['top_z']
wt = report['walls']['wall-04']['top_z_local']
g0 = report['ground']['LOD0']['parts']
report['derived'] = {
    'deck_top_z': DT, 'pier_top_z': max(p['hi'][2] for p in l1['piers']),
    'wall_top_z_local': wt, 'wall_top_minus_deck_top_m': round(wt - DT, 4),
    'ground_attachment_top_z_range': [min(p['top_z_min'] for p in g0), max(p['top_z_max'] for p in g0)],
    'rise_ground_attachment_to_deck_m': round(DT - max(p['top_z_max'] for p in g0), 4),
    'rise_gate_origin_z0_to_deck_m': DT,
}
OUT.write_text(json.dumps(report, indent=1, ensure_ascii=False))
print('LY014_MEASURE_OK', OUT)
