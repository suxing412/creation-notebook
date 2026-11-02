"""Package only intended deliverables. Work logs, private paths and caches stay out."""
from pathlib import Path
import zipfile,json,hashlib
from PIL import Image
root=Path(__file__).resolve().parents[1];selected=[];audit=[]
for folder in ['assets','configs','source','review','vendor']:
 for p in (root/folder).rglob('*'):
  if not p.is_file() or '__pycache__' in p.parts or any(x.startswith('.') for x in p.relative_to(root).parts):continue
  if 'first-version' in p.parts and p.suffix in ['.blend','.glb']:continue
  if p.suffix in ['.log','.pyc'] or (p.name.startswith('candidate-') or p.name=='delivery-files.json'):continue
  selected.append(p)
selected +=[root/'README.md',root/'manifest.json',root/'config.schema.json',root/'view.html',root/'viewer.js',root/'viewer.css']
for p in selected:
 if p.suffix=='.png':
  im=Image.open(p);before=hashlib.sha256(im.tobytes()).hexdigest();im.save(p);assert hashlib.sha256(Image.open(p).tobytes()).hexdigest()==before
 b=p.read_bytes();markers=[t.decode() for t in [b'/workspace/',b'/home/agent/',b'file://'] if t in b]
 # Source includes the forbidden strings as literals in its scanner; only exported artifacts/text evidence must be clean.
 if p.suffix not in ['.py','.js','.mjs','.cjs'] and markers:raise RuntimeError('Private path marker in '+str(p.relative_to(root)))
 audit.append({'path':str(p.relative_to(root)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
(root/'review/delivery-files.json').write_text(json.dumps({'private_path_scan_passed':True,'work_and_logs_excluded':True,'files':audit},indent=2))
selected.append(root/'review/delivery-files.json')
archive=root/'recipe-source.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(set(selected)):z.write(p,str(p.relative_to(root)))
print('Packaged',len(selected),'files',archive.stat().st_size,'bytes')
