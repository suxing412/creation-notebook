# -*- coding: utf-8 -*-
# LY-010 决策数据（唯一手写源）。build_decision.py 读它，解析引用的 SHA、做一致性检查，生成 decision/ 下的表。
# 引用写法：
#   "file:<lab 路径>"   = 资产卡登记的文件，SHA 取 qa/candidate-inventory.json（cad338b 提交字节）
#   "asset:<城景资产id>" = city-data.mjs 资产，SHA 取 qa/city-data.cad338b.dump.json
#   "node:<城景节点id>"  = city-data.mjs 节点（只校验存在）
#   "ws:<workpacks 相对路径>" = 工作包内文件，构建时现算 SHA
BASELINE = {
    "commit": "cad338ba683f7277aea098f45c8feb6c915a847c",
    "tag": "r2026.11.05-8",
    "previous": "bce3211f818ee5a8bef1773539da70695ba37b17",
    "frozenBy": "协调者（任务补充说明：G 基线冻结为 cad338b）",
    "byteRule": "一律按提交字节（git -c core.autocrlf=false show / archive）计 SHA；Windows 检出字节不作准（LY-001 C8、LY-008）",
}

# 决定词汇
GO, COND, REUSE, CONTRACT, WAIT, BLOCK, SERVICE = (
    "放行", "有条件放行", "放行·预判复用", "放行·契约", "待前件", "阻断·缺输入", "持续服务（按批）")
CITY_PROPOSAL, LOCAL_ONLY, NO_GEOM, FORBIDDEN = (
    "可提城市装配提案（须过区域验收与LY-100）", "仅局部包（不得带城市矩阵）", "不产生城市几何", "禁建")

# ------------------------------------------------------------------ 本批统一判据（C 工程判据，不是历史或规范结论）
CRITERIA = {
    "baseline": BASELINE,
    "coordinates": "沿用 LY-005 冻结契约（米制，+X东 +Y上 -Z北，无地理原点；只许绕Y旋转、缩放=1）。cad338b 全部 77 个节点复核通过，旧 66 节点矩阵零漂移（qa/contract-recheck-cad338b.json）。",
    "bodyEnvelope": {
        "id": "LY010-BODY-C1",
        "pedestrian": "竖直圆柱 r=0.30 m、h=1.80 m；转身圆直径 1.20 m；头顶净空 ≥1.85 m",
        "footSupport": "脚带半宽 0.30 m，采样步长 ≤0.10 m；支承判定竖向间隙 ≤0.005 m",
        "step": "单处高差 ≤0.05 m 视为平接；0.05–0.20 m 只能作为有踏面(≥0.25 m)的台阶级；>0.20 m 必须分级或做坡；坡段 ≤1:8",
        "carry": "搬运包络 LY010-CARRY-C1：宽 0.90 m、高 1.80 m、长 1.20 m（人+货），只用于仓储/市肆卸货/作业院路线",
        "vehicle": "本批不定义车辆包络；任何包不得写车辆可通行",
        "basis": "C 工程判据。与 LY-016、LY-044、LY-076、LY-095 prep 采用的 r0.30/h1.80 一致；不是汉代尺度或现代规范",
    },
    "tolerances": {"portPlanar_m": 0.005, "portVertical_m": 0.002, "contactGap_m": 0.005,
                   "basis": "LY-006 端口容差 0.005/0.002 m"},
    "loading": "本批新增节点一律 initial=false、按章加载；冷开集合保持 cad338b 的 65 个初始节点 / 27 份 GLB（原始 2,948,644 B）。改冷开集合须先由 LY-096 按 C15（全部默认 GLB 传输响应体 ≤1,900,000 B）重测。",
    "fileLimits": "单 GLB ≤15,000,000 B；近景原件超限的保留在源工程，公开档如实标注最高档；不得把 LOD0 复制改名充三档",
    "checks": "交付前在导出副本里依次跑 LY-008 ly_check（package → glb/lodset → privacy → official），官方 build_assets.py --check 只在副本跑，绝不在 D:/GitHub/creation-notebook-lab 里跑",
    "positionUncertainty": "可接城坐标须有有限的历史位置不确定度且来源为考古控制点配准（LY-003/004）；上限冻结为 75 m（沿用 LY-003 presentation_m）。示意点重描残差（3–29 m）不是历史误差。本批宫区、礼制、南北郊候选全部为 null，故全部不可接城。",
    "holdZoneRule": "落位不得进入 LY-003 悬置区（buffer_m：宫区200、复道/示意路80、标签400 m）；buffer_covers_e1_e2=false 的区按 buffer+e1_e2_max_shift 判。悬置区外 ≠ 证明在宫外。",
    "fiveThings": "模型能读取、局部通行通过、已入城、真实结构安全、历史复原成立是五件事；本表放行只涉及「能否开工」与「能否提城市装配提案」，不替代其余四件。",
    "styleBaseline": "LY-007 冻结基线（五种 LY_P01 材料、三档规则、D-LOD-BBOX）；P-GENERATOR/P-NEWMAT/P-LEGACY/P-DOUGONG/P-TYPEGATE/P-STONE-COLOR 未拍板前按 LY-007 暂行做法；新件只用五种材料，继承件原样保留其已有材料",
}

# ------------------------------------------------------------------ 需要伊苏里亚 / 协调者补的输入
INPUTS_NEEDED = [
    {"id": "I1", "who": "伊苏里亚", "what": "开阳 bearing-section-v1 失败承托样例本体，及开阳适配失败/实际剖面记录（0.0936 m³ 门楣/梁交体、约 21.76 m³ 重复 deck 的出处）",
     "seats": ["LY-011", "LY-012", "LY-013", "LY-014", "LY-015"], "blocking": True,
     "effect": "LY-011 验收条「旧0.0936m³问题有可定位的前后证据」与 LY-013「旧件替换可重放」无法满足；几何可按 K-v1 实测开工，但这两条保持阻断。若该样例已不存在，须由协调者书面修订验收条（LY-010 无权豁免）。不能从 GLB 重建（K-v1 本体无落在 0.0936±0.003 m³ 的交体对，LY-011 prep 实测）。"},
    {"id": "I2", "who": "伊苏里亚", "what": "「原谷物加工院」三档 GLB、源包（.blend/源ZIP）与工作棚瓦落座/行缝/承件缺陷记录",
     "seats": ["LY-057", "LY-058", "LY-059", "LY-060"], "blocking": True,
     "effect": "LY-057、LY-058 阻断；LY-059、LY-060 因依赖 058 连带等待。任务池明写已发布双屋作业院（workyard 7eb9739e）是不同产物，LY-010 不得改判以它代替；cad338b 起 workyard 已作为北缘第三院入城，更不能拿来改。"},
    {"id": "I3", "who": "伊苏里亚", "what": "灵台五处踏步修订的近景 LOD0（卡片记 26,176,944 B）及其 .blend/生成器/路线 QA",
     "seats": ["LY-076", "LY-094"], "blocking": False,
     "effect": "缺时 LY-076 只在 LOD1/LOD2 上做叠加件，近景档标「近景未验」；从 GLB 重建的近景不得称原件。"},
    {"id": "I4", "who": "伊苏里亚", "what": "夏门 B-library-v1 LOD0（16,054,944 B，私密）与源 .blend/生成器",
     "seats": ["LY-019"], "blocking": False, "effect": "缺时近景档接缝检查标待验；LOD1/LOD2 接缝件可从 GLB 重建并标注。原件超 15,000,000 B，本就不能作公开档。"},
    {"id": "I5", "who": "伊苏里亚", "what": "谷门 G-v1 源包（LOD0 13,213,712 B、隐藏试放 delta、remove_on_rollback 清单）",
     "seats": ["LY-018"], "blocking": False, "effect": "缺时墙帽/底板从公开 chunk 72 顶点重建并标「从GLB重建」，原生撤回未做。"},
    {"id": "I6", "who": "伊苏里亚", "what": "平城地面附件源包（生成器 + 原 3114 样点检查器与报告）",
     "seats": ["LY-016", "LY-017"], "blocking": False,
     "effect": "缺时按 LY-016 route_check 新定义重现旧斜路依赖（西 447/1236、东 423/1236），并写明「原 565/3114 不能逐字重现」，该项记待验，不判阻断。"},
    {"id": "I7", "who": "伊苏里亚", "what": "城市母版 city-C032-entry-LOD0.blend（1e8c4d2c…）与门位底座 eabb2a90、覆盖层 660cdf37",
     "seats": ["LY-015", "LY-016", "LY-017", "LY-018", "LY-019", "LY-021", "LY-022", "LY-025", "LY-026", "LY-028", "LY-029", "LY-030", "LY-036", "LY-038", "LY-039", "LY-040", "LY-059", "LY-060", "LY-071", "LY-072", "LY-073", "LY-085"],
     "blocking": False, "effect": "只影响「在原生母版里安装/撤回」这一项：一律记「未做」。网页侧安装/撤回按 cad338b 城景+GLB 做，可见集分块只作测量参照。"},
    {"id": "I8", "who": "伊苏里亚", "what": "太仓 operations/入口体积诊断（卡片 A 51 / B 77 处 1.8 m 失败的探针定义与原结果）",
     "seats": ["LY-031", "LY-032", "LY-033", "LY-034", "LY-035"], "blocking": False,
     "effect": "缺时各席位用自建探针，数字口径不同，不得称复现 51/77。"},
    {"id": "I9", "who": "伊苏里亚", "what": "武库 B v2.2 原生 .blend + 枢轴生成器 + 私有路线 QA",
     "seats": ["LY-036", "LY-037", "LY-093"], "blocking": False, "effect": "缺时门叶真轴与角度范围按 GLB 估算轴并写明，最终门态检验记待验。"},
    {"id": "I10", "who": "伊苏里亚", "what": "W2 备食放置 QA 包（14 路线、2 作业位、2 回转、65 受保护路线、错位负例）",
     "seats": ["LY-044"], "blocking": False, "effect": "缺时按 LY010-BODY-C1 重建测试，不继承原 W2 通过结论。"},
    {"id": "I11", "who": "伊苏里亚", "what": "复道 A 旧柱脚未支持记录（16 点、旧城市变换、地形版本）与复道/登临源包、A↔access-A 原装配变换",
     "seats": ["LY-067", "LY-068", "LY-069", "LY-070"], "blocking": False,
     "effect": "缺时逐脚对账只有「新」一侧；A↔access-A 变换作为 C 装配参数重新给出并标注。"},
    {"id": "I12", "who": "伊苏里亚", "what": "luoyang-palace-admission-court-v1.zip（3 个 .blend、builder、finite-routes/route-interfaces 原检查器）",
     "seats": ["LY-061", "LY-062", "LY-063", "LY-069", "LY-070"], "blocking": False,
     "effect": "缺时用从 GLB 重写的等价检查器，报告写「重写版」，不称原检查器重跑。"},
    {"id": "I13", "who": "伊苏里亚", "what": "玉堂 v2.0.0 原生源与「屋顶端部旧修订」前后 SHA/说明", "seats": ["LY-066"], "blocking": False,
     "effect": "缺时 T4「不回退」以 cad338b 现状指纹为基准。"},
    {"id": "I14", "who": "伊苏里亚", "what": "店前线 v2.1 私密源包/生成器与原「72段入口包络」QA 定义", "seats": ["LY-021", "LY-024", "LY-027", "LY-029"], "blocking": False,
     "effect": "缺时单铺身份只能从合批网格派生，柜后不回退用 GLB 指纹+自建路线判，不称原 QA 复现。"},
    {"id": "I15", "who": "伊苏里亚", "what": "井族 original-source.zip（b8946793…，含 build.py、check*.py）", "seats": ["LY-025", "LY-026"], "blocking": False,
     "effect": "缺时小件从 GLB 重建并标注；源 QA 不能重跑。"},
    {"id": "I16", "who": "协调者", "what": "「被停用的31组重复宫殿」清单（路径或 SHA）", "seats": ["LY-061", "LY-066", "LY-070", "LY-094"], "blocking": False,
     "effect": "缺时 LOCK-31PALACES 只能按名称禁用；宫院席位不得引用任何未登记宫殿件。"},
    {"id": "I17", "who": "协调者/伊苏里亚", "what": "「东北长路预检」与「既有三条长接路规划」原件", "seats": ["LY-039", "LY-040", "LY-084", "LY-093"], "blocking": False,
     "effect": "本批按「不存在」处理：LY-084 只审重建的 R1–R3 并交禁建结论，不造路；如原件出现，084 重跑。"},
]

