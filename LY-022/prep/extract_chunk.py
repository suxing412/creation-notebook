# LY-022 prep: read-only in-memory reassembly of city-visible public ZIP parts; writes only the market chunk + qa/ manifests into prep/inputs.
import hashlib,io,json,sys,zipfile
from pathlib import Path
R=Path('D:/GitHub/creation-notebook-lab/modeling-lab/review-batches/2026-11-04-city-visible')
O=Path(sys.argv[1])
b=b''.join((R/f'city-visible-web-handoff-v1-public.zip.part0{i}').read_bytes() for i in range(1,6))
zs=hashlib.sha256(b).hexdigest(); assert zs=='5895ef23a684a343271183dce1e92e112fb49bba9e03e4372023d1247bb50b69',zs
z=zipfile.ZipFile(io.BytesIO(b)); assert z.testzip() is None
names=z.namelist()
want=[n for n in names if 'market' in n or n.endswith(('chunk-manifest.json','source-node-manifest.json'))]
out={}
for n in want:
    d=z.read(n); p=O/n.replace('/','__'); p.write_bytes(d); out[n]=dict(bytes=len(d),sha256=hashlib.sha256(d).hexdigest(),savedAs=p.name)
json.dump(dict(zipSha256=zs,entries=len(names),extracted=out),open(O/'extract-log.json','w'),indent=1)
print(json.dumps(out,indent=1))
