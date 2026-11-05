"""Turn committed batch files into r tags (used by .github/workflows/originals.yml on every push to main).

  python -I lab/tools/tag_batches.py            # tag every batch file that has no tag yet; prints the new tags
  python -I lab/tools/tag_batches.py --check    # only validate the batch files

Whoever can only commit (no tag or Release rights) closes a batch by committing
docs/asset-spec/batches/rYYYY.MM.DD-N.json:

  {"tag": "rYYYY.MM.DD-N", "summary": "这一批做了什么", "sources": ["model.blend", "source.zip"]}

- tag: the same as the file name. Date in Asia/Shanghai, N is the day's batch number; it must not exist yet.
- summary: one or two sentences. It becomes the tag message and the top of the Release notes.
- sources (optional): the source files still to come, so the Release says what is missing.

The tag is put on the commit that added the batch file, annotated, then pushed. That commit must come after the
latest existing r tag, so the batch (previous tag → this one) is never empty or backwards.
"""
import json, os, re, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
DIR = 'docs/asset-spec/batches'
TAG = re.compile(r'^r\d{4}\.\d{2}\.\d{2}-\d+$')


def git(*a, check=True):
    r = subprocess.run(['git', '-C', ROOT, *a], capture_output=True, text=True, encoding='utf-8')
    if check and r.returncode:
        sys.exit(f'git {" ".join(a[:2])}: {r.stderr.strip()}')
    return r


def batches():
    d = os.path.join(ROOT, DIR)
    return sorted(f for f in os.listdir(d) if f.endswith('.json')) if os.path.isdir(d) else []


def validate(f):
    errs = []
    try:
        b = json.load(open(os.path.join(ROOT, DIR, f), encoding='utf-8'))
    except Exception as e:  # noqa: BLE001
        return None, [f'{f}: 不是合法的 JSON（{e}）']
    tag = b.get('tag')
    if not isinstance(tag, str) or not TAG.match(tag):
        errs.append(f'{f}: tag 要写成 rYYYY.MM.DD-N')
    elif f != tag + '.json':
        errs.append(f'{f}: 文件名要和 tag 一致（{tag}.json）')
    if not isinstance(b.get('summary'), str) or not b['summary'].strip():
        errs.append(f'{f}: 缺 summary（这一批做了什么）')
    if 'sources' in b and not (isinstance(b['sources'], list) and all(isinstance(x, str) for x in b['sources'])):
        errs.append(f'{f}: sources 是文件名列表')
    return b, errs


def main():
    check = '--check' in sys.argv
    tags = set(git('tag', '-l', 'r*').stdout.split())
    latest = git('tag', '-l', 'r*', '--sort=creatordate').stdout.split()
    latest = latest[-1] if latest else None
    errs, made = [], []
    for f in batches():
        b, e = validate(f)
        errs += e
        if e or check or b['tag'] in tags:
            continue
        path = f'{DIR}/{f}'
        commit = git('log', '-1', '--diff-filter=A', '--format=%H', '--', path).stdout.strip()
        if not commit:
            errs.append(f'{f}: 找不到加入这个文件的提交')
            continue
        if latest and git('merge-base', '--is-ancestor', commit, latest, check=False).returncode == 0:
            errs.append(f'{f}: 它的提交早于最新的标签 {latest}，这一批会是空的；请换一个新的序号重新提交')
            continue
        git('tag', '-a', b['tag'], commit, '-m', b['summary'].strip())
        git('push', 'origin', b['tag'])
        tags.add(b['tag']); latest = b['tag']
        made.append(b['tag'])
        print(f'tagged {b["tag"]} at {commit[:7]}')
    if errs:
        for e in errs:
            print('ERROR ' + e)
        sys.exit(1)
    out = os.environ.get('GITHUB_OUTPUT')
    if out:
        open(out, 'a', encoding='utf-8').write(f'tags={" ".join(made)}\n')
    if not made and not check:
        print('no new batch files')


if __name__ == '__main__':
    main()
