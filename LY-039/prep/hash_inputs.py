# LY-039 prep: hash every input (working-tree bytes and committed HEAD bytes) and
# write inputs.json. Read-only on the lab repo (uses `git show`, no write ops).
# python -I hash_inputs.py <lab_repo> <scratch_extract_dir> <out_json> [lab_ref=bce3211f818ee5a8bef1773539da70695ba37b17]
# Committed bytes are read from the pinned lab_ref, not from whatever HEAD the checkout is on.
import hashlib, json, subprocess, sys, os

lab, xdir, out = sys.argv[1:4]
REF = sys.argv[4] if len(sys.argv) > 4 else 'bce3211f818ee5a8bef1773539da70695ba37b17'
WP = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
L = 'docs/cities/luoyang/'
RB = 'modeling-lab/review-batches/2026-11-04-city-visible/'

def sh(b):
    return hashlib.sha256(b).hexdigest()

def head_bytes(rel):
    try:
        return subprocess.run(['git', '-C', lab, 'show', REF + ':' + rel], capture_output=True, check=True).stdout
    except subprocess.CalledProcessError:
        return None

rows = [
 # (rel, role, loadedInCity, loaderLocation)
 (RB + 'city-visible-web-handoff-v1-public.zip.part01', '196m road source container part 1/5 (concatenate 01..05 -> zip; road chunk chunks/northeast_C_access.glb)', False, 'not referenced by any docs/ code; archive only'),
 (RB + 'city-visible-web-handoff-v1-public.zip.part02', 'zip part 2/5', False, 'archive only'),
 (RB + 'city-visible-web-handoff-v1-public.zip.part03', 'zip part 3/5', False, 'archive only'),
 (RB + 'city-visible-web-handoff-v1-public.zip.part04', 'zip part 4/5', False, 'archive only'),
 (RB + 'city-visible-web-handoff-v1-public.zip.part05', 'zip part 5/5', False, 'archive only'),
 (RB + 'adapter/adapter.json', 'frontend adapter contract; asset visible-current-asset-northeast_C_access + node, chapter northeast_C_access, sourceNodeIds [C_NE_APPROACH_LOCAL]; deploymentStatus "not published"', False, 'not imported by app.mjs/city-renderer.mjs/v1; JSON does not run renderer'),
 (RB + 'adapter/qa/validation.json', 'readback bbox of northeast_C_access chunk (bytes_verified 413628)', False, 'QA only'),
 (RB + 'privacy-and-bytes.json', 'chunk + 3 embedded image SHA for northeast_C_access.glb', False, 'QA only'),
 (RB + 'intake.json', 'handoff intake; mother city-C032-entry-LOD0.blend SHA 1e8c4d2c... (not in repo)', False, 'QA only'),
 (RB + 'README.zh-CN.md', 'handoff rules: exclusive with legacy city layer; no rotation/recentre', False, 'doc'),
 (L + 'city-data.mjs', 'current city manifest; storage-main asset (L582-599), node (L3717-3730), chapter storage (L3984-3995); contains NO northeast/C_NE node', True, 'app.mjs:1 import manifest from ./city-data.mjs'),
 (L + 'progress-assets/granary-city-v1/granary-city-LOD0.glb', 'current in-city granary group incl. original_city_ground_preserved (12 tri slab z 0..0.2, south edge y=3647.469) = north end ground of the road', True, 'city-data.mjs L583 asset storage-main; loaded via chapter storage loadNodeIds (city-renderer.mjs:601, GLTFLoader parse :299)'),
 (L + 'progress-assets/granary-city-v1/granary-city-LOD1.glb', 'granary mid tier, not loaded', False, 'source.json only'),
 (L + 'progress-assets/granary-city-v1/granary-city-LOD2.glb', 'granary far tier, not loaded', False, 'source.json only'),
 (L + 'progress-assets/granary-city-v1/source.json', 'granary contract: externalRoadActivated false; NE road not connected', True, 'city-data.mjs sourceContract L599/L3729'),
 (L + 'progress-assets/granary-city-v1/README.md', 'granary readme: "东北对外道路仍未接通"', False, 'doc'),
 (L + 'assets/storage/storage-group-organized.glb', 'old storage group, still loaded only by v1 archive entry', True, 'v1/west-layer.mjs storage level (load key storage-calt, L30); NOT current entry'),
 (L + 'assets/city-wall/A/wall-01.glb', 'only other in-city node whose bbox overlaps road region; real geometry 123.5 m away', True, 'city-data.mjs L192 asset wall-A-wall-01 (initial)'),
 (L + 'p-luoyang.asset.json', 'project card: 2026-11-05 entry "不接入缺武库端支撑的东北C路径，外部道路仍待建"', False, 'project card, not runtime'),
 (L + 'data/west/storage-interface.json', 'old storage contract: unconnected true; externalRoad held at palace edge', False, 'v1 data'),
 (L + 'data/west/storage-precedents.json', 'region_taicang_B (2285.714,3673.469), region_wuku_B (2316.327,3500); gao2023 source rows', False, 'v1 data'),
 (L + 'data/west/road-preconstraints.json', 'road_northeast_gate_link_B classification hold_palace_interface; C corridor rules', False, 'v1 data'),
 (L + 'data/evidence/evidence-geometry.json', 'B schematic features: taicang/wuku points, north_palace_extent_gao2023_B (542 m from road), city_wall_schematic_B', False, 'evidence view (v1/evidence-adapter.mjs)'),
 ('docs/library/models/m-luoyang-wuku/m-luoyang-wuku.asset.json', 'armory card: not in city; independent file lacks outer ground', False, 'library card'),
 ('docs/library/models/m-luoyang-wuku/files/wuku-B-LOD0.glb', 'armory B v2.2 LOD0 (local origin, no city transform)', False, 'library only'),
 ('docs/library/models/m-luoyang-wuku/files/wuku-B-LOD1.glb', 'armory B LOD1', False, 'library only'),
 ('docs/library/models/m-luoyang-wuku/files/wuku-B-LOD2.glb', 'armory B LOD2', False, 'library only'),
 ('docs/library/models/m-luoyang-wuku/files/wuku-A-LOD0.glb', 'armory A v2 LOD0', False, 'library only'),
 ('lab/data/assets.json', 'site asset summary (m-storage-functional, m-luoyang-wuku)', False, 'site build data'),
]
res = {'labHead': subprocess.run(['git', '-C', lab, 'rev-parse', REF], capture_output=True, text=True).stdout.strip(),
       'labCheckoutHead': subprocess.run(['git', '-C', lab, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip(),
       'note': 'sha256Worktree = bytes on disk (Windows checkout, may be CRLF for text); sha256Commit = git show <labHead>:path bytes. Bind GLB by either (identical for binaries); bind text by sha256Commit.',
       'inputs': []}
for rel, role, loaded, where in rows:
    p = os.path.join(lab, rel)
    wb = open(p, 'rb').read() if os.path.exists(p) else None
    hb = head_bytes(rel)
    res['inputs'].append({'path': rel, 'role': role, 'bytes': None if wb is None else len(wb),
                          'sha256Worktree': None if wb is None else sh(wb), 'sha256Commit': None if hb is None else sh(hb),
                          'loadedInCurrentCity': loaded, 'loaderLocation': where})
# concatenated zip + extracted members (scratch, derived)
parts = b''.join(open(os.path.join(lab, RB + 'city-visible-web-handoff-v1-public.zip.part0%d' % i), 'rb').read() for i in range(1, 6))
res['derived'] = [{'path': '(concat part01..05)/city-visible-web-handoff-v1-public.zip', 'bytes': len(parts), 'sha256': sh(parts)}]
for m, role in [('chunks/northeast_C_access.glb', 'THE existing ~196 m C_NE_APPROACH_LOCAL road (32 tri, 1 node, material REUSED_C_earth.003); expected SHA 58f2f58a... per adapter/privacy-and-bytes'),
                ('chunks/granary_C_with_ground.glb', 'mother-blend granary chunk (differs from in-city granary-city-LOD0; same ground seam z)'),
                ('qa/source-node-manifest.json', 'source node C_NE_APPROACH_LOCAL world matrix (2285.714,3486,0), evaluated triangle SHA 0f806978...; C_WUKU_ISOLATED_SUPPORT_PATCH matrix (2316.327,3500,0) bbox x2307.327-2329.327 y3490-3510 z-0.4-0, tri SHA 1f46fa3e...'),
                ('chunks/wuku_C_with_support-01.glb', 'old trial armory support: node C_WUKU_ISOLATED_SUPPORT_PATCH (12 tri, top z 0.000, south edge y=3490) + wuku B static earth/timber; meets road stub cap y=3490 flush (out/bind-oldpatch.json); LY-036 input, not LY-039 property'),
                ('chunks/wuku_C_with_support-02.glb', 'wuku B static tile (roof) of the same trial group; not needed for the seam')]:
    b = open(os.path.join(xdir, m), 'rb').read()
    res['derived'].append({'path': 'zip:' + m, 'bytes': len(b), 'sha256': sh(b), 'role': role,
                           'loadedInCurrentCity': False})
wprows = [
 ('LY-003/tables/admission.json', 'row 东北接路（LY-039）: 宫墙条件未决（不是放行）; allowed only as rollback-able C local package inside NE-C-SCREEN'),
 ('LY-003/tables/hold-zones.json', '9 hold zones (base feature + buffer) used by ne_screen_check.py'),
 ('LY-003/qa/ne-checks.json', 'NE-C-SCREEN rule and granary margins; says C_NE_APPROACH_LOCAL not found in bce3211 (it is, inside the committed zip parts) and asks LY-039 to recheck'),
 ('LY-006/registry/ports.json', 'ports ne-approach:start (2285.714,0.2,-3647.469) and ne-approach:end-E (2317.827,0.0,-3487.25, fwd +X); tolerance pos 0.005 / elev 0.002; storage-site:forecourt-north, wuku-B:outer-arrival, wuku-B:forecourt-side declared without values'),
 ('LY-006/registry/zones.json', 'S-NE-ROAD write zones LY-039:write:001/002 (road +0.5 m)'),
 ('LY-006/registry/seats.json', 'LY-039 seat: owns source object C_NE_APPROACH_LOCAL (mode keep), no city nodes, site owner LY-040'),
 ('LY-006/qa/chunks/northeast_C_access.glb', 'LY-006 copy of the road chunk (must equal 58f2f58a)'),
 ('LY-009/board/locks.json', 'LOCK-NE-196C: 不可再造、不可延成东北主干路；LY-039 只重绑定'),
]
res['workpackInputs'] = []
for rel, role in wprows:
    p = os.path.join(WP, rel)
    b = open(p, 'rb').read() if os.path.exists(p) else None
    res['workpackInputs'].append({'path': 'workpacks/' + rel, 'role': role, 'bytes': None if b is None else len(b), 'sha256': None if b is None else sh(b), 'loadedInCurrentCity': False, 'loaderLocation': 'workpack contract (read-only)'})
res['missing'] = [
 {'item': 'city-C032-entry-LOD0.blend (mother, SHA 1e8c4d2ce19827bb8ab5ff24a662fd4f3909aa5c6074fc9a90623a103b73b01b)', 'use': 'native source of C_NE_APPROACH_LOCAL object, modifiers/parameters, original end-cap intent', 'rebuildFromGLB': 'yes for geometry: 32-tri strip fully recoverable from chunk (18 unique verts, out/glb-raw-check.json); generator params and original end-cap intent not recoverable'},
 {'item': '东北长路预检 (NE long-road precheck)', 'use': 'listed as existing input in TASKPOOL LY-039/040; not found in lab bce3211, origin/main, origin/luoyang-content, nor in any workpack (LY-084 prep reports the same)', 'rebuildFromGLB': 'no; it is an analysis report. Coordinator must supply it or declare it nonexistent'},
 {'item': 'LY-034 delivery: storage-site:forecourt-north:road-end values', 'use': 'north end binds to this port; LY-006 declared it without position', 'rebuildFromGLB': 'no (port is a contract); the geometry side is already measured flush'},
 {'item': 'LY-036 delivery: wuku-B:outer-arrival:ground (selected support piece + SHA)', 'use': 'south stub cap y=3490 must meet it; old trial patch meets it today but is not in city and LY-036 may change it', 'rebuildFromGLB': 'old patch yes (12-tri box in wuku_C_with_support-01.glb); the selected new piece no'},
 {'item': 'LY-037 delivery: wuku-B:forecourt-side:ground', 'use': 'consumer seam listed by LY-006 for LY-039', 'rebuildFromGLB': 'no'},
 {'item': 'LY-006 port for the stub north cap (x 2314.827-2317.827, y 3490, top 0.000, facing north)', 'use': 'the face that actually meets the armory support; registry v1 only froze end-E (east face x=2317.827, which faces open void)', 'rebuildFromGLB': 'values yes (measured here); the frozen port record must come from LY-006'},
 {'item': 'LY-008 checker, LY-010 region admission decision', 'use': 'official checker entry and whether the NE region is released', 'rebuildFromGLB': 'no'},
]
json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok', len(res['inputs']))
