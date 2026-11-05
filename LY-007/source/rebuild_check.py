# -*- coding: utf-8 -*-
"""比对 round2 复刻件重建结果与样件字节。先跑：
  D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P source/round2/build_round2.LY007.py -- tmp/rebuild
再跑: python -I rebuild_check.py <LY-007 目录>   输出 qa/round2-rebuild.json
"""
import sys, os, json, hashlib
W = sys.argv[1]
h = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
rows = []
for m in ('S84', 'G10'):
    for l in (0, 1, 2):
        f = f'{m}-LOD{l}.glb'
        a, b = os.path.join(W, 'tmp', 'rebuild', f), os.path.join(W, 'models', 'samples', f)
        rows.append(dict(file=f, rebuild_sha256=h(a), sample_sha256=h(b), byte_identical=h(a) == h(b), bytes=os.path.getsize(b)))
res = dict(command='D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P source/round2/build_round2.LY007.py -- tmp/rebuild',
           library='source/lib/ly_style.py sha256 ' + h(os.path.join(W, 'source', 'lib', 'ly_style.py')),
           blender='5.2.1 LTS (hash 9e2066aef7ef)', files=rows, all_identical=all(r['byte_identical'] for r in rows))
json.dump(res, open(os.path.join(W, 'qa', 'round2-rebuild.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(res['all_identical'])
