# LY-006: read-only dump of glTF node trees (name, parent, mesh, world AABB) for GLBs listed in
# LY-001 snapshot-ledger glbFiles. Writes qa/glb-node-index.json. Lab repo is only read.
import json, sys, os, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from glbio import read_glb, world_matrices, accessor, apply

LAB_DOCS, LEDGER, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
led = json.load(open(LEDGER, encoding='utf-8'))
out = {'labDocs': LAB_DOCS, 'ledger': LEDGER, 'files': {}}
for gf in led['glbFiles']:
    p = os.path.join(LAB_DOCS, gf['path'])
    if not os.path.exists(p):
        out['files'][gf['path']] = {'error': 'missing'}; continue
    g = read_glb(p)
    js = g['json']
    world, parent = world_matrices(g)
    nodes = []
    for i, n in enumerate(js.get('nodes', [])):
        rec = {'i': i, 'name': n.get('name', ''), 'parent': parent.get(i), 'inScene': i in world}
        if 'mesh' in n and i in world:
            mn = np.full(3, np.inf); mx = np.full(3, -np.inf); tris = 0
            for pr in js['meshes'][n['mesh']]['primitives']:
                pos = accessor(g, pr['attributes']['POSITION']).astype(np.float64)
                wp = apply(world[i], pos)
                mn = np.minimum(mn, wp.min(0)); mx = np.maximum(mx, wp.max(0))
                if 'indices' in pr:
                    tris += js['accessors'][pr['indices']]['count'] // 3
                else:
                    tris += len(pos) // 3
            rec['aabb'] = [mn.round(5).tolist(), mx.round(5).tolist()]
            rec['tris'] = int(tris)
        nodes.append(rec)
    out['files'][gf['path']] = {'sha256': g['sha256'], 'bytes': g['size'], 'ledgerSha256': gf['sha256'],
                                'nodeCount': len(nodes), 'nodes': nodes}
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
print('files', len(out['files']), 'nodes', sum(f.get('nodeCount', 0) for f in out['files'].values()))
