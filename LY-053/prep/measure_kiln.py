# LY-053 prep: read-only measurement of tile-kiln GLBs.
# D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P measure_kiln.py -- out.json a.glb [b.glb ...]
# Reports per-node world bbox (glTF Y-up converted back: Blender Z-up, so glTF y == Blender z,
# glTF z == -Blender y), triangles, material, and planar/vertical stats; no file is modified.
import bpy, sys, json, hashlib, os
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
out, srcs = argv[0], argv[1:]
res = {}
for src in srcs:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    dg = bpy.context.evaluated_depsgraph_get()
    nodes = []
    for o in bpy.context.scene.objects:
        if o.type != 'MESH':
            continue
        me = o.evaluated_get(dg).to_mesh()
        me.calc_loop_triangles()
        mw = o.matrix_world
        vs = [mw @ v.co for v in me.vertices]
        lo = [min(v[i] for v in vs) for i in range(3)]
        hi = [max(v[i] for v in vs) for i in range(3)]
        # count up-facing / down-facing / vertical face area
        up = dn = vert = 0.0
        zs_up = {}
        for p in me.polygons:
            n = (mw.to_3x3() @ p.normal).normalized()
            a = p.area
            if n.z > 0.95:
                up += a
                z = round((mw @ p.center).z, 3)
                zs_up[z] = zs_up.get(z, 0) + a
            elif n.z < -0.95:
                dn += a
            elif abs(n.z) < 0.05:
                vert += a
        nodes.append({
            'name': o.name,
            'parent': o.parent.name if o.parent else None,
            'mat': [m.name for m in o.data.materials if m],
            'tris': len(me.loop_triangles),
            'verts': len(me.vertices),
            'min': [round(x, 4) for x in lo],
            'max': [round(x, 4) for x in hi],
            'size': [round(hi[i] - lo[i], 4) for i in range(3)],
            'upArea': round(up, 3), 'downArea': round(dn, 3), 'vertArea': round(vert, 3),
            'upZ': {str(k): round(v, 3) for k, v in sorted(zs_up.items())},
        })
        o.evaluated_get(dg).to_mesh_clear()
    h = hashlib.sha256(open(src, 'rb').read()).hexdigest()
    res[os.path.basename(src)] = {'sha256': h, 'bytes': os.path.getsize(src),
                                  'axis': 'Blender Z-up after glTF import (glTF +Y -> Blender +Z, glTF +Z -> Blender -Y)',
                                  'nodes': sorted(nodes, key=lambda n: n['name'])}
json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE', out)
