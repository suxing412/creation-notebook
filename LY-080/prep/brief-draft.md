# LY-080 北郊方坛四陛接地包 · 开工准备简报（草稿）

状态：**开工准备，待输入**。本目录只放读取、测量与测试准备，没有制作或修改任何交付几何。

前置席位状态（2026-11-06 复核，各席位 status.json）：

| 席位 | 状态 | 对本项的结论 |
|---|---|---|
| LY-001 / 002 / 005 / 007 / 008 / 009 | 交付完成 | 见下文 |
| LY-004 | 交付完成（status.json SHA256 c9358ea5…7906） | 北郊**未配准**。三说互斥：A 城北四里、B 六里、C 西北角一里所，都不出点。`geometry/north-suburb.json`（eb4ae791…0cd4）明写 LY-079、LY-080 不能取得位置放行 |
| LY-006 | 交付完成 | 给本项登记了 site `S-NORTH-ALTAR`、frame `local:north-altar`（placement=null）、写区 `LY-080:write:001`、组件 `T080-arrival`（fixed），以及**唯一一个**端口 `north-altar:stairs:ground` v1 |
| **LY-010** | **无工作包** | 区域准入与首批方案未冻结，所以 **G 仍未冻结** |

**复核时重跑了测量**：`python -I prep/measure_altar.py <lab> <out>`，输出与 `prep/measure_out.json` 逐键相同。

基线：`D:/GitHub/creation-notebook-lab` main `bce3211f818ee5a8bef1773539da70695ba37b17`（只读）。资产目录最后一次提交：`c0555aa`（2026-11-05 15:01:28 +0800）。

## 1. 本项目标（照任务池原文）

把现有的方坛四陛做成北郊独立安装包：坛体加四陛、四个地面端口、可撤回。北郊与城南严格分开；围营、祠舍、具体位置都是未知，不能把四陛模型扩称完整北郊。

本项是**复用装配**，不重造坛体。

## 2. 核到的现有成果

| 文件 | SHA256 | 字节 | 说明 |
|---|---|---|---|
| docs/library/models/m-luoyang-northern-altar/files/northern-altar-C-LOD0.glb | d62dce7d2130828c4e309edf42701fd8890454d39d51d2763f16fe351a8e6ebe | 425,760 | 512 px 纹理 |
| …/northern-altar-C-LOD1.glb | 4842be77757597237ddcedcd1e2d2f66402db0dcde57986e9fbb926cc096d6dd | 164,836 | 256 px 纹理 |
| …/northern-altar-C-LOD2.glb | 7c7f3a51ac7cce90137a8a0210f3031129058b5d7e21a1eb850bc222953a1287 | 25,644 | 64 px 纹理 |
| …/m-luoyang-northern-altar.asset.json | 检出 091332bc…a18899；提交 blob 9deabeb6…fe666c（行尾差异） | 1,739 | 状态“待审”，“未入城” |

三档 GLB 在检出文件和 `git show bce3211:` 里的字节 SHA 完全一致。

GLB 自带的元数据：场景 extras 写着 `cityPlacement:"null"`、`evidenceGrade:"C_DIMENSIONAL_PLACEHOLDER"`、`northAxisNative:"+Y"`、`sourceConfig:"config/altar.json"`、`lodGeometryPolicy:"identical topology; texture tiers only"`。唯一的节点叫 `north_altar_platform_four_stepped_approaches_C`，extras 里有 `placementStatus:"independent_candidate_not_in_city"`、`enclosureEntrances:"unknown_and_not_modeled"` 和 `accessCount:4`。

**城景加载状态**：没有加载。`city-data.mjs` 的 assets、nodes、researchModels 三处都找不到 `northern` 或 `北郊`。城景里也没有“独立查看”入口，而灵台、太学有。它出现的地方只有这些：项目卡 `p-luoyang.asset.json` 第 179–184 行（进度条目“已建模”，备注“未定址”）和第 536 行（related 列表），`lab/data/assets.json` 第 834 行和第 4121–4268 行，以及 `glb-cache.json`、`report.json`。LY-001 台账的记法是“仅模型（资产卡文件）”，城市节点数 0。

## 3. 改 / 不改范围（拟）

