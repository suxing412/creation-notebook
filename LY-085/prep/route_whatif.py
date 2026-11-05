# LY-085 prep: discrete support-reach test, gate outer side-passage ports -> docs road end, Pingcheng.
# Compositions (all read-only inputs, nothing is exported):
#   C0 docs city now      : pingcheng-ground-LODn strips + docs network-ground-stitched
#   C1 + mother segment   : C0 + mother-1e8c4d chunk C_stitch_primary clipped to local y in [-60.6, -10.0]
#   N1 negative           : C1 but strips removed (road segment alone must not reach the side passages)
# Grid 0.1 m in gate-local x[-12,12], y[-66,-2.0] (start cells at y=-5.0 inside the open side passages); a cell is walkable when every sample of a square
# footprint (half-width h) has a support hit (presence erosion; z spread reported) and no gate/wall solid
# between support+0.05 and support+1.9 m (vertical ray). 4-neighbour BFS, step tolerance 0.02 m.
# This is a discrete local check, not continuous body motion, vehicles or structure.
#   D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P route_whatif.py -- <lab_root> <chunk.glb> <out.json>
import bpy, sys, json, hashlib
from pathlib import Path
from collections import deque
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]; LAB = Path(a[0]); CH = Path(a[1]); OUT = Path(a[2])
D = LAB / 'docs'; CITY = D / 'cities/luoyang'


def load(p, M=Matrix.Identity(4)):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=str(p))
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
    return BVHTree.FromPolygons(vs, fs, epsilon=0.0) if fs else None


bpy.ops.wm.read_factory_settings(use_empty=True)
src = json.loads((CITY / 'progress-assets/north13-gates/source.json').read_text(encoding='utf-8'))
pl = [p['placement'] for p in src['packages'] if p['package'] == 'luoyang-pingcheng-gate-study-v1'][0]
T = Matrix.Translation(Vector(pl['engineering_origin_from_existing_wall_caps'])) @ Matrix.Rotation(pl['rotation_z_rad'], 4, 'Z'); Ti = T.inverted()
# everything converted to gate-local
docs_road = [o for o in load(CITY / 'assets/ground-atomic/network-ground-stitched.glb', Ti) if o['name'] == 'C_stitch_primary']
mom = load(CH, Ti)
# mother road used only inside local y in [-60.6,-10.0] (support hits outside the window are ignored;
# the road triangles are tens of metres long, so this is a query-side clip, not an exported cut)
SEGWINS = {'M10': (-60.6, -10.0), 'M64': (-60.6, -6.4)}   # stop at outer port vs stop at gate outer face (-6.353)
walls = []
for w in ('wall-05', 'wall-06'):
    walls += load(CITY / 'assets/city-wall/A' / (w + '.glb'), Ti)
res = {'note': 'discrete grid reach, gate-local frame', 'chunk_sha256': hashlib.sha256(CH.read_bytes()).hexdigest(),
       'mother_segment_windows_local_y': SEGWINS, 'runs': {}}
MB = bvh(mom); DB = bvh(docs_road)
for lod in range(3):
    strips = load(D / ('library/models/m-luoyang-pingcheng-gate/files/pingcheng-ground-LOD%d.glb' % lod))
    gate = load(D / ['library/models/m-luoyang-pingcheng-gate/files/pingcheng-P-LOD0.glb',
                     'cities/luoyang/progress-assets/north13-gates/luoyang-pingcheng-gate-study-v1/models/pingcheng-P-LOD1.glb',
                     'cities/luoyang/progress-assets/north13-gates/luoyang-pingcheng-gate-study-v1/models/pingcheng-P-LOD2.glb'][lod])
    SOL = bvh(gate + walls)
    SB = bvh(strips)
    comps = {'C0_docs_now': (SB, DB), 'C1a_plus_mother_seg_to_y-10': (SB, DB, 'M10'), 'C1b_plus_mother_seg_to_y-6.4': (SB, DB, 'M64'),
             'N1_seg_to_y-6.4_without_strips': (DB, 'M64'), 'N2_strips_plus_seg_only_no_docs_road': (SB, 'M64')}
    for cname, parts in comps.items():
        def sup(x, y):
            best = None
            for B in parts:
                if isinstance(B, str):
                    w = SEGWINS[B]
                    if not (w[0] <= y <= w[1]): continue
                    B = MB
                h = B.ray_cast(Vector((x, y, 3.0)), Vector((0, 0, -1)), 6.0)
                if h[0] is not None and (best is None or h[0].z > best): best = h[0].z
            return best
        X0, X1, Y0, Y1, S = -12.0, 12.0, -66.0, -2.0, 0.1
        nx = int(round((X1 - X0) / S)) + 1; ny = int(round((Y1 - Y0) / S)) + 1
        top = {}
        for j in range(ny):
            for i in range(nx):
                x = X0 + i * S; y = Y0 + j * S
                z = sup(x, y)
                if z is None: continue
                b = SOL.ray_cast(Vector((x, y, z + 0.05)), Vector((0, 0, 1)), 1.85)
                if b[0] is None: top[(i, j)] = z
        for hw in (0.3, 0.5):
            k = int(round(hw / S))
            # separable presence erosion (square footprint); z spread is checked separately below
            rowok = {(i, j) for (i, j) in top if all((i + d, j) in top for d in range(-k, k + 1))}
            ok = {(i, j) for (i, j) in rowok if all((i, j + d) in rowok for d in range(-k, k + 1))}
            cell = lambda x, y: (int(round((x - X0) / S)), int(round((y - Y0) / S)))
            out = {}
            for side, xs in (('W', -7.9), ('E', 7.9)):
                st = cell(xs, -5.0)
                seen = {st} if st in ok else set(); q = deque(seen)
                while q:
                    i, j = q.popleft()
                    for n in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                        if n in ok and n not in seen and abs(top[n] - top[(i, j)]) <= 0.02: seen.add(n); q.append(n)
                minj = min((j for _, j in seen), default=None)
                zs = [top[c] for c in seen]
                out[side] = {'start_walkable': st in ok, 'reached_cells': len(seen), 'z_local_range': [round(min(zs), 4), round(max(zs), 4)] if zs else None,
                             'southmost_local_y': round(Y0 + minj * S, 2) if minj is not None else None,
                             'reaches_docs_road_end_y<=-60.6': (minj is not None and Y0 + minj * S <= -60.6),
                             'reaches_y<=-65.0_on_docs_road': (minj is not None and Y0 + minj * S <= -65.0)}
            res['runs']['LOD%d|%s|halfwidth%.1f' % (lod, cname, hw)] = out
OUT.write_text(json.dumps(res, indent=1), encoding='utf-8'); print('ROUTE_OK')
