# LY-040 prep: rebuild the split public zip of review batch 2026-11-04-city-visible into a scratch dir and extract
# only the four northeast chunks + manifests; verify each against adapter.json SHA256. Never writes into the lab repo.
# Usage: python -I extract_chunks.py <review-batch-dir> <scratch-out-dir>
import sys, os, glob, zipfile, hashlib, json
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
zp = os.path.join(out, 'handoff.zip')
with open(zp, 'wb') as w:
    for p in sorted(glob.glob(os.path.join(src, 'city-visible-web-handoff-v1-public.zip.part0*'))):
        w.write(open(p, 'rb').read())
adapter = json.load(open(os.path.join(src, 'adapter', 'adapter.json'), encoding='utf-8'))
want = {a['relativePath']: a['sha256'] for a in adapter['assets']
        if any(k in a['relativePath'] for k in ('granary_C_with_ground', 'northeast_C_access', 'wuku_C_with_support'))}
z = zipfile.ZipFile(zp); ok = True
for rel, sha in sorted(want.items()):
    b = z.read(rel); got = hashlib.sha256(b).hexdigest()
    open(os.path.join(out, os.path.basename(rel)), 'wb').write(b)
    print(rel, len(b), got, 'MATCH' if got == sha else 'MISMATCH adapter=' + sha); ok &= got == sha
print('zip sha256', hashlib.sha256(open(zp, 'rb').read()).hexdigest())
sys.exit(0 if ok else 1)
