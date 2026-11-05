# LY-083 市肆外街真实接点补件 · 开工准备（brief 草稿，第二遍）

状态：**开工准备 / 待输入**。G（LY-001/002/005/006/007/008/009/010）未冻结，LY-030（市肆区域包）和 LY-081（实际地面可达网络）也没交付。本目录**没有制作、也没有修改任何交付几何**，只做了读取、实测和测试准备。
- 基线：creation-notebook-lab `main` = `bce3211f818ee5a8bef1773539da70695ba37b17`（只读）。
- 漂移：`origin/main` 已到 `cad338ba683f`，比基线多 3 个提交。本项输入里只有 `city-data.mjs` 和项目卡变了，**而这一变化直接影响第 3 节缺口 1**（见 3.1b）。
- 第二遍（2026-11-06）做了三件事：
  - 重新核对 26 个输入的 SHA，全部相符。
  - 重跑 `measure_outer_street.py`，输出与第一遍逐字节相同（`1bba3cd9…`）。
  - 补跑第一遍没执行的负例、包络扫掠、净空和漂移检查：`measure/measure_supplement.py`、`measure/measure_drift_cad338b.py`。

## 1. 本项目标（按任务池原文）

做市肆区域边界到现有主地面/路段的实际接续，以及对应的地坪差异件。
- 内部前街属 LY-022。LY-022 的 prep 把补件区止于本地 x=24，也就是城市 x=244.286。外街从 x=244.286 往东算，归本项。
- 不能为了接上路去改市场的历史位置，也不能把 C 连接说成古金市的真实街网。
- 验收：用市肆边界和真实主路端点；外街长度和高差必须来自本次测量；不能为接通去改市场内部道路或历史地块。

## 2. 核到的现有成果：公共外街已经存在

运行时的外街，是原子地面 `assets/ground-atomic/network-ground-stitched.glb` 里节点 `C_stitch_primary` 的一段（SHA256 `fdfc3ce5c63305f79aa746b31c3be60f3d11a6acb75f190886124f2d3446db60`）。它是 C 设计的支线，从市肆公共出口 `route_exitPublic` 接到城西主路 `road_west_spine_B_C_0`。市肆根文件是 `assets/market/market-cluster.glb`（`77b8bf2e9e1488df02c99ffa1b83af9517fabbb23e9d6b7f86dd3c3361c5a5c8`）。

| 项 | 实测值（Blender 5.2.1，GLB 回读） | 证据 |
|---|---|---|
| 市肆东界 x | 244.28599548。市肆根和城网顶点在这里的极值相同，缝宽 **0.000000 m** | `fine_measure.json#seam` |
| 主路中线在市肆轴线 y=1959.184 处 | x = 395.378223（`road-plan.json` 线性插值） | `outer_street_measure.json#spineCenterXAtMarketAxis` |
| 主路西缘（y+4 m，0.01 m 步长） | x = 392.40 | `fine_measure.json#spineWestEdgeAtY+4` |
| 外街长度 | 到主路西缘 **148.11 m**；到主路中线 **151.09 m** | 上两行相减 |
| 宽度 | 边界处 4.00 m，等于 `route_exitPublic` 的宽度。到 x≈254.3 线性放宽到 6.0 m（0.01 m 采样读到 5.99）。丁字口 x=392.5 处读到 9.0 m（含路口面） | `fine_measure.json#networkWidthProfile` |
| 顶面高程 / 高差 | 全线 0.20999–0.21001；与 `route_exitPublic` 的 **高差 0.000 m** | `outer_street_measure.json#centerline.v1_market_A.heightSteps` |
| 中线连续性（0.25 m 步长） | v1 市肆 A/B 视图下 x 184.5–398.25 无缺测 | `centerline.v1_market_A/B.missRuns` |
| 缝口 5 mm 精扫（9 线 × 41 点） | 0 缺测，z 0.21；只有 `route_exitPublic` 和 `C_stitch_primary` 两件承托 | `fine_measure.json#seamScan_5mm` |
| **身体包络扫掠**（第二遍新增） | 人 0.6 m 包络：19,266 点，0 无承托。小件手搬 1.6 m 包络：48,906 点，0 无承托。横向最大高差 0.00002 m。步长为纵向 0.1 m × 横向 0.05 m | `supplement_measure.json#S2` |
| **头顶净空 0.215–2.4 m**（第二遍新增） | 1,445 根上射线，0 处遮挡。范围仅限 v1 市肆 calt 视图载入的对象 | `supplement_measure.json#S3` |
| 主路连续（y 1900–2020） | 0 缺测，0.21 | `outer_street_measure.json#spineProfile_v1A` |

