# LY-023 测试计划（本项验收 → 可执行检查）

所有命令在 `D:/GitHub/creation-notebook-workpacks/LY-023/prep/` 下运行，Blender 命令统一写作 `BL="D:/Blender/blender.exe -b --factory-startup --python-exit-code 1"`。
制作期如果交 overlay 件，记作 `models/*.glb`，不改原 GLB，并把它作为额外的 `--ground` 或主件输入。

## 0. 先绑定 SHA（任一项不符就停止，判阻断）

| 文件 | 必须的 SHA256 |
|---|---|
| market-cluster.glb | `77b8bf2e9e1488df02c99ffa1b83af9517fabbb23e9d6b7f86dd3c3361c5a5c8` |
| street_frontage-LOD0/1/2.glb | `46f08f41…f6f2` / `03ad28cf…6126` / `b5b13b1c…a0fa` |
| market-LOD0/1/2.glb (v2) | `acdd4391…aa07` / `e925451b…0683` / `ea0c235f…8864` |
| flowB-routes.glb | `43d7799f85feccb0d6f1e0412c46853e6b3339535e38a9b806e8c5d3898f845e` |
| G 冻结后新增 | LY-005 坐标/高程契约、LY-006 所有权表、LY-022 选定地坪 GLB（若有）——在此表补 SHA 后才可跑 §2 以后 |

检查：`sha256sum <files>`，与上表逐字比较。若 main 已前进，先按 LY-001 新快照更新表并重跑全部检查，不沿用本 prep 数字。

## 1. 工具自检（负例必须失败）

| ID | 命令 | 期望 |
|---|---|---|
| N1 | `$BL -P measure_stall_feet.py -- --glb <cluster> --mode named --no-sample-ground --ground <joined-route-terrain> <corridor-6m-market-link> --out out/neg1.json` | `status_summary == {"no_ground": 24}`（证明外路不承托摊位，判据不会凭空报接触） |
| N2 | `... --glb <v2 LOD0> --mode loose --datum 0.15 --out out/neg2.json` | 24 摊脚全部 `floating`，gap_min = 0.05 ± 0.001 |
| N3 | `... --glb <v2 LOD0> --mode loose --datum 0.25 --out out/neg3.json` | 24 摊脚全部 `embedded`，gap_max = −0.05 ± 0.001 |
| N4（制作期） | 把待交 overlay 垫件人为下移 0.01 m 后测 | 对应脚变 `floating`；否则测试无效 |

## 2. 逐脚接触（验收①：逐脚实际接触/支承面积可复核）

正例 P1（城内 v1，已入城）：
```
$BL -P measure_stall_feet.py -- --glb <cluster> --mode named --out out/P1.json \
    --ground <joined-route-terrain> <corridor-6m-market-link> [<LY-022 selected ground>]
```
期望（容差 |gap| ≤ 0.005 m，9×9 采样）：
- `feet_count == 24`，`status_summary == {"contact": 24}`。
- 每根 `T?_canopypost*`：`contact_area_m2 == 0.0100 ± 0.0002`；每条 `T?_leg*`：`0.0144 ± 0.0002`；每摊合计 0.0976 ± 0.001。
- 每只脚 `top.touch_fraction == 1.0`（棚柱→棚顶，桌腿→桌底）。
- 若 LY-022 地坪取代 sample_ground：加 `--no-sample-ground` 再跑一次，结果必须仍为 24 contact；否则列出逐脚 gap，那才是本项需制作的脚端缺口。

正例 P2（v2 库，三档）：`--mode loose --datum 0.2`，LOD0/1/2 各跑一次。期望摊脚 24 contact（15 个 z0=0.39 的铺面柱为 floating，属铺面，不计入摊脚，必须在报告中单列而不是丢弃）。

正例 P3（店前线 4 棚，三档）：`--mode loose --datum <LY-005/LY-022 给定的店前线地坪高；未给定时 0.0 并标“推定”>`。
- 脚底：LOD0/1 `feet_count == 24` 全 contact（16 柱 0.0147 m²、8 支架 0.192 m²）；LOD2 16 柱 contact。
- 上部（当前已知缺口，制作前应复现为“失败”）：8 片支架 `top.up_gap_min == 0.030 ± 0.001`、touch 0；坡顶棚 C01/C02 的 8 柱 `top.up_gap ∈ [0.075, 0.134]`、touch 0。
- 若制作 overlay 垫接：把 overlay 作为合并主件重测，期望这 16 项 touch_fraction == 1.0 且 overlay 与原件无正体积侵入（§4）。

## 3. 棚下通道与路带（验收②：地脚附件不挡棚下通道）

P4：`$BL -P measure_route_clearance.py -- <cluster> out/P4.json <flowB-routes>`
- 期望 `route_public` 与 `flowB_public` 到 T1/T2/T3 最小平面净距 == 0.85 ± 0.005（与 prep 一致，证明无附件外伸）；其余路带 ≥ 9.85。
- 制作期若有任何脚端附件：把附件 AABB 加入 targets 后重跑，附件到任何路带净距必须 ≥ 0.85 − 0（即不得小于现状）；附件水平投影不得超出所属柱/腿 AABB 外 0.02 m（C 工程容差）。

P5（棚下净距不减少）：从 `out/P1.json` 的 `canopies[]` 读取并比较——
- v1：`table_to_canopy_edge` = {west 0.2, east 0.2, south 0.15, north 0.15}，`clear_between_posts_x == 3.1`，`clear_between_posts_y == 2.0`，`headroom_centre == 2.655`。
- 店前线：桌边至棚边 0.175/0.275，平顶净空 2.35、坡顶 2.95。
- 任一值减小 > 0.005 m 即失败。说明：现状棚下本无 0.6 m 人体通道（桌占满棚下），本检查只证明“附件不使其更差”，不宣称棚下可通行。

## 4. 复用判定与防叠层（验收③：已有合格脚端识别为复用）

P6：P1 全通过 ⇒ T1–T3 判 **复用**；交付 `assembly.json` 只含 SHA 绑定、24 脚的接触记录，**不含任何新网格**。负例：若 `models/` 中出现以 `T1_|T2_|T3_` 定位的新脚件，判失败（多做一层）。
P7：节点指纹不变——对 cluster 导出 39×3 个 T 节点的名称、顶点数、AABB（6 位小数），与 prep 的 `out/city-market-cluster.json` 中 `bbox_min/bbox_max` 逐项一致。
P8（仅当交店前线 overlay）：overlay 与原件做表面 BVH 重叠（`BVHTree.overlap`）+ 顶点包含测试，区分“合法局部接面（共面）/正体积侵入/完全包含”；只做表面 BVH 时报告中注明“非实体碰撞穷尽”。
P9（安装与撤回，至少一次）：按 LY-005 契约把 overlay 装入严格输入、再撤回，比较原节点名、几何哈希、材质、矩阵完全不变。

## 5. 结果记录

每次运行把 `out/*.json` 的 SHA 写入 `qa/run-<date>.json`，连同输入 SHA、工具 SHA、Blender 版本。CPU 测量，不声称 GPU/浏览器验收；接触≠结构安全，≠历史复原。
