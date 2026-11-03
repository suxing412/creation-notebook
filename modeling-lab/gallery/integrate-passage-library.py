from pathlib import Path
import json
D=Path(__file__).resolve().parents[2]/'docs'
p=D/'index.html';s=p.read_text();n=json.loads((D/'model-library/registry.json').read_text())['logicalAssets']
import re
s=re.sub(r'可复用模型库 · \d+个模型资产组 ↗',f'可复用模型库 · {n}个模型资产组 ↗',s)
link='<a href="model-library/methods/passage-wfc/">最新方法研究 · 通行接口WFC（未接城） ↗</a>'
if link not in s:s=s.replace('<a id="model-library-entry"',link+'<a id="model-library-entry"',1)
p.write_text(s)
