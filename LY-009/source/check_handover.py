"""LY-009 daily-handover checker.

python -I check_handover.py <handover.json> [--root <workpacks root>]

1. JSON Schema (templates/daily-handover.schema.json, jsonschema Draft 2020-12);
2. semantic rules the schema cannot express:
   H1 '已入城' may be '做到' only for LY-100 (city write is LY-100's);
   H2 every '做到' claim carries evidence and a sha256 that is one of the listed products/sources;
   H3 status 交付完成/复用完成 needs at least one product;
   H4 cityReadiness '可接城' needs cityAdmissionRef (LY-010 entry);
   H5 products paths pass the seat whitelist (check_whitelist R1-R6);
   H6 with --root: every product exists, and its bytes/sha256 match the file on disk.
"""
import hashlib, json, os, sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_whitelist  # noqa: E402
import jsonschema  # noqa: E402

SCHEMA = os.path.join(HERE, '..', 'templates', 'daily-handover.schema.json')


def check(h, root=None):
    errs = []
    schema = json.load(open(SCHEMA, encoding='utf-8'))
    v = jsonschema.Draft202012Validator(schema)
    for e in sorted(v.iter_errors(h), key=lambda e: list(e.path)):
        errs.append(f"schema: {'/'.join(map(str, e.path)) or '(root)'}: {e.message[:160]}")
    if errs:
        return errs
    seat = h['seat']
    shas = {p['sha256'] for p in h['products']} | {s['sha256'] for s in h['sources'] if s.get('sha256')}
    for k, c in h['fiveClaims'].items():
        if c['result'] == '做到':
            if k == '已入城' and seat != 'LY-100':
                errs.append('H1: 已入城 只能由 LY-100 写「做到」')
            if not c.get('evidence') or c.get('sha256') not in shas:
                errs.append(f'H2: {k}=做到 但缺证据或 sha256 不在本交接的产物/来源中')
    if h['status'] in ('交付完成', '复用完成') and not h['products']:
        errs.append('H3: 声明完成但没有产物')
    if h['cityReadiness'] == '可接城' and not h.get('cityAdmissionRef'):
        errs.append('H4: 可接城 需写 LY-010 准入条目')
    for p in h['products']:
        r = check_whitelist.classify(f"{seat}/{p['path']}", seat, p['bytes'])
        if not r['ok']:
            errs.append(f"H5: {p['path']}: {r['rule']} {r['reason']}")
        if root:
            fp = os.path.join(root, seat, p['path'])
            if not os.path.isfile(fp):
                errs.append(f"H6: {p['path']} 不存在")
            else:
                b = open(fp, 'rb').read()
                if len(b) != p['bytes'] or hashlib.sha256(b).hexdigest() != p['sha256']:
                    errs.append(f"H6: {p['path']} 字节或 SHA 与磁盘不符")
    return errs


if __name__ == '__main__':
    a = sys.argv[1:]
    root = a[a.index('--root') + 1] if '--root' in a else None
    h = json.load(open(a[0], encoding='utf-8'))
    errs = check(h, root)
    print(json.dumps({'file': a[0], 'verdict': 'PASS' if not errs else 'FAIL', 'errors': errs}, ensure_ascii=False, indent=1))
    sys.exit(0 if not errs else 1)
