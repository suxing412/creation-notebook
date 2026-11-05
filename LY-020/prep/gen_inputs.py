"""LY-020 prep: hash every input and record whether/where the city scene loads it. Read-only on the lab repo.
python -I gen_inputs.py <lab_root> <out inputs.json>"""
import sys, json, hashlib, os, subprocess

LAB, OUT = sys.argv[1], sys.argv[2]
L = 'docs/cities/luoyang/'


def sha(rel):
    p = os.path.join(LAB, rel)
    return hashlib.sha256(open(p, 'rb').read()).hexdigest(), os.path.getsize(p)


head = subprocess.run(['git', '-C', LAB, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
dirty = subprocess.run(['git', '-C', LAB, 'status', '--porcelain', '--', 'docs/cities/luoyang', 'docs/library/models/m-luoyang-earthwall-family'], capture_output=True, text=True).stdout.strip()
MAIN = {'loaded': True, 'how': 'main city index.html -> app.mjs -> city-renderer.mjs (manifest from city-data.mjs); chapter "walls", node initial=true -> first screen',
        'code': ['docs/cities/luoyang/city-data.mjs:171-428 (assetRecords)', 'docs/cities/luoyang/city-data.mjs:3203-3550 (nodes, position [0,0,0])',
                 'docs/cities/luoyang/city-renderer.mjs:221 (initial filter)', 'docs/cities/luoyang/city-renderer.mjs:294 (fetch GLB)']}
V1A = 'also v1 archive: docs/cities/luoyang/v1/wall-layer.mjs:20-21 (?wall=A, expects 13 roots, checks SHA-256)'
items = []
for n in ['A/wall-00', 'A/wall-01', 'A/wall-02', 'A/wall-03', 'A/wall-04', 'A/wall-05', 'A/wall-06', 'A/wall-07', 'A/wall-10', 'A/wall-11',
          'direct/wall-08', 'direct/wall-09', 'direct/gate-body-only']:
    rel = L + 'assets/city-wall/' + n + '.glb'
    h, b = sha(rel)
    items.append({'role': 'current city wall segment (sample A/direct)' if 'gate' not in n else 'Guangyang gate body on direct walls (neighbour, not LY-020)',
                  'path': rel, 'sha256': h, 'bytes': b, 'native': None, 'nativeNote': 'no .blend/generator in repo; geometry fully recoverable from GLB (pure lofts)' if n.startswith('A/') else 'no .blend/generator in repo',
                  'loadedInCity': True, 'loadCode': MAIN['code'] + [V1A], 'ownerNote': 'read-only input; LY-020 must not modify' + ('' if 'gate' not in n else '; Guangyang direct transition')})
for i in range(12):
    rel = L + 'assets/city-wall/B/wall-%02d.glb' % i
    h, b = sha(rel)
    items.append({'role': 'exclusive alternative wall sample B (top 8 / base 10 / top width 6.5)', 'path': rel, 'sha256': h, 'bytes': b,
                  'loadedInCity': False, 'loadCode': ['v1 archive only: docs/cities/luoyang/v1/wall-layer.mjs:20-21 (?wall=B, 12 roots); not in city-data.mjs']})
for g, pos in [('network-ground-stitched', [0, 0, 0]), ('retained', [0, 0, 0]), ('south', [0, 0, 0]), ('D08', [580, 0, -960])]:
    rel = L + 'assets/ground-atomic/' + g + '.glb'
    h, b = sha(rel)
    items.append({'role': 'city ground (atomic C ground)', 'path': rel, 'sha256': h, 'bytes': b, 'nodePosition': pos,
                  'loadedInCity': True, 'loadCode': ['docs/cities/luoyang/city-data.mjs:431-510 (assetRecords)', 'docs/cities/luoyang/city-data.mjs:3555-3660 (nodes, chapter "terrain", initial=false)',
                                                    'docs/cities/luoyang/city-renderer.mjs:597-611 (chapter open loads loadNodeIds)'],
                  'note': 'NOT on first screen: only after opening chapter terrain'})
for rel, role, load, code in [
    (L + 'data/west/city-wall-interface.json', 'wall runtime contract (A 13 roots / B 12 roots, SHA list)', True, ['v1/wall-layer.mjs:20 fetch', 'city-data.mjs sourceContract field (metadata only)']),
    (L + 'data/west/city-wall-constraints.json', 'wall C-parameter constraints + gate C projections (B points unchanged)', False, ['linked as a document from v1/wall-layer.mjs:13; read by measure_walls.py for gate points']),
    (L + 'data/west/city-wall-interface-original.json', 'original wall interface (pre-direct)', False, []),
    (L + 'data/west/ground-atomic-contract.json', 'ground atomic contract (D08 translation 580,0,-960)', False, ['metadata']),
    (L + 'city-data.mjs', 'city manifest (shared file, LY-100 only)', True, ['app.mjs:1 import']),
    (L + 'city-renderer.mjs', 'renderer', True, ['app.mjs:177 dynamic import']),
    (L + 'v1/wall-layer.mjs', 'v1 archive wall sample switch', True, ['v1/west-layer.mjs:6,61']),
    (L + 'p-luoyang.asset.json', 'project card (shared file, LY-100 only)', False, ['site build']),
    ('docs/library/models/m-luoyang-earthwall-family/m-luoyang-earthwall-family.asset.json', 'earthwall family card', False, ['library only']),
    (L + 'progress-assets/yong-city-v1/yong-apron-LOD0.glb', 'Yong gate apron + wing walls filling the Yong 32 m gap (reserved owner, neighbour)', True, ['city-data.mjs yong-gate-apron / node yong-gate-interface (matrix, initial=true)']),
    ('docs/library/models/m-luoyang-yong-gate/files/yong-Y-LOD0.glb', 'Yong gate body (reserved owner, neighbour)', True, ['city-data.mjs yong-gate-near / node yong-gate-body']),
]:
    h, b = sha(rel)
    items.append({'role': role, 'path': rel, 'sha256': h, 'bytes': b, 'loadedInCity': load, 'loadCode': code})
for f in ['A-LOD0', 'A-LOD1', 'A-LOD2', 'B-LOD0', 'B-LOD1', 'B-LOD2', 'C-LOD0', 'C-LOD1', 'C-LOD2']:
    rel = 'docs/library/models/m-luoyang-earthwall-family/files/earthwall-' + f + '.glb'
    h, b = sha(rel)
    items.append({'role': 'earthwall family module (library; C matches city A section 8/5.6/6.03; A/B are 14/10/8 and match neither city sample)', 'path': rel, 'sha256': h, 'bytes': b,
                  'loadedInCity': False, 'loadCode': ['none: not referenced by city-data.mjs, v1, or any data/*.json (grep earthwall in docs/cities/luoyang -> no hit)']})
for f in ['westwall10-LOD1', 'westwall10-LOD2']:
    rel = 'docs/library/models/m-luoyang-earthwall-family/files/' + f + '.glb'
    h, b = sha(rel)
    items.append({'role': 'west wall 10 mid/far tiers (near tier withheld >12MB)', 'path': rel, 'sha256': h, 'bytes': b, 'loadedInCity': False, 'loadCode': []})
assets_json = 'lab/data/assets.json'
h, b = sha(assets_json)
items.append({'role': 'site build summary (working copy has local modification per LY-001 snapshot; hash is of working copy)', 'path': assets_json, 'sha256': h, 'bytes': b, 'loadedInCity': False, 'loadCode': []})
wp = 'D:/GitHub/creation-notebook-workpacks/'
for rel in ['LY-001/qa/snapshot-ledger.json', 'TASKPOOL.md', 'taskboard.json']:
    p = wp + rel
    items.append({'role': 'workpack input', 'path': 'workpacks/' + rel, 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest(), 'bytes': os.path.getsize(p)})
missing = [
    {'what': 'earthwall family native source (.blend / generator + parameters)', 'use': 'build a corner stub with the same rammed-layer undulation, UV and LOD rules as earthwall-C so the piece is a family member, not a look-alike',
     'rebuildFromGLB': 'partial: the C-LOD0/1/2 GLBs can be imported and the end profile (390/198/54 verts) cut and swept, but that is a derived C piece, not the original parametric source; must be declared "rebuilt from GLB"'},
    {'what': 'city-wall C01 segment generator (luoyang-west-connection workspace: wall_offset_from_B, gate_gap_width, corner_join parameters)', 'use': 'regenerate the Shangdong segment ends with the same rules instead of hand-placing a stub',
     'rebuildFromGLB': 'yes for geometry: A segments are pure trapezoid lofts (stations recovered exactly in measure-walls.json); parameters themselves (B offset rule) are not recoverable'},
    {'what': 'reusedContext sources route-corridor.glb / guangyang-C-form.glb / south14 connection-terrain.glb / south14-after.glb (city-wall-interface.json reusedContext, copiedIntoPackage=false)', 'use': 'only needed if a foot piece must meet the Guangyang approach terrain; not needed for Shangdong',
     'rebuildFromGLB': 'connection-terrain SHA equals ground-atomic/south.glb (4313826d...), so that one is present; the other three are not in the repo'},
    {'what': 'G package (LY-005 coordinate/port contract, LY-006 ownership, LY-007 material/LOD baseline, LY-008 checker, LY-010 admission)', 'use': 'port IDs for the Shangdong gap, ownership of the gate gap volume, LY_P01 material, official checker command', 'rebuildFromGLB': 'no'},
]
json.dump({'schema': 'LY-020/inputs-prep-1', 'lab': LAB, 'labHead': head, 'labCityDirty': dirty or 'clean', 'items': items, 'missing': missing}, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(items), 'items; head', head, 'dirty:', dirty or 'clean')
