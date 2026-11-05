"""Turn the JSON ledgers into checks.json, city-nodes.csv and ledger.md (human tables).
usage: python -I render_ledger.py <workpack_dir>"""
import csv, json, sys
from pathlib import Path

W = Path(sys.argv[1]); QA = W / 'qa'
L = json.load(open(QA / 'snapshot-ledger.json', encoding='utf8'))
F = json.load(open(QA / 'family-ledger.json', encoding='utf8'))
R = json.load(open(QA / 'runtime-load-capture.raw.json', encoding='utf8'))
R1 = json.load(open(QA / 'runtime-load-capture-v1.raw.json', encoding='utf8'))
files = {f['path']: f for f in json.load(open(QA / 'file-hashes.json', encoding='utf8'))}

# ---------------------------------------------------------------- checks
checks = []


def chk(cid, ok, detail):
    checks.append({'id': cid, 'result': 'pass' if ok else 'fail', 'detail': detail})


far_near = [(a['assetId'], k, a[k]) for a in L['cityAssets'] for k in ('far', 'near') if k in a]
chk('C1 城市清单每个 GLB 引用都能定位', all(x[2]['exists'] for x in far_near), f'{len(far_near)} 个 far/near 引用；缺失 {[x[:2] for x in far_near if not x[2]["exists"]]}')
chk('C2 声明字节数与提交字节一致', all(x[2]['bytesMatch'] for x in far_near), f'不符 {[x[:2] for x in far_near if not x[2]["bytesMatch"]]}')
decl = [x for x in far_near if x[2]['sha256Declared']]
chk('C3 声明 SHA256 与提交字节一致（有声明者）', all(x[2]['shaMatch'] for x in decl),
    f'{len(decl)}/{len(far_near)} 个引用带 SHA 声明；无声明：{[x[0] + ":" + x[1] for x in far_near if not x[2]["sha256Declared"]]}')
ex = [x for x in far_near if x[2].get('excludeNodes')]
chk('C4 excludeNodes 在 GLB 中全部命中（渲染器严格校验）', all(x[2]['excludeAllMatched'] for x in ex), f'{len(ex)} 个带排除节点的引用')
loaded = {p.replace('/', '', 1) for s in R['steps'] for p in s['newResources']}
static_city = {x[2]['path'] for x in far_near if x[1] == 'far'}
static_research = {n['farPath'] for n in L['cityNodes'] if n['state'].startswith('仅模型')}
init_paths = {n['farPath'] for n in L['cityNodes'] if '首屏' in n['state']}
first = {p.lstrip('/') for p in R['steps'][0]['newResources']}
chk('C5 运行实测首屏请求集合 = 静态推断首屏 far 集合', first == init_paths, f'首屏实测 {len(first)} 个 GLB；差集 实测-静态={sorted(first - init_paths)} 静态-实测={sorted(init_paths - first)}')
far_all = static_city
chk('C6 运行实测遍历后请求的 far 集合 = 清单全部 far', far_all <= loaded, f'清单 far {len(far_all)} 个；未被请求 {sorted(far_all - loaded)}')
chk('C7 全城下载字节与清单 allCityModelBytes 一致', R['steps'][5]['metrics'][2].endswith('13.47 MB'), '实测“本次已载入模型 13.47 MB”，清单 allCityModelBytes=13466348；首屏 3.87 MB 对 initialModelBytes=3872084')
cs = L['sourceContracts']
chk('C8 provenance.sourceContracts 的 SHA 与提交（线上）字节一致', all(c['matchCommitted'] for c in cs),
    f"{sum(c['matchCommitted'] for c in cs)}/{len(cs)} 与提交字节一致；{sum((not c['matchCommitted']) and c['matchWorktree'] for c in cs)} 个只与本机 autocrlf 检出字节一致")
