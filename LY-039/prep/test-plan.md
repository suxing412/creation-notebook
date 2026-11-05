# LY-039 测试计划（制作时直接跑；第2版）

本计划把「本项验收」逐条写成可执行检查。

## 约定

- 命令里的缩写：
  - `B="D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P"`
  - `P=workpacks/LY-039/prep`
  - `X=<zip 解包目录>`。解包方法：把 part01..05 按顺序拼成 zip（SHA `5895ef23…`），再解出 `chunks/northeast_C_access.glb`、`chunks/wuku_C_with_support-01.glb`、`chunks/granary_C_with_ground.glb` 和 `qa/source-node-manifest.json`。
- 公差取 LY-006 registry v1 端口的冻结值：位置 **0.005 m**，高程 **0.002 m**。LY-008 交付后改用它的检查器入口重跑，公差以它为准。
- 判定规则：**连通图、接缝探针、体积侵入三项都必须通过**。任何一项失败都算断开或越界。

## 0. 绑定的 SHA（任何一项变化就停下，先重新出 brief）

| 输入 | SHA256 |
|---|---|
| 路 GLB `chunks/northeast_C_access.glb` | `58f2f58a464183e20d5489b13902f62f2570573cb8bf96fb237df781027d076e` |
| 拼接 zip（part01..05） | `5895ef23a684a343271183dce1e92e112fb49bba9e03e4372023d1247bb50b69` |
| 源节点有向三角（manifest 记录） | `0f806978e9558e7ca8286f9120f89e692553a7a74a7ed7b1d59c0334d9333a4f` |
| 太仓地坪所在的 `granary-city-LOD0.glb` | `5937211c7366a5920ae222185176f198cc3d16e8763605fa248e61031c74bc93` |
| 旧试放武库支持片所在的 `wuku_C_with_support-01.glb`（只作参照） | `29709e25f77f6becaf2566555a4d55b0525e244f73ede92ae344a78cc1a57b37` |
| v1 旧仓储组（只作对照） | `b8482824513a101d36eb4c768a4f641e77aaac66c3e834718d7f3964104a644b` |
| 城墙 wall-01（邻近对照） | `cfbbc45a874a32a0501ea6e57dbd58aefcb2c2e42c943ad34f9704e3b7453a95` |
| LY-006 `registry/ports.json` | `28bcfb68…`（全长见 inputs.json） |
| LY-003 `tables/admission.json` / `hold-zones.json` | `dd0ab8c0…` / `0b9bb0ff…` |
| 武库支持片（LY-036 交付） | 待填，LY-036 冻结后写入 |
| 武库 B 选定版 | 预期 `e5de60b6ff972e6b9446bb60c9c8b79572d345c69be7124dfc855181ac87dfd3`（B-LOD0 v2.2），以 LY-036/038 的声明为准 |
| lab | `bce3211f818ee5a8bef1773539da70695ba37b17`；开工时换成 LY-001 新快照（现在 origin/main 是 cad338b） |

**T0**：运行 `python -I $P/hash_inputs.py <lab> $X inputs.json [lab_ref]`，逐项和上表比对，有一项不一致就失败。另外运行 `python -I $P/glb_raw_check.py $X/chunks/northeast_C_access.glb`，要求：32 个三角、18 个唯一顶点、1 个节点 `C_NE_APPROACH_LOCAL`、1 个材质。

## 1. 验收：「实际GLB两端与当前地坪标高吻合」

**T1 北端接缝（正例）**

运行：`$B $P/check_ne_binding.py -- --road $X/chunks/northeast_C_access.glb --ground <granary-city-LOD0> [--support <武库支持片>] --out qa/bind.json`

通过条件：
- `north_seam_missing == 0`。
- `north_seam_max_abs_step <= 0.002`（现测 1e-5）。
- 位置：路北盖 y 与 LY-034 冻结的 `storage-site:forecourt-north:road-end` 世界坐标相差不超过 0.005 m（现测 y=3647.469，地坪南沿也是 3647.469）。
- 与 LY-006 的 `ne-approach:start:road-end` 对比：位置 (2285.714, 0.2, −3647.469) 偏差 ≤ 0.005 m，高程偏差 ≤ 0.002 m。

