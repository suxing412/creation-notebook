#!/usr/bin/env python3
"""在仓库的导出副本里跑官方 `python -I lab/tools/build_assets.py --check`：基线 → 注入负例 → 撤回，三次。
绝不在原仓库里跑：本脚本每次先删掉并重新导出副本 `git -C <repo> -c core.autocrlf=false archive <commit> | tar -x -C <LY-008>/tmp/repo`
（没有 .git；autocrlf=false 让文本文件保持提交字节），再逐文件核 git blob id；
ly_check.run_official 见到 .git 就拒绝。原仓库只读：前后各记一次 HEAD 与 `git status --porcelain`。

用法：python -I source/run_official.py <LY-008 目录> <原仓库> <commit>
结果：qa/official-runs.json（规范版本与 SHA、命令、退出码、每张注入卡官方判了什么、与 ly_check 的对照）。
"""
import hashlib, importlib.util, json, os, shutil, subprocess, sys

ROOT = os.path.abspath(sys.argv[1])
REPO = os.path.abspath(sys.argv[2])
COMMIT = sys.argv[3]
COPY = os.path.join(ROOT, 'tmp', 'repo')
spec = importlib.util.spec_from_file_location('ly_check', os.path.join(ROOT, 'source', 'ly_check.py'))
lc = importlib.util.module_from_spec(spec); spec.loader.exec_module(lc)


def git(*a):
    return subprocess.run(['git', '-C', REPO, *a], capture_output=True, text=True, encoding='utf-8').stdout


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


NEG_CARDS = [
    # id, 注入的 GLB（相对 LY-008）, files 路径写法, ly_check 对同一文件的判定代码（来自 qa/selftest.json）
    ('ly008-neg-oversize', 'tmp/neg-big/N11-oversize-15000004.glb', 'files/model.glb', 'N11-oversize-15000004'),
    ('ly008-neg-boundary', 'tmp/neg-big/B11-boundary-15000000.glb', 'files/model.glb', 'B11-boundary-15000000'),
    ('ly008-neg-tris', 'tmp/neg-big/N23-over-triangle-limit.glb', 'files/model.glb', 'N23-over-triangle-limit'),
    ('ly008-neg-escape', None, '../../../../../../outside/model.glb', None),
    ('ly008-neg-truncated', 'qa/negatives/N02-truncated.glb', 'files/model.glb', 'N02-truncated'),
    ('ly008-neg-badlen', 'qa/negatives/N01-bad-header-length.glb', 'files/model.glb', 'N01-bad-header-length'),
    ('ly008-neg-nan', 'qa/negatives/N04-nan-position.glb', 'files/model.glb', 'N04-nan-position'),
    ('ly008-neg-notex', 'qa/negatives/N07-missing-texture-index.glb', 'files/model.glb', 'N07-missing-texture-index'),
    ('ly008-neg-exttex', 'qa/negatives/N09-external-texture-missing.glb', 'files/model.glb', 'N09-external-texture-missing'),
    ('ly008-neg-private', 'qa/negatives/N13a-private-path-extras.glb', 'files/model.glb', 'N13a-private-path-extras'),
    ('ly008-neg-idx', 'qa/negatives/N17-index-out-of-range.glb', 'files/model.glb', 'N17-index-out-of-range'),
    ('ly008-pos-s84', '../LY-007/models/samples/S84-LOD0.glb', 'files/model.glb', 'G-base-S84-LOD0.glb'),
]
COVER_SRC = 'docs/library/models/m-luoyang-lingtai/cover.webp'


