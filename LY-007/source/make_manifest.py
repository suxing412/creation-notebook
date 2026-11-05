# -*- coding: utf-8 -*-
"""生成 qa/checks.json（从各 qa 结果文件读数判定，不手填）与 delivery-manifest.json（白名单、大小、SHA256、分类、依赖、重算顺序）。
用法: python -I make_manifest.py <LY-007 目录>
delivery-manifest.json 与 status.json 不列入自身白名单的 SHA（避免自引用），其余交付文件逐个入账。
"""
import sys, os, json, hashlib, subprocess

W = os.path.abspath(sys.argv[1])
J = lambda p: json.load(open(os.path.join(W, p), encoding='utf-8'))
sha = lambda p: hashlib.sha256(open(os.path.join(W, p), 'rb').read()).hexdigest()
C = 'bce3211f818ee5a8bef1773539da70695ba37b17'
checks = []


def add(cid, criterion, evidence, ok, measured, recompute):
    checks.append(dict(id=cid, criterion=criterion, result='通过' if ok else '未通过', measured=measured,
                       evidence={e: sha(e) for e in evidence}, recompute=recompute))


tp = J('qa/texture-provenance.json')['summary']
add('K1', '贴图字节与 manifest 一致，LY_P01 贴图与她提交 GLB 嵌入字节逐字节相同', ['qa/texture-provenance.json', 'textures/manifest.json'],
    tp['all_manifest_match'] and tp['non_legacy_with_byte_identical_source_in_commit'] == tp['non_legacy'], tp,
    f'python -I source/verify_textures.py . <lab> {C}')
sem = J('baseline/LY_P01-material-semantics.json')
rt = {m['material']: m['flat']['roundtrip_int_srgb_to_linear_float32_bit_exact'] for m in sem['materials']}
add('K2', 'FLAT 线性因子 = 8-bit sRGB 整数色经换算的 float32，逐位可重算', ['baseline/LY_P01-material-semantics.json'], all(rt.values()), rt,
    f'python -I source/make_semantics.py . <lab> {C}')
rb = J('qa/readback.json')
iss = {k: v['issues'] for k, v in rb.items()}
cs = {k: sorted({(i['name'], i['colorspace']) for i in v['reimport']['images']}) for k, v in rb.items() if v['reimport']['images']}
uvc = {k: {n: x['uv_spans'] for n, x in v['uv_calibration'].items()} for k, v in rb.items() if v['uv_calibration']}
add('K3', '基准球与样件经官方导入器重读：材质语义、FLAT 逐位、贴图属共享库且分辨率对档、颜色空间、世界盒式 UV、1 m 标定块',
    ['qa/readback.json'] + [k for k in rb], all(not v for v in iss.values()),
    dict(files=len(rb), files_with_issues=sum(1 for v in iss.values() if v), uv_calibration=uvc,
         colorspaces_lod0_refsphere=cs.get('models/refsphere/lyref-A-LOD0.glb')),
    'D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P source/readback_blender.py -- . models/refsphere/*.glb models/samples/*.glb')
cmp_ = J('qa/sample-vs-original.json')
flags = ['nodes_equal', 'meshes_equal', 'materials_equal', 'material_json_equal', 'images_order_equal', 'image_bytes_equal',
         'bufferview_lengths_equal', 'bufferview_offsets_equal', 'samplers_equal']
okc = all(all(v[f] for f in flags) and all(n['triangle_match'] == 1.0 and n['corner_match_pos_normal_uv'] == 1.0 for n in v['per_node']) for v in cmp_.values())
add('K4', '样件与她的提交字节原件：结构逐项相同，顶点（位置+法线+UV）与三角形吻合 1.0', ['qa/sample-vs-original.json'], okc,
    {k: dict(generator=v['generator'], min_triangle_match=min(n['triangle_match'] for n in v['per_node'])) for k, v in cmp_.items()},
    'git show <commit>:<path> > tmp/orig/...；python -I source/round2/compare.LY007.py models/samples tmp/orig qa/sample-vs-original.json')
rbd = J('qa/round2-rebuild.json')
add('K5', '样件可由冻结库 + 原字节贴图逐字节重出', ['qa/round2-rebuild.json'], rbd['all_identical'], [(r['file'], r['byte_identical']) for r in rbd['files']],
    rbd['command'] + '；python -I source/rebuild_check.py .')
