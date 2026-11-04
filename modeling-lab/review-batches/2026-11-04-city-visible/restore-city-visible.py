"""Place this script beside all5 parts, run python restore-city-visible.py.
Only reassembles verified ZIP in this directory; does not modify any website.
ZIP contains47 separately valid GLB chunks. Parts themselves are NOT GLB assets.
"""
from pathlib import Path
import hashlib,json,zipfile
R=Path(__file__).resolve().parent
PARTS=[{'name': 'city-visible-web-handoff-v1-public.zip.part01', 'sha256': 'd3d5eb7263e9f840c5444d46082eb7ced1c8e5488e7fba9b00d1a0fc3f32a9a3', 'bytes': 10485760}, {'name': 'city-visible-web-handoff-v1-public.zip.part02', 'sha256': 'c20213e1eaa6f212f5dbf9cf41482347a26947880119ebba0f13978cd1876703', 'bytes': 10485760}, {'name': 'city-visible-web-handoff-v1-public.zip.part03', 'sha256': '6a468122cb53a36c5fc93652c2c7f7dc13658510ceee955dc8faf0de9fc9105b', 'bytes': 10485760}, {'name': 'city-visible-web-handoff-v1-public.zip.part04', 'sha256': '74f4cd0a08d3f69882cd44dc412efc885d84bf80a39fe0619ae6ff2043d924cb', 'bytes': 10485760}, {'name': 'city-visible-web-handoff-v1-public.zip.part05', 'sha256': 'a8a0331b4408228a23181adcc3d07d8ca17d25cd108b2179b8bf99880331de5f', 'bytes': 4454445}]
ZIP_SHA="5895ef23a684a343271183dce1e92e112fb49bba9e03e4372023d1247bb50b69"
chunks=[]
for item in PARTS:
 b=(R/item['name']).read_bytes()
 assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256'],item['name']
 chunks.append(b)
b=b''.join(chunks);assert hashlib.sha256(b).hexdigest()==ZIP_SHA
p=R/'city-visible-web-handoff-v1-public.zip';p.write_bytes(b)
with zipfile.ZipFile(p)as z:
 assert z.testzip()is None
 m=json.loads(z.read('manifest.json'))
 for r in m:assert hashlib.sha256(z.read(r['path'])).hexdigest()==r['sha256'],r['path']
print('Restored ZIP; CRC and all manifest SHA verified:',p.name)
