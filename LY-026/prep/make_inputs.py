"""LY-026 prep: write inputs.json (path, SHA256, city-loaded?, loader code location). Read-only on inputs."""
import json, hashlib
from pathlib import Path

LAB = Path('D:/GitHub/creation-notebook-lab')
WP = Path('D:/GitHub/creation-notebook-workpacks')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


W = 'docs/model-library/well-study/'
items = []
for v in ['A-LOD0', 'A-LOD1', 'B-LOD0', 'B-LOD1']:
    p = W + 'assets/well-%s.glb' % v
    items.append({'id': 'well-' + v, 'path': p, 'sha256': sha(LAB / p), 'bytes': (LAB / p).stat().st_size,
                  'kind': 'GLB (public library)', 'role': 'operating parts under test', 'loadedInCity': False,
                  'loadedBy': ['docs/model-library/well-study/viewer.js:3 (template assets/well-{v}-LOD{lod}.glb)',
                               'docs/model-library/well-study/index.html (links)']})
for f, role in [('m-well-family.asset.json', 'asset card (status 待审)'), ('contract.json', 'metric/origin/opening contract'),
                ('README.md', 'scope and limits'), ('inputs/reference-contract.json', 'evidence contract'),
                ('qa/local-contact-checks.json', 'source joint/envelope QA'),
                ('qa/local-boolean-intersections.json', 'source selected-pair boolean QA (LOD0 only)'),
                ('qa/actual-GLB.json', 'source GLB readback'), ('qa/native-check.json', 'source native check'),
                ('qa/static-web-check.json', 'names native SHA'), ('viewer.js', 'library viewer'), ('index.html', 'library page')]:
    items.append({'id': 'well-study/' + f, 'path': W + f, 'sha256': sha(LAB / (W + f)), 'kind': 'doc/QA', 'role': role,
                  'loadedInCity': False, 'loadedBy': []})
cv = 'modeling-lab/review-batches/2026-11-04-city-visible/'
for i in range(1, 6):
    p = cv + 'city-visible-web-handoff-v1-public.zip.part0%d' % i
    items.append({'id': 'city-visible-part0%d' % i, 'path': p, 'sha256': sha(LAB / p), 'kind': 'ZIP part (not a GLB)',
                  'role': 'container of the mother-scene trial chunk', 'loadedInCity': False, 'loadedBy': []})
items.append({'id': 'city-visible-zip', 'path': cv + 'city-visible-web-handoff-v1-public.zip (in-memory concat only; never written)',
              'sha256': '5895ef23a684a343271183dce1e92e112fb49bba9e03e4372023d1247bb50b69', 'kind': 'ZIP',
              'loadedInCity': False, 'loadedBy': []})
items.append({'id': 'chunk-market_frontage_well_routes', 'path': 'zip:chunks/market_frontage_well_routes.glb',
              'sha256': '0193ebc0cfe200292defd595ff4f4011b2b2d05388d4f53e7b4c3a19a255b4c5', 'bytes': 3695576,
              'kind': 'GLB (mother-scene visible chunk, tier C)',
              'role': '井入母场景试放: well A-LOD0 minus apron at Zup (196.286,1952.184,0.200) + C_market_ground_well_A (hole r=0.59)',
              'loadedInCity': False, 'loadedBy': [],
              'note': 'adapter node visible-current-node-market_frontage_well_routes initial:false; no docs code references chunks/'})
for f, role in [('adapter/adapter.json', 'chunk adapter (node/asset ids, bounds, sourceNodeIds)'),
                ('README.zh-CN.md', 'handoff scope'), ('restore-city-visible.py', 'part SHAs (not executed: it writes into the repo)')]:
    items.append({'id': 'city-visible/' + f, 'path': cv + f, 'sha256': sha(LAB / (cv + f)), 'kind': 'doc', 'role': role,
                  'loadedInCity': False, 'loadedBy': []})
C = 'docs/cities/luoyang/'
items.append({'id': 'market-main', 'path': C + 'assets/market/market-cluster.glb', 'sha256': sha(LAB / (C + 'assets/market/market-cluster.glb')),
              'kind': 'GLB (city)', 'loadedInCity': True,
              'role': 'current site market; solid sample_ground (same 60x44 m rectangle as trial ground, top y=0.2, 24 verts, no hole; nearest vertex 19.2 m from well axis); no well',
              'loadedBy': ['docs/cities/luoyang/city-data.mjs:510-513 (id market-main)',
                           'docs/cities/luoyang/v1/west-layer.mjs:33 (level market: environmentUrl)']})
