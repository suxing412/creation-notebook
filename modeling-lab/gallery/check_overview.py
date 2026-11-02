from pathlib import Path
import json,hashlib,subprocess,re,argparse,sys
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
R=Path(__file__).resolve().parent;D=(R/'dist') if (R/'dist').is_dir() else ((R.parent/'dist') if (R.parent/'dist').is_dir() else R.parents[1]/'docs')
args_parser=argparse.ArgumentParser(description='Check overview links, catalog parity and deterministic rebuild; optionally compare a supplied prior static snapshot.')
args_parser.add_argument('--baseline',type=Path,help='Prior static snapshot directory; omitted means preservation is NOT checked.')
args_parser.add_argument('--report',type=Path,default=R/'overview-qa/static-qa.json')
args=args_parser.parse_args()
if args.baseline is not None and not args.baseline.is_dir():args_parser.error('--baseline must be an existing static snapshot directory')
assert D.is_dir(),'Static website directory not found'
args.report.parent.mkdir(parents=True,exist_ok=True)
class Parser(HTMLParser):
 def __init__(self):super().__init__();self.urls=[];self.ids=[];self.works=[];self.picks=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  for k in ('href','src'):
   if k in a:self.urls.append(a[k])
  if 'id' in a:self.ids.append(a['id'])
  if tag=='article' and 'data-id'in a:self.works.append(a['data-id'])
  if tag=='button' and 'data-select'in a:self.picks.append(a['data-select'])
errs=[];refs=0
for p in D.rglob('*.html'):
 z=Parser();z.feed(p.read_text());
 if len(set(z.ids))!=len(z.ids):errs.append([str(p.relative_to(D)),'duplicate id'])
 for u in z.urls:
  a=urlsplit(u)
  if a.scheme or a.netloc:continue
  target=(p.parent/unquote(a.path)).resolve() if a.path else p.resolve()
  if not target.is_relative_to(D.resolve()):errs.append([str(p.relative_to(D)),u,'escape']);continue
  if target.is_dir():target/= 'index.html'
  refs+=1
  if not target.exists():errs.append([str(p.relative_to(D)),u,'missing'])
cat=json.loads((D/'catalog.json').read_text());z=Parser();z.feed((D/'index.html').read_text());ids=[x['id'] for x in cat]
assert len(ids)==len(set(ids))==len(z.works)
assert set(z.works)==set(ids) and sorted(z.picks)==sorted(ids*2)
assert z.works[0]==max(x['id'] for x in cat if x['kind']=='regular') and '开启 3D 目录索引' in (D/'index.html').read_text()
policy=json.loads((R/'manifest.json').read_text())['designPolicy']
historical=[x for x in cat if x['kind']=='fusion']
assert policy['acceptedSpatialWorks']==0,'New spatial design acceptance requires an explicit reviewed schema change'
assert len(historical)==policy['historicalSpatialExperiments']
assert all(x.get('designStatus')=='按新设计要求待重做' for x in historical)
assert all(x['publication']=='verified' for x in historical),'Historical publication must not be conflated with redesign status'
assert '3D空间设计 <span>00</span>' in (D/'index.html').read_text()
assert not errs,errs
before={str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest() for p in D.rglob('*') if p.is_file()}
subprocess.run([sys.executable,str(R/'build.py')],check=True,capture_output=True)
after={str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest() for p in D.rglob('*') if p.is_file()}
assert before==after,'rebuild changed output'
changed=[]
if args.baseline is not None:
 for p in args.baseline.rglob('*'):
  if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()!=after.get(str(p.relative_to(args.baseline))):changed.append(str(p.relative_to(args.baseline)))
 assert set(changed)<= {'index.html','manifest.json'},changed
result={'items':len(ids),'regular':sum(x['kind']=='regular' for x in cat),'fusion':sum(x['kind']=='fusion' for x in cat),'methods':sum(x['kind'] in ('recipe','method') for x in cat),'relativeReferences':refs,'htmlPages':len(list(D.rglob('*.html'))),'rebuildZeroDiff':True,'originalChangedOnly':changed,'assetPreservation':'passed' if args.baseline is not None else 'not_checked: no baseline supplied','browserLimits':'CSS narrow/noJS/noGL only; GPU/iPhone not tested'}
args.report.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
