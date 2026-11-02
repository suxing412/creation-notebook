"""Classify checked fixed contacts by the documented design intent, not by error suppression."""
from pathlib import Path
import json,collections
r=Path(__file__).resolve().parents[1];d=json.loads((r/'dist/assets/geometry-check.json').read_text());cats=collections.defaultdict(list)
for p in d['bvh_candidates']:
 a,b=p['a'],p['b'];n=a+' '+b
 if 'voussoir' in n or 'cut jamb' in n:c='拱石与门框嵌入墙身／平台'
 elif a.startswith('Instrument') or b.startswith('Instrument'):c='望远镜固定装配与基座落地'
 elif a.startswith('Stair /') or b.startswith('Stair /'):c='护栏立柱脚嵌接踏步／扶手连接'
 elif 'Rock /' in n:c='阶梯／基础／后侧基础脚／抵达平台嵌入开挖岩体'
 elif 'Coping' in n:c='压顶与护墙嵌接'
 else:c='建筑楼板／墙／屋面／基础／阶梯与下平台接缝'
 cats[c].append(p)
out={'candidateObjectPairs':len(d['bvh_candidates']),'categories':[{'name':k,'count':len(v),'pairs':v} for k,v in cats.items()],'notes':'Object-pair labels describe intended assembly relationships, not blanket approval of every local intersection. Visible tread/riser regions require separate checks. Front two footings are contained inside rock and not surface-intersection pairs. BVH is not a complete containment/contact proof. Not a manufacturing fused solid.'};(r/'dist/assets/contact-classification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print([(k,len(v)) for k,v in cats.items()])