# ------------------------------------------------------------------ bce3211 → cad338b 对各区的影响（由 qa/ 实测文件支撑）
BASELINE_IMPACT = {
    "summary": "3 个提交（f28d650、b70c495、cad338b），32 个文件、+1880/−206 行；没有修改或删除任何既有 GLB，只新增 4 个雍门接街 GLB；城景资产 42→53、节点 66→77（+11，改 4：ground-network-ground-stitched.replaces、ground-retained.initial、yong-gate-body/interface 的 initial/replaces）、章节 7→8（+north-three）、院数 44→47；原 44 院矩阵与资产全部不变；evidence-geometry.json 不变（fa8b7002…）；研究视图 14 个不变；冷开 21→27 份 GLB、原始字节 3,872,084→2,948,644 B。",
    "evidence": ["ws:LY-010/qa/baseline-diff.json", "ws:LY-010/qa/contract-recheck-cad338b.json", "ws:LY-010/qa/zone-overlap-cad338b.json",
                 "ws:LY-010/qa/plan-zone-overlap.yong-road-receiver.json", "ws:LY-010/qa/plan-zone-overlap.ground-retained.json",
                 "ws:LY-010/qa/court-ground-probe.json", "ws:LY-010/qa/candidate-inventory.json"],
}

# ------------------------------------------------------------------ 前置席位未解决条件（来自各 status.json openItems），按影响面归类
INHERITED_GLOBAL = [
    {"from": "LY-001/005/007/008", "kind": "待验", "item": "没有浏览器/GPU/手机实测；所有预览是 CPU 图。全部区域允许此项待验，交 LY-097，不得写成通过。"},
    {"from": "LY-001", "kind": "阻断合并", "item": "C8：city-data.mjs 13 条 sourceContracts 中 12 条 SHA 只匹配 CRLF 检出字节（PZ-09）。任一批改 city-data.mjs 前须由 LY-100 统一按提交字节重算。"},
    {"from": "LY-005", "kind": "待验", "item": "渲染器 transformFor() 不拒收非1缩放/非Y轴旋转；R1/R2 只是契约。各包自检 + LY-096 复核，建议 LY-100 加硬校验。"},
    {"from": "LY-007", "kind": "待拍板", "item": "P-GENERATOR/P-NEWMAT/P-LEGACY/P-DOUGONG/P-TYPEGATE/P-STONE-COLOR 未拍板，按暂行做法；N1-MATORDER 库排序缺陷只影响 JSON 排列。"},
    {"from": "LY-007", "kind": "条件", "item": "D-LEAF-UV：第一个开合动件交付前必须量门扇 UV 坐标系（影响 LY-012、LY-031、LY-032、LY-042、LY-062）。"},
    {"from": "LY-008", "kind": "条件", "item": "官方 --check 漏查截断、NaN、缺纹理、私密路径；合并队列须同时跑 ly_check。docs/asset-spec/README.md 两处 D:/ 路径交 LY-100。三角上限按 mesh 定义口径判错、实例口径只报警。"},
    {"from": "LY-009", "kind": "条件", "item": "PZ-14：工作包不得混入 .blend/.zip/tmp/超限 GLB（native/ 与 tmp/ 不进 git）；分支名用 wp/LY-###。PZ-10：根 taskboard.json 每节末席 text 串了下一节导语，以 LY-009 v2 为准。"},
    {"from": "LY-002", "kind": "条件", "item": "禁用表 X01–X24 对所有卡片/说明有效；汉尺/里换算是 C（X22）。"},
]