def inject():
    made = []
    cover = os.path.join(COPY, COVER_SRC)
    for cid, glb, fpath, _ in NEG_CARDS:
        d = os.path.join(COPY, 'docs', 'library', 'models', cid)
        os.makedirs(os.path.join(d, 'files'), exist_ok=True)
        shutil.copyfile(cover, os.path.join(d, 'cover.webp'))
        if glb:
            shutil.copyfile(os.path.join(ROOT, glb), os.path.join(d, 'files', 'model.glb'))
        card = {'spec': 1, 'id': cid, 'category': 'models', 'kind': '建筑', 'title': 'LY-008 负例', 'english': 'LY-008 negative',
                'summary': 'LY-008 检查器注入的负例卡，只存在于导出副本。', 'status': '草稿', 'cover': 'cover.webp', 'coverAlt': '负例',
                'gallery': ['cover.webp'], 'files': [{'path': fpath}],
                'notes': {'已完成的检查': '无', '限制与待解决': '负例'}}
        json.dump(card, open(os.path.join(d, f'{cid}.asset.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        made.append(d)
    b = os.path.join(COPY, 'docs', 'library', 'models', 'ly008-neg-boundary', 'files', 'scene.blend')
    open(b, 'wb').write(b'BLENDER-v502 LY-008 negative fixture\n')
    return made


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    before = {'head': git('rev-parse', 'HEAD').strip(), 'status': git('status', '--porcelain=v1')}
    # 每次都重新导出一份干净副本（git archive 只读原仓库），保证基线不受上一次 build_assets 产物影响
    if os.path.isdir(COPY):
        shutil.rmtree(COPY)
    os.makedirs(COPY)
    arc = subprocess.Popen(['git', '-C', REPO, '-c', 'core.autocrlf=false', 'archive', COMMIT], stdout=subprocess.PIPE)
    subprocess.run(['tar', '-x', '-C', COPY], stdin=arc.stdout, check=True)
    arc.wait()
    assert not os.path.exists(os.path.join(COPY, '.git')), '副本不能含 .git'
    # 副本身份：与提交的 tree 逐文件比对太慢，这里核 3 个检查器文件与 categories.json 的提交字节
    ident = {}
    for p in ('lab/tools/build_assets.py', 'lab/tools/glb_audit.py', 'docs/asset-spec/categories.json', 'docs/asset-spec/README.md'):
        blob = subprocess.run(['git', '-C', REPO, 'show', f'{COMMIT}:{p}'], capture_output=True).stdout
        ident[p] = {'commitBlobSha256': hashlib.sha256(blob).hexdigest(), 'copySha256': sha(os.path.join(COPY, p))}
        ident[p]['same'] = ident[p]['commitBlobSha256'] == ident[p]['copySha256']
    # 整个副本逐文件核 git blob id（sha1("blob <len>\0" + 字节)）：副本必须是提交字节（导出时要 -c core.autocrlf=false，
    # 否则 Windows 上 git archive 会把文本文件转成 CRLF，见 brief.md）
    tree = {}
    for line in subprocess.run(['git', '-C', REPO, 'ls-tree', '-r', '-z', COMMIT], capture_output=True).stdout.split(b'\0'):
        if line:
            meta, path = line.split(b'\t', 1)
            mode, typ, oid = meta.split()
            if typ == b'blob':
                tree[path.decode('utf-8')] = (oid.decode(), mode.decode())
    bad, missing = [], []
    for p, (oid, mode) in tree.items():
        full = os.path.join(COPY, p)
        if mode == '120000':
            continue
        if not os.path.isfile(full):
            missing.append(p); continue
        data = open(full, 'rb').read()
        if hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest() != oid:
            bad.append(p)
    extra = []
    for dp, dn, fn in os.walk(COPY):
        for f in fn:
            r = os.path.relpath(os.path.join(dp, f), COPY).replace('\\', '/')
            if r not in tree:
                extra.append(r)
    ident['_wholeTree'] = {'blobs': len(tree), 'mismatch': bad[:20], 'mismatchCount': len(bad), 'missing': missing[:20],
                           'extraBeforeRun': extra[:20], 'extraCountBeforeRun': len(extra), 'identical': not bad and not missing}
    selftest = {r['id']: r for r in json.load(open(os.path.join(ROOT, 'qa', 'selftest.json'), encoding='utf-8'))['rows']}
    refused = lc.run_official(REPO).as_dict()           # 负例：对原仓库调用必须被拒绝（不运行 build_assets）
    runs = {}
    print('baseline …', flush=True)
    runs['baseline'] = lc.run_official(COPY).as_dict()
    made = inject()
    print('injected …', flush=True)
    runs['injected'] = lc.run_official(COPY).as_dict()
    for d in made:
        shutil.rmtree(d)
    print('reverted …', flush=True)
    runs['reverted'] = lc.run_official(COPY).as_dict()
    after = {'head': git('rev-parse', 'HEAD').strip(), 'status': git('status', '--porcelain=v1')}
    # 每张注入卡：官方判了什么 vs ly_check
    errs = {e['card'].split('/')[-2]: e['errors'] for e in runs['injected']['info'].get('cardErrors', [])}
    rep = json.load(open(os.path.join(COPY, 'lab', 'data', 'report.json'), encoding='utf-8'))  # 已是 reverted 的报告
    cmp_rows = []
    for cid, glb, fpath, case in NEG_CARDS:
        st = selftest.get(case) if case else None
        cmp_rows.append({'card': cid, 'glb': glb, 'glbSha256': sha(os.path.join(ROOT, glb)) if glb else None, 'filesPath': fpath,
                         'officialErrors': errs.get(cid, []), 'officialCatches': bool(errs.get(cid)),
                         'lyCheckCase': case, 'lyCheckErrorCodes': st['errorCodes'] if st else None,
                         'lyCheckCatches': bool(st and st['errorCodes']) if st else None})
    blend_caught = [e for e in runs['injected']['info'].get('repoErrors', []) if 'ly008' in e]
    out = {'repo': REPO.replace('\\', '/'), 'commit': COMMIT, 'copy': 'tmp/repo（git archive 导出，无 .git）', 'copyIdentity': ident,
           'officialSpec': runs['baseline']['info'].get('spec'),
           'command': 'python -I lab/tools/build_assets.py --check（cwd = 导出副本；env GIT_CEILING_DIRECTORIES = 副本上一级）',
           'refusedOnRealRepo': {'errorCodes': refused['errorCodes'], 'ranBuildAssets': 'exitCode' in refused['info']},
           'runs': {k: {kk: v['info'].get(kk) for kk in ('exitCode', 'seconds', 'reportCounts', 'repoErrors', 'cardErrors', 'orphans', 'stdoutTail')}
                    | {'errorCodes': v['errorCodes']} for k, v in runs.items()},
           'injectedComparison': cmp_rows, 'blendInjectedCaught': blend_caught,
           'revertedEqualsBaseline': runs['reverted']['info'].get('reportCounts') == runs['baseline']['info'].get('reportCounts')
           and runs['reverted']['info'].get('exitCode') == runs['baseline']['info'].get('exitCode'),
           'labRepoBefore': before, 'labRepoAfter': after, 'labRepoUnchanged': before == after}
    json.dump(out, open(os.path.join(ROOT, 'qa', 'official-runs.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    for k, v in out['runs'].items():
        print(k, 'exit', v['exitCode'], v['reportCounts'], 'repoErrors', len(v['repoErrors'] or []))
    for r in cmp_rows:
        print(f"{r['card']:22s} official={r['officialCatches']!s:5s} ly_check={r['lyCheckCatches']!s:5s} {r['officialErrors'][:2]}")
    print('lab unchanged', out['labRepoUnchanged'], 'reverted==baseline', out['revertedEqualsBaseline'])


if __name__ == '__main__':
    main()
