"""Upload source files waiting in the local inbox to their batch Release (run on the machine where gh is signed in).

  python -I lab/tools/upload_sources.py [inbox]    # default D:/GitHub/creation-notebook-待传
  add --dry-run to only list what would be uploaded

The inbox has one folder per batch tag, holding that batch's source files (.blend, source ZIPs, .psd …):

  D:/GitHub/creation-notebook-待传/r2026.11.05-4/model.blend

For each file: upload it to the Release of that tag (one file at a time, with retries, since uploads here time out
often; set HTTPS_PROXY=http://127.0.0.1:3213), then compare GitHub's SHA-256 of the uploaded asset with the local
file. Only a verified file leaves the inbox, and it is moved to D:/待删-<date>-已传源文件/<tag>/, never deleted.
A folder whose Release doesn't exist yet is left alone (the Release appears a minute or two after the batch is tagged).
Files in subfolders are uploaded as <subfolder>__<name>.
"""
import datetime, hashlib, json, os, re, shutil, subprocess, sys, time

REPO = 'suxing412/creation-notebook'
TAG = re.compile(r'^r\d{4}\.\d{2}\.\d{2}-\d+$')


def gh(*a):
    return subprocess.run(['gh', *a, '-R', REPO], capture_output=True, text=True, encoding='utf-8')


def assets(tag):
    r = gh('release', 'view', tag, '--json', 'assets')
    if r.returncode:
        return None
    return {x['name']: x for x in json.loads(r.stdout)['assets']}


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    inbox = args[0] if args else 'D:/GitHub/creation-notebook-待传'
    if not os.path.isdir(inbox):
        print(f'no inbox at {inbox}'); return
    done_dir = f'D:/待删-{datetime.date.today():%Y-%m-%d}-已传源文件'
    failed = 0
    for tag in sorted(os.listdir(inbox)):
        folder = os.path.join(inbox, tag)
        if not os.path.isdir(folder) or not TAG.match(tag):
            continue
        files = []
        for dp, dn, fn in os.walk(folder):
            for f in fn:
                p = os.path.join(dp, f)
                rel = os.path.relpath(p, folder).replace(os.sep, '__')
                files.append((p, rel))
        if not files:
            continue
        have = assets(tag)
        if have is None:
            print(f'{tag}: Release not there yet, {len(files)} files wait'); continue
        for p, name in sorted(files):
            local = sha(p); size = os.path.getsize(p)
            a = have.get(name)
            if a and a.get('digest') == 'sha256:' + local:
                status = 'already there'
            elif a:
                print(f'  {tag}/{name}: a different file with this name is already in the Release; left in the inbox')
                failed += 1; continue
            elif dry:
                print(f'  {tag}/{name}: would upload ({size / 1e6:.1f} MB)'); continue
            else:
                tmp = None
                src = p
                if os.path.basename(p) != name:  # gh names the asset after the file
                    tmp = os.path.join(os.path.dirname(folder), '.upload-tmp')
                    os.makedirs(tmp, exist_ok=True)
                    src = os.path.join(tmp, name); shutil.copy2(p, src)
                for i in range(5):
                    r = gh('release', 'upload', tag, src)
                    if r.returncode == 0:
                        break
                    time.sleep(10 * (i + 1))
                if tmp:
                    os.remove(src)  # the copy made just above, not the producer's file
                a = (assets(tag) or {}).get(name)
                if not a or a.get('digest') != 'sha256:' + local:
                    print(f'  {tag}/{name}: upload not verified ({(r.stderr or "").strip()[:160]}); left in the inbox')
                    failed += 1; continue
                status = 'uploaded, SHA-256 verified'
            if dry:
                print(f'  {tag}/{name}: {status}'); continue
            dst = os.path.join(done_dir, tag, os.path.relpath(p, folder))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(p, dst)
            print(f'  {tag}/{name}: {status} ({size / 1e6:.1f} MB) → moved to {dst}')
    if failed:
        sys.exit(f'{failed} files not uploaded')


if __name__ == '__main__':
    main()
