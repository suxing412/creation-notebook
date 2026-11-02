from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json,hashlib,math,re
from PIL import Image
R=Path(__file__).resolve().parents[1];D=R/'dist'if(R/'dist/index.html').exists()else R;V=['hinge','reach','poise'];P=['default','folded','extended']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Links(HTMLParser):
 def __init__(self):super().__init__();self.refs=[]
 def handle_starttag(self,t,attrs):
  for k,v in attrs:
   if k in ['href','src']and v:self.refs.append(v)
class TextTree(HTMLParser):
 def __init__(self):super().__init__();self.root={'tag':'root','attrs':{},'children':[]};self.stack=[self.root];self.nodes=[]
 def handle_starttag(self,tag,attrs):
  n={'tag':tag,'attrs':dict(attrs),'children':[]};self.stack[-1]['children'].append(n);self.nodes.append(n)
  if tag not in ['area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr']:self.stack.append(n)
 def handle_endtag(self,tag):
  for i in range(len(self.stack)-1,0,-1):
   if self.stack[i]['tag']==tag:self.stack=self.stack[:i];break
 def handle_data(self,data):self.stack[-1]['children'].append(data)
 def one(self,attr,value):
  ns=[n for n in self.nodes if attr in n['attrs'] and n['attrs'][attr]==value]
  if len(ns)!=1:raise ValueError('expected one HTML '+attr+'='+str(value))
  return ns[0]
def text(n):return ''.join(c if isinstance(c,str)else text(c)for c in n['children'])
def run():
 failures=[];refs=0;pages=0;tree=TextTree();tree.feed((D/'index.html').read_text())
 for f in D.rglob('*.html'):
  if '__qa' in f.parts:continue
  p=Links();p.feed(f.read_text());pages+=1
  for a in p.refs:
   u=urlsplit(a)
   if u.scheme or u.netloc or not u.path:continue
   refs+=1;target=(f.parent/unquote(u.path)).resolve()
   if not target.is_relative_to(D.resolve()):failures.append('escape '+str(f.relative_to(D))+': '+a)
   elif not target.exists():failures.append('missing '+str(f.relative_to(D))+': '+a)
 review=R/'review'if(R/'review/model-parity.json').exists()else R/'web-review';parity=json.loads((review/'model-parity.json').read_text());actual={p.relative_to(D/'model').as_posix():p for p in(D/'model').rglob('*')if p.is_file()};expected={x['path']:x for x in parity['files']}
 if actual.keys()!=expected.keys():failures.append('model entry set changed')
 for n,p in actual.items():
  if n in expected and (p.stat().st_size!=expected[n]['bytes']or sha(p)!=expected[n]['sha256']):failures.append('model byte difference '+n)
 data=json.loads((D/'web-assets/pose-data.json').read_text());cameras=[];observations=[]
 for v in V:
  cfg=json.loads((D/'model/assets'/v/'model-info.json').read_text())['config']
  expected_stats={'arms':f"{cfg['lower_length']*1000:g} / {cfg['upper_length']*1000:g} mm",'base':f"Ø {cfg['base_radius']*2000:g} mm",'head':f"Ø {cfg['head_radius']*2000:g} mm"}
  if data['variants'][v]['stats']!=expected_stats:failures.append('dimension input mismatch '+v)
  if v=='hinge':
   for k,val in expected_stats.items():
    if text(tree.one('data-stat',k))!=val:failures.append('initial HTML stat mismatch '+k)
  for pose in P:
   b=D/'model/assets'/v
   if pose!='default':b=b/'poses'/pose
   info=json.loads((b/'model-info.json').read_text());entry=data['variants'][v]['poses'][pose]
   for k,actualval in [('angles',info['pose']['angles_degrees']),('headCenter',info['pose']['head_center'])]:
    if entry[k]!=actualval:failures.append('numeric mismatch '+v+'/'+pose+'/'+k)
   card=tree.one('id',v+'-'+pose);card_text=text(card);q=entry['angles'];hc=entry['headCenter']
   if f'肩 {q[0]}° · 相对肘 {q[1]}° · 灯头世界角 {q[2]}°'not in card_text or f'{hc[0]*1000:.1f} / {hc[2]*1000:.1f} mm'not in card_text:failures.append('atlas HTML numeric mismatch '+v+'/'+pose)
   if v=='hinge'and pose=='default':
    for i,num in enumerate(q):
     if text(tree.one('data-angle',str(i)))!=f'{num}°':failures.append('initial HTML angle mismatch')
    if text(tree.one('data-center',None))!=f'{hc[0]*1000:.1f} / {hc[2]*1000:.1f} mm':failures.append('initial HTML center mismatch')
   if entry['image']!=(b/'front.png').relative_to(D).as_posix():failures.append('wrong image path '+v+'/'+pose)
   with Image.open(b/'front.png')as im:
    if im.size!=(960,960):failures.append('non-final image size '+v+'/'+pose)
   if info['studio']['samples']!=128:failures.append('non-final samples '+v+'/'+pose)
   cam=info['studio']['views']['front'];cameras.append(cam)
   if cam['location'][0]!=cam['target'][0]or cam['location'][2]!=cam['target'][2]:failures.append('crop projection requires exact horizontal front camera')
   zmin,zmax=info['bounds_m'][2];top=480-(zmax-cam['target'][2])/cam['ortho_scale']*960;bottom=480-(zmin-cam['target'][2])/cam['ortho_scale']*960
   if not 180<=top<=bottom<=900:failures.append('fixed crop cuts model '+v+'/'+pose)
   observations.append({'variant':v,'pose':pose,'info_sha256':sha(b/'model-info.json'),'image_sha256':sha(b/'front.png'),'angles':entry['angles'],'headCenter':entry['headCenter']})
 if any(c!=cameras[0]for c in cameras):failures.append('front camera not fixed across all poses')
 css=(D/'style.css').read_text()
 if '[data-image-frame]{aspect-ratio:4/3;overflow:hidden}'not in css or '.visual [data-image-frame] img{width:100%;height:100%;object-fit:cover;object-position:50% 75%;aspect-ratio:auto}'not in css:failures.append('declared fixed crop CSS changed; reevaluate contract')
 for f in ['app.js','pose-state.js','style.css']:
  if(R/f).read_bytes()!=(D/f).read_bytes():failures.append('authored source/dist drift '+f)
 report={'passed':not failures,'scope':'Static links, preserved model bytes, 9 actual pose metadata/image references and fixed recorded camera. Not browser or GPU verification.','html_pages':pages,'relative_references':refs,'original_files':len(actual),'pose_checks':observations,'failures':failures}
 (review/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 assert not failures,failures
 return report
if __name__=='__main__':print(json.dumps(run(),ensure_ascii=False,indent=2))