ld = J('qa/lod-diff.json')
lr = {g: dict(ratio=v['ratio'], bbox_delta=v['bbox_size_delta_vs_lod0_m'], copy=[k for k, c in v['copy_check'].items() if c['is_lod0_copy']]) for g, v in ld.items()}
ok_ratio = all(0.17 <= ld[g]['ratio']['LOD1'] <= 0.62 and 0.05 <= ld[g]['ratio']['LOD2'] <= 0.20 for g in ('S84', 'G10', 'lyref'))
ok_copy = all(not lr[g]['copy'] for g in ('S84', 'G10', 'S84_orig', 'G10_orig', 'lyref')) and lr['NEG_lod0_copied_as_lod1']['copy'] == ['LOD1']
ok_bbox = all(all(abs(x) < 1e-6 for x in ld[g]['bbox_size_delta_vs_lod0_m']['LOD1']) for g in ('S84', 'G10', 'lyref'))
add('K6', '三档差异：面数比在验收区间、LOD1 包围盒与 LOD0 相同、无 LOD0 复制；负例被判出', ['qa/lod-diff.json'], ok_ratio and ok_copy and ok_bbox, lr,
    'python -I source/lod_diff.py qa/lod-diff.json S84=models/samples:S84-LOD{lod}.glb ...（见 recompute）')
nr = J('qa/near-retention.json')['summary']
add('K7', '原近景可恢复：城中引用提交字节 SHA 全一致、近远档字节不同、无三档复制 LOD0', ['qa/near-retention.json'],
    nr['city_refs'] == nr['city_refs_match'] and not nr['near_far_same_bytes'] and not nr['stems_with_tier_copy_of_LOD0'],
    {k: nr[k] for k in ('city_refs', 'city_refs_match', 'near_refs', 'near_far_pairs', 'tier_stems')} | {'stems_without_LOD0': len(nr['stems_without_LOD0'])},
    f'python -I source/near_retention.py . <lab> {C}')
lt = J('qa/lib-negative-tests.json')
add('K8', '冻结库反例测试（悬空、穿插、共面、净空、落地、GLB 自检、LOD 派生、檐口瓦、门扇单独节点三档导出）', ['qa/lib-negative-tests.json'],
    all(t['pass'] for t in lt), f'{sum(t["pass"] for t in lt)}/{len(lt)}',
    'D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P source/run_lib_tests.py -- . <abs>/tmp/testchecks')
sizes = {p: os.path.getsize(os.path.join(W, p)) for p in [f'models/refsphere/lyref-A-LOD{l}.glb' for l in range(3)] + [f'models/samples/{m}-LOD{l}.glb' for m in ('S84', 'G10') for l in range(3)]}
add('K9', '单 GLB ≤ 15,000,000 字节', [], all(v <= 15_000_000 for v in sizes.values()), sizes, 'stat')
lab = subprocess.run(['git', '-C', 'D:/GitHub/creation-notebook-lab', 'status', '--short'], capture_output=True, text=True).stdout.strip().splitlines()
add('K10', 'lab 仓库只读（收尾时 git status）', [], all(l.startswith('?? .claude') for l in lab), lab, 'git -C <lab> status --short')
cen = J('qa/census-bce3211.json')['summary']
checks.append(dict(id='I1', criterion='现状普查（信息项，不判通过）', result='记录', measured={k: cen[k] for k in ('files', 'compliant', 'deviation_counts', 'over_15MB')},
                   evidence={'qa/census-bce3211.json': sha('qa/census-bce3211.json'), 'qa/census-bce3211.csv': sha('qa/census-bce3211.csv')},
                   recompute=f'python -I source/census.py . <lab> {C}'))
