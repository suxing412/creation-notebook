# LY-034 prep: writes inputs.json (read-only on the lab repo; uses `git show` only).
import json, hashlib, subprocess, os
LAB = 'D:/GitHub/creation-notebook-lab'
HERE = os.path.dirname(os.path.abspath(__file__))
HEAD = subprocess.run(['git', '-C', LAB, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
def sha_file(p): return hashlib.sha256(open(os.path.join(LAB, p), 'rb').read()).hexdigest()
def sha_blob(p):
    r = subprocess.run(['git', '-C', LAB, 'show', 'HEAD:' + p], capture_output=True)
    return hashlib.sha256(r.stdout).hexdigest() if r.returncode == 0 else None
C = 'docs/cities/luoyang/'
M = 'docs/model-library/'
U = M + 'updates/m-storage-functional/files/'
rows = [
 (C + 'progress-assets/granary-city-v1/granary-city-LOD0.glb', 'GLB', True,
  'city-data.mjs:582-599 asset storage-main (path); :3716-3740 node storage-main initial:false; :3983-4008 chapter storage loadNodeIds; city-renderer.mjs:217 assets map, :285-299 loadAsset() fetch + GLTFLoader.parseAsync, :601 chapter loadNodeIds added on focus',
  'Current in-city near tier. Measured: ground slab, receiving shelter/table/cargo, A 4-riser and B 6-riser stairs. Primary baseline for LY-034.'),
 (C + 'progress-assets/granary-city-v1/granary-city-LOD1.glb', 'GLB', False, 'not referenced by city-data.mjs; listed in model-library/m-storage-functional.asset.json files', 'Mid tier, independent inspection only (source.json cityRuntime.midAndFar). Ports measured identical to LOD0.'),
 (C + 'progress-assets/granary-city-v1/granary-city-LOD2.glb', 'GLB', False, 'not referenced by city-data.mjs; listed in model card', 'Far tier, no cargo proxies. Ports identical to LOD0.'),
 (C + 'progress-assets/granary-city-v1/source.json', 'contract', False, 'city-data.mjs:599 and :3729 sourceContract (link only, app.mjs:96)', 'Runtime contract: absolute coords, position [0,0,0], no external road.'),
 (C + 'progress-assets/granary-city-v1/README.md', 'doc', False, 'not loaded', '0.9 m pass / 1.8 m fail, external road not connected.'),
 (C + 'assets/storage/storage-group-organized.glb', 'GLB', True, 'v1/west-layer.mjs:39 (legacy v1 entry, level storage: layout.environmentUrl); app.mjs:7 redirects legacy view to v1/', 'Old organized v1 group still loaded by the v1 page; front-field islands geometry-identical to LOD0 (16/16 at 1 mm), steps are 10 separate boxes instead of 2 welded stairs.'),
 (C + 'data/west/storage-interface.json', 'contract', False, 'city-data.mjs:4521 provenance list only', 'STALE: defaultLoad = old organized GLB; 3 of 4 listed file paths do not resolve under cities/luoyang; declares no ports.'),
 (C + 'data/west/storage-precedents.json', 'evidence', False, 'v1 page evidence', 'C proposal + evidence limits for storage (Houshigu mingqi, Gao 2023 regional diagram).'),
 (C + 'city-data.mjs', 'code', True, 'imported by app.mjs:1', 'Shared file: read-only for LY-034 (only LY-100 writes).'),
 (C + 'city-renderer.mjs', 'code', True, 'imported by app.mjs', 'Loader: no LOD switch, merges static meshes; excludeNodes honoured at :309.'),
 (C + 'app.mjs', 'code', True, 'index.html', 'Entry.'),
 (C + 'v1/west-layer.mjs', 'code', True, 'v1/index.html', 'Legacy storage view loads old GLB.'),
 (C + 'p-luoyang.asset.json', 'card', False, 'site build', 'Project card; read-only.'),
 (C + 'assets/city-wall/A/wall-01.glb', 'GLB', True, 'city-data asset wall-A-wall-01 (initial true)', 'Only city node whose bounds overlap the storage bbox; measured 61.6 m plan distance from the slab.'),
 (M + 'm-storage-functional.asset.json', 'card', False, 'model library', 'Status pending review; lists 12 v2 GLBs + 3 city tiers + legacy files.'),
 (M + 'assets/storage-origin-contract.json', 'contract', False, 'model library', 'Anchor (2285.714111328125, 0, -3673.468994140625) used by all LY-034 measurements.'),
 (U + 'granary-receiving-LOD0.glb', 'GLB', False, 'model card only', 'v2 receiving part; 15/15 islands identical to city LOD0 at 1 mm.'),
 (U + 'granary-A-LOD0.glb', 'GLB', False, 'model card only', 'v2 A part, origin offset (-12,0,-6) from city local; stair island identical.'),
 (U + 'granary-B-LOD0.glb', 'GLB', False, 'model card only', 'v2 B part, origin offset (+12,0,-6); stair island identical.'),
 (U + 'granary-group-LOD0.glb', 'GLB', False, 'model card only', 'v2 group without ground slab; 168/212 islands identical, 44 roof tiles differ at 1 mm hash level.'),
]
for n in ('A', 'B', 'group', 'receiving'):
    for l in (1, 2):
        rows.append((U + 'granary-%s-LOD%d.glb' % (n, l), 'GLB', False, 'model card only', 'v2 tier, not measured by LY-034 prep.'))
out = {'seat': 'LY-034', 'labHead': HEAD,
       'note': 'sha256 = bytes of the local checkout (core.autocrlf=true: text files are CRLF); commitBlobSha256 = bytes of git show HEAD:path (LF). They differ for text files only.',
       'anchor_gltf_world': [2285.714111328125, 0.0, -3673.468994140625], 'inputs': []}
for p, kind, loaded, where, note in rows:
    a, b = sha_file(p), sha_blob(p)
    out['inputs'].append({'path': p, 'kind': kind, 'bytes': os.path.getsize(os.path.join(LAB, p)), 'sha256': a,
                          'commitBlobSha256': b, 'checkoutEqualsCommit': a == b, 'loadedInCity': loaded,
                          'loadedBy': where, 'note': note})
out['missing'] = [
 {'what': 'private native .blend and "Luoyang private granary city composer v1" generator / validation sources',
  'use': 'named sub-objects (shelter, table, stair) and authored ports; source.json limitations last line',
  'rebuildFromGLB': 'yes for LY-034: ports, support and fingerprints are measured from GLB loose parts; no geometry needs regenerating'},
 {'what': 'operations / entrance-volume diagnostic data cited in TASKPOOL (card: A 51 / B 77 failing 1.8 m probes)',
  'use': 'reproduce the earlier probe set exactly as a regression baseline',
  'rebuildFromGLB': 'partially: measure_frontfield.py re-derives pass/fail by body width; the 51/77 counts depend on an unpublished probe definition'},
 {'what': 'G package outputs LY-005 (coordinate/port format), LY-006 (port IDs, ownership template), LY-007, LY-008 (checker), LY-010 (storage region admission)',
  'use': 'port JSON schema, ownership of slab and stair-foot cells, checker entry point',
  'rebuildFromGLB': 'no - contracts, must be frozen by their seats'},
 {'what': 'C_NE_APPROACH_LOCAL (~196 m C road) GLB and preflight',
  'use': 'neighbour-road fingerprint at the slab edge',
  'rebuildFromGLB': 'not in lab repo at bce3211 (grep 0 hits); owned by LY-039'},
]
json.dump(out, open(os.path.join(HERE, 'inputs.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(out['inputs']), 'inputs;', sum(not r['checkoutEqualsCommit'] for r in out['inputs']), 'CRLF-differing')
