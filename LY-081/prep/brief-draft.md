# LY-081 建立实际地面可达网络：开工准备简报（草稿）

状态：**待输入（开工准备）**。G（LY-001/002/005/006/007/008/009/010）没有冻结，本席位没有制作、修改或发布任何交付几何或网络数据。本目录中只有只读测量脚本、测量结果、输入清单和测试计划。
基线：`D:/GitHub/creation-notebook-lab` main `bce3211f818ee5a8bef1773539da70695ba37b17`（`git rev-parse HEAD` 已核）。坐标：仓库数据用 glTF 坐标（X 向东，Y 向上，Z 为负时向北）；本目录测量全部用 Blender 世界坐标，即 x = glTF X，y = −glTF Z，z = glTF Y。

## 1. 本项目标（按任务池原文）

用**当前城景实际加载的三角面**提取三样东西：可以站人的支持区、端口、真实断点和禁用边，再整理成网络数据。要求如下：
- 不用 B 标签直接连直线，不把展示底板当成可走的地面；
- 写明覆盖范围只是有限样本或有限体积检查，不能说成全城连通；
- 网络里每条已通边都要能对回实际的面和对应的测试；
- 移除某块地面后，必须出现断点，作为负例；
- 未建区域不能因为连线算法而变成路。

LY-081 属于考据/契约席位，交付的是网络数据和检查，不交模型。断点的修补由别的席位负责（LY-082/083/084/085 等，或原负责人）。

## 2. 核到的现有成果（文件 + SHA256）

| 文件（相对 lab 仓库） | SHA256 | 作用 |
|---|---|---|
| docs/cities/luoyang/assets/ground-atomic/network-ground-stitched.glb | fdfc3ce5c63305f79aa746b31c3be60f3d11a6acb75f190886124f2d3446db60 | 三节点原子组：C_stitch_primary / west / patch，共 128,342 个三角面 |
| docs/cities/luoyang/assets/ground-atomic/retained.glb | aed8b3d4cb12aeaddf5c696a8a86355b15b7cb4fc8ebd76cc364d23789d630cc | C02 保留地面，21,192 个三角面 |
| docs/cities/luoyang/assets/ground-atomic/south.glb | 4313826ddf5fbe0c0d8dcb4983d6cdbd647713d49faa1980cd34f587a3273a0e | 南 14 院地面，96,796 个三角面 |
| docs/cities/luoyang/assets/ground-atomic/D08.glb | 3ab933108b88c5c359fc7512d324e14f15157eaa54fb17f80f2adeb6c4626d9a | D08 样段地面，140 个三角面，只平移一次 [580,0,−960] |
| docs/cities/luoyang/data/west/ground-atomic-contract.json | bfc7fc83c3d8f34c79e9395532b74c324987b4dbf0c4342328b7581ebc2be584 | 原子契约：三节点必须同时加载，doNotClaim 不能声称的项写明包括 collision validated |
| docs/cities/luoyang/data/west/ground-final-actual-GLB.json | 405db4fee6a822f1e2a54260ed5c256782d087e49a40eba457b3940f94b6ea13 | 旧报告：聚合闭合，沿示意路径做有限采样，pathMissing 为 0 |
| docs/cities/luoyang/data/west/network.json | af8e5479f47ccae1dd5c41766da60e6a871e74808018737a85514895334afc73 | 旧报告：14 条门到路的**示意路径**图可达性，路径由 B/C 折线组成 |
| docs/cities/luoyang/data/west/road-plan.json | 9792f217619ef72f2cb7528856112c7403a765420814a0dfe562ad23a7ebd361 | 6m/10m 两种宽度各 7 段 C 路，含切断理由（cuts） |
| docs/cities/luoyang/data/west/road-preconstraints.json | 8b2fa0faaf5c6fa5fcb3a9d50e2e7d412a5f5a8f47e03ce13cc641474c5f449d | 12 条 B 道路关系：5 条为 C 试验，2 条只记关系，5 条宫缘悬置 |
| docs/cities/luoyang/data/west/runtime-coverage.json | 0b25c3176d7aaf26f0aa0a1c04d7e0f96f584b8668026e1e056f93113a476f9e | 自述「711 finite points not traffic」，并说明不能宣称全网连通 |
| docs/cities/luoyang/city-data.mjs | e4115705aeab28f2f6cc2635fbedfabf4158a08af9c626f6dd493ee27d430a1a | 主城清单：terrain 章 4 个节点，initial:false |

