"""LY-026 prep: re-extract chunks/market_frontage_well_routes.glb from the five read-only ZIP parts
(in memory; never writes into the lab repo). Usage: python -I extract_chunk.py <outdir>"""
import hashlib, io, sys, zipfile
from pathlib import Path
R = Path('D:/GitHub/creation-notebook-lab/modeling-lab/review-batches/2026-11-04-city-visible')
ZIP_SHA = '5895ef23a684a343271183dce1e92e112fb49bba9e03e4372023d1247bb50b69'
CHUNK_SHA = '0193ebc0cfe200292defd595ff4f4011b2b2d05388d4f53e7b4c3a19a255b4c5'
b = b''.join((R / f'city-visible-web-handoff-v1-public.zip.part0{i}').read_bytes() for i in range(1, 6))
assert hashlib.sha256(b).hexdigest() == ZIP_SHA
c = zipfile.ZipFile(io.BytesIO(b)).read('chunks/market_frontage_well_routes.glb')
assert hashlib.sha256(c).hexdigest() == CHUNK_SHA
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
(out / 'market_frontage_well_routes.glb').write_bytes(c)
print('ok', CHUNK_SHA, len(c))
