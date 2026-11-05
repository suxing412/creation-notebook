# LY-083 测试计划（按「本项验收」写成可执行检查，第二遍）

运行方式：`D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P <脚本> -- <参数>`

`<city_root>` 在正式开工时，改成 LY-001 冻结快照的 `docs/cities/luoyang`，不用 `bce3211`。

| 脚本 | 参数 | 内容 |
|---|---|---|
| `prep/measure/measure_outer_street.py` | `<city_root> <out_json>` | 5 个配置下的中线、横断面、主路、路口 |
| `prep/measure/measure_fine_and_render.py` | `<city_root> <out_json> <png_dir>` | 宽度剖面、缝口 5 mm 精扫、主路西缘、落空出口、CPU 前图 |
| `prep/measure/measure_supplement.py` | `<city_root> <out_json>` | S1 v1 original 视图、S2 包络扫掠、S3 净空、S4/S5/S6 负例 |
| `prep/measure/measure_drift_cad338b.py` | `<city_root> <receiver_glb> <out_json>` | 快照含 yong-road-receiver 时的冷启动复测 |

基线可复现性已核：bce3211 上重跑 `measure_outer_street.py`，输出与首跑逐字节相同（`1bba3cd921e6…`）。

## 0. 先绑定 SHA，任何一项不符就停止

GLB 直接比文件字节。文本文件比 `git show <commit>:<path>` 的 LF 字节；Windows 工作区是 CRLF，SHA 会不同，两种都记在 `inputs.json`。

| 文件 | 期望 SHA256 |
|---|---|
| assets/market/market-cluster.glb | 77b8bf2e9e1488df02c99ffa1b83af9517fabbb23e9d6b7f86dd3c3361c5a5c8 |
| assets/market/N2-replacement.glb | d33cbad1ea14e9436219e895791aafa3c4de20dfe7648635909d6b734e1c99d1 |
| assets/market/flowB-routes.glb | 43d7799f85feccb0d6f1e0412c46853e6b3339535e38a9b806e8c5d3898f845e |
| assets/ground-atomic/network-ground-stitched.glb | fdfc3ce5c63305f79aa746b31c3be60f3d11a6acb75f190886124f2d3446db60 |
| assets/ground-atomic/retained.glb | aed8b3d4cb12aeaddf5c696a8a86355b15b7cb4fc8ebd76cc364d23789d630cc |
| assets/ground-atomic/south.glb | 4313826ddf5fbe0c0d8dcb4983d6cdbd647713d49faa1980cd34f587a3273a0e |
| assets/ground-atomic/D08.glb | 3ab933108b88c5c359fc7512d324e14f15157eaa54fb17f80f2adeb6c4626d9a |
| assets/market/corridor-6m-market-link.glb（仅负例） | b46dd450d7e8636b744d2dcd1d0cee8e98352025b7cda57b2cd0938a3da149bf |
| progress-assets/yong-road-link-v2/yong-road-receiver-component209.glb（快照含 cad338b 时） | e5baa0df8fd28e117b4ef997cab0d962b0834a4c9664bb1ed73b7746d2488e38 |
| data/west/road-plan.json（LF） | 0bc4528cbf354a18c5a74f9bbf4574bfc0ea0ee817516736e9d15ef5dca6881a |
| data/west/N2-contract.json（LF） | 498f51fcd0723da69ab1b97c56f3de004a449a86e0e322dedc6489446a00e2cd |
| data/west/market-flow-plan.json（LF） | fb2416122d3b9fd7e2bbeafcaa1934ee4efcaf67cbe4654139b212e4e50ce37b |
| data/west/ground-atomic-contract.json（LF） | 7f26720bf40fc8cd7f7d0b445398d889fcc70c407f7cc7e26e4acd0eb6332367 |
| city-data.mjs（LF） | bce3211：c849706b6210813c74851b86cfd3353183a47badc0e019a1151247db1e34bf00<br>cad338b：d8933a32a6a133b38bc8ae5591bd0b350d206f9c884e1a6c4a1adabf5fc6daf3 |

还要绑定两样东西，届时补进本表：LY-030 冻结的市肆边界/出口清单 SHA，以及 LY-081 网络数据 SHA。缺任何一样，状态都保持「待输入」。

## 1. 正例（公共外街复用身份）

