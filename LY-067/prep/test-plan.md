# LY-067 测试计划（按「本项验收」逐条可执行）

所有命令在 `D:/GitHub/creation-notebook-workpacks/LY-067/prep/` 下运行，用 `python -I`，只读仓库。
每次运行先复核绑定 SHA。SHA 不一致就停，不比较结果。

## 0. 绑定 SHA（开工时逐一复核，不符即阻断）

| 对象 | SHA256 |
|---|---|
| gallery-A-LOD0.glb | 0c09279723e2334c35f21c7602c195cc867d97808ac0f99ccf6f0208d3ff3849 |
| gallery-A-LOD1.glb | 227c3c4ecc2625629d00ef6beb274575587e4f1095f68b7a50359781e94b3e68 |
| gallery-A-LOD2.glb | cb26b56e1634f27a878d83997649804eaeef29f5a0bb1420b8aa959a65e137ea |
| access-A-LOD0.glb | c973d325d1d08cfd53c129df5270f6276677694a5d4a96cab35fde47d3d11076 |
| access-A-LOD1.glb | 7b5e26f443a1e1bcecd47c7e2072aaf00d2496c944afe6bfa4068ce72553834b |
| access-A-LOD2.glb | b39c34c28ab38963be7bc90ff2650eb6360eb71d4a1d16a294c76ab344809fd9 |
| access-A-collision-candidate.glb | 7327547eee27c4c0bb259b757de4533c95f640600c94882c24b881bd8b8a8209 |
| 城市地面 network/retained/south/D08 | fdfc3ce5… / aed8b3d4… / 4313826d… / 3ab93310…（全长见 inputs.json） |
| LY-006 registry zones.json / ports.json / seats.json / ownership.json | 6b3595ac735d180866e823ddeb4e3676ffc0e816d083f6be2d57d6e4df0821c0 / 28bcfb68cd7d7fe0026f62de23ae3e45ba8f714a139e38c0b0957039f12fc633 / a1426412c84cab875713a63846fc9c487c6d01a9f8c445d5268c02187d959069 / ecbbbcf5614d41bf7c7bf3b04416504ae70891e212c7551456de4ff1a417b4ca |
| LY-005 coordinate-contract.json / port-schema.json | b6d7fe9db9523569383bf656df39aef63e7d80e8a1d5877196ba0bcab8747712 / 30854ed927c6088ce4a5c89c38097086ae5227769b314673ad81dcb29480332f |
| LY-008 ly_check.py | **开工时重绑**（准备期内 SHA 已变过一次：fda345d4… → 4beeaf57…；以 LY-008 status.json 写明的冻结版为准） |
| 局部演示域地面 GLB、矩阵 JSON、端口 JSON | **待 G（LY-005/006/010）给出**，要求是 G 冻结版本的 SHA，不能是 LY-067 自己产出的 |
| 旧柱脚未支持记录 | **待协调者提供**；缺失时 T2 走「依赖缺失」分支 |

## T1 柱脚清单重建（「逐脚」的基准）

`python -I measure_footings.py feet.json <A-LOD0> <A-LOD1> <A-LOD2>`

- 正例：每档 post_count=16、plinth_count=16、components_touching_min_y=16。柱础 0.50×0.50×0.20 m，柱底与柱础顶面间隙 |gap| ≤ 1e-4 m。三档 16 个中心逐个相等，容差 1e-4 m。
- 负例：数量 ≠ 16，或三档中心不一致 → FAIL。这说明输入已不是基线 A，要停下来重新核对来源。
- 交叉复核：`D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P bl_import_check.py -- bl.json <三档>`，16 个网格中心底面都在 Z=0。

## T2 逐脚对账（旧记录 ↔ 新结果）

- 有旧记录时：旧清单的 16 个 ID 要和 A-F01…F16 一一对应，按本地 XZ 匹配，容差 0.01 m。缺 ID、多 ID，或匹配不上 → FAIL。每脚输出一行：旧状态（未命中）、新状态（支持 / 基础接口 / 缺失）、新支持件的 SHA、测量值。
- 没有旧记录时：输出 `old_record: missing`，同时列出 16 脚的「新」一侧结果。整体状态最多只能写「部分对账」，不得写成完成。

## T3 实际支持（`check_feet.py run`）

`python -I check_feet.py run support.json <A-LOD0> <演示域地面.glb> <matrix.json>`

- 判据：每脚 9 个采样点，即底面四角（各内缩 10 mm）、四边中点和中心。竖直射线落到支持面顶部，gap = 柱础底 − 支持顶，满足 −5 mm ≤ gap ≤ +5 mm 才算 PASS。16 脚 × 9 点全部 PASS，才能称这只脚「有支持」。
- 防假底板：同一个支持连通件如果垫在 2 只或以上的脚下，又不是 G 冻结的地形资产（以 SHA 判定，不认标签），就判 FAIL「shared plate」。`declared_terrain=true` 只能用于 SHA 属于 G 冻结的地面（城市地坪按 LY-006 归 LY-090；S-PALACE 演示域地面归 LY-070/LY-010 指定，目前 envelope=null）的情况。
- LOD1、LOD2 用同一矩阵重跑，结果必须与 LOD0 相同。
- 自检必须先过：`python -I check_feet.py selftest st.json <A-LOD0>`，期望 N1 无支持 0/16、P1 每脚垫块齐平 16/16、N2 垫块低 3 cm 0/16、N3 单块展示底板 0/16、P2 声明地形齐平 16/16、N4 缺 A-F07 15/16，即 all_selftests_ok=True。准备期已实测通过（`selftest-check_feet.json`）。

