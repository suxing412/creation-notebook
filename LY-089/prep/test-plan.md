# LY-089 测试计划：地形支承差异片与边缘闭合（第 2 轮）

本计划对应任务池中本项的验收，共四条：
1. 新增片只落在批准缺口范围内；
2. 实际的实体支持和边缘接触可以重算；
3. 原地面的高程和孔洞保持不变；
4. 不批量把全城盖平。

所有检查到制作期才运行。运行前要做三件事：
- 把 `BASE` 改成 LY-001 或 LY-010 冻结的基线；
- 把 `APPROVED` 指向「LY-010 放行 + LY-006 认领通过」的缺口多边形文件。这个文件目前还没有；
- 把 `prep/scripts/` 整体搬到 `LY-089/source/`，并在 `qa/checks.json` 里记录 SHA。

第 1 轮的计划存档在 `qa/r1-archive/test-plan.r1.md`。本版保留它的 T1–T15，并新增针对三处接缝候选的 T16–T19。

## 0 绑定的 SHA（bce3211 基线；换基线就全部重算）

| 对象 | SHA256 |
|---|---|
| network-ground-stitched.glb | fdfc3ce5c63305f79aa746b31c3be60f3d11a6acb75f190886124f2d3446db60 |
| retained.glb | aed8b3d4cb12aeaddf5c696a8a86355b15b7cb4fc8ebd76cc364d23789d630cc |
| south.glb | 4313826ddf5fbe0c0d8dcb4983d6cdbd647713d49faa1980cd34f587a3273a0e |
| D08.glb | 3ab933108b88c5c359fc7512d324e14f15157eaa54fb17f80f2adeb6c4626d9a |
| LY-005 frames-bce3211.json | c0f846cbe2966526535c23358b1695b830e2ba2a191fd1758adc1256687ccba6 |
| LY-005 glbio.py / vray.py | 2acd023b5a3f4c32bf215273d44e2aa567a574759c7fa8b00e2ac210e2e2fb6b / ab4984f26dd298a6a848da0190aa8b9979e535e70299618d9fc69893e272eccd |
| LY-006 ownership / seats / zones / seams / ports | ecbbbcf5… / a1426412… / 6b3595ac… / ca4d81f8… / 28bcfb68…（全值见 inputs.json） |
| LY-008 ly_check.py | 39aaa491859e1a796080dd91ccabd1c47423cf7f9ef2af61c5f123b04b3dff4b |
| measure_support.py | 306692d4ad57b492e6eec017e8606b6c25aee7c4891b0e6e2762a8aa4bf5ab37 |
| ground_fingerprint.py | 99a6241c8de4d7826e57c5f65c0043cf09169c2cb05ddcf460aa55ab34d089f9 |
| measure_seams.py | 2bc69cfc5c402908107ed4daa2b385ba7f38d49284c545aa701390281b7d81c5 |
| seam_neighbours.py | fea2b52f865dde957f52f2fa09766071d0f027de8724747f4aa4ea1715445c8b |
| 基线 support-bce3211.json | 3b5c786c6e0ca9294f4014cfd8b87b1882d42030970a70b7c328a18fd5fc09c1（比较时忽略 `seconds`） |
| 基线 ground-fingerprint-bce3211.json | c3078dcce04b0d77e63c1791d42f34634efbfab65c6372fd1ae330564a53ce37 |
| 基线 seams-bce3211.json | 2aa9539146dc9819c47f38446a253c004d274638a8d83cefd52c118a2450645d |

被测差异片 `models/terrain-diff-*.glb` 的 SHA 在导出后写入，所有 T 项都要绑定这个 SHA。

## 1 前置门槛（任何一条不满足都判「阻断」，不进入制作）

- **P1：依赖已交付。** G（含 LY-010）和 LY-081 的 `status.json` 都写着「交付完成」。
  - 现状：LY-010 目录不存在，LY-081 只有 prep，**不满足**。
- **P2：缺口已批准、已认领。** `APPROVED` 里的每个多边形都要满足：
  - 有 LY-010 的放行编号；
  - 有 LY-006 认领通过的记录：写入区 ID 为 `LY-089:write:NNN`，`check_registry` 的写入区和包络互检结果为 0 相交；
  - 有 LY-090 的书面确认：overlay 不等于修改它的地面文件；
  - 片名符合 `gp:LY-089:<name>`；
  - 写明相邻端口或原地面边界边，以及各自的 C 高程。
  - 负例：多边形的 owner 是 LY-020、022、083、090 等其他席位，或者缺少放行编号，就拒绝制作。
