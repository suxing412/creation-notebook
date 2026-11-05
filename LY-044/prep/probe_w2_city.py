# Negative probe: what would happen if the W2 GLB (life-block frame) were loaded as-is into the city.
# blender -b --factory-startup --python-exit-code 1 -P probe_w2_city.py -- <lab_root> <out.json>
import bpy, sys, os, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
argv = sys.argv[sys.argv.index('--') + 1:]
LAB, OUT = argv[0], argv[1]
CITY = os.path.join(LAB, 'docs/cities/luoyang')
def load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    dg = bpy.context.evaluated_depsgraph_get(); out = {}
    for o in bpy.context.scene.objects:
        if o.type != 'MESH': continue
        me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); mw = o.matrix_world
        v = np.array([tuple(mw @ x.co) for x in me.vertices]).reshape(-1, 3); v = np.stack([v[:, 0], v[:, 2], -v[:, 1]], 1)
        t = np.array([tuple(l.vertices) for l in me.loop_triangles]).reshape(-1, 3)
        out[o.name] = (v, t); o.evaluated_get(dg).to_mesh_clear()
    return out
w2 = load(os.path.join(LAB, 'docs/library/models/m-luoyang-residential-preparation/files/W2-stove-A-LOD0.glb'))
bot = np.vstack([v[v[:, 1] < 0.202] for v, t in w2.values()])
res = {}
for gid, rel, tr in (('ground-network', 'assets/ground-atomic/network-ground-stitched.glb', (0, 0, 0)),
                     ('ground-retained', 'assets/ground-atomic/retained.glb', (0, 0, 0)),
                     ('ground-south', 'assets/ground-atomic/south.glb', (0, 0, 0)),
                     ('ground-D08', 'assets/ground-atomic/D08.glb', (580, 0, -960))):
    V, T, off = [], [], 0
    for n, (v, t) in load(os.path.join(CITY, rel)).items():
        v = v + np.array(tr, float)
        V.append(v); T.append(t + off); off += len(v)
    V = np.vstack(V); T = np.vstack(T)
    lo = V[T].min(1); hi = V[T].max(1)
    keep = (hi[:, 0] >= 486) & (lo[:, 0] <= 492) & (hi[:, 2] >= -1007) & (lo[:, 2] <= -1001)
    if not keep.any(): res[gid] = None; continue
    tree = BVHTree.FromPolygons([Vector(p) for p in V], [tuple(map(int, x)) for x in T[keep]], all_triangles=True)
    hs = []
    for p in bot:
        h = tree.ray_cast(Vector((p[0], 20.0, p[2])), Vector((0, -1, 0)), 40.0)
        hs.append(None if h[0] is None else float(h[0][1]))
    ok = [x for x in hs if x is not None]
    res[gid] = {'hits': len(ok), 'of': len(hs), 'groundY_min': min(ok) if ok else None, 'groundY_max': max(ok) if ok else None,
                'w2BottomY': float(bot[:, 1].min()), 'gap_min': float(bot[:, 1].min() - max(ok)) if ok else None}
json.dump({'tool': 'probe_w2_city.py', 'w2BottomVerts': int(len(bot)), 'cityGroundUnderW2': res,
           'meaning': 'negative case: W2 coordinates are life-block (13-yard) frame; loading W2 as-is in the city puts it outside any of the 44 lots'},
          open(OUT, 'w', encoding='utf-8'), indent=1)
print('WROTE', OUT)
