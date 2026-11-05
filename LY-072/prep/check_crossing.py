# LY-072 acceptance harness (read-only on inputs). Runs the support / port / deck / water checks of
# test-plan.md on one crossing instance against its context, and writes a JSON verdict.
#
# Usage:
#   blender -b --factory-startup --python-exit-code 1 -P check_crossing.py -- <params.json> <out.json>
#
# params.json:
# {
#  "shift": [2183.673095703125, -938.7760009765625, 0.0],   # world -> local (subtracted)
#  "sources": [ {"glb": "...", "role": "context|water|crossing", "include": ["..."], "exclude": ["..."],
#                "matrix": null | 16 floats row-major applied after import (for a candidate GLB)} ],
#  "axis": "x"|"y", "sign": 1|-1,
#  "innerPort_t": 69.8, "outerPort_t": 78.2,          # deck ends along the axis (local metres)
#  "halfWidth": 4.0,                                  # deck half width
#  "bearingMin_m": 0.30,                              # C-design minimum bearing length per end
#  "contactTol_m": 0.005, "riseMax_m": 0.20, "lateralLines": [-3.7,-2.0,0.0,2.0,3.7],
#  "headroom_m": 2.0, "sampleStep_m": 0.05
# }
import bpy, bmesh, sys, json, hashlib, math
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
P = json.load(open(argv[0], encoding='utf-8')); OUT = argv[1]
shift = Vector(P['shift'])
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()


def collect(src):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src['glb'])
    M = Matrix([P_ for P_ in [src['matrix'][i * 4:(i + 1) * 4] for i in range(4)]]) if src.get('matrix') else Matrix.Identity(4)
    bm = bmesh.new(); names = []
    for o in bpy.context.scene.objects:
        if o.type != 'MESH': continue
        if src.get('include') and not any(s in o.name for s in src['include']): continue
        if any(s in o.name for s in src.get('exclude', [])): continue
        t = bmesh.new(); t.from_mesh(o.data); t.transform(M @ o.matrix_world)
        for v in t.verts: v.co -= shift
        me = bpy.data.meshes.new('tmp'); t.to_mesh(me); t.free(); bm.from_mesh(me); names.append(o.name)
    return bm, names


roles = {'context': bmesh.new(), 'water': bmesh.new(), 'crossing': bmesh.new()}
rep = {'params': P, 'sources': []}
for s in P['sources']:
    bm, names = collect(s)
    me = bpy.data.meshes.new('acc'); bm.to_mesh(me); roles[s['role']].from_mesh(me); bm.free()
    rep['sources'].append({'glb': s['glb'], 'sha256': sha(s['glb']), 'role': s['role'], 'objects': names})
for b in roles.values(): b.verts.ensure_lookup_table(); b.faces.ensure_lookup_table()
bvh = {k: BVHTree.FromBMesh(b) for k, b in roles.items()}
both = bmesh.new()
for k in ('context', 'crossing'):
    me = bpy.data.meshes.new('b'); roles[k].to_mesh(me); both.from_mesh(me)
bvh_both = BVHTree.FromBMesh(both)

ax, sg = P['axis'], P['sign']
pt = lambda t, l, z: Vector((sg * t, l, z)) if ax == 'x' else Vector((l, sg * t, z))
step = P.get('sampleStep_m', 0.05); tol = P.get('contactTol_m', 0.005)
DOWN, UP = Vector((0, 0, -1)), Vector((0, 0, 1))
res = {}

# deck underside height field (crossing only) and what lies beneath it (context only, water ignored)
t0, t1 = min(P['innerPort_t'], P['outerPort_t']), max(P['innerPort_t'], P['outerPort_t'])
hw = P['halfWidth']
under = []
nt = int(round((t1 - t0) / step)); nl = int(round(2 * hw / step))
for i in range(nt + 1):
    t = t0 + i * step
    row = []
    for j in range(nl + 1):
        l = -hw + j * step
        hb = bvh['crossing'].ray_cast(pt(t, l, -50.0), UP, 100.0)      # lowest crossing face from below
        if hb[0] is None: row.append(None); continue
        zb = hb[0].z
        hc = bvh['context'].ray_cast(pt(t, l, zb + tol), DOWN, 100.0)
        gap = None if hc[0] is None else zb - hc[0].z
        row.append({'t': round(t, 3), 'l': round(l, 3), 'zBottom': round(zb, 4), 'gap': None if gap is None else round(gap, 4)})
    under.append(row)

