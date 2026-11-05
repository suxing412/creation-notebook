# Builds inputs.json (read-only hashing of lab files). python make_inputs.py
import json, hashlib, os
LAB = 'D:/GitHub/creation-notebook-lab/'
HERE = os.path.dirname(os.path.abspath(__file__))
def sha(p): return hashlib.sha256(open(LAB + p, 'rb').read()).hexdigest()
items = []
def add(p, role, loaded, where, note=''):
    items.append({'path': p, 'sha256': sha(p), 'bytes': os.path.getsize(LAB + p), 'role': role,
                  'loadedInCity': loaded, 'loadedBy': where, 'note': note})
S = 'docs/library/models/m-luoyang-cooking-stove/files/'
for f in ['A', 'B']:
    for l in (0, 1, 2):
        add(S + f'stove-{f}-LOD{l}.glb',
            f'reuse geometry: stove {f} LOD{l} (earth body + side prep board in one GLB, nodes {f}_earth/{f}_timber, origin = body bottom centre, fire mouth on local +z)',
            False, None, 'no reference in docs/cities/luoyang *.mjs, v1/*.mjs, data/*.json (grep stove|cooking|preparation hits only p-luoyang.asset.json text)')
add('docs/library/models/m-luoyang-cooking-stove/m-luoyang-cooking-stove.asset.json', 'asset card stove A/B (status 待审, 未入城)', False, None)
P = 'docs/library/models/m-luoyang-residential-preparation/files/'
for l in (0, 1, 2):
    add(P + f'W2-stove-A-LOD{l}.glb',
        f'existing W2 relation LOD{l}: stove-A translated by (489.4,0.2,-1003.8) in the 13-yard life-block frame; nodes C_LIFE_W2_STOVE_A_V1__A_earth / __A_timber',
        False, None, 'measured: equals stove-A vertices after pure translation (max nearest-vertex distance <= 4.7e-5 m); 0 of 87 bottom vertices have any city ground below (probe-w2-city.json)')
add('docs/library/models/m-luoyang-residential-preparation/m-luoyang-residential-preparation.asset.json', 'asset card W2 relation (status 待审, 已建模未入城)', False, None)
L = 'docs/library/models/m-luoyang-residential-life/files/'
for l in (0, 1, 2):
    add(L + f'life-block-LOD{l}.glb', f'13-yard life block LOD{l} (yard LIFE-W2 hosts W2); protected 13院 area, read only, used only to re-verify W2 support', False, None)
add('docs/library/models/m-luoyang-residential-life/m-luoyang-residential-life.asset.json', 'asset card 13-yard life block', False, None)
add('docs/cities/luoyang/assets/c02v/A2-LOD1-prototype.glb', 'candidate yard C02-010 far prototype (LY-041 draft choice, not frozen)', True,
    'city-data.mjs:88-112 asset courtyard-A2 path; node C02-010 city-data.mjs:2322; excludeNodes applied at city-renderer.mjs:309')
add('docs/cities/luoyang/assets/c02v/A2-LOD0-prototype.glb', 'candidate yard C02-010 near prototype', True,
    'city-data.mjs:109 nearPath; near tier only for the focused node (city-renderer.mjs:416, focusCourtyard :616)')
add('docs/cities/luoyang/assets/c02v/TC03-2-LOD1-prototype.glb', 'comparison yard C02-012 far (layout has route rear_to_kitchen)', True,
    'city-data.mjs:142-168 asset courtyard-TC03-2; node C02-012 city-data.mjs:2406')
add('docs/cities/luoyang/assets/c02v/TC03-2-LOD0-prototype.glb', 'comparison yard C02-012 near', True, 'city-data.mjs:165 nearPath')
for g, line in (('south', 'city-data.mjs:471 asset / :3609 node ground-south, initial:false'),
                ('network-ground-stitched', 'city-data.mjs:432'), ('retained', 'city-data.mjs:452'),
                ('D08', 'city-data.mjs:492 (node translation 580,0,-960)')):
    add(f'docs/cities/luoyang/assets/ground-atomic/{g}.glb', f'actual city ground ({g}); C02-010 lot is 100% ground-south at y=0.2000', True,
        line + '; also v1/west-layer.mjs:31,35')