**不改**：
- 三档 GLB 的字节一律不动，直接引用原件。
- 不改坛体尺寸、陛数、踏步；不加围营、营门、祠舍、壝墙、兆域界。
- 不写任何城南坐标，也不从南郊圆坛（m-luoyang-southern-altar）取几何或位置。

**改，在本工作包内**：
- `assembly.json`：原节点到安装节点的映射；本地 N 默认为单位矩阵，世界 N 在 LY-004 给出前保持 `null` 或“未定址”。
- 四个 `ground` 类端口（东、西、南、北各一）和四个陛顶 `floor` 端口。
  - LY-006 目前只登记了 `north-altar:stairs:ground` 一个端口，见 G8。portId 以 LY-006 增登结果为准，建议写成 `north-altar:stairs:ground:E/W/S/N`。
  - 端口 JSON 按 LY-006 `port.schema.json` 写：`world:null`、`nodeMatrixColumnMajor:null`、`elevationClass:"C-engineering"`，容差 0.005 m / 0.002 m。
- 可选：一块北郊局部 C 地坪片，见 §5 缺口 G2，最终由 LY-010 决定。
- 安装 / 撤回脚本与 QA。

**只交提案、不直接写**：`city-data.mjs` 的 researchModels 条目和项目卡字段，这两项归 LY-100。

## 4. 证据与未知（四类分栏）

| 事项 | 类别 | 依据 |
|---|---|---|
| 北郊为“方坛四陛” | 原始文献 | 《续汉书·祭祀志中》。维基文库《後漢書/卷98》页面原文为「北效在雒阳城北四里，为方坛四陛」（“效”应为“郊”的刊误）：https://zh.wikisource.org/wiki/%E5%BE%8C%E6%BC%A2%E6%9B%B8/%E5%8D%B798 。LY-002 E-R02 已逐字核对 |
| 位置：城北四里 / 六里 / 城西北角去城一里所 | 原始文献（三说并存，未定） | LY-002 evidence-ledger E-R02（S06、S06 注引张璠记〔晋〕、S10 注引汉官仪）。本项不选其中一说当定论 |
| 中外营、营门存在 | 原始文献（形制未知） | 「四陛醊及中外营门封神如南郊」（LY-002 S06；维基文库此处有乱码） |
| 只有祠舍类建筑 | 原始文献（有缺字） | 汉官仪「但有□祠舍而已」（LY-002 S10） |
| 坛边 20 m、坛高 1.2 m、陛宽 3.2 m、踏步 0.2/0.5 m、土色外观 | **C 工程设计** | 资产卡 notes；GLB extras `C_DIMENSIONAL_PLACEHOLDER` |
| 坛的朝向（四陛正对东西南北，与城市 -Z 北对齐） | C | 城市坐标 `rotationToTrueNorth=null`（LY-005 frame） |
| 坛址的世界坐标、地面高程 | **未知** | 无考古控制点；LY-004 未交付 |
| 围营、祠舍的数量、形态、位置 | **未知**（存在有文献依据） | 不建模，不画边界 |
| 南郊圆坛八陛、北魏、西汉长安材料 | 异地 / 异期类比，**不得使用** | 任务池证据规则 |

以下五件事各自独立：
- **模型能读取**：已证，有回读结果。
- **局部通行通过**：只做过几何台阶检查，没有做连续人体检查。
- **已入城**：否。
- **结构安全**：不声称。
- **历史复原成立**：否，尺寸是 C。

## 5. 实测数据与缺口

测量脚本：`prep/measure_altar.py`（numpy 独立 GLB 解析，SHA256 9f7652e5…1def6），结果在 `prep/measure_out.json`。Blender 交叉回读脚本：`prep/blender_readback.py`（SHA256 a2d66fa3…9acc），结果在 `prep/blender_out.json`，用 Blender 5.2.1 LTS 导入。

### 已经合格、可直接复用的部分（实测）

**几何与体积**
- 尺寸 26 × 1.2 × 26 m（glTF X/Y/Z）。坛心 20 × 20 m，四陛各外伸 3 m。原点在坛心、坛底，y=0 即接地面，符合 LY-005 local-origin 新件规则。
- 268 三角形，焊接后 1 个连通体，非流形边 0，Blender 边界边 0。
- 有向体积 506.88 m³，与解析值 20·20·1.2 + 4·3.2·0.5·(0.2+0.4+…+1.2) = 480 + 26.88 = 506.88 吻合。numpy 和 Blender 结果一致。
- 三档几何哈希相同：三档只换纹理，不是独立几何简化。

