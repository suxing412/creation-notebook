# LY-041｜示范住宅地基与地坪适配：开工准备稿

状态：**开工准备**。G（LY-001/002/005/006/007/008/009/010）尚未冻结。本稿只读输入、实测、准备测试，**没有制作或修改任何交付几何**。基线是 lab `bce3211f818ee5a8bef1773539da70695ba37b17`，所有数字都在这个基线上测得。

## 1. 本项目标（任务池原文的要点）

- 从现有 44 院里选定一院，按它在城景里的实际底部，补必要的地脚或地坪差异件。
- 不碰 13 院片区，不移动原院矩阵，不增加院数；已有支持就复用；禁止用大底板盖住真实孔洞和道路。
- 验收：写明所选院 ID、源矩阵和底部三角；新增地脚只覆盖测得的缺口；旧孔洞、邻院和道路不被大底板盖住。

## 2. 选院建议：C02-010（A2）。最终由 LY-010 冻结

| 项 | 值 |
|---|---|
| 城景节点 | `C02-010`，title「住宅院落 24」，city-data.mjs:2322，`initial: true`，chapter `residential`，tier「推测」 |
| 原型 | `courtyard-A2`：远档 `assets/c02v/A2-LOD1-prototype.glb`（277e9e73…）；近档 `assets/c02v/A2-LOD0-prototype.glb`（19b05202…） |
| 源矩阵（glTF 列主序，C-alt） | `[1,0,0,0, 0,1,0,0, 0,0,1,0, 531,0,-818.45,1]`，来自 `data/far44/instances-calt.json`（c830b4e3…），`changedByCalt: true` |
| 原布局矩阵（对照） | 平移 `[537.17635,0,-817.45]`，来自 `instances-original.json`（a8545891…） |
| 地块世界范围 | x 522…540，z −830.45…−806.45（18 × 24 m = 432 m²）；院门在 x 527.5、z −806.45 |
| 城景剔除节点（excludeNodes） | `site_lot`、`site_neutral_lane`、`designed_hardpacked_activity_ground`，city-renderer.mjs:309 剔除，:346 要求全部命中 |

选它的理由：

- 它属于城景首页先介绍的南组 14 院（index.html:52）。`data/west/network.json` 有它的 `C02-010_door_approach` 门前连接，west-layer.mjs:58 把这条路画成样例路线。后续 LY-049 和 LY-082 可以直接用。
- A2 在北区研究里就是「生活院修订」（研究模型 `research-north13-court-A2`），适合 LY-044、045、047 的生活设施。
- 它离 13 院片区很远。`m-luoyang-residential-life` life-block 的 AABB 是 x 480…640、z −1060…−962，C02-010 地块和它没有交集。

排除的院：

- FROZEN-D08-M、E、NW、NE 四院的地块和 13 院片区 AABB 相交，相交面积分别为 432、432、1008、1008 m²。其余 D08 院紧挨这一片，也不选。
- C02-003、C02-012（TC03-2）有一处继承的悬空木件，见第 5 节。

备选院：C02-021（A2）。它不受 C-alt 影响，矩阵在两种布局下相同，落在 ground-retained 上，但没有已测的门前连接。

## 3. 核到的现有成果（文件 + SHA256）

| 文件 | SHA256 | 在城景中 |
|---|---|---|
| docs/cities/luoyang/assets/c02v/A2-LOD1-prototype.glb | 277e9e73e8f2d8b8e07ec828671d37cc7c9e3f1653dcebfe4290c51de412d85d | 加载，`assets[courtyard-A2].path`，city-data.mjs:88 |
| docs/cities/luoyang/assets/c02v/A2-LOD0-prototype.glb | 19b052022b2f6955e4a72f1a48280f7f8c229e11f001aa02ac95e357b890d9c7 | 近景加载，nearPath，city-data.mjs:109–111；focusCourtyard 在 city-renderer.mjs:616 |
| docs/cities/luoyang/assets/ground-atomic/south.glb | 4313826ddf5fbe0c0d8dcb4983d6cdbd647713d49faa1980cd34f587a3273a0e | 节点 `ground-south`（city-data.mjs:3609），`initial: false`，只在 terrain 章打开后加载 |
| docs/cities/luoyang/assets/ground-atomic/retained.glb | aed8b3d4cb12aeaddf5c696a8a86355b15b7cb4fc8ebd76cc364d23789d630cc | 同上，`ground-retained` |
| docs/cities/luoyang/assets/ground-atomic/network-ground-stitched.glb | fdfc3ce5c63305f79aa746b31c3be60f3d11a6acb75f190886124f2d3446db60 | 同上，原子三节点 |
| docs/cities/luoyang/assets/ground-atomic/D08.glb | 3ab933108b88c5c359fc7512d324e14f15157eaa54fb17f80f2adeb6c4626d9a | 同上，平移 [580,0,−960] |
| docs/cities/luoyang/data/far44/instances-calt.json | c830b4e37090da5e070156b7f6199f36c5d0191c339f5a9399f0becded50ff85 | 44 院矩阵来源（city-data nodes 的 sourceContract） |
| docs/cities/luoyang/data/far44/preflight-contract.json | 90dfa0774643b90d61f057aed726525cfe3e18647e897d3c90eb64fa79426d6b | 原型清单 |
| docs/cities/luoyang/data/west/ground-atomic-contract.json | bfc7fc83c3d8f34c79e9395532b74c324987b4dbf0c4342328b7581ebc2be584 | 地面组合合同 |
| docs/cities/luoyang/city-data.mjs | e4115705aeab28f2f6cc2635fbedfabf4158a08af9c626f6dd493ee27d430a1a | — |
| docs/cities/luoyang/city-renderer.mjs | fa0a8dcbfaa5f5f8bd410f3d2295d788f32480c4dab316dd291a561d40d026ca | — |
| docs/model-library/updates/m-courtyard-family/files/A2-LOD0-C2.glb / A2-LOD1-C2.glb | e9981a07… / f3f31774… | 不加载。C2 只更新 UV，待审 |