# ------------------------------------------------------------------ 区域决策
REGIONS = [
 {
  "id": "R01", "name": "开阳门局部", "site": "S-KAIYANG", "batch": "开阳局部",
  "seats": ["LY-011", "LY-012", "LY-013", "LY-014", "LY-015"], "sharedSeats": ["LY-085"],
  "selected": {"scheme": "K-v1 门体三档 + 三条门下测试带，按源包 city/placement.json 的隐藏试放帧 local:kaiyang-K-v1（activation=false）装配",
               "refs": ["file:docs/library/models/m-luoyang-kaiyang-gate/files/kaiyang-K-LOD0.glb",
                        "file:docs/cities/luoyang/progress-assets/north13-gates/luoyang-kaiyang-gate-study-v1/models/kaiyang-K-LOD1.glb",
                        "file:docs/cities/luoyang/progress-assets/north13-gates/luoyang-kaiyang-gate-study-v1/models/kaiyang-K-LOD2.glb",
                        "file:docs/library/models/m-luoyang-kaiyang-gate/files/kaiyang-ground-LOD0.glb",
                        "file:docs/library/models/m-luoyang-kaiyang-gate/files/kaiyang-ground-LOD1.glb",
                        "file:docs/library/models/m-luoyang-kaiyang-gate/files/kaiyang-ground-LOD2.glb",
                        "asset:wall-A-wall-04", "asset:wall-A-wall-05"]},
  "retainedUnselected": [{"scheme": "城景研究视图 research-north13-kaiyang-K（study-north13-kaiyang-K-94693c58…）", "rule": "保留不动，与门组局部包互斥，不叠载"}],
  "allowedChanges": ["中门道柱列/地栿/横梁新子件（LY-011）", "门框/枢接或明确固定开门件（LY-012）", "保留 K-v1 C_upper_deck 作唯一楼板及其面层/接口件（LY-013）", "登临侧口、台阶/坡段、平台与墙顶端口件（LY-014）",
                     "按 source-object-ranges 截三角的派生门体档或隐藏清单（只经 LY-015 装配，原 GLB 字节不改）", "门下测试带外的独立地面片（从 GLB 重建，标注）"],
  "forbidden": ["改左右门道、屋盖、wall-A-wall-04/05 墙身", "以隐藏门叶换取通行通过", "补开中门道以外的新门道", "写荷载安全", "用北魏门楼/一门三道（X01/X03）定形制"],
  "localAdmission": "放行", "cityAdmission": "条件放行",
  "cityAdmissionMeaning": "可在既有 C 城垣 wall-A-wall-04/05 缺口按隐藏试放帧作 C 设计落位提案（与雍门同级），须 LY-091 区域验收、本批 LY-095–097、LY-100 合并；不是门址测绘复原。",
  "evidence": ["LY-002 E-G05（开阳门名与位置）", "LY-002 E-G08 / X01 / X03（门楼、门道数为北魏实证，禁作东汉事实）", "LY-005 端口与高程（城垣基底 0.17）", "LY-006 S-KAIYANG 帧与写入区"],
  "allowedUnverified": ["原生母版内安装/撤回（I7）", "原始未净化 .blend 的 SHA 映射：以净化等价件 + NATIVE-EQUIVALENCE 代用并写明", "浏览器/GPU"],
  "blockers": ["I1 缺 bearing-section-v1 与适配失败记录：LY-011「前后证据」、LY-013「旧件替换可重放」两条保持阻断；未解除前本区不得进入合并批"],
  "inherited": [{"from": "LY-005", "item": "城垣/城门基底 0.17 与地面 0.20/0.21 有 3–4 cm 系统差，门下接缝高差由端口写明，不抹平"},
                {"from": "LY-006", "item": "开阳端间落在实测墙端帽上（≤0.15 mm）；端口 world 值来自 activation=false 的隐藏试放，不代表已入城"}],
  "cad338bImpact": ["无直接改动（开阳文件与 wall-A-wall-04/05 节点不变）"],
 },
 {
  "id": "R02", "name": "平城门局部", "site": "S-PINGCHENG", "batch": "平城局部",
  "seats": ["LY-016", "LY-017"], "sharedSeats": ["LY-085"],
  "selected": {"scheme": "P-v1 门体三档 + 两带四片侧门地面 + 旧斜路（网络地面 C_stitch_primary 中门前段），中门关闭；帧 local:pingcheng-P-v1（隐藏试放）",
               "refs": ["file:docs/library/models/m-luoyang-pingcheng-gate/files/pingcheng-P-LOD0.glb",
                        "file:docs/cities/luoyang/progress-assets/north13-gates/luoyang-pingcheng-gate-study-v1/models/pingcheng-P-LOD1.glb",
                        "file:docs/cities/luoyang/progress-assets/north13-gates/luoyang-pingcheng-gate-study-v1/models/pingcheng-P-LOD2.glb",
                        "file:docs/library/models/m-luoyang-pingcheng-gate/files/pingcheng-ground-LOD0.glb",
                        "file:docs/library/models/m-luoyang-pingcheng-gate/files/pingcheng-ground-LOD1.glb",
                        "file:docs/library/models/m-luoyang-pingcheng-gate/files/pingcheng-ground-LOD2.glb",
                        "asset:ground-network-ground-stitched", "asset:wall-A-wall-05", "asset:wall-A-wall-06"]},
  "retainedUnselected": [{"scheme": "研究视图 research-north13-pingcheng-P", "rule": "保留，互斥"}, {"scheme": "条件路 A（conditional_link_A，y≥+21.2）", "rule": "本批不启用"}],
  "allowedChanges": ["侧门道补支承/边缘地面差异件（LY-016，独立节点，不重导三门共用块）", "门墙旧路联合装配清单（LY-017）"],
  "forbidden": ["开中门", "把旧斜路复制进第二层地面", "改旧路或门墩去消除继承侵入（旧路顶侵入西中门墩/关闭中门叶 0.04 m 须单列为继承）", "写约180年平城门已修复（177/178 损坏记载）"],
  "localAdmission": "放行", "cityAdmission": "条件放行",
  "cityAdmissionMeaning": "可在 wall-A-wall-05/06 缺口作 C 设计落位提案；卡片须写「完整门形是假说，177/178 损坏后状态未知」；须 LY-091 验收。",
  "evidence": ["LY-002 E-G04（平城门：正南、属卫尉、开设年两说、177/178 损坏）", "LY-006 S-PINGCHENG"],
  "allowedUnverified": ["原 565/3114 样点不能逐字重现（I6）：用 LY-016 route_check 定义重现并写明", "原生母版安装/撤回（I7）", "浏览器/GPU"],
  "blockers": [],
  "inherited": [{"from": "LY-006 / PZ-04", "item": "pingcheng-P-v1:old-ramp:ground 只有 ID：由 LY-016 从公开交接分块 2b89e858 实测交值+SHA，LY-006 v2 回填后 LY-017 才能交付"},
                {"from": "LY-005", "item": "地面底 world 0.01、门墩底 0.17、旧路底 0.16 下方无支承面（整体悬空），属地形契约，不由本区补"}],
  "cad338bImpact": ["平城一带无改动。ground-network-ground-stitched 新增 replaces:[yong-road-receiver]：完整道路章加载时替换雍门接收片；平城门在接收片包围盒（x 43–1445）之外，默认视图下平城门前没有已加载路面，只在 terrain 章有。"],
 },
 {
  "id": "R03", "name": "谷门·夏门·城垣接口", "site": "S-GU / S-XIA / S-WALLS", "batch": "谷门夏门城垣",
  "seats": ["LY-018", "LY-019", "LY-020"], "sharedSeats": [],
  "selected": {"scheme": "谷门 G-v1（公开 LOD1/LOD2）配当前 A 墙 wall-A-wall-00/01 缝；夏门 B 型（公开 LOD1/LOD2）配 wall-A-wall-00/11 缝；城垣以现城 A 族 12 段 + direct 08/09 为准",
               "refs": ["file:docs/library/models/m-luoyang-gu-gate/files/gu-G-LOD1.glb", "file:docs/library/models/m-luoyang-gu-gate/files/gu-G-LOD2.glb",
                        "file:docs/library/models/m-luoyang-xia-gate/files/gate-B-LOD1.glb", "file:docs/library/models/m-luoyang-xia-gate/files/gate-B-LOD2.glb",
                        "asset:wall-A-wall-00", "asset:wall-A-wall-01", "asset:wall-A-wall-02", "asset:wall-A-wall-11"]},
  "retainedUnselected": [{"scheme": "城垣 B 变体（city-wall/B/*）", "rule": "未选，只作比对；不入城"}, {"scheme": "谷门 B 样本墙帽", "rule": "实测不合，未选"}],
  "allowedChanges": ["谷门底部支承、阈值地片、可拆墙帽独立节点（从 chunk 97c48379 拆出，标从GLB重建）", "夏门实测未闭合接缝件与底部支承", "城垣真实缺口处的短转角/坡脚有限件；无缺口则只交诊断（LY-020：11 处斜接角、12 段闭合墙身已合格，不造）"],
  "forbidden": ["移动 B 示意点去迎合墙端", "复制夏门当谷门", "改相邻城墙墙身", "全城重造墙或加防御设施"],
  "localAdmission": "放行", "cityAdmission": "条件放行",
  "cityAdmissionMeaning": "谷门/夏门可在既有 C 墙缝作 C 设计落位提案；公开最高档是 LOD1，卡片与 manifest 必须写明「近景档未交付/未验」；须 LY-091 验收。",
  "evidence": ["LY-002 E-G01/E-G02（门数、门名方位）", "LY-006 S-GU/S-XIA 墙缝包络", "LY-020 prep measure-walls 99ada63e"],
  "allowedUnverified": ["夏门近景 LOD0（I4，原件 16,054,944 B 超限）", "谷门 LOD0（I5，从 GLB 重建）", "原生撤回清单", "浏览器/GPU"],
  "blockers": [],
  "inherited": [{"from": "LY-005", "item": "广阳门侧 direct 墙 08/09 墙脚比地面低 1.33 cm；多数墙脚下没有已交付地面——只记录，不由本区抹平"},
                {"from": "LY-002 D-01", "item": "证据层 gate_xuan_B「旋门」应作「秏门（旄、耗异写）」；本区卡片措辞照此，证据层改名归 LY-100"}],
  "cad338bImpact": ["无直接改动。雍门（同为城垣章）改为默认远档、近档按章；LY-091 的保护指纹集要把 yong-gate-body-far、yong-gate-interface-far、yong-road-link(-near)、yong-road-receiver 加进去"],
 },
 {
  "id": "R04", "name": "市肆（金市候选附近·C 样板）", "site": "S-MARKET / S-MARKET-STREET", "batch": "市肆",
  "seats": ["LY-021", "LY-022", "LY-023", "LY-024", "LY-025", "LY-026", "LY-027", "LY-028", "LY-029", "LY-030"], "sharedSeats": ["LY-083", "LY-090"],
  "selected": {"scheme": "生产候选 F = 店前线 v2.1 八铺四棚（已修 S84/S86）+ 井 A（well-A-LOD0 去展示坪）+ 开孔地面 C_market_ground_well_A；帧 local:market-site（214.286, 0, −1959.184）。城中默认仍是五店三摊 V1（market-cluster + N2），F 只以互斥替换包存在，不自动替换",
               "refs": ["file:docs/library/models/m-luoyang-market-frontage/files/street_frontage-LOD0.glb",
                        "file:docs/library/models/m-luoyang-market-frontage/files/street_frontage-LOD1.glb",
                        "file:docs/library/models/m-luoyang-market-frontage/files/street_frontage-LOD2.glb",
                        "file:docs/library/models/m-luoyang-market-modular-assembly/files/S84-LOD0.glb",
                        "file:docs/library/models/m-luoyang-market-modular-assembly/files/S86-LOD0.glb",
                        "file:docs/model-library/well-study/files/well-A-LOD0.glb",
                        "asset:market-main", "asset:market-N2"]},
  "retainedUnselected": [{"scheme": "V1 五店三摊 + N2（城中默认，回退态）", "rule": "LY-029 的回退目标；F 启用时整体卸下 V1 结构节点，保留共享层"},
                         {"scheme": "V2 m-market-functional（market-LOD0/1/2）", "rule": "未选，保留；三套任何时候只许一套出现"}],
  "allowedChanges": ["八铺门口 0.22 m 起步件（LY-021，叠加件）", "前街地坪接口与端口（LY-022，优先判复用）", "棚摊脚端适配（LY-023，T1–T3 判复用）", "一类铺型闭铺静态互斥态（LY-024，证据未知，标 C）",
                     "井+开孔地面原子包（LY-025 复用）与井架兼容检查（LY-026）", "F 组货架支承与可删占位（LY-027）", "C02 东边卸货/暂存地面（LY-028）", "V1/V2/F 互斥与回退包（LY-029）", "区域局部交付（LY-030）"],
  "forbidden": ["再动 S84/S86 柜台与柱网（LOCK-MARKET-V21）", "三套布局叠载", "以「市井」之名论证设井（市肆先例回避表）；井只作 C 取水功能件", "把四川画像砖十字街布局定为金市平面（X13）", "称「西市」或增加历史铺数"],
  "localAdmission": "放行", "cityAdmission": "条件放行",
  "cityAdmissionMeaning": "F 可作为与 V1 互斥的城市装配提案（同一 market-site 帧，按章加载）；默认显示哪一套由 LY-100/协调者在 LY-092 验收后另定，LY-010 不授权自动替换。",
  "evidence": ["LY-002 E-M01（三市只有二手综述；可用措辞「金市候选附近·市肆C样板」）", "LY-002 X13", "LY-006 S-MARKET 帧（C 假设，LY-029 确认）"],
  "allowedUnverified": ["v2.1 单铺节点身份与原 72 段 QA（I14）", "井族源 QA（I15）", "原生母版安装/撤回（I7）", "market-cluster HIGH_DRAWCALLS 500（LY-001 继承，交 LY-096）", "浏览器/GPU"],
  "blockers": [],
  "inherited": [{"from": "LY-006", "item": "八铺 12 个门口 x 范围取自 LY-021 prep，LY-006 只复测了台面高度（0.22/0.42）——LY-021 交付时须独立实测"},
                {"from": "LY-006", "item": "市肆西端卸货边是保守划分；LY-028 只用 C02 东边，越区须申请 v2"}],
  "cad338bImpact": ["新的默认可见雍门接收片 yong-road-receiver（e5baa0df…，209 三角，顶 0.21）在平面上压到 LY-025:write:002（整板开孔地面区）12 个三角、LY-083:write:001 18 个三角（qa/plan-zone-overlap.yong-road-receiver.json）。bce3211 时这些三角只在 terrain 章出现；现在「默认 + 市肆章」状态就会与 sample_ground(0.20)/路带(0.21) 同处。LY-022/025/028/083/090 必须分别测「默认+市肆章」与「terrain 章（network 替换接收片）」两种状态的双层/共面。"],
 },
 {
  "id": "R05", "name": "示范住宅 C02-010", "site": "S-COURT / S-COURT-LANE", "batch": "示范住宅",
  "seats": ["LY-041", "LY-042", "LY-043", "LY-044", "LY-045", "LY-046", "LY-047", "LY-048", "LY-049", "LY-050"], "sharedSeats": ["LY-082"],
  "selected": {"scheme": "示范院 = 原44院中的 C02-010（courtyard-A2，calt 矩阵平移 531,0,−818.45，承托 ground-south）。用途组合 U1：灶 A 一处 + 圈厕 service-A 一组（东院、现朝向、无孔版为默认态）+ 门前/檐下排水试片 + 房门 paired-door 两处接回；储藏/棚下不进本院；不设侧口，主院门只声明开启态（原型无院门门叶）",
               "refs": ["node:C02-010", "asset:ground-south",
                        "file:docs/library/models/m-luoyang-cooking-stove/files/stove-A-LOD0.glb",
                        "file:docs/library/models/m-luoyang-service-court/files/service-A-LOD0.glb",
                        "file:docs/library/models/m-luoyang-inner-door-components/files/paired-door-LOD0.glb"]},
  "retainedUnselected": [{"scheme": "灶 B（stove-B 三档）", "rule": "未选，保留候选，不加载"},
                         {"scheme": "圈厕有孔版", "rule": "与无孔版互斥；只有 LY-090 交出局部地面替换件且坑深标「未定」时才可启用"},
                         {"scheme": "储藏/棚下路线 R（17 个 B/B2 院原位作业棚与储藏屋）", "rule": "LY-047 只交复用说明，不装进 C02-010，不加载"},
                         {"scheme": "路线 W（A2 装 workshed）", "rule": "LY-006 v1 的 LY-047 区放不下，不选"},
                         {"scheme": "备选院 C02-021", "rule": "不选；LY-006 registry v1 帧维持 C02-010，不必发 v2"},
                         {"scheme": "北缘三院 C_NORTH_INFILL_01–03", "rule": "伊苏里亚 r2026.11.05-8 新落位，不在「原44院」内，不得选作示范院、不得改"}],
  "allowedChanges": ["C02-010 院内叠加件（可撤回节点），不动院矩阵与 courtyard-A2 共享资产", "派生宿主（只为隐藏旧门叶 timber#5/#13，按岛拆分，原资产不改）", "排水试片与出口端口（无准入去向时停在试片）", "门道至院界端口值（LY-049，现地面已支承，判复用）"],
  "forbidden": ["移动或增删院（计数维持原44 + 北缘3 = 47）", "把修订批量套到其余 8 个 A2 院", "碰 13 院片区（LOCK-13COURT）与北缘三院", "大底板覆盖孔洞或道路", "写燃烧/排烟/防火/卫生/水密结论", "给每院复制厨灶组合"],
  "localAdmission": "放行", "cityAdmission": "条件放行",
  "cityAdmissionMeaning": "C02-010 已在城中（C 设计落位）；本区新增件可作该院按章加载的装配提案，须 LY-092 验收。不代表古宅址或住宅范式。",
  "evidence": ["LY-002 E-H01（约180年洛阳城内无发掘住宅资料）", "LY-002 X12/X24（明器放大、三杨庄院落禁作模板）", "LY-006 court:C02-010 帧与 court-A2-free-space（圈厕组 6.75×7.56 m 只在东院现朝向放得下）"],
  "allowedUnverified": ["W2 原 QA 不继承（I10）", "院坪 0.200 与原型 0.215 的 15 mm 差按 LY-005 端口写明", "lane 浅槽（z≈−803.7，低 25 mm）设计意图未知", "浏览器/GPU"],
  "blockers": [],
  "inherited": [{"from": "LY-006", "item": "示范院帧 C02-010 由本表冻结（PZ-05 解除）；主屋前门带假定 x<1.1"},
                {"from": "LY-001", "item": "其余 5 种院落近景 LOD0 换档只做了静态 SHA 核对"}],
  "cad338bImpact": ["院数 44→47：北缘三院（x 577–647, z −1246…−1222）与 LY-006 任何写入区包围盒相距 >2 m（0 命中，qa/zone-overlap-cad338b.json）；原 44 院节点零改动。",
                    "ground-retained 改为默认显示，但它在 C02-010 院盒与 LY-082 巷盒内 0/1728、0/160 覆盖（qa/court-ground-probe.json）；示范院支承仍只来自 ground-south（initial=false，1728/1728 顶 0.200）。默认视图示范院下无地面这一点不变，按章加载 ground-south 的配置由 LY-050 提案、LY-100 定。"],
 },
 {
  "id": "R06", "name": "东北仓储与武库", "site": "S-STORAGE / S-NE-ROAD / S-WUKU", "batch": "东北功能区",
  "seats": ["LY-031", "LY-032", "LY-033", "LY-034", "LY-035", "LY-036", "LY-037", "LY-038", "LY-039", "LY-040"], "sharedSeats": ["LY-084"],
  "selected": {"scheme": "太仓 = 城中 storage-main（granary-city-LOD0/1/2，原位近景）；武库 = B v2.2（e5de60b6 等，固定 150° 门态）；接路 = 既有约 196 m C_NE_APPROACH_LOCAL（58f2f58a）",
               "refs": ["asset:storage-main",
                        "file:docs/cities/luoyang/progress-assets/granary-city-v1/granary-city-LOD0.glb",
                        "file:docs/library/models/m-luoyang-wuku/files/wuku-B-LOD0.glb",
                        "file:docs/library/models/m-luoyang-wuku/files/wuku-B-LOD1.glb",
                        "file:docs/library/models/m-luoyang-wuku/files/wuku-B-LOD2.glb",
                        "ws:LY-006/qa/chunks/northeast_C_access.glb"]},
  "retainedUnselected": [{"scheme": "武库 A（wuku-A 三档）", "rule": "未选；LY-038 只交只读兼容报告与负例，A/B 互斥"},
                         {"scheme": "v1 旧组 storage-group-organized / 中远档独立备选", "rule": "保留，不入本批"},
                         {"scheme": "东北长接路（约 1.7 km，三案）", "rule": "禁建（LY-003 不可落位）"}],
  "allowedChanges": ["两仓门扇枢接子件（LY-031/032，叠加节点，原仓体字节不改）与启闭联合包（LY-033）", "前场端口/路线包（LY-034，零几何）", "可关闭暂存变体（LY-035）", "武库 B 外围接地支承（LY-036，替代悬空旧片 C_WUKU_ISOLATED_SUPPORT_PATCH）", "150° 旁注契约（LY-037）", "196 m 路两端绑定与安装/撤回（LY-039，零几何）", "区域局部装配（LY-040）"],
  "forbidden": ["重造或延长 196 m 路成东北主干（LOCK-NE-196C）", "改太仓原位近景（LOCK-GRANARY-NEAR）与武库 B 门框枢轴（LOCK-WUKU-B22）", "写宫外有据或历史通行", "用北魏/隋唐仓窖（X08）、西汉长安武库（X14）"],
  "localAdmission": "放行", "cityAdmission": "条件放行",
  "cityAdmissionMeaning": "太仓附加件随 storage-main 按章加载；武库 B 与 196 m 路可作 C 设计落位提案，限在 LY-003 东北 C 试放筛查区内、卡片写「与旧研究示意不冲突，未证明在宫外」；须 LY-093 验收。",
  "evidence": ["LY-002 E-S01/E-S02（太仓、武库职能有据，「城东北隅」是研究推定）", "LY-003 admission 东北两行", "本席位复核 qa/ne-holdzone-screen.json：196 m 路 56/56、武库 B 试放分块 4846/4846 顶点在筛查区内；9 个悬置区全部在外，最紧为永安宫标签区 HZ-Y 余量 12.9 m（路）/23.8 m（武库）"],
  "allowedUnverified": ["A51/B77 原探针（I8）", "武库真轴（I9）", "武库 B 三档 14 个退化三角、A1 需 meshopt（LY-001 继承，披露）", "原生母版安装/撤回（I7）", "浏览器/GPU"],
  "blockers": [],
  "inherited": [{"from": "LY-003", "item": "东北短路「宫墙条件未决」源于几何未核；本表用 58f2f58a 实测补核为筛查区内、悬置区外，但新东墙仍未配准：落位只是 C 设计，不得据此外推长路"},
                {"from": "LY-001", "item": "旧 v1 入口太仓视图加载 storage-group-organized；v1 入口不纳入本批验收"},
                {"from": "LY-006", "item": "196 m 路短头北盖端口（x 2314.827–2317.827）未冻结，LY-006 v2 补登"}],
  "cad338bImpact": ["无改动（storage-main、evidence-geometry 不变）"],
 },
 {
  "id": "R07", "name": "作业设施（独立演示域）", "site": "S-WORK", "batch": "独立作业场（局部，不入城）",
  "seats": ["LY-051", "LY-052", "LY-053", "LY-054", "LY-055", "LY-056", "LY-057", "LY-058", "LY-059", "LY-060"], "sharedSeats": [],
  "selected": {"scheme": "厩 A（槽前地面）+ 系留分栏件 A/B；窑 A 为主（坑位 A/B 互斥都做，窑前地面只配 A）；磨 A 安装场景；足碓独立件 foot-pestle 三档；作业样板 = 「原谷物加工院」（待 I2）；全部在各自局部帧，cityPlacement=null",
               "refs": ["file:docs/library/models/m-luoyang-stable/files/A.glb", "file:docs/library/models/m-luoyang-stable/files/B.glb",
                        "file:docs/library/models/m-luoyang-tile-kiln/files/kiln-A.glb", "file:docs/library/models/m-luoyang-tile-kiln/files/kiln-B.glb",
                        "file:docs/library/models/m-luoyang-hand-mill/files/hand-mill-A.glb",
                        "file:docs/library/models/m-luoyang-foot-pestle/files/foot-pestle-LOD0.glb",
                        "file:docs/library/models/m-luoyang-workyard-shed/files/workshed-LOD0.glb"]},
  "retainedUnselected": [{"scheme": "磨 B、窑 B 前地面、厩 B 地面", "rule": "未选，保留；同帧 A/B 互斥"},
                         {"scheme": "已发布双屋作业院 workyard（7eb9739e，已作为 C_NORTH_INFILL_03 入城）与紧凑作业院 compact_work（e799b588，C_NORTH_INFILL_02）", "rule": "不是「原谷物加工院」；城中实例与原 GLB 冻结，059/060 不得改其字节或节点；若要作对照只能用局部派生副本，不得第二次入城"},
                         {"scheme": "私密母版 C02-034 workyard 试放", "rule": "未发布、无准入，不用"}],
  "allowedChanges": ["厩可拆系留/分隔件与槽前/入口地面", "窑坑与基底（剔除展示地坪）、窑前作业/暂存地面", "磨台脚支承与操作地面", "足碓踏台支承", "（I2 到位后）原谷物院屋面修订、扬谷暂存通路、围界服务口、作业场所组装"],
  "forbidden": ["城市落位或新建工业区", "窑/碓/磨/厩全塞一院", "以已发布 workyard 冒充原谷物院", "写热工/消防/动物适宜/产量结论", "污水接虚构古渠"],
  "localAdmission": "放行", "cityAdmission": "不放行",
  "cityAdmissionMeaning": "本批没有作坊/窑场选址准入（LY-002 E-H02：城内作坊位置无资料）；全部只交独立演示域包。",
  "evidence": ["LY-002 E-H02", "LY-002 E-M02（平准令、导官令只给机构，不给位置）"],
  "allowedUnverified": ["宫院与生产两族的 LY-007 数值待复核：本区第一件新件交付前须先对一张她的生产族卡做逐三角复刻（D-U09），由最先交新件的席位做并共享", "浏览器/GPU"],
  "blockers": ["I2 缺原谷物加工院：LY-057、LY-058 阻断，LY-059、LY-060 连带等待"],
  "inherited": [{"from": "LY-006", "item": "作业样板帧（058–060）保守划分；LY-060 在 registry v1 中没有写入区与外接端口，须 v2 补登"},
                {"from": "LY-008", "item": "生产族判据只有 default/house 两族，交付时可能需补家族参数"}],
  "cad338bImpact": ["workyard（7eb9739e/6baefbd0/574d81d9）与 compact_work（e799b588/ca0a6fa4/84426f91）已作为北缘第二、三院入城（默认远档，north-three 章近档）。原「059 改 workyard_earth/timber」「060 以 workyard 为互斥候选场所」的设想，现在会改到在城资产，一律禁止；只能用局部派生副本。"],
 },
 {
  "id": "R08", "name": "宫院与复道（局部 C 兼容试案）", "site": "S-PALACE / S-WATERWAY", "batch": "宫院局部研究（不入城）",
  "seats": ["LY-061", "LY-062", "LY-063", "LY-064", "LY-065", "LY-066", "LY-067", "LY-068", "LY-069", "LY-070"], "sharedSeats": ["LY-086"],
  "selected": {"scheme": "无名候入院（open/closed 三档 + 门卫切片）为组合基座，殿堂取德阳 A（候入院 registry 已含 hall__deyang-A），侧廊 sidehall-A，对阙 Q 独立前庭，玉堂 A/B 作互斥可安装副本（默认 A，不并入组合），复道 A + 登临 access-A 接西端 K-W，复道 B 只配 LY-068 登临件；宫墙水道局部墙块单列",
               "refs": ["file:docs/library/models/m-luoyang-palace-admission-court/files/palace-admission-court-open-LOD0.glb",
                        "file:docs/library/models/m-luoyang-palace-admission-court/files/palace-admission-court-closed-LOD0.glb",
                        "file:docs/library/models/m-luoyang-deyang-hall/files/deyang-A-LOD0.glb",
                        "file:docs/library/models/m-luoyang-palace-sidehall/files/sidehall-A-LOD0.glb",
                        "file:docs/library/models/m-luoyang-palace-paired-que/files/palaceque-Q-LOD0.glb",
                        "file:docs/library/models/m-luoyang-yutang-halls/files/yutang-A-LOD0.glb",
                        "file:docs/library/models/m-luoyang-palace-gallery/files/gallery-A-LOD0.glb",
                        "file:docs/library/models/m-luoyang-palace-gallery/files/gallery-B-LOD0.glb",
                        "file:docs/library/models/m-luoyang-gallery-access/files/access-A-LOD0.glb",
                        "file:docs/library/models/m-luoyang-palace-waterway-interface/files/palace-waterway-interface-near.glb"]},
  "retainedUnselected": [{"scheme": "德阳 B（七间）", "rule": "未选，保留"}, {"scheme": "玉堂 B", "rule": "与 A 互斥的副本，不同时加载"},
                         {"scheme": "31 组停用重复宫殿", "rule": "禁用（LOCK-31PALACES），不得填空白"}],
  "allowedChanges": ["候入院外围墙（LY-061，独立叠加件）", "侧口/工作口关闭件（LY-062）", "侧廊端部模块（LY-063）", "对阙前庭地坪/基脚/端口（LY-064）", "德阳 A 侧后台缘与维护口（LY-065）", "玉堂配置包（LY-066，零几何）", "复道 A 柱脚演示域地面（LY-067）", "复道 B 3.5 m 层高登临件（LY-068）", "端部廊口兼容装配（LY-069）", "局部整合包（LY-070）", "水道局部 C 墙块与竖井盖（LY-086，墙厚为 C，不代表宫墙厚度）"],
  "forbidden": ["任何带城市矩阵的宫殿/宫墙/宫门/复道/水道安装（LY-003 悬置区禁令）", "把示意线端点当宫门", "用阊阖门、太极殿、单一宫城（X04）、东掖门（X05）", "用「两宫相去七里」配准（X16）", "重做 access-A（LOCK-GALLERY-A）", "缩放水道或城垣件冒充宫墙"],
  "localAdmission": "放行", "cityAdmission": "不放行",
  "cityAdmissionMeaning": "南宫、北宫、复道、永安宫、宫墙水道全部不可落位（LY-003：共同控制点 0）；只交局部演示域包，帧 local:palace-composite 由 LY-069/070 定义，world=null。",
  "evidence": ["LY-003 tables/admission.json（宫区五行全部不可落位）", "LY-002 E-P01–E-P07"],
  "allowedUnverified": ["原检查器重跑（I12，用重写版）", "复道旧柱脚对账旧侧（I11）", "LY-007 宫院族数值待复核：本区第一件新件交付前做一张宫院族卡的逐三角复刻（D-U09）", "浏览器/GPU"],
  "blockers": [],
  "inherited": [{"from": "LY-003", "item": "旧 B 北宫南北约 1398 m 与北魏宫城同数，示意图可能混入后期数据；宫院包不得引用 B 包络尺寸"},
                {"from": "LY-001", "item": "progress-assets/palace-admission-court 6 个 GLB 与资产卡逐字节重复且无入口加载，交 LY-100"},
                {"from": "LY-006", "item": "宫院组合帧 069/070 保守划分；LY-061 write:003 标注错误、wall-end 只 1 个端口等需 v2"}],
  "cad338bImpact": ["无改动"],
 },
 {
  "id": "R09", "name": "城南礼制四所（局部安装包）", "site": "S-BIYONG / S-MINGTANG / S-LINGTAI / S-TAIXUE", "batch": "礼制安装包（局部，不入城）",
  "seats": ["LY-071", "LY-072", "LY-073", "LY-074", "LY-075", "LY-076", "LY-077", "LY-078"], "sharedSeats": [],
  "selected": {"scheme": "辟雍 = 礼堂 A + 围护 L（公开三档，按试配变换 ≤0.133 mm）；跨水只做东、西、南三处，北面无水、作车驾由北门入的地面接近；明堂 A（阶脚 r=16.64，与 LY-075 写区一致）；灵台 = 五踏步修订卡 LOD1/LOD2 上做叠加件；太学 A v3.2 + 观经空间（X2 只在局部帧）",
               "refs": ["file:docs/library/models/m-luoyang-biyong/files/biyong-A-LOD0.glb", "file:docs/library/models/m-luoyang-biyong/files/enclosure-L-LOD0.glb",
                        "file:docs/library/models/m-luoyang-mingtang/files/mingtang-A-LOD0.glb",
                        "file:docs/library/models/m-luoyang-lingtai/files/lingtai-A-LOD1.glb", "file:docs/library/models/m-luoyang-lingtai/files/lingtai-A-LOD2.glb",
                        "file:docs/library/models/m-luoyang-taixue-a/files/taixue-A-LOD1.glb",
                        "file:docs/library/models/m-luoyang-stoneclassic-access-court/files/stoneclassic_access_near.glb"]},
  "retainedUnselected": [{"scheme": "明堂 B（阶脚 r=14.48）", "rule": "未选；LY-075 已核 A/B 内部，B 保留"}, {"scheme": "辟雍围护 A-v2（母版）", "rule": "未选"},
                         {"scheme": "辟雍北面跨水板与北段水符号", "rule": "不做；水符号北段由 LY-073 去掉或标争议（LY-002 D-04、E-R05）"},
                         {"scheme": "城景研究视图 research-lingtai（c1b58de1，五踏步前的旧谱系）、research-taixue-A/B", "rule": "保留不动；哪一谱系展示由 LY-094/LY-100 定"}],
  "allowedChanges": ["辟雍装配契约、三处跨水件、岸缘与外侧地面", "明堂四侧阶前到达地面（独立节点）", "灵台未修台缘与绕行叠加件（不改 lingtai-A 字节，LOCK-LINGTAI-STEPS）", "太学 A 门外到达接口", "观经空间无损拆分单元+端口+街向带（待 LY-006 v2）"],
  "forbidden": ["城市落位", "把 B 示意点当地块", "闭合环水", "加未证楼梯、环水或北魏台基尺寸（明堂 MT8 风险）", "用西晋辟雍碑（X10）、正始石经（X11）、魏晋太学范围（X09）", "台顶加护栏"],
  "localAdmission": "放行", "cityAdmission": "不放行",
  "cityAdmissionMeaning": "四所只有 B 研究示意点、无考古控制点，install180 全部不放行（LY-004）；B 点只许作研究标记（P16/P17）。只交局部包。",
  "evidence": ["LY-004 tables/site-constraints（六站点全部不放行）", "LY-002 E-R03/E-R04/E-R05/E-R06/E-R08"],
  "allowedUnverified": ["灵台近景 LOD0（I3）", "灵台 20/80 柱脚 0.46–0.54 支承、LOD 比例低于 LY-007 下限、LY_NOT_GROUNDED 警告：均为继承，须引基线数字披露", "浏览器/GPU"],
  "blockers": [],
  "inherited": [{"from": "LY-004", "item": "现有 C 地面 ground-network-ground-stitched 有一条约 16 m 宽带从灵台、明堂标记圈之间穿过（8 个三角相交）：后续礼制包须把它当既有接口，不叠载"},
                {"from": "LY-004", "item": "R-01–R-05 命名与归章问题（南郊礼制区混名、北郊归 ritual 章等）交 LY-098/LY-100"},
                {"from": "LY-009 / LY-006", "item": "灵台：LY-006 许 LY-076 改 lingtai-A，LY-009 锁只读——本表裁定锁优先，LY-076 只交独立叠加节点"}],
  "cad338bImpact": ["无改动"],
 },
 {
  "id": "R10", "name": "南郊圆坛（单列）", "site": "S-SOUTH-ALTAR", "batch": "礼制安装包（局部，不入城）",
  "seats": ["LY-079"], "sharedSeats": [],
  "selected": {"scheme": "南郊坛 A（八陛 + 四阶），剔除 A_presentation_ground 后做接地包；局部帧",
               "refs": ["file:docs/library/models/m-luoyang-southern-altar/files/south-altar-A.glb", "file:docs/library/models/m-luoyang-southern-altar/files/south-altar-A-LOD1.glb"]},
  "retainedUnselected": [{"scheme": "南郊坛 B", "rule": "未选，保留；A/B 无历史依据可分，按「先冻结一套」选 A"}],
  "allowedChanges": ["八陛阶足端口、局部 C 地坪片、展示地面互斥"], "forbidden": ["城市落位", "与曹魏圜丘、北魏圜丘、明清天坛混同", "把《月令章句》五郊里数当测量距离（X17）"],
  "localAdmission": "放行", "cityAdmission": "不放行",
  "cityAdmissionMeaning": "只有「城南七里」文本带，未配准，不出点（LY-004）。",
  "evidence": ["LY-004 南郊行", "LY-002 E-R01"], "allowedUnverified": ["只有 LOD0+LOD1，按 LY-007 规则补 LOD2 或写明缺档", "浏览器/GPU"], "blockers": [],
  "inherited": [], "cad338bImpact": ["无改动"],
 },
 {
  "id": "R11", "name": "北郊方坛（单列，绝不归城南）", "site": "S-NORTH-ALTAR", "batch": "礼制安装包（局部，不入城）",
  "seats": ["LY-080"], "sharedSeats": [],
  "selected": {"scheme": "北郊方坛 C 三档（四陛各 6×0.200 m），按陛分 4 个 ground 端口，可选局部 T080-arrival 地坪；world=null",
               "refs": ["file:docs/library/models/m-luoyang-northern-altar/files/northern-altar-C-LOD0.glb",
                        "file:docs/library/models/m-luoyang-northern-altar/files/northern-altar-C-LOD1.glb",
                        "file:docs/library/models/m-luoyang-northern-altar/files/northern-altar-C-LOD2.glb"]},
  "retainedUnselected": [], "allowedChanges": ["4 个按陛端口（待 LY-006 v2 增登）", "局部 C 地坪片（只在 LY-080:write:001）"],
  "forbidden": ["放进城南或礼制四所区", "在北郊三说（四里/六里/西北角一里所）中择一当定论"],
  "localAdmission": "放行", "cityAdmission": "不放行",
  "cityAdmissionMeaning": "三说互斥、未配准，不出点；与城南至少相距 4.7 km（LY-004）。",
  "evidence": ["LY-004 北郊单列文件", "LY-002 E-R02、D-05"], "allowedUnverified": ["浏览器/GPU"], "blockers": [],
  "inherited": [{"from": "LY-004 R-04", "item": "项目卡把北郊方坛归在 ritual 章与城南并列，交 LY-098/LY-100 改"}], "cad338bImpact": ["无改动"],
 },
 {
  "id": "R12", "name": "地面网络·地形支承·水工（跨区服务）", "site": "S-CITYGROUND / S-WATERWAY", "batch": "随各批",
  "seats": ["LY-081", "LY-082", "LY-083", "LY-084", "LY-085", "LY-086", "LY-087", "LY-088", "LY-089", "LY-090"], "sharedSeats": [],
  "selected": {"scheme": "四块原子地面（network-ground-stitched、retained、south、D08）原样只读；cad338b 新增雍门接收片与接街只读（雍门附件，LOCK-YONG-ROAD）",
               "refs": ["asset:ground-network-ground-stitched", "asset:ground-retained", "asset:ground-south", "asset:ground-D08", "asset:yong-road-receiver", "asset:yong-road-link-far"]},
  "retainedUnselected": [{"scheme": "古河渠/水系几何", "rule": "未配准，只作文字资料层（LY-088），不画河槽、流向、码头、桥"}],
  "allowedChanges": ["可达网络契约（LY-081，三种加载态）", "C02-010 外巷短接续（LY-082，判复用）", "市肆外街接点（LY-083，复用 C_stitch_primary）", "东北对外候选审查（LY-084，只交禁建结论）",
                     "平城城南端接路（LY-085，只在平城侧；开阳侧无目标端，不造）", "水道局部安装接口（LY-086，局部墙块）", "排水端口一致性（LY-087，无准入去向即保持「未接」）", "水系分期资料层（LY-088）",
                     "地形差异片（LY-089，只在 R01–R06 有城市提案的区、按认领协议）", "多地坪开孔合成（LY-090，本批城市态只有市肆井一孔；厕孔仅有孔版启用时；窑坑、水道孔只在局部域）"],
  "forbidden": ["在未放行区铺路或补地", "改四块原子地面原文件字节（差异件另立节点）", "把水系资料层当可行走地面", "借最短路算法穿未知宫区"],
  "localAdmission": "放行", "cityAdmission": "随所服务区域",
  "cityAdmissionMeaning": "本组只为已放行区域补真实接点；服务 R07–R11 时只交局部件。",
  "evidence": ["LY-003 悬置区与道路悬置", "LY-002 E-H03、X15、X23"],
  "allowedUnverified": ["四块原子地面源工程不在仓库：差异件「从GLB重建」并标注", "PZ-06：LY-087 不依赖 LY-086，宫墙水道 drain 端口在本批记「未接（不可落位）」，依赖是否追加由协调者定", "浏览器/GPU"],
  "blockers": [],
  "inherited": [{"from": "LY-005", "item": "f28d650 起 network 替换接收片；进入 terrain 章时接收片隐藏——cad338b 已确认，LY-081 须分别给冷开、terrain 章、各区章节三种状态的可达图"},
                {"from": "LY-006", "item": "LY-089 无预分配区，按认领协议、check_registry 互检后生效"},
                {"from": "LY-081 prep MISS", "item": "「B 冻结证据 SHA fa8b7002…无文件对应」已解：cad338b 提交字节的 docs/cities/luoyang/data/evidence/evidence-geometry.json 正是 fa8b7002…（本席位 git show -c core.autocrlf=false 实算），先前不符是 CRLF 检出字节所致"}],
  "cad338bImpact": ["冷开新增 ground-retained、yong-road-link（远档）、yong-road-receiver；terrain 章新增接街近档与接收片、network 替换接收片。ground-retained 不压任何 LY-006 写入区（0 命中）；接收片压 LY-025:write:002、LY-083:write:001（见 R04）。LY-081/089 的基线要按 cad338b 三种加载态重算；四块地面 GLB 字节未变，LY-089 的 44 院支承结论仍有效。"],
 },
 {
  "id": "R13", "name": "区域验收·全城回归·核验（持续服务）", "site": "—", "batch": "每批",
  "seats": ["LY-091", "LY-092", "LY-093", "LY-094", "LY-095", "LY-096", "LY-097", "LY-098", "LY-099"], "sharedSeats": [],
  "selected": {"scheme": "按批次 manifest（selected_tasks、dependency_closure、gate_results、excluded_regions）只验本批采用的包及硬前置；未纳入的区记「本批未纳入」", "refs": []},
  "retainedUnselected": [], "allowedChanges": ["只写各自工作包的验收结论与重放脚本"], "forbidden": ["验收席位自己生产被验物", "把「本批未纳入」写成通过"],
  "localAdmission": "不涉及", "cityAdmission": "不涉及",
  "cityAdmissionMeaning": "LY-094 对宫区/礼制/南北郊按本表判「不可接城」；位置不确定度上限 75 m 冻结（见 criteria.positionUncertainty）。",
  "evidence": [], "allowedUnverified": ["v1 归档入口不纳入本批验收，只要求 LY-097 冒烟加载不报错"], "blockers": [],
  "inherited": [{"from": "LY-008", "item": "上传通道承载没有真实上限数据，LY-096 不替任何通道下结论"}],
  "cad338bImpact": ["LY-096：冷开 27 份 GLB；线上 C15 只有旧部署实测（1,408,005 B，north-three README），新部署后须重测", "LY-091：雍门保护指纹集扩到 7 个节点", "LY-092：院数口径改为「原44 + 北缘3 = 47」，示范院仍取自原44"],
 },
]

