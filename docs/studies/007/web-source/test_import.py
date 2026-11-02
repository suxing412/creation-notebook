"""Isolated import failure tests. Never writes the production directory."""
from pathlib import Path
import tempfile,zipfile,json,hashlib,argparse
import sys
sys.dont_write_bytecode=True
import import_model

def run(out):
 cases=[]
 with tempfile.TemporaryDirectory(prefix='007-import-test-') as td:
  root=Path(td);dest=root/'dist';dest.mkdir();(dest/'sentinel').write_text('preserve me')
  def archive(name,entries):
   entries=dict(entries)
   if entries.get('manifest.json')=='AUTO':
    records=[{'path':n,'bytes':len(b.encode() if isinstance(b,str) else b),'sha256':hashlib.sha256(b.encode() if isinstance(b,str) else b).hexdigest()} for n,b in sorted(entries.items()) if n!='manifest.json']
    entries['manifest.json']=json.dumps({'study':'007','version':'1.0.0','manifest_does_not_hash_itself':True,'contains_source_archive_itself':False,'files':records})
   p=root/name
   with zipfile.ZipFile(p,'w',compression=zipfile.ZIP_STORED) as z:
    for n,b in entries.items():z.writestr(n,b)
   return p
  valid={'manifest.json':'AUTO','README.md':'Fixture','viewer/index.html':'<title>fixture only</title>'}
  assets=[]
  for key in ('orison','latitude','ascend'):
   identities={}
   for field,name in [('native','model.blend'),('glb','model.glb'),('info','model-info.json')]:
    payload='tiny fixture '+key+' '+field;valid['assets/'+key+'/'+name]=payload;identities[field]=hashlib.sha256(payload.encode()).hexdigest()
   assets.append({'variant':key,'passed':True,'report_identities_current':True,'input_sha256':identities})
  valid['review/gate-final-asset-identity.json']=json.dumps({'passed':True,'assets':assets})
  good=archive('good.zip',valid)
  def reject(name,p,sha):
   before=(dest/'sentinel').read_bytes()
   try:import_model.run(p,sha,dest)
   except Exception:pass
   else:raise RuntimeError('Invalid archive accepted '+name)
   if (dest/'sentinel').read_bytes()!=before:raise RuntimeError('Import changed previous target '+name)
   cases.append({'name':name,'rejected':True,'previous_target_preserved':True})
  reject('unapproved ZIP hash',good,'0'*64)
  unsafe=archive('unsafe.zip',{**valid,'../escape':'bad'});reject('parent path traversal',unsafe,hashlib.sha256(unsafe.read_bytes()).hexdigest())
  private=archive('private.zip',{**valid,'work/stdout.log':'bad'});reject('raw log entry',private,hashlib.sha256(private.read_bytes()).hexdigest())
  alias=archive('alias.zip',{**valid,'./manifest.json':json.dumps({'status':'draft'})});reject('dot path alias cannot overwrite checked manifest',alias,hashlib.sha256(alias.read_bytes()).hexdigest())
  collision=archive('web-collision.zip',{**valid,'web-source/pretend.py':'bad'});reject('model package cannot occupy web namespace',collision,hashlib.sha256(collision.read_bytes()).hexdigest())
  emptyqa=archive('empty-qa.zip',{**valid,'review/qa/':''});reject('empty QA directory rejected',emptyqa,hashlib.sha256(emptyqa.read_bytes()).hexdigest())
  nested=archive('nested.zip',{**valid,'source/entire-model-copy.zip':'not duplicated'});reject('nested archive in otherwise valid model namespace',nested,hashlib.sha256(nested.read_bytes()).hexdigest())
  incomplete=archive('incomplete.zip',{'README.md':'missing'});reject('required model files missing',incomplete,hashlib.sha256(incomplete.read_bytes()).hexdigest())
  draft=archive('draft.zip',{**valid,'manifest.json':json.dumps({'status':'draft'})});reject('unsupported model manifest contract',draft,hashlib.sha256(draft.read_bytes()).hexdigest())
  broken=root/'bad-crc.zip';b=bytearray(good.read_bytes());idx=b.index(b'Fixture');b[idx]=ord('X');broken.write_bytes(b);reject('CRC corruption after supplied ZIP hash matches',broken,hashlib.sha256(b).hexdigest())
  identity_path='review/gate-final-asset-identity.json'
  top_string=archive('identity-top-string.zip',{**valid,identity_path:json.dumps({'passed':'false','assets':assets})});reject('identity report passed must be boolean true',top_string,hashlib.sha256(top_string.read_bytes()).hexdigest())
  for field in ('passed','report_identities_current'):
   bad_assets=json.loads(json.dumps(assets));bad_assets[0][field]='false'
   bad_identity=archive('identity-string-'+field+'.zip',{**valid,identity_path:json.dumps({'passed':True,'assets':bad_assets})})
   reject('identity asset '+field+' must be boolean true',bad_identity,hashlib.sha256(bad_identity.read_bytes()).hexdigest())
  duplicate=archive('identity-duplicate-variant.zip',{**valid,identity_path:json.dumps({'passed':True,'assets':assets+[dict(assets[0])]})});reject('identity variants must be exactly three unique entries',duplicate,hashlib.sha256(duplicate.read_bytes()).hexdigest())
  snapshot=archive('snapshot.zip',valid);snapshot_bytes=snapshot.read_bytes();replacement=archive('replacement.zip',{**valid,'README.md':'changed after hash'}).read_bytes()
  original_open=import_model.zipfile.ZipFile
  def swapped_open(source,*args,**kwargs):
   snapshot.write_bytes(replacement)
   return original_open(source,*args,**kwargs)
  isolated=root/'snapshot-dest'
  try:
   import_model.zipfile.ZipFile=swapped_open
   import_model.run(snapshot,hashlib.sha256(snapshot_bytes).hexdigest(),isolated)
  finally:import_model.zipfile.ZipFile=original_open
  if (isolated/'README.md').read_text()!='Fixture':raise RuntimeError('Hashed bytes differed from consumed ZIP bytes')
  cases.append({'name':'disk ZIP replacement after hash cannot change consumed snapshot','passed':True})
  import_model.run(good,hashlib.sha256(good.read_bytes()).hexdigest(),dest)
  if (dest/'sentinel').exists() or not (dest/'viewer/index.html').exists():raise RuntimeError('Valid replace did not replace target')
  cases.append({'name':'valid tiny fixture commits after all checks','passed':True})
 report={'passed':True,'source_sha256':hashlib.sha256(Path(import_model.__file__).read_bytes()).hexdigest(),'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'Isolated tiny ZIP fixtures, including interrupted import preservation; not final model quality or browser verification.','count':len(cases),'cases':cases}
 if out:out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2));return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path);a=p.parse_args();run(a.output)