**四陛（numpy 逐侧实测）**

| 侧 | 宽 | 踏步 | 踢面 | 踏面深 | 2R+T | 脚下端口（本地 glTF） |
|---|---|---|---|---|---|---|
| 东 +X | 3.2 m | 6 级 | 6 × 0.200 m | 0.500 m | 0.90 m | (13, 0, 0) |
| 西 -X | 3.2 | 6 | 6 × 0.200 | 0.500 | 0.90 | (-13, 0, 0) |
| 南 +Z | 3.2 | 6 | 6 × 0.200 | 0.500 | 0.90 | (0, 0, 13) |
| 北 -Z | 3.2 | 6 | 6 × 0.200 | 0.500 | 0.90 | (0, 0, -13) |

各陛的最高一级（y=1.2，外伸 10.0–10.5）与坛面齐平；四陛都在边中，切向中心为 0。

**支承**
- 底面 y=0 的面积 438.40 m²，等于坛心 400 加四陛投影 4 × 3.2 × 3 = 38.4。每陛的支承比都是 1.000。
- y>0 处朝下的面积为 0 m²，即无悬空、无挑出。
- 坛体及踏步上方没有任何几何，所以模型内部没有净空限制。

### 真实缺口

**G1 ｜北郊没有任何已加载地面。**
- 城景四块原子地面实测，最北的向上三角形在 Z = -2402.361（network-ground-stitched），另外三块地面更靠南。
- 北城垣的世界包围盒在 Z -2648.5 至 -3953.8（wall-11、wall-00）。
- 所以北城垣以北的可支承地面是 **0 m²**。四个脚下端口无论放在北郊哪里，`cityTerrainYBelow` 都只能填 `null`。

**G2 ｜基底与城市地面有一级踏步的高差。**
- 本件底面 y = 0。城景已有地面顶面为 0.20 m（地块）或 0.21 m（道路），城垣底为 0.17 m（LY-005 实测表）。
- 如果直接按城市零点落在 0.20/0.21 的地面上，第一级 0.200 m 踢面会被整级埋掉，端口高差 -0.20 或 -0.21 m，超出 E3 规定的 2 mm 容差 100 倍。
- 解决办法只有两种：配一块 y=0 的北郊局部地坪；或者由 LY-010/005 决定把世界 N 的 Y 设为 0.20 或 0.21，并按 E4 规定把它作为新版本、重算端口。

**G3 ｜端口 schema 与“未定址”（已由 LY-006 解决）。**
- LY-005 的 `port-schema.json`（SHA256 30854ed9…332f）把 `world` 列为必填。
- LY-006 的 `schemas/port.schema.json`（9fcdf932…fdc）改成 `world` 可以是 pose 或 null。条件是该 local frame 在 `registry/zones.json` 中 `placement==null`。`local:north-altar` 正是这样：`placement:null`，状态写着“unplaced (north suburb, never grouped with south)”。
- 所以端口可以合法提交 `world:null`、`nodeMatrixColumnMajor:null`。`frames.world` 仍要写 `luoyang-local-schematic-v01`（schema 定为 const）。这只是框架名，不是坐标。

**G8 ｜端口粒度：登记了 1 个端口，本项需要 4 个（新发现）。**
- LY-006 `registry/ports.json`（28bcfb68…c612）只登记了 `north-altar:stairs:ground` 这一个 ground 端口，`local:null`。
- schema 里一个 pose 只能有一个 position。四陛的脚下分别在 (±13,0,0) 和 (0,0,±13)，相距 26 m，一个 pose 表达不了。
- 验收要求“四陛全部独立核支持”，四个端口必须分开。
- 需要 LY-006 增登 4 个端口，或者升版成 4 个：建议 `north-altar:stairs:ground:E/W/S/N`，这是 4 段，符合 portId 正则 `{1,3}` 个冒号。陛顶的 4 个 `floor` 端口是可选项。
- 本项是 steward，`consumers` 为空，所以升版不需要别人重新确认。但新 portId 写进登记表属于 LY-006 或协调者的权限，本席位不自行增登。

