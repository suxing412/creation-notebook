#!/usr/bin/env python3
"""Static and asset provenance checks. These are not browser/AT or manufacturing validation."""
import json,re,hashlib,sys,xml.etree.ElementTree as ET
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
R=Path(__file__).resolve().parents[1];WR=R/'web-review' if (R/'web-review').exists() else R/'review';errors=[];checks=[]
def check(name,condition,detail=None):
 checks.append({'name':name,'passed':bool(condition),'detail':detail})
 if not condition:errors.append(name)
class Parse(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.refs=[];self.img=[];self.h1=0;self.lang=None;self.noscript=0;self.svgs=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id'in a:self.ids.append(a['id'])
  for key in ['src','href']:
   if key in a:self.refs.append((tag,key,a[key]))
  if tag=='img':self.img.append(a)
  if tag=='h1':self.h1+=1
  if tag=='html':self.lang=a.get('lang')
  if tag=='noscript':self.noscript+=1
  if tag=='svg':self.svgs.append(a)
p=Parse();s=(R/'index.html').read_text();p.feed(s)
check('Exactly one main page h1',p.h1==1);check('Unique IDs including inline SVG accessibility labels',len(p.ids)==len(set(p.ids)));check('Chinese language tag',p.lang=='zh-CN');check('All bitmap images have nonempty content-specific alt',all(len(a.get('alt',''))>12 for a in p.img));check('Image intrinsic dimensions reserve space',all(a.get('width') and a.get('height') for a in p.img));check('Inline SVGs have accessible label relationships',all(x.get('role')=='img' and len(x.get('aria-labelledby','').split())==2 and all(i in p.ids for i in x['aria-labelledby'].split()) for x in p.svgs));check('No remote font/image/CDN dependencies',not any(urlsplit(v).scheme in ('http','https') for tag,key,v in p.refs if tag in ('img','script','link')));check('No fake final placeholder',not any(x in s for x in ['非冻结稿','待冻结','待接入','asset-await','pending-download']));check('No-JS core controls hidden until enhancement','class="image-controls" hidden' in s and p.noscript==1)
links=[]
for tag,key,ref in p.refs:
 u=urlsplit(ref)
 if u.scheme or ref.startswith('//'):continue
 dest=(R/unquote(u.path)).resolve() if u.path else R/'index.html'
 if not dest.is_relative_to(R):links.append({'ref':ref,'status':'integration-scope','note':'Return-to-gallery checked by integrating parent'});continue
 ok=dest.exists();links.append({'ref':ref,'exists':ok})
 if not ok:errors.append('Missing '+ref)
 if u.fragment and dest.suffix=='.html' and ok:
  z=Parse();z.feed(dest.read_text());check('Anchor '+ref,u.fragment in z.ids)
evidence=json.loads((R/'assets/diagrams/diagram-evidence.json').read_text());check('All 7 original SVG exports have evidence',len(evidence['records'])==7)
for q in evidence['records']:
 f=R/q['source'];v=R/q['path'];check(q['path']+' source hash',hashlib.sha256(f.read_bytes()).hexdigest()==q['source_sha256']);check(q['path']+' output hash',hashlib.sha256(v.read_bytes()).hexdigest()==q['svg_sha256']);ET.fromstring(v.read_text())
for v in ['folio','atlas','spire']:
 d=json.loads((R/f'assets/{v}/model-info.json').read_text());check(v+' config parity',d['config']==json.loads((R/f'configs/{v}.json').read_text()));check(v+' source units',d['units']=='metres');t=d['config']['thickness']
 for b in d['construction']['bends']:check(v+' bend '+str(b['corner'])+' derived thickness',abs((b['outside_radius_mm']-b['inside_radius_mm'])-t*1000)<1e-9)
css=(R/'style.css').read_text();check('Reduced-motion rule disables smooth scroll','@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}' in css)

def luminance(hex):
 x=[int(hex[i:i+2],16)/255 for i in (1,3,5)];q=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in x];return .2126*q[0]+.7152*q[1]+.0722*q[2]
def contrast(a,b):
 x,y=sorted([luminance(a),luminance(b)]);return (y+.05)/(x+.05)
colors=[]
for name,a,b in [('body','#112c52','#f5f7fa'),('muted','#52627a','#f5f7fa'),('link-blue','#194bd4','#f5f7fa'),('dark-body','#d1dded','#102b50'),('dark-muted','#c1d0e5','#102b50'),('dark-link-hover-focus','#b5cdf9','#102b50')]:
 ratio=contrast(a,b);colors.append({'pair':name,'foreground':a,'background':b,'ratio':round(ratio,3)});check('Specified CSS contrast '+name,ratio>=4.5)
result={'scope':'Static authored-file and selected flat CSS color checks; not full WCAG/browser/AT certification','passed':not errors,'checks':checks,'specified_color_pairs':colors,'errors':errors};(WR/'static-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));(WR/'link-checks.json').write_text(json.dumps({'scope':'Local references in main page; gallery return belongs to integration','refs':links,'missing':[x for x in links if x.get('exists') is False]},ensure_ascii=False,indent=2));print(json.dumps({'checks':len(checks),'errors':errors,'colors':colors},ensure_ascii=False,indent=2));sys.exit(bool(errors))
