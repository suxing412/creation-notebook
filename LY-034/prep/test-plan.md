# LY-034 测试计划（制作时直接跑）

绑定基线（任一不符就停止，并重新做准备）：
- `granary-city-LOD0.glb` sha256 = `5937211c7366a5920ae222185176f198cc3d16e8763605fa248e61031c74bc93`（当前入口）
- `storage-group-organized.glb` sha256 = `b8482824513a101d36eb4c768a4f641e77aaac66c3e834718d7f3964104a644b`（v1 入口）
- LOD1 `a1265bbf…2e45`、LOD2 `6b2564d3…efe7`（只做一致性检查）
- lab HEAD：执行时由 LY-001 给出最新 main；如果不是 bce3211，先重跑 T0。
- 锚点：(2285.714111328125, 0, −3673.468994140625)，局部 z 为正表示朝南。

命令前缀：`B="D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P"`，工作目录 `D:/GitHub/creation-notebook-workpacks/LY-034/`。

## T0 输入未漂移
- 跑 `python -I prep/build_inputs.py`，对比 inputs.json 里每一项的 sha256 和 commitBlobSha256。
- 正例：GLB 全部相同。负例：把任意一个 GLB 复制到临时目录并改 1 个字节，T0 必须报不符。
- 容差：0（逐字节）。

## T1 原件指纹不变（棚 / 台案 / 地面 / 阶梯）
- 跑 `python -I prep/fingerprint.py <GLB> <measure.json>`，和 `prep/out/fingerprint-city-LOD0.json` 逐项比较：整文件 SHA；4 个节点的名称和 translation；每个 primitive 的 POSITION/NORMAL/TEXCOORD_0/indices 字节 SHA；9 张图像的 SHA。
- 松散件层级：`islandFingerprint.receivingShelterAndTable`（11 件）、`fieldCargoOutsideShelter`（4 件）、`groundSlab`（`1422314d826503c3`）、`stairs`（A `5574b19bf3458897`，B `d8f3a1b0d9d938d8`），geomHash3mm 必须全部相同。
- 装配后：如果装配以叠加层（overlay）或端口数据的方式交付，原 GLB 的 SHA 必须仍是 5937…。如果 LY-100 要求重新封装，要另外跑「顶点逐点最大偏差 ≤ 1e-5 m、三角数与 UV 字节不变」，不能用 1 mm 取整哈希代替。原因：v2 分件与 LOD0 之间有 44 块瓦在 1 mm 取整边界上翻转（`out/v2-parts-vs-city.json`），取整哈希不足以证明「不变」。
- 负例：把台案平移 1 mm，或把棚柱删掉，比较必须失败。

## T2 端口由几何测得，不靠名称
- 先把所有节点改名为 `n0…n3`（在临时副本里改 JSON chunk，不动二进制），再跑 measure_frontfield.py。必须仍然测出 2 个阶梯和 1 个收货棚，端口坐标与原名运行一致（容差 0.005 m）。
- 期望端口（局部 / 世界，y 是支持面）：

| 端口 | 局部 (x, y, z) | 世界 glTF | 容差 |
|---|---|---|---|
| RCV-N 收货棚北沿中点 | (0, 0.20, 9.60) | (2285.714, 0.20, −3663.869) | 0.01 |
| A-FOOT A 阶脚沿中点 | (−12.00, 0.20, −1.52) | (2273.714, 0.20, −3674.989) | 0.01 |
| A-HEAD A 阶顶 / 仓板沿 | (−12.00, 0.85, −2.80) | (2273.714, 0.85, −3676.269) | 0.01 |
| B-FOOT B 阶脚沿中点 | (12.00, 0.20, −1.38) | (2297.714, 0.20, −3674.849) | 0.01 |
| B-HEAD B 阶顶 / 仓板沿 | (12.00, 1.10, −3.30) | (2297.714, 1.10, −3676.769) | 0.01 |
| SLAB-EDGE 地坪四边 | x ±36 / z ±26，y 0.20，下沿 0 | x 2249.714…2321.714，z −3699.469…−3647.469 | 0.01，状态「未连接」 |

