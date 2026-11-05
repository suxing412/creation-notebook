"""Put each batch's model originals into its GitHub Release (used by .github/workflows/originals.yml).

  python -I lab/tools/release_originals.py rYYYY.MM.DD-N     # one batch tag
  python -I lab/tools/release_originals.py --missing         # every r tag whose Release has no originals.json yet
  add --dry-run to only print what would be uploaded

The website only shows models (and publishes compressed copies). The originals are kept like this:
- A batch is the commits between the previous r tag and this one. The GLBs under docs/ that the batch added or changed
  go into the Release of the same name, uncompressed and byte-for-byte as committed. The first tag takes everything it has.
- Asset names are the path under docs/ with "/" written as "__", for example library__models__m-x__files__A.glb.
- originals.json in the Release lists path, asset name, bytes and SHA-256 for each one.
- Source files (.blend, source ZIPs) are never in the repository. The producer uploads them to the same Release
  (docs/asset-spec/README.md §7). This script creates the Release when it is missing, and never touches other assets.

Needs git (full history and tags) and gh, authenticated through GH_TOKEN.
"""
import hashlib, json, os, subprocess, sys, tempfile, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
MANIFEST = 'originals.json'


def git(*a, binary=False, check=True):
    r = subprocess.run(['git', '-C', ROOT, *a], capture_output=True, check=check)
    if not check:
        return r
    return r.stdout if binary else r.stdout.decode('utf-8')


def gh(*a, check=True):
    for i in range(4):
        r = subprocess.run(['gh', *a], capture_output=True, text=True, encoding='utf-8')
        if r.returncode == 0 or not check:
            return r
        if 'not found' in (r.stderr or '').lower() or 'release not found' in (r.stderr or '').lower():
            return r
        time.sleep(5 * (i + 1))
    sys.exit(f'gh {" ".join(a[:3])} failed: {r.stderr.strip()[:300]}')


def tags():
    out = git('tag', '-l', 'r*', '--sort=creatordate').split()
    return [t for t in out if t[1:2].isdigit()]


def glbs_at(ref):
    """path → blob for every GLB under docs/ at ref."""
    out = {}
    for line in git('ls-tree', '-r', ref, '--', 'docs').splitlines():
        meta, path = line.split('\t', 1)
        if path.lower().endswith('.glb'):
            out[path] = meta.split()[2]
    return out


def batch(tag):
    ts = tags()
    prev = ts[ts.index(tag) - 1] if tag in ts and ts.index(tag) > 0 else None
    now, before = glbs_at(tag), glbs_at(prev) if prev else {}
    return prev, sorted(p for p, b in now.items() if before.get(p) != b), now


def asset_name(path):
    return path[len('docs/'):].replace('/', '__')


def release_assets(tag):
    r = gh('release', 'view', tag, '--json', 'assets', check=False)
    if r.returncode:
        return None
    return {a['name']: a['size'] for a in json.loads(r.stdout)['assets']}


def archive(tag, dry):
    prev, changed, blobs = batch(tag)
    have = release_assets(tag)
    total = 0
    with tempfile.TemporaryDirectory() as tmp:
        entries, todo = [], []
        for p in changed:
            data = git('cat-file', 'blob', blobs[p], binary=True)
            name = asset_name(p)
            entries.append({'path': p, 'asset': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
            total += len(data)
            if have is None or have.get(name) != len(data):
                f = os.path.join(tmp, name)
                open(f, 'wb').write(data)
                todo.append(f)
        print(f'{tag}: {len(changed)} GLB originals since {prev or "the start"} ({total / 1e6:.0f} MB), {len(todo)} to upload'
              + (' · Release missing' if have is None else ''))
        bf = git('show', f'{tag}:docs/asset-spec/batches/{tag}.json', check=False)
        bfile = json.loads(bf.stdout.decode('utf-8')) if bf.returncode == 0 else None
        # a batch closed by a batch file gets its Release even without GLBs: its source files go there
        if dry or not (changed or bfile):
            return
        if have is None:
            notes = (f'这一批（{prev or "仓库开始"} → {tag}）新增或改动的 GLB 原件，未压缩，与仓库里提交的文件逐字节相同。'
                     f'清单见 {MANIFEST}（路径、体积、SHA-256）。\n\n'
                     '网站上发布的是压缩后的副本，只用来展示。这一批的源文件（.blend、源码 ZIP 等）也上传到这个 Release。')
            if bfile:
                notes = (bfile.get('summary') or '').strip() + '\n\n' + notes
                if bfile.get('sources'):
                    notes += '\n\n待传的源文件：' + '、'.join(bfile['sources'])
            gh('release', 'create', tag, '--verify-tag', '--title', f'{tag} · 原件', '--notes', notes)
        for i in range(0, len(todo), 20):
            gh('release', 'upload', tag, *todo[i:i + 20], '--clobber')
        man = os.path.join(tmp, MANIFEST)
        json.dump({'tag': tag, 'since': prev, 'files': entries}, open(man, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        gh('release', 'upload', tag, man, '--clobber')
        after = release_assets(tag) or {}
        missing = [e['asset'] for e in entries if after.get(e['asset']) != e['bytes']]
        if missing:
            sys.exit(f'{tag}: {len(missing)} originals did not land in the Release, e.g. {missing[:3]}')
        print(f'{tag}: Release holds all {len(entries)} originals')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    if '--missing' in sys.argv:
        todo = [t for t in tags() if MANIFEST not in (release_assets(t) or {})]
    else:
        todo = args
    if not todo:
        print('nothing to archive')
    for t in todo:
        if t not in tags():
            sys.exit(f'{t} is not an r tag in this clone (fetch with tags first)')
        archive(t, dry)


if __name__ == '__main__':
    main()
