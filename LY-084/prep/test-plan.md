# LY-084 测试计划（按「本项验收」，制作时直接跑）

本项验收原文：三方案分别列碰撞、支持缺失、宫墙/水系约束；资料不足时可全部拒绝，不能仅凭最短路径选择施工。

## 0. 绑定（每次运行先核，任一不符即停）

| 输入 | sha256 |
|---|---|
| lab 基线 | `bce3211f818ee5a8bef1773539da70695ba37b17`（正式开工时换成 LY-001 冻结的新快照，并重新登记下表） |
| network-ground-stitched.glb | `fdfc3ce5c63305f79aa746b31c3be60f3d11a6acb75f190886124f2d3446db60` |
| retained / south / D08.glb | `aed8b3d4cb12aeaddf5c696a8a86355b15b7cb4fc8ebd76cc364d23789d630cc` / `4313826ddf5fbe0c0d8dcb4983d6cdbd647713d49faa1980cd34f587a3273a0e` / `3ab933108b88c5c359fc7512d324e14f15157eaa54fb17f80f2adeb6c4626d9a` |
| wall-00..03.glb | `12d84a0b27f7e5d630b46f76b751f956177a055c0afd1b925da8d9ec551abc74` / `cfbbc45a874a32a0501ea6e57dbd58aefcb2c2e42c943ad34f9704e3b7453a95` / `8a17587a995e6851a1c4c7e0844f79cb880cf70348edb55dfb62891434b2afa9` / `cd4cb2b629c15cbf1eaaada61eca546fc96a034a1a53802acd9d7ebeb84e4762` |
| granary-city-LOD0.glb | `5937211c7366a5920ae222185176f198cc3d16e8763605fa248e61031c74bc93` |
| northeast_C_access.glb（zip 内） | `58f2f58a464183e20d5489b13902f62f2570573cb8bf96fb237df781027d076e` |
| evidence-geometry.json（提交 blob） | 由 `out/hashes.json` 给出；内部 frozen 42 项 `fa8b7002…` 不变 |
| road-preconstraints.json（提交 blob） | `d369409a…`（全值见 hashes.json） |
| LY-003 tables/hold-zones.json | `0b9bb0ff52883ac7cb90a285db701edb807f558695a08e792eb1f6dfad6bc03b` |
| LY-003 tables/ne-screening-cells.json | `5bd9a5016ac879a198cb7830048f0647ad2f980f12b84a5f7870821e4703e98b` |
| LY-003 tables/admission.json | `dd0ab8c018e714be1366cb491107ff09131e5e176b9106894a2e5b2b86e88dd3` |
| LY-003 qa/ne-checks.json | `d2fe03f840a532ececd8f5054afefdec55ab9c538c5788bf735726133a71e633` |
| LY-005 coordinate-contract.json | `b6d7fe9db9523569383bf656df39aef63e7d80e8a1d5877196ba0bcab8747712` |
| LY-006 registry/ports.json | `28bcfb68cd7d7fe0026f62de23ae3e45ba8f714a139e38c0b0957039f12fc633` |
| LY-006 schemas/interface.schema.json | `1e525d50965a78115b23b570e598e85beab11fba9f80a18146134d9ec5e71f74` |
| LY-010 / LY-040 / LY-081 交付 | 交付后补登 SHA；**缺任何一项，结论只能是「待输入/禁建」** |

命令：
```
python -I hash_inputs.py D:/GitHub/creation-notebook-lab > out/hashes.json
D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P measure_routes.py -- \
    D:/GitHub/creation-notebook-lab out/city-nodes-ne.json work/northeast_C_access.glb out/routes.json
python -I plan_svg.py D:/GitHub/creation-notebook-lab out/routes.json out/plan-ne.svg
```
LY-003 约束筛查（平面，6 项自检全部要求 ok，否则退出码 1）：
```
python -I ly003_screen.py D:/GitHub/creation-notebook-lab <commit> D:/GitHub/creation-notebook-workpacks/LY-003 out/routes.json out/ly003-screen.json
D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P net_in_screen.py --     D:/GitHub/creation-notebook-lab out/city-nodes-ne.json work/northeast_C_access.glb     D:/GitHub/creation-notebook-workpacks/LY-003/tables/ne-screening-cells.json out/net-in-screen.json
```
`out/city-nodes-ne.json` 由 node 导入 city-data.mjs 生成（命令见 brief 和 inputs.json）。城景节点集合一旦改动，必须重新导出。

## 1. 每案必列项（R1/R2/R3 各一行；原三条规划交来后再加 O1/O2/O3）

