#!/usr/bin/env python3
"""汇总 LY-008 的验收项，每项绑定实际文件 SHA256，可重算。写 qa/checks.json。
用法：python -I source/checks.py <LY-008 目录> <LY-007 目录> <原仓库> <commit> <workpacks 目录>
"""
import csv, hashlib, json, os, subprocess, sys

ROOT, LY7, REPO, COMMIT, WP = sys.argv[1:6]
ROOT, LY7, REPO, WP = map(os.path.abspath, (ROOT, LY7, REPO, WP))


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def J(p):
    return json.load(open(os.path.join(ROOT, p), encoding='utf-8'))


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    C = []
    chk = os.path.join(ROOT, 'source', 'ly_check.py')
    st = J('qa/selftest.json'); s = st['summary']
    C.append({'id': 'C1-selftest', 'pass': s['selftestFailures'] == 0 and s['negativesCaught'] == s['negatives'] and s['positivesPassed'] == s['positives']
              and all(x['detectedAsWrong'] for x in s['harnessSanity']) and s['checkerSha256'] == sha(chk)
              and s['casesSha256'] == sha(os.path.join(ROOT, 'qa', 'negatives', 'cases.json')),
              'detail': {k: s[k] for k in ('cases', 'negatives', 'negativesCaught', 'positives', 'positivesPassed', 'selftestFailures')},
              'bind': {'source/ly_check.py': sha(chk), 'qa/negatives/cases.json': s['casesSha256'], 'qa/selftest.json': sha(os.path.join(ROOT, 'qa', 'selftest.json'))}})
    # C2 负例逐字节可重出
    cases = J('qa/negatives/cases.json')['cases']
    before = {c['id']: c.get('sha256') for c in cases}
    subprocess.run([sys.executable, '-I', os.path.join(ROOT, 'source', 'make_negatives.py'), ROOT, LY7], check=True, capture_output=True)
    after = {c['id']: c.get('sha256') for c in J('qa/negatives/cases.json')['cases']}
    onfile = {c['id']: sha(os.path.join(ROOT, c['file'])) == c['sha256'] for c in cases if c.get('file') and c.get('sha256') and os.path.isfile(os.path.join(ROOT, c['file']))}
    C.append({'id': 'C2-fixtures-deterministic', 'pass': before == after and all(onfile.values()),
              'detail': {'regeneratedIdentical': before == after, 'filesCheckedAgainstRecordedSha': len(onfile), 'mismatch': [k for k, v in onfile.items() if not v]}})
    # C3 好样本 = LY-007 交付字节
    m7 = {f['path']: f['sha256'] for f in json.load(open(os.path.join(LY7, 'delivery-manifest.json'), encoding='utf-8'))['files']}
    goods = sorted({c['file'] for c in cases if c['id'].startswith('G-') and c.get('file')})
    gmap = {}
    for g in goods:
        rel7 = os.path.relpath(os.path.join(ROOT, g), LY7).replace('\\', '/')
        gmap[rel7] = {'sha256': sha(os.path.join(ROOT, g)), 'ly007Manifest': m7.get(rel7)}
    C.append({'id': 'C3-good-samples-are-LY007-bytes', 'pass': all(v['sha256'] == v['ly007Manifest'] for v in gmap.values()) and len(gmap) == 9,
              'detail': gmap, 'bind': {'LY-007/delivery-manifest.json': sha(os.path.join(LY7, 'delivery-manifest.json'))}})
    # C4 官方 checker
    of = J('qa/official-runs.json')
    inj = {r['card']: r for r in of['injectedComparison']}
    must = ['ly008-neg-oversize', 'ly008-neg-tris', 'ly008-neg-escape', 'ly008-neg-idx']
    ok4 = (of['runs']['baseline']['exitCode'] == 0 and of['runs']['injected']['exitCode'] == 1 and of['runs']['reverted']['exitCode'] == 0
           and all(inj[m]['officialCatches'] for m in must) and not inj['ly008-pos-s84']['officialCatches'] and not inj['ly008-neg-boundary']['officialCatches']
           and bool(of['blendInjectedCaught']) and of['revertedEqualsBaseline'] and of['labRepoUnchanged']
           and of['refusedOnRealRepo']['errorCodes'] == ['OFFICIAL_REFUSED_REAL_REPO'] and not of['refusedOnRealRepo']['ranBuildAssets']
           and of['copyIdentity']['_wholeTree']['identical'] and all(v['same'] for k, v in of['copyIdentity'].items() if k != '_wholeTree'))
    C.append({'id': 'C4-official-checker', 'pass': ok4,
              'detail': {'command': of['command'], 'spec': of['officialSpec']['spec'], 'limits': {k: of['officialSpec']['limits'][k] for k in ('glbMaxMB', 'glbWarnMB', 'trianglesMax', 'trianglesWarn')},
                         'exit': {k: v['exitCode'] for k, v in of['runs'].items()}, 'baselineCounts': of['runs']['baseline']['reportCounts'],
                         'copyWholeTree': of['copyIdentity']['_wholeTree'], 'labRepoUnchanged': of['labRepoUnchanged']},
              'bind': {k: v['commitBlobSha256'] for k, v in of['copyIdentity'].items() if k != '_wholeTree'} | {'qa/official-runs.json': sha(os.path.join(ROOT, 'qa', 'official-runs.json'))}})
    gaps = [r for r in of['injectedComparison'] if r['lyCheckCatches'] and not r['officialCatches']]
    C.append({'id': 'C5-official-coverage-gaps', 'pass': True, 'kind': 'finding',
              'detail': [{'card': r['card'], 'glbSha256': r['glbSha256'], 'lyCheck': r['lyCheckErrorCodes']} for r in gaps],
              'note': '这些负例官方 build_assets --check 判为通过（退出码只受其他卡影响），ly_check 判出；所以合并队列需要两者都跑'})
    # C6 普查
    ce = J('qa/census-bce3211.json'); cs = ce['summary']
    l1 = {}
    p1 = os.path.join(WP, 'LY-001', 'qa', 'glb-files.csv')
    if os.path.isfile(p1):
        for row in csv.DictReader(open(p1, encoding='utf-8')):
            l1[row['path']] = row['sha256']
    cross = [(r['path'], r['sha256'] == l1[r['path']]) for r in ce['rows'] if r['path'] in l1]
    C.append({'id': 'C6-census-vs-official-audit', 'pass': cs['statsMatchOfficialAudit'] == cs['glbFiles'] and cs['filesWithErrors'] == 0 and all(x[1] for x in cross),
              'detail': {'glbFiles': cs['glbFiles'], 'statsMatch': cs['statsMatchOfficialAudit'], 'filesWithErrors': cs['filesWithErrors'],
                         'warningCodeCounts': cs['warningCodeCounts'], 'shaCrossCheckWithLY001': {'compared': len(cross), 'equal': sum(1 for x in cross if x[1])}},
              'bind': {'qa/census-bce3211.json': sha(os.path.join(ROOT, 'qa', 'census-bce3211.json')), 'LY-001/qa/glb-files.csv': sha(p1) if os.path.isfile(p1) else None}})
    sp = J('qa/seat-packages.json')
    C.append({'id': 'C7-predecessor-packages', 'pass': all(not v['errorCodes'] for v in sp.values()),
              'detail': {k: {'entries': v['entries'], 'errors': v['errorCodes'], 'warnings': v['warningCodes'], 'manifestSha256': v['manifestSha256']} for k, v in sp.items()}})
    pv = J('qa/privacy-docs-bce3211.json')['reports'][0]
    C.append({'id': 'C8-docs-privacy', 'pass': True, 'kind': 'finding',
              'detail': {'files': pv['info'], 'errors': [i['msg'] for i in pv['issues'] if i['level'] == 'error'],
                         'errorHits': [h['kind'] for i in pv['issues'] if i['level'] == 'error' for h in i.get('hits', [])],
                         'weakWarnings': sum(1 for i in pv['issues'] if i['level'] == 'warning')},
              'note': 'bce3211 的 docs/asset-spec/README.md 有 2 处 D:/ 盘路径（源包落盘与待删目录说明）；交 LY-100/协调者定是否改写，本席位不改公共文件'})
    rows = {r['id']: r for r in st['rows']}
    sep = (rows['N11-oversize-15000004']['pass'] and rows['N11-oversize-15000004']['errorCodes'] == ['GLB_OVER_FORMAL_LIMIT']
           and rows['B11-boundary-15000000']['pass'] and rows['N12-upload-channel-14000000']['errorCodes'] == ['UPLOAD_OVER_CHANNEL_LIMIT']
           and rows['B12-same-file-no-channel-limit']['pass'] and rows['B12-same-file-no-channel-limit']['upload']['verdict'] == 'not-judged')
    C.append({'id': 'C9-formal-limit-vs-upload-channel', 'pass': sep,
              'detail': {k: {'bytes': rows[k]['bytes'], 'sha256': rows[k]['inputSha256'], 'errorCodes': rows[k]['errorCodes'], 'upload': rows[k]['upload']}
                         for k in ('N11-oversize-15000004', 'B11-boundary-15000000', 'N12-upload-channel-14000000', 'B12-same-file-no-channel-limit')}})
    out = {'seat': 'LY-008', 'commit': COMMIT, 'allPass': all(c['pass'] for c in C), 'checks': C}
    json.dump(out, open(os.path.join(ROOT, 'qa', 'checks.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    for c in C:
        print('PASS' if c['pass'] else 'FAIL', c['id'], c.get('kind', ''))


if __name__ == '__main__':
    main()
