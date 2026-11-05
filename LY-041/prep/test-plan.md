# LY-041 测试计划（制作期直接跑）

依据「本项验收」：

- 所选院 ID、源矩阵和底部三角写明；
- 新增地脚只覆盖测得的缺口；
- 旧孔洞、邻院和道路不被大底板盖住。

全部命令只读 lab 仓库，输出只写 `workpacks/LY-041/`。
`$LAB = D:/GitHub/creation-notebook-lab`，脚本目录 `workpacks/LY-041/prep/`（制作期复制到 `qa/`）。

## 0. 前置门槛（不满足就停）

| ID | 检查 | 通过条件 |
|---|---|---|
| T0.1 | G 已冻结 | LY-001、002、005、006、007、008、009、010 在任务板上都是「交付完成」 |
| T0.2 | LY-010 选院 | 冻结表写明示范院 ID（建议 C02-010）和布局（calt 或 original）。若与本稿不同，用新 ID 重跑 T1 到 T4，并重写 BASELINE |
| T0.3 | 基线重核 | 最新 main 上以下 SHA 与下表一致。不一致就整套重测，不沿用本稿数字 |

**T0.3 需比对的 SHA**：

| 文件 | SHA256 |
|---|---|
| A2-LOD1-prototype.glb | 277e9e73e8f2d8b8e07ec828671d37cc7c9e3f1653dcebfe4290c51de412d85d |
| A2-LOD0-prototype.glb | 19b052022b2f6955e4a72f1a48280f7f8c229e11f001aa02ac95e357b890d9c7 |
| ground-atomic/south.glb | 4313826ddf5fbe0c0d8dcb4983d6cdbd647713d49faa1980cd34f587a3273a0e |
| retained.glb | aed8b3d4cb12aeaddf5c696a8a86355b15b7cb4fc8ebd76cc364d23789d630cc |
| network-ground-stitched.glb | fdfc3ce5c63305f79aa746b31c3be60f3d11a6acb75f190886124f2d3446db60 |
| D08.glb | 3ab933108b88c5c359fc7512d324e14f15157eaa54fb17f80f2adeb6c4626d9a |
| instances-calt.json | c830b4e37090da5e070156b7f6199f36c5d0191c339f5a9399f0becded50ff85 |
| city-data.mjs | e4115705aeab28f2f6cc2635fbedfabf4158a08af9c626f6dd493ee27d430a1a |

如果 LY-007 或 LY-010 选用 C2 修订：

- A2-LOD0-C2 是 e9981a07…，A2-LOD1-C2 是 f3f31774…；
- 在 `check_footing.py` 的 VAR 里换成这两个路径，再全部重跑。

## 1. 身份与矩阵（验收第 1 条）

- **T1.1 矩阵不变**
  - 命令：`python check_footing.py --lab $LAB --id C02-010 --out qa/check-calt.json`
  - 正例：`C4_matrix_unchanged.pass = true`，矩阵为 `[1,0,0,0, 0,1,0,0, 0,0,1,0, 531,0,-818.45,1]`，容差 1e-9。
  - 负例：`--selftest` 中的 `neg_matrix_shift_0.1m` 必须失败。
- **T1.2 底部三角清单可复现**
  - 命令：`python list_bottom_tris.py <A2-LOD0|LOD1> qa/bottom-tris-LOD{0,1}.json site_lot,site_neutral_lane,designed_hardpacked_activity_ground`
  - 结果必须与 prep 的 `bottom-tris-A2-LOD{0,1}.json` 逐项相同：

    | 节点 | 底面三角 | 面积 |
    |---|---|---|
    | 台基 | 12 | 62.352 m² |
    | 土墙 | 14 | 29.300 m² |
    | 木作 | 4 | 0.154 m² |
    | 屋面 | 0 | — |

  - 每个节点 `trisBelowBase` 都为 0。
- **T1.3 院数与位置**
  - city-data `nodes` 中 chapter 为 residential 的节点仍是 44 个；
  - 44 个矩阵与 `instances-calt.json` 逐个相同；
  - 不新增 `courtyard-*` 资产。
  - 用 node 动态 import city-data.mjs 计数并比对。

## 2. 支持与缺口（验收第 2 条）

- **T2.1 正例：现有地面已承托**
  - 命令同 T1.1。
  - LOD0 和 LOD1 的 `C1_footprint_contact` 都满足 floating = 0、buried = 0、noGround = 0（容差 5 mm）。
  - `C2_lot_single_continuous_ground`：lotCoverage = 1.0，承托方只有 `ground-south`。
- **T2.2 精确复核**
  - 命令：`python measure_c02010_exact.py $LAB qa/exact.json C02-010`
  - 每个保留节点的 gap_min 和 gap_max 绝对值都 ≤ 1e-6 m，verticesWithoutGround = 0；
  - 地块 1,813 个采样点全部有地面，groundTop 为 0.2。
