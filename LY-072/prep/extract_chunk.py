"""LY-072 prep (read-only on lab repo): reassemble the tracked city-visible handoff ZIP parts in
memory and write ONLY chunks/biyong_C_relationship.glb to <out_dir> (outside the repo).
Verifies ZIP SHA and the chunk SHA against the package's own qa/chunk-manifest.json.
Usage: python -I extract_chunk.py <out_dir>
"""
import hashlib, io, json, sys, zipfile
from pathlib import Path

SRC = Path(r"D:/GitHub/creation-notebook-lab/modeling-lab/review-batches/2026-11-04-city-visible")
ZIP_SHA = "5895ef23a684a343271183dce1e92e112fb49bba9e03e4372023d1247bb50b69"
CHUNK = "chunks/biyong_C_relationship.glb"
CHUNK_SHA = "1bd1c446f26cf5551bbbf71c4948869ab216334e50886e9253535ccd0b78ffa1"

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
parts = sorted(SRC.glob("city-visible-web-handoff-v1-public.zip.part0*"))
blob = b"".join(p.read_bytes() for p in parts)
rec = {"parts": [{"path": str(p).replace("\\", "/"), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in parts],
       "zip_sha256": hashlib.sha256(blob).hexdigest()}
assert rec["zip_sha256"] == ZIP_SHA, rec["zip_sha256"]
z = zipfile.ZipFile(io.BytesIO(blob))
cm = json.loads(z.read("qa/chunk-manifest.json"))
want = [c for c in cm["chunks"] if c["file"] == CHUNK][0]
data = z.read(CHUNK)
s = hashlib.sha256(data).hexdigest()
assert s == want["sha256"] == CHUNK_SHA, s
(out / "biyong_C_relationship.glb").write_bytes(data)
src_nodes = json.loads(z.read("qa/source-node-manifest.json"))
rec["chunk"] = {"path": CHUNK, "sha256": s, "bytes": len(data)}
rec["source_master_sha256"] = src_nodes["source_sha256"]
rec["biyong_source_nodes"] = [n for n in src_nodes["nodes"] if "biyong" in n["source_name"].lower()]
(out / "chunk-extract-record.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps({k: rec[k] for k in ("zip_sha256", "chunk")}, indent=1))
