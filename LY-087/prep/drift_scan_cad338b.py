# LY-087 prep: read-only drift scan. For every GLB that the origin/main commit adds or changes
# relative to the bce3211 baseline, read the committed blob with `git show <rev>:<path>`
# (read-only), and list drain/water-like node, mesh and material names. Nothing is written to the lab.
import json, struct, hashlib, os, re, subprocess, sys
LAB = r'D:/GitHub/creation-notebook-lab'
BASE = 'bce3211f818ee5a8bef1773539da70695ba37b17'
REV = sys.argv[1] if len(sys.argv) > 1 else 'cad338b'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', f'drift-{REV}-drain-scan.json')
PAT = re.compile(r'drain|gutter|ditch|channel|culvert|sewer|sump|outlet|inlet|spout|water|river|canal|moat|pool|pond|well|shaft|trough|水|渠|沟|溝|涵|井|池|槽|排', re.I)

def git(*a):
    return subprocess.run(['git', '-C', LAB, *a], capture_output=True, check=True).stdout

full = git('rev-parse', REV).decode().strip()
names = git('diff', '--name-only', BASE, full).decode().split()
glbs = [n for n in names if n.lower().endswith('.glb')]
cd_base = git('show', f'{BASE}:docs/cities/luoyang/city-data.mjs')
cd_rev = git('show', f'{full}:docs/cities/luoyang/city-data.mjs')
res = {'base': BASE, 'rev': full, 'changedFiles': len(names), 'changedGlbs': [],
       'cityData': {'baseSha256': hashlib.sha256(cd_base).hexdigest(), 'revSha256': hashlib.sha256(cd_rev).hexdigest()}}
for n in glbs:
    try:
        raw = git('show', f'{full}:{n}')
    except subprocess.CalledProcessError:
        res['changedGlbs'].append({'path': n, 'deletedInRev': True}); continue
    clen = struct.unpack('<I', raw[12:16])[0]
    js = json.loads(raw[20:20 + clen].decode('utf-8'))
    hits = [{'kind': k, 'index': i, 'name': o.get('name', '')}
            for k in ('nodes', 'meshes', 'materials') for i, o in enumerate(js.get(k, [])) if PAT.search(o.get('name', ''))]
    res['changedGlbs'].append({'path': n, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw),
                               'nodes': len(js.get('nodes', [])), 'animations': len(js.get('animations', [])),
                               'hits': hits})
# city-data paths newly referenced at REV
pat = re.compile(rb'"(?:path|nearPath)"\s*:\s*"([^"]+\.glb)"')
added = sorted(set(pat.findall(cd_rev)) - set(pat.findall(cd_base)))
res['cityDataNewGlbRefs'] = [a.decode() for a in added]
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'changedGlbs'}, ensure_ascii=False, indent=1))
for g in res['changedGlbs']:
    print(g['path'], g.get('sha256', '')[:16], 'nodes', g.get('nodes'), 'anim', g.get('animations'), 'hits', [h['name'] for h in g.get('hits', [])])
