# LY-060 prep: build inputs.json from sha-lab-inputs.txt (path, committed-blob SHA256, worktree SHA256)
# plus measure-out.json. python -I make_inputs.py
import json
LAB = 'D:/GitHub/creation-notebook-lab/'
m = json.load(open('measure-out.json', encoding='utf-8'))
meas = {v['path'].split('creation-notebook-lab/')[1]: v for v in m.values()}
NOT_LOADED = {'loadedInCity': False,
              'loaderCode': None,
              'loadEvidence': 'grep of docs/cities/luoyang/{city-data.mjs,app.mjs,city-renderer.mjs,index.html} @bce3211: 0 hits for card id or file name; renderer only loads manifest.nodes + manifest.researchModels (city-renderer.mjs:218,221; chapters via loadNodeIds :601). LY-001 family-ledger: cityNodes=0, state 仅模型（资产卡文件）.'}
role = {
 'm-luoyang-stable': ('厩棚与饲槽 A/B（互斥）', 'LY-051/052 输入；LY-060 只引用其交付后的差异件'),
 'm-luoyang-tile-kiln': ('砖瓦窑 A/B（互斥），含 presentation_ground 展示地坪', 'LY-053/054 输入；展示地坪由 LY-053 移除'),
 'm-luoyang-hand-mill': ('人力石磨 A/B（互斥），含 presentation_ground', 'LY-055 输入'),
 'm-luoyang-foot-pestle': ('足碓与踏台（独立）', 'LY-056 输入；与 workyard 内嵌足碓互斥'),
 'm-luoyang-workyard-shed': ('开敞作业棚 / 双屋足碓作业院（已发布，非原谷物加工院）', 'LY-057/058/059 对照；LY-060 候选场所之一'),
 'm-luoyang-court-layout-kit': ('普通院落两种组装（compact_work 与 workyard 同外框 18x24.15）', '仅作外框比对，不是谷物院'),
}
items = []
for line in open('sha-lab-inputs.txt', encoding='utf-8'):
    p, c, w = line.split()
    it = {'path': LAB + p, 'sha256Committed': c, 'sha256Worktree': w,
          'crlfDiffers': c != w}
    card = next((k for k in role if k in p), None)
    if card:
        it['card'] = card; it['role'], it['useBy'] = role[card]
        it.update(NOT_LOADED)
        if p in meas:
            v = meas[p]
            it['measured'] = {'bytes': v['bytes'], 'bboxMin_blenderZup': v['bboxMin'], 'bboxMax_blenderZup': v['bboxMax'],
                              'footprintXY': v['footprintXY'], 'height': v['height'], 'nodes': v['nodeCount'], 'tris': v['tris'],
                              'nodesTouchingMinZ': v['nodesTouchingMinZ']}
    elif p.endswith('city-data.mjs'):
        it.update(role='城市清单（节点/章/研究视图）', loadedInCity=True, loaderCode='app.mjs:1 import manifest from ./city-data.mjs')
    elif p.endswith('city-renderer.mjs'):
        it.update(role='渲染器装载规则', loadedInCity=True, loaderCode='app.mjs:177 dynamic import ./city-renderer.mjs')
    elif p.endswith('app.mjs'):
        it.update(role='城景入口脚本', loadedInCity=True, loaderCode='index.html <script type=module src=app.mjs>')
    elif p.endswith('index.html'):
        it.update(role='城景入口页', loadedInCity=True, loaderCode='entry')
    elif p.endswith('p-luoyang.asset.json'):
        it.update(role='项目卡：members 含五个作业家族（:542-568），只是成员登记，不是城市落位', loadedInCity=False, loaderCode=None)
    elif p.endswith('assets.json'):
        it.update(role='官方汇总（工作树有既有时间戳改动，以提交 blob 为准）', loadedInCity=False, loaderCode=None)
    items.append(it)
