"""Read-only complete model-package manifest, static-link and payload-presence audit.
The web-design author's root index is an explicit integration dependency, not silently passed.
"""
import argparse,json,hashlib
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k in ['href','src'] and v:self.links.append((tag,v))
def main():
 p=argparse.ArgumentParser();p.add_argument('directory');a=p.parse_args();root=Path(a.directory).resolve();manifest=json.loads((root/'manifest.json').read_text());bad=[]
 for q in manifest['files']:
  path=(root/q['path']).resolve()
  if not path.is_relative_to(root) or not path.is_file() or path.stat().st_size!=q['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest()!=q['sha256']:bad.append(q['path'])
 parser=Links();parser.feed((root/'viewer/index.html').read_text());missing=[];integration=[];checked=[]
 for tag,url in parser.links:
  u=urlsplit(url)
  if u.scheme or u.netloc or not u.path:continue
  path=(root/'viewer'/unquote(u.path)).resolve()
  if path==root/'index.html' and not path.exists():integration.append('index.html from independent web-design author');continue
  if not path.is_relative_to(root) or not path.exists():missing.append(url)
  else:checked.append(url)
 payload=[]
 for n in ['orison','latitude','ascend']:
  d=root/'assets'/n;g=json.loads((d/'gate-identity.json').read_text());info=json.loads((d/'model-info.json').read_text());okay=g['passed'] and g['input_sha256']['native']==hashlib.sha256((d/'model.blend').read_bytes()).hexdigest() and g['input_sha256']['glb']==hashlib.sha256((d/'model.glb').read_bytes()).hexdigest() and g['input_sha256']['info']==hashlib.sha256((d/'model-info.json').read_bytes()).hexdigest();payload.append({'variant':n,'final_identity_verified':okay})
 r={'passed':not bad and not missing and all(q['final_identity_verified'] for q in payload),'manifest_files_checked':len(manifest['files']),'manifest_mismatches':bad,'viewer_static_links_checked':len(checked),'missing_internal_links':missing,'explicit_integration_dependencies':integration,'final_assets':payload,'scope':'Model-package bytes and static viewer links only. Independent exhibition website integration has its own manifest/QA. No GPU or physical-device inference.'};print(json.dumps(r,indent=2));raise SystemExit(0 if r['passed'] else 1)
if __name__=='__main__':main()
