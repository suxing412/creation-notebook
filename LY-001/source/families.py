"""Family de-duplication, superseded/failed-version routing.  Pure function of
qa/snapshot-ledger.json (+ mq audit sha check).  usage: python -I families.py <qa_dir>"""
import json, sys
from collections import defaultdict
from pathlib import Path

QA = Path(sys.argv[1])
L = json.load(open(QA / 'snapshot-ledger.json', encoding='utf8'))
files = {f['path']: f for f in json.load(open(QA / 'file-hashes.json', encoding='utf8'))}
glbrows = {g['path']: g for g in L['glbFiles']}

# city asset -> family (by delivered identity; variants/LODs/attachments are not new families)
CITY_FAMILY = {
    'courtyard-A': 'F-courtyard', 'courtyard-B': 'F-courtyard', 'courtyard-TC03': 'F-courtyard',
    'courtyard-A2': 'F-courtyard', 'courtyard-B2': 'F-courtyard', 'courtyard-TC03-2': 'F-courtyard',
    'wall-direct-gate-body-only': 'F-gate-guangyang', 'yong-gate-near': 'F-gate-yong', 'yong-gate-apron': 'F-gate-yong',
    'market-main': 'F-market', 'market-N2': 'F-market', 'storage-main': 'F-storage',
    'study-lingtai': 'F-lingtai', 'study-taixue-A': 'F-taixue-hall', 'study-taixue-B': 'F-taixue-hall',
    'study-north13-kaiyang-K': 'F-gate-kaiyang', 'study-north13-pingcheng-P': 'F-gate-pingcheng',
    'study-north13-shangxi-X': 'F-gate-shangxi', 'study-north13-zhongdong-Z': 'F-gate-zhongdong',
    'study-north13-yong-Y': 'F-gate-yong', 'study-mao-gate': 'F-gate-mao',
    'study-north13-court-A': 'F-courtyard', 'study-north13-court-A2': 'F-courtyard', 'study-north13-court-B': 'F-courtyard',
    'study-north13-court-B2': 'F-courtyard', 'study-north13-court-TC03-2': 'F-courtyard',
}
for a in L['cityAssets']:
    if a['assetId'].startswith('wall-'):
        CITY_FAMILY.setdefault(a['assetId'], 'F-citywall')
    if a['assetId'].startswith('ground-'):
        CITY_FAMILY[a['assetId']] = 'F-ground-road'
CARD_FAMILY = {
    'm-courtyard-family': 'F-courtyard', 'm-luoyang-yong-gate': 'F-gate-yong', 'm-luoyang-guangyang-gate': 'F-gate-guangyang',
    'm-market-functional': 'F-market', 'm-storage-functional': 'F-storage', 'm-luoyang-lingtai': 'F-lingtai',
    'm-luoyang-taixue-a': 'F-taixue-hall', 'm-luoyang-kaiyang-gate': 'F-gate-kaiyang', 'm-luoyang-pingcheng-gate': 'F-gate-pingcheng',
    'm-luoyang-shangxi-gate': 'F-gate-shangxi', 'm-luoyang-zhongdong-gate': 'F-gate-zhongdong', 'm-luoyang-mao-gate': 'F-gate-mao',
}
PACKAGE_FAMILY = {
    'luoyang-kaiyang-gate-study-v1': 'F-gate-kaiyang', 'luoyang-pingcheng-gate-study-v1': 'F-gate-pingcheng',
    'luoyang-shangxi-gate-study-v1': 'F-gate-shangxi', 'luoyang-yong-gate-study-v1': 'F-gate-yong',
    'luoyang-zhongdong-gate-study-v1.1': 'F-gate-zhongdong', 'luoyang-north-four-courts-v2': 'F-courtyard',
    'luoyang-north-perimeter-v1': 'F-courtyard', 'luoyang-north-second-row-v1': 'F-courtyard',
}
NAMES = {
    'F-courtyard': '住宅院落家族（R01-A/B、TC03、A2/B2/TC03-2 变体）', 'F-citywall': '城垣（A 段＋direct 转接段）',
    'F-gate-guangyang': '广阳门', 'F-gate-yong': '雍门', 'F-ground-road': '道路与地面（ground-atomic）',
    'F-market': '市肆功能组（五店三摊＋N2 替换）', 'F-storage': '仓储作业组（太仓候选附近）', 'F-lingtai': '灵台',
    'F-taixue-hall': '太学长堂（A/B 两方案）', 'F-gate-kaiyang': '开阳门', 'F-gate-pingcheng': '平城门',
    'F-gate-shangxi': '上西门', 'F-gate-zhongdong': '中东门', 'F-gate-mao': '旄门',
}
RANK = ['已入城·首屏默认加载', '已入城·按章加载（initial=false）', '隐藏试放（activation=false）',
        '仅模型·独立研究视图（cityPlacement=null，城中不渲染）', '仅模型（资产卡文件）']

