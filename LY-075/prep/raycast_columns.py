# LY-075 prep: Blender headless multi-hit vertical ray columns over a GLB.
# Usage: blender -b --factory-startup --python-exit-code 1 -P raycast_columns.py -- <glb> <out.npz> [step_m]
# Output frame = glTF frame (x, y-up, z). Blender import maps glTF (x,y,z) -> Blender (x,-z,y).
# For every grid column (x, z) it records all surface hits from above down (height y, normal-up sign,
# material id). Read-only on the GLB; writes only <out.npz>.
import bpy, sys, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
src, out = argv[0], argv[1]
step = float(argv[2]) if len(argv) > 2 else 0.05
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
dg = bpy.context.evaluated_depsgraph_get()
verts, polys, pmat = [], [], []
mat_names = []
for o in bpy.context.scene.objects:
    if o.type != 'MESH':
        continue
    me = o.evaluated_get(dg).to_mesh()
    me.calc_loop_triangles()
    base = len(verts)
    M = o.matrix_world
    verts.extend([M @ v.co for v in me.vertices])
    key = o.name.split('static_')[-1] if 'static_' in o.name else o.name
    if key not in mat_names:
        mat_names.append(key)
    mid = mat_names.index(key)
    for t in me.loop_triangles:
        polys.append([base + i for i in t.vertices]); pmat.append(mid)
bvh = BVHTree.FromPolygons(verts, polys, all_triangles=True)
V = np.array([tuple(v) for v in verts])
lo, hi = V.min(0), V.max(0)  # Blender frame
xs = np.arange(lo[0] + step / 2, hi[0], step)
ys = np.arange(lo[1] + step / 2, hi[1], step)  # Blender y = -gltf z
top = hi[2] + 1.0
MAXH = 24
H = np.full((len(xs), len(ys), MAXH), np.nan, np.float32)  # hit height (gltf y)
NU = np.zeros((len(xs), len(ys), MAXH), np.int8)           # +1 normal up, -1 down, 0 vertical-ish
MT = np.full((len(xs), len(ys), MAXH), -1, np.int8)
down = Vector((0, 0, -1))
for i, x in enumerate(xs):
    for j, y in enumerate(ys):
        z = top; k = 0
        while k < MAXH:
            loc, nor, idx, dist = bvh.ray_cast(Vector((x, y, z)), down)
            if loc is None:
                break
            H[i, j, k] = loc.z
            NU[i, j, k] = 1 if nor.z > 0.5 else (-1 if nor.z < -0.5 else 0)
            MT[i, j, k] = pmat[idx]
            k += 1
            z = loc.z - 1e-4
# convert columns to gltf frame: gltf x = bl x, gltf z = -bl y
np.savez_compressed(out, H=H, NU=NU, MT=MT, xs=xs, zs=-ys, step=step, mats=np.array(mat_names),
                    bbox_lo=np.array([lo[0], lo[2], -hi[1]]), bbox_hi=np.array([hi[0], hi[2], -lo[1]]), src=src)
print('DONE', src, H.shape, 'tris', len(polys), 'mats', mat_names)
