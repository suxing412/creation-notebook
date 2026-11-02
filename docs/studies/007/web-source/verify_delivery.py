"""Exact original model files + explicit webpage allow-set; no permissive directory globs."""
from pathlib import Path
import argparse,json,hashlib,sys,ast,re
sys.dont_write_bytecode=True
WEB_ROOT={'index.html','style.css','app.js','gallery-state.js','design-case.html','model-source.html','WEB-README.md','WEB-README.html','WEB-FROZEN-SHA256.json'}
WEB_SOURCE={'compose.py','project.py','test_projection.py','gallery_pipeline.py','render_reports.py','verify.py','verify_delivery.py','freeze.py','import_model.py','test_import.py','test_gallery.cjs','test_app.cjs','model_lock.py'}
WEB_REPORTS={'design-review.md','design-review.html','pipeline-audit.md','pipeline-audit.html','pipeline-audit.json','reference-notes.md','reference-notes.html','browser-qa.md','browser-qa.html','reflection.md','reflection.html','v1-desktop.jpg','v2-desktop.jpg','final-desktop.jpg','mobile-320.jpg','projection-comparison.jpg','nojs.jpg','image-failure.jpg','image-recovery.jpg','viewer-fallback.jpg','unit-checks.json','app-unit-checks.json','projection-unit-checks.json','import-unit-checks.json','static-checks.json','link-checks.json','asset-parity.json','browser-checks.json','delivery-files.json'}
WEB_ASSETS={'projection-data.json'}|{f'{k}-{v}-projection.png' for k in ('orison','latitude','ascend') for v in ('front','side')}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def has_concrete_private_path(content):
 # A generic privacy-detector prefix or regex pattern is not a concrete path.
 # Do not exempt source files: reject any such prefix followed by real path characters.
 prefixes=('/'+'workspace'+'/', '/'+'home'+'/'+'agent'+'/')
 return any(re.search(re.escape(prefix)+r'[A-Za-z0-9_.~/-]+',content) for prefix in prefixes) or ('/'+'tmp'+'/'+'web007') in content

def privacy_controls():
 w='/'+'workspace'+'/';h='/'+'home'+'/'+'agent'+'/'
 cases=[(w+'scratch/secret',True),(w+'a',True),(h+'data',True),("b'"+w+"'",False),("b'"+h+"'",False),("rb'"+w+r"(?:scratch|shared)/[A-Za-z0-9_-]{6,}'",False)]
 return all(bool(has_concrete_private_path(text))==expected for text,expected in cases)

def verify(root):
 errors=[]
 if not privacy_controls():errors.append('Concrete-path detector positive/negative controls failed')
 parity=json.loads((root/'web-review/asset-parity.json').read_text());model_files={x['path'] for x in parity['files']}
 from import_model import MODEL_DIRS,MODEL_ROOT,validate_manifest
 lock={}
 for node in ast.parse((root/'web-source/model_lock.py').read_text()).body:
  if not isinstance(node,ast.Assign) or len(node.targets)!=1 or not isinstance(node.targets[0],ast.Name):raise ValueError('Invalid generated model lock')
  lock[node.targets[0].id]=ast.literal_eval(node.value)
 entryset=hashlib.sha256(json.dumps(parity['files'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
 if entryset!=lock['APPROVED_ENTRYSET_SHA256'] or parity['manifest_sha256']!=lock['APPROVED_MANIFEST_SHA256'] or parity['source_archive_sha256']!=lock['APPROVED_ARCHIVE_SHA256']:errors.append('Original import identity/entry set differs from approved lock')
 if any(Path(n).parts[0] not in MODEL_DIRS and n not in MODEL_ROOT for n in model_files):errors.append('Model parity expanded outside original model namespace')
 allowed=model_files|WEB_ROOT|{'web-source/'+x for x in WEB_SOURCE}|{'web-review/'+x for x in WEB_REPORTS}|{'web-assets/'+x for x in WEB_ASSETS}
 for x in parity['files']:
  p=root/x['path']
  if not p.is_file() or sha(p)!=x['sha256'] or p.stat().st_size!=x['bytes']:errors.append('Original model entry changed/missing '+x['path'])
 manifest=json.loads((root/'manifest.json').read_text())
 try:validate_manifest({name:(root/name).read_bytes() for name in model_files})
 except Exception as e:errors.append('Original model manifest/identity contract failed: '+str(e))
 if sha(root/'manifest.json')!=parity['manifest_sha256']:errors.append('Approved manifest changed')
 required=(WEB_ROOT-{'WEB-FROZEN-SHA256.json'})|{'web-source/'+x for x in WEB_SOURCE}|{'web-review/'+x for x in WEB_REPORTS-{'viewer-fallback.jpg','delivery-files.json'}}|{'web-assets/'+x for x in WEB_ASSETS}
 for f in sorted(required):
  if not (root/f).is_file():errors.append('Required web entry missing '+f)
 files=[]
 for p in root.rglob('*'):
  if p.is_symlink():errors.append('Symlink forbidden '+p.relative_to(root).as_posix());continue
  if p.is_dir() and any(x in p.relative_to(root).parts for x in ('qa','__qa','__modelqa','before','work','__pycache__')):errors.append('Private/temporary directory '+p.relative_to(root).as_posix())
  if not p.is_file():continue
  rel=p.relative_to(root).as_posix()
  if rel not in allowed:errors.append('Outside exact delivery set '+rel)
  if p.suffix.lower() in {'.zip','.tar','.gz','.tgz','.7z','.rar'}:errors.append('Nested archive excluded '+rel)
  if any(x in p.relative_to(root).parts for x in ('qa','__qa','__modelqa','before','work','__pycache__')) or p.suffix in ('.log','.pyc','.blend1'):errors.append('Private/temporary file '+rel)
  if p.suffix in ('.html','.js','.mjs','.cjs','.css','.md','.json','.py','.txt'):
   content=p.read_text(errors='replace')
   if has_concrete_private_path(content):errors.append('Private absolute path '+rel)
  if rel not in ('WEB-FROZEN-SHA256.json','web-review/delivery-files.json'):files.append({'path':rel,'bytes':p.stat().st_size,'sha256':sha(p)})
 for name in ('static-checks.json','unit-checks.json','app-unit-checks.json','projection-unit-checks.json','import-unit-checks.json','browser-checks.json'):
  q=root/'web-review'/name
  if not q.exists() or not json.loads(q.read_text()).get('passed'):errors.append('Required web test not passed '+name)
 result={'passed':not errors,'privacy_detector_controls_passed':privacy_controls(),'scope':'Exact original model archive entry identity + explicit webpage delivery files; tests remain separately scoped. Gallery integration and hosting are parent-owned.','files_count':len(files),'bytes':sum(x['bytes'] for x in files),'excluded_from_inventory':['WEB-FROZEN-SHA256.json','web-review/delivery-files.json'],'errors':errors,'files':sorted(files,key=lambda x:x['path'])}
 (root/'web-review/delivery-files.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();r=verify(a.directory.resolve());print(json.dumps({k:v for k,v in r.items() if k!='files'},ensure_ascii=False,indent=2));raise SystemExit(not r['passed'])
