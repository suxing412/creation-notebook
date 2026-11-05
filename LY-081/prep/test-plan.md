# LY-081 测试计划（按「本项验收」，制作时直接跑）

验收原文：图中每条已通边都能回到实际面和测试；移除地面后出现断点负例；未建区域不因连线算法变成路。

## 0. 绑定（每次运行先核对，不一致就停）

| 对象 | 期望 SHA256 |
|---|---|
| lab main | `bce3211f818ee5a8bef1773539da70695ba37b17`（开工时 LY-001 若换了新基线，以 LY-001 冻结的为准，并全部重跑） |
| network-ground-stitched.glb | fdfc3ce5c63305f79aa746b31c3be60f3d11a6acb75f190886124f2d3446db60 |
| retained.glb | aed8b3d4cb12aeaddf5c696a8a86355b15b7cb4fc8ebd76cc364d23789d630cc |
| south.glb | 4313826ddf5fbe0c0d8dcb4983d6cdbd647713d49faa1980cd34f587a3273a0e |
| D08.glb | 3ab933108b88c5c359fc7512d324e14f15157eaa54fb17f80f2adeb6c4626d9a |
| city-data.mjs | e4115705aeab28f2f6cc2635fbedfabf4158a08af9c626f6dd493ee27d430a1a |
| ground-atomic-contract.json | bfc7fc83c3d8f34c79e9395532b74c324987b4dbf0c4342328b7581ebc2be584 |
| road-plan.json | 9792f217619ef72f2cb7528856112c7403a765420814a0dfe562ad23a7ebd361 |
| measure_ground.py（本包） | e28e34a8e59209a9b3d2791f509b0e0ab4fb7ff7b6ca03e8d0f9f1dcbd3aae2e，改了脚本就重记 |
| LY-005 / LY-006 / LY-010 冻结文件 | 开工时填入；没有就不开工 |

measure_ground.py 每次运行都在 `nodes[].sha256_actual` 字段里重新计算 GLB 的 SHA，并和 city-data 声明的值比对。任何一项不同，判 FAIL。

## 1. 运行命令

```
node prep/scripts/make_config.mjs D:/GitHub/creation-notebook-lab scene-config.json
B="D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P prep/scripts/measure_ground.py --"
$B --config scene-config.json --ports ports.json --out base.json --ground-only
$B --config scene-config.json --ports ports.json --out full.json --grid 2.0
for n in ground-network-ground-stitched ground-retained ground-south ground-D08; do
  $B --config scene-config.json --ports ports.json --out drop-$n.json --ground-only --drop $n; done
```

制作时，ports.json 换成 LY-006 冻结的端口（保留 ID 和版本）。本目录的 ports.json 只是**临时探针**：14 个门槛点取自 network.json，门、市、仓的点取自 interface 文件的相机目标，另加两个负例点。

## 2. 参数与容差（全部为 C，不是规范）

| 项 | 值 | 说明 |
|---|---|---|
| 可走上表面 | 法线和竖直方向夹角 ≤ 20° | 网络交付时另报 20°–45° 的面（当前四件地面里为 0） |
| 顶点焊接 | 1 mm | |
| seam（同一表面的接缝） | 两侧高差 ≤ 0.02 m | |
| step（台阶边） | 0.02 < 高差 ≤ 0.18 m | 只进入容差图；严格图里不连 |
| drop / void | 高差 > 0.18 m，或探针下没有面 | 记为断点或禁用 |
| 边界探针 | 沿边界每 1.0 m 一个，向外偏 0.10 m，另加一个偏 4 mm 的微探针 | |
| 网格 | 2.0 m 一格，竖直射线，净空线 2.0 m | 只是线检查，**不是人体包络** |
| 人体包络（制作期新增） | 直径 0.6 m、高 1.8 m 的圆柱，沿已通边每 0.25 m 扫一次 | C 值，向 LY-006/010 报备后冻结 |

## 3. 正例（必须 PASS）

- P1 **已通边可追溯**：每条边 `{a,b}` 都要带三样东西：
  - 两侧分量各自的三角面索引集合，加上所属 GLB 的 SHA；
  - seam 探针的样本坐标列表；
  - 实测接缝长度 ≥ 0.6 m（人体宽）。

  抽出 10% 的边，用 `scan_line.py` 以 1 mm 步长横跨接缝扫描，扫描上必须连续有面。