| # | 检查 | 通过条件 | 容差 | 基线实测 |
|---|---|---|---|---|
| P1 | 市肆东界与城网缝 | `seam` 缝宽/侵入 = 0 | ≤ 0.001 m，不允许正体积侵入 | 0.000000 |
| P2 | 缝口 5 mm 精扫（9 线 × 41 点） | miss = 0；承托件只有 `route_exitPublic` 和 `C_stitch_primary`（或 receiver） | z 0.21 ± 0.0005 | 0 / 369 |
| P3 | 中线从市肆东界到主路西缘 | v1_market_A/B 的 missRuns 不与 [244.286, 392.4] 相交；该区间内 heightSteps 为空 | 0.25 m 步长；台阶阈值 5 mm | 通过 |
| P4 | 长度 | 东界到主路西缘 148.11 m；东界到主路中线 151.09 m | ± 0.05 m | 148.11 / 151.09 |
| P5 | 宽度 | 东界处 4.00 m，等于 exitPublic；x ≥ 254.3 为 6.0 m | 0.01 m 采样，± 0.02 m | 4.00 → 5.99 |
| P6 | 主路连续 | y 1900–2020 无缺测，z 0.21 | ± 0.0005 | 0 缺 |
| P7 | 包络扫掠（S2） | 0.6 m 和 1.6 m 包络全程 0 无承托；横向高差 < 5 mm | 纵向 0.1 m，横向 0.05 m | 0 / 19,266；0 / 48,906；0.00002 m |
| P8 | 净空（S3） | z 0.215–2.4 m 内 0 处遮挡 | 0.5 m 纵向，5 条横线 | 0 / 1,445 |
| P9 | 四片原子地面全载 | 四个文件按 SHA 各出现 1 次（stitched + `keep` 里三个），且 `C_stitch_primary/_west/_patch` 各出现 1 次 | 精确 | 四片时通过 |
| P10 | v2 冷启动市肆（新快照） | 冷启动节点集 = `initial!==false` ∪ market `loadNodeIds`；对它跑中线、1.6 m 包络、缝口，全部 0 缺 | 同 P2/P3/P7 | bce3211：失败（661）；cad338b：通过（45，全在区间外） |

## 2. 负例（每条都必须真的失败，否则说明测试无效）

| # | 操作 | 期望 | 基线实测 |
|---|---|---|---|
| N1 | 移除 stitched（`neg_no_network`） | 中线 x 244.5–405 全部缺测 | 661 / 901 |
| N2 | bce3211 的 v2 市肆冷启动（只有 market-main 和 market-N2） | 同 N1，记作「未入城」 | 661 / 901 |
| N3 | 旧件 `corridor-6m-market-link.glb` 与 stitched 叠载 | 检出共面双层路面，并拒绝 | 444 / 444 双层（S4） |
| N4 | 只载 stitched，不载另外三片 | **P9 的 SHA 检查报错**。注意：`assertGroundAtomic` 只数三个节点名，只载 stitched 时它照样通过（S6），不能拿它当这条负例 | 第一遍写错，第二遍已更正 |
| N5 | 市肆整体平移 Δx = +1 m（模拟「改市场位置就路」） | x 244.296–245.276 内出现市肆和城网双覆盖，判为越界 | 基线 0 / 3,861；平移后 3,861 / 3,861（S5） |
| N6 | exitN / exitS 边界外 0.1 m | 无承托（`supportJustBeyondBoundary: null`）。若做了差异件，撤回后必须恢复为 null | null |
| N7 | 新快照里 receiver 与 stitched 同载（先冷启动，再开 terrain 章节） | 若检出双层面，记为风险并转交 LY-081，不由本项修改 | 待测 |

## 3. 边界外差异件（仅在 LY-030 / LY-081 放行后才做）

- **输入**：LY-030 冻结的出口清单。只给已确认为真实出口、且被 LY-081 判为断点（不是禁用边）的出口补件。
- **几何**：
  - 独立 GLB，米制，原点为绝对坐标，无额外平移。
  - 顶面 0.21，与出口、外街都是 0 高差。
  - 不进入 x < 244.286（市肆内部归 022）。
  - 与 `C_stitch_primary` 和 receiver 都没有正面积投影重叠，阈值 1e-7 m²。
- **通行**：
  - 用 S2 方法，对新路线扫 0.6 m 和 1.6 m 包络。
  - 给出足下支持，以及 0.20/0.21 两种台阶的分类。
  - 只打中线射线不够。
  - 用 S3 方法测净空。
- **安装与撤回**：在严格基线上装一次、撤一次。撤回后，市肆根全部节点的矩阵/材质、stitched 和 receiver 的 SHA 都不变，N6 恢复。
- **体积**：不超过 15,000,000 字节，固定件合批。

## 4. 「已入城」的检查（交 LY-100）

- **快照含 cad338b**：跑 P10 和 N7 即可，不提共享文件改动。
- **快照是 bce3211**：
  - 提案：market 章节 `loadNodeIds` 加入四片原子地面，不改任何几何。
  - 验证：用 node 读取 `city-data.mjs`，算出冷启动节点集，确认 P9；再对它跑 P10。
- **局限**：没有真实浏览器/GPU 时，写「CPU 网格采样，未测 GPU」，不能声称已测。