# ------------------------------------------------------------------ 席位决策（011–099）
# expected：本表预判的交付类型（补件/复用/契约/验收/阻断）；最终以席位实测为准，但不得越出 scope。
S = {}


def seat(sid, decision, expected, city, scope, unverified=(), blockers=(), needs=(), v2=None, note=None):
    S[sid] = {"seat": sid, "decision": decision, "expected": expected, "cityLanding": city, "scope": scope,
              "allowedUnverified": list(unverified), "blockers": list(blockers), "needsInputs": list(needs),
              "registryV2": v2, "note": note}


# R01 开阳
seat("LY-011", COND, "补件", CITY_PROPOSAL, "按 K-v1 实测（中门道楼板底 97% 悬空）做柱列/地栿/横梁子件三档，明确替换 C_door_head_1、C_jamb_(1,±1) 的隐藏/替换清单；柱位避开门叶开启区 y −4.55…−1.99；中门道上层继承交体 0.4–0.57 m³ 作回归哨兵",
     unverified=["荷载/结构安全（只报接触与支承比例）"], blockers=["验收条「旧0.0936m³问题有可定位的前后证据」缺 I1，保持阻断"], needs=["I1", "I7"])
seat("LY-012", GO, "补件", CITY_PROPOSAL, "门框与枢接件；本批采用「枢接 + 开/闭/中间角三态互斥」方案，不用固定开门顶替；端口取 LY-011 冻结值", unverified=["动画/运行时联锁"], needs=["I1"],
     note="D-LEAF-UV 须先量（LY-007）")
