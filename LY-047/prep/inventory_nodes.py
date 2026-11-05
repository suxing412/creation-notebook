# LY-047 prep: per-node inventory (tris, bbox, materials) of candidate storage/shed GLBs. Read-only.
# usage: python -I inventory_nodes.py <lab_docs_root> <out.json> rel1.glb rel2.glb ...
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import glbio

root, outp, rels = sys.argv[1], sys.argv[2], sys.argv[3:]
res = {}
for rel in rels:
    p = os.path.join(root, rel)
    nodes = glbio.node_tris(p)
    ent = {'sha256': glbio.sha256(p), 'bytes': os.path.getsize(p), 'nodes': {}}
    for n, (T, ml) in nodes.items():
        V = T.reshape(-1, 3)
        ent['nodes'][n] = {'tris': int(len(T)), 'min': np.round(V.min(0), 4).tolist() if len(V) else None,
                           'max': np.round(V.max(0), 4).tolist() if len(V) else None, 'materials': ml}
    res[rel] = ent
json.dump(res, open(outp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for rel, e in res.items():
    print('==', rel, e['sha256'][:16], e['bytes'])
    for n, d in e['nodes'].items():
        print(f"  {n:55s} {d['tris']:6d} {d['min']} {d['max']} {d['materials']}")