- P2 **分量面积守恒**：各分量面积之和等于上表面三角面总面积。当前值是 192,877.81 m²，误差不超过 1e-3。
- P3 **基线复现**：在当前输入下必须得到以下结果，否则说明输入变了，先查输入：
  - 5 个上表面分量，主分量 174,298.76 m²；
  - 4 条孤立的 C 段：2,571.59、6,161.39、2,941.19、6,904.89 m²；
  - 分量间隙：3.761、4.292、56.202 m；
  - 33 个探针有支持。
- P4 **端口落点**：每个冻结端口必须同时满足三条：
  - 端口点 0.3 m 半径内全部有支持；
  - 竖直净空线没有被挡；
  - 端口所在分量是网络里的节点。

  端口还要按 LY-006 的字段同时写出本地坐标和世界坐标。
- P5 **人体包络**（制作期）：每条已通边扫过的圆柱都满足三条：
  - 脚下全部有支持（圆柱底面 9 个点都要打到面上）；
  - 和 obstacle 三角面（墙、院、门体）没有正体积相交，只用表面 BVH 时如实写明；
  - 最窄处宽度 ≥ 0.6 m。

  报告里要写清：这是离散的姿态采样，不是连续运动。
- P6 **焊接与裂缝如实登记**：T 型接缝长度（当前 879.78 m）和裂缝（当前 C_stitch_primary 内宽 4–62 mm、长约 4.2 m，位置 x≈397.94–398.01、y 1845.76–1849.94）必须出现在网络数据的 `defects` 字段里。不允许为了让测试通过而在网络层把裂缝悄悄合并。

## 4. 负例（必须 FAIL 或断开；任何一条没有触发，说明检查器失效）

- N1 **移除地面**：用 `--drop` 分别移除每一件地面，结果必须分别是：
  - 移除 stitched：剩 2 个分量，D08 单独成岛（10,320 m²）；广阳 3 个探针和 market-link 失去支持。
  - 移除 south：14 个门槛和门外 1m 共 28 个端口失去支持。
  - 移除 D08：D08-center 失去支持。
  - 移除 retained：主分量面积降到 89,770.76 m²。

  任何一项结果和这里不同，判检查器 FAIL。
- N2 **未建区域**：城中心 (1200,1900) 和北宫 B 区 (700,2400) 必须没有支持，也不属于任何节点。若把 road-plan 或 network.json 的 B/C 折线当作边加进图里，这两个点所在的格子仍不能变成可达。用注入测试证明这一点：故意把一条 B 折线写成边，检查器必须报「边无实际面」。
- N3 **展示底板**：把住宅原型的 site_lot、site_neutral_lane、designed_*，或仓储的 optional-functional-overlay.glb 加进 ground 角色，检查器必须报「非城景加载面」并拒收。依据是 city-renderer.mjs:309 会把 excludeNodes 剔除。
- N4 **互斥地面**：把 corridor-10m.glb 或 route-corridor.glb 和 6m 原子组一起载入，检查器必须因为互斥而拒收。依据是 road-interface 和 market-interface 都写着 Never overlay。
- N5 **原子性**：只载 network-ground-stitched 三节点中的两个，必须 FAIL。依据是契约 allNodesRequired，同 assertGroundAtomic 的规则。
- N6 **禁用边不可通**：以下间隙即使在容差图里也不能连通，除非 LY-010 追加放行，且有对应的补件 SHA：
  - C_3 和 C_4 之间 56.202 m（palaces_connector_B，立交方式未知）；
  - 各门点 cut：gate_jin 31.11 m，gate_zhongdong 49.29 m，平城北端 57.71 m；
  - 雍门 47.1–49.5 m（保护项，归原负责人）。
- N7 **裂缝注入**：把一块 seam 两侧拉开 0.05 m，必须出现 crack_4to100mm 记录；拉开 0.5 m，必须变成 void 或断点。
- N8 **坏输入**：GLB 的 SHA 不符、矩阵出现 NaN 或剪切、exclude 节点没有匹配上，三种情况都必须 FAIL。最后一条和 city-renderer「模型替换节点不完整」的规则一致。

## 5. 覆盖声明（交付时必须原样写出）

