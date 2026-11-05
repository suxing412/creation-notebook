# -*- coding: utf-8 -*-
# LY-006: write inputs.json and delivery-manifest.json (whitelist, size, SHA256, class, install order).
# Usage (from LY-006/): python -I source/write_manifest.py .
import json, os, sys, hashlib, subprocess
W6 = os.path.abspath(sys.argv[1]); WP = os.path.dirname(W6)
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
LAB = 'D:/GitHub/creation-notebook-lab'
lc = subprocess.run(['git', '-C', LAB, 'rev-parse', 'origin/luoyang-content'], capture_output=True, text=True).stdout.strip()
ext = lambda rel: {'path': rel, 'sha256': sha(os.path.join(WP, rel)), 'bytes': os.path.getsize(os.path.join(WP, rel))}
inputs = {
    'seat': 'LY-006', 'baseline': {'repo': LAB, 'commit': 'bce3211f818ee5a8bef1773539da70695ba37b17', 'readOnly': True},
    'predecessors': {'LY-001': [ext('LY-001/status.json'), ext('LY-001/qa/snapshot-ledger.json'), ext('LY-001/qa/city-data.dump.json'), ext('LY-001/qa/family-ledger.json')],
                     'LY-005': [ext('LY-005/status.json'), ext('LY-005/coordinate-contract.json'), ext('LY-005/port-schema.json'), ext('LY-005/qa/ports-bce3211.json')]},
    'taskpool': [ext('TASKPOOL.md'), ext('taskboard.json')],
    'publicSourcePackages (origin/luoyang-content, read with git show; extracted only to the session scratchpad)': {
        'branchHead': lc,
        'luoyang-kaiyang-gate-study-v1 content.zip (part001+002)': {'zipSHA256': 'bad99bb9f5b301b5b6a3450931511caec385df3da8b5ffc5b94b1664eb598c23', 'used': ['qa/source-object-ranges.json', 'city/placement.json', 'city/kaiyang-K-mid-hidden-trial.blend (sha256 75c96a3f1a8bb1d6231e005ed115a0c810f0f81f4ddeb7938ce10e56659558aa, read with Blender 5.2.1 headless)']},
        'luoyang-pingcheng-gate-study-v1 content.zip (part001+002)': {'zipSHA256': '19646f31c10acb3fbc90cbf19c84cdecc7acb40f6b5aec1635a52397958043ac', 'used': ['qa/source-object-ranges.json', 'city/placement.json', 'city/pingcheng-P-mid-hidden-trial.blend (sha256 2d2b74a742d76478681646768760673963a88eedebdb1c5648ebb15cd48aa806)']},
        'city-visible-web-handoff-v1-public.zip (part01..05)': {'zipSHA256': '5895ef23a684a343271183dce1e92e112fb49bba9e03e4372023d1247bb50b69',
                                                             'used': ['chunks/northeast_C_access.glb (58f2f58a464183e20d5489b13902f62f2570573cb8bf96fb237df781027d076e; copied to qa/chunks/)',
                                                                      'chunks/market_frontage_well_routes.glb (0193ebc0cfe200292defd595ff4f4011b2b2d05388d4f53e7b4c3a19a255b4c5; not copied)',
                                                                      'chunks/C_gate_local_ground.glb (6002f5a6dcc6653dc6cf081e77236dbd281e60ab9e88574a91eceb96afb6ceb6; searched for old ramp, not copied)']}},
    'otherSeatPrepReadOnly': [ext('LY-021/prep/out/entry-LOD0-vground.json'), ext('LY-028/prep/out/gap-summary.json'), ext('LY-039/prep/out/measure-ne-approach.json')],
    'otherSeatPrepUse': 'LY-021 opening x-ranges copied as data (qa/frontage-openings.from-LY-021-prep.json); LY-028 canopy rectangles typed into registry_spec CANOPIES; LY-039 values cross-checked against LY-006 own read of the NE chunk. All other prep folders were only read to learn what each seat intends to touch.',
    'labGlbIndex': 'qa/glb-node-index.json: 373 GLB files at bce3211, every SHA equal to the LY-001 ledger (check C7)',
    'nativeSource': 'no private .blend / source ZIP was available or needed; only the public sanitized ZIPs above were read',
    'tools': {'python': sys.version.split()[0], 'blender': 'D:/Blender/blender.exe 5.2.1 (headless, factory startup) for bl_list_objects.py only'},
}
json.dump(inputs, open(os.path.join(W6, 'inputs.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
CLASS = lambda r: ('contract' if r.startswith(('registry/', 'schemas/', 'templates/')) else 'qa' if r.startswith('qa/') else
                   'preview' if r.startswith('preview/') else 'source' if r.startswith('source/') else 'doc')
files = []
for root, ds, fs in os.walk(W6):
    ds[:] = [d for d in ds if d != '__pycache__']
    for f in sorted(fs):
        p = os.path.join(root, f); rel = os.path.relpath(p, W6).replace('\\', '/')
        if rel == 'delivery-manifest.json': continue
        files.append({'path': rel, 'bytes': os.path.getsize(p), 'sha256': sha(p), 'class': CLASS(rel),
                      'public': False})
man = {'seat': 'LY-006', 'baseline': 'bce3211f818ee5a8bef1773539da70695ba37b17', 'registryVersion': 1,
       'whitelist': files, 'totalBytes': sum(f['bytes'] for f in files), 'maxGlbBytes': max([f['bytes'] for f in files if f['path'].endswith('.glb')] or [0]),
       'publicDocsFiles': 'none (nothing in this package goes to docs/; LY-100 only reads registry/ when merging)',
       'dependencies': ['LY-001', 'LY-005'],
       'installOrder': ['1. LY-009 / LY-010 read registry/seats.json + registry/zones.json (sites, frames, zones) when building the task lock and region admission tables',
                        '2. every LY-011..090 seat copies templates/interface.template.json, fills it, and runs source/validate_interface.py against registry/',
                        '3. a seat needing a different zone/port/owner files a registry v2 request; LY-006 (or coordinator) re-runs source/check_registry.py and re-issues all registry files with version 2',
                        '4. LY-100 merges only packages whose interface files pass against the registry version they declare'],
       'recompute': 'see brief.md section 7'}
json.dump(man, open(os.path.join(W6, 'delivery-manifest.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(files), man['totalBytes'])
