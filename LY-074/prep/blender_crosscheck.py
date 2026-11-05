"""LY-074 prep: independent Blender cross-check of the numpy GLB reader (measure_access.py /
stair_exact.py).  Read-only: imports each mingtang GLB into a factory-startup scene and
prints bbox, per-object matrix, base footprint half width, stair foot radius on the four
axes and the lowest/highest vertex.  Writes nothing except the JSON given as last arg.

usage:
  D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P blender_crosscheck.py -- <out.json> <glb>...

Blender imports glTF Y-up as Z-up: glTF (x, y, z) -> Blender (x, -z, y).  We report in the
glTF frame again (x, y_up, z) so the numbers compare 1:1 with stair-exact.json.
"""
import bpy, sys, json, hashlib
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
out_path, glbs = argv[0], argv[1:]
res = {}
for p in glbs:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=p)
    sha = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    rec = {'sha256': sha, 'objects': {}}
    allv = []
    for o in objs:
        M = o.matrix_world
        ident = all(abs(M[i][j] - (1.0 if i == j else 0.0)) < 1e-9 for i in range(4) for j in range(4))
        co = np.array([(M @ v.co)[:] for v in o.data.vertices])
        g = np.stack([co[:, 0], co[:, 2], -co[:, 1]], 1)  # back to glTF frame
        allv.append((o.name, g))
        rec['objects'][o.name] = {
            'matrix_world_identity_after_import': ident,
            'verts': len(o.data.vertices), 'tris': sum(len(pl.vertices) - 2 for pl in o.data.polygons),
            'min': [round(float(x), 4) for x in g.min(0)], 'max': [round(float(x), 4) for x in g.max(0)],
            'materials': [m.name for m in o.data.materials if m],
        }
    earth = [g for n, g in allv if n.endswith('static_earth')][0]
    # stair foot radius on each axis: max extent of earth verts within the stair lateral band
    feet = {}
    for side, (ax, sg) in {'+X': (0, 1), '-X': (0, -1), '+Z': (2, 1), '-Z': (2, -1)}.items():
        lat = 2 - ax
        band = earth[np.abs(earth[:, lat]) <= 2.1001]
        feet[side] = round(float((band[:, ax] * sg).max()), 4)
        # base half width: extent of earth verts well outside the stair band
        off = earth[np.abs(earth[:, lat]) > 3.0]
        feet[side + '_base_half'] = round(float((off[:, ax] * sg).max()), 4)
    rec['stair_foot_r'] = feet
    rec['earth_y_min'] = round(float(earth[:, 1].min()), 4)
    allg = np.concatenate([g for _, g in allv])
    rec['bbox_min'] = [round(float(x), 4) for x in allg.min(0)]
    rec['bbox_max'] = [round(float(x), 4) for x in allg.max(0)]
    res[p.replace('\\', '/').split('/')[-1]] = rec
json.dump(res, open(out_path, 'w'), indent=1)
print('CROSSCHECK WROTE', out_path, len(res))