fam = defaultdict(lambda: {'members': [], 'cards': [], 'states': set()})
for n in L['cityNodes']:
    f = CITY_FAMILY[n['assetId']]
    fam[f]['states'].add(n['state'])
    fam[f]['members'].append({'kind': 'cityNode', 'id': n['nodeId'], 'asset': n['assetId'], 'state': n['state'],
                              'far': n.get('farPath'), 'farSha256': files[n['farPath']]['sha256'],
                              'near': n.get('nearPath'), 'nearSha256': n.get('nearPath') and files[n['nearPath']]['sha256']})
for t in L['hiddenTrials']:
    f = PACKAGE_FAMILY[t['package']]
    fam[f]['states'].add('隐藏试放（activation=false）')
    fam[f]['members'].append({'kind': 'hiddenTrial', 'package': t['package'], 'file': t['file'], 'sha256': t['actualSha256'],
                              'lod': t['lod'], 'targets': [x['id'] for x in t['targets']], 'activation': t['activation']})
for c in L['cards']:
    if not c['isLuoyang'] or c['id'] == 'p-luoyang':
        continue
    f = CARD_FAMILY.get(c['id'], 'C:' + c['id'])
    fam[f]['cards'].append({'id': c['id'], 'title': c['title'], 'status': c['status'], 'files': len(c['files']),
                            'bytes': sum(x['bytes'] or 0 for x in c['files'])})
    if f.startswith('C:'):
        fam[f]['states'].add('仅模型（资产卡文件）')
        NAMES[f] = c['title']

families = []
for k, v in fam.items():
    st = sorted(v['states'] or {'仅模型（资产卡文件）'}, key=lambda s: RANK.index(s) if s in RANK else 99)
    families.append({'family': k, 'name': NAMES.get(k, k), 'cityState': st[0], 'allStates': st,
                     'cityNodes': sum(1 for m in v['members'] if m['kind'] == 'cityNode' and m['state'].startswith('已入城')),
                     'cards': v['cards'], 'members': v['members']})
families.sort(key=lambda f: (RANK.index(f['cityState']) if f['cityState'] in RANK else 99, f['family']))

# ------------------------------------------------ superseded / duplicate / failed routing
G = lambda p: glbrows.get(p) or {}
routes = []


def add(kind, family, paths, why, route):
    routes.append({'kind': kind, 'family': family, 'files': [{'path': p, 'sha256': files[p]['sha256'], 'bytes': files[p]['bytes'],
                                                              'class': G(p).get('class')} for p in paths if p in files],
                   'why': why, 'route': route})


C = 'cities/luoyang/'
add('同家族重复展示', 'F-gate-yong',
    [C + 'progress-assets/flat/study-north13-yong-Y-1983dab58385.glb', C + 'progress-assets/north13-gates/luoyang-yong-gate-study-v1/models/yong-Y-LOD1.glb',
     C + 'progress-assets/north13-gates/luoyang-yong-gate-study-v1/models/yong-Y-LOD2.glb'],
    '雍门已以 yong-Y-LOD0＋yong-apron 在城中首屏加载；城墙章仍列出“雍门 · 研究候选”，研究视图状态文字为“城市位置尚未配准”（运行实测）。旧 north13 雍门试放包 activation=false。',
    '按同家族旧档/低档记账，不另计门数；建议 LY-100 合并时把 research-north13-yong-Y 标为“已入城同家族·旧研究档”或撤出 walls.researchModelIds。')
add('被替代版本（仅旧版 v1 入口仍载）', 'F-storage', [C + 'assets/storage/storage-group-organized.glb'],
    '当前入口 storage-main=granary-city-LOD0.glb；v1 ?mode=west 太仓视图运行实测仍请求旧 storage-group-organized.glb。',
    '保留为 v1 归档原字节，不作为当前仓储输入；新生产只读 granary-city-v1。')
add('未加载的同家族中远档', 'F-storage', [C + 'progress-assets/granary-city-v1/granary-city-LOD1.glb', C + 'progress-assets/granary-city-v1/granary-city-LOD2.glb'],
    '城中只装 LOD0（完整近档），无远档切换；LOD1/2 只在 source.json 记录。', '同家族 LOD，不计家族；是否接远档由 LY-100/资源审计决定。')
add('被替代版本（仅合同/旧接口记录）', 'F-gate-guangyang', [C + 'assets/west/guangyang-C-form.glb'],
    '只出现在 data/west/guangyang-replacement-contract.json；当前城中广阳门为 city-wall/direct/gate-body-only.glb。',
    '历史替换前版本，只读归档，不作输入。')
