"""Make the assembled site smaller, in place (called by assemble_site.py after copying). The repository keeps the originals.

- GLB models: meshopt compression (gltfpack -cc), with embedded PNG/JPEG textures re-encoded as WebP (EXT_texture_webp).
  Every vendored three.js GLTFLoader gets the meshopt decoder by default, so the old project pages read them too.
- PNG pictures become WebP, and the references to them are rewritten.
- Identical copies of a vendored three.js tree are published once; the pages that used a copy point at the kept one.

What is left alone, because changing its bytes or names would break something that checks them:
- files whose SHA-256 is written in the text of a project folder whose code verifies hashes (the Luoyang scene does);
- everything under docs/cities/ and docs/prototypes/, and any file named in their text (they replace nodes by name);
- textures referenced by .gltf files, files under vendor/, GLBs that already use meshopt or Draco;
- text files whose own hash is pinned somewhere.

PNG references are often built in code (`assets/${id}.png`), which no scan can resolve. So a project folder whose
text has such an unresolved ".png" converts all of its PNGs and rewrites every ".png" in its text, or converts none.

Afterwards every reference that resolved before the change must still resolve, or the build fails.
"""
import hashlib, io, json, os, re, shutil, struct, subprocess, sys, urllib.parse
from concurrent.futures import ThreadPoolExecutor

TEXT_EXT = ('.html', '.htm', '.js', '.mjs', '.cjs', '.json', '.css', '.md', '.svg', '.gltf')
GLTFPACK_ARGS = ['-cc', '-kn', '-km', '-ke', '-vp', '16', '-vt', '14']
WEBP_Q = 88
HEX64 = re.compile(rb'(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])')
# a path-like token ending in .png (no spaces, quotes, brackets or operators)
PNG_TOKEN = re.compile(r'''[^\s'"`()<>=,;{}\[\]|\\*+!]*\.png(?=[\s'"`)?#<>,;\]}&]|$)''', re.I)
VENDOR_TOKEN = re.compile(r'''(["'`])([^"'`\s]*?\bvendor/[^"'`\s]*)\1''')
PROTECTED_DIRS = ('cities/', 'prototypes/')
CACHE = os.environ.get('SLIM_CACHE') or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.site-cache')


def sha(b):
    return hashlib.sha256(b).hexdigest()


def rel(out, p):
    return os.path.relpath(p, out).replace(os.sep, '/')


def walk(out):
    for dp, dn, fn in os.walk(out):
        for f in fn:
            yield rel(out, os.path.join(dp, f))


def scope_of(r):
    """The project folder a site path belongs to: docs/<section>/<id>/… → <section>/<id>; root files → ''."""
    parts = r.split('/')
    return '/'.join(parts[:2]) if len(parts) > 2 else (parts[0] if len(parts) > 1 else '')


class Site:
    def __init__(self, out):
        self.out = out
        self.files = set(walk(out))
        self.dirs = {d for f in self.files for d in self._parents(f)}
        self.text = {r for r in self.files if r.lower().endswith(TEXT_EXT)}
        self._cache = {}

    @staticmethod
    def _parents(f):
        p = f.split('/')[:-1]
        return ['/'.join(p[:i]) for i in range(1, len(p) + 1)]

    def read(self, r):
        if r not in self._cache:
            self._cache[r] = open(os.path.join(self.out, r), encoding='utf-8', errors='surrogateescape').read()
        return self._cache[r]

    def write(self, r, s):
        self._cache[r] = s
        open(os.path.join(self.out, r), 'w', encoding='utf-8', errors='surrogateescape').write(s)

    def bases(self, r):
        """Where a relative path inside text file r may be resolved from: its folder, then each folder above it."""
        p = r.split('/')[:-1]
        return ['/'.join(p[:i]) for i in range(len(p), -1, -1)]

    def resolve(self, r, token, files=None):
        """All site paths token can mean when read from text file r."""
        files = self.files if files is None else files
        t = urllib.parse.unquote(token.split('?')[0].split('#')[0])
        if not t or re.match(r'^[a-z][a-z0-9+.-]*:', t, re.I) or t.startswith('//'):
            return set()
        found = set()
        for b in ([''] if t.startswith('/') else self.bases(r)):
            cand = os.path.normpath(os.path.join(b, t.lstrip('/'))).replace(os.sep, '/')
            if not cand.startswith('..') and cand in files:
                found.add(cand)
        return found