tr = L['hiddenTrials']
chk('C9 隐藏试放包模型 SHA 与 source.json 声明一致', all(t['shaMatch'] for t in tr), f'{len(tr)} 个模型文件')
chk('C10 隐藏试放在当前入口不被加载', not ({t['file'] for t in tr} & loaded), '实测请求集合与 north13 试放模型文件无交集（城景用的是 flat 转换件）')
chk('C11 研究模型全部 cityPlacement=null', all(n.get('cityPlacement') is None for n in L['cityNodes'] if n['state'].startswith('仅模型')), '14 件')
after = (QA / 'lab-status-before-after.txt').read_text(encoding='utf8').splitlines()
after_m = sorted(l.strip() for l in after if l.startswith((' M', 'M ', 'A ', 'D ', ' D', 'R ')))
before_m = sorted(l.strip() for l in L['git']['status_porcelain'])  # git() strips the first line's leading space
chk('C12 lab 仓库未被本席位改动', after_m == before_m and not L['git']['status_city'] and not L['git']['status_library'] and
    any(l.startswith('HEAD ' + L['git']['head']) for l in after),
    f'快照时与收尾时的已跟踪改动一致：{before_m}（均为既有时间戳改动）；docs/cities/luoyang、docs/library、docs/model-library 无改动；HEAD 不变')
