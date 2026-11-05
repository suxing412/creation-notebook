# LY-059 作坊围界与服务口补件 · 开工准备草稿（prep）

状态：**待输入**（G 未冻结；LY-010 未选样板；LY-053/054/058 未交付）。本目录只含读输入、实测和测试准备，没有任何交付几何。
核对基线：creation-notebook-lab main `bce3211f818ee5a8bef1773539da70695ba37b17`（只读）。Blender 5.2.1 headless，factory-startup。

## 1. 本项目标（照任务池原文）

为 LY-010 选定的**一个**作业样板，补实测得出的外围缺口、工作门口（服务口）和台阶接口。
- 不重造已有院墙，现围墙不能再叠一圈。
- 窑、碓、磨、厩不能全部塞进同一院。
- 围界具体形态属于 C（工程设计），不认定行业分区，也不认定法定隔离距离。
- 验收要求：外围与服务口的开放/关闭规则写清楚；选定的场所和被排除的设施都要进安装清单。

## 2. 核到的现有成果（SHA256 全长见 inputs.json）

| 候选 | 文件 | SHA256（前12位） | 在城景里 |
|---|---|---|---|
| 双屋足碓作业院（已发布，待审） | docs/library/models/m-luoyang-workyard-shed/files/workyard-LOD0/1/2.glb | 7eb9739ec09a / 6baefbd0fc1b / 574d81d91d38 | **未加载**。只在 p-luoyang.asset.json:568 的 related 里出现 |
| 开敞作业棚（同卡） | workshed-LOD0/1/2.glb | 89e0a43923fb / a21c2893a1cc / 7c054863f108 | 未加载 |
| 紧凑作业院布局 | docs/library/models/m-luoyang-court-layout-kit/files/compact_work-LOD0.glb | e799b5880cd1 | 未加载（只在私有母版 C_NORTH_INFILL_02 里出现） |
| 北区储藏作业院 court-B v2 | docs/cities/luoyang/progress-assets/north13-gates/luoyang-north-four-courts-v2/models/court-B-LOD1/2.glb | 2be52632e16e / 641b05a535a2 | 作为 local-study 加载：city-data.mjs:806–850 与 4232，由 city-renderer.mjs:619 focusResearchModel 显示，没有落城 |
| 城里实际的 B 院 R01-B | docs/cities/luoyang/assets/r01/R01-B-LOD0/LOD1-prototype.glb | a8d94bb38978 / 25f018fa8fad | **已入城**：city-data.mjs:35–57 的 courtyard-B，排除 site_lot、site_neutral_lane、designed_loading_yard 三个节点；C02-034 在 city-data.mjs:2742（"住宅院落 34"）；布局见 data/c02v/layout.json，由 v1/west-layer.mjs:17 加载 |
| 私有母版里的作业院试放 | city-visible 交接 adapter.json 的 res_workyard_034（C02-034__workyard_trial__*）与 C_NORTH_INFILL_03__workyard_* | chunk 6ed43d99447c（1849736 B） | 网页未接入。只在私有 city-C032-entry-LOD0.blend 里可见 |
| 「原谷物加工院」及其缺陷记录 | **仓库内找不到**（全仓搜「谷物/加工院/扬谷/舂」0 命中） | — | — |

**关键实测结论：四个候选共用同一个院框。** workyard、compact_work、court-B 和 R01-B 的外围墙、门位和门洞，在 0.05 m 分辨率下扫描结果完全一致（见 §5）。所以「现有院墙」实际上就是 R01-B 院框。它已经以 courtyard-B 在城里实例化（C02 有 14 个 B 院），也属于保护清单里「13院模型压缩」的北区四院 v2。LY-059 不能改这个框，只能作为样板自己的 overlay 或互斥变体交付。

## 3. 改 / 不改范围（草案，等 LY-006 端口和 LY-010 选择冻结后定稿）

**可以改（仅限 workpacks/LY-059/）**
- 新增独立的服务口组件：在指定墙段开洞的替换墙段（互斥替换，不叠加），配门框、门扇（开 / 闭两个状态，各自独立语义），门外台阶或坡道接口。
- 主门口的门槛和门内外支持面差异件（只在样板地坪与外部地形有高差时才需要）。
- 安装清单：选定场所、被排除设施（窑 A/B、磨 A/B、厩 A/B 按 010 的结论列出），以及开放 / 关闭规则。

**不改**
- R01-B / court-B / workyard / compact_work 的原 GLB 与原节点（矩阵、材质、几何都不动）。
- 城里 14 个 courtyard-B 实例、city-data.mjs、项目卡。
- 院内房屋门阶（属于房屋资产）、足碓本体（LY-056）、窑坑（LY-053）、窑前地面（LY-054）、院内通路（LY-058）。

## 4. 证据与未知（四类分栏）

| 事项 | 类别 | 说明 |
|---|---|---|
| 院框 18×24 m、墙厚 0.35 m、墙高 2.2 m、单门 | C 工程设计 | 来自 R01 合同 lot 18×24、ground_top_z 0.2（data/r01/model-contract.json）。不是遗址尺度 |
| 院落形制的类比 | 异地异期类比（二手记录） | r01 合同写的是「Henan Eastern Han Zhangmao courtyard mingqi; not Luoyang city residential foundation」。本轮没有回看原图版 |
| 服务口位置、宽度、门扇、开闭规则 | C | 本项要新定，必须标 C |
| 约 180 年洛阳作坊围界、门制、行业分区 | 未知 | 仓库内没有原始考古或原文。本轮没有做网络查证，也没有引用任何外部文献 |
| 地形高程 0.2 m 平地 | C 工程（城景现状） | C02 / C02v 环境地形是 C 布局实验，不是古地面 |

