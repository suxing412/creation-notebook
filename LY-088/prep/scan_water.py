# LY-088 prep measurement: read-only scan of the bce3211 Luoyang city inputs.
# Usage: python -I scan_water.py <lab_repo> <ly001_dir> <out_json>
# Reads only git blob bytes (git show bce3211:path) so results do not depend on CRLF checkout.
import sys, json, hashlib, subprocess, struct, re, csv, io

LAB, LY001, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
REV = 'bce3211f818ee5a8bef1773539da70695ba37b17'
WATER = re.compile(r'(water|river|canal|channel|moat|stream|pond|lake|drain|ditch|水|渠|河|池|壍|濠|沟|溝|漕)', re.I)

def blob(path):
    return subprocess.run(['git', '-C', LAB, 'show', f'{REV}:{path}'], capture_output=True, check=True).stdout

def wt(path):
    with open(f'{LAB}/{path}', 'rb') as f:
        return f.read()

def sha(b):
    return hashlib.sha256(b).hexdigest()

def glb_json(b):
    magic, ver, length = struct.unpack_from('<4sII', b, 0)
    assert magic == b'glTF', 'not glb'
    clen, ctype = struct.unpack_from('<II', b, 12)
    return json.loads(b[20:20 + clen].decode('utf-8'))

res = {'rev': REV, 'inputs': {}, 'glb_scan': {}, 'evidence_geometry': {}, 'checks': {}}

# 1. Hash key inputs as git blob (LF, what the site serves) and working tree (CRLF checkout)
paths = [
    'docs/cities/luoyang/data/evidence/evidence-geometry.json',
    'docs/cities/luoyang/data/evidence/stage-contract.json',
    'docs/cities/luoyang/research/2026-11-03/city-milestones.json',
    'docs/cities/luoyang/p-luoyang.asset.json',
    'docs/cities/luoyang/city-data.mjs',
    'docs/cities/luoyang/app.mjs',
    'docs/cities/luoyang/index.html',
    'docs/cities/luoyang/v1/index.html',
    'docs/cities/luoyang/v1/boot.mjs',
    'docs/cities/luoyang/v1/evidence-view.mjs',
    'docs/cities/luoyang/v1/resource-url.mjs',
    'docs/cities/luoyang/v1/c01-layer.mjs',
    'docs/cities/luoyang/progress-assets/yong-city-v1/source.json',
    'docs/library/models/m-luoyang-palace-waterway-interface/m-luoyang-palace-waterway-interface.asset.json',
    'docs/library/models/m-luoyang-palace-waterway-interface/files/palace-waterway-interface-near.glb',
    'docs/library/models/m-luoyang-palace-waterway-interface/files/palace-waterway-interface-mid.glb',
    'docs/library/models/m-luoyang-palace-waterway-interface/files/palace-waterway-interface-far.glb',
    'docs/library/models/m-luoyang-palace-waterway-interface/files/palace-waterway-interface-inspection-near.glb',
]
for p in paths:
    b = blob(p)
    try:
        w = wt(p)
    except FileNotFoundError:
        w = None
    res['inputs'][p] = {'blobSha256': sha(b), 'bytes': len(b), 'worktreeSha256': sha(w) if w is not None else None,
                        'crlfDiffers': (w is not None and sha(w) != sha(b))}

# 2. Water-named nodes/meshes/materials in every GLB the city entry loads (LY-001 city-nodes.csv)
rows = list(csv.DictReader(open(f'{LY001}/qa/city-nodes.csv', encoding='utf-8')))
loaded = {}
for r in rows:
    if r['state'].startswith('已入城'):
        for k in ('farPath', 'nearPath'):
            if r.get(k):
                loaded[r[k]] = r['nodeId']
glb_rows = list(csv.DictReader(open(f'{LY001}/qa/glb-files.csv', encoding='utf-8')))
for g in glb_rows:
    if g['class'].startswith('已入城') or g['class'].startswith('隐藏试放') or 'waterway' in g['path']:
        loaded.setdefault(g['path'], g['class'])