- **P3：基线一致。** 基线 SHA 与第 0 节一致。
  - 若基线换成 cad338b 或更新版本，重跑 `measure_support.py`、`ground_fingerprint.py` 和 `measure_seams.py`。
  - 已知情况：cad338b 的四块地面 blob 与 bce3211 相同，所以 seams 的结果预计不变；但 support 要按新的节点集重跑，因为新增了北缘三院。

## 2 通用检查项（沿用第 1 轮）

| ID | 检查 | 正例（必须通过） | 负例（必须被判失败） | 容差 |
|---|---|---|---|---|
| T1 原件不变 | 四块地面 GLB 的字节 SHA，以及 `ground_fingerprint.py` 的 geometryHash、topBoundaryEdgeSetHash、topY_histogram、signedVolume，都与基线逐项相同 | 安装差异片前后都一致 | 把复制件某一点的 y 改 1 mm，geometryHash 必须变 | 逐字节；哈希按 1e-4 m 取整 |
| T2 只落在批准范围 | 差异片每个顶点的 XZ 都在 `APPROVED` 某个多边形内或边上 | 全部顶点通过 | ① 片整体外移 0.5 m；② 片超出多边形 1 m²；③ 用整城包围盒当片。三种都必须失败 | 1 mm |
| T3 不盖平全城 | 片的总顶面积 ≤ 批准多边形面积之和，并且 ≤ 四块地面顶面合计 192,878 m² 的 10% | 通过。现候选合计 49.72 m²，占 0.026% | 用城垣外包矩形生成的大平面（约 9.7 km²）必须失败 | 面积 1e-6 |
| T4 不造起伏 | 顶面高度只能取相邻端口或边的 C 高程，或在两侧之间线性过渡；法向 y ≥ cos 5° | 高度集合 ⊆ {两侧高程} ∪ 线性插值 | 加一个 +0.3 m 的鼓包，必须失败 | 1 mm |
| T5 实体闭合 | 1 mm 焊接后非流形边为 0、退化三角为 0；有符号体积 > 0，并且与「顶面积 × 平均厚度」相差 ≤ 0.1% | 通过 | 删掉一个侧面三角，必须失败 | 见左 |
| T6 不与原地面叠顶 | 片的顶面与四块原地面的顶面在 XZ 投影上正面积重叠为 0 | 通过 | 片向原地面多伸 0.2 m，必须失败 | 1e-7 m² |
| T7 保持孔洞 | 原地面每个内环的内部点上，片不提供顶面；LY-090 登记的四个切孔（cut:LY-025/045/053/086）也不能被片覆盖 | 通过 | 片盖住 network 某内环里的一点，必须失败 | 点采样 0.25 m |
| T8 支承重算 | `measure_support.py --extra-support <片节点>`：目标节点在批准范围内的 noGround → 0，contact 的 \|底 − 片顶\| ≤ 5 mm；范围外节点的 classes 与基线逐项相同 | 通过 | 片降 2 cm，必须判为 floating | 5 mm |
| T9 边缘接触 | 片的外缘每条边都要归到一个 portId 或一条原地面边界边，或者标成「暴露边（已声明）」；沿边每 1 m 一个探针，外移 0.1 / 0.5 m | 未声明的台阶为 0 | 片与地面之间留 5 cm 缝，探针必须报 void | 5 mm；台阶按声明值 ±1 mm |
| T10 撤回 | 去掉片节点后重跑 support 和 seams，结果与基线 JSON 逐项相同 | 通过 | 安装时改过原节点矩阵，撤回后漂移 > 0，必须失败 | 逐值 |
| T11 坐标契约 | 片为 local-origin，节点矩阵只绕 Y 旋转、缩放为 1、只施加一次（LY-005 R1–R7）；用 LY-005 的 `bl_roundtrip.py` 做往返 | 往返差 ≤ 7e-5 m | 缩放 1.001、施加两次、镜像，都必须被拦下 | 见 LY-005 |
| T12 文件规范 | 运行 LY-008 `ly_check.py glb`、`lodset`、`privacy`：单个 GLB ≤ 15,000,000 B，纹理内嵌，材质语义按 LY-007（earth/path），不得把 LOD0 复制改名冒充其他档；平板若只交一档，要写明理由 | ly_check 0 error | LY-008 自带的负例夹具 | — |
| T13 双法复核 | 用 Blender BVH（`bl_crosscheck.py`，点集加上片的边与中心）和 numpy 分别取片顶高度 | 一致 | — | 1e-4 m |
| T14 只读 | lab 的 `git status --porcelain` 哈希和 HEAD 在开工前后相同 | 通过 | — | 逐字节 |
| T15 合并前 | 由 LY-100 运行官方 `build_assets.py --check` 和 LY-008 的检查器；LY-089 本身不运行 `build_assets.py` | LY-100 报告通过 | — | — |