def bearing(end_t, direction):
    # contiguous supported length from the deck end inward, using the WORST lateral line
    # (samples exactly on the slab outline return no crossing hit; they are skipped, and columns
    # with no crossing at all are ignored)
    worst = None
    for j in range(nl + 1):
        rng = list(range(nt + 1)) if direction > 0 else list(range(nt, -1, -1))
        cells_j = [under[i][j] for i in rng]
        k = 0
        while k < len(cells_j) and cells_j[k] is None: k += 1
        if k == len(cells_j): continue
        L = 0.0; started = False
        for c in cells_j[k:]:
            if c is None or c['gap'] is None or abs(c['gap']) > tol: break
            L += step
        worst = L if worst is None else min(worst, L)
    return round(worst or 0.0, 3)

inner_first = P['innerPort_t'] < P['outerPort_t']
res['T1_bearing_inner_m'] = bearing(P['innerPort_t'], 1 if inner_first else -1)
res['T1_bearing_outer_m'] = bearing(P['outerPort_t'], -1 if inner_first else 1)
cells = [c for r in under for c in r if c]
res['T1_unsupportedUndersideFraction'] = round(sum(1 for c in cells if c['gap'] is None) / max(1, len(cells)), 4)
res['T1_penetrationCells(gap<-tol)'] = sum(1 for c in cells if c['gap'] is not None and c['gap'] < -tol)
res['T1_pass'] = (res['T1_bearing_inner_m'] >= P['bearingMin_m'] and res['T1_bearing_outer_m'] >= P['bearingMin_m']
                  and res['T1_penetrationCells(gap<-tol)'] == 0)

# deck walking surface along several lateral lines (not only the centre ray), extended 2 m past both ports
lines = {}
worst_rise = 0.0; gaps = 0
for l in P.get('lateralLines', [0.0]):
    prof = []; t = t0 - 2.0
    while t <= t1 + 2.0 + 1e-9:
        h = bvh_both.ray_cast(pt(t, l, 30.0), DOWN, 100.0)
        prof.append(None if h[0] is None else round(h[0].z, 4)); t += step
    rises = [abs(b - a) for a, b in zip(prof, prof[1:]) if a is not None and b is not None]
    gaps += sum(1 for z in prof if z is None)
    worst_rise = max(worst_rise, max(rises) if rises else 0.0)
    lines[str(l)] = {'maxRise': round(max(rises) if rises else 0.0, 4), 'noSurfaceSamples': sum(1 for z in prof if z is None),
                     'zAtInnerPort-0.5': prof[int(round(1.5 / step))], 'zAtOuterPort+0.5': prof[int(round((t1 - t0 + 2.5) / step))]}
res['T2_lines'] = lines
res['T2_worstRise_m'] = round(worst_rise, 4)
res['T2_pass'] = worst_rise <= P['riseMax_m'] + 1e-6 and gaps == 0

# headroom over the deck along the same lines
hits = 0
for l in P.get('lateralLines', [0.0]):
    t = t0
    while t <= t1 + 1e-9:
        h = bvh_both.ray_cast(pt(t, l, 30.0), DOWN, 100.0)
        if h[0] is not None:
            u = bvh_both.ray_cast(h[0] + Vector((0, 0, 0.02)), UP, P.get('headroom_m', 2.0))
            if u[0] is not None: hits += 1
        t += step
res['T2_headroomObstructions'] = hits

# water: deck must not rely on the water mesh, and must not intersect it
wz = []
for r in under:
    for c in r:
        if not c: continue
        h = bvh['water'].ray_cast(pt(c['t'], c['l'], c['zBottom'] + tol), DOWN, 100.0)
        if h[0] is not None: wz.append(c['zBottom'] - h[0].z)
res['T5_minClearAboveWater_m'] = None if not wz else round(min(wz), 4)
res['T5_waterIgnoredForSupport'] = True   # by construction: water never in the 'context' BVH
res['T5_pass'] = (not wz) or min(wz) >= 0.0

# crossing vs context triangle overlap (surface BVH only; not an exhaustive solid test)
ov = bvh['crossing'].overlap(bvh['context'])
res['T4_surfaceOverlapPairs'] = len(ov)
res['note'] = 'CPU raycast/BVH only; no GPU, no body simulation, no load calculation.'
rep['results'] = res
json.dump(rep, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False))
