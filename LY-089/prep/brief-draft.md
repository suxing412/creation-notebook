# LY-089｜地形支承差异片与边缘闭合 · 开工准备稿（第 2 轮，2026-11-06）

席位类型：补件/修订。依赖：G（LY-001/002/005/006/007/008/009/010）和 LY-081。
当前阶段：**开工准备**。G 还没冻结，原因是 LY-010 没有交付：workpacks 下根本没有 LY-010 目录。LY-081 也还停在 prep。所以本稿只读输入、实测缺口、准备测试。**没有制作或修改任何交付几何**。第 1 轮的稿件原样存档在 `qa/r1-archive/`。

写入范围：只写了 `workpacks/LY-089/prep/`。lab 仓库只读：
- 第 2 轮开工前后，`git status --porcelain` 的哈希都是 `fbc8443a…`，HEAD 都是 `bce3211`（`qa/lab-status-before-r2.txt`、`qa/lab-status-after-r2.txt`）。
- 第 1 轮的两份状态文件记的是 `6c985f6a…`，和现在不同。原因是 lab 里原先有三个未提交的修改（含 `lab/data/assets.json`），在两轮之间被别处还原了。LY-006 的 openItems 也记了这件事。本席位没有写过 lab。
- 没有做 git 写操作，没有运行 `build_assets.py`。
- 第 2 轮新写的脚本和 Blender 一样，只读 GLB。

## 0 第 2 轮相对第 1 轮变了什么

1. **G 席位的状态**：LY-001、002、005、006、007、008、009 都已「交付完成」，`status.json` 的 SHA 记在 inputs.json。**LY-010 不存在**，LY-081 仍在 prep。所以 G 未冻结，本席位不能开工。
2. **LY-006 registry v1 已冻结，三件事和本席位直接相关**：
   - LY-089 **没有预分配写入区**（`writeZones: []`），要走认领协议（`claimProtocol: true`）：认领区必须通过 `check_registry` 的写入区和包络互检才生效。
   - 四块原子地面，以及市肆、仓储两块自带底板，**都归 LY-090**：「only LY-090 may emit a diff/replacement of this file」。
   - 新的地坪片必须命名为 `gp:<seat>:<name>`，并且落在该席位的写入区内。本席位的构件是 `G089-support-patches`（fixed）。本席位消费 133 个冻结端口（`qa/consumed-ports-ly006v1.json`）。
   第 1 轮的 G-3（市肆底板）和 G-4（仓储底板）因此不归 LY-089。G-1 和 G-2（墙脚）的端口 steward 是 LY-020。
3. **新测出三处地面内部的待闭合接缝 G-7/G-8/G-9**：这是本席位最具体的「最小差异片」候选。数字与 LY-081 prep 报的一致（3.761 m、4.292 m、4–62 mm），但这是本席位独立测的，用自己的 numpy 脚本，没有用 LY-081 的 Blender 脚本。
4. **复现**：
   - 第 1 轮的 `measure_support.py` 重跑结果，除 `seconds` 字段外逐值相同（`qa/rerun-r2/support-bce3211.json`）。
   - `ground_fingerprint.py` 重跑逐字节相同（`c3078dcc…`）。
   - 新脚本 `measure_seams.py` 跑两次，输出 SHA 相同（`2aa95391…`）。
5. **cad338b 漂移**：bce3211 到 cad338b 之间，四块地面 GLB 的 blob id 完全相同，`data/west/` 也没有改动（`git diff --quiet` 通过）。所以 G-7/G-8/G-9 在 cad338b 上同样成立。city-data.mjs 有改动：ground-retained 在 cad338b 改成了 `initial:true`。

## 1 本项目标（任务池原文）

在**批准区域内**、实际**未被支持**的安装边界上，生成**最小实体**地形差异片，并写接边记录。
- 保留已有的高程和网格，不用整城大平面填空。
- 考古地形未知的地方不造起伏细节，越界就停。
- 验收：
  - 新片只落在批准缺口内；
  - 实际实体支持和边缘接触能重算；
  - 原地面的高程和孔洞保持不变；
  - 不批量把全城盖平。

## 2 输入版本