**结论：没有可以直接复用的合格成果。** 旧的 network.json 和 ground-final-actual-GLB.json 都是**沿 B/C 示意折线做有限点采样**（路线先定，再查脚下有没有面）。它们不是从三角面提取的支持区网络，没有列出真实断点和禁用边，也没有移除地面后的负例。它们可以作为输入对照，不能直接当成 LY-081 的交付。

## 3. 现在实际加载了什么（加载路径）

- **主页面**：`index.html` → `app.mjs` → `city-renderer.mjs`。
  - 启动时只加载 `initial !== false` 的节点（city-renderer.mjs:221）。
  - terrain 章的 4 个地面节点都是 `initial:false`。只有打开「06 道路与地形」时，`chapter.loadNodeIds` 才把它们加入加载集合（city-renderer.mjs:601）。
  - 加载调用 `loadAsset`（:286），变换由 `transformFor`（:372）给出。D08 的变换来自 position [580,0,−960]（city-data.mjs:3636 起）。
  - 住宅院落的 `excludeNodes` 会剔除 site_lot、site_neutral_lane、designed_*（:309）。这些就是展示底板，不进城。
- **v1 页面**：`v1/west-layer.mjs:35-37`。只在 calt 布局、而且不是仓储层时，才加载同样四件地面。之后由 `assertGroundAtomic` 核对契约（v1/ground-atomic.mjs）。
  - `v1/road-layer.mjs:17-19` 走 road-interface.json 的 runtimeAssets，宽度 6m 时加载同样四件。
  - 宽度 10m 时加载另一套互斥地面：corridor-10m.glb、route-corridor.glb、south.glb。
  - **LY-081 只处理 6m 原子组**，10m 这套另列，不能混用。

## 4. 实测缺口（脚本：`prep/scripts/measure_ground.py`，SHA e28e34a8…aae2e）

测量方法：导入 GLB，按城景矩阵摆放。把坡度不超过 20° 的上表面三角面按 1mm 焊接，按共边连成连通分量。在每条边界边上每 1m 设一个探针，向外偏 0.10m 和 4mm，向下打射线，按高差把边界分为 void / seam / step / drop / crack。另用 2m 网格做竖直射线，检查净空线 2.0m。最后跑移除地面的负例。

| # | 缺口 | 实测数字 | 证据文件 |
|---|---|---|---|
| G1 | 四件地面的上表面只有 **5 个互不相连的分量**（strict 和 tolerant 都是 5）。主分量 174,298.76 m²，同时包含四件地面 | 另有 4 条孤立的 C 段：C_1 2,571.59 m²、C_4 6,161.39 m²、C_5 2,941.19 m²、C_6 6,904.89 m²，合计 18,579 m² | run-ground-only.json |
| G2 | C_5（road_west_south_link，东西向）在广阳街口东侧断开 | 平面间隙 **3.761 m**，位置 x 404.00→407.76，y≈488，dz 0.01；road-plan cuts 记为「final seam pending」 | componentGaps |
| G3 | C_1（road_west_spine 南段）在街口以南断开 | 间隙 **4.292 m**，位置 y 471.71→476.00，x≈386.6 | componentGaps |
| G4 | 中部东西路 C_3 和 C_4 之间断开，这是**禁用边**：palaces_connector_B 的立交方式未知，不能造桥，也不能做平交 | 间隙 **56.202 m**，位置 x 1445.46→1501.65 | componentGaps + road-plan cuts |
| G5 | C_6（平城南接线）完全孤立，北端没有到城墙 | 长约 1,150 m；北端离 wall-06 端头 **57.71 m**；离最近的其他地面分量 913.3 m | run-ends.json |
| G6 | C_4 东端离东墙 wall-02 **49.29 m**；C_1 南端离 wall-07 **31.11 m**。两处都是门点切断（gate_zhongdong_B / gate_jin_B：门点和墙体不吻合的问题未解决） | 同上 | run-ends.json |
| G7 | 雍门：apron 是独立的上表面岛（539.83 m²），和地面网络不相连 | 门内探针离最近地面 **47.1 m**，apron 东缘 −6.37 到 C_2 起点 43.1 约 49.5 m。**雍门接街属于原负责人的保护项，LY-081 只记录断点，不补** | ports: yong-* |
| G8 | 仓储（storage-main）200 m 内没有任何地面，自身院面 3,744 m² 是独立的岛 | storage-target 到最近地面为 null（搜索半径 200 m 内没有）；和 storage-interface 里写的 `unconnected:true` 一致 | run-full-grid2 / run-promoted |
| G9 | 市肆：market-center 脚下是 market-main 自己的地面（z 0.21），不是原子地面；离最近原子地面 30.0 m | 原子地面边界上只有 **4.0 m** 碰到 market 面。把 market-main 地面提升进分析后，它和主分量以 seam 相连。N2 只能在容差图（台阶不超过 0.18 m）里连上 | run-promoted |
| G10 | 主分量内部有 **879.78 m** 边界是 T 型接缝（向外探 4mm 仍有面），说明面没有焊接；另有 6 条非流形上表面边 | 不是断点，但导航网格构建时必须焊接或做容差 | boundaryProbeLength_m |
| G11 | C_stitch_primary 内有一条**真实裂缝**：一边宽 4mm，另一边宽 62mm，长约 4.2 m | 位置 x 397.94–398.01，y 1845.76–1849.94。1mm 扫描结果：y=1846 处宽 4mm，y=1848 处 33mm，y=1849.5 处 56mm | scan_line.py 输出 / crack_width.py |
| G12 | 网格检查：44 院建筑占地压在地面上，竖直净空线被挡 939 格（2m 格，约 3,756 m²）；wall-08/09 各挡 2 格 | 建筑底下的地面不能算成路，网络必须扣掉占地 | grid.blockedByNode |
| G13 | 主分量向城外延伸到 x=−39（广阳门外 35.2 m），然后直接没有地面（void），是死端 | 原地面的外缘 | run-ends.json |
| G14 | 负例已经成立：移除 network-ground-stitched 后剩 2 个分量，D08 单独成岛（10,320 m²），广阳 3 个探针和 market-link 失去支持；移除 south 后，14 个门槛和门外 1m 的 28 个端口全部失去支持；移除 D08 后 D08-center 失去支持；移除 retained 后主分量从 174,298.76 m² 降到 89,770.76 m² | 见 run-drop-*.json | run-drop-*.json |
| G15 | 未建负例已经成立：城中心 (1200,1900) 离最近地面 65.1 m；北宫 B 区 (700,2400) 200 m 内没有地面。连线算法不能把它们变成路 | ports NEG-* | run-ground-only.json |