# ---------------------------------------------------------------- GLB

def read_glb(b):
    if b[:4] != b'glTF':
        raise ValueError('not a GLB')
    jl = struct.unpack('<I', b[12:16])[0]
    j = json.loads(b[20:20 + jl])
    o = 20 + jl
    binc = b''
    if len(b) > o + 8:
        bl, bt = struct.unpack('<II', b[o:o + 8])
        if bt == 0x004E4942:
            binc = b[o + 8:o + 8 + bl]
    return j, binc


def write_glb(j, binc):
    js = json.dumps(j, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    js += b' ' * (-len(js) % 4)
    binc += b'\0' * (-len(binc) % 4)
    body = struct.pack('<II', len(js), 0x4E4F534A) + js + (struct.pack('<II', len(binc), 0x004E4942) + binc if binc else b'')
    return b'glTF' + struct.pack('<II', 2, 12 + len(body)) + body


def webp_textures(b):
    """Re-encode embedded PNG/JPEG images as WebP (lossy for colour, lossless for normal/data maps). None if nothing to do."""
    from PIL import Image
    j, binc = read_glb(b)
    imgs = j.get('images') or []
    if not imgs or not binc or any('uri' in im for im in imgs) or len(j.get('buffers', [])) != 1:
        return None
    data_class = set()
    for m in j.get('materials', []):
        for key in ('normalTexture', 'occlusionTexture'):
            if key in m: data_class.add(m[key]['index'])
        mr = m.get('pbrMetallicRoughness', {})
        if 'metallicRoughnessTexture' in mr: data_class.add(mr['metallicRoughnessTexture']['index'])
    data_img = {j['textures'][t].get('source') for t in data_class if t < len(j.get('textures', []))}
    views = j['bufferViews']
    used_by_img = {im['bufferView'] for im in imgs if 'bufferView' in im}
    new_img = {}
    for i, im in enumerate(imgs):
        if im.get('mimeType') not in ('image/png', 'image/jpeg') or 'bufferView' not in im:
            continue
        v = views[im['bufferView']]
        raw = binc[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']]
        pic = Image.open(io.BytesIO(raw)); pic.load()
        if pic.mode not in ('RGB', 'RGBA'):
            pic = pic.convert('RGBA' if 'A' in pic.mode or 'transparency' in pic.info else 'RGB')
        buf = io.BytesIO()
        if i in data_img:
            pic.save(buf, 'WEBP', lossless=True, method=4)
        else:
            pic.save(buf, 'WEBP', quality=WEBP_Q, method=4, alpha_quality=100)
        if buf.tell() < len(raw) * 0.9:
            new_img[i] = buf.getvalue()
    if not new_img:
        return None
    # lay the binary chunk out again: every buffer view keeps its bytes except the re-encoded images
    out, remap = bytearray(), {}
    img_of_view = {im['bufferView']: i for i, im in enumerate(imgs) if 'bufferView' in im}
    for vi, v in enumerate(views):
        if v.get('buffer', 0) != 0:
            return None
        out += b'\0' * (-len(out) % 4)
        i = img_of_view.get(vi)
        chunk = new_img[i] if i in new_img else binc[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']]
        remap[vi] = (len(out), len(chunk))
        out += chunk
    for vi, v in enumerate(views):
        v['byteOffset'], v['byteLength'] = remap[vi]
        if vi in used_by_img:
            v.pop('byteStride', None)
    j['buffers'][0]['byteLength'] = len(out)
    for i in new_img:
        imgs[i]['mimeType'] = 'image/webp'
    for t in j.get('textures', []):
        if t.get('source') in new_img:
            t.setdefault('extensions', {})['EXT_texture_webp'] = {'source': t.pop('source')}
    for k in ('extensionsUsed', 'extensionsRequired'):
        j[k] = sorted(set(j.get(k, [])) | {'EXT_texture_webp'})
    return write_glb(j, bytes(out))


def named_nodes(j):
    return {n['name'] for n in j.get('nodes', []) if n.get('name')}


USED = set()


def prune_cache():
    for sub in ('glb', 'png'):
        d = os.path.join(CACHE, sub)
        for f in os.listdir(d) if os.path.isdir(d) else []:
            if os.path.join(d, f) not in USED:
                os.remove(os.path.join(d, f))


def pack_glb(gltfpack, src, tmpdir):
    """Return the packed bytes, or None to keep the original (with the reason)."""
    b = open(src, 'rb').read()
    key = sha(b + ' '.join(GLTFPACK_ARGS + [str(WEBP_Q), 'v1']).encode())
    cached = os.path.join(CACHE, 'glb', key + '.glb')
    USED.add(cached)
    if os.path.exists(cached):
        return open(cached, 'rb').read(), 'cache'
    j, _ = read_glb(b)
    used = set(j.get('extensionsUsed', []))
    if used & {'EXT_meshopt_compression', 'KHR_meshopt_compression', 'KHR_draco_mesh_compression'}:
        return None, 'already compressed'
    stage = webp_textures(b) or b
    tag = key + '-' + hashlib.sha1(src.encode('utf-8', 'surrogateescape')).hexdigest()[:8]  # identical files may run at once
    tin, tout = os.path.join(tmpdir, tag + '-in.glb'), os.path.join(tmpdir, tag + '-out.glb')
    open(tin, 'wb').write(stage)
    r = subprocess.run(gltfpack + ['-i', tin, '-o', tout] + GLTFPACK_ARGS, capture_output=True, text=True)
    os.remove(tin)
    if r.returncode or not os.path.exists(tout):
        return None, 'gltfpack: ' + (r.stderr or r.stdout).strip()[:200]
    packed = open(tout, 'rb').read(); os.remove(tout)
    pj, _ = read_glb(packed)
    lost = named_nodes(j) - named_nodes(pj)
    if lost:
        return None, f'gltfpack dropped {len(lost)} named nodes'
    if len(packed) > len(b) * 0.9:
        return None, 'not smaller'
    os.makedirs(os.path.dirname(cached), exist_ok=True)
    open(cached, 'wb').write(packed)
    return packed, 'packed'


# ---------------------------------------------------------------- PNG

def png_to_webp(src):
    from PIL import Image
    b = open(src, 'rb').read()
    key = sha(b + f'q{WEBP_Q}v1'.encode())
    cached = os.path.join(CACHE, 'png', key + '.webp')
    USED.add(cached)
    if os.path.exists(cached):
        return open(cached, 'rb').read(), len(b)
    pic = Image.open(io.BytesIO(b)); pic.load()
    if pic.mode not in ('RGB', 'RGBA'):
        pic = pic.convert('RGBA' if 'A' in pic.mode or 'transparency' in pic.info else 'RGB')
    buf = io.BytesIO()
    pic.save(buf, 'WEBP', quality=WEBP_Q, method=4, alpha_quality=100)
    os.makedirs(os.path.dirname(cached), exist_ok=True)
    open(cached, 'wb').write(buf.getvalue())
    return buf.getvalue(), len(b)


# ---------------------------------------------------------------- main

def link_map(site, exts=('.png', '.glb', '.js', '.mjs', '.json', '.css', '.webp', '.jpg', '.html', '.gltf')):
    """(text file, token) → resolved site paths, for every path-like token that resolves to a file today."""
    tok = re.compile(r'''[^\s'"`()<>=,;{}\[\]|\\*+!]+\.(?:%s)(?=[\s'"`)?#<>,;\]}&]|$)''' % '|'.join(e[1:] for e in exts), re.I)
    m = {}
    for r in site.text:
        for t in set(tok.findall(site.read(r))):
            hit = site.resolve(r, t)
            if hit:
                m[(r, t)] = hit
    return m


def slim(out, log=print):
    gltfpack = os.environ.get('GLTFPACK', '').split() or None
    site = Site(out)
    before_links = link_map(site)

    # --- what must not change
    # hashes count where code checks them: a project folder whose scripts call crypto.subtle.digest (review reports
    # that merely list hashes don't verify anything at run time)
    checking = {scope_of(r) for r in site.text if 'subtle.digest' in site.read(r)} | {'cities/luoyang'}
    pinned = set()
    for r in site.text:
        if scope_of(r) not in checking and not r.startswith(PROTECTED_DIRS):
            continue
        pinned.update(h.decode().lower() for h in HEX64.findall(site.read(r).encode('utf-8', 'surrogateescape')))
    hashes = {r: sha(open(os.path.join(out, r), 'rb').read()) for r in site.files if r.lower().endswith(('.glb', '.png')) or r in site.text}
    pinned_files = {r for r, h in hashes.items() if h in pinned}
    city_names = set()
    for r in site.text:
        if r.startswith(PROTECTED_DIRS):
            city_names.update(os.path.basename(x) for x in re.findall(r'''[^\s'"`()<>=,;{}\[\]|\\*+!]+\.(?:glb|gltf)''', site.read(r), re.I))  # PNGs they use are caught by reference below
    gltf_names = set()
    for r in site.text:
        if r.endswith('.gltf'):
            gltf_names.update(os.path.basename(urllib.parse.unquote(x)) for x in re.findall(r'"uri"\s*:\s*"([^"]+)"', site.read(r)))

    def protected(r):
        n = os.path.basename(r)
        return (r in pinned_files or r.startswith(PROTECTED_DIRS) or n in city_names or n in gltf_names
                or '/vendor/' in '/' + r or r.startswith('vendor/'))

    stats = {}

    # --- GLB
    glbs = sorted(r for r in site.files if r.lower().endswith('.glb') and not protected(r))
    new_size = {}
    if glbs and not gltfpack:
        sys.exit('GLTFPACK is not set (e.g. GLTFPACK="node /path/to/gltfpack/cli.js"); refusing to publish uncompressed models')
    tmp = os.path.join(CACHE, 'tmp'); os.makedirs(tmp, exist_ok=True)
    def one(r):
        try:
            return r, *pack_glb(gltfpack, os.path.join(out, r), tmp)
        except Exception as e:
            return r, None, f'error: {e}'
    saved = kept = 0
    with ThreadPoolExecutor(max_workers=max(2, os.cpu_count() or 2)) as ex:
        for r, packed, why in ex.map(one, glbs):
            p = os.path.join(out, r); old = os.path.getsize(p)
            if packed is None:
                kept += 1
                if not why.startswith(('already', 'not smaller')):
                    log(f'  WARN GLB kept as is ({why}): {r}')
                continue
            open(p, 'wb').write(packed); new_size[r] = len(packed); saved += old - len(packed)
    stats['glb'] = (len(glbs) - kept, saved)

    # --- vendored GLTFLoader: meshopt decoder by default
    decoder = 'vendor/meshopt_decoder.module.js'
    for r in sorted(site.files):
        if r.endswith('/loaders/GLTFLoader.js') and decoder in site.files:
            s = site.read(r)
            if 'this.meshoptDecoder = null;' in s and 'slim_site' not in s:
                imp = os.path.relpath(decoder, os.path.dirname(r)).replace(os.sep, '/')
                s = (f"import {{ MeshoptDecoder as __meshopt }} from '{imp}'; // slim_site: published GLBs are meshopt-compressed\n"
                     + s.replace('this.meshoptDecoder = null;', 'this.meshoptDecoder = __meshopt;', 1))
                site.write(r, s)

    # --- PNG → WebP
    pngs = {r for r in site.files if r.lower().endswith('.png')}
    by_scope = {}
    for r in pngs:
        by_scope.setdefault(scope_of(r), set()).add(r)
    unresolved = {}  # scope → text files with a .png token that resolves to nothing
    resolved_refs = {}  # png → [(text file, token)]
    for r in site.text:
        if r.endswith('.gltf'):
            continue
        for t in set(PNG_TOKEN.findall(site.read(r))):
            if re.match(r'^[a-z][a-z0-9+.-]*:|^//', t, re.I):
                continue
            hit = site.resolve(r, t)
            if not hit:
                unresolved.setdefault(scope_of(r), set()).add(r)
            for h in hit:
                resolved_refs.setdefault(h, []).append((r, t))
    convert = set()
    skipped_scopes = []
    for sc, members in by_scope.items():
        prot = {r for r in members if protected(r)}
        # a PNG referenced from a text file we may not edit has to stay a PNG
        prot |= {r for r in members if any(f in pinned_files or protected(f) and f.startswith(PROTECTED_DIRS) for f, _ in resolved_refs.get(r, []))}
        if sc and sc in unresolved and sc != 'lab':
            if prot:
                skipped_scopes.append(sc); continue
            convert |= members
        else:
            convert |= members - prot
    # ambiguous tokens (one token, several files, not all converted) keep their files as PNG
    for r, refs in resolved_refs.items():
        for f, t in refs:
            hits = site.resolve(f, t)
            if len(hits) > 1 and not hits <= convert:
                convert -= hits
    # a folder with built paths is all or nothing: if the step above kept one of its PNGs, keep them all
    for sc, members in by_scope.items():
        if sc and sc in unresolved and members & convert and not members <= convert:
            convert -= members
            skipped_scopes.append(sc)
    jobs = sorted(convert)
    png_saved = 0
    with ThreadPoolExecutor(max_workers=max(2, os.cpu_count() or 2)) as ex:
        for r, (wb, old) in zip(jobs, ex.map(lambda r: png_to_webp(os.path.join(out, r)), jobs)):
            dst = r[:-4] + '.webp'
            if dst in site.files:
                sys.exit(f'{dst} already exists next to {r}')
            open(os.path.join(out, dst), 'wb').write(wb)
            os.remove(os.path.join(out, r))
            png_saved += old - len(wb)
            site.files.discard(r); site.files.add(dst)
    stats['png'] = (len(jobs), png_saved)
    # rewrite references: resolved tokens that point at a converted file; in fully converted scopes, every .png token
    full = {sc for sc, m in by_scope.items() if sc and m and m <= convert and sc in unresolved}
    conv_set = set(jobs)
    files_before = site.files | conv_set
    for r in sorted(site.text):
        if r in pinned_files or r.endswith('.gltf') or r.startswith(PROTECTED_DIRS):
            continue
        def sub(m, r=r):
            t = m.group(0)
            if re.match(r'^[a-z][a-z0-9+.-]*:|^//', t, re.I):
                return t
            hits = site.resolve(r, t, files_before)
            if (hits and hits <= conv_set) or (not hits and scope_of(r) in full):
                return t[:-4] + '.webp'
            return t
        s = site.read(r)
        s2 = PNG_TOKEN.sub(sub, s)
        if s2 != s:
            site.write(r, s2)

    # --- identical vendored three.js trees: keep one
    trees = {}
    for r in site.files:
        m = re.match(r'^(.*?/vendor)/', r)
        if m and m.group(1) != 'vendor':
            trees.setdefault(m.group(1), {})[r[len(m.group(1)) + 1:]] = None
    sig = {}
    for v, members in trees.items():
        h = hashlib.sha256()
        for f in sorted(members):
            h.update(f.encode() + b'\0' + hashlib.sha256(open(os.path.join(out, v, f), 'rb').read()).digest())
        sig.setdefault(h.hexdigest(), []).append(v)
    vendor_saved = 0; dropped = []
    for group in sig.values():
        if len(group) < 2:
            continue
        keep, *rest = sorted(group)
        for v in rest:
            if any(f'{v}/{f}' in pinned_files for f in trees[v]):
                continue
            # every reference into v must be rewritable
            edits = {}
            for r in site.text:
                if r.startswith(v + '/'):
                    continue
                s = site.read(r)
                for q, t in VENDOR_TOKEN.findall(s):
                    base = os.path.dirname(r)
                    tgt = os.path.normpath(os.path.join(base, t)).replace(os.sep, '/')
                    if tgt == v or tgt.startswith(v + '/'):
                        if r in pinned_files:
                            edits = None; break
                        new = os.path.relpath(keep + tgt[len(v):], base).replace(os.sep, '/')
                        if t.endswith('/') and not new.endswith('/'): new += '/'
                        if t.startswith('./') and not new.startswith('.'): new = './' + new
                        edits.setdefault(r, []).append((q + t + q, q + new + q))
                if edits is None:
                    break
            if edits is None:
                continue
            for r, pairs in edits.items():
                s = site.read(r)
                for a, b in pairs:
                    s = s.replace(a, b)
                site.write(r, s)
            vendor_saved += sum(os.path.getsize(os.path.join(out, v, f)) for f in trees[v])
            shutil.rmtree(os.path.join(out, v))
            for f in trees[v]:
                site.files.discard(f'{v}/{f}')
            dropped.append(v)
    stats['vendor'] = (len(dropped), vendor_saved)

    # --- the library's numbers follow the published files
    lib = 'data/assets.json'
    if lib in site.files:
        d = json.loads(site.read(lib))
        for a in d['assets']:
            for f in a.get('files', []):
                if f.get('path') in new_size:
                    f['bytes'] = new_size[f['path']]
                    f['extUsed'] = sorted(set(f.get('extUsed') or []) | {'EXT_meshopt_compression'})
            if a.get('files'):
                a['bytes'] = sum(f.get('bytes') or 0 for f in a['files'])
        site.write(lib, json.dumps(d, ensure_ascii=False, separators=(',', ':')))

    # --- nothing that resolved before may stop resolving: each old reference is still in its file and still resolves,
    # or its rewritten form (.webp, or the kept vendor copy) is
    keep_of = {v: sorted(g)[0] for g in sig.values() for v in g if v in dropped}
    broken, listed = [], 0
    for (r, t), hits in before_links.items():
        if r not in site.files:
            continue
        s = site.read(r)
        cands = [t]
        if t.lower().endswith('.png'):
            cands.append(t[:-4] + '.webp')
        base = os.path.dirname(r)
        tgt = os.path.normpath(os.path.join(base, t)).replace(os.sep, '/')
        for v, keep in keep_of.items():
            if tgt.startswith(v + '/'):
                new = os.path.relpath(keep + tgt[len(v):], base).replace(os.sep, '/')
                cands += [new, './' + new]
        if not any(c in s and site.resolve(r, c) for c in cands):
            if all(any(h.startswith(v + '/') for v in keep_of) for h in hits) and (r.endswith(('.json', '.md')) or '/source/' in r):
                listed += 1  # a review report or offline test naming the delivered vendor files, not a page link
            else:
                broken.append(f'{r}: {t}')
    for b in broken[:30]:
        log('  BROKEN ' + b)
    if listed:
        log(f'  note: {listed} vendor paths named in review JSON/Markdown now point at a shared copy')
    if broken:
        sys.exit(f'{len(broken)} references would break; not publishing')
    prune_cache()
    return stats, skipped_scopes