for p, r, w in (
        ('docs/cities/luoyang/data/far44/instances-calt.json', '44-yard matrices (C02-010 calt T=(531,0,-818.45), changedByCalt true)', 'sourceContract of residential nodes, e.g. city-data.mjs:1382'),
        ('docs/cities/luoyang/data/far44/preflight-contract.json', 'prototype list', 'sourceContract of courtyard assets'),
        ('docs/cities/luoyang/data/c02v/layout.json', 'localRoutes per lot (C02-010: gate_to_main, yard_to_side; C02-012 adds rear_to_kitchen)', 'C02 preset layer under v1/, not city-data'),
        ('docs/cities/luoyang/data/c02v/routes.json', 'world route overlay in ORIGINAL layout coordinates (not calt)', 'C02 preset layer under v1/'),
        ('docs/cities/luoyang/data/west/ground-atomic-contract.json', 'ground composition contract (doNotClaim: collision validated)', 'v1/west-layer.mjs:40, v1/road-layer.mjs:19'),
        ('docs/cities/luoyang/city-data.mjs', 'city manifest (shared; only LY-100 writes)', 'app.mjs'),
        ('docs/cities/luoyang/city-renderer.mjs', 'loader: initial set :221, excludeNodes :309, near tier :416, focusCourtyard :616', 'app.mjs'),
        ('docs/cities/luoyang/v1/west-layer.mjs', 'C-alt ground composition', 'v1 boot'),
        ('docs/cities/luoyang/p-luoyang.asset.json', 'project card: 院内备食关系 :203-208, 庖厨炉灶 :226-230 (shared; only LY-100 writes)', 'library build')):
    add(p, r, None, w)
out = {
    'seat': 'LY-044', 'phase': 'prep (G not frozen; no delivery geometry made)',
    'labBaseline': 'bce3211f818ee5a8bef1773539da70695ba37b17',
    'labWorkingTreeNote': 'lab working tree has uncommitted edits in lab/data/assets.json, glb-cache.json, report.json (not by LY-044); every docs/ file listed is clean vs HEAD. lab/data/assets.json HEAD blob sha256 53d863121bb583b362bf9929bf18c1d91aaf6f36fb8d3808e70a8a3e4825df78, working tree 3440caa2a38a0893e4c27177c0127fc46ea6ffec31694ab3c1d6980d212c3f7a',
    'nativeSources': {'status': 'missing (not in repo)', 'items': [
        {'what': 'stove A/B editable source (.blend / generator) behind m-luoyang-cooking-stove', 'use': 'only if stove geometry had to change; also backs the card claim native == GLB',
         'rebuildFromGLB': 'geometry yes (complete static mesh + UV + embedded textures); not needed: LY-044 must not change stove geometry'},
        {'what': 'W2 placement source / QA package (life-block frame: 14 routes, 2 fixed-orientation work positions, 2 turn-back bays, 65 protected routes, wrong-work-position negative)',
         'use': 'reuse already validated operator / turn envelopes and their negative', 'rebuildFromGLB': 'no: test definitions are not contained in any GLB; must be redefined as C parameters for the chosen city yard'},
        {'what': 'life-block (13-yard) source and its yard-ground definition', 'use': 're-verify W2 context only', 'rebuildFromGLB': 'geometry yes; not needed for a 44-yard installation'}]},
    'contracts': {'coordinate': 'glTF Y-up metres, x east, z = -local north; city node matrices column-major (LY-005 to freeze)',
                  'groundDatum': 'C02-010 yard ground = ground-south top y=0.2000 (measured 0.199997..0.200005); NOT the excluded prototype designed_hardpacked_activity_ground 0.215',
                  'ports': 'pending LY-006'},
    'inputs': items,
    'prepOutputs': {f: hashlib.sha256(open(os.path.join(HERE, f), 'rb').read()).hexdigest()
                    for f in ['measure_ly044.py', 'measure-ly044.json', 'probe_w2_city.py', 'probe-w2-city.json', 'mask-C02-010.png', 'mask-C02-012.png', 'probe_a2.py', 'probe_place.py', 'probe-place.json', 'make_inputs.py']}}
json.dump(out, open(os.path.join(HERE, 'inputs.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(items))
for k, v in out['prepOutputs'].items(): print(k, v)
