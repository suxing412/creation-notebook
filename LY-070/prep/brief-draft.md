# LY-070 宫院复道局部整合包 · 开工准备简报（草稿）

状态：**开工准备（prep）**。初稿 2026-11-05 21:39；**23:5x 复核更新**（见第 9 节）：G 中 LY-001/002/005/006/007/009 已交付，**LY-008（无 status.json，仍在写）与 LY-010（目录不存在）未冻结**；LY-003 已交付，结论为宫区与两宫复道「不可落位」；LY-061…069 全部只有 prep。本目录只有读取、实测和测试准备，**没有制作或修改任何交付几何**。

- 基线：`D:/GitHub/creation-notebook-lab` main `bce3211f818ee5a8bef1773539da70695ba37b17`（只读；未运行 git 写操作、未运行 build_assets.py）。
- 写入范围：仅 `D:/GitHub/creation-notebook-workpacks/LY-070/prep/`。
- 工具：Blender 5.2.1 LTS（`D:/Blender/blender.exe -b --factory-startup --python-exit-code 1`），Python `-I`。

## 1. 本项目标（按任务池原文）

把已经存在的宫院件和复道件（复道 A/B、A 服务登临节点、候入院及其补件、对阙、殿堂、玉堂组）组装成**一个**有边界的 C 空间实验组，附带可回退的安装表。只有 LY-003 给出准入后，才提供城市矩阵。

验收的核心是两条否定式：
1. 所有选中件都符合地域准入，**不出现多套宫殿叠加**；
2. LY-003 未通过时，只输出「仅局部组装」这一明确状态，不能写成「完成宫区」。

本席位属于**复用装配**：不新建宫殿家族，不新造前殿、后殿或复道。

## 2. 现有成果（已核对，SHA256 为提交字节）