## 3 接缝专项检查（第 2 轮新增；只对已获批准的候选运行）

候选的精确几何来自 `qa/seams-bce3211.json` 的 boundaryEdges，用的是 world 坐标。

| ID | 候选 | 正例（必须通过） | 负例（必须被判失败） | 容差 |
|---|---|---|---|---|
| T16 SEAM-C5 闭合 | `gp:LY-089:seam-c5`。L 形，顶点 (404.000,−492.796) (407.761,−492.796) (407.761,−486.796) (403.000,−486.796) (403.000,−488.000) (404.000,−488.000)。顶面西边 0.20、东边 0.21 | 把片加入顶面集后重跑 `measure_seams.py`：SEAM-C5 的 linesWithBoundedVoid 从 24 降到 0；西、东接边的 \|dy\| ≤ 1 mm；顶面积 23.770 m² ± 0.01 | ① 片只做 3.761 m 的矩形，漏掉北侧 1×1.204 m 的缺角：Z −487.75…−487.0 的 4 条线仍有夹空，必须判失败；② 顶面整体取 0.21（不做过渡）：西边台阶 +10 mm 未声明，必须判失败 | 1 mm |
| T17 SEAM-C1 闭合 | `gp:LY-089:seam-c1`。四边形，顶点 (386.5904,−476.000) (392.5904,−476.000) (392.5904,−471.6843) (386.5904,−471.7077)。北边 0.20、南边 0.21 | linesWithBoundedVoid 从 24 降到 0；面积 25.824 m² ± 0.01 | 片的南边取平直的 Z = −471.70（不按 primary 边 0.023 m 的斜度）：会叠顶（违反 T6）或留缝（违反 T9），必须判失败 | 1 mm |
| T18 CRACK 闭合（仅当判给 LY-089） | `gp:LY-089:crack-stitch`。楔形，沿 C_stitch_primary 的精确边界边 (398.0154,−1849.9385)–(397.9369,−1845.7626) 及其对边；顶面 0.21 | 1 mm 步长扫描下 linesWithBoundedVoid 从 41 降到 0；与 primary 的叠顶面积 ≤ 1e-6 m² | 用 0.1 m 宽的矩形条去盖：叠顶 > 1e-6 m²（违反 T6），必须判失败 | 0.5 mm |
| T19 闭合后连通 | 交 LY-081 重算可达网络：C_5 和 C_1 由孤立分量并入主分量；同时验证中横路 56.2 m 的禁用边仍然断开 | LY-081 报告两分量并入，禁用边保持断开 | 把片误放在中横路缺口上：禁用边被接通，必须失败 | — |

在这些检查之外，还要把候选框外扩 2 m 跑一遍 `seam_neighbours.py`：
- 与其他席位写入区、场地包络的相交必须为 0；
- 负例夹具 `qa/neg/neg-boxes.json`（市肆框、C02-010 框）必须检出相交。

## 4 已在准备期跑过的基线和负例

| 项 | 结果 | 文件 |
|---|---|---|
| 支承基线 | 62 个安装节点；第 2 轮重跑，除 seconds 外逐值相同 | `qa/support-bce3211.json`、`qa/rerun-r2/support-bce3211.json` |
| 近档复核 | 44 院和雍门 | `qa/support-near-bce3211.json` |
| 叠加支承 | 门体在地坪上、N2 在市肆底板上、门楼在墙顶上 | `qa/support-stack-bce3211.json` |
| 负例：去掉 D08 | D08 院 100% 变为无地面 | `qa/neg-drop-D08.json` |
| 原地面指纹 | 第 2 轮重跑逐字节相同 | `qa/ground-fingerprint-bce3211.json` |
| 双法复核 | 10 个点全部一致 | `qa/bl-crosscheck.json` |
| 接缝实测和正负对照 | 3/3 的 controls.pass 为 true；重跑逐字节相同 | `qa/seams-bce3211.json`、`qa/rerun-r2/seams-bce3211.json` |
| 邻接 / 写入区互检 | 候选框 0 相交；负例框能检出相交 | `qa/seam-neighbours-bce3211.json`、`qa/neg/neg-neighbours.json` |
| 消费端口 | 133 个 | `qa/consumed-ports-ly006v1.json` |

## 5 不声称

全部检查都只是竖直射线、有限扫描线、包围盒互检和投影面积。不是实体碰撞，不是身体扫掠，也不是车辆、结构或现代规范认证。没有浏览器或 GPU 实测。差异片是 C 工程闭合件，不是考古地形。