注意事项：
- 14 个示意门槛点和门外 1m 点脚下都有地面，都在主分量里，竖直净空线也都没有被挡。这只说明这些点脚下有面，**不等于**门道里一个人体能连续走过去。
- 主分量里没有 step 类型的台阶（容差 0.18m 内没有出现台阶），上表面高程在 0.175–0.21 m 之间。
- 墙体底在 0.17 m，地面顶在 0.21 m，墙脚压入地面 0.04 m。这需要做接触分类，不能把它当作通行面。

## 5. 改 / 不改范围（草案）

**改**：只写 `workpacks/LY-081/`，内容包括：
- 网络数据：节点是支持分量和端口，边是 seam 或 step 连接，每条边带实测长度、高差，并绑定输入 SHA；
- 断点表：G2–G8、G13；
- 禁用边表：palaces_connector、各门点 cut、宫缘悬置、水系未知；
- 负例；
- 可以重跑的脚本。

**不改**：
- 任何 GLB、city-data.mjs、项目卡、build_assets；
- 雍门接街、13 院压缩；
- 市肆内部前街（LY-022）；
- 不补任何断点几何（交给 082/083/084/085 或原负责人）；
- 不把 B 示意线、10m 互斥地面、仓储现代讲解层（optional-functional-overlay）、院落 site_lot 等展示底板算进网络。

## 6. 证据与未知（四类分开）

- **原始考古/原文**：本席位没有新增。道路关系的 B 层来自 gao2023_fig1（road-preconstraints.json 中 `geometry_role: "B schematic topology, not surveyed centreline"`，`excavated_alignment_verified: false`）。原图版本席位没有重新核对。
- **异地异期类比**：不使用。北魏铜驼街轴线、魏晋水道不能前推（city-milestones.json 写有：不能前推 180 年）。
- **C 工程设计**：全部地面、6m 路宽、0.21m 地面顶高、各段切断位置、本席位的坡度 20°、台阶 0.18m、净空线 2.0m、焊接 1mm 等阈值，全部是 C。
- **未知**：
  - 东汉路宽和分期；
  - 古水道：B 仍是 null。宫墙水道接口卡 m-luoyang-palace-waterway-interface 状态为「研究」，未入城，city-data 里没有引用；
  - 两宫之间的立交方式；
  - 门点和墙体对位。

LY-081 的网络只表达**这些 C 面在模型里是否可以支撑**，不表达历史路网。下面五件事分开记录：「模型能读取 / 局部通行通过 / 已入城 / 真实结构安全 / 历史复原成立」。本准备只做到了第一件，加上有限的支撑采样。

## 7. 复核与基线漂移（2026-11-06 复核补记）

