# LY-060 prep (second pass, 2026-11-05 23:3x): append G-pack deliverables and the private trial chunk to inputs.json.
# Usage: python -I add_g_inputs.py <inputs.json> <trial-chunk.glb>
import hashlib, json, subprocess, sys

WP = 'D:/GitHub/creation-notebook-workpacks/'
LAB = 'D:/GitHub/creation-notebook-lab'


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def blob_sha(rel):
    b = subprocess.run(['git', '-C', LAB, 'show', 'HEAD:' + rel], capture_output=True, check=True).stdout
    return hashlib.sha256(b).hexdigest()


path, trial = sys.argv[1], sys.argv[2]
d = json.load(open(path, encoding='utf-8'))
d['inputs'] = [i for i in d['inputs'] if not i.get('pass2')]

g = [
    ('LY-001/status.json', 'LY-001 快照（交付完成）', None),
    ('LY-001/qa/family-ledger.json', 'LY-001 家族台账：五个作业家族 cityNodes=0', None),
    ('LY-002/status.json', 'LY-002 证据与禁用表（交付完成）', None),
    ('LY-005/coordinate-contract.json', 'LY-005 坐标/高程契约（交付完成）：+Y 上；新件 local-origin，本地 y=0=接地面；地块地面 0.20；E3 高程 2 mm/平面 5 mm', None),
    ('LY-005/port-schema.json', 'LY-005 端口格式（local+world 双坐标）', None),
    ('LY-006/status.json', 'LY-006 端口与所有权 registry v1（交付完成）', None),
    ('LY-006/registry/seats.json', 'LY-060：site S-WORK 的 siteOwner；writeZones=[]，ownsGroundPieces=[]，produces=[]，consumes=[work-site:service-gate:opening, stable:entrance:ground]；ownsCards=五个作业卡', None),
    ('LY-006/registry/zones.json', 'frames/local:work-site placement=null；sites/S-WORK envelope=null', None),
    ('LY-006/registry/ownership.json', 'C02-034 owner=null status=frozen（44院原矩阵与计数不变）', None),
    ('LY-006/registry/ports.json', '端口 stable:entrance:ground（LY-052）、work-site:service-gate:opening（LY-059），值待生产方交付', None),
    ('LY-006/registry/seams.json', '接缝 seams[273] LY-052->LY-060、seams[391] LY-059->LY-060', None),
    ('LY-006/schemas/interface.schema.json', '接口 JSON schema', None),
    ('LY-006/schemas/port.schema.json', '端口 schema', None),
    ('LY-006/templates/interface.template.json', '接口模板', None),
    ('LY-006/source/validate_interface.py', '接口校验器（制作期自检用）', None),
    ('LY-007/baseline/lod-rules.json', 'LY-007 LOD 规则（交付完成；生产族数字标「待复核」）', None),
    ('LY-007/baseline/texture-uv-rules.json', 'REUSED_C_* 为旧调色板现状，新模型禁用', None),
    ('LY-007/baseline/decisions.json', 'P-LEGACY 等决定', None),
    ('LY-008/source/ly_check.py', 'LY-008 检查器（席位尚无 status.json，未冻结）', None),
    ('LY-009/board/taskboard.v2.json', 'LY-009 任务板 v2：LY-060 状态「待输入」，S4 未完成依赖 LY-008/009/010/051..059（LY-009 尚无 status.json）', None),
    ('LY-009/board/pause-zone.json', 'PZ-10 advisory：根 taskboard.json 中 LY-060 的 text 串入下一节导语', None),
]
for rel, role, _ in g:
    p = WP + rel
    d['inputs'].append({'pass2': True, 'path': p, 'sha256': sha(p), 'role': role,
                        'loadedInCity': False, 'loaderCode': None})

rel = 'modeling-lab/review-batches/2026-11-04-city-visible/adapter/adapter.json'
d['inputs'].append({'pass2': True, 'path': LAB + '/' + rel, 'sha256Committed': blob_sha(rel),
                    'role': '私有母版可见交接 adapter：res_workyard_034 节点（单位矩阵、city-absolute，bounds x 592.89..610.89 / y 0.20..5.128 / z -1092.20..-1068.05），sourceNodeIds C02-034__workyard_trial__*；deploymentStatus「not published」',
                    'loadedInCity': False,
                    'loaderCode': None,
                    'loadEvidence': 'adapter.deploymentStatus = "not published; no public prefix selected; JSON does not run renderer"；docs/cities/luoyang 不读取 modeling-lab/'})
d['inputs'].append({'pass2': True, 'path': LAB + '/modeling-lab/review-batches/2026-11-04-city-visible/city-visible-web-handoff-v1-public.zip.part01..05 :: chunks/res_workyard_034.glb',
                    'sha256': sha(trial), 'bytes': 1849736,
                    'role': '作业院入城试放块（只解出这一个成员到 scratchpad 比对，不入 workpacks）。compare_trial_chunk.py：5/5 网格与 workyard-LOD0 顶点数、三角数、本地包围盒逐值相同（Δ=0.0），只多了节点平移 (601.8912, 0, -1080.2) = city-data.mjs:2742 C02-034「住宅院落 34」的矩阵；材质名带 .027/.030 后缀',
                    'loadedInCity': False, 'loaderCode': None,
                    'compareResult': 'trial-chunk-compare.json'})

d['missing'] = [m for m in d['missing'] if not m.get('pass2')]
d['missing'].append({'pass2': True, 'what': 'LY-008 冻结检查器（status.json）、LY-009 status.json、LY-010 决策表（目录为空）',
                     'neededFor': '作业样板选择、区域准入、官方检查入口；LY-010 未出则 local:work-site 无原点',
                     'rebuildFromGlb': '不适用'})
d['missing'].append({'pass2': True, 'what': 'LY-060 自身的写入区 / 演示域承托地坪归属',
                     'neededFor': 'registry v1 给 LY-060 writeZones=[]、ownsGroundPieces=[]、produces=[]，S-WORK envelope=null；若演示域需要一块承托地坪或外接端口，须协调者/LY-006 补登，否则只能用前置包的地坪件',
                     'rebuildFromGlb': '不适用'})
d['missing'].append({'pass2': True, 'what': 'city-C032-entry-LOD0.blend（私有母版）中 C02-034__workyard_trial__* 的原生对象',
                     'neededFor': '只用于说明试放来源；LY-060 不使用它落城（C02-034 冻结）',
                     'rebuildFromGlb': '可以：试放块与 workyard-LOD0 网格逐值相同，只是平移'})
d['pass2'] = {'at': '2026-11-05T23:3x', 'note': 'G 部分交付后的增补；pass1 条目未改'}
json.dump(d, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(d['inputs']), len(d['missing']))