| 组件 | 文件（`docs/library/models/…`） | SHA256（前 16 位） | 城景加载 |
|---|---|---|---|
| 复道 A LOD0/1/2 | m-luoyang-palace-gallery/files/gallery-A-LOD0/1/2.glb | 0c09279723e2334c / 227c3c4ecc262562 / cb26b56e1634f27a | 否 |
| 复道 B LOD0/1/2 | …/gallery-B-LOD0/1/2.glb | c7cb279cfd110315 / fe72e192573df077 / ff15e1c4ca8cb4f9 | 否 |
| A 服务登临节点 LOD0/1/2 + 碰撞候选 | m-luoyang-gallery-access/files/access-A-*.glb | c973d325d1d08cfd / 7b5e26f443a1e1bc / b39c34c28ab38963 / 7327547eee27c4c0 | 否 |
| 候入院组合 open LOD0/1/2 | m-luoyang-palace-admission-court/files/palace-admission-court-open-LOD*.glb | 59c8b758a5a25231 / d95bd22f9317683e / 01b2017fac9d8ee6 | 否（progress-assets 下为逐字节重复副本，也无入口加载） |
| 候入院组合 closed LOD0/1/2 | …/palace-admission-court-closed-LOD*.glb | 6ea892982b46e554 / 455a12153d4132d2 / 108e28a567dcef23 | 否 |
| 德阳类殿堂 A LOD0/1/2 | m-luoyang-deyang-hall/files/deyang-A-*.glb | 7736998077a8414f / 6f605ed7d79a0914 / 134b0375590b7440 | 否 |
| 德阳类殿堂 B LOD0/1/2 | …/deyang-B-*.glb | 6ef34781443e13cd / d9a73c76db5fd7eb / 1fd999980d904342 | 否 |
| 玉堂前后殿 A LOD0/1/2 | m-luoyang-yutang-halls/files/yutang-A-*.glb | 6e7f06c054d07984 / 297c11b01604122c / 6ff5440cc0be5563 | 否 |
| 玉堂前后殿 B LOD0/1/2 | …/yutang-B-*.glb | 92091dbe9c51e72b / 1566de0280fbe50d / 965ab0b851398f1f | 否 |
| 对阙 Q LOD0/1/2 | m-luoyang-palace-paired-que/files/palaceque-Q-*.glb | a022d9870594f986 / 09839d70748ea5c5 / 9b75671b3d12f393 | 否 |
| 侧廊庑 A LOD0/1/2 | m-luoyang-palace-sidehall/files/sidehall-A-*.glb | bd000b1bf36419ee / 547935049e53cee8 / b4c64f499c9c7066 | 否 |
| 值守切片（12 个 GLB，例如 closed-LOD0） | m-luoyang-palace-guard/files/*.glb | 48c511c54010cc00 等，全表见 inputs.json | 否 |

完整 72 项（含卡片、source.json、QA json、城市入口文件）的路径、字节数、工作树/提交字节两套 SHA，以及加载扫描结果，都在 `inputs.json`。

**加载结论**：在 bce3211 中，`docs/cities/luoyang/*.mjs|*.html`、`v1/*`、`data/**/*.json` 对上表全部 GLB 的引用都是 0 处。它们只会被资产库详情页 `docs/model-library/inspect.mjs` 按卡片 `files[]` 动态读取，不属于城景。项目卡 `p-luoyang.asset.json` 把它们登记为「已建模 · 未入城」。城市里与复道有关的只有证据标记 `palaces_connector_B`（`data/evidence/evidence-geometry.json`，`representation: evidence-marker-only`，`architectural_completion: not_modeled`）。另外 `road-preconstraints.json` 明文写着「不能造高架桥、桥墩、坡道」，用于公共路网层。

文本文件有 CRLF 问题：21 个文本输入的工作树 SHA 与提交字节 SHA 不同（与 LY-001 C8 一致），QA 一律绑定 `sha256_committed`。

## 3. 改 / 不改范围（草案，以 LY-006/LY-010 冻结为准）

**本包会做（制作阶段）**
- 一份 `assembly.json`：选中件 → 输出节点映射，每件一个刚体变换（只绕 Y 旋转，缩放 1，遵循 LY-005 契约），列出端口 ID/版本、保留/替换/隐藏/删除清单、互斥组。
- 一份可回退安装表：安装和撤回各做一次严格回放，原节点、矩阵、几何和材质的哈希不变。
- 两档状态输出：`localOnly`（LY-003 未通过时的唯一合法状态，`cityPlacement=null`）和 `cityCandidate`（只在 LY-003 与 LY-010 同时放行后才写城市矩阵）。

**本包不做**
- 不新造或修改任何原件（复道、登临节点、殿、廊、阙、门卫）。修订件只引用 LY-061…069 的交付物。
- 不写 `city-data.mjs`、项目卡、`lab/data/*`；城市接入只交 LY-100 合并提案。
- 不铺「七里」连续复道，不把三条通行带称作三层，不给任何件起实名殿名或宫门名。
- 不叠加多套殿堂：候入院里已经内嵌 `hall__deyang-A-*`，德阳 A/B 与玉堂 A/B 都是互斥选择。

## 4. 证据与未知（四类分栏）

| 类别 | 内容 | 出处 |
|---|---|---|
| 原始原文（东汉末，同城） | 南北宫间有复道，中央作大屋，「三道行」，天子行中道；五营校尉行复道中 | 《后汉书·光武帝纪上》李贤注引蔡质《汉典职仪》；本轮在 zh.wikisource 检索摘要中看到「南宮至北宮，中央作大屋，複道，三道行」（https://zh.wikisource.org/wiki/後漢書/卷1上）；LY-002 证据表 E-P02（S09、S03） |
| 原始原文，**不可用作数字** | 「两宫相去七里」与城市规模冲突 | LY-002 禁用表 X16 |
| 异地异期类比 | 无。北魏阊阖门/太极殿中轴（X04）、魏晋东掖门（X05）、185 年以后的残毁状态（X19）均禁用 | LY-002 |
| C 工程设计 | 复道 A/B 全部尺寸（楼板 z=4.0/3.5、柱网、三带宽 1.9/2.1 m、柱础 0.5 m）；登临节点梯级 0.2/0.32 m；候入院布局；本包的所有相对变换 | 资产卡 notes：「所有尺寸与走线为C推测」 |
| 未知 | 复道是否高架、结构形式；复道与任何宫门或殿的接法；两宫位置与配准（取决于 LY-003）；180 年时宫院内是否有这种局部复道 | E-P01、E-P02、E-P06 |

五件事分开记：
- 「模型能读取」：已实测，全部 GLB 都能读取。
- 「局部通行通过」：只在后文的有限射线与剖线意义上成立。
- 「已入城」：**否**。
- 「真实结构安全」：**未做，也不做**。
- 「历史复原成立」：**否，属于 C 试案**。

## 5. 实测缺口（带数字，均可重跑）

所有测量都在 Blender 世界坐标下进行：Z 向上，单位米，导入时 glTF +Y→Z、glTF +Z→−Y。脚本放在 `prep/scripts/`，结果放在 `prep/out/`。

### G1 复道 A 与 B 层高不一致，登临节点只配 A
- `measure_gallery.py` → `out/gallery-measure.json`：A 楼板顶 z=4.000，面积 79.2 m²（x ±6.0，y ±3.3）；B 楼板顶 z=3.500，面积 64.8 m²（x ±4.5，y ±3.6）。三档一致。
- access-A 台面 z=4.000，面积 21.628 m²（LOD2 为 22.268 m²，因梯级合并）。
- `compose_probe.py` s2（B 末端 x=4.5 接 access-A）：接缝高差 **0.500 m**，timber 面交 64 对。所以 B 必须用 LY-068 的独立件，不能套 A 节点。

### G2 复道 A 有 16 个柱础，GLB 内没有地面
- `measure_feet.py` → `out/feet.json`：A 的触地件全部是 `gallery-A-static_earth` 的柱础，底面 z=0.000，共 16 块，每块 0.5×0.5 m，合计底面积 4.000 m²。柱础位于 x∈{±2,±6}、y∈{±1.1,±3.3}，柱子坐在 z=0.2 的础顶。B 有 12 块，合计 3.0 m²。
- 柱础下方 GLB 内没有任何支承（体检射线返回 None），所以必须由外部地坪托住。这正对应任务池所说「A 局部片段 16 个旧未命中地表支点」。逐脚对账由 LY-067 负责，本包只消费其结论。
- 旧的城市候选位置、地形版本和那份未命中记录都不在仓库里（见 inputsMissing）。

### G3 A 与 access-A 的对接变换没有公开，候选变换会产生小正体积侵入（23:5x 已逐件复核，见第 9.3 节）
- 假定 access-A 平移 +6.0 m（台面起点贴 A 楼板末端 x=6.0），s1 实测如下：
  - 三条剖线（y=−2.2/0/2.2）从 A 楼板到 access 台面高差都是 **0.000**，无断点。
  - timber 面交 38 对，`overlap_detail.py` 显示全部是 x=6.0 处的端面共面接触，或 z=4.0 处的贴合接触。0.02 m 网格的体内采样没有找到共享点。但 timber 网格不一定闭合，这一条只能记为「未发现正体积」，不能写成「无穿插」。
  - earth 柱础有正体积侵入：A 端础 x 5.75…6.25 与 access 础 x 6.225…6.875 重叠 0.025 m，y 方向重叠 0.275 m，高 0.2 m，两侧各 0.001375 m³，合计 **0.00275 m³**（两件都是闭合方块，AABB 交即实体交；0.02 m 网格估得 0.002 m³）。
- 真实对接变换应由 LY-067/LY-069 冻结。若沿用 +6.0，两块柱础的重叠必须声明为合法共础，或者改用单础方案。

### G4 三条通行带在登临节点处只剩中道
- A 楼板上三带宽都是 1.900 m（y −3.15…−1.25 / −0.95…0.95 / 1.25…3.15），在 0.3/1.0/1.8 m 三个高度都贯通；B 三带宽都是 2.100 m。
- 接上 access-A（s1）后，两条侧带 y=±2.2 在 0.3 m 和 1.0 m 高度于 x≈9.04 被 access 栏杆挡住。只有中带 y=0 一直通到梯口，梯宽 2.0 m（y ±1.0）。
- 结论：「三道行」到地面只剩一条下行路线。侧带属于尽端，这一点需要声明，不能写成三带都可下地。

### G5 登临节点梯脚和梯帮压进地坪 0.2 m
- access-A 两块梯脚 earth 块（各 1.0×0.65 m，z −0.2…0.0）和 4 根 timber 帮脚（z≥−0.1302）低于 z=0。若坐在候入院平板上（`new_court_support_C`，z −0.2…0），会与平板产生正体积重叠（s3：72 个顶点低于地面）。
- 处理办法二选一：地坪切孔（归属需 LY-006 判定），或者把它归为合法埋入并在 QA 声明。梯口 y=0 处 x≥15.58（s1 世界坐标）不在梯脚块上，需要外部地面 z=0 承接首级（首级顶 0.2，踏步 0.2/0.32 m，共 20 级）。

### G6 候入院没有复道端口，开阔庭地只能放局部
- 候入院 `route-interfaces.json` 的端口只覆盖门卫→庭→殿阶，`source.json` 中 `cityPlacement: null`，没有复道或高处端口。
- 开阔庭地约 x −18.1…18.1（侧廊台内缘）、y −51.0…−16.58（门卫北缘到殿台南缘），合 **36.2 m × 34.4 m**。A+access 的平面长度为 22.37 m（−6.45…15.92）、宽 7.65 m，物理上放得下。
- 但主路线沿 x≈0 南北贯通。复道若横跨主路线，柱础内缘 ±1.75 m 只留 3.5 m 净宽，净高低于 4.0 m（梁顶 3.8–3.9 m，梁底待测）。放不放、放在哪由 LY-069 和 LY-010 决定，本包不自选。

### G7 多套殿堂叠加的实测负例
- 候入院 GLB 已含 `hall__deyang-A-static_{earth,timber,tile}`，局部 bbox 与独立 deyang-A-LOD0 完全一致。
- s4/s5：再放一份 deyang-B，与内嵌 deyang-A 的共享体积约 **1545 m³**（0.1 m 网格），面交 earth 307 对、timber 1244 对。再放一份 deyang-A，面交 9988 对（tile）等。
- deyang-B 与侧廊 earth 只在 bbox 上重叠（x 18.1…20.3，y −17…−13），体内共享点为 0，几何上没有相交。
- 所以若 LY-065 选 B，必须**替换**内嵌的 A，不能追加。这一组数据可直接作为「无多套宫殿叠加」的负例基准。

### G8 复道两端是开放的高处落差
- A 的两端在 x=±6.0 处是楼板高 4.0 m 的开口（资产卡也写明「端口在高起楼板高度」）。接上 access 之后，另一端（x=−6.0）在 LY-069 交付前仍是 4.0 m 落差，局部包必须列为「未接端」。

## 6. 依赖现状（2026-11-05 读取）

- 已交付：LY-001、LY-002、LY-005。
- 尚无目录：LY-003、LY-006、LY-007、LY-008、LY-009、LY-010。
- 只有 prep：LY-061…065。
- 有目录但没有状态文件：LY-066…069。

各项依赖的状态文件 SHA 见 `inputs.json` 的 `upstream_workpacks`。

## 7. 测量脚本与结果（SHA256）

| 文件 | SHA256 |
|---|---|
| scripts/glb_nodes.py | b3fcc82f5f134a843cd44cf19c2392f8c04f9ab0f9edb9fca1e52074ad14fa11 |
| scripts/measure_gallery.py | 4b84943e58222d86cd3778b55580a6867146823ae8d69b9b284107d150e6288c |
| scripts/measure_feet.py | 27b8fe77487d70cc9fd595a8a1637114707e7e32412769dd3752f0cf79f4912d |
| scripts/compose_probe.py | fc7c3e787896e8f2c0236bd1d3a62da094a9b465d4d0819dc35f7d63cb630f93 |
| scripts/containment_probe.py | 76383f45ca9267d18caf889c871aea5756c360ae6e1fc4f3be0dd3d0f719d7d8 |
| scripts/overlap_detail.py | ac9a538e2e9daf1e347432100306cdab13273a2592fc7915bcbd2de912bc7d46 |
| scripts/build_inputs.py | f7d9ec964f8acf7be2d6e3f86ace741a680229aefcc838a0c029491c232dba2d |
| out/gallery-measure.json | 7754f659e7984563c05846f03f19a82fae63e36b24d4afcb76ab7bf08e3d21e8 |
| out/feet.json | a473aafa2f2d1d9ec4e5684c4768379d70d07899bafa7ad52176458a74e2c252 |
| out/compose-s1-galA-accA.json | 2629a25f9596d0566d98f469b6c3798e0ba0319105794af8152d5e4fde80873a |
| out/compose-s2-galB-accA.json | e44253c6bc50d9116641609e2f6ef81731bc9618dc4339306768d1d47a2d0aca |
| out/compose-s3-court-galA-accA-probe.json | 869d556f161f0d49e92f75b484700fa6d22ec32e3d827337b45e9df74b295983 |
| out/compose-s4-court-hall-swap.json | 13e787f8180f744ec08db76e482b81e1b74b0907b48fe619daaecff9c7a57910 |
| out/containment-s5.json | fcd0b320c495c1cb6f88edadd98896dbfc1f3edf226999c168d11761d326f879 |
| out/containment-s6-fine.json | a6b1e2e8d39aafd3386b96b9356b72cf989ba88c663261f085043323f33e9a5c |
| out/overlap-galA-accA-x6.json | 2605f02fdfb36af35ac307ea8ca4b4ff2900331240fce636cea5b079e82c279f |

所有 s3 摆放都只是**测量用探针**，不是选址。`out/spec-*.json` 里含本机绝对路径，只供 prep 复跑，不能进入任何公共交付。

## 8. 复用判定

**不能判为复用完成**。bce3211 中没有任何把复道与宫院件组合起来的装配包：
- 候入院没有复道端口；
- A 与 access-A 的对接变换没有公开；
- 两件都是「独立研究模型 · 未入城」。

本席位产出的是新的装配表和 QA，不是新几何，所以按「复用装配」交付，所有构件都引用原件。

## 9. 23:5x 复核更新（上游已交付部分）

用 `scripts/refresh_upstream.py`（SHA256 `60e43a68036ef27e32b2b74303eb24f1e43717429c920744afec4715866f620b`）重算了 `inputs.json`：72 个 lab 输入的提交字节 SHA **无一变化**，lab HEAD 仍是 `bce3211`。唯一漂移是 `lab/data/assets.json` 的工作树字节（`3440caa2…` → `c39e8e9a…`），提交字节 `53d86312…` 没变。新增 `upstream_workpacks`（每席位状态文件 SHA）和 `upstream_contracts`（本席位要消费的 18 个契约文件 SHA）。

### 9.1 LY-003 已交付：本轮只能是 localOnly

- `LY-003/status.json`（`46f2872d0013340a…`）状态为「交付完成」。`tables/admission.json`（`dd0ab8c018e714be…`）中：
  - 北宫：不可落位，「仅独立研究视图或局部包（无城市矩阵）；LY-070只交局部组装」；
  - 南宫：不可落位；
  - 两宫复道 `palaces_connector_B`：不可落位，「仅关系示意；复道模块只作局部C」。
- 原因：项目坐标与任何测绘或发掘坐标之间的共同控制点为 0，平移、刚体、相似、仿射变换全部欠定。
- 所以本轮 T2.2（`cityCandidate`）不可能触发。制作时必须走 T2.1：`status: "localOnly"`、`cityPlacement: null`、不得出现 `cityMatrix`。LY-003 的解除条件是取得至少 2 个双方都有数值坐标的共同点，本轮一个也没有。

### 9.2 LY-006 已交付：本席位的所有权与端口

`registry/seats.json`（`a1426412c84cab87…`）里 LY-070 的条目：

- `siteOwner` 为 S-PALACE 场地的负责人（061–070 共 10 席）。场地 `envelope: null`，所以组的 bounds 要由本席位提出，并经 `check_registry` 通过。
- **`writeZones: []`、`cutZones: []`、`components: []`、`produces: []`。** 本席位在任何坐标里都没有写入区，因此不能补盖缝板、地坪、切孔或任何几何。所有接缝处置（含 G3 的 0.00275 m³ 柱础重叠）只能由所有权方（LY-069 / LY-067）交付，本包只做引用和判定。
- `ownsCards`：8 张卡（deyang-hall、gallery-access、palace-admission-court、palace-gallery、palace-guard、palace-paired-que、palace-sidehall、yutang-halls）的「提案所有权」。卡片改动只能写成给 LY-100 的提案。
- `consumes` 5 个端口：`gallery-end:junction:floor`（LY-069）、`paired-que:forecourt-edge:ground`（LY-064）、`deyang:maintenance-edge:floor`（LY-065）、`yutang:outer-port:ground`（LY-066）、`admission-court:side-opening-E:opening`（LY-062）。
  - `ports.json`（`28bcfb68cd7d7fe0…`）中这 5 个端口的 `local`/`world` 全部为 null（「values filled by producer at delivery」），容差为 **position 0.005 m、elevation 0.002 m**。
  - `seams.json` 有 5 条对应的 `…->LY-070` 接缝。
- 本席位**不直接消费** `gallery-A:feet:ground`、`gallery-B:landing:floor`、`sidehall:ends:floor`、`admission-court:side-opening-W:opening`。这些由 LY-069 消费，LY-061 的 `admission-court:enclosure:wall-end` 由 LY-062/063 消费。所以 LY-061、LY-063、LY-067、LY-068 的成果只能经 LY-069 的组合件，或作为整件引用进入本包。
- 帧：`local:palace-composite` 写着「composed frame defined by LY-069/LY-070; unplaced」。`local:admission-court`、`local:deyang`、`local:yutang`、`local:paired-que`、`local:gallery-A/B` 的 `placement` 都是 null。**各局部帧之间没有任何已登记的相对变换**，本包的 `assembly.json` 要第一次给出这些相对变换（C 设计）。
- LY-069 的写入区是 `local:palace-composite` 原点处 12×9.3×12 m 的盒子（x,z ±6，y −0.3…9.0）。

### 9.3 A↔access-A 接缝逐件复核（更正 LY-069 prep 的木构数字）

LY-069 prep（`LY-069/prep/out/seam-portal-lod0.json`）在 dx=6.0 时报告「木构约 0.00114 m³、土构约 0.00235 m³」。本次用焊点后的松散件和逐面列表复核：

- 脚本：`scripts/seam_parts.py`（`53ea46a1…`）→ `out/seam-parts-dx6.0.json`（`b5cdbeb4…`）、`-dx6.0675.json`（`a8c54cc3…`）、`-dx6.17.json`（`ffd7b23f…`）；`scripts/seam_faces.py`（`fa192c61…`）→ `out/seam-faces-accA-dx6.0.json`（`e74db094…`）、`out/seam-faces-galA-end.json`（`ada7f9e9…`）。
- **土构**：两对闭合方块（A 端柱础 × access 台础），各 0.001375 m³，合计 **0.00275 m³**，是精确值。LY-069 的网格值 0.00235 偏低约 15%。
- **木构**：逐面看，dx=6.0 时**没有实体交**。
  - A 端梁 x 5.83…6.17、z 3.6…3.9；access 平台的唇板 x 6.0…6.18、z 3.92…4.0，与梁顶之间有 **0.02 m 竖缝**；access 主板从 x 6.18 起，与梁端之间有 **0.01 m 水平缝**。
  - A 楼板止于 x 6.0，与唇板端面共面（z 3.92…4.0 段）。A 端上柱的底面 z=4.0 落在唇板顶 z=4.0 上，是共面接触。
  - 松散件 AABB 法给出 0.02244 m³，是假阳性：access 的唇板与主板焊成一个 L 形非闭合件，AABB 把空隙也算进去了。LY-069 的 0.00114 m³ 很可能来自 z=4.0 共面层上的网格点奇偶误判。
- 结论：dx=6.0 时只需白名单 2 处土构正体积（各 0.001375 m³，位于 x 6.225…6.25、y ±(3.05…3.325)、z 0…0.2），木构按「共面接触 + 0.01/0.02 m 缝」分类。唇板 z 3.92…4.0 下方 0.02 m 无支承：它是平台的悬挑，不是放在复道梁上。**这一条要求 LY-069 交付时采用同一分类，两家数字不一致时由 LY-008/LY-094 裁定，本席位不自行取舍。**

### 9.4 依赖现状（23:5x）

| 席位 | 状态 | 状态文件 SHA（前 16 位） |
|---|---|---|
| LY-001 / 002 / 005 | 交付完成 | a32d742a0064baf4 / 0ac63db873219d1b / add0f9b1a722f08e |
| LY-003 | 交付完成（宫区不可落位） | 46f2872d0013340a |
| LY-006 / 007 / 009 | 交付完成 | fe4aaa6c7cb1441f / 2fddce70c110a19c / 09a1c45415aa3a86 |
| LY-008 | 未冻结（目录在写，无 status.json） | — |
| LY-010 | 未开始（目录不存在） | — |
| LY-061…069 | 只有 prep | 061 add7fb6e / 062 e795f15d / 063 2c1450f8 / 064 028cc3ae / 065 c0bd142d / 066 bbc6606a / 067 99035d00 / 068 3652f25d / 069 bbf706db |

LY-009 的 `board/taskboard.v2.json`（`bd2fcbbe…`）把 LY-070 记为「待输入」（S4：未完成依赖 LY-008、LY-010、LY-061…069）。LY-065 的 prep 写着 `readyAfterG: false`，所以 LY-070 的最长链至少是 G → LY-065 → LY-070，以及 G → LY-061 → LY-062/063 → LY-069 → LY-070。

另外，lab 本地 `main` 分支指向 `44c66da`，`bce3211` 不是它的祖先；`origin/main` 为 `cad338b`。当前检出在 `lab/site-redesign @ bce3211`。T0.5 取基线时必须按协调者冻结的 SHA，不要按本地 `main` 分支名。
