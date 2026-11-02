"""Freeze the standalone web projection with all imported original model bytes."""
from pathlib import Path
import hashlib,json,zipfile
R=Path(__file__).resolve().parents[1];D=R/'dist'
def sha(b):return hashlib.sha256(b).hexdigest()
assert not(D/'qa').exists(),'Remove temporary failure fixtures before freezing'
assert json.loads((R/'review/static-verification.json').read_text())['passed']
assert json.loads((R/'review/model-final-binding.json').read_text())['passed']
for p in D.rglob('*'):
 if p.is_file():
  assert '__pycache__'not in p.parts and p.suffix not in ['.pyc','.log'],p
  if p.suffix in ['.html','.js','.json','.py','.md','.css','.txt']:
   b=p.read_bytes()
   for token in [b'/work'+b'space/',b'/home/'+b'agent/',b'local'+b'host:',b'127.'+b'0.0.1:']:assert token not in b,'private runtime path '+str(p.relative_to(D))
files=[{'path':p.relative_to(D).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}for p in sorted(D.rglob('*'))if p.is_file()and p.name!='WEB-MANIFEST.json']
(D/'WEB-MANIFEST.json').write_text(json.dumps({'study':'010','web_design':'assembly reader','status':'archived locally; public deployment and overview integration are separate','files':files},ensure_ascii=False,indent=2)+'\n')
out=R/'slot-010-model-and-web.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9)as z:
 for p in sorted(D.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(D).as_posix())
with zipfile.ZipFile(out)as z:
 assert z.testzip()is None
 assert set(z.namelist())=={p.relative_to(D).as_posix()for p in D.rglob('*')if p.is_file()}
 for n in z.namelist():assert z.read(n)==(D/n).read_bytes(),n
r={'passed':True,'file':out.name,'bytes':out.stat().st_size,'sha256':sha(out.read_bytes()),'files':len(files)+1,'round_trip':'Every archive entry exactly equals dist bytes; original model parity checked separately','public':False,'overview_integration':'root pending'}
(R/'combined-package-verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False))
