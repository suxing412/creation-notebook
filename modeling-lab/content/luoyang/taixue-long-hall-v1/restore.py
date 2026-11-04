from pathlib import Path
import json,hashlib,zipfile
r=Path(__file__).resolve().parent
m=json.loads((r/'archive.json').read_text())
chunks=[]
for p in m['parts']:
 b=(r/p['file']).read_bytes();assert len(b)==p['bytes'] and hashlib.sha256(b).hexdigest()==p['sha256'],p['file'];chunks.append(b)
b=b''.join(chunks);assert len(b)==m['zipBytes'] and hashlib.sha256(b).hexdigest()==m['zipSHA256']
out=r/'source.zip';out.write_bytes(b)
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 manifest=json.loads(z.read('manifest.json'))
 for e in manifest['files']:assert hashlib.sha256(z.read(e['path'])).hexdigest()==e['archiveSHA256'],e['path']
print('Verified source.zip; extract it to a new directory before use.')
