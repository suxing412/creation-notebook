"""Static HTML/link/display-data identity checks, not model quality or browser QA."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json,hashlib,re,argparse,math
class Parse(HTMLParser):
 def __init__(self):super().__init__();self.refs=[];self.ids=[];self.images=[];self.h1=0;self.main=0;self.lang=None
 def handle_starttag(self,t,attrs):
  a=dict(attrs)
  if 'id'in a:self.ids.append(a['id'])
  for k in ('src','href'):
   if k in a:self.refs.append((t,k,a[k]))
  if t=='img':self.images.append(a)
  if t=='h1':self.h1+=1
  if t=='main':self.main+=1
  if t=='html':self.lang=a.get('lang')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(root):
 root=Path(root).resolve();checks=[];errors=[];links=[]
 def check(name,ok,detail=None):
  checks.append({'name':name,'passed':bool(ok),'detail':detail})
  if not ok:errors.append(name)
 s=(root/'index.html').read_text();p=Parse();p.feed(s)
 check('single main/h1 and Chinese language',p.h1==p.main==1 and p.lang=='zh-CN');check('unique main IDs',len(set(p.ids))==len(p.ids))
 check('substantive alt and image dimensions',all(len(q.get('alt',''))>10 and 'width'in q and 'height'in q for q in p.images))
 check('no external runtime media or font dependencies',not any(urlsplit(ref).scheme for tag,attr,ref in p.refs if tag in ('img','script','link')))
 check('no candidate placeholders in main',not any(x in s for x in ('图版接入中','待真实配置','尚未冻结','仅审排版','待模型冻结')))
 check('noJS static reading and hidden script controls','<noscript>'in s and 'static-images'in s and 'data-controls hidden'in s)
 pages={}
 for f in root.rglob('*.html'):
  q=Parse();q.feed(f.read_text());pages[f.resolve()]=q
 for f,q in pages.items():
  for tag,attr,ref in q.refs:
   u=urlsplit(ref)
   if u.scheme or ref.startswith('//'):continue
   dest=(f.parent/unquote(u.path)).resolve() if u.path else f;item={'from':f.relative_to(root).as_posix(),'ref':ref}
   if not dest.is_relative_to(root):item['scope']='parent gallery integration';links.append(item);continue
   ok=dest.exists();item['exists']=ok;links.append(item)
   if not ok:errors.append('Missing '+item['from']+' → '+ref)
   elif u.fragment and dest in pages and u.fragment not in pages[dest].ids:errors.append('Missing anchor '+ref)
 data=json.loads((root/'web-assets/plate-data.json').read_text());check('exact three display variants',set(data['variants'])=={'veil','horizon','fold'})
 for k,d in data['variants'].items():
  info_path=root/'assets'/k/'model-info.json';i=json.loads(info_path.read_text());c=i['config'];g=i['construction']
  check(k+' metadata source hash',d['source_info_sha256']==sha(info_path));check(k+' actual GLB hash',d['source_glb_sha256']==sha(root/'assets'/k/'model.glb'))
  expected={'width':f'{c["width"]*1000:.0f} mm','height':f'{c["height"]*1000:.0f} mm','thickness':f'{c["thickness"]*1000:.1f} mm','hole_count':str(g['hole_count'])};check(k+' nominal values exactly derived',d['stats']==expected)
  check(k+' exact main view set',set(d['images'])=={'beauty','hole-detail','top'})
  for view,rel in d['images'].items():check(k+' '+view+' image exists',(root/rel).is_file())
  check(k+' preserved final report identity',(root/d['identity_report']).is_file())
  native_path=root/d['source_native_report'];native=json.loads(native_path.read_text());bound=min(x['conservative_polyline_lower_bound_m'] for x in native['ligament_sampling']['records']);comparison={'bbox_mm':i['dimensions_mm'],'nominal_curve_angle_degrees':c['curve_angle_degrees'],'analytic_footprint_ratio':g['surface_open_area_ratio'],'mouth_polyline_lower_bound_m':bound,'lower_bound_display_mm':math.floor(bound*100000)/100}
  check(k+' current native report SHA',sha(native_path)==d['source_native_report_sha256'])
  check(k+' comparison values and conservative floor rounding',d['comparison']==comparison)
  check(k+' bound displayed in static noJS body',f'≥ {comparison["lower_bound_display_mm"]:.2f} mm' in s)

 css=(root/'style.css').read_text();js=(root/'app.js').read_text()
 check('44px native button targets','min-height:44px'in css);check('reduced motion preference','@media(prefers-reduced-motion:reduce)'in css)
 check('no scroll hijack/auto-rotation',not re.search(r'addEventListener\([\"\x27]wheel|setInterval|requestAnimationFrame',js))
 check('separate download-only delivery config','web-delivery.json'in js and (root/'web-delivery.json').is_file())
 colors=[]
 def lum(h):
  v=[int(h[x:x+2],16)/255 for x in (1,3,5)];v=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in v];return sum(x*y for x,y in zip(v,[.2126,.7152,.0722]))
 for name,a,b in [('body','#252720','#e9e7df'),('muted','#62645b','#e9e7df'),('accent','#b34328','#e9e7df'),('dark','#e9e7df','#252720'),('dark-muted','#b4baaa','#252720')]:
  lo,hi=sorted([lum(a),lum(b)]);ratio=(hi+.05)/(lo+.05);colors.append({'name':name,'ratio':round(ratio,3)});check('specified text contrast '+name,ratio>=4.5)
 out=root/'web-review';out.mkdir(exist_ok=True);result={'passed':not errors,'scope':'Authored HTML/CSS, explicit display-data identities and local links. Not full WCAG, native browser, model gates, GPU or manufacturing.','checker_sha256':sha(Path(__file__)),'checks':checks,'specified_color_pairs':colors,'errors':errors}
 (out/'static-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');(out/'link-checks.json').write_text(json.dumps({'passed':not any(e.startswith('Missing')for e in errors),'scope':'Local HTML references; relative gallery exits delegated to parent','links':links,'errors':[e for e in errors if e.startswith('Missing')]},ensure_ascii=False,indent=2)+'\n');return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();r=verify(a.directory);print(json.dumps({'passed':r['passed'],'errors':r['errors']},ensure_ascii=False,indent=2));raise SystemExit(not r['passed'])
