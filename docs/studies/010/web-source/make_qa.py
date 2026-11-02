"""Temporary browser fixtures. Delete dist/qa before final archive; not a phone emulator."""
from pathlib import Path
import shutil,json
R=Path(__file__).resolve().parents[1];D=R/'dist';Q=D/'qa'
Q.mkdir(exist_ok=True)
(Q/'narrow.html').write_text('''<!doctype html><meta charset="utf-8"><title>010 CSS narrow and noJS fixtures</title><style>body{margin:0;background:#ccc}iframe{height:850px;border:2px solid #888;vertical-align:top}p{font:16px sans-serif}</style><p>320 CSS px / 390 CSS px / 390 CSS px noJS sandbox. Not actual phone.</p><iframe title="320 CSS px" width="335" src="../index.html"></iframe><iframe title="390 CSS px" width="405" src="../index.html"></iframe><iframe title="390 CSS px no script" width="405" sandbox="allow-same-origin" src="../index.html"></iframe>''')
for case in ['cold','image']:
 p=Q/case;p.mkdir(exist_ok=True)
 for f in ['index.html','app.js','reader-state.js','style.css']:shutil.copyfile(D/f,p/f)
 data=json.loads((D/'web-assets/reader-data.json').read_text());(p/'web-assets').mkdir(exist_ok=True)
 if case=='image':(p/'web-assets/reader-data.json').write_text(json.dumps(data,ensure_ascii=False))
 # Restore the metadata fixture later to test actual HTTP recovery on the same URL.
 (Q/(case+'-metadata.json')).write_text(json.dumps(data,ensure_ascii=False))
 for v,a in data['variants'].items():
  for name,b in a['views'].items():
   if case=='cold' or (v=='span' and name=='joint'):continue
   dest=p/b['image'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(D/b['image'],dest)
print(Q)
