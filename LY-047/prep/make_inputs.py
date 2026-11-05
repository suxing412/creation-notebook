# LY-047 prep: hash every input and record whether/where the city loads it. Read-only on the lab repo.
# usage: python -I make_inputs.py <lab_root> <out.json>
import sys, os, json, hashlib, re, subprocess
LAB, OUT = sys.argv[1], sys.argv[2]
D = os.path.join(LAB, 'docs')
HERE = os.path.dirname(os.path.abspath(__file__))
WP = os.path.dirname(os.path.dirname(HERE))


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def head_sha(relpath):
    # sha256 of the committed (LF) blob at HEAD; the Windows work tree has core.autocrlf=true so text files differ
    try:
        b = subprocess.run(['git', '-C', LAB, 'show', 'HEAD:' + relpath], capture_output=True, check=True).stdout
        return hashlib.sha256(b).hexdigest()
    except Exception:
        return None


def line_of(path, needle):
    for i, L in enumerate(open(path, encoding='utf-8', errors='replace'), 1):
        if needle in L:
            return i
    return None


CD = os.path.join(D, 'cities/luoyang/city-data.mjs')
CR = os.path.join(D, 'cities/luoyang/city-renderer.mjs')
cr_loc = 'city-renderer.mjs:221 initial set (initial!==false); :286-309 loadAsset + excludeNodes; :346 all exclusions must match; :411-419 near file only for focused node; :612-623 focusCourtyard'