全部条目见 `inputs.json`。

## 4. 改 / 不改范围

- **改**：本席位只写 `workpacks/LY-041/`。按实测结果，**不新造地脚或地坪几何**，理由见第 5 节。交付物是复用判定、绑定 SHA 的安装说明（C02-010 + ground-south 同时加载）和可重跑检查器。
- **不改**：C02-010 矩阵；A2 原型的任何节点；ground-south 和其他地面文件；city-data.mjs；p-luoyang.asset.json；lab/data/*；13 院片区；邻院 C02-009（x 499…517）、C02-011（x 545…563）、C02-006（路北）；门前 lane 和道路，它们归 LY-049 和 LY-082。
- 如果 LY-045 以后要在院内开厕孔，ground-south 必须开孔。这个文件是单节点、96,796 三角，覆盖整个南组 14 院。开孔的写入权要 LY-006 判定，本席位不预先切地面。

## 5. 实测（脚本都在本目录，可重跑）

脚本：

- `measure_footing.py`：44 院全量。0.1 m 栅格高度场加边线撒点，`grid_m=0.1`，容差 5 mm。结果在 `measure-footing-44.json`。
- `measure_c02010_exact.py`：C02-010 精确检查。底部顶点逐个对地面三角做点在三角形内判定，不用栅格。结果在 `measure-C02-010-exact.json`。
- `list_bottom_tris.py`：列出底部三角。结果在 `bottom-tris-A2-LOD{0,1}.json`。
- `check_footing.py`：判定器，带负例，见 test-plan。

### 5.1 地面打开（terrain 章）时：C02-010 没有缺口

- 地块 432 m² 全部由 **ground-south 一个文件**覆盖，覆盖率 1.0。顶面全部在 y = 0.200，最小值和最大值都是 0.2。没有多文件叠层（multi = 0），也没有无地面的格（noGround = 0）。
- 院内保留构件中，底部落在地块顶面加 5 cm 以内的足迹格有 9,933 个，约 99.3 m²。LOD0 和 LOD1 都是：**悬空（>5 mm）0、埋入（<−5 mm）0**。
- 精确检查：底部顶点 54 个（台基 20、木作 8、土墙 26），与地面的间隙全部为 **0.000000 m**，全部由 ground-south 承托。按 C-alt 矩阵和原布局矩阵各测一次，结果相同。
- 底部三角在 LOD0 和 LOD1 中相同：
  - `architecture_C_floor_plinth.001`：底面 12 三角，62.352 m²
  - `architecture_C_whitebox_earth_wall.001`：底面 14 三角，29.300 m²
  - `architecture_C_plain_timber.001`：底面 4 三角，0.154 m²（只有落地的两根柱）
  - 屋面没有落地三角。
  - 没有任何三角低于 y 0.2。
- 地块内没有孔：ground-south 在地块内只有上下两层水平面（570 上 / 570 下，y 0.2 / 0.0），没有竖面；site_lot 是 12 三角的闭合盒。44 院原型都不含井孔或厕孔，所以不存在会被大底板盖住的旧孔洞。

**结论**：「已有支持就复用」成立。现有 ground-south 已经承托 C02-010 的全部落地构件，任何新增地脚或底板都没有可覆盖的缺口。`check_footing.py` 规定新件只能落在实测缺口内（C3），现在缺口格数为 0，所以任何新件都会被判失败。

### 5.2 真实缺口（带数字）

1. **默认视图和近景下院落没有地面**：
   - 地面四节点都是 `initial: false`（city-data.mjs:3609 等）。初始加载集合由 city-renderer.mjs:221 按 `initial !== false` 筛出。focusCourtyard（:616–623）只加入该院本身。
   - 因此首页和「走进住宅街区」近景下，C02-010 的 9,876 个足迹格（另一栅格原点下的计数）**全部无地面**，lotCoverage 为 0，底部 y 0.2 下面是空的。见 `check-C02-010-initial-load-no-terrain.json`。
   - 只有用户打开过「道路与地面」章，地面才会留在场景里（:603 是并集）。
   - 这是城景加载配置的缺口，不是几何缺口。修法：在 LY-100 的城景合并时，把 ground-south 和 C02-010 写成同进同出，或者让 residential 章的 loadNodeIds 带上地面。本席位只提出建议，不改 city-data。
2. **院坪基准差 15 mm**：被剔除的 `designed_hardpacked_activity_ground` 顶面是 0.215；城景里同一位置是 ground-south 的 0.200，差 0.015–0.0153 m，面积约 94.4 m²。LY-044、045、047 放灶、厕和棚时必须以 0.200 为准，不能照原型的 0.215 放，否则会悬空 15 mm。这个差值需要 LY-005 写进高程契约。
3. **门前 lane 有浅凹**：被剔除的 `site_neutral_lane` 是平的，顶面 0.2。城景 lane 带（z −806.45…−802.45）的实际地面：
   - 范围 0.175–0.205 m；
   - 在 z ≈ −803.7 处有一条横跨 18 m、比 0.2 低 25 mm 的浅槽；
   - 剖面：出院门后约 1.9 m 是平的（0.200）；随后约 0.85 m 内降到 0.175；再在约 1.25 m 内升到 0.205，到达 lane 外缘 z −802.45。
   - 这一段归 LY-049 和 LY-082，本席位只交数字。
4. **44 院全量旁证**：
   - 44 院中，42 院在 0.1 m 栅格下足迹悬空和埋入均为 0。
   - C02-003 和 C02-012（TC03-2）各有 10 格（0.1 m²）悬空 0.03 m。来源是 `architecture_C_plain_timber.001` 在局部 x 23.35、z −22.85…−21.95 处的木件，底面 0.23。即使在原型里，它也比被剔除的 side_passage 顶面 0.212 高 0.018 m，是原型继承的问题，不归本席位。
   - 44 个地块两两之间没有重叠（lotOverlaps 为空）。

### 5.3 Blender 独立复核（不用 glbio.py）

- 脚本 `blender_crosscheck.py`（SHA256 c7a1d6ed0346b06f54f6a8bcefe5c2ee135c459a68276b0f26f45b02b93a64b2）。Blender 5.2.1 LTS 用自带 glTF 导入器读 A2-LOD0、A2-LOD1 和 ground-south，按 C-alt 平移放置。对每个底部顶点（世界 y 在最低保留顶点 +5 mm 以内）向下射线测到 ground-south 的距离。
- 结果在 `blender-crosscheck-C02-010.json`（SHA256 8f6e4c0e4a4719c74333f9435e3f9926e083813ca4f32dd896fa15ec96cbf7d1），退出码 0。
- 保留网格 4 个（台基、木作、屋面、土墙），剔除网格 3 个，和 excludeNodes 一致。世界最低 y = 0.19999993。
- 底部顶点按 Blender 的拆分法线计数，比 glbio 的唯一顶点多：台基 72、木作 24、土墙 84。无地面 0；间隙在 −2.4e−7 到 0 m 之间，也就是浮点精度内为 0。LOD0 和 LOD1 相同。
- 地块按 0.5 m 采样 1,728 点，无地面 0，顶面 0.199999–0.200001。
- 和 5.1 的 glbio 结果一致：两条独立的读取路径都得出「没有缺口」。

### 5.4 局限

- 测量基于表面高度场：0.1 m 格心采样加边线撒点。没有做实体碰撞，也没有做 GPU 或浏览器实测。
- 格数会随栅格原点漂移：同一院在两个脚本里分别是 9,933 和 9,876 格。判定只依据「悬空、埋入、无地面三类格数是否为 0」。
- 没有评估结构承载，也没有评估地基的真实埋深。

## 6. 证据与未知（四类）

- **原始考古 / 原文**：这一院**没有**对应的东汉宅址实测。city-data 原文写的是「住宅形态与落位为设计研究，尚无对应古代宅址的实测定位」。
- **异地异期类比**：本稿**没有使用**任何类比。如果以后要给地脚埋深或夯土台基找依据，需要 LY-002 判定可用材料。北魏洛阳、西汉长安、四川画像砖都不能直接当约 180 年洛阳的事实。
- **C 工程设计**：
  - 地面基准 y 0.200，南区地面板厚 0.2 m；
  - 墙、台基、柱直接坐在地面顶面上，没有埋入式地脚；
  - 院坪 0.215；
  - lane 浅槽 0.175。
  - 以上全部是 C 设计，不是考古高程。
- **未知**：东汉洛阳普通宅院的台基做法、埋深、院面排水坡向；lane 浅槽的设计意图（排水还是建模残差）。

需要分开说清的五件事：

| 事项 | 状态 |
|---|---|
| 模型能读取 | 是，已实测回读 |
| 局部通行通过 | 本席位没有测 |
| 已入城 | 是，现在就在城景里，但默认不带地面 |
| 真实结构安全 | 没有评估 |
| 历史复原成立 | 不成立，属 C 设计 |
