# -*- coding: utf-8 -*-
"""写 inputs.json 与 delivery-manifest.json（在 build.py 与 status.json 之后运行）。"""
import hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.normpath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import site_data as SD  # noqa: E402


def fsha(p):
    with open(p, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


ih = json.load(open(os.path.join(PKG, 'qa/inputs-hashes.json'), encoding='utf-8'))
inputs = {
    "seat": "LY-004", "baselineCommit": "bce3211f818ee5a8bef1773539da70695ba37b17",
    "coordinateContract": {"frame": "luoyang-local-schematic-v01", "from": "LY-005/coordinate-contract.json",
                           "sha256": ih['inputs']['predecessors'].get('LY-005/coordinate-contract.json')},
    "repoFilesReadOnly": ih['inputs']['repo'],
    "predecessorFiles": ih['inputs']['predecessors'],
    "externalSources": [dict(id=k, **{kk: vv for kk, vv in v.items()}, local=ih['sources'].get(k)) for k, v in SD.SOURCES.items()],
    "altUpload": SD.ALT_UPLOAD,
    "notObtained": SD.NOT_OBTAINED,
    "nativeSources": "本席位不涉及模型原生源包；无 .blend/源ZIP 需求",
    "units": SD.UNITS,
}
with open(os.path.join(PKG, 'inputs.json'), 'w', encoding='utf-8', newline='\n') as f:
    json.dump(inputs, f, ensure_ascii=False, indent=1); f.write('\n')

CLASS = {'tables': '公开数据（研究表）', 'geometry': '公开数据（约束几何，研究层，不入180安装层）', 'qa': '检查记录', 'preview': '预览（CPU）',
         'source': '源工程（生成器与公有领域快照）'}
files = []
for root, dirs, fs in os.walk(PKG):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for fn in sorted(fs):
        p = os.path.join(root, fn)
        rel = os.path.relpath(p, PKG).replace('\\', '/')
        if rel == 'delivery-manifest.json':
            continue
        top = rel.split('/')[0] if '/' in rel else None
        files.append({"path": rel, "bytes": os.path.getsize(p), "sha256": fsha(p), "class": CLASS.get(top, '交付说明')})
files.sort(key=lambda x: x['path'])
man = {
    "seat": "LY-004", "baselineCommit": "bce3211f818ee5a8bef1773539da70695ba37b17",
    "whitelist": files,
    "publicCandidates": ["tables/site-constraints.json", "geometry/city-south.json", "geometry/north-suburb.json"],
    "notForPublicDocs": ["source/", "qa/", "inputs.json（含本机路径与外部来源SHA）"],
    "dependencies": ["LY-001/status.json", "LY-002/tables/evidence-ledger.json", "LY-002/source/snapshots/*.html", "LY-005/coordinate-contract.json",
                     "LY-005/qa/frames-bce3211.json", "外部：gao2023.pdf（SHA c10cd82d…，版权，不随包）"],
    "installOrder": ["本包不安装任何城市节点。", "若 LY-100 采纳 R-01—R-03：先在 research-unplaced.json / evidence-geometry.json 加列名不落位条目（geometry:null），再考虑把 geometry/*.json 作为研究标记层；北郊与城南必须是两个独立图层。",
                     "LY-079/LY-080 只能交局部包；位置放行需要新的控制点资料，届时重跑本包。"],
    "rollback": "本包无城市写入，无需撤回。",
}
with open(os.path.join(PKG, 'delivery-manifest.json'), 'w', encoding='utf-8', newline='\n') as f:
    json.dump(man, f, ensure_ascii=False, indent=1); f.write('\n')
print(len(files), 'files; total bytes', sum(x['bytes'] for x in files))
