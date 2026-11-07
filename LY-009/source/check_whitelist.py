"""LY-009 whitelist checker: does a change set stay inside one seat's whitelist?

Modes (all read-only):
  python -I check_whitelist.py --seat LY-021 --paths <file with one path per line> [--root <workpacks>]
  python -I check_whitelist.py --seat LY-021 --git <repo> <base> <head>      (both sides; committed blob sizes)
  python -I check_whitelist.py --scan <workpacks root> <out.json>           (classify every file; plus
                                                                            git status of the shared branch)
Paths are workpacks-relative ('LY-021/brief.md'). A path with '..', a drive letter, a leading '/',
backslash tricks or a wrong-case seat dir is rejected.

Rule set (version 1):
  R1  a seat may write only '<seat>/**'                          (pool: 唯一写入区)
  R2  root files TASKPOOL.md / taskboard.json / README.md / .gitignore / .gitattributes: coordinator only
  R3  inside the seat dir, source projects are refused: *.blend *.blend1 *.zip *.7z *.rar *.part### *.z##
      *.tar *.gz *.tgz *.bz2 *.xz (including compound suffixes such as *.tar.gz)
      (README: 源工程（.blend、源 ZIP）不进这个分支)
  R4  a .glb above 15,000,000 bytes is refused (pool: 单GLB不超过15,000,000字节)
  R5  any file above 100 MiB is refused (GitHub hard limit); above 50 MiB is a warning
  R6  __pycache__/ *.pyc, Thumbs.db, .DS_Store are warnings (junk, not a breach)
  R7  nothing outside the workpacks tree (lab repo, 待传 dir, absolute paths) is writable by LY-001..099;
      LY-100 writes the lab repo only through its batch procedure, which this tool does not grant.
"""
import json, os, re, subprocess, sys, hashlib

COORD_FILES = {'TASKPOOL.md', 'taskboard.json', 'README.md', '.gitignore', '.gitattributes'}
SEAT_RE = re.compile(r'^LY-(\d{3})$')
SOURCE_EXT = re.compile(r'\.(blend\d*|zip|7z|rar|part\d+|z\d\d|tar|gz|tgz|bz2|xz)$', re.I)
JUNK = re.compile(r'(^|/)(__pycache__/|Thumbs\.db$|\.DS_Store$)|\.pyc$')
GLB_LIMIT = 15_000_000
HARD = 100 * 1024 * 1024
WARN = 50 * 1024 * 1024
RULESET = 'LY-009 whitelist v1'


def norm(p):
    """Return (normalized path, error)."""
    if p is None or p == '':
        return None, 'empty path'
    if re.match(r'^[A-Za-z]:', p) or p.startswith('/') or p.startswith('\\'):
        return None, 'absolute path (outside workpacks tree; R7)'
    if '\\' in p:
        return None, 'backslash in path'
    parts = p.split('/')
    if any(x in ('..', '.') for x in parts):
        return None, 'dot segment in path'
    return p, None


def classify(path, seat=None, size=None):
    """Return dict(ok, rule, reason, owner, warn)."""
    p, err = norm(path)
    if err:
        return {'path': path, 'ok': False, 'rule': 'R7' if 'absolute' in err else 'R1', 'reason': err, 'owner': None}
    top = p.split('/')[0]
    res = {'path': p, 'ok': True, 'rule': None, 'reason': '', 'owner': None, 'warn': []}
    if '/' not in p and top in COORD_FILES:
        res['owner'] = 'coordinator'
        if seat is not None:
            res.update(ok=False, rule='R2', reason='root task-board file is coordinator-only')
        return res
    m = SEAT_RE.match(top)
    if not m or '/' not in p:
        if top.upper().startswith('LY-') and not m:
            res.update(ok=False, rule='R1', reason='seat dir name not exactly LY-### (case/format)')
        else:
            res.update(ok=False, rule='R1', reason='path outside every seat dir and not a coordinator file')
        return res
    res['owner'] = top
    if not (1 <= int(m.group(1)) <= 100):
        res.update(ok=False, rule='R1', reason='seat number out of range')
        return res
    if seat is not None and top != seat:
        res.update(ok=False, rule='R1', reason=f'{seat} may not write into {top}/')
        return res
    if SOURCE_EXT.search(p):
        res.update(ok=False, rule='R3', reason='source project / archive not allowed in workpacks branch')
        return res
    if size is not None:
        if p.lower().endswith('.glb') and size > GLB_LIMIT:
            res.update(ok=False, rule='R4', reason=f'GLB {size} bytes > 15,000,000')
            return res
        if size > HARD:
            res.update(ok=False, rule='R5', reason=f'{size} bytes > 100 MiB')
            return res
        if size > WARN:
            res['warn'].append('R5: file > 50 MiB')
    if JUNK.search(p):
        res['warn'].append('R6: junk file (cache/OS metadata)')
    return res


def check_paths(seat, items):
    """items: list of (path, size|None)."""
    out = [classify(p, seat, s) for p, s in items]
    return {'ruleset': RULESET, 'seat': seat, 'n': len(out), 'fail': sum(not r['ok'] for r in out),
            'warn': sum(bool(r.get('warn')) for r in out), 'results': out,
            'verdict': 'PASS' if all(r['ok'] for r in out) else 'FAIL'}


def git(repo, *args, raw=False):
    out = subprocess.run(['git', '--no-optional-locks', '--no-replace-objects', '-C', repo, *args], capture_output=True,
                         check=True).stdout
    return out if raw else out.decode('utf-8', errors='surrogateescape')


