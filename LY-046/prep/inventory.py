# LY-046 prep: node inventory of every GLB under docs/cities/luoyang/assets, flagging
# water/drain/eave/roof related node and material names. Read-only.
# usage: python inventory.py <lab_root> <out_json>
import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbio import load, nodes_tris, sha256
LAB, OUT = sys.argv[1], sys.argv[2]
ROOT = os.path.join(LAB, 'docs/cities/luoyang/assets')
PAT = re.compile(r'drain|gutter|ditch|drip|water|channel|sewer|eave|roof|apron|slope|threshold|step|sill|gou|shui|plinth|lot|lane|ground', re.I)
rep = {}
for dp, dn, fn in os.walk(ROOT):
    for f in sorted(fn):
        if not f.endswith('.glb'): continue
        p = os.path.join(dp, f); rel = os.path.relpath(p, os.path.join(LAB, 'docs/cities/luoyang')).replace(os.sep, '/')
        js, _ = load(p)
        names = [n.get('name', '') for n in js.get('nodes', [])]
        mats = [m.get('name', '') for m in js.get('materials', [])]
        rep[rel] = {'sha256': sha256(p), 'bytes': os.path.getsize(p), 'nodes': len(names),
                    'flagNodes': sorted(set(n for n in names if PAT.search(n))),
                    'waterish': sorted(set(n for n in names + mats if re.search(r'drain|gutter|ditch|drip|water|channel|sewer|水|沟', n, re.I))),
                    'materials': mats}
json.dump(rep, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for k, v in rep.items():
    if v['waterish']: print('WATER', k, v['waterish'][:12])
print(len(rep), 'glbs')
