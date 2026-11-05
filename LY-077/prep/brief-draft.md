# LY-077 太学A门外到达接口：开工准备草稿

阶段：**开工准备**。G（LY-001/002/005/006/007/008/009/010）还没冻结，本席位没有制作、导出或修改任何交付几何。本目录只放读入记录、实测、测量脚本和验收脚手架。`check_arrival.py` 里的 `synthetic:*` 地块只在内存里生成，用来证明检查器能分清通过和失败，不导出、不交付。

基线：`D:/GitHub/creation-notebook-lab` main `bce3211f818ee5a8bef1773539da70695ba37b17`，只读；`git status` 前后一致（三个 lab/data 文件原本就有未提交改动，不是本席位造成的）。复核轮（同日第二次）：HEAD 仍为 `bce3211`，`git status --short` 只剩未跟踪的 `.claude/`（不是本席位产生的）；五个仓库内 A/B/v1 文件 SHA 重算一致；`check_arrival.py` 在 LOD1 上重跑 `none` / `synthetic:ok` / `synthetic:gap`，去掉标签字段后与 `qa/selftest/` 原报告逐字段相同（输出在 `qa/recheck-2/`）。任务池 `TASKPOOL.md` SHA256 `00c2e171…6c7`，第 799 行。

## 1. 本项目标（按任务池原文）

- 复用现有的太学长堂 A v3.2 入口修订版。**不重新造太学**，A/B 不混用。
- 补三件东西：A 的门外地面端口、阶前支撑、三个入口之间的局部侧向汇流关系。
- 门外观经空间（`m-luoyang-stoneclassic-access-court`）的年代和归属都没确证。没经过选择，不能把它和 A 自动焊成一个院子。
- 验收标准：从院外端口到 A 每个既有入口，支撑和体积检查都要完整；原 A 入口修订不变；B 模型不混入；外接关系只是 C 的，要明说。

## 2. 核到的现有成果

| 成果 | 路径（lab 仓库内） | SHA256 | 字节 | 城景是否加载 |
|---|---|---|---|---|
| A v3.2 中档 LOD1 | `docs/cities/luoyang/progress-assets/taixue-A-v3.2/models/taixue-A-LOD1.glb` | `413c2f35ec264dfbc6f24c1ceab9a0f8ce492c975b50e34fd5320ad25be391f2` | 638,660 | 间接加载：城景加载的是它的无纹理投影 ↓ |
| A 城景实际加载件（flat 投影） | `docs/cities/luoyang/progress-assets/flat/study-taixue-A-ee4163421d16.glb` | `ee4163421d1652b9301b8d50c7fe9f04ed09440000683b9a207ddf3f1600dda3` | 248,276 | **是**，在「礼制研究」章的独立视图里，`cityPlacement=null` |
| A v3.2 远档 LOD2 | `docs/library/models/m-luoyang-taixue-a/files/taixue-A-LOD2.glb` | `b911beb4c21aa7cc56d8e7d69660e23ac56dcad357635e008a3f300046e03860` | 118,848 | 否（只在资产卡里） |
| A v3.2 近档 LOD0 | 公开源包 `modeling-lab/review-batches/2026-11-04-taixue-A-v3.2/public-source.zip.part001-003` 中的 `models/taixue-A-LOD0.glb` | `ed40ae07e41060726781185d709017f43ac95bd2c6eac58f003582109c0a87f6` | 27,855,752 | 否（超过 15 MB 单文件门槛） |
| A 原生 .blend（三档） | 同一个公开源包 `models/taixue-A-LOD{0,1,2}.blend` | `af30bc12…f8722` / `0e1fe2ba…69296` / `3cd8b6e4…6ae7` | — | 否 |
| A v3.2 入口检查器 | 公开源包 `source/check-entry.py` | `d8c83c3a47fde5dd59dde2d6786f8e68dd810fd17c78f99bc86be5f7b6d5f8a6` | — | — |
| 来源合同 | `docs/cities/luoyang/progress-assets/taixue-A-v3.2/source.json` | 提交 blob `535e10ae…3083`；CRLF 检出 `5f2a8078…d76d`（city-data 声明的是后者，即 LY-001 的 C8 问题） | 2,566 | 是，provenance 引用 |
| 旧 v1 A 展示件（已被替换） | `docs/cities/luoyang/progress-assets/taixue-long-hall-v1/display/hall-A-LOD1.gltf` | `1403135d7a082f511fc5696d4fc10e5b19234b21e1086d566ecb33d7cdbddba7` | 111,804 | 否（被 v3.2 替代），仍在提交里 |
| B 方案（负例，不得混入） | `docs/cities/luoyang/progress-assets/flat/study-taixue-B-11b01e4948be.glb`，源 `taixue-long-hall-v1/display/hall-B-LOD1.gltf` | `11b01e49…0c57` / `fa828ef0…f089` | 373,040 | 是，同章的独立视图 |
| 门外观经空间 | `docs/library/models/m-luoyang-stoneclassic-access-court/files/stoneclassic_access_{near,middle,far}.glb` | `0fcb76be…49d5` / `5a0ff55f…e9f` / `1b45de37…e9f` | 8,977,644 / 1,934,304 / 178,124 | 否（只有资产卡） |

