"""Make temporary browser-only fixtures; delete __qa before delivery verification.
Uses final source bytes and assets, never changes original model files.
"""
from pathlib import Path
import argparse,json,shutil
p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();r=a.directory.resolve();qa=r/'__qa'
if qa.exists():shutil.rmtree(qa)
qa.mkdir()
for name,sandbox in [('mobile',''),('nojs',' sandbox="allow-same-origin"')]:
 w=320 if name=='mobile' else 1080
 (qa/(name+'.html')).write_text(f'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>008 {name} browser fixture</title><style>body{{margin:0;background:#bbb;font:12px system-ui}}p{{margin:8px 18px}}iframe{{display:block;border:0;width:{w}px;height:900px;margin:0 18px;background:#e9e7df}}</style><p>008 · {"320 CSS宽度；非实体手机" if name=="mobile" else "浏览器sandbox不允许运行脚本；不是全局浏览器设置"}</p><iframe title="008 {name}" id="specimen" src="../index.html"{sandbox}></iframe></html>')
for name in ['failure','initial-failure']:
 d=qa/name;d.mkdir();(d/'web-assets').mkdir()
 s=(r/'index.html').read_text()
 # Every relative HTML asset or link is rebased; actual app.js itself remains unmodified.
 from html import escape
 import re
 s=re.sub(r'(src|href)="(?!https?://|#)([^"]+)"',lambda m:m.group(1)+'="../../'+m.group(2)+'"',s)
 if name=='initial-failure':s=s.replace('src="../../assets/veil/beauty-wide.png"','src="absent-initial.png"')
 (d/'index.html').write_text(s)
 data=json.loads((r/'web-assets/plate-data.json').read_text())
 for variant,entry in data['variants'].items():
  entry['images']={k:'../../'+v for k,v in entry['images'].items()}
 if name=='failure':data['variants']['horizon']['images']['beauty']='recoverable-horizon.png'
 (d/'web-assets/plate-data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 shutil.copyfile(r/'web-delivery.json',d/'web-delivery.json')
print('Temporary __qa fixtures created; must be removed before freeze')