**G9 ｜写区与地坪片的限制（LY-006 冻结值）。**
- 写区 `LY-080:write:001` 在 local:north-altar 中的盒子是 [-17,-0.3,-17]–[17,0.3,17]，标签写着“不得改动坛体”。
- 地坪片如果从端口向外伸 1 m，到 ±14 m 为止，在写区内。地坪顶面必须 ≤ 0.3 m。
- 本项 `ownsGroundPieces` 为空：没有任何既有城市地坪片归本项。新地坪片只能作为组件 `T080-arrival` 交付。
- 地坪片如果铺在坛底投影下面，它的 y=0 顶面会和坛底 y=0 共面重叠，形成 400 m² 共面面，有 z-fighting 风险。办法是在坛底投影内开孔，或只铺四个端口外的条带。由 LY-010 决定。

**G4 ｜位置三说，城市坐标无法换算。**
- 城市坐标是示意工程米，`geographicOrigin=null`、`rotationToTrueNorth=null`。模型里的北城垣本身也是斜线：wall-11 从 (-44.8, -2648.5) 斜到 (718.7, -3596.0)。
- “四里 / 六里 / 西北角一里所”无法换算成城市坐标，本项不做换算。

**G5 ｜LY-004 已交付，结论是北郊未配准。**
- 三说互斥，都不出点。各说的包络范围都只是 C 平移量得出的文本距离带，`notAHistoricalBoundary:true`、`admittedTo180InstallLayer:false`。
- 包络覆盖的距离：A 带距北垣 1449–1944 m，B 带 2277–2808 m，C 扇区以西北角为心、半径 207–648 m。
- 结论：本项只能交局部包，`world` 保持 null，不能入城。LY-004 `qa/separation.json`（b766823d…2443）测得南北要素最近相距 4738.9 m，本项不得改变这个分离。
- LY-004 另外记了一条出入 R-02：研究层没有北郊条目。补条目的提案交 LY-100，本项不写。

**G6（继承披露，不在本项修；LY-007 已出规则）**
- LOD1、LOD2 的几何哈希与 LOD0 相同，只降纹理：512 / 256 / 64 px。
- 按 LY-007 `baseline/lod-rules.json`（fbf53757…9b）的 copy_ban，几何哈希、贴图分辨率、材质名三项都相同才算“LOD0 复制”。本件贴图分辨率不同，所以**不算复制**；`qa/near-retention.json` 中 lod1/2_equals_lod0 也都是 false。
- 但三角形比是 1.0，超出 LY-007 新件验收区间：LOD1/LOD0 0.17–0.62，LOD2/LOD0 0.05–0.20。LY-007 自己的注释是“夯土不降档”，本件全是 earth，所以可以按“纹理档”如实标注，不能写成几何降档。
- 交互、通行、接触一律在 LOD0 上测。
- LY-007 普查（census-bce3211.csv 204–206 行）对本件三档记的继承标记：`material_names`、`suffix_vs_tier`、`legacy_grey_texture`（LOD0、LOD1）、`texture_not_in_library`（LOD1、LOD2）、`uv_not_1m_box`。旧灰调色板对新模型禁用，对复用件只做披露。
- 材质 doubleSided=true。
- UV 统一按 0.25 cycle²/m² 重复平铺，不是唯一烘焙。
- LY-009 `board/locks.json`（5eb5ae32…cc9d）把 `docs/library/models/m-luoyang-northern-altar/**` 列在 LOCK-PROTOTYPES 下，持有者为“既有成果（本轮只读）”。这和本项“只引用，不改字节”一致。

**G7 ｜通行只核到几何台阶。**
- 2R+T = 0.90 m，比常用的 0.60–0.64 m 舒适值大，属于 C 设计，只记录，不改。
- 坛边落差 1.2 m，没有栏杆，也没有台阶侧挡。
- 没有做连续人体包络、上下坡负例或浏览器/GPU 测试。

## 6. 私密源与重建

- 缺 `config/altar.json`（GLB extras 里的 sourceConfig），以及生成器或 .blend 原生源。资产卡称“实际 GLB 与原生有向几何一致”，可见原生源存在，但不在仓库里。
- 本项复用时不改几何，所以不需要原生源。
- 如果后续要改几何，可以完全**从 GLB 重建**：几何全为轴对齐，所有参数（20 m / 1.2 m / 3.2 m / 0.2 m / 0.5 m / 6 级）已实测。但重建件必须标“从 GLB 重建”，不能冒称原件。