def git_items(repo, base, head):
    """Check every changed path, including deletions, without reading the working tree."""
    # Read original objects, pin refs, and prevent Git config from hiding changed paths.
    base = git(repo, 'rev-parse', '--verify', '--end-of-options', f'{base}^{{commit}}').strip()
    head = git(repo, 'rev-parse', '--verify', '--end-of-options', f'{head}^{{commit}}').strip()
    fields = git(repo, 'diff', '--name-status', '-z', '--no-renames', '--no-ext-diff', '--ignore-submodules=none',
                 '--no-textconv', base, head, '--', raw=True).split(b'\0')
    if fields.pop() != b'' or len(fields) % 2:
        raise ValueError('invalid NUL-delimited git diff output')
    items = []
    for i in range(0, len(fields), 2):
        status, path = fields[i], os.fsdecode(fields[i + 1])
        if status not in (b'A', b'M', b'D', b'T') or not path:
            raise ValueError('unexpected git diff status or empty path')
        size = None
        if status != b'D':
            obj = f'{head}:{path}'
            if git(repo, 'cat-file', '-t', obj).strip() != 'blob':
                raise ValueError(f'changed path is not a blob: {path!r}')
            size = int(git(repo, 'cat-file', '-s', obj).strip())
        # A deletion has no head blob, but must still pass the same path/owner rules.
        items.append((path, size))
    return items


def scan(root):
    files = []
    for dp, dns, fns in os.walk(root):
        if '.git' in dns:
            dns.remove('.git')
        for fn in fns:
            if fn == '.git':
                continue
            full = os.path.join(dp, fn)
            rel = os.path.relpath(full, root).replace(os.sep, '/')
            files.append((rel, os.path.getsize(full)))
    files.sort()
    per_owner, bad, warns = {}, [], []
    for rel, size in files:
        r = classify(rel, None, size)
        own = r.get('owner') or '(none)'
        per_owner.setdefault(own, {'files': 0, 'bytes': 0})
        per_owner[own]['files'] += 1
        per_owner[own]['bytes'] += size
        if not r['ok']:
            bad.append(r)
        if r.get('warn'):
            warns.append({'path': rel, 'warn': r['warn']})
    # which violations are already kept out of git by the root .gitignore (read-only check-ignore)
    if bad:
        r = subprocess.run(['git', '--no-optional-locks', '--no-replace-objects', '-C', root, 'check-ignore', '--stdin', '-z', '-v', '-n'],
                           input='\0'.join(v['path'] for v in bad) + '\0', capture_output=True, text=True, encoding='utf-8')
        f = r.stdout.split('\0')
        ign = {}
        for k in range(0, len(f) - 3, 4):
            src, ln, pat, path = f[k], f[k + 1], f[k + 2], f[k + 3]
            if pat and not pat.startswith('!'):
                ign[path] = f'{src}:{ln}:{pat}'
        for v in bad:
            v['ignoredBy'] = ign.get(v['path'])
    # shared-branch change set (read-only)
    st = git(root, 'status', '--porcelain=v1', '--untracked-files=all', '-z')
    changed = []
    for ent in st.split('\0'):
        if not ent:
            continue
        code, path = ent[:2], ent[3:]
        changed.append({'code': code, 'path': path})
    ch_bad = []
    for c in changed:
        r = classify(c['path'], None, None)
        if not r['ok']:
            ch_bad.append({**c, 'reason': r['reason']})
    seats_changed = sorted({c['path'].split('/')[0] for c in changed if SEAT_RE.match(c['path'].split('/')[0])})
    coord_changed = sorted({c['path'] for c in changed if c['path'] in COORD_FILES})
    return {
        'ruleset': RULESET, 'root': 'D:/GitHub/creation-notebook-workpacks',
        'branch': git(root, 'rev-parse', '--abbrev-ref', 'HEAD').strip(),
        'head': git(root, 'rev-parse', 'HEAD').strip(),
        'filesScanned': len(files), 'perOwner': per_owner, 'violations': bad, 'warnings': warns,
        'violationsNotIgnored': [v['path'] for v in bad if not v.get('ignoredBy')],
        'gitignore': (hashlib.sha256(open(os.path.join(root, '.gitignore'), 'rb').read()).hexdigest()
                      if os.path.isfile(os.path.join(root, '.gitignore')) else None),
        'workingTreeChanges': {'n': len(changed), 'seatsWithChanges': seats_changed,
                               'coordinatorFilesChanged': coord_changed, 'outsideWhitelist': ch_bad},
        'verdict': 'PASS' if not [v for v in bad if not v.get('ignoredBy')] and not ch_bad else 'FAIL',
        'verdictNote': 'FAIL 只计没有被根 .gitignore 挡住的违规与越界改动；被挡住的仍列在 violations 里（ignoredBy）',
    }


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == '--scan':
        out = scan(a[1])
        with open(a[2], 'w', encoding='utf-8', newline='\n') as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print(out['verdict'], out['filesScanned'], 'files;', len(out['violations']), 'violations;',
              len(out['warnings']), 'warnings;', out['workingTreeChanges']['n'], 'changed paths')
        sys.exit(0 if out['verdict'] == 'PASS' else 1)
    seat = a[a.index('--seat') + 1]
    if '--paths' in a:
        fp = a[a.index('--paths') + 1]
        root = a[a.index('--root') + 1] if '--root' in a else None
        items = []
        for ln in open(fp, encoding='utf-8').read().splitlines():
            if not ln.strip():
                continue
            size = None
            if root and norm(ln)[1] is None and os.path.isfile(os.path.join(root, ln)):
                size = os.path.getsize(os.path.join(root, ln))
            items.append((ln, size))
    else:
        i = a.index('--git')
        repo, base, head = a[i + 1:i + 4]
        items = git_items(repo, base, head)
    out = check_paths(seat, items)
    print(json.dumps(out, ensure_ascii=True, indent=1))
    sys.exit(0 if out['verdict'] == 'PASS' else 1)
