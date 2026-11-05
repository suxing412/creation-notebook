# LY-060 prep: compare private-master trial chunk res_workyard_034.glb with public workyard-LOD0.glb.
# Pure-python GLB reader (no Blender). Usage: python -I compare_trial_chunk.py <trial.glb> <workyard-LOD0.glb> <out.json>
import hashlib, json, struct, sys


def load(path):
    b = open(path, 'rb').read()
    magic, ver, length = struct.unpack_from('<III', b, 0)
    assert magic == 0x46546C67 and length == len(b)
    jl, jt = struct.unpack_from('<II', b, 12)
    g = json.loads(b[20:20 + jl].decode('utf-8'))
    off = 20 + jl
    bl, bt = struct.unpack_from('<II', b, off)
    binc = b[off + 8: off + 8 + bl]
    return g, binc, hashlib.sha256(b).hexdigest(), len(b)


def positions(g, binc, acc_i):
    a = g['accessors'][acc_i]
    bv = g['bufferViews'][a['bufferView']]
    start = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = bv.get('byteStride', 12)
    out = []
    for i in range(a['count']):
        out.append(struct.unpack_from('<fff', binc, start + i * stride))
    return out


def summarize(path):
    g, binc, sha, n = load(path)
    meshes = {}
    for ni, node in enumerate(g.get('nodes', [])):
        if 'mesh' not in node:
            continue
        m = g['meshes'][node['mesh']]
        pts, tris = [], 0
        for p in m['primitives']:
            pts += positions(g, binc, p['attributes']['POSITION'])
            if 'indices' in p:
                tris += g['accessors'][p['indices']]['count'] // 3
        mn = [min(q[k] for q in pts) for k in range(3)]
        mx = [max(q[k] for q in pts) for k in range(3)]
        name = node.get('name', 'node%d' % ni)
        meshes[name] = {
            'translation': node.get('translation'), 'rotation': node.get('rotation'), 'scale': node.get('scale'),
            'matrix': node.get('matrix'), 'verts': len(pts), 'tris': tris, 'min': mn, 'max': mx,
            'materials': [g['materials'][p['material']].get('name') for p in m['primitives'] if 'material' in p],
        }
    return {'path': path, 'sha256': sha, 'bytes': n, 'meshes': meshes,
            'images': len(g.get('images', [])), 'extrasAsset': g.get('asset', {})}


trial, pub = summarize(sys.argv[1]), summarize(sys.argv[2])


def short(n):
    for pre in ('C02-034__workyard_trial__',):
        if n.startswith(pre):
            return n[len(pre):]
    return n


pairs = []
pm = pub['meshes']
for tn, t in trial['meshes'].items():
    k = short(tn)
    p = pm.get(k)
    if not p:
        pairs.append({'trial': tn, 'public': None})
        continue
    dmin = [t['min'][i] - p['min'][i] for i in range(3)]
    dmax = [t['max'][i] - p['max'][i] for i in range(3)]
    pairs.append({'trial': tn, 'public': k, 'sameVerts': t['verts'] == p['verts'], 'sameTris': t['tris'] == p['tris'],
                  'trialTranslation': t['translation'], 'publicTranslation': p['translation'],
                  'deltaMin_localMesh': dmin, 'deltaMax_localMesh': dmax,
                  'trialMaterials': t['materials'], 'publicMaterials': p['materials']})
json.dump({'trial': {k: trial[k] for k in ('path', 'sha256', 'bytes', 'images')},
           'public': {k: pub[k] for k in ('path', 'sha256', 'bytes', 'images')},
           'pairs': pairs,
           'publicOnly': [k for k in pm if k not in {short(n) for n in trial['meshes']}],
           'trialMeshes': trial['meshes'], 'publicMeshes': pm},
          open(sys.argv[3], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(pairs, ensure_ascii=False, indent=1))
