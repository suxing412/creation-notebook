# LY-005 writes inputs.json and delivery-manifest.json (after checks.py). python -I write_manifest.py <LY-005 dir>
import json, hashlib, os, glob, sys

B = sys.argv[1].rstrip('/\\') + '/'
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
rel = lambda p: os.path.relpath(p, B).replace(os.sep, '/')
LAB = 'D:/GitHub/creation-notebook-lab/'
fr = json.load(open(B + 'qa/frames-bce3211.json', encoding='utf-8'))
inputs = {
    'seat': 'LY-005', 'baseline': 'bce3211f818ee5a8bef1773539da70695ba37b17',
    'prerequisites': [{'seat': 'LY-001', 'status': '交付完成', 'file': '../LY-001/status.json', 'sha256': sha(B + '../LY-001/status.json'),
                       'cityDataDumpSha256': sha(B + '../LY-001/qa/city-data.dump.json')}],
    'codeRead': [{'path': p, 'sha256Checkout': sha(LAB + p)} for p in [
        'docs/cities/luoyang/city-data.mjs', 'docs/cities/luoyang/city-renderer.mjs', 'docs/cities/luoyang/scene.mjs', 'docs/cities/luoyang/app.mjs',
        'docs/cities/luoyang/progress-assets/yong-city-v1/source.json', 'docs/cities/luoyang/data/west/ground-atomic-contract.json',
        'docs/cities/luoyang/data/west/city-wall-interface.json', 'docs/cities/luoyang/data/far44/preflight-contract.json',
        'docs/cities/luoyang/v1/r01-assets.mjs', 'docs/cities/luoyang/v1/c01-layer.mjs']],
    'glbInputs': [{'asset': k, 'lod': t, 'path': f['path'], 'bytes': f['bytes'], 'sha256': f['sha256'], 'declaredSha256Match': f['shaMatchesDeclared']}
                  for k, v in fr['assets'].items() for t, f in v['files'].items()],
    'nativeSources': '无。私密 .blend/源 ZIP 拿不到，本席位也不需要原生件，全部在公开 GLB 上实测。Blender 往返导出件是从 GLB 重建的 QA 件，不是原件。',
    'newerSnapshotReadOnly': {'commit': 'f28d650dbb1c079027d7c26851a6c0f483c0c647', 'method': 'git show 到 qa/f28d650/，只读',
                              'files': {rel(p): sha(p) for p in sorted(glob.glob(B + 'qa/f28d650/**/*', recursive=True)) if os.path.isfile(p)}},
    'tools': {'blender': 'D:/Blender/blender.exe 5.2.1 LTS（factory-startup，headless）', 'python': 'numpy、PIL；-I 隔离模式', 'node': 'source/dump_city_data.mjs（复制自 LY-001）'},
    'coordinateContract': 'coordinate-contract.json',
}
json.dump(inputs, open(B + 'inputs.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def cls(p):
    if p.startswith('source/'):
        return 'source-tool'
    if p.startswith('qa/'):
        return 'qa-internal'
    if p.startswith('preview/'):
        return 'preview'
    return 'contract'


files = [p for p in sorted(glob.glob(B + '**/*', recursive=True)) if os.path.isfile(p) and '__pycache__' not in p]
entries = []
for p in files:
    r = rel(p)
    if r in ('delivery-manifest.json', 'status.json'):
        continue
    entries.append({'path': r, 'bytes': os.path.getsize(p), 'sha256': sha(p), 'class': cls(r)})
man = {
    'seat': 'LY-005', 'baseline': 'bce3211f818ee5a8bef1773539da70695ba37b17',
    'publicCandidates': ['coordinate-contract.json', 'port-schema.json'],
    'publicNote': '本席位不写公共文件。若要把契约放进 docs，由 LY-100 合并，且只放 publicCandidates；qa/、source/ 里有本机路径，不能进入公共 docs。',
    'whitelist': entries,
    'dependencies': ['LY-001（快照 dump 28ce130c…）'],
    'installOrder': ['不安装：契约类交付，没有模型或城市改动', '下游 LY-006 读 coordinate-contract.json + port-schema.json + qa/ports-bce3211.json 冻结端口归属'],
    'maxSingleGlbBytes': max([e['bytes'] for e in entries if e['path'].endswith('.glb')] or [0]),
}
json.dump(man, open(B + 'delivery-manifest.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('inputs glb', len(inputs['glbInputs']), 'manifest files', len(entries), 'max glb', man['maxSingleGlbBytes'])