**复用判定（候选）**：市肆唯一的公共出口到主路，已经有一条连续、零高差、零缝宽、包络扫掠全部有承托的 C 外街。公共外街**不需要新造**。

这只证明两件事：「模型能读取」，以及「局部通行在有限射线和包络采样下通过」。它不证明连续人体运动、实体碰撞已穷尽或 GPU 效果，也不涉及结构安全或历史复原。

## 3. 实测到的真实缺口

### 3.1 v2 城景市肆章节冷启动没有外街：基线 bce3211 上属实，origin/main cad338b 上已被别人闭合

**a. bce3211 的情况**
- 代码路径：`city-renderer.mjs` 第 221 行，只有 `initial!==false` 的节点进入 `loadedIds`。第 595–613 行 `focusChapter()` 把章节的 `loadNodeIds` 并入 `cityIds`。
- `city-data.mjs` 的 `market` 章节，`loadNodeIds` 只有 `market-main` 和 `market-N2`。四片原子地面都是 `initial:false`，只属于 `terrain` 章节。
- 用 node 读取 city-data 复核：节点包围盒覆盖外街走廊的只有 `ground-network-ground-stitched` 和 `market-main` 两个。
- 实测配置 `v2_market_chapter_cold`：中线 901 个采样里 **661 个缺测**，x 244.5–405 整段悬空。负例 `neg_no_network` 同样 661。

**b. cad338b 的情况（漂移，第二遍新增）**
- 新节点 `yong-road-receiver`（`initial:true`）。它是从主路无损提取的 209 三角连通分量，文件 `progress-assets/yong-road-link-v2/yong-road-receiver-component209.glb`，SHA `e5baa0df8fd28e117b4ef997cab0d962b0834a4c9664bb1ed73b7746d2488e38`，节点名 `C_stitch_primary_yong_receiver_component209`。
- 实测：这个分量**包含外街**。冷启动市肆（market + N2 + retained + receiver）中线缺测 **45/901**，只在市肆西界外和主路东缘外，x 244.5–398.25 由 receiver 承托，0.21。
- 7 个 x 位置上，receiver 宽度与 `C_stitch_primary` 完全一致。1.6 m 包络 48,906 点 0 无承托。缝口 5 mm 精扫 369 点 0 缺测。
- 证据：`measure/drift_cad338b_measure.json`。

**处置**
- 若 LY-001 冻结的新快照包含 cad338b，第一遍拟交的「市肆章节加载四片原子地面」合并提案就**不再需要**。只需要在新快照上重跑 N2 冷启动测试，并绑定 receiver 的 SHA。
- 若快照回到 bce3211，提案仍成立：须四片全载，交 LY-100。
- 两种情况下本席位都不改共享文件。
- 附带风险，不归本项：cad338b 的 `ground-retained` 变成 `initial:true`，stitched 仍是 `false`。打开 terrain 章节后，README 说 network 会替换 receiver。是否会出现双层面，由 LY-081 和区域验收席位复核。

### 3.2 市肆东边界另有两个出口落空
- `route_exitN`（y 1974.184–1978.184）和 `route_exitS`（y 1940.184–1944.184）止于 x=244.286，边界外 0.1 m 无任何承托（`supportJustBeyondBoundary: null`）。LY-030 prep 也独立测得 egress 125/125 无承托。
- 出口中心到外街的横向距离：边界处 14.99 m，x=300 处 14.01 m。换算成出口边缘到外街边缘约 13.0 m。
- `sample_ground` 边缘有 0.20 m 落差，外面是未建空白。
- `market-flow-plan.json` 的 A/B 路线只用公共出口，所以这两个出口不在任何受测路线上。
- 处置：补「边界外 4 m 宽、约 13 m 长 ×2」的接坡/地坪差异件，是 C 设计选择。必须等 LY-030 冻结保留出口、LY-081 判定它们是断点（不是禁用边）以后再定。**不得自行虚构沿边外街。**

