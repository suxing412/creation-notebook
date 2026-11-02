from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json,hashlib,subprocess
R=Path(__file__).resolve().parents[1];D=R/'dist';M=R/'model-stage'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Links(HTMLParser):
 def __init__(self):super().__init__();self.refs=[];self.ids=[];self.images=[]
 def handle_starttag(self,t,a):
  d=dict(a)
  if 'id'in d:self.ids.append(d['id'])
  if t=='img':self.images.append(d)
  for k in ['src','href']:
   if k in d:self.refs.append(d[k])
class FactBlocks(HTMLParser):
 def __init__(self):super().__init__();self.blocks=[];self.active=None;self.tag=None;self.text=''
 def handle_starttag(self,t,a):
  d=dict(a)
  if t=='dl' and 'data-static-facts' in d:self.active={'variant':d['data-static-facts'],'facts':[]};self.blocks.append(self.active)
  if self.active is not None and t in ['dt','dd']:self.tag=t;self.text=''
 def handle_data(self,x):
  if self.tag:self.text+=x
 def handle_endtag(self,t):
  if t==self.tag:
   if t=='dt':self.active['facts'].append({'label':self.text})
   if t=='dd':self.active['facts'][-1]['value']=self.text
   self.tag=None
  if t=='dl':self.active=None
p=Links();p.feed((D/'index.html').read_text());fb=FactBlocks();fb.feed((D/'index.html').read_text());issues=[]
assert [b['variant'] for b in fb.blocks]==['slot','slot','span','rise'],'missing/reordered static variant blocks' 
assert len(p.ids)==len(set(p.ids)),'duplicate ids'
for ref in p.refs:
 u=urlsplit(ref)
 if u.scheme or u.netloc:continue
 if not u.path:
  if u.fragment and u.fragment not in p.ids:issues.append('missing anchor '+ref)
 elif u.path=='../../index.html':pass # root-owner overview integration, not claimed checked here
 elif not (D/unquote(u.path)).is_file():issues.append('missing file '+ref)
for im in p.images:
 if not im.get('alt','').strip():issues.append('missing alt')
originals=[p for p in M.rglob('*')if p.is_file()]
assert {p.relative_to(M).as_posix() for p in originals}=={p.relative_to(D/'model').as_posix() for p in (D/'model').rglob('*') if p.is_file()},'extra or missing original model files'
for src in originals:
 dest=D/'model'/src.relative_to(M)
 if not dest.is_file()or sha(src)!=sha(dest):issues.append('model mismatch '+str(src.relative_to(M)))
for f in ['app.js','reader-state.js','style.css']:
 if sha(R/f)!=sha(D/f):issues.append('web source mismatch '+f)
# Data binding: generated values must equal original records, not a hand-edited metadata layer.
data=json.loads((D/'web-assets/reader-data.json').read_text())
assert set(data['variants'])=={'slot','span','rise'}
for v,a in data['variants'].items():
 source=json.loads((M/f'assets/{v}/model-info.json').read_text());c=source['config'];ac=source['assembly_contract']
 mm=lambda n:f'{n*1000:g}'
 b=source['bounds_m']
 expected=[{'label':'构件','value':f'2 纵轨 + {c["dividers"]} 横隔板'},{'label':'名义板厚 / 槽宽','value':f'{mm(c["thickness"])} / {mm(ac["nominal_slot_width"])} mm'},{'label':'世界外包长 × 宽 × 高','value':' × '.join(f'{(x[1]-x[0])*1000:.2f}' for x in b)+' mm'},{'label':'名义总侧隙','value':mm(ac['nominal_total_lateral_clearance'])+' mm'}]
 assert a['facts']==expected,'metadata facts differ from source '+v
 assert set(a['views'])=={'beauty','exploded','joint'}
 for block in fb.blocks:
  if block['variant']==v:assert block['facts']==expected,'static facts incorrectly bound '+v

 for view,b in a['views'].items():
  filename='joint-exploded' if view=='joint' else view
  assert b['image']==f'model/assets/{v}/{filename}.png'
 assert source['variant']==v and len(source['parts'])==2+c['dividers']
report={'passed':not issues,'issues':issues,'original_model_files':len(originals),'html_images':len(p.images),'html_references':len(p.refs),'external_overview_link':'../../index.html; root integration pending, not checked by this verifier','sha256':{f:sha(D/f)for f in ['index.html','app.js','reader-state.js','style.css','web-assets/reader-data.json']},'scope':'Static links, same-byte complete imported model, generated metadata; not GPU/phone or geometric acceptance'}
(R/'review/static-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False));assert report['passed']