- 基线 `bce3211f818ee5a8bef1773539da70695ba37b17`（lab HEAD，也是 LY-001 锁定的快照）。origin/main 在 `cad338b`，见第 0 节第 5 条。
- 坐标和高程沿用 LY-005 契约（`coordinate-contract.json` `b6d7fe9d…`）：米制，+X 东、+Y 上、−Z 北，world = N·S·v。LY-081 用的平面坐标是 (x, y) = (X, −Z)。
- 读取 GLB、做竖直射线：按路径导入 LY-005 的 `glbio.py`（`2acd023b…`）和 `vray.py`（`ab4984f2…`），没有复制。
- 所有权和端口：LY-006 registry v1。`ownership.json` `ecbbbcf5…`，`seats.json` `a1426412…`，`zones.json` `6b3595ac…`，`seams.json` `ca4d81f8…`，`ports.json` `28bcfb68…`。
- `inputs.json` 共 81 条：第 1 轮 59 条全部重算了 SHA，第 2 轮新增 22 条。第 1 轮里只有 `lab/data/assets.json` 的磁盘字节变了，原因见上：别处还原了未提交修改，文件不在城景加载链上。

## 3 现有成果（只读核对）

### 3.1 城景实际加载的四块原子地面

四块都属于 terrain 章。在 bce3211 时都是 `initial:false`，所有权都归 LY-090。

| 节点 | 文件 | SHA256 | 三角 | 顶面积 m² |
|---|---|---|---|---|
| ground-network-ground-stitched（C_stitch_primary / west / patch） | assets/ground-atomic/network-ground-stitched.glb | fdfc3ce5c63305f79aa746b31c3be60f3d11a6acb75f190886124f2d3446db60 | 128342 | 65325.1 |
| ground-retained | assets/ground-atomic/retained.glb | aed8b3d4cb12aeaddf5c696a8a86355b15b7cb4fc8ebd76cc364d23789d630cc | 21192 | 84528.0 |
| ground-south | assets/ground-atomic/south.glb | 4313826ddf5fbe0c0d8dcb4983d6cdbd647713d49faa1980cd34f587a3273a0e | 96796 | 32704.7 |
| ground-D08（平移 580,0,−960） | assets/ground-atomic/D08.glb | 3ab933108b88c5c359fc7512d324e14f15157eaa54fb17f80f2adeb6c4626d9a | 140 | 10320.0 |

四块合计顶面约 192,878 m²。

加载链：
- `city-data.mjs` 的 terrain 章 `loadNodeIds`，L4027–4041（第 2 轮复核过行号）；
- `city-renderer.mjs` 的 `loadAsset()`（L286，excludeNodes 在 L309）、`rebuild()`（L409，setMatrixAt 在 L431）、`focusChapter()`（L595）。

`data/west/road-plan.json`（`9792f217…`）记录了第 4 节 G-7 和 G-8 这两条「final seam pending」切口。它**不被当前城景入口加载**，只被 v1 存档入口的 `v1/road-layer.mjs` L17 读取。

### 3.2 已经完整支承、判为复用、不造片：住宅 44 院

第 1 轮的结论，第 2 轮重跑后不变：
- 底面 6,354.54 m² 中，6,354.24 m² 贴合地面（|Δ| ≤ 5 mm）；没有地面的面积为 0。
- 足迹边界 12,500.4 m 中，12,489.0 m 与地面同高。
- LOD1 和 LOD0 六种原型结果都一样。
- 用 Blender BVH 和 numpy 两种方法复核，一致。

LY-006 把这 44 院的 `ground-base` 端口（44 个，status 为 imported from LY-005）列为本席位的消费端口。本席位对它们不需要造任何片。

### 3.3 不属于本席位的现有成果（只记录，不动）

- 雍门接街：f28d650/b70c495 由原负责人做，是保护件。
- 市肆底板 `market-cluster:sample_ground` 和仓储底板 `granary-city:original_city_ground_preserved`：归 LY-090。
- 城垣墙脚的 floor 和 wall-end 端口：steward 是 LY-020。
- 宫墙水道三段：LY-086，不在城中。

## 4 实测缺口（全部可以重算）

### 4.1 第 1 轮缺口（重跑后不变）

