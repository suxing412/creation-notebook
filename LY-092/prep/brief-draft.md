# LY-092｜市肆住宅区域验收 · 开工准备（brief 草稿，第二轮 2026-11-06）

状态：**待输入**。G 还没冻结：LY-001/002/005/006/007/008/009 已标「交付完成」，但 **LY-010 目录不存在**，而且这些 G 包都绑定 bce3211。LY-030、050、082、083、090 都还停在 prep，没有可验的包。本席位这一步只做三件事：写验收方案、写检查脚本框架、对当前基线跑「改前」测量。没有制作或修改任何几何。lab 仓库全程只读，只用了 `git show`、`git diff`、`git log`、`git rev-parse` 这几个只读命令。

第二轮的起因：origin/main 已经从 bce3211 前进到 **cad338b**（r2026.11.05-8「place three northern courts」）。住宅从 44 院变成 **47 院**，ground-retained 也改成首屏加载。本轮把框架改到能在 47 院基线上验「原 44 院不变」，并在 bce3211 和 cad338b 上各重跑了一遍。

## 1 目标（来自任务池 LY-092 节）

在**同一个当前基线**上，把市肆区域包（030）、示范院包（050）、院外短巷（082）、市肆外街接点（083）和多地坪开孔合成（090）放进一次联合装配，然后验六件事：
1. 原 44 院计数不变；
2. 所选市肆计数不变；
3. 井孔和其他孔洞一起检查；
4. 道路能通行；
5. 互斥关系成立；
6. 撤回后恢复原状。

各包单独通过的结果不能顶替联合结果。失败时要指出具体的模型、三角形和路线，截图不算验收。本席位不产出模型，产物是验收报告、可重跑脚本和负例。

## 2 基线与漂移（实测）

| 提交 | 说明 | 区域指纹（`regionFingerprint`） |
|---|---|---|
| `bce3211f818e…` | 任务池核对基线，lab 检出 HEAD | `b1f59a7e1deb4379…` |
| `b70c4957e2b6…` | 雍门道路（第一轮已测） | `b37a817723146fed…` |
| `cad338ba683f…` | origin/main（2026-11-06），新增北缘三院 | `5ff321bb54188710…` |

bce3211 → cad338b 之间，`city-renderer.mjs` 没有改（`git diff --name-only` 只列出 city-data.mjs）。区域内节点逐个比较（`out/drift-bce3211-to-cad338b-G.json`）：
- **原 44 院**：指纹 44/44 相同（资产、矩阵、far/near 实测 SHA、excludeNodes、initial、chapter、replaces 都相同）。冻结在 `scripts/original44.json`，键汇总 sha256 是 `9194384cc200f455…`。
- **市肆**：market-main 和 market-N2 的指纹不变。
- **变化 2 个**：`ground-network-ground-stitched` 新增 `replaces:[yong-road-receiver]`；`ground-retained` 的 `initial` 从 false 改为 **true**（city-data.mjs@cad338b:3813）。
- **新增 8 个**：`C_NORTH_INFILL_01/02/03`（chapter residential，initial）；它们的 `-near` 节点（chapter north-three，各自 replaces 对应的 far 节点）；`yong-road-link-near`；`yong-road-receiver`。
- `provenance.counts.courtyards` 从 44 变成 **47**（L5219），住宅章副标题改成「47 座已落位院落 · 原44院与北缘3院」。

**结论**：任务池写的「原 44 院计数不变」在 cad338b 上必须拆成两条：
- I1：总院数等于冻结基线的院数（bce3211 是 44，cad338b 是 47）；
- I1c：原 44 个 ID 全部在场，并且指纹逐个不变。

正式验收用 LY-001 届时重发的快照**重跑全部测量**，本草稿的数字不能沿用。

字节规则：文本文件以提交 blob 为准（本机 autocrlf 检出的字节不同）；GLB 检出与 blob 相同。

## 3 已有成果核对（文件 + SHA256，全部实测）

城中实际加载的本区 GLB，声明 SHA 等于实际 SHA（bce3211 18/18；cad338b 加 6 个，共 24/24）。完整 SHA、字节数和加载代码位置见 `inputs.json`。

