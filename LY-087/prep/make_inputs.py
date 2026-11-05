# LY-087 prep: write inputs.json (path, sha256 of working-tree bytes and of committed bytes, city load status, loader location)
import os, json, hashlib, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
LAB = 'D:/GitHub/creation-notebook-lab'
WP = 'D:/GitHub/creation-notebook-workpacks'


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def commit_sha(rel):
    try:
        b = subprocess.run(['git', '-C', LAB, 'show', 'HEAD:' + rel], capture_output=True, check=True).stdout
        return hashlib.sha256(b).hexdigest()
    except Exception:
        return None


R = 'docs/cities/luoyang/city-renderer.mjs'
LOADER = f'{R}:221 (loadedIds = initial!==false), :286 loadAsset, :299 GLTFLoader.parseAsync, :309 excludeNodes, :595-605 focusChapter adds chapter.loadNodeIds'
items = [
    # in-city drainage carriers
    ('docs/cities/luoyang/assets/d08/TC03-LOD1-prototype.glb', 'city: 首屏默认加载 (far) for C02-020, C02-008, FROZEN-D08-NW, FROZEN-D08-NE', 'docs/cities/luoyang/city-data.mjs:62-63 asset courtyard-TC03; nodes :1440 :2238 :3120 :3162; ' + LOADER, 'contains architecture_C_drain_stone'),
    ('docs/cities/luoyang/assets/d08/TC03-LOD0-prototype.glb', 'city: near tier of courtyard-TC03 (focusCourtyard)', 'docs/cities/luoyang/city-data.mjs:82 nearPath; ' + LOADER, 'drain triangles identical to LOD1 (hash 2739cd13e8b5df72)'),
    ('docs/cities/luoyang/assets/c02v/TC03-2-LOD1-prototype.glb', 'city: 首屏默认加载 (far) for C02-003, C02-012', 'docs/cities/luoyang/city-data.mjs:142-143 asset courtyard-TC03-2; nodes :2028 :2406; ' + LOADER, 'contains architecture_C_drain_stone.001'),
    ('docs/cities/luoyang/assets/c02v/TC03-2-LOD0-prototype.glb', 'city: near tier of courtyard-TC03-2', 'docs/cities/luoyang/city-data.mjs:165 nearPath; ' + LOADER, 'drain triangles identical to LOD1 (hash b4b891d7470da637)'),
    # four atomic grounds
    ('docs/cities/luoyang/assets/ground-atomic/network-ground-stitched.glb', 'city: 按章加载 terrain chapter only (initial=false)', 'docs/cities/luoyang/city-data.mjs:431 asset, :3555 node; ' + LOADER, ''),
    ('docs/cities/luoyang/assets/ground-atomic/retained.glb', 'city: 按章加载 terrain chapter only', 'docs/cities/luoyang/city-data.mjs:451, :3582; ' + LOADER, ''),
    ('docs/cities/luoyang/assets/ground-atomic/south.glb', 'city: 按章加载 terrain chapter only', 'docs/cities/luoyang/city-data.mjs:471, :3609; ' + LOADER, ''),
    ('docs/cities/luoyang/assets/ground-atomic/D08.glb', 'city: 按章加载 terrain chapter only; node translation [580,0,-960]', 'docs/cities/luoyang/city-data.mjs:491, :3636; ' + LOADER, ''),
    ('docs/cities/luoyang/data/west/ground-atomic-contract.json', 'contract (not fetched by renderer)', 'sourceContract field in city-data.mjs:448/468/488/508', 'no drainage/fall fields'),
    # palace waterway three segments
    ('docs/library/models/m-luoyang-palace-waterway-interface/files/palace-waterway-interface-near.glb', 'library only, not loaded in city', 'none (0 refs in city-data.mjs/app.mjs)', ''),
    ('docs/library/models/m-luoyang-palace-waterway-interface/files/palace-waterway-interface-mid.glb', 'library only', 'none', ''),
    ('docs/library/models/m-luoyang-palace-waterway-interface/files/palace-waterway-interface-far.glb', 'library only', 'none', ''),
    ('docs/library/models/m-luoyang-palace-waterway-interface/files/palace-waterway-interface-inspection-near.glb', 'library only (modern teardown, not an ancient device)', 'none', 'segment nodes inner/shaft/outer'),
    ('docs/library/models/m-luoyang-palace-waterway-interface/m-luoyang-palace-waterway-interface.asset.json', 'asset card, status 待审, 未入城', 'p-luoyang.asset.json:187 inventory, :535 members', ''),
    # dependency candidates
    ('docs/library/models/m-luoyang-stable/files/A.glb', 'library only (LY-052 base)', 'none', ''),
    ('docs/library/models/m-luoyang-stable/files/B.glb', 'library only (LY-052 base)', 'none', ''),
    ('docs/library/models/m-luoyang-tile-kiln/files/kiln-A.glb', 'library only (LY-054 base)', 'none', ''),
    ('docs/library/models/m-luoyang-tile-kiln/files/kiln-B.glb', 'library only (LY-054 base)', 'none', ''),
    # city code and project data
    ('docs/cities/luoyang/city-data.mjs', 'city manifest', 'imported by app.mjs / city-renderer.mjs', 'worktree bytes are CRLF; bind commit bytes'),
    ('docs/cities/luoyang/city-renderer.mjs', 'renderer', 'no water/flow animation; pigmentFor :153 colours names matching water|river|渠|水', ''),
    ('docs/cities/luoyang/app.mjs', 'entry', ':312 research text says 古水系配准待补充', ''),
    ('docs/cities/luoyang/p-luoyang.asset.json', 'project card', 'read-only; LY-100 only', ''),
    ('docs/cities/luoyang/data/evidence/evidence-geometry.json', 'evidence view', 'v1/evidence-view.mjs', 'water features are B schematic/unplaced'),
]
out = {'seat': 'LY-087', 'baseline': 'bce3211f818ee5a8bef1773539da70695ba37b17', 'note': 'sha256 = working-tree bytes; commitSha256 = git show HEAD:path bytes (differ only for CRLF text files)', 'inputs': []}
for rel, status, where, note in items:
    p = LAB + '/' + rel
    out['inputs'].append({'path': rel, 'sha256': sha(p), 'commitSha256': commit_sha(rel), 'bytes': os.path.getsize(p),
                          'cityLoad': status, 'loadedBy': where, 'note': note})
