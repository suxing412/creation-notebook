"""Assemble the published site (used by .github/workflows/pages.yml).

  python -I lab/tools/assemble_site.py [_site]

- docs/ goes to the site root as before, except source files (.blend, source ZIPs and parts, …): those live in the
  GitHub Release listed in docs/asset-spec/source-archive.json, and links to them in HTML pages point there.
- Part-download pages get a note with a direct link to the whole, verified ZIP in the release.
- lab/ (the asset library) goes to the site root and replaces the old docs/index.html homepage; its "../docs/"
  references become root-relative. The old /lab/ pages stay as redirects to the same page at the root.
- Fails if the site would exceed the GitHub Pages size limit, so a too-large site is never half-published.
"""
import json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
DOCS = os.path.join(ROOT, 'docs')
LAB = os.path.join(ROOT, 'lab')
OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, '_site'))
LIMIT = 1_000_000_000  # GitHub Pages: published sites may be no larger than 1 GB
SOURCE = re.compile(r'\.(blend|blend1|zip|part\d{3}|psd|exr|fbx|max|ma|mb|c4d|spp|kra)$', re.I)
ARCH_PATH = os.path.join(DOCS, 'asset-spec', 'source-archive.json')
arch = json.load(open(ARCH_PATH, encoding='utf-8')) if os.path.exists(ARCH_PATH) else {'base': '', 'files': {}, 'joined': {}}
ATTR = re.compile(r'''(\b(?:href|src)\s*=\s*)(["'])([^"'#?]+)([^"']*)\2''', re.I)


def release_url(name):
    return arch['base'] + name


def rewrite_html(rel, text):
    here = os.path.dirname(rel)
    def sub(m):
        val = m.group(3)
        if re.match(r'^[a-z][a-z0-9+.-]*:|^/', val, re.I):
            return m.group(0)
        target = os.path.normpath(os.path.join(here, val)).replace('\\', '/')
        name = arch['files'].get(target)
        return f'{m.group(1)}{m.group(2)}{release_url(name)}{m.group(2)}' if name else m.group(0)
    text = ATTR.sub(sub, text)
    mm = re.search(r'data-archive-manifest\s*=\s*"([^"]+)"', text)
    if mm:
        man = os.path.normpath(os.path.join(here, mm.group(1))).replace('\\', '/')
        name = arch['joined'].get(man)
        if name:
            note = (f'<aside style="margin:0 0 20px;padding:12px 16px;border:1px solid currentColor;line-height:1.8">'
                    f'源包已移到 GitHub Release：<a href="{release_url(name)}"><b>下载完整 ZIP（已按清单校验）</b></a>。'
                    f'网站上的「一键还原」已停用；下面的分卷链接和离线还原脚本照常可用。</aside>')
            text = re.sub(r'(<main\b[^>]*>)', r'\1' + note.replace('\\', '\\\\'), text, count=1)
    return text


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    total, skipped, unmapped = 0, 0, []
    for dp, dn, fn in os.walk(DOCS):
        dn[:] = [d for d in dn if not d.startswith('.git')]
        for f in fn:
            src = os.path.join(dp, f)
            rel = os.path.relpath(src, DOCS).replace('\\', '/')
            if SOURCE.search(f):
                skipped += 1
                if rel not in arch['files']:
                    unmapped.append(rel)
                continue
            dst = os.path.join(OUT, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if f.lower().endswith(('.html', '.htm')):
                text = open(src, encoding='utf-8', errors='surrogateescape').read()
                open(dst, 'w', encoding='utf-8', errors='surrogateescape').write(rewrite_html(rel, text))
            else:
                shutil.copy2(src, dst)
            total += os.path.getsize(dst)
    for dp, dn, fn in os.walk(LAB):
        dn[:] = [d for d in dn if d != 'tools']
        for f in fn:
            src = os.path.join(dp, f)
            rel = os.path.relpath(src, LAB).replace(os.sep, '/')
            dst = os.path.join(OUT, rel)
            if os.path.exists(dst) and rel != 'index.html':
                sys.exit(f'library file {rel} would overwrite docs/{rel} at the site root')
            if os.path.exists(dst):
                total -= os.path.getsize(dst)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if f.endswith(('.html', '.mjs', '.js', '.json', '.css')):
                open(dst, 'w', encoding='utf-8').write(open(src, encoding='utf-8').read().replace('../docs/', './'))
            else:
                shutil.copy2(src, dst)
            total += os.path.getsize(dst)
            if dp == LAB and f.endswith('.html'):  # old /lab/ address → same page at the root, query and hash kept
                stub = os.path.join(OUT, 'lab', f)
                os.makedirs(os.path.dirname(stub), exist_ok=True)
                open(stub, 'w', encoding='utf-8').write(
                    f'<!doctype html><meta charset="utf-8"><title>造物之匣</title>'
                    f'<script>location.replace("../{f}" + location.search + location.hash)</script>'
                    f'<a href="../{f}">造物之匣已搬到站点首页</a>')
    open(os.path.join(OUT, '.nojekyll'), 'w').close()
    print(f'site {total / 1e6:.0f} MB · {skipped} source files left out (in release {arch.get("tag")})')
    for u in unmapped:
        print(f'  WARN source file not in the release map, left out of the site: {u}')
    if total > LIMIT:
        sys.exit(f'site is {total / 1e6:.0f} MB, over the {LIMIT / 1e6:.0f} MB GitHub Pages limit — not publishing')


if __name__ == '__main__':
    main()