| 资产 | 文件 | SHA256 前 16 位 | 节点 |
|---|---|---|---|
| courtyard-A | assets/r01/R01-A-LOD1 / LOD0-prototype.glb | 0827fa4994b2de31 / 93b70de24ee56573 | 12 |
| courtyard-B | assets/r01/R01-B-LOD1 / LOD0 | 25f018fa8fad0ec6 / a8d94bb3… | 10 |
| courtyard-TC03 | assets/d08/TC03-LOD1 / LOD0 | 8daea250825976b3 / 367a7d25… | 4 |
| courtyard-A2 | assets/c02v/A2-LOD1 / LOD0 | 277e9e73e8f2d8b8 / 19b05202… | 9 |
| courtyard-B2 | assets/c02v/B2-LOD1 / LOD0 | 8328237369a33571 / d99affca… | 7 |
| courtyard-TC03-2 | assets/c02v/TC03-2-LOD1 / LOD0 | d2432b7c22017c46 / bf6287a5… | 2 |
| north-three ×3（只在 cad338b） | docs/library/models/m-luoyang-court-layout-kit/files/opposed_rooms-LOD2/LOD0、compact_work-LOD2/LOD0；m-luoyang-workyard-shed/files/workyard-LOD2/LOD0 | 44366ced / 21ffb5af；84426f91 / e799b588；574d81d9 / 7eb9739e | 各 1 + 各自的 -near |
| market-main | assets/market/market-cluster.glb | 77b8bf2e9e1488df | 1（按章加载，排除 30 个 N2_*） |
| market-N2 | assets/market/N2-replacement.glb | d33cbad1ea14e943 | 1（按章加载） |
| ground ×4 | assets/ground-atomic/{network-ground-stitched, retained, south, D08}.glb | fdfc3ce5 / aed8b3d4 / 4313826d / 3ab93310 | 各 1；retained 在 cad338b 改为首屏加载 |

北缘三院的 6 个 GLB 在 bce3211 检出里就有，作为资产卡文件存在，与 cad338b 的 blob 字节相同；只有 cad338b 的 city-data 引用它们。

**复用判定：无。** 本席位交付的是联合验收结果，不存在可以复用的「已有合格成果」。029/030/041/045/082/083/090 的 prep 测量是被验方自测，只当线索。能重测的部分本席位都独立重测了（§5）。

## 4 改 / 不改范围

- **写**：只写 `workpacks/LY-092/prep/`，以后是 `workpacks/LY-092/qa/`。
- **不改**：city-data.mjs、项目卡、渲染器、任何 GLB、任何他人工作包。联合装配用 overlay 在内存里给 manifest 打补丁（`check92.py apply_overlay`），候选 dump 写进本席位目录的临时文件，测完删除。
- **不判**：历史复原是否成立、真实结构是否安全、GPU 和手机表现。只判「模型能读取 / 局部通行 / 装配与 manifest 一致」三层。任务池列的五件事各自独立，不能互相替代；「已入城」由 LY-100 合并后另验。

## 5 实测缺口（脚本 `scripts/baseline92.py`，固定栅格 `out/grid-frozen-v1.json`）

**测量方式**：用 numpy 重实现渲染器的组合规则：
- initial 集合；
- 章节只加不减；
- `replaces`；
- excludeNodes 严格匹配；
- 矩阵和剪切检查。

几何取上表 GLB 的真实三角形，栅格化朝上的面（ny>0.5，高度带 −0.5 到 1.2 m）。住宅格 0.5 m，市肆格 0.25 m，取格心。测五个状态：S0 冷启动、S_residential、S_market、S_terrain、S_all（所有城市章节都打开过）。

**本轮新修的测量问题**：第一轮的栅格原点跟着区域包围盒走。北缘三院让 z0 从 −1244.0107 移到 −1276.0000，格心整体偏了 1.07 cm，叠层格数因此从 4,969 假变成 4,971。现在栅格固定（z0 = −1276.010701，与 bce3211 的格点对齐），两个基线上都是 4,969。同一输入跑两次，输出逐字节相同；bce3211 的旧输出也能逐项重现。