## T4 旧城市地形依赖（必须如实报缺）

`python -I probe_ground.py probe.json probe-points-connectorB.json <四块城市地面>`

- 当前基线结果：示意线 10/10 未命中；对照组 2/2 命中 y=0.2；ground bbox 外负例 0 命中。
- 判定：只要宫区城市地面仍不存在，或 LY-003 不放行，报告就必须写「城市地形依赖缺失 → 不入城」。不能用演示域里的结果代替城市支持。
- 负例：如果有人把演示域地面直接当城市地面登记，并且它不在 city-data.mjs 的冻结地面之中 → FAIL。

## T5 A 既有木梯不变

- access-A 四个 GLB 的 SHA 与第 0 节逐字节相同；交付白名单里不得出现 access-A 的任何新版本。
- 前提：要有 access-A 到 gallery-A 的变换，由 LY-069/070 或协调者给出。准备期查过，这个变换不存在。没有这个变换时，本条只记「不可测」，不得写成通过。
- access-A 在地面以下的部分（`zone-measure.json`）：2 块梯脚垫 y 从 −0.20 到 0，2 根梯帮 y 最低 −0.130。变换给定后，检查它们是否落进 LY-067 写入区。如果落进了，本席位的基础件必须避让，与这 4 件的体积交为 0；不能改木梯来迁就。
- 装配后在演示域坐标下实测：access 平台顶面 y = A 楼面顶面 y，|Δ| ≤ 1 mm（基线都是 4.0）；梯脚垫底面相对演示域地面的嵌入深度要如实报告（基线比 A 的 y0 低 0.20 m），不能悄悄改。
- 负例：把 access-A 平移 0.05 m 后重跑，平台高差检查必须 FAIL。

## T6 写入区与防假底板（`zone_check.py gate`，按 LY-006 冻结边界）

先跑自检：`python -I zone_check.py selftest st-zone.json <LY-006/registry> <A-LOD0>`。期望 `all_selftests_ok=True`，即 P1 每脚外扩 0.20 m 的垫块通过，N1 外扩 0.25 m、N2 铺满整区、N3 单块高出地面 2 cm、N4 一条垫两只脚都判 FAIL。准备期已经实测通过（`selftest-zone_check.json`）。

正式跑：`python -I zone_check.py gate gate.json <LY-006/registry> <A-LOD0> <support.glb> [support_to_gallery.json]`，以下逐个连通件判定，容差 1e-4 m。

- G1：AABB 在 `LY-067:write:001` 之内，即 x ±6.45、y −0.6..0、z ±3.824。
- G2：顶面 y ≤ 0，只能在地面以下。柱础由 LY-006 规定为 keep，不准改，也不准在 y > 0 处加任何东西。
- G3：单件平面面积 ≤ 0.81 m²，相当于柱础 0.5 m 外扩 0.20 m。这个上限是 C 值，LY-006 改写入区时同步改。
- G4：单件不能同时压在 2 只或以上柱础的平面范围下。
- G5：所有件的并集面积 ≤ 12.96 m²。基线数据：写入区 98.66 m²，柱础 4.00 m²。

`gate_ok=False` 即 FAIL，不能凭标签或「C 演示」豁免。G1–G5 只限定本席位能写什么；脚下到底有没有支持，要看 T3。

体积侵入与撤回：

- 新件与 gallery-A 实体之间只允许和柱础底面（y=0）共面接触。正体积侵入大于 1 mm³，或出现完全包含，都判 FAIL。只做了表面 BVH 的，要写明这一点。
- 在严格输入上安装一次再撤回。gallery-A 和 access-A 的节点、几何、材质、矩阵 SHA 都不能变。
- 新地坪件一律命名为 `gp:LY-067:<name>`，名字不合规则判 FAIL。

## T6b 端口填写（`gallery-A:feet:ground@v1`）

- 交付时按 LY-005 的 port-schema 填 local 值：16 个脚的柱础底面中心，形如 (x, 0, z)。依据是 `footings-A.json`，容差为平面 0.005 m、高程 0.002 m。还要写 `measuredFrom`，给出 GLB 路径和 SHA。
- world 和 nodeMatrixColumnMajor 写 null，并注明「frames.local:gallery-A placement=null；PZ-02 open」。
- 负例：world 写了任何数值却没有 LY-003/010 的准入，判 FAIL；portId 或 version 与 seams.json 里 `gallery-A:feet:ground@v1::LY-067->LY-069` 对不上，也判 FAIL。

## T7 交付规范

- 单个 GLB ≤ 15,000,000 字节，米制，Y 向上，纹理内嵌，材质用 LY_P01 语义（等 LY-007）；三档不得由复制改名得到。
- 官方 `lab/tools/build_assets.py --check` 只在合并队列由 LY-100 运行，本席位不运行。
- 报告只写实测范围。没有做 GPU、手机、结构或连续人体测试，就不写这些项目已通过。
