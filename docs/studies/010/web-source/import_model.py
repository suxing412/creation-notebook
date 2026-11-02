"""Import an approved model ZIP snapshot, preserving every original file byte."""
from pathlib import Path,PurePosixPath
import json,hashlib,zipfile,io,stat,unicodedata,shutil,tempfile,argparse

def sha(b):return hashlib.sha256(b).hexdigest()
def strict(data):
 def pairs(items):
  d={}
  for k,v in items:
   if k in d:raise ValueError('duplicate JSON key')
   d[k]=v
  return d
 return json.loads(data,object_pairs_hook=pairs,parse_constant=lambda s:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
def canonical(s,isd=False):
 if not isinstance(s,str) or not s or '\\' in s or '\x00' in s or unicodedata.normalize('NFC',s)!=s:raise ValueError('invalid path')
 s=s[:-1] if isd and s.endswith('/') else s;p=PurePosixPath(s)
 if p.is_absolute() or '..'in p.parts or p.as_posix()!=s or any(ord(c)<32 or c in ':?#%'for c in s):raise ValueError('noncanonical path')
 if any(x in ['.git','.aws','.codex','__pycache__']for x in p.parts)or p.suffix.lower()in['.pyc','.log','.blend1','.blend2']:raise ValueError('private/temporary entry')
 return s

def load_archive(path,expected):
 raw=Path(path).read_bytes()
 if len(expected)!=64 or sha(raw)!=expected:raise ValueError('archive SHA mismatch')
 entries={};case={}
 with zipfile.ZipFile(io.BytesIO(raw))as z:
  infos=z.infolist()
  if len(infos)>20000 or sum(i.file_size for i in infos)>2*1024**3:raise ValueError('archive limit')
  for i in infos:
   name=canonical(i.filename,i.is_dir())
   if name.casefold()in case:raise ValueError('duplicate/casefold collision')
   case[name.casefold()]=name
   mode=(i.external_attr>>16)&0o170000
   if mode not in (0,stat.S_IFREG,stat.S_IFDIR)or i.flag_bits&1:raise ValueError('unsupported file type/encryption')
   if i.is_dir()and mode==stat.S_IFREG or not i.is_dir()and mode==stat.S_IFDIR:raise ValueError('type mismatch')
   data=z.read(i)
   if i.is_dir():
    if data:raise ValueError('directory payload')
   else:entries[name]=data
 for p in entries:
  if any(x.as_posix().casefold()in{n.casefold()for n in entries}for x in PurePosixPath(p).parents if str(x)!='.'):raise ValueError('prefix collision')
 if 'manifest.json'not in entries:raise ValueError('missing manifest')
 m=strict(entries['manifest.json']);records=m.get('files')
 if not isinstance(records,list):raise ValueError('manifest files missing')
 by={}
 for r in records:
  n=canonical(r.get('path'))
  if n in by or type(r.get('bytes'))is not int or r['bytes']<0 or not isinstance(r.get('sha256'),str):raise ValueError('manifest record malformed')
  by[n]=r
 if set(by)!=set(entries)-{'manifest.json'}:raise ValueError('manifest file set mismatch')
 for p,r in by.items():
  if r['bytes']!=len(entries[p])or r['sha256']!=sha(entries[p]):raise ValueError('entry identity mismatch '+p)
 return entries

def run(path,expected,dest):
 entries=load_archive(path,expected);dest=Path(dest)
 if dest.exists()or dest.is_symlink():raise ValueError('destination must be fresh')
 if any(p.is_symlink()for p in dest.parents):raise ValueError('symlink destination ancestor')
 dest.parent.mkdir(parents=True,exist_ok=True);stage=Path(tempfile.mkdtemp(dir=dest.parent,prefix='010-import-'))
 try:
  for name,b in entries.items():p=stage/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
  for name,b in entries.items():
   if(stage/name).read_bytes()!=b:raise ValueError('write verification failed')
  stage.rename(dest)
 finally:
  if stage.exists():shutil.rmtree(stage)
 report={'passed':True,'scope':'Transfer identity only, not a replacement for geometry QA','source_zip_sha256':expected,'manifest_sha256':sha(entries['manifest.json']),'files':[{'path':p,'bytes':len(b),'sha256':sha(b)}for p,b in sorted(entries.items())]}
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('zip');p.add_argument('--sha256',required=True);p.add_argument('--dest',required=True);p.add_argument('--report',required=True);a=p.parse_args();r=run(a.zip,a.sha256,a.dest);Path(a.report).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print('Imported',len(r['files']),'files')