五件事分开写：「模型能读取」已由 audit 和本轮回读证明；「局部通行」本轮只有离散射线，不能算通过；「已入城」中 workyard 未入城；「真实结构安全」和「历史复原成立」都未验证，不作主张。

## 5. 实测缺口（脚本都在本目录，Blender 坐标 Z 向上：X=glTF X，Y=−glTF Z）

脚本：measure_enclosure.py、probe_gate.py、probe_inner_band.py、probe_coping.py、probe_terrain.py。结果 JSON 与脚本同目录。

1. **外围缺口 = 0（门洞除外）。** 周界水平射线（高度 0.15/0.5/1.0/1.6 m，步长 0.05 m，穿深 2.5 m）在 84 m 周长上只发现一个通透段，即主门。墙顶压顶扫描（probe_coping.py）四边没有裸露段（只在角点有掠射样本）。LOD0、LOD1、LOD2、compact_work、court-B 结果相同。**结论：没有需要补的墙体缺口。**
2. **服务口 / 工作门口：不存在。** 全院唯一开口在 Blender −Y 墙（glTF +Z，对应城中 C02-034 朝 C02_upper_spur 的一侧）。墙洞 x −6.30…−3.30，宽 3.00 m；门墩之间净宽 2.40 m（x −6.00…−3.60）；开启门扇之间净宽 **2.13 m**（x −5.865…−3.735）；门洞木梁底 z=2.25，相对院基 0.2 净高 **2.05 m**；门屋进深 y −11.8…−9.4（2.4 m）。北、东、西三面墙连续，没有任何门口。
3. **主门门扇只有「全开」一种静态形态。** 门扇是贴在门墩内侧的 0.07×1.10×2.00 m 木板（y −11.55…−10.45），没有关闭状态，也没有独立节点（并在 workyard_timber 里）。**开放 / 关闭规则目前无法用现有几何表达。**
4. **门内外没有任何地面几何。** workyard、compact_work、court-B 都不带地坪（2 m 外沿 752 个竖直采样 0 命中；门洞中心线向下 0 命中），全靠外部地形托底。R01-B 带 site_lot（0→0.2）、4 m 中性前巷和 designed_loading_yard（x −5.6…2.72，y −16…4.38，z 0.2–0.215），但城里这三个节点都被排除。
5. **门外高差 = 0.000 m（仅限 C02-034 现址）。** C02 与 C02v 环境地形在门前 y 1062.2…1072.2 范围内全部为 z=0.2（0.0001 m 以内），与院基 0.2 齐平。道路 C02_upper_spur 中线 y=1064、宽 3.5 m，路沿到墙外皮只有 **2.45 m**。所以主门在现址**不需要台阶**。如果 010 选的是其他地块，或 LY-053 的窑坑改了地形，这一条要重测。
6. **服务口的候选墙段（墙内 2.0 m 进深无遮挡，三个高度取最小值）：**
   - workyard：北墙 x −8.65…−4.85 与 4.85…8.65（各 3.8 m）；西墙 y −11.65…−6.15（5.5 m）、1.15…11.65（10.5 m）；东墙 y −11.65…−4.75（6.9 m）、1.75…11.65（9.9 m）。
   - compact_work：北墙各 5.4 m；东墙 0.75…11.65（10.9 m）。
   - 主门入院直行 3.25 m 后在 y=−6.1 被院内建筑挡住（workyard 与 compact_work 都是这样），入口必须折行。court-B 直行 14.45 m。
7. **所有权冲突：** 外围墙和院内房屋的夯土墙在同一个网格对象 workyard_earth（424 三角，bbox 覆盖整院，z 到 4.9）里。court-B 与 R01-B 也一样（architecture_C_whitebox_earth_wall）。开服务口不能切原网格，只能隐藏原对象、换成拆分后的墙段，或作为 overlay 替换段。具体由 LY-006 定归属。

## 6. 与相邻席位的接口（待冻结）

- LY-053/054（窑）：若样板选窑场，窑前操作地面要接服务口的门外地坪；窑本体不进 workyard 院（院内已有足碓：石臼 x 4.54…5.46、y −0.66…0.26；杠杆 x 4.89…5.11）。
- LY-058：入院、舂作、扬谷、暂存路线从主门 (−4.8, −12.0) 起，服务口作为第二端口。
- LY-060：互斥规则（服务口开 / 闭，原墙段 / 替换墙段）交给 060 组包。

## 7. 复核记录（2026-11-05 23:26）

- lab HEAD 仍是 bce3211f818ee5a8bef1773539da70695ba37b17，工作树只有未跟踪的 .claude/，没有改动。
- inputs.json 里 9 个关键输入的 SHA256 重新计算，前 16 位全部一致。
- city-data.mjs:35–57（courtyard-B 的 excludeNodes 三项）、:2742（C02-034）、v1/west-layer.mjs:17（c02v/layout.json）重新读过，与上文一致。
- 「谷物 / 加工院 / 扬谷」和 grain / threshing / winnow 在 docs/library/models、docs/model-library、lab/data/assets.json、p-luoyang.asset.json 里仍然 0 命中。
- measure_enclosure.py 对 workyard-LOD0 重跑一次（Blender exit 0），输出 JSON 与 workyard-LOD0.enclosure.json 逐字段相同。周界通透段只有主门 x −5.85…−3.75（2.15 m 采样宽）；两侧 0.05–0.1 m 的单点是门扇缝和角点掠射，不是墙体缺口。
