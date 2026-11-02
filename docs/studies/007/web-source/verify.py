"""Static source/link/provenance checks, not a browser or model-quality substitute."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json,hashlib,re,sys,argparse
class Parse(HTMLParser):
 def __init__(self):super().__init__();self.refs=[];self.ids=[];self.images=[];self.h1=0;self.main=0;self.lang=None
 def handle_starttag(self,t,attrs):
  a=dict(attrs)
  if 'id' in a:self.ids.append(a['id'])
  for k in ('src','href','data-src'):
   if k in a:self.refs.append((t,k,a[k]))
  if t=='img':self.images.append(a)
  if t=='h1':self.h1+=1
  if t=='main':self.main+=1
  if t=='html':self.lang=a.get('lang')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify(root):
 checks=[];errors=[];links=[]
 def check(name,ok,detail=None):
  checks.append({'name':name,'passed':bool(ok),'detail':detail})
  if not ok:errors.append(name)
 s=(root/'index.html').read_text();p=Parse();p.feed(s)
 check('one h1 / one main',p.h1==p.main==1);check('Chinese language',p.lang=='zh-CN');check('no duplicate main IDs',len(p.ids)==len(set(p.ids)))
 check('content-specific nonempty image alt',all(len(i.get('alt',''))>15 for i in p.images));check('image dimensions reserve layout',all('width'in i and 'height'in i for i in p.images))
 check('no external runtime dependencies',not any(urlsplit(r).scheme for t,k,r in p.refs if t in ('img','script','link')))
 check('no candidate placeholder in final main',not any(x in s for x in ['候选','未冻结','不可交付','待接入','worker','待定']))
 check('no-JS core includes all three photo plates','<noscript>'in s and 'static-plates' in s and 'data-controls hidden'in s)
 pages={}
 for f in root.rglob('*.html'):
  pp=Parse();pp.feed(f.read_text());pages[f.resolve()]=pp
 for f,pp in pages.items():
  for t,k,ref in pp.refs:
   u=urlsplit(ref)
   if u.scheme or ref.startswith('//'):continue
   dest=(f.parent/unquote(u.path)).resolve() if u.path else f
   rec={'from':f.relative_to(root).as_posix(),'ref':ref}
   if not dest.is_relative_to(root):rec['scope']='gallery-integration';links.append(rec);continue
   ok=dest.exists();rec['exists']=ok;links.append(rec)
   if not ok:errors.append('Missing '+rec['from']+' → '+ref)
   elif u.fragment and dest in pages and u.fragment not in pages[dest].ids:errors.append('Missing anchor '+ref)
 data=json.loads((root/'web-assets/projection-data.json').read_text());check('six projections, explicit limited scope',len(data['records'])==6 and data['passed'] and 'raster' in data['scope'].lower())
 check('projection generator matches current source',data['generator_sha256']==sha(root/'web-source/project.py'))
 for q in data['records']:
  check(q['file']+' actual GLB hash',q['source_glb_sha256']==sha(root/q['source_glb']))
  check(q['file']+' image hash',q['output_sha256']==sha(root/'web-assets'/q['file']))
  info=root/q['source_glb'].replace('model.glb','model-info.json');check(q['file']+' info hash',q['source_info_sha256']==sha(info))
  check(q['file']+' metric is nonnegative',q['interior_blank_area_cm2']>=0)
  check(q['file']+' world-axis bounds identity',q['native_bounds_max_abs_error_m']<2e-6)
 css=(root/'style.css').read_text();check('reduced motion disables smooth scrolling','@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}'in css)
 check('native 44px photo controls','min-height:44px'in css)
 check('no wheel hijacking or automatic rotation in page',not re.search(r'wheel|setInterval|requestAnimationFrame', (root/'app.js').read_text()))
 def lum(hex):
  v=[int(hex[i:i+2],16)/255 for i in (1,3,5)];q=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in v];return sum(a*b for a,b in zip(q,[.2126,.7152,.0722]))
 colors=[]
 for name,a,b in [('body','#242420','#f4f2ed'),('muted','#62635b','#f4f2ed'),('dark','#f4f2ed','#222620'),('dark-muted','#c0c6b4','#222620'),('dark-hover','#eef0d7','#222620')]:
  lo,hi=sorted([lum(a),lum(b)]);ratio=(hi+.05)/(lo+.05);colors.append({'name':name,'ratio':round(ratio,3)});check('specified text color '+name,ratio>=4.5)
 result={'passed':not errors,'scope':'Authored HTML/CSS, local links and actual source/output identity; not full WCAG, browser, GPU or manufacturing validation.','checks':checks,'specified_color_pairs':colors,'errors':errors}
 out=root/'web-review';out.mkdir(exist_ok=True);(out/'static-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');(out/'link-checks.json').write_text(json.dumps({'scope':'Local HTML refs and data-src; parent validates gallery-relative returns','refs':links,'errors':[e for e in errors if e.startswith('Missing')]},ensure_ascii=False,indent=2)+'\n')
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();r=verify(a.directory.resolve());print(json.dumps({'passed':r['passed'],'checks':len(r['checks']),'errors':r['errors']},ensure_ascii=False,indent=2));raise SystemExit(not r['passed'])