for f, ln in [('assets/market/N2-replacement.glb', ['city-data.mjs:563', 'v1/west-layer.mjs:33', 'v1/west-layer.mjs:36']),
              ('assets/market/corridor-6m-market-link.glb', ['v1/west-layer.mjs:32', 'v1/west-layer.mjs:33']),
              ('assets/road-junction/joined-route-terrain.glb', ['v1/west-layer.mjs:32', 'v1/west-layer.mjs:33'])]:
    items.append({'id': f.split('/')[-1], 'path': C + f, 'sha256': sha(LAB / (C + f)), 'kind': 'GLB (city)',
                  'role': 'neighbour context for site negative test', 'loadedInCity': True,
                  'loadedBy': ['docs/cities/luoyang/' + x for x in ln]})
for f, role, loaded in [('city-data.mjs', 'city asset list (shared; LY-100 only)', True),
                        ('v1/west-layer.mjs', 'market level loader', True),
                        ('data/west/market-precedents.json', 'market evidence; avoid list contains 因名市井而强加水井', False),
                        ('p-luoyang.asset.json', 'project card (shared; LY-100 only)', False)]:
    items.append({'id': f, 'path': C + f, 'sha256': sha(LAB / (C + f)), 'kind': 'code/data', 'role': role,
                  'loadedInCity': loaded, 'loadedBy': []})
for f in ['TASKPOOL.md', 'taskboard.json', 'LY-001/qa/snapshot-ledger.json', 'LY-001/source/glbinfo.py']:
    items.append({'id': 'workpacks/' + f, 'path': str(WP / f), 'sha256': sha(WP / f), 'kind': 'workpack',
                  'role': 'task text / LY-001 pre-freeze snapshot / reused GLB reader', 'loadedInCity': False, 'loadedBy': []})
out = {
    'seat': 'LY-026', 'baseline': 'bce3211f818ee5a8bef1773539da70695ba37b17', 'labRepo': str(LAB),
    'coordinateNote': 'well-local origin = well-mouth centre at exterior ground, Blender Z up; GLB Y up. City trial offset Zup '
                      '(196.28599548339844, 1952.1839599609375, 0.20000000298023224), rotation/scale identity.',
    'inputs': items,
    'missing': [
        {'what': 'well-study source/ (build.py, check.py, check-contacts.py, check-local-booleans.py) and manifest.json',
         'use': 'regenerate parts with original parameters/seed 0; re-run source QA', 'rebuildFromGLB': 'yes for the small operating parts, must be labelled 从GLB重建'},
        {'what': 'native .blend of the well family (native SHA ba15e0dd862933fdc46bd73aec3231fad87f88f97c69816592318609ddd6fac8 per qa/static-web-check.json)',
         'use': 'native-vs-GLB oriented-triangle parity; hidden variant collections', 'rebuildFromGLB': 'partially (no hidden collection / modifier state)'},
        {'what': 'mother scene city-C032-entry-LOD0.blend (1e8c4d2ce19827bb8ab5ff24a662fd4f3909aa5c6074fc9a90623a103b73b01b)',
         'use': 'exact trial placement source and re-export', 'rebuildFromGLB': 'chunk GLB suffices for measurement, not for re-exporting the scene'},
        {'what': 'G package: LY-001/002/005/006/007/008/009/010 frozen outputs',
         'use': 'port IDs, ownership of wheel/rope/container nodes, LOD rules, checker command, admission', 'rebuildFromGLB': 'no'},
        {'what': 'LY-025 atomic well + cut-ground package', 'use': 'exact ground/hole/placement LY-026 must test against', 'rebuildFromGLB': 'no'},
        {'what': 'original plates (灵宝张湾 1975, 刘家渠, 烧沟) and museum images actually viewed',
         'use': 'check pulley/axle/cheek form before any revision', 'rebuildFromGLB': 'no'}]}
json.dump(out, open('D:/GitHub/creation-notebook-workpacks/LY-026/prep/inputs.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(items))
