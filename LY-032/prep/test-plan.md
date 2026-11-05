# LY-032 测试计划（按「本项验收」写，制作时直接跑）

记号：`BL=D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P`；`P=D:/GitHub/creation-notebook-workpacks/LY-032/prep`；`G=D:/GitHub/creation-notebook-lab/docs/cities/luoyang/progress-assets/granary-city-v1`。
任何一项失败都不能改阈值来过关。阈值只能由 G（LY-010 的验收格式）修订，并写明修订版本。

## 0. 绑定的 SHA（开跑前先核对，不一致就停）

| 输入 | SHA256 |
|---|---|
| granary-city-LOD0.glb | 5937211c7366a5920ae222185176f198cc3d16e8763605fa248e61031c74bc93 |
| granary-city-LOD1.glb | a1265bbf53d10ddb6398efa6f505c1b6dee86b81b37397f7af9855acc34f2e45 |
| granary-city-LOD2.glb | 6b2564d3ffd76e6e982a4a7f703cfd0790ac0e0b2dfa75add4df169c4c82efe7 |
| granary-B-LOD0/1/2.glb | 407403ceeb418f6e1d3f0e86bff7d535642c0236d94691fd2b9a10c2f7866dc6 / 3ce46eee0c9b1ef56fcf380c4dfec3d39251697bab7cad45a719b19c06e6ce8a / 0735a9f2cc76cfef98f5e548ab621295e40870bd2aef248ce25cc10e0b10022f |
| storage-group-organized.glb（v1 回退） | b8482824513a101d36eb4c768a4f641e77aaac66c3e834718d7f3964104a644b |
| 脚本 m02/m03/m04 | 见 inputs.json 的 prepScripts；脚本一旦改动，就要重跑本节全部基线 |
| 门件 GLB（制作后填写） | `models/*.glb` 的实际 SHA 写进 qa/，每个结论都绑定这个 SHA |

## 1. B 单独实测（验收①：门口 / 6 阶 / 地板）

T01 基线复现：`$BL $P/m02_door_scan.py -- $G/granary-city-LOD{0,1,2}.glb out.json 2297.7141 -3676.969 B`
- 正例：jamb_x = [2296.9641, 2298.4641]、lintel_underside_y = 3.200、floor_y_inside = sill_y_outside_wall = 1.100、wall z = [-3676.969, -3677.169]，中线上有 6 个 0.150 的升高。容差 ±0.001 m。
- 负例：用相同参数扫 A（`2273.7141 -3676.469`），必须得到地板 0.850、4 个 0.1625 的升高。证明脚本不会把 A 认成 B。
- 门件装上后再跑一次：地板、台阶剖面、门侧壁的读数都不能变。门件不能改动 6 阶和 1.10 地板。

T02 仓体不变：`python -I $P/m03_baseline.py new.json <装配后基底…>`，与 out/baseline.json 比较。
- 正例：每个原有 primitive 的 sha_indices / sha_position / sha_normal / sha_uv0 和 `B_bay_sha_world_pos_uv` 全部相同；B 区三角数 LOD0/1/2 = 4948 / 476 / 368；timber 的 B 区三角 = 392 / 392 / 332。
- 负例：把门件节点并进 timber 后重算，B_bay 三角数必须变化。证明这项检查能发现「顺手合批或简化」。

## 2. 门件本身