| # | 缺口 | 实测数字 | 第 2 轮归属（按 LY-006 v1） |
|---|---|---|---|
| G-0 | 默认首屏没有加载地面 | bce3211 时四块地面全是 initial:false；cad338b 已把 retained 改为 true | 加载策略，归 LY-100/LY-010 |
| G-1 | 城垣 A 段 10 段的墙脚 | 底 0.17，足迹 84,761 m²，100% 没有地面；200 m 内也没有地面 | 墙脚端口的 steward 是 LY-020；整圈铺地 = 被禁止的整城填平 |
| G-2 | direct 08/09 墙 | 足迹 13,804 m²，其中 13,038 m² 没有地面；另有 766.2 m² 被地面带（顶 0.20）伸进墙脚 3 cm，属正体积侵入 | LY-020 做接触分类；本席位不盖平 |
| G-3 | 市肆自带底板 | 60×44×0.2 m 闭合；周长 208 m 里只有 4 m 接上 0.21 的路 | **底板归 LY-090**；外街接点归 LY-083（S-MARKET-STREET） |
| G-4 | 仓储自带底板 | 72×52×0.2 m；248/248 个探针 200 m 内没有地面 | **底板归 LY-090**；东北路归 LY-039/040/084 |
| G-5 | 雍门地坪 | 底面 539.8 m²，下方无地面 | 保护件 |
| G-6 | 四块地面外露的顶面边界 | 合计 17,832 m；1 mm 焊接下，network 有 10 个、retained 有 23 个非流形边 | 只做基线 |

### 4.2 第 2 轮新测：地面内部待闭合的接缝（`scripts/measure_seams.py`）

方法：
- 取四块地面的顶面三角（法向 y ≥ 0.94），按 LY-005 frames 的矩阵摆放。
- 跨缝方向打竖直射线扫描线：两条路缝的步长 1 cm，线距 0.25 m；裂缝的步长 1 mm，线距 0.1 m。
- 只统计**两侧都有地面夹着**的空段。
- 另外按 1 mm 焊接列出窗口内的顶面边界边，取精确端点。

| # | 位置（world） | 实测 | 两侧 | 与 LY-081 prep 对照 |
|---|---|---|---|---|
| **G-7 SEAM-C5** | road_west_south_link_B_C_5 西端；X 404.000→407.761，Z −492.796…−486.796（路宽 6 m）。北侧 Z −488…−486.796 处西岸退到 X 403.000，空隙呈 L 形 | 24/31 条扫描线有夹空；空长 3.761 m（精确边距），北侧 1.204 m 宽的一段为 4.761 m；多边形面积 **23.770 m²**（扫描估算 23.62） | 西：C_stitch_west 顶 0.20（板底 0.00）；东：C_stitch_primary 顶 0.21（板底 0.16）；**dy = +0.01 m** | 3.761 m，一致 |
| **G-8 SEAM-C1** | road_west_spine_B_C_1 北端；Z −476.000→−471.684/−471.708，X 386.590…392.590（6 m） | 24/53 条扫描线有夹空；空长 4.292–4.316 m；四边形面积 **25.824 m²**（扫描估算 25.86） | 北：C_stitch_west 0.20；南：C_stitch_primary 0.21；dy = +0.01 m | 4.292 m，一致 |
| **G-9 CRACK-STITCH** | C_stitch_primary 内部；X 397.937…398.015，Z −1849.94…−1845.76（西脊与中横路相交处） | 41/56 条扫描线有夹空；宽 3–62 mm（Z −1845.9 处 3 mm，Z −1849.9 处 62 mm）；楔形，长 4.18 m；面积约 **0.13 m²** | 两侧都是 C_stitch_primary 0.21；dy = 0 | 4–62 mm、长约 4.2 m，一致 |

`road-plan.json` 对 G-7 和 G-8 的记录：cut `existing_route_0/1`，「reuse old corridor, no duplicate road plane; final seam pending」。也就是说，新 C 路面在旧走廊处截断以免重面，接缝留待以后做，一直没做。G-9 在 road-plan 里没有记录，看起来是缝合误差留下的楔形缺口，属于 C 工程缺陷，没有任何历史含义。

**对照组**（在内存里做，没有导出任何几何）：
- 正例：用一个平板正好填满实测的空隙框，三处的夹空扫描线都降为 0。
- 负例：把同一块板平移 0.5 m，仍有 4/24/41 条线留空。
- 结论：检测器能看出闭合，也不会被错位的片骗过（`controls.pass = true`）。

