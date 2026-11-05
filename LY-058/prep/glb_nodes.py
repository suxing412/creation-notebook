# LY-058 prep: read-only GLB structure dump (nodes, meshes, materials, per-primitive bounds).
# usage: python glb_nodes.py <glb> [<glb> ...]  -> JSON on stdout
import json, struct, sys, hashlib

def load(path):
    b = open(path, 'rb').read()
    magic, ver, length = struct.unpack('<III', b[:12])
    off = 12; js = None
    while off < length:
        cl, ct = struct.unpack('<II', b[off:off + 8]); off += 8
        if ct == 0x4E4F534A:
            js = json.loads(b[off:off + cl])
        off += cl
    return b, js

out = []
for p in sys.argv[1:]:
    b, js = load(p)
    rec = {'path': p, 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest(),
           'generator': js.get('asset', {}).get('generator'), 'nodes': [], 'materials': [m.get('name') for m in js.get('materials', [])],
           'extras': js.get('asset', {}).get('extras')}
    for i, n in enumerate(js.get('nodes', [])):
        e = {'i': i, 'name': n.get('name'), 'mesh': n.get('mesh')}
        for k in ('translation', 'rotation', 'scale', 'matrix', 'children', 'extras'):
            if k in n: e[k] = n[k]
        if 'mesh' in n:
            me = js['meshes'][n['mesh']]
            e['meshName'] = me.get('name')
            prims = []
            for pr in me['primitives']:
                a = js['accessors'][pr['attributes']['POSITION']]
                prims.append({'material': js['materials'][pr['material']].get('name') if 'material' in pr else None,
                              'min': a.get('min'), 'max': a.get('max'), 'verts': a['count'],
                              'tris': js['accessors'][pr['indices']]['count'] // 3 if 'indices' in pr else None})
            e['prims'] = prims
        rec['nodes'].append(e)
    out.append(rec)
print(json.dumps(out, ensure_ascii=False, indent=1))