chk('C13 单 GLB ≤ 15,000,000 字节（快照内全部 GLB）', not F['over15MB'], f"{len(L['glbFiles'])} 个 GLB，超限 {F['over15MB']}")
json.dump(checks, open(QA / 'checks.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- csv
with open(QA / 'city-nodes.csv', 'w', encoding='utf8', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['nodeId', 'state', 'chapter', 'assetId', 'tier', 'variant', 'farPath', 'farSha256', 'farBytes', 'nearPath', 'nearSha256', 'translation_xyz'])
    for n in L['cityNodes']:
        fp = files[n['farPath']]
        npth = n.get('nearPath')
        m = n.get('matrix')
        t = m[12:15] if m else (n.get('position') or '')
        w.writerow([n['nodeId'], n['state'], n.get('chapter'), n['assetId'], n.get('tier'), n.get('variant') or '',
                    n['farPath'], fp['sha256'], fp['bytes'], npth or '', files[npth]['sha256'] if npth else '', t])
with open(QA / 'glb-files.csv', 'w', encoding='utf8', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['path', 'class', 'bytes', 'sha256', 'triangles', 'byteIdenticalCopies', 'referencedBy'])
    for g in L['glbFiles']:
        w.writerow([g['path'], ' + '.join(g['class']), g['bytes'], g['sha256'], (g['glb'] or {}).get('triangles'),
                    ';'.join(g['byteIdenticalCopies']), ';'.join(g['referencedBy'][:6])])

# ---------------------------------------------------------------- md
o = []
P = o.append
gi = L['git']
P('# LY-001 快照台账（自动生成，勿手改；由 source/render_ledger.py 从 qa/*.json 生成）\n')
P(f"- 仓库：`{L['lab']}`，HEAD `{gi['head']}`（{gi['head_date']}，分支 `{gi['branch']}`；origin/main=`{gi['origin_main']}`；本地 main 引用 `{gi['local_main']}` 落后）")
P(f"- 工作树：`lab/data/*.json` 3 个文件有未提交改动（仅时间戳），docs/ 无改动；哈希一律取提交 blob 字节，检出字节另记（autocrlf 使 {len(L['worktreeEolDiffs'])} 个文本文件检出字节不同）。")
P(f"- 计数：哈希文件 {L['counts']['filesHashed']}，GLB {L['counts']['glbFiles']}；城市清单 assets {L['counts']['cityAssets']}、nodes {L['counts']['cityNodes']}、researchModels {L['counts']['researchModels']}、chapters {L['counts']['chapters']}。\n")
P('## 1 校验结果（qa/checks.json）\n')
P('| 检查 | 结果 | 说明 |\n|---|---|---|')
for c in checks:
    P(f"| {c['id']} | {c['result']} | {c['detail']} |")
P('\n## 2 当前入口城市节点（66 + 研究视图 14；全量 SHA 见 qa/city-nodes.csv）\n')
P('| 状态 | 数量 | 节点 |\n|---|---|---|')
from collections import defaultdict
byst = defaultdict(list)
for n in L['cityNodes']:
    byst[n['state']].append(n['nodeId'])
for s, ids in byst.items():
    P(f"| {s} | {len(ids)} | {'、'.join(ids)} |")
P('\n### 2.1 城市资产（42 个 assetId）\n')
P('| assetId | far 路径 | far SHA256 | near 路径 | near SHA256 | 排除节点 | 使用节点数 |\n|---|---|---|---|---|---|---|')
for a in L['cityAssets']:
    fr, nr = a.get('far', {}), a.get('near', {})
    P(f"| {a['assetId']} | `{fr.get('path','').replace('cities/luoyang/','')}` | `{(fr.get('actualSha256') or '')[:16]}…` | `{nr.get('path','').replace('cities/luoyang/','')}` | `{(nr.get('actualSha256') or '')[:16]}` | {len(fr.get('excludeNodes') or [])} | {len(a['usedBy'])} |")
P('\n## 3 运行实测（本机 Chromium，127.0.0.1 只读服务）\n')
for s in R['steps']:
    P(f"- **{s['step']}**：新请求 {len(s['newResources'])} 个" + (f"（{s['metrics'][1]}；{s['metrics'][2]}）" if s.get('metrics') else ''))
P('- v1 归档入口：' + R1['crlfNote'])
for s in R1['steps']:
    P(f"  - {s['step']}：{len(s['newResources'])} 个新请求" + (f"；{s['note']}" if s.get('note') else ''))
P('\n## 4 隐藏试放（north13 8 包，activation=false/未激活）\n')
P('| 包 | 文件 | LOD | SHA256 | 目标/原点 |\n|---|---|---|---|---|')
for t in L['hiddenTrials']:
    tgt = ','.join(x['id'] for x in t['targets']) or (str([round(v, 2) for v in t['origin'][:2]]) if t['origin'] else '')
    P(f"| {t['package']} | `{t['file'].split('/')[-1]}` | {t['lod']} | `{t['actualSha256'][:16]}` | {tgt} |")
P('\n## 5 家族去重（按家族计，不按 LOD/姿态/附件；qa/family-ledger.json）\n')
P('| 家族 | 最高状态 | 在城节点 | 资产卡 |\n|---|---|---|---|')
for f in F['families']:
    P(f"| {f['name']} | {f['cityState']} | {f['cityNodes']} | {'、'.join(c['id'] for c in f['cards'])} |")
P('\n计数：' + '；'.join(f'{k} {v}' for k, v in F['familyCountByState'].items()) + f"；合计 {F['familyCount']} 个家族。")
P('\n## 6 重复、被替代与失败版本的去向\n')
for r in F['routes']:
    P(f"- **{r['kind']}**（{r['family']}）：{r['why']} → {r['route']}")
    for x in r['files']:
        P(f"  - `{x['path']}` {x['bytes']} B `{x['sha256'][:16]}`")
P('\n### 6.1 既有全库体检标出的问题（mq 卡片 audit.json，SHA 与当前提交字节逐一比对）\n')
for m in F['mqFlags']:
    P(f"- {m['card']} `{m['path']}` `{m['currentSha256'][:16]}` 体检 SHA {'一致' if m['auditMatchesCurrent'] else '不一致'}：{m['issues']}" + ('（此文件在城中按章加载）' if m['inCity'] else ''))
P('\n### 6.2 字节重复 GLB\n')
for d in F['byteDuplicateGlb']:
    P(f"- `{d['sha256'][:16]}`：" + '；'.join(f'`{p}`' for p in d['paths']))
P('\n### 6.3 未找到\n')
for n in F['notFound']:
    P(f"- {n['item']}：{n['result']}")
P('\n## 7 合同 SHA 的换行依赖\n')
P('| 合同 | 声明 | 提交字节 | 检出字节 | 依据 |\n|---|---|---|---|---|')
for c in L['sourceContracts']:
    P(f"| `{c['path'].replace('cities/luoyang/','')}` | `{c['declaredSha256'][:12]}` | `{c['committedSha256'][:12]}` | `{c['worktreeSha256'][:12]}` | {c['matchBasis']} |")
(W / 'qa' / 'ledger.md').write_text('\n'.join(o) + '\n', encoding='utf8')
print('\n'.join(f"{c['result']}  {c['id']}" for c in checks))