**复核**：lab 工作区 HEAD 仍是 `bce3211`（分支 lab/site-redesign，工作区干净，只有未跟踪的 `.claude/`）。四件原子地面、契约、city-data.mjs、road-plan.json 等的 SHA256 重算，结果和第 2 节一致。用新的加载状态配置（`scripts/make_config_drift.mjs`，严格模拟 city-renderer.mjs:221 的 initial 过滤和 :412-415 的 replaces 替换）在 bce3211 的 terrain 章状态下重跑，复现了 G1–G3：主分量 174,298.759 m²，四条孤立 C 段面积相同，间隙 3.761 / 4.292 m。见 `drift-cad338b/run/m-base-terrain-P.json`。

**补充更正**：
- 第 4 节 G8、G9 用的 scene-config 是全部 66 个节点的**并集**。实际 terrain 章加载的是 63 个节点，**不含** market-main、N2、storage-main（它们属于各自章节，initial:false）。因此市肆和仓储的接触数字只代表「同时打开多章后的叠加状态」，不代表单一实际加载状态。制作期必须按加载状态分别出网络。
- 在 bce3211 冷开（默认）状态下，**没有任何 terrain 节点被加载**（0 个 ground）。44 院在默认画面里脚下没有已加载地面。

**漂移**：本机已有的 `origin/main` 引用是 `cad338ba683f`，比 bce3211 多 3 个提交（f28d650 / b70c495 / cad338b）。本席位没有 fetch，只用 `git show` 把变化文件抽到 `prep/drift-cad338b/`，lab 仓库没有改动。
- 四件原子 GLB 和契约在两个版本之间逐字节相同（`git diff --quiet` 通过）。
- 加载状态有变化：
  - 冷开时加载 ground-retained，加上 yong-road-link（LOD2），加上 yong-road-receiver。receiver 是从 C_stitch_primary 无损抽出的 209 个三角面的分量。
  - terrain 章加载 network 时替换 receiver，并用 link LOD0 替换 LOD2。
  - 新增 3 院 C_NORTH_INFILL_01..03（initial:true），位置在 Blender xy (586|612|638, 1234)，落在 retained 上。

cad338b 下的实测结果（`scripts/measure_ground.py` 未改，SHA e28e34a8…；汇总在 `drift-cad338b/drift-summary.json`）：

| # | 结果 | 数字 |
|---|---|---|
| D1 | terrain 章状态（apron 提升为 ground）：雍门 apron、接街、主分量连成一个严格区域。**G7 在 cad338b 已经闭合** | 区域 174,987.43 m²；apron↔link 接缝 6.939 m，link↔主分量接缝 6.0 m，高差都是 0；yong-in 和 yong-mid 两个探针都落在这个区域内 |
| D2 | 负例：移除 yong-road-link-near 后，apron 重新变成孤岛 | 间隙 49.579 m，dz 0.04 m（与 G7 原记录 49.5 m 相符）；yong-in 失去支持 |
| D3 | 冷开状态是新的独立加载态，分成 2 个互不相连的主区域 | retained 84,528.00 m²，其上有 47 院中的 C02 及北三院；apron+link+receiver 合计 21,183.17 m²。两者间隙 **84.381 m**，位置 (480,1250)→(395.62,1250.33) |
| D4 | 冷开状态下大部分端口失去支持 | 43 个探针中只有 6 个有支持。14 个南院门槛和门外 1m 共 28 个点、广阳 3 个点、D08-center 都没有地面，原因是 south / network / D08 都没有加载 |
| D5 | 北三院增加了净空遮挡 | terrain 状态被挡格数从 939 增到 **1007**（2m 格）：01 号 31 格，03 号 23 格，02 号 14 格 |
| D6 | 北三院门外临时探针（x 581.2 / 607.2 / 633.2，y 1221.5，按南向假设）都有支持 | 在 terrain 状态属于主区域，在冷开状态属于 retained 区域 |
| D7 | apron 上有两块高出 5.0 m 的 34.41 m² 平台，和地面分量的平面距离为 0，高差 5 m | 和 source.json limits[1]「Upper access is still missing」相符。记为不可达的高处平台，不是断点 |

**结论**：
- G 的冻结基线必须由 LY-001 明确是 bce3211 还是 cad338b（或更新的版本）。
- 若取 cad338b，就不再把 G7 作为断点列出，改为一条带 SHA 的已通边：yong-road-link-near 456a7dd5…，receiver e5baa0df…。同时网络必须至少分成「冷开」和「terrain 章」两个加载状态分别交付。
- 两种情况下，其余断点（G2–G6、G8、G13）和禁用边都没有变化。
