"""Freeze explicit delivery file set only after the native and code QA finish."""
from pathlib import Path
import json,hashlib,zipfile,shutil,argparse
R=Path(__file__).resolve().parents[1];D=R/'dist'
def sha(b):return hashlib.sha256(b).hexdigest()
def freeze():
 if(D/'__qa').exists():raise ValueError('Remove temporary browser QA harness before freezing')
 for p in D.rglob('*'):
  if p.is_file()and(p.suffix in['.log','.pyc','.blend1']or any(x in['.git','__pycache__']for x in p.parts)):raise ValueError('Private/temporary file in delivery '+str(p))
 required=['web-review/native-checks.json','web-review/verification.json','web-review/model-parity.json']
 for p in required:
  if not(D/p).is_file():raise ValueError('Missing final report '+p)
 for p in ['web-review/verification.json','web-review/model-parity.json']:
  if json.loads((D/p).read_text())['passed']is not True:raise ValueError('Final gate not passed')
 paths=[p for p in sorted(D.rglob('*'))if p.is_file()and p.name not in['WEB-FROZEN.json','delivery-contract.json']]
 records=[{'path':p.relative_to(D).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}for p in paths]
 (D/'WEB-FROZEN.json').write_text(json.dumps({'study':'009','scope':'Model + independent webpage, not GPU/device certification','files':records},ensure_ascii=False,indent=2)+'\n')
 (D/'delivery-contract.json').write_text(json.dumps({'series':'009','kind':'regular','entry':'index.html','model_prefix':'model/','model_bytes_preserved':True,'gpu_verified':False,'phone_verified':False,'download_config':'web-delivery.json','frozen_manifest':'WEB-FROZEN.json'},ensure_ascii=False,indent=2)+'\n')
 zpath=R/'hinge-009-model-and-web.zip'
 with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED,compresslevel=9)as z:
  for p in sorted(D.rglob('*')):
   if p.is_file():z.write(p,p.relative_to(D).as_posix())
 with zipfile.ZipFile(zpath)as z:
  names=z.namelist();assert len(names)==len(set(names));assert z.testzip()is None
  for n in names:assert z.read(n)==(D/n).read_bytes()
 report={'passed':True,'zip_name':zpath.name,'bytes':zpath.stat().st_size,'sha256':sha(zpath.read_bytes()),'entries':len(names),'frozen_sha256':sha((D/'WEB-FROZEN.json').read_bytes())}
 (R/'combined-package-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':freeze()