| # | 测量 | bce3211 | cad338b |
|---|---|---|---|
| G1 | 住宅节点 / 原 44 院不变 | 44；A12 B10 TC03 4 A2 9 B2 7 TC03-2 2；重复矩阵 0；足迹重叠 0 对；最近院距 1.85–19.21 m | 47 = 原 44（指纹 44/44 相同）+ 北缘 3；足迹重叠 0 对；新院与邻院最近 7.84 m（C02-031）/ 8.0 m |
| G1m | 市肆实际组合（S_market 和 S_all） | 524 网格、18,296 三角；店 N1/N2/N3/S1/S2，摊 T1/T2/T3 | 相同 |
| G2 | 冷启动 S0 的住宅足下支持 | 44 院内部平均 **18.23%**（只有台基）；院外 2 m 环带 44/44 院为 0% | 原 44 院内部平均 **59.81%**；22 院 100%（坐在 retained 上），**22 院环带仍是 0%**（C02-005…017、C02-032、8 个 FROZEN-D08，坐在 south 或 D08 上）；新 3 院 100% |
| G2t | S_terrain / S_all | 内部和环带都是 100% | 相同 |
| G3 | 市肆东出口（x=244.286 往东 20 m，80 个样点） | exitPublic：S_market 0/80，S_all 80/80；exitN、exitS 在所有状态下都是 0/80 | exitPublic：S_market 80/80（yong-road-receiver 承托）；exitN、exitS 仍是 0/80 |
| G3r | 路线 X-market-public-cold（S_market，289 个样点） | 71 个失败（无支持） | 0 个失败 |
| G4 | 叠面（不同节点之间的朝上面） | 小于 2 mm：0 格；2–30 mm：S_terrain/S_all 6 对、4,969 格；S0 为 0 | 小于 2 mm：0 格；S_terrain/S_all 6 对、4,969 格；**S0 新出现 2 对、1,249 格**（C02-020×retained 1,214 格，C02-003×retained 35 格），原因是 retained 改为首屏加载 |
| G4b | Blender 交叉核对叠层高度（`scripts/blender_xcheck92.py`，`out/blender-xcheck-TC03.json`） | TC03-LOD1 的 designed_front_apron、side_passage、rear_work_ground 顶面 **0.212 m**；site_lot 和地面在 0.200 m，差 **0.012 m**；三块合计 293.6 m²（numpy 按格估算约 298 m²）；drain_stone 0.20–0.29 m | 同一文件 |
| G5 | 基线孔洞 | 区内名字像孔的部件只有 6 个 drain_stone（地表件），没有一个真孔 | 相同 |
| G5p | 计划孔位探针（LY-006 registry 切孔区，`tests/probe-planned-holes.overlay.json`） | 井 A（196.286, −1952.184, r 0.59）：S_market 和 S_all 被 `market-main\|sample_ground#3` 封住；S0 和 S_terrain 下面是**空的**，没有地面也没有井沿（环 0/8）。C02-010 厕孔区中心（535.55, −818.65）：S_terrain 和 S_all 被 **`ground-south\|single_closed_terrain_after#78164`** 封住 | 相同 |
| G6 | 排除与互斥 | 12 个院落文件的 excludeNodes 缺 0 个；6 种近档换档组合 0 错误；market-main.excludeNodes 与 N2-replacement 重名 30 个；没有一个节点用 `replaces`；渲染器加载时不核 SHA（city-renderer.mjs:286-346） | 9 种近档换档组合 0 错误（北缘 3 种在 S_residential 上测，因为 S_all 里它们已被 -near 节点替换）；7 个节点用了 `replaces`；仍然没有互斥组 |
| G7 | v1 归档入口 | 没有重测（west-layer.mjs 另有一套组合） | 同左 |

**交给他人的具体发现：**
1. **LY-006 / 045 / 090**：registry 把 `LY-045:cut:002` 写成「ground-retained 上的厕孔」，但该区中心实测由 **ground-south** 的三角形 #78164 承托和封住，retained 不覆盖这一点。切孔的地坪归属要重核，否则 090 会切错地面文件。
2. **LY-025 / 090**：井 A 位置去掉 sample_ground 后，下面没有任何地面。这独立证实了 025 prep 的说法。孔洞检查因此必须同时要求「孔开着」和「井沿有支持」（检查 H 的环 8/8），否则空洞也会被判成开孔。
3. **LY-001 / 010 / 100**：cad338b 让首屏住宅支持从 0/44 院变成 22/44 院，但也把 C02-020 的 1.2 cm 双层地坪带进了首屏。050 如果选 C02-010（registry 的候选），它在 S0 仍然没有外环支持（C02-010 坐在 south 上）。
4. **LY-083 / 030**：市肆公共出口的冷启动支持随 main 改变了。bce3211 下 71/289 个样点失败，b70c495 起是 0 失败。两包的冷启动结论都必须在新快照上重测。

## 6 证据分类

| 内容 | 类别 |
|---|---|
| 44 院与北缘 3 院的形态和落位、五店三摊布局、地坪高程 0.20/0.21/0.212 | C 工程设计（manifest 的 basis 自述「C 级设计落位」「推测」；北缘三院的 basis 明说「不证明洛阳古代宅址、院数或尺寸」） |
| 市肆位置（金市研究示意点 region_jin_B） | 未知 + C，不是考古配准 |
| 井 A 尺寸、厕孔区 | C 工程设计（LY-025 prep、LY-006 C-partition） |
| 成都市肆画像砖、北魏洛阳、西汉长安、东汉陶院落 | 只能作异地、异期或类型类比，本席位不拿来当尺寸依据 |
| 本草稿的全部数字 | 本机重实现测量，CPU 计算，没有经过浏览器或 GPU |

## 7 局限（如实）

- 格心采样（0.5/0.25 m），不是连续人体扫掠。净空检查用「三角形 y 范围与 0.35–1.8 m 带相交，并且 XZ 距离小于半径」，偏保守。
- 叠面只看 −0.5 到 1.2 m 带里朝上的面。2 mm 是 z-fighting 风险阈值，不是 GPU 实测值。
- 没有做三角形对三角形的实体相交，不能说实体碰撞已经查尽。
- Blender 只交叉核对了 TC03 和 TC03-2 两个 LOD1 文件的地坪高度，联合状态的 Blender 复核留到正式验收。
- 没有运行官方 `build_assets.py --check`（本阶段禁止）。B 类检查改为读 LY-008 `ly_check.py` 的报告。
- 北缘 3 院的近档换档是在 S_residential 上测的。S_all 里 far 节点被 -near 替换，这时浏览器里 focusCourtyard 的行为还没有核。
