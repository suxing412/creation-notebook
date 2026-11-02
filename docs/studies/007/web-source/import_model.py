"""Import an approved model ZIP transactionally, after all bytes/CRC/path checks.
The original model manifest/review remain unchanged. No archive is nested into hosted output.
"""
from pathlib import Path,PurePosixPath
import argparse,zipfile,hashlib,json,shutil,tempfile,os,io
ROOT=Path(__file__).resolve().parents[1]
MODEL_DIRS={'assets','review','source','configs','vendor','viewer'}
MODEL_ROOT={'README.md','schema.json','manifest.json'}
def sha(data):return hashlib.sha256(data).hexdigest()
def load_archive(archive,expected):
 raw=archive.read_bytes()
 if sha(raw)!=expected:raise ValueError('Unapproved source ZIP SHA256')
 entries={}
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  for q in z.infolist():
   p=PurePosixPath(q.filename)
   spelling=q.filename[:-1] if q.is_dir() and q.filename.endswith('/') else q.filename
   if spelling!=p.as_posix():raise ValueError('Noncanonical ZIP path '+q.filename)
   if p.parts[0] not in MODEL_DIRS and q.filename not in MODEL_ROOT:raise ValueError('Outside model namespace '+q.filename)
   if p.is_absolute() or '..'in p.parts or '\\'in q.filename or q.filename in entries:raise ValueError('Unsafe/duplicate path')
   if any(x in p.parts for x in ('work','qa','__qa','__modelqa','before','__pycache__')) or p.suffix in ('.log','.pyc'):raise ValueError('Private/bad file in model package '+q.filename)
   if p.suffix.lower() in {'.zip','.tar','.gz','.tgz','.7z','.rar'}:raise ValueError('Nested archive excluded from model import '+q.filename)
   if ((q.external_attr>>16)&0o170000)==0o120000:raise ValueError('Symlink rejected')
   if q.is_dir():continue
   entries[q.filename]=z.read(q) # Entire archive CRC is checked before any target changes.
 if not {'manifest.json','README.md','viewer/index.html'}<=set(entries):raise ValueError('Incomplete model package')
 validate_manifest(entries)
 return entries

def validate_manifest(entries):
 manifest=json.loads(entries['manifest.json'])
 if manifest.get('study')!='007' or manifest.get('version')!='1.0.0' or manifest.get('manifest_does_not_hash_itself') is not True or manifest.get('contains_source_archive_itself') is not False:raise ValueError('Unsupported 007 manifest contract')
 records=manifest.get('files',[])
 if not isinstance(records,list) or len({x['path'] for x in records})!=len(records) or {x['path'] for x in records}!=set(entries)-{'manifest.json'}:raise ValueError('Original manifest file set differs from ZIP')
 for item in records:
  data=entries[item['path']]
  if len(data)!=item['bytes'] or sha(data)!=item['sha256']:raise ValueError('Original manifest bytes/hash mismatch '+item['path'])
 report=json.loads(entries['review/gate-final-asset-identity.json'])
 assets=report.get('assets')
 if report.get('passed') is not True or not isinstance(assets,list) or len(assets)!=3 or any(not isinstance(x,dict) or type(x.get('variant')) is not str for x in assets) or {x['variant'] for x in assets}!={'orison','latitude','ascend'}:raise ValueError('Final model identity evidence missing or variant set is not exactly three unique entries')
 for asset in assets:
  if asset.get('passed') is not True or asset.get('report_identities_current') is not True:raise ValueError('Final model identity not current')
  for key,name in [('native','model.blend'),('glb','model.glb'),('info','model-info.json')]:
   if asset['input_sha256'][key]!=sha(entries['assets/'+asset['variant']+'/'+name]):raise ValueError('Final model input hash mismatch')
 return manifest

def run(archive,expected,dest):
 entries=load_archive(archive,expected)
 # Never preserve candidate model bytes: create a fresh model-only directory.
 temp=Path(tempfile.mkdtemp(prefix='007-import-',dir=dest.parent));backup=dest.with_name(dest.name+'.previous-import')
 try:
  for name,data in entries.items():
   p=temp/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
  report={'passed':True,'scope':'All original ZIP entries were CRC-read and imported byte-for-byte; this verifies transfer identity, not model quality.','source_archive_name':archive.name,'source_archive_sha256':expected,'manifest_sha256':sha(entries['manifest.json']),'files':[{'path':n,'bytes':len(b),'sha256':sha(b)} for n,b in sorted(entries.items())]}
  (temp/'web-review').mkdir(exist_ok=True);(temp/'web-review/asset-parity.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
  (temp/'web-source').mkdir(exist_ok=True)
  lock={'APPROVED_ARCHIVE_SHA256':expected,'APPROVED_MANIFEST_SHA256':report['manifest_sha256'],'APPROVED_ENTRYSET_SHA256':sha(json.dumps(report['files'],sort_keys=True,separators=(',',':')).encode())}
  (temp/'web-source/model_lock.py').write_text('# Generated from the approved original archive; regenerate only through verified reimport.\n'+''.join(k+' = '+repr(v)+'\n' for k,v in lock.items()))
  if backup.exists():raise ValueError('Previous backup exists; resolve it explicitly')
  if dest.exists():dest.rename(backup)
  try:temp.rename(dest)
  except Exception:
   if backup.exists():backup.rename(dest)
   raise
  if backup.exists():shutil.rmtree(backup)
 finally:
  if temp.exists():shutil.rmtree(temp)
 print(json.dumps({'imported':len(entries),'archive_sha256':expected},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('--sha256',required=True);p.add_argument('--dest',type=Path,default=ROOT/'dist');a=p.parse_args();run(a.archive,a.sha256,a.dest)