ext = [
    (WP + '/LY-001/qa/city-data.dump.json', 'LY-001 delivered snapshot dump (node matrices, excludeNodes)'),
    (WP + '/LY-001/qa/glb-files.csv', 'LY-001 delivered GLB load-class ledger'),
    (WP + '/LY-002/tables/evidence-ledger.md', 'LY-002 delivered: E-H03 (水系未定位), E-R05 (辟雍北无水/未闭合), X15 (今洛河禁用)'),
    (WP + '/LY-005/port-schema.json', 'LY-005 delivered: port kinds ground/threshold/floor/wall-end/road-end (no drain kind; superseded for kinds by LY-006 port.schema v1)'),
    (WP + '/LY-006/registry/ports.json', 'LY-006 delivered registry v1: 214 ports incl. 5 kind=drain (C02-010:drip-outlet, stable:drain-outlet, kiln:front-drain, biyong:bank-outlet -> consumer LY-087; waterway:ends consumers=[]), all values null'),
    (WP + '/LY-006/registry/seats.json', 'LY-006 delivered: LY-087 site S-CITYGROUND (owner LY-090), role data+assembly, writeZones=[], produces=[], ownsCityNodes=[]'),
    (WP + '/LY-006/registry/ownership.json', 'LY-006 delivered: C02-020/003/008/012, FROZEN-D08-NW/NE cityNodes owner=null status=frozen'),
    (WP + '/LY-006/registry/seams.json', 'LY-006 delivered seams'),
    (WP + '/LY-006/registry/zones.json', 'LY-006 delivered zones'),
    (WP + '/LY-006/schemas/port.schema.json', 'LY-006 port schema v1: adds kind drain; no flowDir/invert/destState/admittedOutlet fields'),
    (WP + '/LY-006/status.json', 'LY-006 status 交付完成; openItem: LY-087 not dependent on LY-086 (waterway drain ports not wired)'),
    (WP + '/LY-003/tables/admission.json', 'LY-003 delivered: 宫墙水道 不可落位 (LY-086 local only, no world pose); no admitted water outlet anywhere'),
    (WP + '/LY-008/source/ly_check.py', 'LY-008 delivered checker (glb / lodset / package / privacy / official)'),
    (WP + '/LY-009/board/taskboard.v2.json', 'LY-009 delivered board v2: LY-087 status 待输入, pause PZ-06'),
    (WP + '/LY-005/coordinate-contract.json', 'LY-005 delivered coordinate/elevation contract'),
    (WP + '/LY-046/prep/prep-status.json', 'LY-046 prep draft (not frozen)'),
    (WP + '/LY-052/prep/prep-status.json', 'LY-052 prep draft (not frozen)'),
    (WP + '/LY-054/prep/prep-status.json', 'LY-054 prep draft (not frozen)'),
    (WP + '/LY-073/prep/prep-status.json', 'LY-073 prep draft (not frozen)'),
    (WP + '/LY-081/prep/prep-status.json', 'LY-081 prep draft (not frozen); has drift-cad338b re-run'),
    (WP + '/LY-086/prep/prep-status.json', 'LY-086 prep draft (not frozen); producer of waterway:ends:drain'),
    (WP + '/LY-087/prep/out/drift-cad338b-drain-scan.json', 'LY-087 drift scan: origin/main cad338b adds 0 drain-named nodes; 6 TC03 drain node blocks identical'),
    (WP + '/LY-073/prep/_extract/city-visible/chunks/biyong_C_relationship.glb', 'LY-073 extract of modeling-lab ZIP chunk (网页未接入)'),
]
out['workpackInputs'] = [{'path': p, 'sha256': sha(p), 'role': r} for p, r in ext]
out['notYetAvailable'] = ['LY-010 region/demo-court freeze (no directory)', 'LY-081 frozen network (prep only)',
                          'frozen LY-046/052/054/073 deliveries (registry drain port values null)', 'LY-086 waterway install (not a dependency, PZ-06)',
                          'LY-088 water-phase layer (prep only); LY-003 admits no water outlet']
out['drift'] = {'originMain': 'cad338ba683f7277aea098f45c8feb6c915a847c', 'localMain': '44c66da842eca5799d353e07ec1550b000b8855b (ancestor of bce3211, stale)',
                'note': 'baseline stays bce3211 until LY-001 re-snapshots; cad338b changes city-data.mjs (commit sha d8933a32...) but adds no drain geometry and leaves the 6 TC03 drain nodes identical'}
json.dump(out, open(os.path.join(HERE, 'inputs.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for i in out['inputs'] + out['workpackInputs']:
    print(i['sha256'][:8], i.get('commitSha256', '') and i['commitSha256'][:8], i['path'])