json.dump(dict(seat='LY-007', commit=C, checks=checks), open(os.path.join(W, 'qa', 'checks.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# ---- manifest ----
CLASS = [('models/', 'model-baseline（基准件/样件，研究用，未入城）'), ('textures/', 'baseline-texture（她的原字节贴图副本）'),
         ('baseline/', 'baseline-contract'), ('source/', 'source（生成器/检查器，非公共 docs）'), ('qa/', 'qa-evidence'),
         ('preview/', 'preview（CPU 渲染）')]
files = []
for root, dirs, fs in os.walk(W):
    rel = os.path.relpath(root, W).replace('\\', '/')
    if rel.split('/')[0] in ('tmp', 'native', '__pycache__') or '__pycache__' in rel:
        continue
    for f in sorted(fs):
        p = (f if rel == '.' else f'{rel}/{f}')
        if p in ('delivery-manifest.json', 'status.json') or f.endswith('.pyc'):
            continue
        cls = next((c for pre, c in CLASS if p.startswith(pre)), 'seat-doc')
        files.append(dict(path=p, bytes=os.path.getsize(os.path.join(W, p)), sha256=sha(p), class_=cls))
for f in files:
    f['class'] = f.pop('class_')
man = dict(
    seat='LY-007', commit=C, public=False,
    note='本席位不产生公共 docs 文件；全部为工作包内的基线契约、基准件、证据。进入公共文件须另走 LY-100',
    excluded=dict(native='native/lyref-A.blend（源工程，不进 git，不入白名单）', tmp='tmp/（她的原件提交字节导出、重建副本、负例、渲染原图；可按 recompute 重出）',
                  self=['delivery-manifest.json', 'status.json']),
    dependencies=dict(seats=['LY-001'], repo_commit=C, tools=['D:/Blender/blender.exe 5.2.1', 'python -I（numpy、Pillow）',
                                                               '<scratch>/mq/render.py sha256 ff89761743a064f7d599835e3e3123f330ca152df43634717c312ece667d4dc7']),
    install_order=['baseline/*.json 与 LY-style-bible.frozen.md（读）', 'textures/（贴图目录）', 'source/lib/ly_style.py（import 后设 ly.TEX_DIR）',
                   'models/refsphere、models/samples（对照件）', 'source/readback_blender.py、source/lod_diff.py（下游自检）'],
    recompute=[
        f'python -I source/verify_textures.py . D:/GitHub/creation-notebook-lab {C}',
        f'python -I source/make_semantics.py . D:/GitHub/creation-notebook-lab {C}',
        'D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P source/build_refsphere.py -- .',
        'D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P source/readback_blender.py -- . models/refsphere/lyref-A-LOD0.glb models/refsphere/lyref-A-LOD1.glb models/refsphere/lyref-A-LOD2.glb models/samples/S84-LOD0.glb models/samples/S84-LOD1.glb models/samples/S84-LOD2.glb models/samples/G10-LOD0.glb models/samples/G10-LOD1.glb models/samples/G10-LOD2.glb',
        f'python -I source/census.py . D:/GitHub/creation-notebook-lab {C}',
        'for each of S84/G10 LOD0-2: git -C D:/GitHub/creation-notebook-lab show ' + C + ':<path> > tmp/orig/<file>',
        'D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P source/round2/build_round2.LY007.py -- tmp/rebuild',
        'python -I source/rebuild_check.py .',
        'python -I source/round2/compare.LY007.py models/samples tmp/orig qa/sample-vs-original.json',
        'cp S84-LOD0 as tmp/neg/NEG-LOD0 and NEG-LOD1, S84-LOD2 as NEG-LOD2; python -I source/lod_diff.py qa/lod-diff.json S84=models/samples:S84-LOD{lod}.glb G10=models/samples:G10-LOD{lod}.glb S84_orig=tmp/orig:S84-LOD{lod}.glb G10_orig=tmp/orig:G10-LOD{lod}.glb lyref=models/refsphere:lyref-A-LOD{lod}.glb NEG_lod0_copied_as_lod1=tmp/neg:NEG-LOD{lod}.glb',
        f'python -I source/near_retention.py . D:/GitHub/creation-notebook-lab {C}',
        'D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P source/run_lib_tests.py -- . <abs LY-007>/tmp/testchecks; cp tmp/testchecks/test_report.json qa/lib-negative-tests.json',
        'render: D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P <scratch>/mq/render.py -- <glb> <ABSOLUTE LY-007>/tmp/r <prefix> <views>（输出目录必须写绝对路径）',
        'python -I source/sheets.py .',
        'python -I source/make_manifest.py .'],
    files=files, totals=dict(count=len(files), bytes=sum(f['bytes'] for f in files)))
json.dump(man, open(os.path.join(W, 'delivery-manifest.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print([(c['id'], c['result']) for c in checks]); print(man['totals'])
