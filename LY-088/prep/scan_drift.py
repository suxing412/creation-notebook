# LY-088 prep: drift check between the frozen baseline and a newer lab ref.
# Usage: python -I scan_drift.py <lab_repo> <base_rev> <new_rev> <out_json>
# Read-only: uses `git show <rev>:<path>` and `git ls-tree`; never touches the work tree.
# For each rev: (a) blob SHA of the water-relevant inputs, (b) every .glb path string referenced by
# city-data.mjs / app.mjs at that rev, scanned for water-like node/mesh/material names,
# (c) water-like sentences in city-data.mjs. Output: per-rev results + diff summary.
import sys, json, hashlib, subprocess, struct, re

LAB, BASE, NEW, OUT = sys.argv[1:5]
WATER = re.compile(r'(water|river|canal|channel|moat|stream|pond|lake|drain|ditch|水|渠|河|池|壍|濠|沟|溝|漕)', re.I)
RIVER = re.compile(r'(river|canal|waterway|河|渠)', re.I)
INPUTS = [
    'docs/cities/luoyang/data/evidence/evidence-geometry.json',
    'docs/cities/luoyang/research/2026-11-03/city-milestones.json',
    'docs/cities/luoyang/p-luoyang.asset.json',
    'docs/cities/luoyang/city-data.mjs',
    'docs/cities/luoyang/app.mjs',
    'docs/cities/luoyang/index.html',
    'docs/cities/luoyang/v1/evidence-view.mjs',
    'docs/cities/luoyang/assets/ground-atomic/network-ground-stitched.glb',
    'docs/cities/luoyang/data/west/road-plan.json',
    'docs/cities/luoyang/data/west/ground-atomic-contract.json',
    'docs/library/models/m-luoyang-palace-waterway-interface/m-luoyang-palace-waterway-interface.asset.json',
]

def show(rev, path):
    r = subprocess.run(['git', '-C', LAB, 'show', f'{rev}:{path}'], capture_output=True)
    return r.stdout if r.returncode == 0 else None

def full(rev):
    return subprocess.run(['git', '-C', LAB, 'rev-parse', rev], capture_output=True, text=True, check=True).stdout.strip()

def glb_names(b):
    magic, _, _ = struct.unpack_from('<4sII', b, 0)
    if magic != b'glTF':
        return None
    clen, _ = struct.unpack_from('<II', b, 12)
    j = json.loads(b[20:20 + clen].decode('utf-8'))
    out = []
    for coll in ('nodes', 'meshes', 'materials'):
        for i, o in enumerate(j.get(coll, [])):
            n = o.get('name', '')
            if WATER.search(n):
                out.append(f'{coll}[{i}]={n}')
    return out

def scan(rev):
    res = {'rev': full(rev), 'inputs': {}, 'glbs': {}, 'waterSentencesCityData': []}
    for p in INPUTS:
        b = show(rev, p)
        res['inputs'][p] = hashlib.sha256(b).hexdigest() if b is not None else None
    cd = (show(rev, 'docs/cities/luoyang/city-data.mjs') or b'').decode('utf-8')
    app = (show(rev, 'docs/cities/luoyang/app.mjs') or b'').decode('utf-8')
    refs = sorted(set(re.findall(r"['\"`]([^'\"`\s]+?\.glb)['\"`]", cd + '\n' + app)))
    for ref in refs:
        cand = ref.lstrip('./')
        for prefix in ('docs/cities/luoyang/', 'docs/', ''):
            b = show(rev, prefix + cand)
            if b is not None:
                names = glb_names(b)
                res['glbs'][prefix + cand] = {'sha256': hashlib.sha256(b).hexdigest(), 'waterNamed': names}
                break
        else:
            res['glbs'][ref] = {'sha256': None, 'waterNamed': None, 'unresolved': True}
    for line in cd.splitlines():
        if re.search(r'(水系|河渠|水道|古水|洛河|渠)', line):
            res['waterSentencesCityData'].append(line.strip()[:200])
    res['summary'] = {
        'glbReferenced': len(res['glbs']),
        'glbUnresolved': sum(1 for v in res['glbs'].values() if v.get('unresolved')),
        'glbWithWaterNames': sorted(k for k, v in res['glbs'].items() if v['waterNamed']),
        'glbWithRiverCanalNames': sorted(k for k, v in res['glbs'].items() if v['waterNamed'] and any(RIVER.search(n) for n in v['waterNamed'])),
        'appLoadsEvidenceGeometry': 'evidence-geometry' in app,
    }
    return res

a, b = scan(BASE), scan(NEW)
diff = {
    'inputsChanged': {p: [a['inputs'][p], b['inputs'][p]] for p in INPUTS if a['inputs'][p] != b['inputs'][p]},
    'glbAdded': sorted(set(b['glbs']) - set(a['glbs'])),
    'glbRemoved': sorted(set(a['glbs']) - set(b['glbs'])),
    'waterNamedGlbAdded': sorted(set(b['summary']['glbWithWaterNames']) - set(a['summary']['glbWithWaterNames'])),
    'riverCanalGlbAdded': sorted(set(b['summary']['glbWithRiverCanalNames']) - set(a['summary']['glbWithRiverCanalNames'])),
    'waterSentencesAdded': [s for s in b['waterSentencesCityData'] if s not in a['waterSentencesCityData']],
    'waterSentencesRemoved': [s for s in a['waterSentencesCityData'] if s not in b['waterSentencesCityData']],
}
json.dump({'base': a, 'new': b, 'diff': diff}, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps({'base': a['summary'], 'new': b['summary'], 'diff': diff}, ensure_ascii=False, indent=1))
