import import_model as im
from pathlib import Path
import tempfile,zipfile,io,json,hashlib,stat
checks=[]
def pack(entries,extras=[]):
 records=[{'path':p,'bytes':len(b),'sha256':im.sha(b)}for p,b in entries.items()];allentries={**entries,'manifest.json':json.dumps({'files':records}).encode()};out=io.BytesIO()
 with zipfile.ZipFile(out,'w')as z:
  for p,b in allentries.items():z.writestr(p,b)
  for p,b in extras:z.writestr(p,b)
 return out.getvalue()
def test(name,blob,expected=None,ok=False):
 with tempfile.TemporaryDirectory()as td:
  p=Path(td)/'in.zip';p.write_bytes(blob)
  try:r=im.load_archive(p,expected or im.sha(blob));passed=ok
  except Exception:passed=not ok
  assert passed,name
 checks.append({'name':name,'passed':True})
base={'README.md':b'hi','assets/slot/front.png':b'not image; transfer fixture'}
test('valid exact snapshot',pack(base),ok=True);test('wrong zip digest',pack(base),'0'*64)
for p in ['/etc/evil','../bad','a/../b','a//b','./a','a\\b','a%2fb','a?x','a#x','C:evil','\x00bad','e\u0301','a\x01b','.git/HEAD','cache/x.pyc','logs/debug.log']:
 test('reject '+repr(p),pack({**base,p:b'x'}))
for extra in [[('README.md',b'other')],[('readme.md',b'other')],[('assets',b'file')],[('undeclared',b'file')]]:test('reject duplicate/unlisted '+repr(extra[0][0]),pack(base,extra))
with tempfile.TemporaryDirectory()as td:
 p=Path(td)/'in.zip';b=pack(base);p.write_bytes(b);dest=Path(td)/'stage';r=im.run(p,im.sha(b),dest);assert all((dest/x).read_bytes()==y for x,y in base.items());checks.append({'name':'actual stage bytes exact','passed':True})
 try:im.run(p,im.sha(b),dest);raise AssertionError('overwrote')
 except ValueError:checks.append({'name':'existing stage not overwritten','passed':True})
# Actual ZIP special entries, malformed manifest, and corruption negative controls.
def rawpack(items):
 b=io.BytesIO()
 with zipfile.ZipFile(b,'w')as z:
  for name,data in items:z.writestr(name,data)
 return b.getvalue()
manifest=json.dumps({'files':[{'path':p,'bytes':len(b),'sha256':im.sha(b)}for p,b in base.items()]}).encode()
for name,alter in [('wrong size',lambda m:m['files'][0].update(bytes=999)),('boolean size',lambda m:m['files'][0].update(bytes=True)),('wrong entry SHA',lambda m:m['files'][0].update(sha256='0'*64)),('missing record',lambda m:m['files'].pop()),('duplicate record',lambda m:m['files'].append(m['files'][0])),('undeclared record',lambda m:m['files'].append({'path':'none','bytes':0,'sha256':im.sha(b'')}))]:
 m=json.loads(manifest);alter(m);test(name,rawpack([*base.items(),('manifest.json',json.dumps(m).encode())]))
test('duplicate JSON manifest key',rawpack([*base.items(),('manifest.json',b'{"files":[],"files":[]}')]))
test('nonfinite JSON manifest',rawpack([*base.items(),('manifest.json',b'{"files":NaN}')]))
zi=zipfile.ZipInfo('escape');zi.create_system=3;zi.external_attr=(stat.S_IFLNK|0o777)<<16;test('symlink entry',rawpack([*base.items(),('manifest.json',manifest),(zi,b'../../outside')]))
zi=zipfile.ZipInfo('payload/');test('directory payload',rawpack([*base.items(),('manifest.json',manifest),(zi,b'bad')]))
b=bytearray(pack(base));off=b.find(b'hi');assert off>=0;b[off]=ord('X');test('actual CRC corruption',bytes(b))
report={'passed':True,'scope':'ZIP path/CRC identity and safe fresh import tests; not geometry verification','count':len(checks),'cases':checks};Path(__file__).resolve().parents[1].joinpath('review/import-unit-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(report)
