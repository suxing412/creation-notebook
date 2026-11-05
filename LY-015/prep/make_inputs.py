"""Regenerate inputs.json (paths + SHA256 + city-load status). python -I make_inputs.py <pkg_dir> <out>
--verify mode: python -I make_inputs.py <pkg_dir> <inputs.json> --verify  -> exit 1 on any SHA drift (negative test: edit a byte in a copy)."""
import json, hashlib, sys
from pathlib import Path
LAB = Path('D:/GitHub/creation-notebook-lab'); PKG = Path(sys.argv[1]); OUT = Path(sys.argv[2])
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

if '--verify' in sys.argv:
    d = json.loads(OUT.read_text(encoding='utf-8')); bad = []
    for r in d['inputs']:
        p = Path(r['path'].split('  (inside')[0])
        if '(inside content.zip)' in r['path']: p = PKG / r['path'].split('luoyang-kaiyang-gate-study-v1/', 1)[1].split('  (inside')[0]
        if not p.exists() or sha(p) != r['sha256']: bad.append(r['id'])
    print('DRIFT' if bad else 'INPUTS_OK', bad); sys.exit(1 if bad else 0)

L = 'docs/cities/luoyang/'
rows = [
 ('gate-LOD0', 'docs/library/models/m-luoyang-kaiyang-gate/files/kaiyang-K-LOD0.glb', 'K-v1 gate body near LOD (merged 3 meshes)', False, 'not referenced by city-data.mjs; only asset card files[1] (library viewer)'),
 ('gate-LOD1', L + 'progress-assets/north13-gates/luoyang-kaiyang-gate-study-v1/models/kaiyang-K-LOD1.glb', 'K-v1 gate body mid LOD', False, 'city-data.mjs:744-749 sourceAsset metadata only (not fetched); asset card files[0]'),
 ('gate-LOD2', L + 'progress-assets/north13-gates/luoyang-kaiyang-gate-study-v1/models/kaiyang-K-LOD2.glb', 'K-v1 gate body far LOD', False, 'city-data.mjs:729-743 availableLod2 metadata only (not fetched); asset card files[2]'),
 ('gate-flat-city', L + 'progress-assets/flat/study-north13-kaiyang-K-94693c58dd63.glb', 'site projection of LOD1 (same 1964 tris and volumes); the only Kaiyang file the city fetches', 'conditional: only when the research model is opened in the walls chapter; space=local-study, cityPlacement=null, not drawn in city coordinates', 'city-data.mjs:707-752 asset study-north13-kaiyang-K; city-data.mjs:3774/3826 walls.researchModelIds; city-data.mjs:4178-4200 researchModels; app.mjs:117-118 study choices; city-renderer.mjs:218, 286-293 loadAsset(asset.url), 619 and 645-660 focusResearchModel'),
 ('ground-LOD0', 'docs/library/models/m-luoyang-kaiyang-gate/files/kaiyang-ground-LOD0.glb', 'existing gate-underside test strips (3 x 1.8 x 14 m) near', False, 'asset card files[4] only'),
 ('ground-LOD1', 'docs/library/models/m-luoyang-kaiyang-gate/files/kaiyang-ground-LOD1.glb', 'test strips mid', False, 'asset card files[3] only'),
 ('ground-LOD2', 'docs/library/models/m-luoyang-kaiyang-gate/files/kaiyang-ground-LOD2.glb', 'test strips far', False, 'asset card files[5] only'),
 ('asset-card', 'docs/library/models/m-luoyang-kaiyang-gate/m-luoyang-kaiyang-gate.asset.json', 'public card (status 待审, 未入城)', False, 'lab/data/assets.json build input'),
 ('wall-A-04', L + 'assets/city-wall/A/wall-04.glb', 'current city wall east of the gate gap; end cap at gate-local x=+16.0 (measured)', True, 'city-data.mjs:251 asset, :3312 node initial=true'),
 ('wall-A-05', L + 'assets/city-wall/A/wall-05.glb', 'current city wall west of the gate gap; end cap at gate-local x=-16.0 (measured)', True, 'city-data.mjs:271 asset, :3339 node initial=true'),
 ('ground-stitched', L + 'assets/ground-atomic/network-ground-stitched.glb', 'current city ground layer; 0 of 3321 downward rays over the gate footprint hit it', 'no: node initial=false', 'city-data.mjs:431 asset, :3555 node initial=false'),
 ('city-data', L + 'city-data.mjs', 'city manifest (read-only; LY-100 owns writes)', True, 'index.html -> app.mjs import'),
 ('city-renderer', L + 'city-renderer.mjs', 'renderer (local-study path)', True, 'app.mjs'),
 ('app', L + 'app.mjs', 'UI shell', True, 'index.html'),
 ('project-card', L + 'p-luoyang.asset.json', 'project card (read-only)', False, 'site build'),
 ('north13-source-contract', L + 'progress-assets/north13-gates/source.json', 'source contract incl. a copy of placement', False, 'sourceContract in city-data.mjs:725'),
 ('wall-constraints', L + 'data/west/city-wall-constraints.json', 'gate_kaiyang_B B point (2010.204,-30.612) and C projection (2010.39717,-21.301146)', False, 'data file; not fetched by the renderer for this gate'),
 ('wall-interface', L + 'data/west/city-wall-interface.json', 'wall interface contract', False, 'sourceContract of wall nodes'),
 ('yong-precedent', L + 'progress-assets/yong-city-v1/source.json', 'precedent of an admitted gate assembly (matrix, annex, rollback counts)', True, 'city-data.mjs:1316 yong-gate-interface'),
 ('pkg-part001', 'modeling-lab/review-batches/2026-11-04-north13-gates/luoyang-kaiyang-gate-study-v1/content.zip.part001', 'K-v1 source package part 1', False, '-'),
 ('pkg-part002', 'modeling-lab/review-batches/2026-11-04-north13-gates/luoyang-kaiyang-gate-study-v1/content.zip.part002', 'K-v1 source package part 2', False, '-'),
 ('pkg-manifest', 'modeling-lab/review-batches/2026-11-04-north13-gates/luoyang-kaiyang-gate-study-v1/manifest.json', 'zipSHA256 bad99bb9..., restore rule', False, '-'),
 ('build-tool', 'lab/tools/build_assets.py', 'official checker (only --check, at production time; never run during prep)', False, '-'),
]
pk = [
 ('native-LOD0', 'models/kaiyang-K-LOD0.blend', 'sanitized native LOD0 (original SHA 88877470... per qa/dimensions.json)'),
 ('native-LOD1', 'models/kaiyang-K-LOD1.blend', 'sanitized native LOD1 (original f876be9e... = placement.model_sha256)'),
 ('native-LOD2', 'models/kaiyang-K-LOD2.blend', 'sanitized native LOD2 (original 7deda70c...)'),
 ('trial-blend', 'city/kaiyang-K-mid-hidden-trial.blend', 'hidden trial: LOD1 + two terminal wall adapters joined into earth (original delta ee0fee04...)'),
 ('placement', 'city/placement.json', 'engineering origin (2010.3973,-21.3011,0.17), rot_z -0.020743634 rad, activation=false'),
 ('interface-input', 'qa/interface-input.json', 'wall cap faces from mother eabb2a90...'),
 ('source-ranges', 'qa/source-object-ranges.json', 'per-source-object triangle ranges (verified to hold in the public GLBs)'),
 ('build-py', 'source/build.py', 'deterministic generator of K-v1'),
 ('city-trial-py', 'source/city-trial.py', 'generator of the terminal adapters and placement'),
 ('evidence-md', 'docs/evidence.md', 'evidence note (text sources; C design)'),
 ('readback-rollback', 'qa/city-readback-rollback.json', '2764 old mesh objects unchanged, rollback exact (bound to original SHAs)'),
]
out = {'baseline_commit': 'bce3211f818ee5a8bef1773539da70695ba37b17',
       'package_zip_sha256_expected': 'bad99bb9f5b301b5b6a3450931511caec385df3da8b5ffc5b94b1664eb598c23',
       'package_restore': 'cat content.zip.part001 content.zip.part002 > content.zip; sha256 must equal expected; unzip into scratch only',
       'inputs': []}
