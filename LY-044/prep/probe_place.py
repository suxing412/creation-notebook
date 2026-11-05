# Trial (NOT a delivery) placement probe: stove bottom vertices vs ground-south, at the correct datum
# and at the wrong prototype datum 0.215 (negative), plus the W2 GLB loaded unchanged (negative).
# blender -b --factory-startup --python-exit-code 1 -P probe_place.py -- <lab_root> <out.json> [x z yaw]
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
argv = sys.argv[sys.argv.index('--') + 1:]
LAB, OUT = argv[0], argv[1]
X, Z, YAW = (float(argv[2]), float(argv[3]), float(argv[4])) if len(argv) > 4 else (533.0, -815.0, 0.0)
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
g = load(os.path.join(LAB, 'docs/cities/luoyang/assets/ground-atomic/south.glb'))
V, T, off = [], [], 0
for v, t in g.values(): V.append(v); T.append(t + off); off += len(v)
V = np.vstack(V); T = np.vstack(T)
lo = V[T].min(1); hi = V[T].max(1)
keep = (hi[:, 0] >= X - 4) & (lo[:, 0] <= X + 4) & (hi[:, 2] >= Z - 4) & (lo[:, 2] <= Z + 4)
tree = BVHTree.FromPolygons([Vector(p) for p in V], [tuple(map(int, x)) for x in T[keep]], all_triangles=True)
def gaps(pts):
    r = []
    for p in pts:
        h = tree.ray_cast(Vector((p[0], p[1] + 1.0, p[2])), Vector((0, -1, 0)), 3.0)
        r.append(None if h[0] is None else float(p[1] - h[0][1]))
    ok = [x for x in r if x is not None]
    return {'verts': len(r), 'noGround': len(r) - len(ok), 'gap_min': min(ok) if ok else None, 'gap_max': max(ok) if ok else None,
            'floating_gt_5mm': sum(1 for x in ok if x > 0.005), 'buried_lt_-1mm': sum(1 for x in ok if x < -0.001)}
res = {'tool': 'probe_place.py', 'trial': {'x': X, 'z': Z, 'yaw_deg': YAW}, 'scope': 'bottom-vertex vertical gap to ground-south only; not solid collision', 'cases': {}}
c, s = math.cos(math.radians(YAW)), math.sin(math.radians(YAW))
for fam in ('A', 'B'):
    st = load(os.path.join(LAB, f'docs/library/models/m-luoyang-cooking-stove/files/stove-{fam}-LOD0.glb'))
    for n, (v, t) in st.items():
        b = v[v[:, 1] < 0.0025]
        for datum in (0.2, 0.215):
            w = np.stack([X + c * b[:, 0] + s * b[:, 2], b[:, 1] + datum, Z - s * b[:, 0] + c * b[:, 2]], 1)
            res['cases'][f'{fam}/{n}/datum{datum}'] = gaps(w)
w2 = load(os.path.join(LAB, 'docs/library/models/m-luoyang-residential-preparation/files/W2-stove-A-LOD0.glb'))
b = np.vstack([v[v[:, 1] < 0.2025] for v, t in w2.values()])
res['cases']['W2-as-is-in-city'] = {'note': 'W2 sits at x~489, z~-1004, far outside ground-south triangles kept near the trial point', 'bottomVerts': int(len(b)),
                                     'bboxXZ': [float(b[:, 0].min()), float(b[:, 0].max()), float(b[:, 2].min()), float(b[:, 2].max())]}
json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
print('WROTE', OUT)
