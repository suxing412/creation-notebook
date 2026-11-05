"""Read-only: reassemble city-visible ZIP parts in memory (SHA-verified) and
extract only the wuku chunks + manifests into prep/work/. Does not write into the repo."""
import hashlib, io, json, sys, zipfile
from pathlib import Path
SRC = Path(r"D:/GitHub/creation-notebook-lab/modeling-lab/review-batches/2026-11-04-city-visible")
OUT = Path(__file__).resolve().parent / "work"
ZIP_SHA = "5895ef23a684a343271183dce1e92e112fb49bba9e03e4372023d1247bb50b69"
parts = sorted(SRC.glob("city-visible-web-handoff-v1-public.zip.part0*"))
b = b"".join(p.read_bytes() for p in parts)
h = hashlib.sha256(b).hexdigest(); assert h == ZIP_SHA, h
z = zipfile.ZipFile(io.BytesIO(b))
names = z.namelist()
OUT.mkdir(exist_ok=True)
sel = [n for n in names if "wuku" in n.lower() or n.endswith("manifest.json") or n.endswith("chunk-manifest.json")]
res = {}
for n in sel:
    data = z.read(n)
    p = OUT / n.replace("/", "__")
    p.write_bytes(data)
    res[n] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "out": p.name}
print(json.dumps({"zip_sha256": h, "entries": len(names), "extracted": res}, indent=1))
print("\n".join(n for n in names if not n.startswith("chunks/")))