seat("LY-013", COND, "复用+补件", CITY_PROPOSAL, "保留 K-v1 C_upper_deck（84.32 m³，三档一致）作唯一楼板，只补面层/接口与完全包含式重叠检测", blockers=["「旧件替换可重放」缺 I1（21.76 m³ 重复 deck 无法定位），保持阻断"], needs=["I1"])
seat("LY-014", GO, "补件", CITY_PROPOSAL, "先重测楼面↔墙顶高差（隐藏试放土楔 15.97°、落差 0.34 m 不可沿用），做侧口/台阶/平台/墙顶端口；按 LY010-BODY-C1 全程检", needs=["I1"])
seat("LY-015", GO, "复用装配", CITY_PROPOSAL, "原门体 + 011–014 修订件 + 接墙件 + 地面的三档局部包与城墙/地面替换清单、撤回", unverified=["原生母版安装/撤回（I7）"], needs=["I7"],
     note="I1 未解除时本包可做但不得进入合并批")
# R02 平城
seat("LY-016", REUSE, "复用（预判）", CITY_PROPOSAL, "按 LY010-BODY-C1（宽 0.60 m ≤1.2 m）现有两带四片 + 旧斜路已构成两侧完整离散支承回路（西东各 1236 点无支承 0）→ 预判复用：交检查器、证据、旧斜路端口实测值+SHA；门道外暴露边交 LY-089/090 地表契约，不补",
     unverified=["原 565/3114 不能逐字重现（I6）"], needs=["I6", "I7"], v2="PZ-04：交 old-ramp 端口值后由 LY-006 v2 回填")
