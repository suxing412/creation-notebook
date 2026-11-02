"""Explicit public whitelist. Work, bad binaries, staging folders, credentials and logs are never copied."""
from pathlib import Path
import json,zipfile,hashlib,re
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files=[]
for name in ['README.md','config.schema.json','manifest.json','view.html','viewer.js','viewer.css']:files.append(R/name)
files += sorted(p for p in (R/'configs').glob('*.json'))
files += sorted(p for p in (R/'source').iterdir() if p.is_file() and p.suffix in ['.py','.mjs','.cjs'])
files += sorted(p for p in (R/'vendor').rglob('*') if p.is_file())
asset_names=['model.blend','model.glb','scene.blend','config.json','model-info.json','validation.json','glb-validation.json','section-measurements.json','beauty.png','front.png','side.png','top.png','rear.png','bend-detail.png','contact-detail.png']
for name in ['atlas','folio','spire']:
 for f in asset_names:files.append(R/'assets'/name/f)
files += sorted(p for p in (R/'review').iterdir() if p.is_file() and p.suffix in ['.md','.json','.png'] and p.name not in ['delivery-files.json','archive-verification.json'])
for name in ['README.md','beauty.png','side.png','bend-detail.png','config.json','model-info.json','recipe-before.py','generate-before.py']:files.append(R/'review/first-version'/name)
assert len(files)==len(set(files))
for p in files:
 assert p.is_file(),str(p);data=p.read_bytes()
 # Generic rejected path-marker literals inside source scanners/docs are not user-secret paths.
 if p.suffix in ['.blend','.glb','.png','.json','.md','.html','.js','.css'] and 'vendor' not in p.parts:
  assert not re.search(rb'/workspace/(scratch|shared)/|/home/agent/|/tmp/[A-Za-z0-9_-]+',data),'Private path marker in '+str(p.relative_to(R))
records=[{'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files];delivery=R/'review/delivery-files.json';delivery.write_text(json.dumps({'files':records,'count':len(records),'policy':'explicit asset paths + known source/vendor + review text/images only; no work/staging or rejected binary models'},indent=2));files.append(delivery)
out=R/'recipe-source.zip'
with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in files:z.write(p,str(p.relative_to(R)))
with zipfile.ZipFile(out) as z:
 assert len(z.namelist())==len(files);assert z.testzip() is None
 for p in files:assert z.read(str(p.relative_to(R)))==p.read_bytes()
report={'archive':'recipe-source.zip','bytes':out.stat().st_size,'sha256':sha(out),'file_count':len(files),'zip_crc_passed':True,'all_entries_byte_equal_to_whitelist_sources':True,'excluded':['work/','all staging directories','first-version .blend/.glb/scene.blend','logs','__pycache__'],'externally_published':False};(R/'review/archive-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