T03 包络：门件 bbox 在 x ∈ [2296.6141, 2298.8141]、y ∈ [1.095, 3.605]、z ∈ [-3677.969, -3676.169] 之内。
T04 门叶下皮 ≥ 1.100 − 0.005，也不能低于外沿 1.10，不许插进地板。
T05 交体：`kb.overlap(base)` 给出的三角对必须逐个归类，只允许三类：(a) 枢/砧落在地板顶面 y=1.10 上的面接触；(b) 连楹/上枢贴在门楣或墙的内皮上；(c) 止挡贴在侧壁上。正体积侵入或完全包含一律阻断。只做了表面 BVH 时，不能说实体碰撞已经查完。
T05b 门件独立语义：每片门叶是独立节点，名字带 `B_door_leaf`，不和固定件合批；三档中门叶节点名一致。
T05c GLB 体检（每档、每个状态）：大小 ≤ 15,000,000 字节；没有退化三角；全部有限值；有 UV 和法线；材质有名字；LOD0/1 用 PBR，LOD2 和 timber 的 FLAT 对应；LOD1/2 不能是 LOD0 改名（三角数和 SHA 必须不同）。

## 3. 开门 / 关门负例（验收③）

运行：`$BL $P/m04_kit_check.py -- $G/granary-city-LOD0.glb out.json <closed|open|half> <kit.glb>`，在 LOD1/LOD2 基底上各重复一次。

| 编号 | 状态 | 必须 | 已用夹具验证能判败 |
|---|---|---|---|
| T06 | closed | 洞口内 29×19 根射线的阻挡率 ≥ 0.999 | 只有基底时 0.0 → FAIL；把 open 夹具当 closed 判 → FAIL |
| T07 | open | 0.9 条带 150 根射线被门件挡住 0 根；基底自身挡住也是 0 根 | 把 closed 夹具当 open 判 → 150 根被挡 → FAIL |
| T08 | open | 洞口阻挡率 ≤ 0.25 | closed 夹具 1.0 → FAIL |
| T09 | half（声明为负例） | 0.9 条带必须被挡（>0 根），证明半开不能当通行态 | 只有基底时 0 根 → FAIL；half 夹具 90 根 → PASS |

已跑过的夹具结果（out/kitcheck-*.json）：closed 1.0 PASS；open 0 根 PASS；half 0.6897 / 90 根 PASS；两个交叉负例都 FAIL；只有基底时 closed 和 half 都 FAIL。夹具门叶厚 0.06，缝 0.005，内开 90°。

T10 余量：开启状态下，门叶加枢、加止挡后到 0.9 条带边的距离 ≥ 0（几何上限是每侧 0.300），实际数值写进 qa/。如果 G 给的 0.9 条带坐标不是居中，就改 m04 的 STRIP 常量，并重跑 T06–T09。
T11 外开（如果采用）：门叶扫掠必须避开第 5、6 阶的踏面，门叶下皮在扫掠全程高于阶顶 1.10。同时要说明站在阶上的人会处在扫掠区里。这是局部通行问题，不是安全认证。
T12 1.8 m 压力条：装件后仍然失败（B 应约 77 处，由私源复算；从 GLB 复算时说明计数方法）。不能靠去掉门叶或柱子换来通过。

## 4. 沿用 A 件时（验收②）

T13 用 LY-031 的实际 GLB（绑定它的 SHA），只平移 (+24.000, +0.250, −0.500)，不缩放、不旋转，然后在 B 基底上跑 T03–T10。
- 正例：全部通过；门叶尺寸与 B 洞口差 ≤ 0.002。
- 负例：A 件不加 +0.250 直接放上去时，T04 必须 FAIL（门叶下皮 0.85 低于 B 地板，插进地板）。上枢件按 A 的 0.20 门楣做的，在 B 的 0.40 门楣上必须报告空隙或交体，并单独改成 B 件。
- 如果任一项要靠缩放才能过：判 A 件不兼容，B 单独做。

## 5. 撤回与互斥

T14 撤回：去掉门件节点后，T02 的全部 SHA 回到基线。
T15 互斥：城景件、旧 v1 件、归档分块三种基底之间，门件只声明其中一种（由 G 决定），绝不叠载两套门件或两套整组。

## 6. 不做的声称

CPU 渲染只写 CPU；没有在浏览器或 GPU 上跑过就不说已测。离散射线不等于连续人体或货物运动。门制属于 C 设计，不是太仓实测，也不代表约 180 年洛阳门制。