- 覆盖范围：当前 6m 原子组四件地面的上表面三角面（坡度 ≤ 20°）。探针沿边界每 1 m 一个，网格 2 m 一格。人体包络按每 0.25 m 一个离散姿态检查。
- 不覆盖：
  - 10m 互斥方案；
  - market、storage 和雍门 apron 的内部地面（只记它们和原子地面之间的接触）；
  - 连续运动、车辆转弯、坡道强度、GPU 和浏览器表现；
  - 古水系（B 仍为 null，所以记为「未知」，既不判「可通」也不判「禁止」）；
  - 历史路网。
- 不能宣称：「全城连通」「碰撞已穷尽」「已入城」（入城由 LY-100 决定）「结构安全」「历史成立」。

## 6. 按加载状态分别验收（2026-11-06 复核补充）

网络必须按**实际加载状态**分别生成。不能把多个章节的节点取并集，当作一个状态。

**生成状态配置**：

```
node prep/scripts/make_config_drift.mjs <cityDataRoot> D:/GitHub/creation-notebook-lab <prefix> [promoteIds]
```

- 这条命令会输出 `<prefix>-default.json` 和 `<prefix>-terrain.json`。生成时严格套用 city-renderer.mjs 的 :221（initial 过滤）和 :412-415（replaces 替换）。
- `promoteIds` 列出要额外当作 ground 处理的非 terrain 节点，例如雍门 apron。必须在报告里列明，不能默认提升。

**L1 状态绑定**：每份网络数据都要写 `loadState`（default / terrain / 其他章节）、city-data SHA、`replacedIds` 和节点清单。如果同一 asset 的两个 LOD 同时出现在 ground 里，判 FAIL；这种情况说明替换规则没有生效。

**L2 基线判定**：
- 如果 G 冻结在 bce3211，必须复现 P3，并且：
  - 冷开状态下 ground 数为 0；
  - 雍门 apron 和主分量之间的间隙为 49.579 m。
- 如果 G 冻结在 cad338b，必须复现以下全部结果：
  - terrain 状态（提升 `yong-gate-interface-far`）下有一个 174,987.43 m² 的严格区域，接缝分别为 6.939 m 和 6.0 m，dz 为 0；
  - 冷开状态下有 2 个主区域，面积分别是 84,528.00 和 21,183.17 m²，两者间隙 84.381 m；
  - 冷开状态下 43 个探针中有 6 个有支持；
  - terrain 状态下被挡格数为 1007。
- 如果冻结在更新的版本，就全部重测。重测时先用 `git diff --quiet <G> -- docs/cities/luoyang/assets/ground-atomic` 确认地面没有变化。

**N9 接街移除负例**（cad338b 起适用）：加参数 `--drop yong-road-link-near` 后，必须同时出现以下三项结果；任何一项没有出现，判检查器失效：
- apron 重新变成独立区域；
- apron 和主分量之间的间隙为 49.579 m；
- yong-in 失去支持。

**N10 冷开不可伪连**：冷开状态下，retained 和 receiver 之间相隔 84.381 m，不得出现任何已通边。不允许借 terrain 章的 network 把冷开状态的两个区域判为连通。

**N11 高处平台**：apron 上两块 +5.0 m 平台（各 34.41 m²），在补上上层登临之前，必须标记为「不可达·高差 5.0 m」。不能因为它们和地面的平面距离为 0，就生成边。

**要绑定的 SHA（cad338b 新增）**：

| 文件 | SHA256 |
|---|---|
| yong-road-link-LOD0.glb | 456a7dd54a5fd623ab17d9823ab1a12701bd764bdd219ec8884e9538536cd93d |
| yong-road-link-LOD2.glb | 2a32c700d401af623701a2ec84523ea2d7688fc9b5d128f22cae542a85b7b844 |
| yong-road-receiver-component209.glb | e5baa0df8fd28e117b4ef997cab0d962b0834a4c9664bb1ed73b7746d2488e38 |
| yong-apron-LOD2.glb | fb8a5f2f93aace63e0229cdc4a9c65d0c1450bb80bf8965e75da0fd92cad529a（运行时实测，与 city-data 声明一致） |

city-data.mjs 的 SHA 以 G 冻结时 blob 的 `git hash-object` 为准。本目录里抽取的副本是 `git show` 的文本输出，换行符可能被转换，不能拿来当绑定值。