- **T2.3 自检负例**
  - 命令：`python check_footing.py --lab $LAB --id C02-010 --selftest --out qa/selftest.json`
  - `allBehaved = true`，下列五项都要按预期失败：

    | 负例 | 预期 |
    |---|---|
    | 地面抬高 20 mm | 判埋入 |
    | 地面降低 20 mm | 判悬空 |
    | 去掉 ground-south | 判无支持 |
    | 32×32 m 大底板盖住地块、lane 和邻院 | C3 失败 |
    | 矩阵平移 0.1 m | C4 失败 |

- **T2.4 新件只覆盖缺口**
  - 只在 LY-005 或 LY-006 认定确有缺口、并要交几何时执行。
  - 命令：`python check_footing.py --lab $LAB --id C02-010 --candidate models/<件>-LOD{0,1,2}.glb`
  - `C3_candidate_only_on_measured_gap.outsideGapCells` 必须为 0，`onLaneOrRoadCells` 必须为 0。
  - 当前实测缺口格数为 0。所以只要提交任何新件，C3 就会失败，这是预期行为：结论是复用。
- **T2.5 默认加载缺口**
  - 命令：`check_footing.py --drop-ground` 四个地面全部去掉。
  - 必须报 noGround 等于足迹格数，lotCoverage 为 0。本稿实测 9,876 格、0.0。
  - 这一项用来证明「默认视图无地面」是真实缺口。修正属于 LY-100 的合并提案。
  - 合并后验收：在 city-data 中，加载 C02-010 近景时 ground-south 一并处于加载集合。按 city-renderer.mjs:221 和 :616 的逻辑静态推演。没有浏览器或 GPU 实测时写「未测」。

- **T2.6 Blender 独立复核**
  - 命令：`D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P blender_crosscheck.py -- $LAB qa/blender-crosscheck.json`
  - 正例：退出码 0，`pass = true`；LOD0 和 LOD1 的台基、木作、土墙都是 `noGround = 0`，|gap| ≤ 1e−5 m；地块 1,728 个采样点 `noGround = 0`，顶面 0.200 ± 1e−5。
  - 输出的 `sha` 段必须与 T0.3 表一致；不一致就停，按新 SHA 重测。
  - 制作期如果交了候选件，要把候选件也加进 BVH 复跑，确认原构件的底部间隙不变，即候选件没有改变原构件的支持对象。

## 3. 旧孔洞、邻院、道路不被封盖（验收第 3 条）

- **T3.1 地块内无孔**
  - ground-south 在地块 x 522…540、z −830.45…−806.45 内只有水平面：上 570、下 570，竖面 0，y 只取 {0, 0.2}。
  - 以后 LY-045 若要开孔，复跑时竖面数应大于 0，同时孔下不得出现 y 0.2 的上表面。这条负例留给 LY-045 复用。
- **T3.2 邻院**
  - 44 个地块的世界矩形两两重叠为 0（`measure_footing.py` 的 lotOverlaps 为空）。
  - 任何新件在 C02-009（x 499…517）、C02-011（x 545…563）、C02-006 地块内的格数为 0。由 C3 的 `outsideLotCells` 覆盖。
- **T3.3 道路 / lane**
  - lane 带 z −806.45…−802.45 原地面范围 0.175–0.205，浅槽在 z ≈ −803.7。
  - 任何 LY-041 新件在 lane 上的格数为 0（C3 的 `onLaneOrRoadCells`）。
  - ground-south 的 SHA 不变，即 4313826d…。
- **T3.4 13 院片区**
  - 选定院的地块和 life-block AABB（x 480…640、z −1060…−962）的交集为 0。C02-010 的交集为 0。

## 4. 安装与撤回（公共底线）

- **T4.1 安装**
  - assembly.json 只引用现有节点：C02-010 用 courtyard-A2（远档和近档），地面用 ground-south。
  - 不复制 GLB，矩阵只施加一次。
  - 输出节点到输入节点的映射为恒等，没有替换、隐藏或删除。
- **T4.2 撤回**
  - 撤回后 city-data 中 C02-010 节点逐字节等于 bce3211 版本；
  - ground-south 节点的 `initial` 恢复原值；
  - 44 院矩阵指纹不变。

## 5. 容差与范围声明（写进 qa 报告）

- 栅格 0.1 m 采样格心，加 h/2 边线撒点；接触容差 5 mm；落地构件判定带为地块顶面加 5 cm。
- 格数会随栅格原点漂移（9,933 和 9,876），判定只看三类异常格数是否为 0。
- 只做了表面高度场，不是实体碰撞穷尽；没有做连续人体通行（门前 lane 留给 LY-049）；没有做 GPU 或手机测试；没有做结构承载评估；不作考古高程声明。