公开源包：三段拼接后的 ZIP SHA256 是 `83556f30e8e88c56f8578b84afba00fe81d4c611cadb23acd30d7e3cbf4e671d`，与 `intake.json` 一致；26 个成员的 SHA 也全部符合 `manifest.json`。还原时没有运行仓库里的 `restore.py`（它会写进仓库目录），而是在 `prep/_src/` 下自己拼接、自己校验。

**入口修订原检查已复跑。** 我把 `source/check-entry.py` 复制到 `prep/_src/rerun/` 后用 Blender 5.2.1 运行，三档 × 三入口的结果是：侵入 0、踏步支承失败 0/27、平台路线支承失败 0（168/168/117）。用 `sort_keys` 归一化 JSON 后，结果与原报告完全相同；原始字节不同，是因为写出的换行符不同。

## 3. 实测到的真实缺口

测量脚本是 `prep/measure_taixue_a_entry.py`（SHA256 `172e10d6…a599`），输出在 `prep/qa/measure-{LOD0,LOD1,LOD2,cityflat,old-v1-hallA,B-flat}.json`。坐标用 A 的局部 glTF 轴：X 向东、Y 向上、Z 向南，单位米。

1. **A 入口的形制（三档相同）。** 入口只有南面三处，中心分别在 x = −10.5 / 1.5 / 10.5，每处宽 2.2 m（−11.6…−9.4、0.4…2.6、9.4…11.6）。每处三级踢面，每级 0.20 m：地面 0.00 → 0.20 → 0.40 → 平台 0.60。踏面深 0.35 m，台阶伸出段在 z = 3.8…4.85。第一级踢面的水平射线在 y = 0.02 / 0.10 / 0.19 三个高度都打在 z = 4.85，说明踢面直落到 y = 0。台基北、东、西三面都是 0.6 m 的直立边，没有入口。
2. **门外完全没有地面。** 独立 GLB 已经去掉旧展示用的 46 × 18 m 支撑地面，四个边带的竖向探针全部 0 命中：
   - 南侧 4 m 带（x ±23，z 4.9…8.85）：0 / 18,440；
   - 两入口之间的凹口（z 3.85…4.8）：0 / 560；
   - 北侧：0 / 18,440；西端：0 / 3,612；东端：0 / 3,612。

   第一级踢面底下（y = 0）也没有任何可以站立的面。`check_arrival.py --patch none` 的结果是：三个阶前垫支承 264/264 全部失败，三条汇流路线 462 / 99 / 372 全部失败。
3. **侧向汇流只能落在地面上。** 三个入口之间是 0.6 m 的直立台基边：x 在 −9.4…0.4 之间宽 9.8 m，在 2.6…9.4 之间宽 6.8 m；两端各剩 7.2 m 到山墙。所以三入口的侧向汇流只能在 z ≥ 4.85 的地面上完成，平台前沿走不通（平台本身在 z = 3.6 这一条上从 x −18.5 到 18.5 连续高 0.60）。
4. **三个入口相对长堂中线不对称。** 中间入口在 x = 1.5，不在长堂中线 x = 0 上。所以单一院外端口放在 x = 0（长堂中线）还是 x = 1.5（中入口轴），属于 C 设计选择，要由 LY-006 冻结，不能悄悄定。
5. **净空。** 台阶上方和门外是露天的：瓦面最低点 y = 4.1，范围只到 z ±3.65。在平台前缘 z = 3.6 处量到的上方净空是 3.525 m。阶前路线的 1.8 m 体积里，A 自身没有构件。
6. **端口坐标系没法闭合。** A 是 `cityPlacement=null`、`space=local-study`，`city-data.mjs` 里没有节点矩阵。LY-005 的 port-schema 要求必填 `world`（`luoyang-local-schematic-v01`）和 `nodeMatrixColumnMajor`，局部研究件现在填不了，需要 LY-005/006 给局部端口一个合法的写法（比如 world = null，并注明「未配准」）。原生母版 `1e8c4d2c…` 里登记过一个 C 位移 [2367.347, −632.653, 0]（Blender Z-up）。它是原设计登记，不是网页城景的落位，也不能拿来替 LY-004 定位。
7. **与观经空间没有任何共享变换。** 观经空间是 40 × 34 m 的单网格局部件（x ±20，z −16…18，地面 y = 0，83,084 三角，见 `qa/probe-stoneclassic-near.json`）。全仓库没有一个文件给出它与 A 的相对位置。LY-077 不能假设它在 A 南侧多远，也不能把两块地面连起来。
8. **A/B 不能互换。** B 的台基高 0.8 m，入口和地面都不一样（自带 −0.4…0 的展示地面，范围 ±26 × ±9.5）。拿 B 放进 A 的位置跑同一套检查（`qa/selftest/NEG-B-in-A-slot.json`），SHA 不符；中入口的踢面差 −0.2 m，28/264 失败。

