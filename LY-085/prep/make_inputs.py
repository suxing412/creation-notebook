# LY-085 prep: write inputs.json (full SHA256 of every input + whether/where the city loads it). Read-only on the lab repo.
#   python -I make_inputs.py <lab_root> <out.json>
import sys, json, hashlib, glob, io, zipfile
from pathlib import Path
LAB = Path(sys.argv[1]); OUT = Path(sys.argv[2]); D = LAB / 'docs'; C = D / 'cities/luoyang'
HERE = Path(__file__).resolve().parent


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


L = 'docs/cities/luoyang/'
rows = [
    # ---- city ground actually loaded (terrain chapter only) ----
    (L + 'assets/ground-atomic/network-ground-stitched.glb', 'city ground; contains C_stitch_primary = Pingcheng south road (6 m, north end local y=-60.45)',
     'conditional: only when the terrain chapter is opened (node initial=false)',
     'city-data.mjs:430-449 asset, :3555-3576 node initial=false, :4027-4042 chapter terrain loadNodeIds; city-renderer.mjs:221 initial filter, :594-603 focusChapter adds loadNodeIds; atomic check v1/ground-atomic.mjs + data/west/ground-atomic-contract.json (archived v1/west-layer.mjs:35,40)'),
    (L + 'assets/ground-atomic/retained.glb', 'city ground (x480-780); no hit near either gate', 'conditional: terrain chapter', 'city-data.mjs:450-469, :3582-3603, :4027-4042'),
    (L + 'assets/ground-atomic/south.glb', 'city ground (x486-710); no hit near either gate', 'conditional: terrain chapter', 'city-data.mjs:470-489, :3609-3630, :4027-4042'),
    (L + 'assets/ground-atomic/D08.glb', 'city ground, node translation [580,0,-960]; no hit near either gate', 'conditional: terrain chapter', 'city-data.mjs:490-509, :3636-3657, :4027-4042'),
    (L + 'data/west/ground-atomic-contract.json', 'atomic rule: the 3 nodes of network-ground-stitched load together; modeRestriction 6m; a link must be a separate node, never a re-export of this file', 'fetched by archived v1 layers only', 'v1/west-layer.mjs:40, v1/road-layer.mjs:19'),
    # ---- walls (contact/obstacle check only) ----
    (L + 'assets/city-wall/A/wall-04.glb', 'east of Kaiyang; 0 cells in outer approach window', 'yes (initial=true)', 'city-data.mjs:250-269 asset, :3312 node; city-renderer.mjs:221'),
    (L + 'assets/city-wall/A/wall-05.glb', 'between the gates; 0 cells in either outer approach window', 'yes (initial=true)', 'city-data.mjs:270-289, :3339; city-renderer.mjs:221'),
    (L + 'assets/city-wall/A/wall-06.glb', 'west of Pingcheng; 0 cells in outer approach window', 'yes (initial=true)', 'city-data.mjs:290-309, :3366; city-renderer.mjs:221'),
    # ---- gates ----
    ('docs/library/models/m-luoyang-pingcheng-gate/files/pingcheng-P-LOD0.glb', 'Pingcheng gate near; side passages x+-[6.12,9.68], centre closed; outer face y=-6.353', 'no (card only)', 'docs/library/models/m-luoyang-pingcheng-gate/'),
    (L + 'progress-assets/north13-gates/luoyang-pingcheng-gate-study-v1/models/pingcheng-P-LOD1.glb', 'Pingcheng gate mid', 'no (metadata in city-data only)', 'city-data.mjs:1042'),
    (L + 'progress-assets/north13-gates/luoyang-pingcheng-gate-study-v1/models/pingcheng-P-LOD2.glb', 'Pingcheng gate far', 'no (metadata only)', 'city-data.mjs:1025'),
    (L + 'progress-assets/flat/study-north13-pingcheng-P-c8ab88f4b326.glb', 'only Pingcheng file the city fetches, in local-study view (cityPlacement=null)', 'local-study view only, not in city space', 'city-data.mjs:1001-1049 asset, :4340 researchModel; city-renderer.mjs:645-660 focusResearchModel'),
    ('docs/library/models/m-luoyang-pingcheng-gate/files/pingcheng-ground-LOD0.glb', 'Pingcheng gate ground strips+patches; outer edge y=-10, support x[-8.8,-3.1]+[2.92,8.78]; top local 0.042', 'no (card only)', 'LY-016 owner'),
    ('docs/library/models/m-luoyang-pingcheng-gate/files/pingcheng-ground-LOD1.glb', 'same, mid', 'no', 'card'),
    ('docs/library/models/m-luoyang-pingcheng-gate/files/pingcheng-ground-LOD2.glb', 'same, far', 'no', 'card'),
    ('docs/library/models/m-luoyang-kaiyang-gate/files/kaiyang-K-LOD0.glb', 'Kaiyang gate near; 3 open passages x[-9.28,-5.92],[-2.48,2.48],[5.92,9.28]; outer face y=-6.311', 'no (card only)', 'docs/library/models/m-luoyang-kaiyang-gate/'),
    (L + 'progress-assets/north13-gates/luoyang-kaiyang-gate-study-v1/models/kaiyang-K-LOD1.glb', 'Kaiyang gate mid', 'no (metadata only)', 'city-data.mjs:748'),
    (L + 'progress-assets/north13-gates/luoyang-kaiyang-gate-study-v1/models/kaiyang-K-LOD2.glb', 'Kaiyang gate far', 'no (metadata only)', 'city-data.mjs:731'),
    (L + 'progress-assets/flat/study-north13-kaiyang-K-94693c58dd63.glb', 'only Kaiyang file the city fetches, local-study view', 'local-study view only', 'city-data.mjs:707-755, :4178; city-renderer.mjs:645-660'),
    ('docs/library/models/m-luoyang-kaiyang-gate/files/kaiyang-ground-LOD0.glb', 'Kaiyang three test strips; outer edge y=-7', 'no (card only)', 'card'),
    ('docs/library/models/m-luoyang-kaiyang-gate/files/kaiyang-ground-LOD1.glb', 'same, mid', 'no', 'card'),
    ('docs/library/models/m-luoyang-kaiyang-gate/files/kaiyang-ground-LOD2.glb', 'same, far', 'no', 'card'),
    # ---- placement / plans ----
    (L + 'progress-assets/north13-gates/source.json', 'gate placements (origin, rotation_z_rad), activation=false for both', 'no (sourceContract link text only)', 'city-data.mjs:726, :1020 sourceContract; app.mjs:93-96 link'),
    (L + 'data/west/road-plan.json', 'road_pingcheng_south_link_B_C_6 (1622.081,-73.712)->(1612.245,-1224.49) 6 m; cut gate_pingcheng_B 43.1 m "no new gateway crossing"', 'archived v1 road layer only', 'v1/road-layer.mjs:17'),
    (L + 'data/west/road-preconstraints.json', 'road_pingcheng_south_link_B = C_corridor_trial, no surveyed centreline/width; forbid north extension through South Palace', 'link only', 'v1/road-layer.mjs:12'),
    (L + 'data/west/city-wall-constraints.json', 'gate B points vs C projections (Pingcheng 17.36 m, Kaiyang 9.31 m); no moat added this round', 'link only', 'v1/wall-layer.mjs:15'),
    (L + 'city-data.mjs', 'city manifest (read only)', 'yes', 'docs/cities/luoyang/index.html -> app.mjs'),
    (L + 'p-luoyang.asset.json', 'project card (read only)', 'n/a', ''),
]
out = []
for rel, role, loaded, where in rows:
    p = LAB / rel
    out.append({'path': rel, 'sha256': sha(p), 'bytes': p.stat().st_size, 'role': role, 'loadedInCity': loaded, 'loaderCode': where})
