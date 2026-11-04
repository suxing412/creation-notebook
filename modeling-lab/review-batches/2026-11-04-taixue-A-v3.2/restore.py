from pathlib import Path
import hashlib,json,zipfile
R=Path(__file__).resolve().parent;m=json.loads((R/'intake.json').read_text());pieces=[]
for x in m['parts']:
 b=(R/x['file']).read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'];pieces.append(b)
b=b''.join(pieces);assert hashlib.sha256(b).hexdigest()==m['zipSHA256'];p=R/'taixue-A-public-source.zip';p.write_bytes(b)
with zipfile.ZipFile(p)as z:
 assert z.testzip() is None
 for x in json.loads(z.read('manifest.json')):assert hashlib.sha256(z.read(x['path'])).hexdigest()==x['sha256']
print('Restored complete public archive; all member hashes verified.')
