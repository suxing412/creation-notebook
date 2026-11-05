#!/usr/bin/env python3
"""LY-008 检查器自检：对 qa/negatives/cases.json 的每个用例，通过命令行入口（子进程）真正跑一次 ly_check.py，
断言：期望失败的用例退出码 = 1 且期望的错误代码全部出现；期望通过的用例退出码 = 0 且没有错误。
同时重算每个输入文件的 SHA256 与 cases.json 对比（输入被改过就判自检失败）。

用法：python -I source/run_selftest.py <LY-008 目录> <LY-007 目录>
结果：qa/selftest.json；每个用例的完整报告在 tmp/selftest/<id>.json（可重算，不进白名单）。
"""
import hashlib, json, os, subprocess, sys

ROOT = os.path.abspath(sys.argv[1])
LY7 = os.path.abspath(sys.argv[2])
CHK = os.path.join(ROOT, 'source', 'ly_check.py')
OUT = os.path.join(ROOT, 'tmp', 'selftest')


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def rel(p):
    return os.path.relpath(p, ROOT).replace('\\', '/')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    os.makedirs(OUT, exist_ok=True)
    cases = json.load(open(os.path.join(ROOT, 'qa', 'negatives', 'cases.json'), encoding='utf-8'))['cases']
    rows, bad = [], 0
    for c in cases:
        args = [a.replace('{LY7}', LY7) for a in c.get('args', [])]
        jp = os.path.join(OUT, c['id'] + '.json')
        if c['cmd'] == 'glb':
            target = [os.path.join(ROOT, c['file'])]
        elif c['cmd'] == 'lodset':
            target = [os.path.join(ROOT, f) for f in c['files']]
        else:
            target = [os.path.join(ROOT, c['dir'])]
        # 全局选项（--json、--private-token）放在子命令前
        glob_args, sub_args = ['--json', jp], []
        it = iter(args)
        for a in it:
            if a == '--private-token':
                glob_args += [a, next(it)]
            else:
                sub_args.append(a)
        cmd = [sys.executable, '-I', CHK, *glob_args, c['cmd'], *target, *sub_args]
        pr = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        rep = json.load(open(jp, encoding='utf-8'))
        errs = sorted({code for r in rep['reports'] for code in r['errorCodes']})
        warns = sorted({code for r in rep['reports'] for code in r['warningCodes']})
        sha_ok = True
        if c['cmd'] == 'glb' and 'sha256' in c:
            got = sha(target[0])
            sha_ok = got == c['sha256']
        if c['expectFail']:
            ok = pr.returncode == 1 and set(c['expectCodes']) <= set(errs)
        else:
            ok = pr.returncode == 0 and not errs
        ok = ok and sha_ok
        bad += not ok
        info = rep['reports'][0]['info']
        rows.append({'id': c['id'], 'cmd': c['cmd'], 'inject': c['inject'], 'expectFail': c['expectFail'], 'expectCodes': c['expectCodes'],
                     'exitCode': pr.returncode, 'errorCodes': errs, 'warningCodes': warns, 'inputSha256OK': sha_ok,
                     'inputSha256': c.get('sha256'), 'bytes': c.get('bytes'),
                     'upload': info.get('upload') if c['cmd'] == 'glb' else None,
                     'command': ' '.join(['python', '-I', 'source/ly_check.py', *[a if not os.path.isabs(a) else rel(a) for a in glob_args[2:]],
                                          c['cmd'], *[rel(t) for t in target], *[a.replace(LY7, '{LY7}') for a in sub_args]]),
                     'pass': ok})
        print(('PASS' if ok else 'FAIL'), c['id'], 'exit', pr.returncode, errs)
    # 自检本身的反证：把好样件当成「期望失败」、把 N04 当成「期望通过」，判定逻辑必须两次都给出不通过
    sanity = []
    for f, exp_fail, codes in ((os.path.join(LY7, 'models', 'samples', 'S84-LOD0.glb'), True, ['GEOM_NONFINITE']),
                               (os.path.join(ROOT, 'qa', 'negatives', 'N04-nan-position.glb'), False, [])):
        jp = os.path.join(OUT, 'sanity.json')
        pr = subprocess.run([sys.executable, '-I', CHK, '--json', jp, 'glb', f], capture_output=True, text=True, encoding='utf-8', errors='replace')
        errs = sorted({code for r in json.load(open(jp, encoding='utf-8'))['reports'] for code in r['errorCodes']})
        ok = (pr.returncode == 1 and set(codes) <= set(errs)) if exp_fail else (pr.returncode == 0 and not errs)
        sanity.append({'file': rel(f), 'pretendExpectFail': exp_fail, 'harnessVerdictPass': ok, 'detectedAsWrong': not ok})
    bad += sum(1 for s_ in sanity if not s_['detectedAsWrong'])
    n_neg = sum(1 for r in rows if r['expectFail'])
    summary = {'cases': len(rows), 'negatives': n_neg, 'positives': len(rows) - n_neg,
               'negativesCaught': sum(1 for r in rows if r['expectFail'] and r['pass']),
               'positivesPassed': sum(1 for r in rows if not r['expectFail'] and r['pass']), 'selftestFailures': bad,
               'checkerSha256': sha(CHK), 'casesSha256': sha(os.path.join(ROOT, 'qa', 'negatives', 'cases.json')),
               'python': sys.version.split()[0], 'harnessSanity': sanity}
    json.dump({'summary': summary, 'rows': rows}, open(os.path.join(ROOT, 'qa', 'selftest.json'), 'w', encoding='utf-8', newline='\n'),
              ensure_ascii=False, indent=1)
    print(json.dumps(summary, ensure_ascii=False))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