**邻接检查**（`scripts/seam_neighbours.py`，空隙框外扩 2 m，只比到包围盒级）：
- 三个框只和 ground-network-ground-stitched 的包围盒相交，没有碰到别的城市节点；
- 与 LY-006 的 173 个写入/切孔区和 11 个场地包络都**不相交**。

所以这三处不压在任何其他席位的写入区里，可以作为认领协议的候选。负例：在市肆处、C02-010 处各放一个测试框，能分别检出 LY-022/025 和 LY-041/042/045/046 的写入区以及 S-MARKET/S-COURT 包络（`qa/neg/neg-neighbours.json`）。

规模：G-7 + G-8 + G-9 合计约 49.72 m²，是四块地面顶面合计的 **0.026%**。

### 4.3 非缺口

- 44 院；
- TC03 院内抬高到 0.23 的小块；
- 雍门门体在地坪上的支承（100%）。
- 负例：去掉 D08 后，FROZEN-D08 两院 100% 无地面，说明测量对缺地面是敏感的。

## 5 改 / 不改范围（制作期，前提是 LY-010 放行，且认领通过 LY-006 check_registry）

**改（候选）**：

1. `gp:LY-089:seam-c5`：L 形多边形，6 个顶点。
   - 顶点：(404.000,−492.796) (407.761,−492.796) (407.761,−486.796) (403.000,−486.796) (403.000,−488.000) (404.000,−488.000)。
   - 顶面：从西岸 0.20 线性升到东岸 0.21，坡度 0.27%。
   - 底面：0.16。这是 C 取值，按东侧 primary 板底。
   - 南北两条边是暴露边，与道路其余段相同，要在接边记录里声明。
2. `gp:LY-089:seam-c1`：四边形。
   - 顶点：(386.5904,−476.000) (392.5904,−476.000) (392.5904,−471.6843) (386.5904,−471.7077)。
   - 顶面：从北侧 0.20 线性升到南侧 0.21；底面 0.16。
3. G-9 裂缝 0.13 m² 有两种做法：
   - 做成 `gp:LY-089:crack-stitch`：一块共面 0.21 的楔形补片，按精确边界边贴合；
   - 或者作为切孔/替换请求交 LY-090，在原文件里缝合。原文件归 LY-090，后一种更干净。由 LY-006 和 LY-090 裁定。
4. 只新增一个 overlay GLB（local-origin，单位节点），附接边记录：每条边对应哪个 portId 或哪条原地面边界边、高差多少、按什么分类。

**不改**：
- 四块原地面的文件、矩阵、材质、孔洞（归 LY-090）；
- 墙、门、院、市、仓的几何；
- city-data.mjs、项目卡（走 LY-100）；
- 雍门接街；
- 宫墙水道；
- LY-090 登记的四个切孔（`cut:LY-025/045/053/086`）。
- G-1 到 G-4 不由本席位造片，除非 LY-010 明确放行，并且 LY-006 v2 把相应区域判给 LY-089。

## 6 证据与未知

- **原始考古 / 原文**：无。LY-002 给 F-ground-road 族绑定的事实只有两条：E-G09（二十四街、街一亭等）和 E-H03（水系未定位）。都不提供地面高程或接缝形态。
- **异地异期类比**：无，也不使用。LY-002 的禁用项：
  - X23：不得把陆机《洛阳记》「城中大道三分、两边土墙高四尺余」当作东汉街道定制；
  - X15：不得把今洛河当作约 180 年的水系。
- **C 工程设计**：0.20/0.21 两档顶高、0.16/0.00 板底、6 m 路宽、0.27% 过渡坡，都是既有 C 模型的工程值（LY-005 E1–E4），不是考古高程。
- **未知**：东汉洛阳的真实地表起伏、墙脚两侧的地形、古河渠位置、绝对高程、真北。因此差异片只做平板或线性过渡的闭合，不表达地形。
- **五件事分开说**：本稿只证明「模型能读取」和「竖直射线意义上的支承与闭合数」。
  - 「局部通行通过」由 LY-081 判；
  - 「已入城」由 LY-100 判；
  - 结构安全、历史复原都不声称。
  - 没有做实体碰撞或身体扫掠，也没有浏览器 / GPU 实测。

