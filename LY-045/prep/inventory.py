# LY-045 prep: loose-part inventory of a GLB, reported in glTF coords (x, y-up, z).
# D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P inventory.py -- in.glb out.json
import bpy, bmesh, sys, json, hashlib
argv = sys.argv[sys.argv.index('--') + 1:]
src, out = argv[0], argv[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
def g(v):  # blender -> glTF
    return [round(v.x, 4), round(v.z, 4), round(-v.y, 4)]
res = {'file': src, 'sha256': hashlib.sha256(open(src, 'rb').read()).hexdigest(), 'objects': []}
for o in bpy.context.scene.objects:
    if o.type != 'MESH':
        continue
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    bm.verts.ensure_lookup_table()
    seen = set(); parts = []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack = [v]; comp = []; seen.add(v.index)
        while stack:
            w = stack.pop(); comp.append(w)
            for e in w.link_edges:
                u = e.other_vert(w)
                if u.index not in seen:
                    seen.add(u.index); stack.append(u)
        cs = [g(w.co) for w in comp]
        lo = [min(c[i] for c in cs) for i in range(3)]; hi = [max(c[i] for c in cs) for i in range(3)]
        faces = set(f.index for w in comp for f in w.link_faces)
        parts.append({'verts': len(comp), 'faces': len(faces), 'min': lo, 'max': hi,
                      'size': [round(hi[i] - lo[i], 4) for i in range(3)]})
    parts.sort(key=lambda p: (p['min'][1], p['min'][0], p['min'][2]))
    res['objects'].append({'name': o.name, 'material': [m.name for m in o.data.materials],
                           'tris': sum(len(f.verts) - 2 for f in bm.faces), 'parts': parts})
    bm.free()
json.dump(res, open(out, 'w'), indent=1)
print('parts', {o['name']: len(o['parts']) for o in res['objects']})
