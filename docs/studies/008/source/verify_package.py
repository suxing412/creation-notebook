"""Read-only exact manifest and final-file identity check. This is not geometry or GPU rerunning."""
import argparse,json,hashlib
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k in ['href','src'] and v:self.links.append(v)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('directory');a=p.parse_args();root=Path(a.directory).resolve();m=json.loads((root/'manifest.json').read_text());fail=[];listed=set()
 for q in m['files']:
  path=(root/q['path']).resolve()
  if q['path'] in listed:fail.append('duplicate:'+q['path'])
  listed.add(q['path'])
  if not path.is_relative_to(root) or not path.is_file() or path.stat().st_size!=q['bytes'] or sha(path)!=q['sha256']:fail.append('entry:'+q['path'])
 actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
 if actual!=listed|{'manifest.json'}:fail.append('exact_entry_set')
 if m.get('manifest_does_not_hash_itself') is not True or m.get('contains_source_archive_itself') is not False:fail.append('self_manifest_contract')
 for variant,rel in m['final_identity_reports'].items():
  r=json.loads((root/rel).read_text())
  if r.get('passed') is not True or r.get('inputs_stable_during_checks') is not True:fail.append('identity:'+variant)
  for key,path in {'native':f'assets/{variant}/model.blend','glb':f'assets/{variant}/model.glb','info':f'assets/{variant}/model-info.json','native_checker':'source/check.py','glb_checker':'source/check_glb.py','recipe':'source/recipe.py','comparison_checker':'source/compare_exports.py'}.items():
   if r['input_sha256'][key]!=sha(root/path):fail.append('identity-sha:'+variant+':'+key)
  if r['wrapper_sha256']!=sha(root/'source/run_gates.py'):fail.append('wrapper:'+variant)
  for kind,q in r['checks'].items():
   if q.get('exit_code')!=0 or any(v is not True for k,v in q.items() if k not in ['exit_code','report']):fail.append('check-bools:'+variant+kind)
   s=json.loads((root/'review'/q['report']).read_text())
   if s.get('passed') is not True or not s.get('run_id'):fail.append('subreport:'+variant+kind)
 parser=Links();parser.feed((root/'viewer/index.html').read_text());dependencies=[]
 for url in parser.links:
  u=urlsplit(url)
  if u.scheme or u.netloc or not u.path:continue
  path=(root/'viewer'/unquote(u.path)).resolve()
  if path==root/'index.html' and not path.exists():dependencies.append('Separate web author index.html');continue
  if not path.is_relative_to(root) or not path.exists():fail.append('link:'+url)
 r={'passed':not fail,'files_checked':len(listed),'failures':fail,'integration_dependencies':sorted(set(dependencies)),'scope':'Exact packaged bytes, identities and static local links only; no rerender, GPU or phone claim.'};print(json.dumps(r,indent=2));raise SystemExit(0 if r['passed'] else 1)
if __name__=='__main__':main()
