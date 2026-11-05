# LY-087 prep: read-only inventory of drainage/water-like node, mesh and material names
# in every GLB under creation-notebook-lab/docs. Reads only the JSON chunk.
import json, struct, hashlib, os, re, csv
ROOT = r'D:/GitHub/creation-notebook-lab/docs'
LEDGER = r'D:/GitHub/creation-notebook-workpacks/LY-001/qa/glb-files.csv'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'drain-name-inventory.json')
PAT = re.compile(r'drain|gutter|ditch|channel|culvert|sewer|sump|outlet|inlet|spout|water|river|canal|moat|pool|pond|well|shaft|trough|水|渠|沟|溝|涵|井|池|槽|排', re.I)
cls = {}
with open(LEDGER, encoding='utf-8') as f:
    for r in csv.DictReader(f):
        cls[r['path']] = (r['class'], r['sha256'])
res = []
for dp, dn, fn in os.walk(ROOT):
    for n in fn:
        if not n.lower().endswith('.glb'):
            continue
        p = os.path.join(dp, n)
        raw = open(p, 'rb').read()
        sha = hashlib.sha256(raw).hexdigest()
        clen, ctype = struct.unpack('<II', raw[12:20])
        js = json.loads(raw[20:20 + clen].decode('utf-8'))
        hits = []
        for kind in ('nodes', 'meshes', 'materials'):
            for i, o in enumerate(js.get(kind, [])):
                nm = o.get('name', '')
                if PAT.search(nm):
                    hits.append({'kind': kind, 'index': i, 'name': nm})
        if hits:
            rel = os.path.relpath(p, ROOT).replace(os.sep, '/')
            c, lsha = cls.get(rel, ('(not in LY-001 ledger)', None))
            res.append({'path': rel, 'sha256': sha, 'ledgerSha256Match': (lsha == sha) if lsha else None,
                        'loadClass': c, 'extensionsUsed': js.get('extensionsUsed', []), 'hits': hits})
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for r in res:
    names = sorted(set(h['name'] for h in r['hits']))
    print(r['loadClass'][:16], '|', r['path'], len(r['hits']), names[:6])