## 7 测量脚本与重算

```
P=D:/GitHub/creation-notebook-workpacks; L5=$P/LY-005; L6=$P/LY-006; LAB=D:/GitHub/creation-notebook-lab; S=$P/LY-089/prep/scripts
# 第 1 轮（第 2 轮已重跑，见 qa/rerun-r2/）
python -I $S/measure_support.py $L5 $LAB qa/support-bce3211.json
python -I $S/ground_fingerprint.py $L5 $LAB qa/ground-fingerprint-bce3211.json
python -I $S/measure_support.py $L5 $LAB qa/neg-drop-D08.json --drop ground-D08 --only FROZEN-D08-S1,FROZEN-D08-NW,C02-018
D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P $S/bl_crosscheck.py -- $L5 $LAB qa/bl-crosscheck.json
# 第 2 轮
python -I $S/measure_seams.py $L5 $LAB qa/seams-bce3211.json                       # G-7/G-8/G-9 + 正负对照
python -I $S/seam_neighbours.py $L5 $L6 qa/seams-bce3211.json qa/seam-neighbours-bce3211.json 2
python -I $S/consumed_ports.py $L6 qa/consumed-ports-ly006v1.json                  # 133 个消费端口
python -I $S/make_inputs_r2.py $LAB $P inputs.json                                  # 重算 59 条 + 新增 22 条
```

| 文件 | SHA256 |
|---|---|
| scripts/measure_support.py | 306692d4ad57b492e6eec017e8606b6c25aee7c4891b0e6e2762a8aa4bf5ab37 |
| scripts/ground_fingerprint.py | 99a6241c8de4d7826e57c5f65c0043cf09169c2cb05ddcf460aa55ab34d089f9 |
| scripts/measure_seams.py | 2bc69cfc5c402908107ed4daa2b385ba7f38d49284c545aa701390281b7d81c5 |
| scripts/seam_neighbours.py | fea2b52f865dde957f52f2fa09766071d0f027de8724747f4aa4ea1715445c8b |
| scripts/consumed_ports.py | 85c8425412ffe947b33b85f548034a7cbf8f2045bf1db45795303c42ee0da48d |
| qa/support-bce3211.json | 3b5c786c6e0ca9294f4014cfd8b87b1882d42030970a70b7c328a18fd5fc09c1（重跑除 seconds 外逐值相同） |
| qa/ground-fingerprint-bce3211.json | c3078dcce04b0d77e63c1791d42f34634efbfab65c6372fd1ae330564a53ce37（重跑逐字节相同） |
| qa/seams-bce3211.json | 2aa9539146dc9819c47f38446a253c004d274638a8d83cefd52c118a2450645d（重跑逐字节相同） |
| qa/seam-neighbours-bce3211.json | 0637b1cb3f2fbcd3fc7e3d945044716d8ded86c11078fdeeb79c1172d80779ac |
| qa/consumed-ports-ly006v1.json | 679abecffb5f66b317e8c60f7da28f05e95c3984d89110a34672a51693d1bb15 |
| qa/bl-crosscheck.json | f9449080ed8a26c81c3b73d09629d59f4062c6647a3c9f8b5aa1522059344310 |

## 8 开工前还缺什么

- **LY-010**（不存在）：放行区域清单。一个缺口都没批，所以本席位不能造任何片。
- **LY-006 认领**：G-7、G-8、G-9 要按认领协议提交写入区，由 `check_registry.py` 互检；同时要 LY-090 确认，overlay 不算改它的文件。若 LY-090 更愿意在原文件里缝合，本席位就只交测量和接边记录。
- **LY-081**（prep）：可达网络最终版。G-7、G-8 闭合后，C_5 和 C_1 能否并入主分量，要 LY-081 重算。
- **私密源包**：四块原子地面的 .blend 或生成器不在仓库。它们只用于解释接缝和裂缝是怎么来的。差异片是新的 overlay，接边几何已经从 GLB 精确取出，所以可以「**从 GLB 重建**」。原材质节点图拿不到：材质按 LY-007 的 earth/path 语义新建，或沿用 GLB 里的 PBR 参数，不能说成找回了原件。