seat("LY-017", GO, "复用装配", CITY_PROPOSAL, "P-v1、两翼、旧斜路、侧门地面的联合局部包；中门保持关闭；路线 旧路→两侧门→旧路 回路", needs=["I7"], note="基线 = cad338b 公开城景+GLB；母版 1e8c4d 与可见集分块只作测量参照")
# R03
seat("LY-018", GO, "补件", CITY_PROPOSAL, "谷门底部支承（现 0%）、门槛地片、墙帽独立节点（三档）；工程原点与 B 示意点分别记录", unverified=["LOD0（I5）"], needs=["I5", "I7"])
seat("LY-019", GO, "补件", CITY_PROPOSAL, "夏门接缝与底部支承；旧失败接缝逐条对到几何；移除新增件可恢复", unverified=["近景档（I4）"], needs=["I4", "I7"])
seat("LY-020", GO, "补件/诊断", CITY_PROPOSAL, "只做上东门缺口一侧的坡脚/端头有限件；11 处斜接角与 12 段墙身已合格，交诊断不凑数", unverified=["生成器参数（从 GLB 重建）"])
# R04 市肆
seat("LY-021", GO, "补件", CITY_PROPOSAL, "店前线 v2.1 八处入口 0.22 m 过渡（叠加件，三档参数），门口 x 范围须独立实测", needs=["I14", "I7"])
seat("LY-022", REUSE, "复用（预判）", CITY_PROPOSAL, "C_market_ground_well_A(0.20) + 7 路带(0.21) 已连续支承前街（7720/7720）；交端口与 0.010 m 路沿说明；须加测「默认+市肆章」下接收片(0.21)共面", needs=["I7"])
seat("LY-023", REUSE, "复用（预判）", CITY_PROPOSAL, "T1–T3 24/24 脚接地 → 复用适配包；F 组店前线棚岛只在 LY-022 定地坪后做 shim 叠加件")
seat("LY-024", GO, "补件", CITY_PROPOSAL, "一类铺型（S84）闭铺静态互斥态，证据未知标 C；不改宿主", unverified=["LY-002 闭铺证据：未知"], needs=["I14"])
seat("LY-025", REUSE, "复用", CITY_PROPOSAL, "井 A（121 节点，去展示坪）+ 开孔地面（sample_ground 外框 + r0.590 48 边孔）原子包，按 cad338b 重绑；测接收片共面", needs=["I15", "I7"])
seat("LY-026", REUSE, "复用（预判）", CITY_PROPOSAL, "四个井族 GLB 操作件兼容检查；未列接触分类须补完才可判复用", needs=["I15"])
seat("LY-027", GO, "补件", CITY_PROPOSAL, "选定组 = F（v2.1）：补悬空三层板支承与可删占位、满/空两态；A 组只交回退态清单（零几何）", needs=["I14"])
seat("LY-028", GO, "补件", CITY_PROPOSAL, "F 组 C02 东边卸货/暂存地面（OP_C02E），与主行路、井操作域互斥检查；货物包络 LY010-CARRY-C1")
seat("LY-029", GO, "复用装配", CITY_PROPOSAL, "V1/V2/F 三套互斥与回退包（excludeNodes 由本席位唯一提出，LY-025 不另改 market-main excludeNodes）", needs=["I14", "I7"])
seat("LY-030", GO, "复用装配", CITY_PROPOSAL, "F 区域局部交付（完整近景、地面、井、操作区、同机位前后图）", needs=["I7"])
# R05 示范住宅
seat("LY-041", REUSE, "复用", CITY_PROPOSAL, "C02-010 已有完整支承（ground-south 覆盖 1.0）→ 复用：交选院、矩阵、底部三角清单、按章同载说明、检查器")
seat("LY-042", GO, "复用装配", CITY_PROPOSAL, "「012内门v2」按 m-luoyang-inner-door-components paired-door 三档认定（仓库无名为 v2 的文件，记为本表假定）；两处门位接回 C02-010；默认 90° 开态，闭态可由实测轴旋转派生（标从GLB重建），新旧门叶互斥",
     v2="写入区须罩门框墙面与开叶侧、旧叶隐藏机制（派生宿主）", note="D-LEAF-UV 须先量")
