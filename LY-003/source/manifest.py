# -*- coding: utf-8 -*-
"""生成 LY-003/delivery-manifest.json：白名单、大小、SHA256、分类、依赖与安装顺序。只写 LY-003/。"""
import hashlib, json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent
CLASS = {'source': '源工程（生成器/数据，非公共docs）', 'qa': '内部核对报告（不进公共docs）', 'tables': '契约数据（供下游席位与LY-100读取）',
         'preview': '预览（CPU示意图）'}
rows = []
for p in sorted(OUT.rglob('*')):
    if not p.is_file() or p.name == 'delivery-manifest.json' or '__pycache__' in p.parts:
        continue
    rel = p.relative_to(OUT).as_posix()
    b = p.read_bytes()
    top = rel.split('/')[0] if '/' in rel else 'root'
    rows.append({'path': rel, 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest(),
                 'class': CLASS.get(top, '席位说明/状态')})
man = {
    'seat': 'LY-003',
    'lab_commit': 'bce3211f818ee5a8bef1773539da70695ba37b17',
    'whitelist': [r['path'] for r in rows] + ['delivery-manifest.json'],
    'files': rows,
    'public_docs_candidates': [],
    'public_note': '本包没有要进入公共docs的文件；tables/*.json 是给下游席位与LY-100的契约输入，若要上线需LY-100另行改写成公共格式，且不得带私密路径。',
    'models': '无（考据/契约席位，不产出GLB）',
    'depends_on': ['LY-001', 'LY-002'],
    'install_order': ['无安装动作：本包不写城市矩阵、不改 city-data.mjs、不激活任何节点'],
    'consumers': ['LY-039', 'LY-070', 'LY-084', 'LY-086', 'LY-088', 'LY-094'],
    'external_bytes_distributed': False,
}
(OUT / 'delivery-manifest.json').write_text(json.dumps(man, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
print(len(rows), 'files')