WP = 'D:/GitHub/creation-notebook-workpacks/'
MQ = 'C:/Users/suxin/AppData/Local/Temp/claude/bfd0867865ae17cc/14ddfcf2-ca06-49dc-95f8-4586da1502c1/scratchpad/mq/'
extra = [
 (WP + 'TASKPOOL.md', '00c2e1715e312d575faab519ff321dd32395f5bd2f2f239929199541788566c7', '任务池原文（LY-060 节 :638-645）'),
 (WP + 'taskboard.json', '1d1fcb9c6e5ea22bb64b053d0ca30e10c3c588ffffb4edcbbbf73db6d4d65ae4', '依赖图：LY-060 deps = G + LY-051..059'),
 (WP + 'LY-001/qa/family-ledger.json', '8eaa7c7a805d5cfb4fd1492a26c480ee0cad9095407e767648e0e9e71eadfe37', 'LY-001 快照家族账（五家族 cityNodes=0）'),
 (WP + 'LY-001/qa/city-nodes.csv', '8ab19b0553faf60717759d3580ac1d173d560a832f58512d83bb478a289f27c7', 'LY-001 城市节点表（无作业节点）'),
 (MQ + 'render.py', 'ff89761743a064f7d599835e3e3123f330ca152df43634717c312ece667d4dc7', '统一渲染脚本'),
 (MQ + 'cards/m-luoyang-stable/audit.json', 'e6999604d36edc8b704f97c3f17d579890c637a602f2eadfabb89926fca4126c', '体检；SHA 与现件一致，issues=[]'),
 (MQ + 'cards/m-luoyang-tile-kiln/audit.json', 'cabc9607d0a2b2992c0c58dd14e4e8a25b86ef2a6a393b6d33bf2a85de26cfc6', '体检；一致，issues=[]'),
 (MQ + 'cards/m-luoyang-hand-mill/audit.json', '8952a86cd1344f977128c75db79d735156839376a015b4029c0a765d39721f98', '体检；一致，issues=[]'),
 (MQ + 'cards/m-luoyang-foot-pestle/audit.json', 'f99eb9333cfb4acc8d5b23f8d48ebc520ef1f5f7a2339508f8e30e80842623cb', '体检；一致，issues=[]'),
 (MQ + 'cards/m-luoyang-workyard-shed/audit.json', 'dce70ed8b82e5a729f70d9447e2d9dde54ea06e3bf0b524fcf6250d63e5a3307', '体检；一致，issues=[]'),
]
for p, s, r in extra:
    items.append({'path': p, 'sha256': s, 'role': r, 'loadedInCity': False, 'loaderCode': None})
missing = [
 {'what': '原谷物加工院（含双足碓、工作棚瓦缺陷记录）的 GLB 与缺陷记录', 'neededFor': 'LY-057/058 修订后作为 LY-060 的一个可选场所', 'searched': 'docs/** 全文 grep「谷物」0 命中；git log --all --grep 0 命中；workyard-LOD0 只有 pestle_0 一具足碓；compact_work 无足碓', 'rebuildFromGlb': '否：仓库里没有它的 GLB，无从重建；需协调者提供来源或由 LY-057 判阻断'},
 {'what': '五个作业家族的原生 .blend / 源 ZIP（stable、tile-kiln、hand-mill、foot-pestle、workyard-shed）', 'neededFor': '若 LY-060 需重新导出合批或补 LOD；纯装配可不需要', 'searched': 'D:/GitHub/creation-notebook-待传/ 只有 说明.txt', 'rebuildFromGlb': '可以：装配只需 GLB 节点+矩阵；如需改几何须标「从GLB重建」'},
 {'what': 'LY-051..059 九个前置包的交付物（models/、assembly.json、qa/）', 'neededFor': 'LY-060 的全部装配输入', 'searched': 'workpacks/LY-051..059 只有 prep/（部分空）', 'rebuildFromGlb': '不适用：须等前置席位交付'},
 {'what': 'LY-005 坐标/高程契约、LY-006 端口与所有权、LY-007 材质基线、LY-008 检查器、LY-010 选定作业样板与区域准入', 'neededFor': '原点/高程基准、外接端口格式、材质合并、检查器、能否入城', 'searched': 'workpacks/LY-005 只有 qa/source 草稿；LY-006/007/008/010 目录不存在', 'rebuildFromGlb': '不适用'},
]
json.dump({'seat': 'LY-060', 'baseline': 'bce3211f818ee5a8bef1773539da70695ba37b17', 'workpacksHead': '09536a8',
           'shaRule': 'lab 文件一律以提交 blob SHA256 为准（git show HEAD:path | sha256sum）；GLB 两者一致，文本卡因 autocrlf 不一致',
           'axisNote': 'measured bbox 为 Blender 导入后 Z-up；glTF (x,y,z) = Blender (x,z,-y)',
           'inputs': items, 'missing': missing},
          open('inputs.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(items))