seat("LY-043", REUSE, "复用", CITY_PROPOSAL, "C02-010 院墙转角、门墩接墙全部闭合面接触、无侵入 → 复用，交逐区域接面清单与负例；墙房样例不换入城景")
seat("LY-044", GO, "复用装配", CITY_PROPOSAL, "灶 A 一处（原件 + 一个矩阵，W2 文件不叠载），操作/转身域按 LY010-BODY-C1", unverified=["W2 原 QA（I10）"], needs=["I10"])
seat("LY-045", GO, "复用装配", CITY_PROPOSAL, "service-A 东院现朝向；默认无孔版；有孔版仅与 LY-090 局部地面替换件同启，坑深「未定」", unverified=["坑深/用途"])
seat("LY-046", GO, "补件", CITY_PROPOSAL, "C02-010 一小段滴水/浅沟试片与出口端口；无准入去向则停在试片，端口标「未接」")
seat("LY-047", REUSE, "复用（说明）", NO_GEOM, "C02-010 不装储藏/棚；交路线 R（B/B2 院原位作业棚与储藏屋）的复用说明与子件清单，不加载、不入城变更")
seat("LY-048", REUSE, "复用", CITY_PROPOSAL, "本表定：示范院不设侧口，主院门只声明开启态 → 零新几何，交围界闭合实测与 C02-010:service-opening:opening 端口声明")
seat("LY-049", REUSE, "复用", CITY_PROPOSAL, "ground-south 已单层连续承托门道到院界 → 交端口 C02-010:gate-boundary:road-end 数值与检查器")
seat("LY-050", GO, "复用装配", CITY_PROPOSAL, "按用途组合 U1 组装单院完整包与可关闭设施组、按章同载 ground-south 的提案；恢复后指纹一致")
# R06 东北
seat("LY-031", GO, "补件", CITY_PROPOSAL, "太仓 A 门扇枢接子件（1.50×2.10 洞口），叠加节点", unverified=["A51 原探针（I8）"], needs=["I8"], note="D-LEAF-UV 须先量")
seat("LY-032", GO, "补件", CITY_PROPOSAL, "太仓 B 门扇枢接子件，叠加节点", unverified=["B77 原探针（I8）"], needs=["I8"], note="D-LEAF-UV 须先量")
seat("LY-033", GO, "复用装配", CITY_PROPOSAL, "两仓开/闭联合包，门态用互斥文件或 excludeNodes（按 LY-006/007 冻结口径）", needs=["I8"])
seat("LY-034", REUSE, "复用", CITY_PROPOSAL, "前场零几何改动：交端口 JSON、路线包、安装与撤回记录")
seat("LY-035", GO, "补件", CITY_PROPOSAL, "可关闭、带互斥规则的暂存附加件，避让门叶扫掠；搬运包络 LY010-CARRY-C1")
seat("LY-036", GO, "补件", CITY_PROPOSAL, "武库 B 外围接地支承（替代 81 m 悬空自由边的旧片），与 196 m 路南端接缝", needs=["I9", "I7"])
seat("LY-037", REUSE, "契约（零几何）", CITY_PROPOSAL, "150° 门态旁注契约 + QA（台前侧路净宽 1.048 m）；门叶不拆独立节点，以三角范围旁注表达", needs=["I9"])
seat("LY-038", REUSE, "复用（只读报告）", NO_GEOM, "本表选 B → A 只交只读兼容报告与负例，不出安装包")
seat("LY-039", REUSE, "复用", CITY_PROPOSAL, "196 m 路零几何重绑定：北接太仓地坪、南接 LY-036 新支承；交安装/撤回；准入依据用本表 ne-holdzone-screen", v2="短头北盖端口", needs=["I17", "I7"])
seat("LY-040", GO, "复用装配", CITY_PROPOSAL, "太仓 + 武库 B + 196 m 路区域局部装配；不延伸长路", needs=["I17", "I7"])
# R07 作业
seat("LY-051", GO, "补件", LOCAL_ONLY, "厩 A/B 各一套可拆系留/分隔件（LY-006 write:001/002）")
seat("LY-052", GO, "补件", LOCAL_ONLY, "厩 A 槽前/入口/清扫地面与有限排水端口；污水终端「未接」")
seat("LY-053", GO, "补件", LOCAL_ONLY, "窑 A、B 两套互斥实验坑与基底，剔除展示地坪；原子切地形契约 host=null")
seat("LY-054", GO, "补件", LOCAL_ONLY, "配窑 A 的前作业地面、接近口与暂存占位")
seat("LY-055", GO, "复用装配", LOCAL_ONLY, "磨 A 安装场景：台脚支承、操作地面；磨 B 不装；只有 LOD0+LOD1 时写明缺档")
seat("LY-056", GO, "复用装配", LOCAL_ONLY, "foot-pestle 独立件在局部作业地坪上的支承包；workyard 内嵌碓只作只读对照，不改")
seat("LY-057", BLOCK, "阻断", LOCAL_ONLY, "原谷物加工院工作棚屋面修订", blockers=["缺 I2；不得以 workshed/workyard 代替（任务池「已发布双屋作业院为不同产物」）"], needs=["I2"])
seat("LY-058", BLOCK, "阻断", LOCAL_ONLY, "原谷物院扬谷暂存通路", blockers=["缺 I2；前件 LY-057 阻断"], needs=["I2"])
seat("LY-059", WAIT, "补件", LOCAL_ONLY, "作业样板 = 原谷物加工院（I2 到位后）的围界服务口；不改城中 workyard/compact_work", needs=["I2"])
seat("LY-060", WAIT, "复用装配", LOCAL_ONLY, "作业设施独立演示域组装；registry v1 无写入区，须 v2", v2="演示域承托地坪写入区与外接端口", needs=["I2"])
# R08 宫院
seat("LY-061", GO, "补件", LOCAL_ONLY, "候入院外围墙（独立叠加件，只在 LY-061:write:001..007）；墙外基准由本包自带垫层，其下为未定义地形", needs=["I12", "I16"], v2="wall-end 6 个端口；061→063 接缝", note="宫院族 D-U09 复刻建议由本席位先做")
seat("LY-062", GO, "补件", LOCAL_ONLY, "侧口/工作口关闭件（overlay）", needs=["I12"], v2="C1：write:003 实为南轴主入口；C2：门卫线关闭件无写入区", note="D-LEAF-UV 须先量")
seat("LY-063", GO, "补件", LOCAL_ONLY, "侧廊 4 个端部的封端/地面过渡（不做转折件，除非 061 交出转向目标）", needs=["I12"])
seat("LY-064", GO, "补件", LOCAL_ONLY, "对阙独立前庭（不并入候入院），地坪/基脚/边缘/端口三档")
seat("LY-065", GO, "补件", LOCAL_ONLY, "德阳 A 侧后台缘与维护接口（台顶 1.80 m）", v2="LY-065 写入区 y 上限 1.6 m 低于台顶，须 v2 后才能交几何")
seat("LY-066", REUSE, "复用装配", LOCAL_ONLY, "玉堂 A/B 互斥可安装配置包（引用原件，cityPlacement=null）", needs=["I13", "I16"])
seat("LY-067", GO, "补件", LOCAL_ONLY, "复道 A 柱脚在冻结局部演示域地面上的适配（只在 LY-067:write:001）", needs=["I11"])
seat("LY-068", GO, "补件", LOCAL_ONLY, "复道 B（层高 3.500）登临兼容件", needs=["I11"])
seat("LY-069", GO, "复用装配", LOCAL_ONLY, "复道 A 西端 K-W 与登临、侧口、廊口的兼容包", needs=["I11", "I12"], v2="登临梯脚垫落在 new_court_support_C 体内的切孔/合法埋入裁定")
seat("LY-070", GO, "复用装配", LOCAL_ONLY, "宫院复道局部整合包（定义 local:palace-composite 帧）", needs=["I11", "I12", "I16"])
seat("LY-086", GO, "复用装配", LOCAL_ONLY, "三段水道在 LY-086 自带的 C 局部墙块（厚 = 水道长 6.600 m）上的可撤回安装；不借城垣 earthwall 冒充宫墙、不缩放；盖/竖井 9 mm 继承侵入须分类", v2="local:waterway 宿主墙块写入区", unverified=["底坡 0（无流向）只记录"])
# R09 礼制
seat("LY-071", REUSE, "复用装配", LOCAL_ONLY, "礼堂 A + 围护 L 装配契约（变换 ≤0.133 mm 重算），端口 biyong:hall-enclosure:ground", v2="S-BIYONG 区盒按实测重划")
seat("LY-072", GO, "补件", LOCAL_ONLY, "东、西、南三处跨水件（替换 A_crossing_0_±1 / 1_-1 占位）；不做北板", v2="跨水写入区实际不含试配位置，须 v2")
seat("LY-073", GO, "补件", LOCAL_ONLY, "岸缘与外侧地面（外岸基准 0.20），北段无水作地面接近；水符号北段去掉或标争议", v2="r 67.65–90 及另三轴写入区")
seat("LY-074", GO, "补件", LOCAL_ONLY, "明堂 A 四侧阶前到达地面（阶脚线 r=16.64），独立节点")
seat("LY-075", REUSE, "复用", LOCAL_ONLY, "明堂 A/B 内部检查已 pass → 复用；待 LY-074 端口后把合成地面换成真实到达地面重跑")
seat("LY-076", GO, "补件", LOCAL_ONLY, "在五踏步修订卡 LOD1/LOD2 上做未修台缘与绕行的独立叠加件；北侧窄绕行保持不加宽", unverified=["近景档（I3）"], needs=["I3"])
seat("LY-077", GO, "补件", LOCAL_ONLY, "太学 A v3.2 门外到达地面（局部研究帧），与 v1 A_presentation_ground 互斥")
seat("LY-078", GO, "复用装配", LOCAL_ONLY, "观经空间无损拆分单元 + 南口端口 + 街向带；X2 与太学 A 的关系只在局部帧", v2="源对象由 keep 改为可派生无损拆分副本")
# R10/R11
seat("LY-079", GO, "复用装配", LOCAL_ONLY, "南郊坛 A 接地包（剔除展示地面、八陛端口）")
seat("LY-080", GO, "复用装配", LOCAL_ONLY, "北郊方坛接地包（四陛端口、可选局部地坪）", v2="4 个按陛 ground 端口")
# R12
seat("LY-081", CONTRACT, "契约", NO_GEOM, "按 cad338b 实际加载 GLB 三角建立冷开 / terrain 章 / 各区章节三种状态的可达网络与断点/禁连边；只给已放行区（R01–R06）提供可接断点")
seat("LY-082", REUSE, "复用（预判）", CITY_PROPOSAL, "ground-south 已把 C02-010 院界接到巷面（15,300/15,300 格承托）→ 预判复用；南组 14 院区域按本表 R05 放行")
seat("LY-083", REUSE, "复用（预判）", CITY_PROPOSAL, "外街复用 C_stitch_primary（无新几何）；须按 cad338b 重测接收片/network 切换后有无双层")
seat("LY-084", CONTRACT, "契约（禁建）", FORBIDDEN, "三条长接路候选全部禁建，交审查表与有条件契约模板，不交几何", needs=["I17"])
seat("LY-085", GO, "补件", CITY_PROPOSAL, "只做平城门城南端接到 C_stitch_primary（y −60.454…−6.353 楔段归属待 LY-006）；开阳侧因城南礼制未配准无目标端，不造", note="依赖 LY-015：开阳侧不造也须等 015 冻结门端口后交付")
seat("LY-087", GO, "复用装配", NO_GEOM, "汇总排水端口与坡向；无准入去向一律「未接」；宫墙水道 drain 端口记「不可落位」", note="PZ-06 由协调者定")
seat("LY-088", CONTRACT, "契约（资料层）", NO_GEOM, "水系分期文字/关系资料层，null 几何只出文字")
seat("LY-089", GO, "补件", CITY_PROPOSAL, "只在 R01–R06 的城市提案区内、经认领协议的缺口出差异片（如 G-7/G-8 接缝）；44 院不造片")
seat("LY-090", GO, "复用装配", CITY_PROPOSAL, "本批城市态开孔清单 = 市肆井一孔（几何即 C_market_ground_well_A）+ 示范院圈厕有孔版（可选）；窑坑、水道孔只进局部域合成")
# R13
for sid in ["LY-091", "LY-092", "LY-093", "LY-094", "LY-095", "LY-096", "LY-097", "LY-098", "LY-099"]:
    seat(sid, SERVICE, "验收", NO_GEOM, "按批次 manifest 只验本批采用的包及硬前置；未纳入区写「本批未纳入」")
