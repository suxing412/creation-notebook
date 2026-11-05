# LY-049 prep: writes inputs.json (paths, SHA256, city load status, loading code location). Read-only on inputs.
import json, hashlib, os
LAB = 'D:/GitHub/creation-notebook-lab/'
WP = 'D:/GitHub/creation-notebook-workpacks/'
C = 'docs/cities/luoyang/'


def sha(p):
    h = hashlib.sha256(); h.update(open(p, 'rb').read()); return h.hexdigest()


items = [
 (LAB + C + 'assets/c02v/A2-LOD0-prototype.glb', 'yes, near only', 'city-data.mjs:109-111 nearPath; city-renderer.mjs:405-416 near = node.id === nextNearId; focusCourtyard city-renderer.mjs:616-623', 'courtyard-A2 near; gate geometry source (measured)'),
 (LAB + C + 'assets/c02v/A2-LOD1-prototype.glb', 'yes, initial', 'city-data.mjs:88-96 path + excludeNodes; node C02-010 city-data.mjs:2322 initial:true; city-renderer.mjs:221', 'courtyard-A2 far'),
 (LAB + C + 'assets/ground-atomic/south.glb', 'only after terrain chapter', 'city-data.mjs:471 asset, :3609 node initial:false; terrain chapter :4027 loadNodeIds; city-renderer.mjs:600-601 union', 'sole support of gate passage (owner LY-090)'),
 (LAB + C + 'assets/ground-atomic/retained.glb', 'only after terrain chapter', 'city-data.mjs:451 / :3582', 'layer check; 0 tris in region'),
 (LAB + C + 'assets/ground-atomic/network-ground-stitched.glb', 'only after terrain chapter', 'city-data.mjs:431 / :3555', 'layer check; 0 tris in region'),
 (LAB + C + 'assets/ground-atomic/D08.glb', 'only after terrain chapter', 'city-data.mjs:491 / :3636 (translation 580,0,-960)', 'layer check; 0 tris in region'),
 (LAB + C + 'city-data.mjs', 'yes (manifest)', 'app.mjs:1 import manifest', 'node C02-010 matrix, excludeNodes, chapters (residential :3835, loadNodeIds :3884 has no ground)'),
 (LAB + C + 'city-renderer.mjs', 'yes', 'app.mjs:177 dynamic import', 'initial set :221; excludeNodes :309-318; transformFor :374-389; focusCourtyard :616'),
 (LAB + C + 'app.mjs', 'yes', 'index.html module entry', 'legacy v1 redirect app.mjs:6-7 only with mode/c01stage/c02stage query'),
 (LAB + C + 'index.html', 'yes', '-', 'page'),
 (LAB + C + 'p-luoyang.asset.json', 'card (not runtime)', '-', 'project card, read only, not edited'),
 (LAB + C + 'data/far44/instances-calt.json', 'no (source contract)', 'city-data.mjs node sourceContract', 'C02-010 matrix provenance'),
 (LAB + C + 'data/far44/instances-original.json', 'no', '-', 'original layout (x 537.17635) for reconciling old routes'),
 (LAB + C + 'data/far44/preflight-contract.json', 'no (source contract)', 'city-data.mjs asset sourceContract', 'prototype list'),
 (LAB + C + 'data/west/ground-atomic-contract.json', 'no (source contract)', 'city-data.mjs ground sourceContract', 'ground composition'),
 (LAB + C + 'data/west/network.json', 'no (v1 legacy only)', 'v1/west-layer.mjs:17', 'C02-010_door_approach; minimumDesignedWidth 2.3 (vs exact 2.13)'),
 (LAB + C + 'data/c02v/routes.json', 'no', '-', 'C02-010-gate in original layout x 533.67635 (C-alt 527.5)'),
 (LAB + C + 'research/2026-11-03/land-contract.json', 'no (research page)', '-', 'C02-010-entry keep-clear reserve x 526.3-528.7, N 798.8-807.65'),
 (LAB + C + 'research/2026-11-03/gate-replacement-contract.json', 'no (research)', '-', 'gate roof study anchor (-3.5,-10.6,0); body retained'),
 (LAB + C + 'research/2026-11-03/south14-geometry.json', 'no (research)', '-', 'C02-010-gate route check, original layout'),
 (LAB + C + 'research/2026-11-03/stair-diagnosis.json', 'no (research)', '-', 'C02-010-gate_to_main stair contacts (inside court, not 049 scope)'),
 (LAB + 'docs/model-library/assets/gate-near-local.glb', 'no (library research)', '-', 'gate roof study near; body identical to A2 gate'),
 (LAB + 'docs/model-library/assets/gate-original.glb', 'no', '-', 'archived original gate'),
 (LAB + 'docs/model-library/assets/gate-roof.glb', 'no', '-', 'gate roof candidate'),
 (LAB + 'docs/model-library/m-gate-roof-study.asset.json', 'card', '-', 'gate roof study card'),
 (LAB + 'docs/model-library/m-courtyard-family.asset.json', 'card', '-', 'courtyard family card (C2 updates not loaded)'),
 (LAB + 'lab/data/assets.json', 'no (site build data)', '-', 'summary, read only'),
 (WP + 'LY-006/registry/ports.json', 'contract', '-', 'C02-010:gate-boundary:road-end v1 (null values), ground-base v1, service-opening v1'),
 (WP + 'LY-006/registry/zones.json', 'contract', '-', 'LY-049:write:001 local box [-5,-0.3,9]-[-1,3.2,12]; LY-082:write:001 world z from -806.45'),
 (WP + 'LY-006/registry/seams.json', 'contract', '-', 'seams[20,21,28,31]'),
 (WP + 'LY-006/registry/ownership.json', 'contract', '-', 'R049-gate-transition fixed; ground-south owner LY-090'),
 (WP + 'LY-006/registry/seats.json', 'contract', '-', 'LY-049 seat record'),
 (WP + 'LY-005/coordinate-contract.json', 'contract', '-', 'world = N.S.v; E1-E4; tolerance 5 mm / 2 mm'),
 (WP + 'LY-002/tables/evidence-ledger.json', 'contract', '-', 'E-H01; prohibitions X07 X12 X24'),
]
out = dict(
    seat='LY-049', baseline='bce3211f818ee5a8bef1773539da70695ba37b17', frame='glTF world, x east, y up, z = -north',
    court=dict(node='C02-010', asset='courtyard-A2', matrixColumnMajor=[1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 531, 0, -818.45, 1],
               selectedBy='LY-006 candidate frame; LY-010 not delivered'),
    ports=dict(produces='C02-010:gate-boundary:road-end@v1', consumes=['C02-010:ground-base@v1', 'C02-010:service-opening:opening@v1']),
    nativeSources=dict(status='missing (not in repo)', items=[
        dict(what='A2 courtyard prototype native source (.blend / c02v generator)', use='only if the gate body itself had to change; not needed for reuse',
             rebuildFromGLB='yes for a new separate component (read GLB); must be labelled 从GLB重建'),
        dict(what='ground-south native source / south14 composition generator', use='only if a ground cut/diff were needed; owner LY-090',
             rebuildFromGLB='possible (single node single_closed_terrain_after, 96,796 tris) but only LY-090 may emit it')]),
    inputs=[dict(path=p.replace(LAB, 'lab:').replace(WP, 'workpacks:'), sha256=sha(p), bytes=os.path.getsize(p),
                 loadedInCity=l, loadedBy=c, use=u) for p, l, c, u in items])
here = os.path.dirname(os.path.abspath(__file__))
prep = []
for f in sorted(os.listdir(here)):
    if f in ('inputs.json', 'prep-status.json') or f.startswith('__'):
        continue
    p = os.path.join(here, f)
    if os.path.isfile(p):
        prep.append(dict(file=f, sha256=sha(p)))
out['prepArtifacts'] = prep
json.dump(out, open(os.path.join(here, 'inputs.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=1)
print(len(out['inputs']), len(prep))