add('被替代版本（v1/合同引用）', 'F-citywall', [C + 'assets/city-wall/A/wall-08.glb', C + 'assets/city-wall/A/wall-09.glb'],
    '当前城中 08/09 两段用 direct/wall-08、direct/wall-09（广阳 direct 转接）；A 版 08/09 只见于 city-wall-interface-original 与 guangyang-replacement-contract。',
    '只读归档。')
add('备选方案（未入城）', 'F-citywall', sorted(p for p in files if p.startswith(C + 'assets/city-wall/B/')),
    'B 组 12 段只被 city-wall-interface(-original).json 引用，当前入口不加载。', '同家族备选，不计家族；不得与 A 叠载。')
add('v1 专用环境/接入件', 'F-courtyard',
    [C + 'assets/c02v/C02-environment.glb', C + 'assets/c02/C02-environment.glb', C + 'assets/d08/D08-environment.glb',
     C + 'assets/d08/access-D08.glb', C + 'assets/c01/access-C.glb', C + 'assets/r01/district-environment.glb'],
    '只在旧版 v1 入口使用（C02 四簇视图运行实测请求 C02-environment/D08-environment/access-D08）；当前入口改由 ground-atomic 地面承担。其中 d08/D08-environment.glb 与城中按章加载的 ground-atomic/D08.glb 逐字节相同（同一文件两处路径）。',
    '只读归档，不计家族。')
add('v1 专用道路件', 'F-ground-road',
    [C + 'assets/road-junction/joined-route-terrain.glb', C + 'assets/market/corridor-6m-market-link.glb', C + 'assets/market/flowB-routes.glb',
     C + 'assets/main-roads/corridor-6m.glb', C + 'assets/main-roads/corridor-10m.glb', C + 'assets/road-junction/corridor-6m.glb',
     C + 'assets/west/route-corridor.glb'],
    '当前入口不加载；被 v1 west-layer 或 data/west 合同引用。main-roads/corridor-6m 与 road-junction/corridor-6m 同为 6832 字节但 SHA 不同，是两份文件。', '只读归档，不计家族。')
add('字节重复副本', 'C:m-luoyang-palace-admission-court',
    sorted(p for p in files if p.startswith(C + 'progress-assets/palace-admission-court/') and p.endswith('.glb')),
    '城目录 progress-assets 下 6 个 GLB 与资产卡 library/models/m-luoyang-palace-admission-court/files 下同名文件逐字节相同；任何城市入口都不加载。',
    '按 1 个家族、1 份资产计；城目录副本标为冗余（是否删除由 LY-100/协调者定，本席位不改）。')
add('非城市入口的质量参照', 'none', [C + 'assets/quality-reference-013-A.glb'], 'v1 shell.mjs 质量参照（孙吴陶院落释读，非东汉洛阳）。', '只读，不计入洛阳家族。')

# failed / flagged by the existing mq review (bound to sha; re-checked against current bytes)
mq_flags = []
for c in L['cards']:
    for i in c['mqAuditIssues']:
        cur = files.get(i['path'])
        mq_flags.append({'card': c['id'], 'path': i['path'], 'auditSha256': i['sha256'], 'currentSha256': cur and cur['sha256'],
                         'auditMatchesCurrent': bool(cur and cur['sha256'] == i['sha256']), 'issues': i['issues'],
                         'inCity': bool(cur and any(f['sameBytesAsCityLoaded'] for f in c['files'] if f['path'] == i['path']))})
over15 = [g['path'] for g in L['glbFiles'] if g['over15MB']]
dup_bytes = defaultdict(list)
for g in L['glbFiles']:
    dup_bytes[g['sha256']].append(g['path'])
dups = [{'sha256': s, 'paths': p} for s, p in dup_bytes.items() if len(p) > 1]

out = {'familyCount': len(families),
       'familyCountByState': {s: sum(1 for f in families if f['cityState'] == s) for s in RANK},
       'families': families, 'routes': routes, 'mqFlags': mq_flags, 'over15MB': over15, 'byteDuplicateGlb': dups,
       'notFound': [{'item': '被停用的 31 组重复宫殿', 'searched': ['docs/**', 'lab/data/assets.json@HEAD', 'git log 全部提交（含删除文件名）'],
                     'result': '在 bce3211 的仓库内容与历史中没有找到对应文件、资产卡或清单；不在本快照内，无法逐条落账。'}]}
json.dump(out, open(QA / 'family-ledger.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
print(json.dumps({k: out[k] for k in ('familyCount', 'familyCountByState')}, ensure_ascii=False, indent=1))
print('over15', over15); print('dups', len(dups)); print('mq', [(m['card'], m['auditMatchesCurrent'], m['inCity']) for m in mq_flags])
for f in families[:16]:
    print(f['family'], f['cityState'], f['cityNodes'], [c['id'] for c in f['cards']])