S["LY-094"]["scope"] += "；宫区/礼制/南北郊按本表全部判不可接城，R12 不确定度上限 75 m"
S["LY-096"]["scope"] += "；冷开集合以 cad338b 27 份 GLB 为准，新部署后重测 C15"

SEATS = S

# ------------------------------------------------------------------ 需协调者处理的 registry v2 与锁
REGISTRY_V2 = {sid: v["registryV2"] for sid, v in S.items() if v["registryV2"]}
REGISTRY_V2_EXTRA = {
    "north-three": "registry v1 早于 cad338b：C_NORTH_INFILL_01–03(+near) 与 ground-retained.initial 不在任何写入区（实测 0 命中），应登记为 frozen、owner=原负责人，不分给任何席位",
    "LY-087": "可选：给 6 条现有 TC03 浅沟补登 drain 端口",
}
LOCK_PROPOSALS = [
    {"id": "LOCK-NORTH3（提案）", "scope": "cad338b 北缘三院：节点 C_NORTH_INFILL_01–03 与 -near、north-three 章、progress-assets/north-three-v1/、ground-retained 的 initial=true", "holder": "原负责人（伊苏里亚，r2026.11.05-8）",
     "reason": "PZ-13 已指出北缘三院未纳入 13 院锁；它们复用 workyard/compact_work/opposed_rooms 原 GLB，R05/R07 席位都可能误碰"},
    {"id": "LOCK-YONG-ROAD 扩充（提案）", "scope": "加入 progress-assets/yong-road-link-v2/ 四个 GLB、节点 yong-gate-body-far / yong-gate-interface-far / yong-road-link / yong-road-link-near / yong-road-receiver、ground-network-ground-stitched.replaces", "holder": "原负责人（雍门接街）",
     "reason": "b70c495 把接街与接收片归为雍门附件；LY-083/085/089 会读到接收片"},
]
COORDINATOR_DECISIONS = [
    "I1 若确认已不存在：是否书面修订 LY-011/013 验收条（LY-010 无权豁免）",
    "I2 原谷物加工院是否存在、何时提供；若不存在，LY-057/058 是撤销还是改题（改题须重排依赖）",
    "PZ-06：LY-087 是否追加依赖 LY-086",
    "registry v2 由谁发（LY-006 已交付）：本表列出 15 处需求",
    "LOCK-NORTH3 与 LOCK-YONG-ROAD 扩充两条锁提案",
    "市肆城中默认显示 V1 还是 F（在 LY-092 验收之后）",
    "示范院按章同载 ground-south 的加载配置（LY-050 提案，LY-100 定）",
    "LY-007 六项待拍板（P-GENERATOR 等）",
]

# ------------------------------------------------------------------ 建议批次（LY-100/协调者最终定）
BATCHES = [
    {"id": "B1", "name": "示范住宅", "selected_tasks": ["LY-041", "LY-042", "LY-043", "LY-044", "LY-045", "LY-046", "LY-047", "LY-048", "LY-049", "LY-050", "LY-081", "LY-082"],
     "acceptance": ["LY-092", "LY-095", "LY-096", "LY-097", "LY-098", "LY-099"], "note": "圈厕取无孔版，不需 LY-090；LY-089 不造片"},
    {"id": "B2", "name": "平城局部", "selected_tasks": ["LY-016", "LY-017"], "acceptance": ["LY-091", "LY-095", "LY-096", "LY-097", "LY-098", "LY-099"],
     "note": "LY-085 依赖 LY-015，不进本批"},
    {"id": "B3", "name": "东北功能区", "selected_tasks": ["LY-031", "LY-032", "LY-033", "LY-034", "LY-035", "LY-036", "LY-037", "LY-038", "LY-039", "LY-040", "LY-084", "LY-081"],
     "acceptance": ["LY-093", "LY-095", "LY-096", "LY-097", "LY-098", "LY-099"], "note": "LY-084 只交禁建契约"},
    {"id": "B4", "name": "市肆", "selected_tasks": ["LY-021", "LY-022", "LY-023", "LY-024", "LY-025", "LY-026", "LY-027", "LY-028", "LY-029", "LY-030", "LY-081", "LY-083"],
     "acceptance": ["LY-092", "LY-095", "LY-096", "LY-097", "LY-098", "LY-099"], "note": "默认仍 V1；F 为互斥提案"},
    {"id": "B5", "name": "谷门夏门城垣", "selected_tasks": ["LY-018", "LY-019", "LY-020"], "acceptance": ["LY-091", "LY-095", "LY-096", "LY-097", "LY-098", "LY-099"], "note": "如需地形差异片，加 LY-081、LY-089"},
    {"id": "B6", "name": "开阳局部 + 平城开阳城南端接", "selected_tasks": ["LY-011", "LY-012", "LY-013", "LY-014", "LY-015", "LY-081", "LY-085"],
     "acceptance": ["LY-091", "LY-095", "LY-096", "LY-097", "LY-098", "LY-099"], "note": "I1 未解除不得开批；LY-085 的平城侧前件 LY-016/017 在 B2"},
    {"id": "L1", "name": "局部研究包（不入城，只走资产库提案）", "selected_tasks": ["LY-051", "LY-052", "LY-053", "LY-054", "LY-055", "LY-056", "LY-061", "LY-062", "LY-063", "LY-064", "LY-065", "LY-066", "LY-067", "LY-068", "LY-069", "LY-070", "LY-086", "LY-071", "LY-072", "LY-073", "LY-074", "LY-075", "LY-076", "LY-077", "LY-078", "LY-079", "LY-080", "LY-087", "LY-088"],
     "acceptance": ["LY-093", "LY-094", "LY-096", "LY-098", "LY-099"], "note": "LY-057–060 待 I2；全部 cityPlacement=null"},
]
