"""Move source files (.blend, source ZIPs and their parts, …) out of the published site and into a GitHub Release.

  python -I lab/tools/archive_sources.py --tag sources-2026.11.05 --out <staging dir>   # stage files + write the map
  then upload the staging dir to that release (gh release upload <tag> <staging>/* ).

Writes docs/asset-spec/source-archive.json: { tag, base, files: {docs path: asset name}, joined: {manifest path: asset name} }.
The site assembler (assemble_site.py) leaves these files out of the site and points links at the release.
Part sets (exact-zip-byte-parts-v1 manifests) are also joined into the original ZIP, verified by SHA-256,
so the release offers the whole archive in one download.
"""
import argparse, hashlib, json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
DOCS = os.path.join(ROOT, 'docs')
REPO = 'suxing412/creation-notebook'
SOURCE = re.compile(r'\.(blend|blend1|zip|part\d{3}|psd|exr|fbx|max|ma|mb|c4d|spp|kra)$', re.I)


def tracked_sources():
    out = subprocess.run(['git', '-C', ROOT, 'ls-files', 'docs'], capture_output=True, text=True, check=True).stdout.split('\n')
    return sorted(p[5:] for p in out if p and SOURCE.search(p))


def asset_name(rel):
    return rel.replace('/', '--')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    files, joined = {}, {}
    for rel in tracked_sources():
        name = asset_name(rel)
        shutil.copy2(os.path.join(DOCS, rel), os.path.join(a.out, name))
        files[rel] = name
    # join every verified part set back into its original ZIP
    for man in sorted({os.path.dirname(r) for r in files if re.search(r'\.part\d{3}$', r)}):
        mp = os.path.join(DOCS, man, 'manifest.json')
        if not os.path.exists(mp):
            print('no manifest for', man); continue
        m = json.load(open(mp, encoding='utf-8'))
        data = b''.join(open(os.path.join(DOCS, man, p['file']), 'rb').read() for p in m['parts'])
        if hashlib.sha256(data).hexdigest() != m['archive']['sha256']:
            sys.exit(f'joined archive does not match its manifest: {man}')
        name = asset_name(os.path.dirname(man) + '/' + m['archive']['name']) if os.path.dirname(man) else m['archive']['name']
        open(os.path.join(a.out, name), 'wb').write(data)
        joined[man + '/manifest.json'] = name
    out = {'tag': a.tag, 'base': f'https://github.com/{REPO}/releases/download/{a.tag}/', 'files': files, 'joined': joined}
    json.dump(out, open(os.path.join(DOCS, 'asset-spec', 'source-archive.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    total = sum(os.path.getsize(os.path.join(a.out, n)) for n in os.listdir(a.out))
    print(f'{len(files)} source files + {len(joined)} joined archives staged, {total / 1e6:.0f} MB')


if __name__ == '__main__':
    main()
