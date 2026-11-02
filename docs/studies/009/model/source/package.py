"""Freeze an explicit, audited model/source/evidence package. Raw failure binaries stay private."""
from pathlib import Path
import hashlib,json,zipfile,shutil
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=ROOT/'delivery'
 if out.exists():raise FileExistsError('Use fresh package directory; do not silently rewrite a frozen delivery')
 out.mkdir()
 chosen=[]
 for folder in ['assets','configs','source','review','vendor']:
  for p in sorted((ROOT/folder).rglob('*')):
   if not p.is_file() or '__pycache__' in p.parts or p.suffix=='.pyc':continue
   rel=p.relative_to(ROOT)
   if folder=='review' and p.suffix in {'.blend','.glb','.blend1'}:continue
   chosen.append(rel)
 chosen += [Path(q) for q in ['README.md','schema.json','parameter-contract.json']]
 for rel in chosen:
  p=ROOT/rel;dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
 # No unrelated environment paths/secrets/third-party images. Scan readable files and raw model containers.
 banned=[b'/'+b'workspace/',b'/'+b'home/agent/',b'appg'+b'prj_']
 for rel in chosen:
  p=out/rel
  if p.suffix.lower() in {'.json','.md','.py','.mjs','.html','.js','.blend','.glb'}:
   data=p.read_bytes()
   assert not any(q in data for q in banned),f'Private environment token in {rel}'
 files=[{'path':str(rel),'bytes':(out/rel).stat().st_size,'sha256':sha(out/rel)} for rel in sorted(chosen)]
 manifest={'study':'009','title':'折光 HINGE','status':'model-complete-web-separate','variants':['hinge','reach','poise'],'pose_ids':['default','folded','extended'],'final_identity_reports':['review/qa-final-identities.json','review/qa-final-run-summary.json'],'reusable_three_module':'source/pose-three.mjs','readme':'README.md','parameter_contract':'parameter-contract.json','files':files,'excludes':['manifest.json itself to avoid self-reference','work and bad-sample binaries','internal logs and unrelated paths'],'gpu_verified':False,'phone_verified':False}
 (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 zpath=ROOT/'hinge-009-model-complete.zip'
 if zpath.exists():raise FileExistsError(zpath)
 with zipfile.ZipFile(zpath,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted(out.rglob('*')):
   if p.is_file():z.write(p,p.relative_to(out))
 with zipfile.ZipFile(zpath) as z:
  assert z.testzip() is None;names=z.namelist();expected={x['path'] for x in files}|{'manifest.json'};assert len(names)==len(set(names)) and set(names)==expected
  for n in names:
   assert not Path(n).is_absolute() and '..' not in Path(n).parts and '\\' not in n
   assert z.read(n)==(out/n).read_bytes()
  for q in files:assert hashlib.sha256(z.read(q['path'])).hexdigest()==q['sha256']
 report={'passed':True,'zip':zpath.name,'zip_bytes':zpath.stat().st_size,'zip_sha256':sha(zpath),'entries':len(names),'manifest_sha256':sha(out/'manifest.json'),'delivery_bytes':sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),'crc_pass':True,'exact_entry_set':True,'all_entry_bytes_and_sha_match':True,'private_path_scan_pass':True}
 (ROOT/'package-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
