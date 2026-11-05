# LY-045 prep: write inputs.json (path, SHA256, bytes, loaded in city?, loader code location). Read-only on lab.
# python -I make_inputs.py <lab_root> <out.json>
import sys, os, json, hashlib, subprocess

LAB, OUT = sys.argv[1], sys.argv[2]


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


R = 'docs/cities/luoyang/'
SCD = 'docs/library/models/m-luoyang-service-court/'
items = [
    # the reused 圈厕组 (primary input)
    (SCD + 'files/service-A-LOD0.glb', 'reuse: 圈厕关系 A LOD0 (9,456 tris; nodes static_tile/static_timber/static_earth)', False, 'not referenced by any docs/cities/luoyang *.mjs/*.json/*.html; only p-luoyang.asset.json:254 lists 圈厕关系 A as 已建模, note 未入城'),
    (SCD + 'files/service-A-LOD1.glb', 'reuse: LOD1 (1,656 tris)', False, 'not referenced'),
    (SCD + 'files/service-A-LOD2.glb', 'reuse: LOD2 (696 tris, no textures)', False, 'not referenced'),
    (SCD + 'm-luoyang-service-court.asset.json', 'asset card (status 待审; checks/limits text)', False, 'library card only; lab/data/assets.json aggregates it'),
    (SCD + 'cover.webp', 'card cover (CPU render of native model, per card note)', False, 'library only'),
    (SCD + 'shots/01.webp', 'card shot', False, 'library only'),
    (SCD + 'shots/02.webp', 'card shot', False, 'library only'),
    # candidate yard (LY-041 draft choice, not frozen)
    (R + 'assets/c02v/A2-LOD1-prototype.glb', 'C02-010 / C02-021 far prototype courtyard-A2', True, 'city-data.mjs:88-108 asset courtyard-A2 path; excludeNodes site_lot/site_neutral_lane/designed_hardpacked_activity_ground culled at city-renderer.mjs:309, all must match :346'),
    (R + 'assets/c02v/A2-LOD0-prototype.glb', 'courtyard-A2 near prototype (measured yard geometry)', True, 'city-data.mjs:109-111 nearPath; only the focused node goes near, city-renderer.mjs:416; focusCourtyard :616'),
    (R + 'data/far44/instances-calt.json', '44-yard matrices (C02-010 T=(531,0,-818.45); C02-021 rotY 270 T=(717.45,0,-893.64308))', True, 'sourceContract of city-data nodes C02-010 (city-data.mjs:2322) and C02-021 (:1482)'),
    (R + 'data/c02v/layout.json', 'lots[].localRoutes gate_to_main / yard_to_side (route corridors kept free)', False, 'data file; routes not drawn by the renderer for this yard (read by prep only)'),
    # real ground under the pen / hole
    (R + 'assets/ground-atomic/south.glb', 'ground-south: single node single_closed_terrain_after, 96,796 tris, slab y 0.0/0.2; real ground of C02-010 and of the pen floor', True, 'asset city-data.mjs:471; node :3609 chapter terrain initial:false -> not in the default load set (city-renderer.mjs:221)'),
    (R + 'assets/ground-atomic/retained.glb', 'ground-retained: real ground of C02-021 (alternative yard), 21,192 tris, coarse (13-38 m edges at the hole)', True, 'asset city-data.mjs:451; node :3582 initial:false'),
    (R + 'assets/ground-atomic/network-ground-stitched.glb', 'ground-network (0 cells in either candidate lot)', True, 'asset city-data.mjs:431; node :3555 initial:false'),
    (R + 'assets/ground-atomic/D08.glb', 'ground-D08 (0 cells in either candidate lot)', True, 'asset city-data.mjs:491; node :3636 position [580,0,-960] initial:false'),
    (R + 'data/west/ground-atomic-contract.json', 'ground composition contract', False, 'sourceContract of the four ground assets'),
    # shared files (read only, LY-100 writes)
    (R + 'city-data.mjs', 'shared manifest (read only)', True, 'imported by app.mjs'),
    (R + 'city-renderer.mjs', 'renderer: initial set :221, excludeNodes :309/:346, near tier :416, focusCourtyard :616', True, 'imported by app.mjs'),
    (R + 'app.mjs', 'city app entry', True, 'index.html'),
    (R + 'index.html', 'city page', True, '-'),
    (R + 'p-luoyang.asset.json', 'project card: 圈厕关系 A entry at :254 (已建模, 未入城)', False, 'library/project card'),
    # unused but related cards (checked, not reused)
    ('docs/library/models/m-luoyang-household-service/files/service-enclosure-LOD0.glb', 'low-wall service enclosure; card says it contains no toilet system -> not part of this package', False, 'not referenced'),
]
rows = []
for rel, role, loaded, where in items:
    p = os.path.join(LAB, rel)
    rows.append({'path': rel, 'sha256': sha(p), 'bytes': os.path.getsize(p), 'role': role, 'loadedInCity': loaded, 'loaderCode': where})
head = subprocess.run(['git', '-C', LAB, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
blob = subprocess.run(['git', '-C', LAB, 'show', 'HEAD:lab/data/assets.json'], capture_output=True).stdout
out = {
    'seat': 'LY-045', 'labHead': head,
    'note': 'all docs/ inputs equal HEAD; lab/data/assets.json working tree has unrelated uncommitted edits (HEAD blob sha below)',
    'labDataAssetsJson_HEAD_blob_sha256': hashlib.sha256(blob).hexdigest(),
    'inputs': rows,
    'privateSourcesMissing': [
        {'what': '圈厕关系 A native source (.blend / generator / batch source ZIP)', 'use': 'only if service-A geometry had to change (it must not; package reuses the GLB unchanged) and to re-render native CPU shots', 'rebuildFromGLB': 'yes for geometry (3 static nodes, no animation); native parameters not recoverable'},
        {'what': 'card QA package behind 有限门口、孔口和台阶检查', 'use': 'inherit the card pass claims', 'rebuildFromGLB': 'no (test definitions); re-derived here by measure_service_court.py and check_install.py'},
        {'what': 'ground-south native source / generator (single_closed_terrain_after)', 'use': 'clean local cut for the has-hole variant', 'rebuildFromGLB': 'yes for a local patch: the slab is a regular 2 m grid (edge 2.0-2.828 m) with flat top 0.2 / bottom 0.0'},
    ],
    'priorSameSeatArtifacts': ['inventory.py', 'measure_service.py', 'out/inventory-LOD{0,1,2}.json', 'out/measure-LOD{0,1,2}.json (2026-11-05 20:46-20:48, BVH ray casts; consistent with this prep: hole x +-0.21, no hit below hole, pen gap 76.5-103.5 deg)'],
}
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(rows), 'inputs')
