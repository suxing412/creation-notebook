# LY-032 test harness (prep): check a future B door kit GLB against the frozen B door bay of a base GLB.
# Read-only. glTF axes (X east, Y up, Z south+). B door faces +Z (south).
# usage: blender -b --factory-startup --python-exit-code 1 -P m04_kit_check.py -- <base.glb> <out.json> <state> [kit.glb]
#   state: closed | open | half      (kit.glb omitted => base-only negative control)
# Exit code 0 always; verdicts are in out.json (PASS/FAIL per check). A runner compares them to test-plan.md.
import bpy, sys, json, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
base, out, state = argv[0], argv[1], argv[2]
kit = argv[3] if len(argv) > 3 else None
# frozen B bay (measured 2026-11-05 on granary-city-LOD0/1/2 5937211c/a1265bbf/6b2564d3, see out/scan-*.json)
JX = (2296.9641, 2298.4641)        # jamb faces
FY, LY = 1.10, 3.20                 # floor/sill top, lintel underside
ZO, ZI = -3676.969, -3677.169       # wall outer / inner face
STRIP = (2297.2641, 2298.1641)      # assumed 0.9 m candidate strip, centred on stair (to be confirmed by G)
TOL = 0.005

def load(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before and o.type == 'MESH']

def bvh_of(objs):
    dg = bpy.context.evaluated_depsgraph_get(); V, P = [], []
    for o in objs:
        me = o.evaluated_get(dg).to_mesh(); b = len(V)
        V += [o.matrix_world @ v.co for v in me.vertices]
        P += [[b + i for i in p.vertices] for p in me.polygons]
        o.evaluated_get(dg).to_mesh_clear()
    return BVHTree.FromPolygons(V, P, epsilon=0.0), V

def Bv(x, y, z): return Vector((x, -z, y))

bpy.ops.wm.read_factory_settings(use_empty=True)
base_objs = load(base)
bb, _ = bvh_of(base_objs)
r = {'base': base, 'kit': kit, 'state': state, 'checks': {}}
kb, kv = (None, [])
if kit:
    kit_objs = load(kit)
    kb, kv = bvh_of(kit_objs)
    r['kit_objects'] = [o.name for o in kit_objs]
    g = [(v.x, v.z, -v.y) for v in kv]
    mn = [min(p[i] for p in g) for i in range(3)]; mx = [max(p[i] for p in g) for i in range(3)]
    r['kit_bbox'] = [mn, mx]
    env_ok = (mn[0] >= JX[0] - 0.35 and mx[0] <= JX[1] + 0.35 and mn[1] >= FY - TOL and mx[1] <= 3.60 + TOL
              and mn[2] >= ZI - 0.80 and mx[2] <= ZO + 0.80)
    r['checks']['T03_envelope'] = 'PASS' if env_ok else 'FAIL'
    r['checks']['T04_leaf_above_floor'] = 'PASS' if mn[1] >= FY - TOL else 'FAIL'
    pairs = kb.overlap(bb)
    r['overlap_tri_pairs'] = len(pairs)
    r['checks']['T05_overlap_needs_classification'] = 'NONE' if not pairs else 'CLASSIFY'

def hit(tree, p, d, dist):
    if tree is None: return False
    loc, n, i, t = tree.ray_cast(Bv(*p), Bv(*d).normalized(), dist)
    return loc is not None

# T06 closed: every ray through the clear opening must be stopped by the kit within the wall depth + 0.30
tot = blk = 0
for i in range(1, 30):
    x = JX[0] + 0.02 + (JX[1] - JX[0] - 0.04) * i / 30
    for k in range(1, 20):
        y = FY + 0.02 + (LY - FY - 0.04) * k / 20
        tot += 1; blk += hit(kb, (x, y, ZO + 0.40), (0, 0, -1), 1.40)
r['closed_block_ratio'] = round(blk / tot, 4)
# T07 open: 0.9 strip corridor from stair top (z ZO+0.45) to 1.2 m inside must be free of kit geometry
tot2 = blk2 = 0
for i in range(0, 10):
    x = STRIP[0] + (STRIP[1] - STRIP[0]) * i / 9
    for k in range(0, 15):
        y = FY + 0.02 + (LY - 0.02 - FY - 0.02) * k / 14
        tot2 += 1; blk2 += hit(kb, (x, y, ZO + 0.45), (0, 0, -1), 0.45 + 0.20 + 1.20)
r['strip_rays'] = tot2; r['strip_blocked'] = blk2
# base must stay clear in the strip as well (regression on the shell itself)
base_blk = sum(hit(bb, (STRIP[0] + (STRIP[1] - STRIP[0]) * i / 9, FY + 0.02 + 1.0 * k / 14, ZO + 0.45), (0, 0, -1), 1.85)
               for i in range(10) for k in range(15))
r['strip_blocked_by_base'] = base_blk
if state == 'closed':
    r['checks']['T06_closed_blocks_opening'] = 'PASS' if r['closed_block_ratio'] >= 0.999 else 'FAIL'
elif state == 'open':
    r['checks']['T07_open_strip_clear'] = 'PASS' if blk2 == 0 and base_blk == 0 else 'FAIL'
    r['checks']['T08_open_not_blocking'] = 'PASS' if r['closed_block_ratio'] <= 0.25 else 'FAIL'
elif state == 'half':
    # half-open is a declared negative: it MUST intrude the strip, proving the test can fail
    r['checks']['T09_half_intrudes_strip_negative'] = 'PASS' if blk2 > 0 else 'FAIL'
json.dump(r, open(out, 'w'), indent=1)
print('LY032 kitcheck', state, r['closed_block_ratio'], blk2, base_blk, r['checks'])
