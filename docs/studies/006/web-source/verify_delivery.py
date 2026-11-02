#!/usr/bin/env python3
"""Local final-distribution file gate: source identity, clean allow-list, HTML references."""
from pathlib import Path
from urllib.parse import urlsplit,unquote
from html.parser import HTMLParser
import json,hashlib,zipfile,sys,argparse
R=Path(__file__).resolve().parents[1];ap=argparse.ArgumentParser();ap.add_argument('--directory');args=ap.parse_args();D=Path(args.directory).resolve() if args.directory else (R/'dist' if (R/'dist').exists() else R);errors=[];records=[]
if not D.exists():raise SystemExit('Run build_preview.py first')
web_files={'index.html','style.css','app.js','design-case.html','WEB-README.md','README.html','recipe-source.zip','WEB-FROZEN-SHA256.json'}
web_files|={'web-source/'+x for x in ['compose.py','diagrams.py','render_reports.py','verify.py','test_app.cjs','test_diagrams.py','verify_delivery.py','freeze.py']}
web_files|={'assets/diagrams/'+x for x in ['folio-profile.svg','folio-small.svg','folio-bend.svg','atlas-profile.svg','atlas-small.svg','spire-profile.svg','spire-small.svg','diagram-evidence.json']}
web_files|={'web-review/'+x for x in ['design-review.html','design-review.md','reference-notes.html','reference-notes.md','browser-qa.html','browser-qa.md','reflection.html','reflection.md','v1-desktop.jpg','v2-desktop.jpg','final-desktop.jpg','mobile-320.jpg','nojs.jpg','image-failure.jpg','image-recovery.jpg','viewer-fallback.jpg','static-checks.json','link-checks.json','unit-checks.json','delivery-files.json','diagram-tests.json','asset-parity.json','browser-checks.json']}
with zipfile.ZipFile(D/'recipe-source.zip') as z:
 source_files={q.filename for q in z.infolist() if not q.is_dir()}
allowed=source_files|web_files
for path in D.rglob('*'):
 if path.is_file():
  rel=path.relative_to(D).as_posix()
  if rel not in allowed:errors.append('Outside explicit source/web delivery set '+rel)
  if any(x in path.parts for x in ['qa','before','__pycache__','work']) or path.suffix in ['.pyc','.log'] or any(x in rel.lower() for x in ['.stdout.','.stderr.','reference-vam-local-only']):errors.append('Forbidden delivery item '+rel)
  if rel not in ['web-review/delivery-files.json','WEB-FROZEN-SHA256.json']:records.append({'path':rel,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
with zipfile.ZipFile(D/'recipe-source.zip') as z:
 for name in z.namelist():
  if name.endswith('/'):continue
  f=D/name
  if not f.is_file():errors.append('Frozen source item absent '+name)
  elif hashlib.sha256(f.read_bytes()).digest()!=hashlib.sha256(z.read(name)).digest():errors.append('Frozen source item changed '+name)
class Links(HTMLParser):
 def __init__(self):super().__init__();self.refs=[];self.ids=[]
 def handle_starttag(self,t,aa):
  a=dict(aa)
  if 'id'in a:self.ids.append(a['id'])
  for k in ['src','href']:
   if k in a:self.refs.append(a[k])
pages={}
for f in D.rglob('*.html'):
 p=Links();p.feed(f.read_text());pages[f.resolve()]=p
for f,p in pages.items():
 for ref in p.refs:
  u=urlsplit(ref)
  if u.scheme or ref.startswith('//'):continue
  target=(f.parent/unquote(u.path)).resolve() if u.path else f
  if not target.is_relative_to(D.resolve()):continue # Integration-owned gallery return.
  if not target.exists():errors.append(f.relative_to(D).as_posix()+' -> missing '+ref)
  elif u.fragment and target in pages and u.fragment not in pages[target].ids:errors.append(f.relative_to(D).as_posix()+' -> missing anchor '+ref)
manifest=json.loads((D/'manifest.json').read_text())
if manifest.get('status')!='frozen-static-validated':errors.append('Model manifest is not frozen-static-validated')
parity=json.loads((D/'web-review/asset-parity.json').read_text())
if parity['source_zip_sha256']!=hashlib.sha256((D/'recipe-source.zip').read_bytes()).hexdigest():errors.append('Source ZIP differs from approved integration identity')
for f in ['index.html','design-case.html']:
 content=(D/f).read_text()
 if f=='index.html' and any(x in content for x in ['非冻结稿','待冻结','待接入','asset-await','pending-download']):errors.append('Incomplete main page')
result={'passed':not errors,'scope':'Exact frozen model ZIP entries plus explicit web file allow-list; unchanged model bytes and local HTML references; parent owns gallery integration','report_and_freeze_inventory_excluded_from_totals':True,'files_count':len(records),'bytes':sum(x['bytes'] for x in records),'errors':errors};(D/'web-review/delivery-files.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2));sys.exit(bool(errors))
