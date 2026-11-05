# -*- coding: utf-8 -*-
"""LY-007 近景保留核验（只读，读提交 blob）：
1. city-data.mjs 里每条 nearPath / nearSha256 与 farPath / farSha256：提交中文件是否存在、SHA 是否一致、
   近档与远档是否为不同字节（防「远档冒充近档」）；
2. 资产卡里同一 <stem>-LOD0/1/2 三档：LOD0 是否存在，LOD1/LOD2 是否与 LOD0 字节相同（防「LOD0 复制改名」）；
3. 输出恢复命令（git show <commit>:<path>）。
用法: python -I near_retention.py <LY-007 目录> <lab 仓库> <commit>
"""
import sys, os, re, json, hashlib, subprocess, collections

W, LAB, C = sys.argv[1], sys.argv[2], sys.argv[3]


def show(p):
    r = subprocess.run(['git', '-C', LAB, 'show', f'{C}:{p}'], capture_output=True)
    return r.stdout if r.returncode == 0 else None


src = show('docs/cities/luoyang/city-data.mjs').decode('utf-8')
base = 'docs/cities/luoyang/'
# assetRecords：每条 {"id", "path"（远档/城中档）, "sha256", 可选 "nearPath", "nearSha256"}；按 "id" 切块
blocks = re.split(r'\n  \{\n    "id": ', src)
city, near_far = [], []
for blk in blocks[1:]:
    aid = re.match(r'"([^"]+)"', blk).group(1)
    body = blk.split('\n  }', 1)[0]
    fp = re.search(r'\n    "path": "([^"]+)"', body); fs = re.search(r'\n    "sha256": "([0-9a-f]{64})"', body)
    np_ = re.search(r'"nearPath": "([^"]+)"', body); ns = re.search(r'"nearSha256": "([0-9a-f]{64})"', body)
    rec = {'id': aid}
    for kind, pm, sm in (('far', fp, fs), ('near', np_, ns)):
        if pm and sm:
            b = show(base + pm.group(1))
            act = hashlib.sha256(b).hexdigest() if b else None
            r = dict(id=aid, kind=kind, path=base + pm.group(1), declared_sha256=sm.group(1), exists=b is not None, actual_sha256=act,
                     match=act == sm.group(1), restore=f'git -C <lab> show {C}:{base + pm.group(1)} > <out>')
            city.append(r); rec[kind] = r
    if 'near' in rec and 'far' in rec:
        near_far.append(dict(id=aid, near=rec['near']['path'], far=rec['far']['path'],
                             same_bytes=rec['near']['actual_sha256'] == rec['far']['actual_sha256']))
ls = subprocess.run(['git', '-C', LAB, 'ls-tree', '-r', '--name-only', C], capture_output=True, text=True).stdout.split()
grp = collections.defaultdict(dict)
for p in ls:
    m = re.match(r'(.*luoyang.*/[^/]+?)-LOD([012])\.glb$', p)
    if m:
        grp[m.group(1)][int(m.group(2))] = p
cards = []
for stem, tiers in sorted(grp.items()):
    sh = {k: hashlib.sha256(show(v)).hexdigest() for k, v in tiers.items()}
    cards.append(dict(stem=stem, tiers=sorted(tiers), has_LOD0=0 in tiers,
                      lod1_equals_lod0=(sh.get(1) == sh.get(0)) if 0 in sh and 1 in sh else None,
                      lod2_equals_lod0=(sh.get(2) == sh.get(0)) if 0 in sh and 2 in sh else None,
                      sha256={f'LOD{k}': v for k, v in sh.items()}))
summ = dict(commit=C, city_refs=len(city), city_refs_match=sum(r['match'] for r in city),
            near_refs=sum(r['kind'] == 'near' for r in city), near_far_pairs=len(near_far),
            near_far_same_bytes=[x for x in near_far if x['same_bytes']],
            tier_stems=len(cards), stems_without_LOD0=[c['stem'] for c in cards if not c['has_LOD0']],
            stems_with_tier_copy_of_LOD0=[c['stem'] for c in cards if c['lod1_equals_lod0'] or c['lod2_equals_lod0']])
json.dump(dict(summary=summ, city=city, near_far=near_far, card_tiers=cards), open(os.path.join(W, 'qa', 'near-retention.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(json.dumps(summ, ensure_ascii=False, indent=1))