for p, owner in sorted(loaded.items()):
    b = blob('docs/' + p)
    j = glb_json(b)
    names = []
    for coll in ('nodes', 'meshes', 'materials'):
        for i, o in enumerate(j.get(coll, [])):
            n = o.get('name', '')
            if WATER.search(n):
                names.append(f'{coll}[{i}]={n}')
        # extras may carry semantic labels
    ex = json.dumps([o.get('extras') for c in ('nodes', 'meshes', 'materials') for o in j.get(c, []) if o.get('extras')], ensure_ascii=False)
    exhits = sorted(set(m.group(0) for m in WATER.finditer(ex)))
    res['glb_scan'][p] = {'owner': owner, 'sha256': sha(b), 'nodes': len(j.get('nodes', [])),
                          'meshes': len(j.get('meshes', [])), 'materials': len(j.get('materials', [])),
                          'waterNamedObjects': names, 'waterTermsInExtras': exhits}

# 3. Evidence geometry: water features and their placement
eg = json.loads(blob('docs/cities/luoyang/data/evidence/evidence-geometry.json'))
feats = eg['features']
wf = [f for f in feats if WATER.search(json.dumps({k: f.get(k) for k in ('id', 'name', 'kind')}, ensure_ascii=False))]
res['evidence_geometry'] = {
    'features': len(feats),
    'waterFeatures': [{k: f.get(k) for k in ('id', 'name', 'kind', 'evidence_class', 'geometry_status', 'placement_mode', 'representation', 'source_ids')} | {'geometryIsNull': f.get('geometry') is None} for f in wf],
    'sourceRegistryWater': {k: v for k, v in eg['source_registry'].items() if 'huang' in k},
}

# 4. Checks
cd = blob('docs/cities/luoyang/city-data.mjs').decode('utf-8')
ev = blob('docs/cities/luoyang/v1/evidence-view.mjs').decode('utf-8')
app = blob('docs/cities/luoyang/app.mjs').decode('utf-8')
egsha = res['inputs']['docs/cities/luoyang/data/evidence/evidence-geometry.json']
m = re.search(r'"path": "data/evidence/evidence-geometry.json",\s*"sha256": "([0-9a-f]{64})"', cd)
res['checks'] = {
    'cityDataProvenanceSha_evidenceGeometry': m.group(1) if m else None,
    'provenanceMatchesBlob': bool(m and m.group(1) == egsha['blobSha256']),
    'provenanceMatchesCRLFWorktree': bool(m and m.group(1) == egsha['worktreeSha256']),
    'evidenceViewPinsBlobSha': egsha['blobSha256'] in ev,
    'appMjsLoadsEvidenceGeometry': 'evidence-geometry' in app,
    'appMjsMentionsWaterTextOnly': [l.strip()[:120] for l in app.splitlines() if '水系' in l],
    'cityDataReferencesWaterwayAsset': 'palace-waterway' in cd,
    'scannedGlbCount': len(res['glb_scan']),
    'enteredCityGlbCount': len([p for p, v in res['glb_scan'].items() if not str(v['owner']).startswith(('仅', '隐藏'))]),
    'hiddenTrialGlbCount': len([p for p, v in res['glb_scan'].items() if str(v['owner']).startswith('隐藏')]),
    'cardOnlyGlbCount': len([p for p, v in res['glb_scan'].items() if str(v['owner']).startswith('仅')]),
    'enteredCityGlbWithWaterNames': [p for p, v in res['glb_scan'].items() if v['waterNamedObjects'] and not str(v['owner']).startswith(('仅', '隐藏'))],
    'riverOrCanalMeshInEnteredCity': [p for p, v in res['glb_scan'].items() if not str(v['owner']).startswith(('仅', '隐藏')) and any(re.search(r'(river|canal|河|渠|waterway)', n, re.I) for n in v['waterNamedObjects'])],
}
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(res['checks'], ensure_ascii=False, indent=1))
print('glb scanned', len(res['glb_scan']))