- 端口 ID 和格式以 LY-006 冻结版为准，这里的 ID 只是占位。
- 负例：交一份只按名称（如 `receiving_*`、`A_step_*`）生成端口的 JSON。在改名副本上它必须失效，检查器应判失败。

## T3 地面支持和高差
- measure_frontfield 输出的 `frontField.cellsOnGroundPlane / cells` 应为 51,893 / 52,332（容差 ±0）。剩下的 439 格全部能归到 `obstacleIslands` 里的件（柱、案腿、货物、阶梯）；只要有一格不能归属就失败。
- 阶梯：A 4 级 × 0.1625，B 6 级 × 0.15（容差 ±0.001），踏面深 0.32；阶顶和仓板的高差 0（容差 ±0.001）。A 仓板 0.85，B 仓板 1.10。
- 门洞：净宽 1.50、净高 2.09（±0.01）。
- 路线：全程支持面都是 0.20，最大相邻高差 0.000（容差 0.005）。
- 负例：在临时副本里把地坪顶面局部下压 0.3 m（或删掉 A 阶几何），A-FOOT 必须变成不可达或检出高差超过 0.20。

## T4 完整路线包（正例 / 负例）
每条路线都要导出 8 邻接折线（局部和世界坐标）、长度、包络宽、净空 1.8 m、支持面序列。
| 路线 | 包络 | 期望 |
|---|---|---|
| RCV → A-FOOT | 0.6 / 0.9 / 1.2 / 1.5 / 1.8 | 都可达，14.15 m（±0.3） |
| RCV → B-FOOT | 同上 | 都可达，14.09 m（±0.3） |
| RCV → A 仓板 | 0.6 / 0.9 / 1.2 | 可达，16.15 m（±0.3） |
| RCV → B 仓板 | 0.6 / 0.9 / 1.2 | 可达，16.69 m（±0.3） |
| RCV → A/B 仓板 | **1.5 / 1.8** | **必须不可达**（保留的窄阶失败边界）。如果变成可达，就说明阶梯被改宽或检查失效，判失败 |
| SLAB-EDGE → RCV | 0.9 | 地坪内 10.7 m。地坪外没有支持，记「未连接」，不得写成已接路 |
- 有限性声明：这是 0.1 m 网格加方形或横向截面包络加 1.8 m 竖直净空的离散检查。它不能代表连续人体运动、负重、车辆、双人交错或结构安全。
- 两个入口各跑一遍：LOD0（5937…）和 v1 的 b848…。v1 文件的阶梯是分块的，阶梯识别要另走「按踏步盒聚类」，或者只跑路线部分。

## T5 邻路指纹
- `python -I prep/neighbour_check.py D:/GitHub/creation-notebook-lab/docs/cities/luoyang`：wall-01 sha `cfbbc45a…a95`，平面距离 61.604 m（±0.05）。
- 用 city-data 的节点包围盒筛 100 m 以内的节点：只能有 storage-main 和 wall-A-wall-01。如果出现新节点（例如 LY-039 的 C_NE_APPROACH_LOCAL），要另外列出接面高程，并确认没有改动地坪。
- 负例：如果 LY-039 的道路包已存在，关掉它以后 SLAB-EDGE 必须回到「未连接」。

## T6 安装与撤回（G 冻结、008 检查器就绪后）
- 严格基线上安装本包（预期只有端口和路线数据，零几何改动），然后撤回。前后要对比：city-data 节点集合、storage-main 的 asset/sha/bounds/excludeNodes、原 GLB SHA、chapter loadNodeIds，以及同一机位（2349.714, 60, −3597.469 → 2285.714, 0, −3673.469）的 CPU 图。图注要写明是 CPU 渲染，不是浏览器或 GPU。
- 不得叠载 v2 分件 A/B/receiving 和整组（这会造成重复计数）；负例：故意叠载时检查器必须报错。
- 跑官方 `lab/tools/build_assets.py --check`，只在 LY-100 的合并分支上运行；本席位不在 lab 仓库里运行它。

## T7 不越界
- 包内没有新的仓、棚或台案几何，三角数增量为 0。没有改动 city-data.mjs、p-luoyang.asset.json、v1 页面或 storage-interface.json（只附合并提案）。
- 证据栏只用 C 和类比，不出现「太仓实测」或「官仓平面」这类表述。