# mother-1e8c4d city-visible handoff (undeployed) - ZIP parts in the lab repo, inner files read in memory
zdir = LAB / 'modeling-lab/review-batches/2026-11-04-city-visible'
parts = sorted(glob.glob(str(zdir / 'city-visible-web-handoff-v1-public.zip.part*')))
blob = b''.join(Path(x).read_bytes() for x in parts)
z = zipfile.ZipFile(io.BytesIO(blob))
mz = {'path': 'modeling-lab/review-batches/2026-11-04-city-visible/city-visible-web-handoff-v1-public.zip.part01-05 (concatenated)',
      'sha256': hashlib.sha256(blob).hexdigest(), 'bytes': len(blob), 'parts': [{'name': Path(x).name, 'sha256': sha(x)} for x in parts],
      'role': 'undeployed mother city-C032-entry-LOD0.blend 1e8c4d2c... visible set', 'loadedInCity': 'no (not deployed)', 'loaderCode': 'none', 'members': []}
for n, role in (('chunks/C_ground_network__C_stitch_primary.glb', 'same Pingcheng road but continuous to local y=+13.25 (through the closed centre lane); south of docs end identical (max dz 2e-5 m); REUSE SOURCE for y[-60.45,-6.353]'),
                ('chunks/C_gate_local_ground.glb', 'pingcheng/kaiyang/yong gate trial grounds (= card ground LOD0)'),
                ('chunks/city_gate_kaiyang-K.glb', 'Kaiyang placed in mother (earth 144 tris incl. terminal adapters); nearest road 372 m'),
                ('chunks/lingtai_C_with_east_access.glb', 'Lingtai + C_access_A touching Pingcheng road at y=-1041.8 (968 m south of docs end) - out of scope, not counted'),
                ('chunks/taixue_C_with_support.glb', 'Taixue isolated support patch, 702 m from Kaiyang port, 724 m from road - unconnected'),
                ('chunks/biyong_C_relationship.glb', 'Biyong relationship, >=487 m from road - unconnected')):
    b = z.read(n)
    mz['members'].append({'name': n, 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b), 'role': role})
out.append(mz)
res = {'seat': 'LY-085', 'baseline_main': 'bce3211f818ee5a8bef1773539da70695ba37b17', 'frame': 'Blender world = glTF (x,-z,y); gate local via source.json T=Translation(origin)@RotZ(rot); local -y = outer/south',
       'inputs': out,
       'prepScripts': {n: sha(HERE / n) for n in ('measure_south_ends.py', 'measure_gap_details.py', 'measure_mother_chunk.py', 'route_whatif.py', 'measure_mother_ritual.py', 'city_nodes_near_gates.mjs', 'make_inputs.py')},
       'prepResults': {n: sha(HERE / n) for n in ('measure-out.json', 'detail-out.json', 'mother-chunk-out.json', 'route-whatif-out.json', 'mother-ritual-out.json', 'city-nodes-out.json')},
       'notInRepo': ['mother city-C032-entry-LOD0.blend 1e8c4d2c... (README: excluded from the handoff)', 'base eabb2a90... / overlay 660cdf37... (gate placement bases)',
                     'network-ground-stitched generator/native source', 'gate-ground source pack (generator, 3114-sample checker)']}
OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding='utf-8'); print('INPUTS_OK', len(out))