for i, rel, role, loaded, code in rows:
    p = LAB / rel
    out['inputs'].append({'id': i, 'path': str(p).replace('\\', '/'), 'bytes': p.stat().st_size, 'sha256': sha(p), 'role': role, 'loadedInCity': loaded, 'loaderCode': code})
for i, rel, role in pk:
    p = PKG / rel
    out['inputs'].append({'id': i, 'path': 'luoyang-kaiyang-gate-study-v1/' + rel + '  (inside content.zip)', 'bytes': p.stat().st_size, 'sha256': sha(p), 'role': role, 'loadedInCity': False, 'loaderCode': 'not public; source package only'})
out['missing'] = [
 {'id': 'bearing-section-v1', 'need': 'named by TASKPOOL as an input; the failed bearing frame and lintel/beam overlap (0.0936 m3) that LY-011 replaces', 'searched': 'lab main bce3211 (git grep), origin/luoyang-content, D:/GitHub/creation-notebook-待传 (only 说明.txt), D:/GitHub grep', 'rebuildFromGLB': 'no: it is a different, failed version; K-v1 GLBs do not contain it'},
 {'id': 'kaiyang adaptation-failure / actual-section records', 'need': 'before-evidence for the 0.0936 m3 and 21.76 m3 issues', 'searched': 'same as above', 'rebuildFromGLB': 'no'},
 {'id': 'kaiyang-ground source (.blend, generator, 1782-sample QA)', 'need': 'editable source and original QA of the 3 test strips', 'searched': 'commit c07ecc5 added only GLBs', 'rebuildFromGLB': 'yes: 3 boxes 1.8 x 14 x 0.2 m with about 2 mm micro-relief; the GLBs carry the full geometry, UV and textures'},
 {'id': 'mother eabb2a90... (city-C032-wuku-facade.blend) and overlay 660cdf37... (four-family-plus-gate-wall-overlay.blend)', 'need': 'placement.json binds both; strict native install/rollback', 'searched': 'not in repo; README of the batch says they are not repackaged', 'rebuildFromGLB': 'partly: the current city wall-04/05 GLBs reproduce both caps at gate-local x=+/-16.0, enough for the web-side contact check, not for re-running the native 2764-object rollback'},
 {'id': 'original pre-sanitization natives f876be9e... / ee0fee04...', 'need': 'placement.json and the old QA are bound to these SHAs', 'searched': 'only sanitized equivalents f283dbf9... / 75c96a3f... plus NATIVE-EQUIVALENCE.json', 'rebuildFromGLB': 'not needed: equivalence report exists; new QA must bind the sanitized SHAs'},
 {'id': 'LY-011/012/013/014 deliverables', 'need': 'the revision parts this seat assembles', 'searched': 'workpacks LY-011..014: only LY-011/prep/_src', 'rebuildFromGLB': 'no: must wait'},
 {'id': 'G frozen contracts (LY-001/002/005/006/007/008/009/010)', 'need': 'ports, ownership, LOD/material baseline, checker, admission', 'searched': 'workpacks: LY-001 ledger in progress, rest absent', 'rebuildFromGLB': 'no'},
]
OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8'); print(len(out['inputs']), 'inputs')