| ID | 检查 | 判定 | 容差 |
|---|---|---|---|
| T0 起点端口 | 每案起点必须是 LY-006 冻结端口 `ne-approach:end-E:road-end` v1：native (2317.827, 3487.25)，顶面 0.0；或者是 LY-040 填好数值的 `storage-site:region-boundary:road-end` | 起点到端口的距离超出容差就失败。prep 时 R1 起点 (2316.327, 3484.5) 离端口 3.13 m，**正式运行前必须重锚** | 位置 0.005 m，高程 0.002 m（LY-006） |
| T1 支持 | 1 m 步长、3 m 宽 3 条射线，统计无支持长度、比例、最长连续段 | 记录数值。无支持长度 > 0 时，该案只能是「需新造地面」，进入 T5 准入审查 | 射线落点 z 与地面差 ≤ 0.01 m |
| T2 接点 | 第一个三射线全落在 network 上的站点，记录坐标和 z | 必须落在真实 6 m 路网三角面上，不能按 B 线端点名称连接 | z 差 ≤ 0.01 m（LY-005 冻结后替换） |
| T3 碰撞 | 3 m 和 6 m 净空棱柱（z 0.25–2.5）与城墙、仓房（以后加入城的所有实体）做表面 BVH 求交，并检查包围盒全包含 | 列出对象和站点区间；有任何交叠必须分类：合法接面、正体积侵入或完全包含 | 0 对；有就逐对解释 |
| T4 证据距离 | 旧 B 北宫、南宫、城垣 B、永安宫、武库、太仓、三门点的最小距离；依附的 B 线及其分级 | 只要依附 `hold_palace_interface` 线超过 0 m，没有 LY-003 配准就**禁建** | — |
| T5 宫墙 | 北宫新 A 墙是否已配准（LY-003 产物 SHA） | 未配准，**禁建**。已配准，就用 LY-003 的误差带重算 T4 | 用 LY-003 给出的误差 |
| T6 水系 | 古河渠几何是否已落位 | null，结论写「无法检查，未知不等于无冲突」，不能判可建 | — |
| T7 长度门槛 | 新造地面长度 | 只要大于 0，又没有 LY-010 追加放行，就**禁建**。≥1000 m 的，还要证明它不是「顺延成主干」 | — |
| T9 LY-003 悬置区 | 每案逐个悬置区记录区内长度、最长连续段和 y 区间，再算并集比例（`ly003-screen.json`） | 落在任一悬置区内的长度大于 0，就**禁建**。悬置区外也只能称「与旧示意不冲突」，不能称「在宫外」 | 1 m 步长；距离边界 ≤0.5 m 的站点在报告里标出 |
| T10 准入区 | 每案在 NE-C-SCREEN 外的长度；同时统计筛查区内有多少路网和其他地面（`net-in-screen.json`） | 筛查区外的长度大于 0，且 LY-010 没有对那一段单列放行，就**禁建**。只要筛查区内路网命中为 0，「东北长接路」就**没有合法路线**，三案不必再逐一比较 | 5 m 格心；太仓地坪正对照应在 3744 m² ±10% 以内 |
| T8 最短路径禁用 | 审查表必须写明每案的选择或拒绝理由 | 理由只有「最短」或「最平」的，判失败 | — |

## 2. 负例和正例（必须得到预期结果，否则检查器无效）

| ID | 构造 | 预期 | 2026-11-05 prep 实测 |
|---|---|---|---|
| N1 | 6 m 走廊 (2300,3600)→(2600,3600)，横穿东墙 | 交叠 > 0，对象 C_wall_A_01 | 18 对，C_wall_A_01 ✓ |
| N2 | 3 m 走廊 (2250,3680)→(2321,3680)，穿过仓体 | 交叠 > 0 | 296 对（paper_cargo_proxy、timber）✓。注意 y=3670 是空场院，会得到 0，负例必须先核目标位置 |
| N3 | 去掉 network 层再跑 R1 | 没有接触点，无支持比例约 1 | 无接触，0.99944 ✓ |
| N4 | 从路南端头往武库方向走 10 m | 无支持比例 1 | 1.0 ✓（与 LY-039 一致） |
| P1 | 沿 C_4 段中线走 987 m | 无支持比例 0 | 0 ✓ |
| P2 | 沿现有 196 m 路走 | 无支持比例 0 | 0（ne_road 195.1 m + 太仓地坪 5 m）✓ |
| S1–S6 | `ly003_screen.py` 自检：仓储组中心在筛查区内、不在悬置区内；永安宫标签点在 HZ-Y 内、不在筛查区内；北宫内部点距离为 0；y=2000 不在筛查区内 | 全部 ok | 2026-11-06：6/6 ✓ |
| P3 | `net_in_screen.py` 在太仓地坪图层上运行 | 命中约 150 格，约 3750 m² | 154 格，3850 m² ✓ |
| N7 | `net_in_screen.py` 在 network 图层上运行 | 预期 0 命中。如果大于 0，说明路网已经进入筛查区，T10 的「无合法路线」结论**失效**，必须按命中格重新做 R1–R3 和新候选 | 0 ✓ |
| N5（待加） | 任何一案的契约里把父 B 线写成 hold 线 | 契约校验失败 | 等契约 schema（LY-006） |
| N6（待加） | 把 R1 端点接到 B 线端点名称上，而不是实际面上 | T2 失败 | 等 LY-081 网络节点 |

## 3. 不得声称

- 0 碰撞不等于「可建」。0 碰撞只说明当前已加载的实体里没有东西挡路；宫墙和水系没有几何，所以测不到。
- 表面 BVH 加包围盒包含，不是实体碰撞穷尽。离散站点不是连续人体或车辆扫掠。
- R1–R3 是本席位重建的候选，不能写成「原规划已复核」。
- 结论「禁建（当前）」不是历史判断，只是说准入条件还没满足。

## 4. 交付前回读

- `out/routes.json` 的 SHA 写进审查表，候选折线逐点保留。
- 2026-11-06 筛查基准值：悬置区内长度（并集）922.0 / 2123.3 / 1753.9 m；筛查区外长度 1157.0 / 2118.3 / 1758.9 m；筛查区内 network 命中 0、其他地面命中 0、太仓地坪命中 154。`ly003-screen.json` 的 SHA 是 `f142d523…`，`net-in-screen.json` 的 SHA 是 `7b2975e9…`。
- 重跑后结果和 2026-11-05 的数值对比：长度 1671.0 / 2167.289 / 2094.787 m，无支持 1670.0 / 2166.289 / 2094.787 m。有变化就要能指出是哪个输入的 SHA 变了。
