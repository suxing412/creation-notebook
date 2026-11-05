#!/usr/bin/env python3
"""写 LY-008 的 delivery-manifest.json：白名单（路径、字节、SHA256、分类、是否公开、负例是否期望失败）、依赖、安装顺序、重算命令。
用法：python -I source/make_manifest.py <LY-008 目录>
不收：tmp/（导出副本、大体积负例、逐用例报告，均可按 recompute 重出）、native/（本席位无源工程）、status.json 与清单自身。
"""
import hashlib, json, os, sys

ROOT = os.path.abspath(sys.argv[1])
COMMIT = 'bce3211f818ee5a8bef1773539da70695ba37b17'


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def cls(rel):
    if rel.startswith('source/'):
        return 'checker-source'
    if rel.startswith('qa/negatives/'):
        return 'negative-fixture' if not rel.endswith('cases.json') else 'qa'
    if rel.startswith('qa/'):
        return 'qa'
    if rel.startswith('preview/'):
        return 'preview'
    return 'seat-doc'


def main():
    cases = json.load(open(os.path.join(ROOT, 'qa', 'negatives', 'cases.json'), encoding='utf-8'))['cases']

    def fixture_of(c):
        a = c.get('args', [])
        fx = {'cmd': c['cmd'], 'case': c['id'], 'expectCodes': c['expectCodes']}
        if '--profile' in a:
            fx['profile'] = a[a.index('--profile') + 1]
        if '--lod' in a:
            fx['lod'] = int(a[a.index('--lod') + 1])
        if '--private-token' in a:
            fx['privateTokens'] = [a[a.index('--private-token') + 1]]
        if '--upload-limit' in a:
            fx['note'] = 'upload 夹具：要带 --upload-limit 才判，package 检查下会显示为意外通过；只在 qa/selftest.json 里判'
        return fx
    by_path, by_sha = {}, {}
    for c in cases:
        if c.get('file', '').startswith('qa/negatives/'):
            by_path.setdefault(c['file'], c)
        if c.get('cmd') == 'glb' and c.get('sha256') and not c.get('args'):
            by_sha.setdefault(c['sha256'], c)
    files = []
    for top in ('brief.md', 'inputs.json', 'assembly.json', 'models', 'source', 'qa', 'preview'):
        full = os.path.join(ROOT, top)
        paths = [full] if os.path.isfile(full) else [os.path.join(dp, f) for dp, dn, fn in os.walk(full) for f in fn]
        for p in sorted(paths):
            rel = os.path.relpath(p, ROOT).replace('\\', '/')
            if '__pycache__' in rel:
                continue
            e = {'path': rel, 'bytes': os.path.getsize(p), 'sha256': sha(p), 'class': cls(rel), 'public': False}
            if rel.startswith('qa/negatives/') and rel.endswith('.glb'):
                c = by_path.get(rel) or by_sha.get(e['sha256'])   # 嵌套负例包里的 GLB 按字节认出是哪个用例的副本
                if c:
                    e['expectFail'] = c['expectFail']
                    if c['expectFail']:
                        e['fixture'] = fixture_of(c)
            files.append(e)
    big = [{'id': c['id'], 'file': c['file'], 'bytes': c['bytes'], 'sha256': c['sha256']} for c in cases if c.get('file', '').startswith('tmp/neg-big/')]
    seen = set()
    big = [b for b in big if not (b['file'] in seen or seen.add(b['file']))]
    man = {
        'seat': 'LY-008', 'commit': COMMIT, 'public': False,
        'note': '本席位只交检查器与证据，不产公共文件；全部 public=false。检查器若要进仓库（如 lab/tools/ 或 CI），由 LY-100 走合并队列。',
        'files': files,
        'totals': {'files': len(files), 'bytes': sum(f['bytes'] for f in files),
                   'negativeFixtures': sum(1 for f in files if f['class'] == 'negative-fixture')},
        'excluded': {'tmp/repo': f'git -C <lab> -c core.autocrlf=false archive {COMMIT} 的导出副本（官方 checker 在这里跑）',
                     'tmp/neg-big': {'why': '超过 1 MB 的体积/面数负例，按 make_negatives.py 逐字节重出', 'files': big},
                     'tmp/selftest': '逐用例完整报告，run_selftest.py 重出', 'native': '本席位没有源工程',
                     'self': ['delivery-manifest.json', 'status.json']},
        'dependencies': {
            'seats': {'LY-001': '快照与 glb-files.csv（普查 SHA 交叉核对）', 'LY-005': '坐标契约（节点缩放/镜像判据来源）',
                      'LY-007': '好样本 9 个 GLB、textures/manifest.json（她的贴图字节）、baseline/*.json（ly-p01 档判据）'},
            'repo': {'path': 'D:/GitHub/creation-notebook-lab', 'commit': COMMIT, 'access': '只读（git archive / ls-tree / show / status）'},
            'tools': ['Python 3.11（python -I）', 'numpy 2.x', 'Pillow（贴图解码复核；缺了只少一项）', 'git、tar（导出副本）'],
        },
        'install_order': [
            '1. 复制 source/ly_check.py 到任意位置（单文件，无同目录依赖）',
            '2. 单个 GLB：python -I ly_check.py [--json out.json] glb <file.glb> [--profile ly-p01 --lod N --tex-manifest <LY-007>/textures/manifest.json]',
            '3. 三档：python -I ly_check.py lodset <LOD0> <LOD1> <LOD2> --family house|default',
            '4. 席位包：python -I ly_check.py package <LY-###> [--glb-profile ly-p01 --tex-manifest …]',
            '5. 公共目录：python -I ly_check.py privacy <copy>/docs --archived <copy>/docs/asset-spec/source-archive.json',
            '6. 官方：python -I ly_check.py official <导出副本>（含 .git 的目录会被拒绝）',
            '退出码：有 error → 1；只有 warning → 0',
        ],
        'recompute': [
            'python -I source/run_all.py . ../LY-007 D:/GitHub/creation-notebook-lab ' + COMMIT + ' ..',
            '分步：python -I source/make_negatives.py . ../LY-007',
            '      python -I source/run_selftest.py . ../LY-007',
            '      python -I source/run_official.py . D:/GitHub/creation-notebook-lab ' + COMMIT,
            '      python -I source/calibrate.py . ..',
            '      python -I source/ly_check.py --json qa/privacy-docs-bce3211.json privacy tmp/repo/docs --archived tmp/repo/docs/asset-spec/source-archive.json',
            '      python -I source/draw_preview.py .',
            '      python -I source/checks.py . ../LY-007 D:/GitHub/creation-notebook-lab ' + COMMIT + ' ..',
            '      python -I source/make_manifest.py .',
        ],
    }
    json.dump(man, open(os.path.join(ROOT, 'delivery-manifest.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(len(files), 'files', man['totals']['bytes'], 'bytes')


if __name__ == '__main__':
    main()
