"""Build a sanitized complete model-study projection + ZIP. Work stays private.
Does not publish or modify the independent website author's index.
"""
import argparse,hashlib,json,shutil,zipfile,os,re
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
ALLOW_DIRS={'assets','configs','source','review','vendor','viewer'}
ALLOW_FILES={'README.md','schema.json','manifest.json'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def allowed(p):
 rel=p.relative_to(ROOT)
 return p.is_file() and '__pycache__' not in rel.parts and p.suffix not in {'.pyc','.log','.blend1','.blend2'} and (rel.parts[0] in ALLOW_DIRS or str(rel) in ALLOW_FILES) and p.name!='manifest.json'
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--zip',required=True);a=p.parse_args();out=Path(a.output).resolve();archive=Path(a.zip).resolve()
 if out.exists() or archive.exists():raise ValueError('Use new output directory and archive paths')
 if out.is_relative_to(ROOT):raise ValueError('Public projection must be outside source study, avoiding recursive packaging')
 rows=[];files=sorted(q for q in ROOT.rglob('*') if allowed(q))
 for path in files:
  rel=path.relative_to(ROOT)
  if path.suffix in {'.blend','.glb','.png','.json','.md','.html','.css','.js','.mjs','.cjs','.py'}:
   data=path.read_bytes()
   # Source and docs may contain intentional scan patterns, but no concrete private identifiers.
   markers=[]
   if re.search(rb'/workspace/(?:scratch|shared)/[A-Za-z0-9_-]{6,}',data):raise RuntimeError('Concrete private path in '+str(rel))
   if path.suffix in {'.blend','.glb','.png','.json'}:markers+=[b'/workspace/',b'/home/agent/',b'/tmp/',b'file://']
   if any(m in data for m in markers):raise RuntimeError('Private path marker in '+str(rel))
  if path.suffix=='.png':
   im=Image.open(path);im.load()
   if im.info:raise RuntimeError('PNG metadata must be cleaned: '+str(rel))
  purpose=({'assets':'Final native/GLB/photography asset and its bound report','configs':'Reusable finite configuration preset','source':'Executable recipe, validator, packaging or QA source','review':'Review evidence, finite regression report or before/after image','vendor':'Pinned Three.js r180 dependency and license','viewer':'Independent model observation room with static fallback'}.get(rel.parts[0],'Reproduction documentation or parameter schema'))
  rows.append({'path':str(rel),'bytes':path.stat().st_size,'sha256':sha(path),'purpose':purpose})
 out.mkdir(parents=True)
 for row in rows:
  target=out/row['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/row['path'],target)
 manifest={'study':'007','name':'ORISON / 回环','version':'1.0.0','date_utc':'2026-11-01','files':rows,'total_bytes_excluding_manifest':sum(q['bytes'] for q in rows),'contains_source_archive_itself':False,'excluded':['work/**','__pycache__/**','raw logs','bad sample binaries','external reference images'],'unverified':['GPU/material playback','dynamic flicker','physical iPhone/touch','manufacture/stability'],'entrypoints':{'independent_model_viewer':'viewer/index.html','independent_web_design':'index.html supplied separately by the web-design author'},'manifest_does_not_hash_itself':True}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False));(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
 with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for path in sorted(out.rglob('*')):
   if path.is_file():z.write(path,str(path.relative_to(out)))
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None
  for row in rows:assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256']
 print(json.dumps({'directory':out.name,'files':len(rows)+1,'uncompressed_bytes':sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),'manifest_sha256':sha(out/'manifest.json'),'zip':archive.name,'zip_bytes':archive.stat().st_size,'zip_sha256':sha(archive),'zip_crc_and_entry_sha_verified':True},indent=2))
if __name__=='__main__':main()