### 3.3 1 cm 台阶在市肆内部，不归本项
`sample_ground` 0.20 对路带 0.21，在 x 187.25→187.5 处，位于 x<244.286 以内，归 LY-022/LY-025。

### 3.4 旧外街在 v1 存档里仍被加载；第一遍「实际不会加载」的说法有误，第二遍更正
- `v1/west-state.mjs` 的 `readState()`：layout 默认是 `calt`，带 `?layout=original` 时才是 original。
- `v1/west-layer.mjs` 第 33 行：market 层级先载 `corridor-6m-market-link.glb` 和 `joined-route-terrain.glb`。第 34–37 行只在 `layout==='calt'` 时把它们换成四片原子地面。
- 因此 `v1/?mode=west&view=market&layout=original` **确实加载旧件**。实测（S1）：旧件节点 `C_main_road_width_6` 承托 x 244.5–398.25，0.21，0 缺口。
- v1 是旧版存档（`index.html` 第 111 行链接、`app.mjs` 第 7 行 legacy 跳转），所以这算存档路径上的旧方案，不是 v2 的缺口。
- `data/west/market-interface.json` 仍把旧件写成现行；`ground-atomic-contract.json` 已把它列入 `replaceResources`。
- 负例 N3 实测：旧件和 stitched 同载时，444/444 个点出现共面双层路面。说明两者必须互斥，提案里要写明，防止有人叠回。

### 3.5 测试计划自查：第一遍的 N4 写错，第二遍更正
`assertGroundAtomic`（`v1/ground-atomic.mjs`）只数 stitched 文件内三个节点名。只载 stitched 时三名各 1，**检查照样通过**（S6），所以它不能证明「四片全载」。四片全载要另按 `ground-atomic-contract.keep` 的三个 SHA 检查，已改进 test-plan。

## 4. 改 / 不改范围（草案）

**不改**
- `market-cluster.glb` 全部节点（含 `route_*`、`sample_ground`、`boundary_*`）、N2、flowB。
- 四片原子地面（含 `C_stitch_primary`）和 receiver。
- 主路，市肆位置（金市 B 点 214.286,1959.184）。
- `city-data.mjs`、`city-renderer.mjs`、`v1/*.mjs`、项目卡、`lab/data/assets.json`。

**可交**
- (a) 公共外街的复用身份包：节点、SHA、实测长度/宽度/高差/包络/净空、测试脚本。快照含 cad338b 时，同时绑定 receiver 的 SHA。
- (b) 视快照而定：要么写「v2 已入城」的复测记录（cad338b），要么交「市肆章节四片原子地面全载」的语义合并提案，给 LY-100（bce3211）。
- (c) 旧件互斥说明：`market-interface.json` 已过时，v1 original 布局仍用旧件。只写说明，不改文件。
- (d) 有条件制作：LY-030 保留 exitN/exitS、且 LY-081 判它们为断点时，才做边界外最小地坪差异件。必须是独立 GLB、可撤回，不与 stitched/receiver 叠面。

## 5. 证据与未知

- **原始考古/原文**：金市只有一个 B 点（`region_jin_B`，来源 gao2023_fig1），没有市界、门位或外街证据（`market-precedents.json`）。
- **异地异期类比**：四川/成都市肆画像砖只给「有界交易空间」的类比，不能给洛阳尺寸。
- **C 工程设计**：60×44 样板、出口位置、外街 4→6 m 宽度、0.21 m 高程、148/151 m 长度、主路走向，全部是 C。
- **未知**：古金市对外道路的走向、宽度、路面材料，以及与城西主路的关系。
- 五件事分开记：
  - 模型能读取：是。
  - 局部通行：有限射线和包络采样通过；没做连续运动和实体碰撞。
  - 已入城：bce3211 否；cad338b 中线、包络、缝口均通过，但没有浏览器/GPU 实测。
  - 结构安全：未涉及。
  - 历史复原：不成立。

## 6. 私密源包

都**不需要**，均可「从 GLB 重建」。市肆东界 x=244.28599548、顶面 0.21，可以从 GLB 精确读出。

| 缺的源包 | 说明 |
|---|---|
| C-ground-stitch-v1 生成器和 .blend | 不在仓库 |
| market-cluster 原生 .blend | 不在仓库 |
| market-link-continuity 检查器 | 只有 SHA `37aa804c…`，已用本目录脚本替代 |
| yong-road-link-v2 源包 | README 说另存 Release |
