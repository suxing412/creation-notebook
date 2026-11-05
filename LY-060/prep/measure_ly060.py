# LY-060 prep: read-only measurement of every workshop-line GLB that LY-060 would assemble.
# Usage:
#   D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P measure_ly060.py -- out.json a.glb [b.glb ...]
# Blender Z-up after glTF import (glTF +Y -> Blender +Z, glTF +Z -> Blender -Y). Nothing is modified or exported.
# Per file: SHA256, world bbox, footprint, lowest z per node, up-facing area at the lowest level (what would
# sit on terrain), node names / materials / tris, and simple "support plate" candidates (large flat up faces).
import bpy, sys, json, hashlib, os

argv = sys.argv[sys.argv.index('--') + 1:]
out, srcs = argv[0], argv[1:]
res = {}
for src in srcs:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    dg = bpy.context.evaluated_depsgraph_get()
    nodes = []
    glo = [1e9] * 3; ghi = [-1e9] * 3
    for o in bpy.context.scene.objects:
        if o.type != 'MESH':
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        mw = o.matrix_world
        vs = [mw @ v.co for v in me.vertices]
        lo = [min(v[i] for v in vs) for i in range(3)]
        hi = [max(v[i] for v in vs) for i in range(3)]
        for i in range(3):
            glo[i] = min(glo[i], lo[i]); ghi[i] = max(ghi[i], hi[i])
        up = {}
        dnmin = 0.0
        for p in me.polygons:
            n = (mw.to_3x3() @ p.normal).normalized()
            c = mw @ p.center
            if n.z > 0.95:
                z = round(c.z, 3)
                up[z] = up.get(z, 0) + p.area
            if n.z < -0.95 and abs(c.z - lo[2]) < 0.005:
                dnmin += p.area
        top_up = sorted(up.items(), key=lambda kv: -kv[1])[:6]
        nodes.append({
            'name': o.name,
            'mat': [m.name for m in o.data.materials if m],
            'tris': len(me.loop_triangles), 'verts': len(me.vertices),
            'min': [round(x, 4) for x in lo], 'max': [round(x, 4) for x in hi],
            'size': [round(hi[i] - lo[i], 4) for i in range(3)],
            'bottomDownArea': round(dnmin, 3),
            'largestUpLevels': [[k, round(v, 3)] for k, v in top_up],
        })
        ev.to_mesh_clear()
    nodes.sort(key=lambda n: n['name'])
    lowest = min(nodes, key=lambda n: n['min'][2]) if nodes else None
    res[os.path.basename(os.path.dirname(os.path.dirname(src))) + '/' + os.path.basename(src)] = {
        'path': src.replace(os.sep, '/'),
        'sha256': hashlib.sha256(open(src, 'rb').read()).hexdigest(),
        'bytes': os.path.getsize(src),
        'bboxMin': [round(x, 4) for x in glo], 'bboxMax': [round(x, 4) for x in ghi],
        'footprintXY': [round(ghi[0] - glo[0], 3), round(ghi[1] - glo[1], 3)],
        'footprintArea': round((ghi[0] - glo[0]) * (ghi[1] - glo[1]), 2),
        'height': round(ghi[2] - glo[2], 3),
        'lowestNode': lowest['name'] if lowest else None,
        'nodesTouchingMinZ': [n['name'] for n in nodes if abs(n['min'][2] - glo[2]) < 0.005],
        'nodeCount': len(nodes), 'tris': sum(n['tris'] for n in nodes),
        'nodes': nodes,
    }
json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE', out, len(res))