items = [
    # role, rel path (docs/...), loaded, loader
    ('B far prototype (10 courts)', 'cities/luoyang/assets/r01/R01-B-LOD1-prototype.glb', True, f'city-data.mjs:{line_of(CD, "R01-B-LOD1-prototype.glb")} assets[courtyard-B].path; {cr_loc}'),
    ('B near prototype (focused court only)', 'cities/luoyang/assets/r01/R01-B-LOD0-prototype.glb', True, f'city-data.mjs:{line_of(CD, "R01-B-LOD0-prototype.glb")} nearPath; city-renderer.mjs:416 near only when node.id===nextNearId'),
    ('B2 far prototype (7 courts)', 'cities/luoyang/assets/c02v/B2-LOD1-prototype.glb', True, f'city-data.mjs:{line_of(CD, "B2-LOD1-prototype.glb")} assets[courtyard-B2].path; {cr_loc}'),
    ('B2 near prototype', 'cities/luoyang/assets/c02v/B2-LOD0-prototype.glb', True, f'city-data.mjs:{line_of(CD, "B2-LOD0-prototype.glb")} nearPath'),
    ('A2 far prototype (C02-010 proposed by LY-041)', 'cities/luoyang/assets/c02v/A2-LOD1-prototype.glb', True, f'city-data.mjs:{line_of(CD, "A2-LOD1-prototype.glb")}'),
    ('A2 near prototype', 'cities/luoyang/assets/c02v/A2-LOD0-prototype.glb', True, f'city-data.mjs:{line_of(CD, "A2-LOD0-prototype.glb")} nearPath'),
    ('workshed LOD0 (registered shed module)', 'library/models/m-luoyang-workyard-shed/files/workshed-LOD0.glb', False, 'not referenced by any docs/cities/luoyang *.mjs or data file; only listed in p-luoyang.asset.json related'),
    ('workshed LOD1', 'library/models/m-luoyang-workyard-shed/files/workshed-LOD1.glb', False, 'not referenced'),
    ('workshed LOD2', 'library/models/m-luoyang-workyard-shed/files/workshed-LOD2.glb', False, 'not referenced'),
    ('workyard LOD0 (complete two-house court; NOT installable into an existing court)', 'library/models/m-luoyang-workyard-shed/files/workyard-LOD0.glb', False, 'not referenced'),
    ('workyard LOD1', 'library/models/m-luoyang-workyard-shed/files/workyard-LOD1.glb', False, 'not referenced'),
    ('workyard LOD2', 'library/models/m-luoyang-workyard-shed/files/workyard-LOD2.glb', False, 'not referenced'),
    ('workyard-shed card', 'library/models/m-luoyang-workyard-shed/m-luoyang-workyard-shed.asset.json', False, 'library card, status 待审'),
    ('B2 preset baseline (pre-C2)', 'model-library/updates/m-courtyard-family/files/baseline.glb', False, 'not referenced by city'),
    ('B2 preset north (shed -0.8 m z)', 'model-library/updates/m-courtyard-family/files/north.glb', False, 'not referenced by city'),
    ('B2 preset south (shed +0.8 m z)', 'model-library/updates/m-courtyard-family/files/south.glb', False, 'not referenced by city'),
    ('B C2 UV revision LOD0', 'model-library/updates/m-courtyard-family/files/B-LOD0-C2.glb', False, 'not referenced (C2 UV-only revision, 待审)'),
    ('B2 C2 UV revision LOD0', 'model-library/updates/m-courtyard-family/files/B2-LOD0-C2.glb', False, 'not referenced'),
    ('courtyard-family card', 'model-library/m-courtyard-family.asset.json', False, 'library card'),
    ('model-library contracts', 'model-library/contracts.json', False, 'courtyard-family origin contract'),
    ('compact_work court (layout kit; full court, not a shed module)', 'library/models/m-luoyang-court-layout-kit/files/compact_work-LOD0.glb', False, 'not referenced'),
    ('north B storage court research model', 'cities/luoyang/progress-assets/flat/study-north13-court-B-6f7f84af4e7f.glb', False, f'city-data.mjs:{line_of(CD, chr(34)+"asset"+chr(34)+": "+chr(34)+"study-north13-court-B"+chr(34))} researchModels, space local-study, cityPlacement null, initial false'),
    ('north B2 storage court research model', 'cities/luoyang/progress-assets/flat/study-north13-court-B2-7d3758ce668d.glb', False, 'researchModels, local-study, cityPlacement null'),
    ('ground south', 'cities/luoyang/assets/ground-atomic/south.glb', 'terrain chapter only', f'city-data.mjs:{line_of(CD, chr(34)+"id"+chr(34)+": "+chr(34)+"ground-south"+chr(34))} asset; node initial:false'),
    ('ground retained', 'cities/luoyang/assets/ground-atomic/retained.glb', 'terrain chapter only', 'node initial:false'),
    ('ground network stitched', 'cities/luoyang/assets/ground-atomic/network-ground-stitched.glb', 'terrain chapter only', 'node initial:false'),
    ('ground D08 (translation 580,0,-960)', 'cities/luoyang/assets/ground-atomic/D08.glb', 'terrain chapter only', 'node initial:false, position [580,0,-960]'),
    ('R01 model contract (variant B = 居住兼储藏作业院)', 'cities/luoyang/data/r01/model-contract.json', False, 'data only'),
    ('C02V model contract', 'cities/luoyang/data/c02v/model-contract.json', False, 'data only'),
    ('far44 instances C-alt (44 matrices)', 'cities/luoyang/data/far44/instances-calt.json', False, 'sourceContract of court nodes'),
    ('far44 preflight', 'cities/luoyang/data/far44/preflight-contract.json', False, 'sourceContract of court assets'),
    ('city manifest', 'cities/luoyang/city-data.mjs', True, 'imported by app.mjs:1'),
    ('city renderer', 'cities/luoyang/city-renderer.mjs', True, 'app'),
    ('app', 'cities/luoyang/app.mjs', True, 'index.html'),
    ('index', 'cities/luoyang/index.html', True, ''),
    ('project card', 'cities/luoyang/p-luoyang.asset.json', False, 'read only; LY-100 owns writes'),
]
out = {'tool': 'make_inputs.py', 'labCommit': 'bce3211f818ee5a8bef1773539da70695ba37b17', 'inputs': []}
for role, relp, loaded, loader in items:
    p = os.path.join(D, relp)
    out['inputs'].append({'role': role, 'path': 'docs/' + relp, 'sha256': sha(p), 'bytes': os.path.getsize(p), 'loadedInCity': loaded, 'loader': loader,
                          'native': 'none in repo; GLB only'} if relp.endswith('.glb') else
                         {'role': role, 'path': 'docs/' + relp, 'sha256': sha(p), 'bytes': os.path.getsize(p), 'loadedInCity': loaded, 'loader': loader})