## 4. 复用判定

- **A v3.2 本身是合格成果，只复用、不改。** 三档 GLB、原生 .blend 和入口检查都齐全并已复核。城景加载的 flat 投影，几何哈希（按三角排序后的 4 位小数）与 LOD1 相同，都是 `283181be5b2737d2…`。
- **门外地面有一个部分复用候选：旧 v1 的 `A_presentation_ground`。** 它在 `hall-A-LOD1.gltf` 里，46 × 18 × 0.4 m，顶面 y = 0，材质 `REUSED_C_earth`，带 UV。它的范围和原生母版里的 `C_TAIXUE_ISOLATED_SUPPORT_PATCH` 记录边界相同（x ±23，z ±9，y −0.4…0）。我只保留这个节点放到 v3.2 A 下面跑检查（`qa/selftest/REUSE-probe-v1-presentation-ground.json`）：三个阶前垫 0 失败，第一级踢面正好 0.200；三条汇流路线 0 失败、0 侵入；进入 A 实体 0；安装和撤回后 A 不变。
  - 但它**不是现成的合格成果**：它是展示底座，没有端口；前方只剩 4.15 m 深（z 4.85…9.0）；它还铺满长堂后方和两端，超出「门外」范围；而且它与原生母版的支撑块是同一块地，一起加载就是旧新叠载。
  - 所以本席位的判定是：**复用 A，补端口和阶前/汇流地块。** 地块可以沿用这个现成 C 尺寸，不另发明，但不能标「复用完成」。

## 5. 改 / 不改范围

- **改（制作时）：** 只新增一个独立的 A 门外到达地块（建议范围 x −19…19、z 3.8…≈9.5、y −0.4…0，顶面 0.000，与第一级踢面底面重合）；端口 JSON（每个入口一个 threshold 端口，加一个院外 ground 端口）；`assembly.json`（安装、撤回和互斥规则：与 v1 `A_presentation_ground`、原生 `C_TAIXUE_ISOLATED_SUPPORT_PATCH` 互斥）。
- **不改：** A 的四个网格（`taixue-A-static_earth / timber / tile / fiber`）和三档 GLB 字节；入口修订的九个踏步；B 的任何文件；观经空间的任何文件（属于 LY-078）；`city-data.mjs`、项目卡和全站数据（属于 LY-100）。台基边 0.6 m 无护栏：没有证据，所以不加栏杆，只在通行报告里列为限制。

## 6. 证据与未知

| 事项 | 分类 | 依据 |
|---|---|---|
| 太学在开阳门外，建武五年起 | 原文（经 LY-002 E-R06：S09 光武纪、注引陆机《洛阳记》） | 只说明区位，不提供端口坐标 |
| 讲堂长十丈、广三丈 / 二丈 | 原文，但为西晋记载且有异文（LY-002 E-R06，X18 禁直接当 180 年实测） | A 的 37.6 × 7.6 m 平台是 C，未采用此数 |
| 石经立于「太学门外」，瓦屋覆之、四面栏障、开门于南 | 原文转引，谢承书（孙吴），见 LY-002 E-R06 S13/S14 | 说的是**太学门**（院门）外，不是 A 长堂的台阶外。A 门前地块不能等同于观经空间 |
| A 的三入口位置、0.2 m 踢面、0.6 m 台基 | C 工程设计（v3.2 README 原话：「都是 C 级功能设计」） | — |
| 门外地面高程 0.000、地块范围、院外端口位置 | C 工程设计 | 本席位要交的就是这一项 |
| 太学院落范围、院门位置、与观经空间的距离、180 年的实际状态 | **未知**（LY-002：「东汉太学院落范围、讲堂确址：未知」） | 不补图 |
| 魏晋太学遗址 150 × 220 m、正始三体石经、北魏资料 | 异期，禁用（LY-002 X09/X11） | — |

五件事要分开说：**模型能读取**（三档 A 都已读回）、**局部通行通过**（门外段目前不通过，缺地块）、**已入城**（否，`cityPlacement=null`）、**真实结构安全**（未测）、**历史复原成立**（不成立，全为 C）。