**T2 南端接缝（正例，依赖 LY-036）**

- 用 `--support <LY-036 交付件>` 运行，要求：
  - `south_stub_missing_beyond == 0`。
  - `south_stub_seam[*].step` 的绝对值全部 ≤ 0.002。
  - 目标 `wuku_port_B_point_side:2316.327,3491.0` 的 `reachable == true`。
  - LY-036 冻结的 `wuku-B:outer-arrival:ground` 端口坐标（用 `--goal name:x,y` 传入）也 `reachable == true`。
- 对照参考：用旧支持片 `--support $X/chunks/wuku_C_with_support-01.glb` 跑，现测 0 缺、高差 0.000、武库侧可达（`out/bind-oldpatch.json`）。LY-036 的新件**不得比这个更差**。
- 现状对照：城景里没有支持片时，11/11 缺，武库侧不可达（`out/bind-baseline.json`）。这是已经测到的缺口，不能拿来当作失败豁免。
- **端口面要核对**：南端接的是短头北盖（y=3490，x 2314.827–2317.827，朝 +y）。LY-006 v1 的 `ne-approach:end-E` 在东侧面（x=2317.827），面外是空的。开工前 LY-006 必须补发或更正短头北盖端口。如果仍然只有 end-E，就记为**阻断：端口与实际接面不符**，不能拿 end-E 去绑武库。

**T3 坡度与断面不变**

- 北段顶面 z 从 0.200 线性降到 0.000（y 从 3647.469 到 3487.5）；东段和短头 z=0.000。
- 每 2 m 取一个断面，要求 `spans == 1`。交汇区 y∈[3487.5, 3490] 允许为 2。
- 路的 18 个唯一顶点逐个和 `out/glb-raw-check.json` 及 `out/measure-ne-approach.json` 比对，差 ≤ 1e-4 m。
- 如果在写入区 002 内改了短头端盖，只许改 y=3490 的 4 个顶点，其余 14 个必须不变。

## 2. 验收：「原端盖接触保留说明」

**T4 接触分类（三类分开计数）**

- 运行 `python -I $P/intrusion_check.py qa/intrusion.json 0,0,0`。如果 LY-036 的件不是简单盒子，就把它的实测盒子或三角网换进 `BOX` 再跑。
- 通过条件：
  - 太仓地坪：合法局部面接触 0.540 m²（±0.01），侵入体积 0。
  - 武库支持片：合法局部面接触约 0.54 m²，侵入体积 0。
  - 正体积侵入大于 1e-5 m³ 就失败。
  - 完全包含（路顶点落在板体内部）计数为 0。
- 表面 BVH 交叠对只能来自 `original_city_ground_preserved` 和支持片节点（北端现测 5 对）。
- 报告必须写明：只做了表面 BVH、解析体素和顶点包含三种测试，**不是实体碰撞穷尽**。

**T5 与城墙、其他节点无交**

- 运行 `python -I $P/scan_city_bounds.py <city-data.mjs> 20`。命中只允许是 wall-A-wall-01、storage-main 和章节并集包围盒（terrain、north-three 等）。出现新的实体节点就逐个测几何距离。
- 与 wall-A-wall-01 的交叠对为 0，最近距离 ≥ 100 m（现测 123.5 m）。

## 3. 验收：「关闭道路负例能检出断开」

下面每一项都必须**失败**（检出断开、高差或侵入）：