for e in out['inputs']:
    if not e['path'].endswith('.glb'):
        e['headBlobSha256'] = head_sha(e['path'])
        e['shaNote'] = 'sha256 = Windows work-tree bytes (CRLF, autocrlf=true); headBlobSha256 = committed LF blob at bce3211'
lab = os.path.join(LAB, 'lab/data/assets.json')
out['inputs'].append({'role': 'site asset summary (read only)', 'path': 'lab/data/assets.json', 'sha256': sha(lab), 'headBlobSha256': head_sha('lab/data/assets.json'), 'bytes': os.path.getsize(lab), 'loadedInCity': False, 'loader': 'site build'})
for seat, f in [('LY-041', 'prep-status.json'), ('LY-043', 'prep-status.json'), ('LY-044', 'prep-status.json'), ('LY-044', 'probe-place.json')]:
    p = os.path.join(WP, seat, 'prep', f)
    if os.path.exists(p):
        out['inputs'].append({'role': f'sibling prep (not frozen) {seat}', 'path': f'workpacks/{seat}/prep/{f}', 'sha256': sha(p), 'bytes': os.path.getsize(p), 'loadedInCity': False, 'loader': 'none'})
for f in ['measure_ly047.py', 'selftest_ly047.py', 'blender_crosscheck.py', 'glbio.py', 'citydata.py', 'measure-ly047.json', 'selftest-ly047.json', 'blender-crosscheck.json']:
    p = os.path.join(HERE, f)
    out.setdefault('prepFiles', []).append({'path': f'workpacks/LY-047/prep/{f}', 'sha256': sha(p), 'bytes': os.path.getsize(p)})
out['missing'] = [
    {'what': 'native source of R01-B / B2 prototypes (.blend or generator, source_sha256 65e4e69b… / B2 per C02V contract)', 'use': 'split the in-place shed (posts, beams, bins, bench, shed roof) out of the court-wide nodes so it could be toggled; only needed if LY-010 asks for a removable B shed', 'rebuildFromGLB': 'yes for the box parts (components identified: 4 posts, 4 plinths, 2 beams, 2 bins, bench top+4 legs); the shed roof is part of a 7,896-tri roof node and must be cut by region; original authoring intent not recoverable'},
    {'what': 'native source of workshed (.blend) ', 'use': 'not needed for install (rigid placement + y offset); needed only if a storage bin set must be added under it', 'rebuildFromGLB': 'not needed'},
    {'what': 'private source ZIP / Release package of m-luoyang-workyard-shed and m-courtyard-family presets', 'use': 'QA definitions behind the card claims (shed support, 0/4/8 deg pose checks, preset route checks) so they could be inherited', 'rebuildFromGLB': 'no; the claims must be re-measured instead (done here for support/clearance)'},
    {'what': 'LY-010 decision table', 'use': 'which court is the demo court and whether a storage/shed use is selected for it', 'rebuildFromGLB': 'n/a'},
    {'what': 'LY-005 elevation contract', 'use': 'freeze floor datum 0.200 vs prototype yard 0.215', 'rebuildFromGLB': 'n/a'},
    {'what': 'LY-006 port/ownership registry', 'use': 'who owns the A2 yard cells a shed would occupy (LY-044 stove, LY-045 latrine, LY-047 shed)', 'rebuildFromGLB': 'n/a'},
    {'what': 'LY-002 evidence table', 'use': 'evidence grade for household storage sheds/bins around 180 CE Luoyang', 'rebuildFromGLB': 'n/a'},
]
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('wrote', OUT, len(out['inputs']))
