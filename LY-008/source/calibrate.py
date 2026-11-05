#!/usr/bin/env python3
"""用真实输入标定检查器（只读）：
1. bce3211 导出副本里 docs/**/*.glb 全部跑 ly_check（base 档），与官方 lab/tools/glb_audit.audit（副本里的同一文件）逐项比对
   bytes / triangles / vertices / primitives / materials / images，并统计 ly_check 的错误/警告代码；
2. 前置席位 LY-001、LY-005、LY-007 的交付包跑 package 检查（清单大小/SHA、路径越界、私密路径、包内 GLB）。

用法：python -I source/calibrate.py <LY-008 目录> <workpacks 目录>
结果：qa/census-bce3211.json、qa/census-bce3211.csv、qa/seat-packages.json
"""
import csv, glob, importlib.util, json, os, sys, collections

ROOT = os.path.abspath(sys.argv[1])
WP = os.path.abspath(sys.argv[2])
COPY = os.path.join(ROOT, 'tmp', 'repo')


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


lc = load('ly_check', os.path.join(ROOT, 'source', 'ly_check.py'))
ga = load('glb_audit_official', os.path.join(COPY, 'lab', 'tools', 'glb_audit.py'))


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    pats = lc.private_patterns()
    files = sorted(glob.glob(os.path.join(COPY, 'docs', '**', '*.glb'), recursive=True))
    rows, codes_e, codes_w, mism = [], collections.Counter(), collections.Counter(), []
    for i, f in enumerate(files):
        rel = os.path.relpath(f, os.path.join(COPY, 'docs')).replace('\\', '/')
        r = lc.check_glb(f, 'base', pats=pats, display_path=rel)
        d = r.as_dict()
        try:
            a = ga.audit(f)
        except Exception as e:  # noqa: BLE001
            a = {'issues': ['PARSE_ERROR:' + repr(e)]}
        row = {'path': rel, 'bytes': r.info.get('bytes'), 'sha256': r.info.get('sha256'), 'triangles': r.info.get('triangles'),
               'vertices': r.info.get('vertices'), 'primitives': r.info.get('primitives'), 'geometryRead': r.info.get('geometryRead'),
               'errors': d['errorCodes'], 'warnings': d['warningCodes'],
               'errorMsgs': [i['msg'][:160] for i in r.errors][:6],
               'official': {k: a.get(k) for k in ('bytes', 'triangles', 'vertices', 'primitives', 'materials', 'images', 'issues')}}
        diff = {k: (row[k] if k in row else None, a.get(k)) for k in ('bytes', 'triangles', 'vertices', 'primitives')
                if row.get(k) != a.get(k)}
        if len(r.info.get('materials') or []) != a.get('materials'):
            diff['materials'] = (len(r.info.get('materials') or []), a.get('materials'))
        if r.info.get('imageCount') != a.get('images'):
            diff['images'] = (r.info.get('imageCount'), a.get('images'))
        row['diffVsOfficial'] = diff
        if diff:
            mism.append(rel)
        codes_e.update(d['errorCodes']); codes_w.update(d['warningCodes'])
        rows.append(row)
        if i % 50 == 0:
            print(i, len(files), flush=True)
    summary = {'commit': 'bce3211f818ee5a8bef1773539da70695ba37b17', 'glbFiles': len(files),
               'filesWithErrors': sum(1 for r in rows if r['errors']), 'filesWithWarnings': sum(1 for r in rows if r['warnings']),
               'errorCodeCounts': dict(codes_e.most_common()), 'warningCodeCounts': dict(codes_w.most_common()),
               'statsMatchOfficialAudit': len(files) - len(mism), 'statsMismatchOfficialAudit': mism,
               'over15MB': [r['path'] for r in rows if (r['bytes'] or 0) > lc.GLB_MAX_BYTES],
               'checkerSha256': lc.sha256_file(os.path.join(ROOT, 'source', 'ly_check.py'))}
    json.dump({'summary': summary, 'rows': rows}, open(os.path.join(ROOT, 'qa', 'census-bce3211.json'), 'w', encoding='utf-8', newline='\n'),
              ensure_ascii=False, indent=1)
    with open(os.path.join(ROOT, 'qa', 'census-bce3211.csv'), 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['path', 'bytes', 'sha256', 'triangles', 'errors', 'warnings', 'officialTriangles', 'officialIssues', 'diffVsOfficial'])
        for r in rows:
            w.writerow([r['path'], r['bytes'], r['sha256'], r['triangles'], ';'.join(r['errors']), ';'.join(r['warnings']),
                        r['official'].get('triangles'), ';'.join(r['official'].get('issues') or []), json.dumps(r['diffVsOfficial'])])
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    # ---- 前置席位交付包 ----
    seats = {}
    for s in ('LY-001', 'LY-005', 'LY-007'):
        r = lc.check_package(os.path.join(WP, s), pats=pats)
        d = r.as_dict()
        seats[s] = {'errorCodes': d['errorCodes'], 'warningCodes': d['warningCodes'], 'entries': r.info.get('entries'),
                    'manifestKey': r.info.get('manifestKey'), 'totalBytes': r.info.get('totalBytes'), 'glbs': r.info.get('glbs'),
                    'issues': [{k: i[k] for k in ('level', 'code', 'msg')} for i in r.issues][:60],
                    'manifestSha256': lc.sha256_file(os.path.join(WP, s, 'delivery-manifest.json'))}
        print(s, d['errorCodes'], d['warningCodes'], r.info.get('entries'))
    json.dump(seats, open(os.path.join(ROOT, 'qa', 'seat-packages.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