| 负例 | 命令差异 | 期望结果（现测值） | 由谁检出 |
|---|---|---|---|
| N1 关闭道路 | `--drop-road` | north_leg_mid、road_stub_end、武库侧都 `reachable=false`；起点只能到 7457 格；north_seam_missing=11 | 连通图加探针 |
| N2 路抬高 5 cm | `--offset 0,0,0.05` | 接缝高差 0.04999，超过 0.002 | 探针 |
| N3 路南移 10 cm（小缝） | `--offset 0,-0.10,0` | 连通图**仍然通**，但 north_seam_missing=11，侵入检查判为「分离」 | 只有探针能查出 |
| N4 路南移 60 cm | `--offset 0,-0.60,0` | 连通断 | 连通图 |
| N5 关闭武库支持片 | 去掉 `--support` | 武库侧不可达，south_stub_missing_beyond=11 | 连通图加探针 |
| N6 武库偏移错误（例如方案 A 北移不够） | 用偏移错误的支持片 | 南接缝缺失、高差超限或侵入 | 三项之一 |
| N7 路北移 10 cm（压入两端） | `--offset 0,0.10,0`，再跑 `intrusion_check.py … 0,0.10,0` | 连通图和探针**都通过**（`out/bind-oldpatch-neg-y+0.10.json`），但两端各侵入 0.054 m³ | 只有侵入检查能查出 |

N3 和 N7 说明：只看连通图不够，只看探针也不够。

## 4. 验收：「新宫墙准入条件有明确状态」

**T6 准入字段**

- 安装包 `assembly.json` 必须有 `admission` 字段，只能取下面三个值之一：
  - `blocked_pending_palace_wall@LY-003:<admission.json sha>`
  - `admitted@LY-010:<sha>`
  - `rejected@LY-003|LY-010:<sha>`
- 现状：LY-003 的结论是「宫墙条件未决（不是放行）」，所以取第一个值，并且 `activate=false`，LY-100 不能合入城景。
- 运行 `python -I $P/ne_screen_check.py <evidence-geometry.json> <LY-003/tables/hold-zones.json> qa/ne-screen.json`。要求 `all_in_NE_C_SCREEN == true`，并写出各悬置区的余量。现测最紧的是 HZ-Y，余量 12.87 m。
- 任何端口或端头改动之后，HZ-Y 余量必须仍然 > 0。
- 旧示意北宫范围（现测 540.48 m）和 NE-C-SCREEN 都**不能**当作准入证据。

## 5. 安装与撤回（任务池公共底线）

**T7 安装/撤回往返**

- 在严格输入上做，即 city-data 快照的拷贝，不写 main。
- 装入路节点：新增 1 个 asset 和 1 个 node，storage 章的 loadNodeIds 加 1 项。然后撤回。
- 撤回后，city-data 拷贝逐字节回到原 SHA。
- 安装前后，以下都不变：granary-city-LOD0 的 SHA、节点矩阵、`original_city_ground_preserved` 的 12 三角指纹。
- 计数不变：仓数 2，武库最多 1，建筑家族数不变。路不计入建筑。
- 互斥：路节点和 city-visible 分块层里的 `visible-current-node-northeast_C_access` 不能同时加载。

**T8 回读**

- Blender 回读要求：32 个三角，1 个材质，包围盒与记录一致。另用 `glb_raw_check.py` 做一次裸解析。
- Three GLTFLoader 用 city-renderer 的同一条解析路径。没跑浏览器就写「未测 GPU/浏览器」。
- 单个 GLB 小于 15 000 000 B（现在是 413 628 B）。

**T9 范围负判据**

- 路的中线总长 ≤ 196.1 m。
- 端点只能是太仓地坪端口和武库支持端口。出现延长到 road_northeast_gate_link_B（y≈2600）或其他节点的，就判失败。
- 写入只能落在 LY-006 的 `LY-039:write:001/002` 内。
- 文案扫描：不得出现「历史道路」「物流已证」「通行权」等定性说法，一律写 C。

## 6. 现状基线（已跑，供对比）

`out/` 目录下的文件：

- `bind-*.json`：第1版的 6 个，加上本版新增的 `bind-oldpatch*.json`（3 个）和 `bind-nopatch-goals.json`。
- `measure-ne-approach.json`
- `glb-raw-check.json`
- `intrusion-check.json`
- `ne-screen-check.json`
- `city-bounds-scan-bce3211.json` 和 `city-bounds-scan-cad338b.json`

这些是开工前的基线。制作时用同一组参数重跑，并和它们比对。
