# LY-087 测试计划（制作时直接跑）

运行环境：`python -I`（numpy 2.4.6），全部脚本都在本 prep/ 目录。lab 仓库只读，不跑 build_assets.py。
SHA 绑定：每次运行先比对 inputs.json 中的 `sha256` / `commitSha256`，任一不符就停下重测，不沿用旧数字。

## T0 输入锁定
- `python -I make_inputs.py`，再与上次的 inputs.json 做 diff。正例：23 个 lab 输入（其中 16 个 GLB）和 1 个 workpack GLB（辟雍关系块 1bd1c446）的 SHA 不变（11-06 复核：全部相同；上一版写的「19 个 GLB」是笔误），文本文件按**提交字节**比对（city-data.mjs c849706b…，city-renderer.mjs 04c6c643…，app.mjs cc0379c0…）。
- 负例：把 CRLF 工作区字节当作提交字节去绑定，必须判不一致（city-data.mjs 工作区是 e4115705，提交是 c849706b）。
- 已绑定（11-06）：LY-006 registry/ports.json 28bcfb68cd7d7fe0…、seats.json a1426412c84cab87…、ownership.json ecbbbcf5614d41bf…、schemas/port.schema.json 9fcdf932adbb4cdc…；LY-003 tables/admission.json dd0ab8c018e714be…；LY-008 source/ly_check.py 39aaa491859e1a79…。任一变化都要重跑 T2 registry 模式。
- 到时额外绑定：LY-010 冻结件、LY-046/052/054/073/081 的 delivery-manifest SHA。
- 漂移检查：`python -I drift_scan_cad338b.py <LY-001 新快照提交>`。正例：排水类命中 0，6 个 TC03 节点块不变。负例：如果新快照新增带 drain/沟/渠 名字的节点，或者 6 个节点块变了，必须先重跑 T1–T3 再继续。

## T1 坡向从实际顶点重算（对应验收：无倒坡）
- `python -I measure_drain_ports.py`。每段排水件的槽底取各端面的最低内侧顶点，坡度 =（高端 − 低端）/ 长度。
- 正例基线：6 个城市节点 × 2 档，坡度 0.1484% 或 0.1603%，远近档三角哈希一致（2739cd13e8b5df72 / b4b891d7470da637）。
- 判据：每条已接边的落差都必须 > 0（容差 0；槽底读数精度 1e-4 m）；落差 ≤ 0 判 R2 失败。宫墙水道全程落差 0，**不能作为已接边**。
- 负例：`fixtures/fx-neg-backfall.json` 必须报 R2。

## T2 来源与去向状态（对应验收：每个出口都有来源和去向）
- `python -I make_port_registry.py`，然后跑 `python -I check_port_graph.py fixtures/current-*.json <交付图>`。
- sourceState 只能取 {roof-drip, surface-runoff, upstream-port, channel, none-declared, unknown}；destState 只能取 {connected, local-sump, ponding-flat, blocked, unconnected-declared, void, unknown}。
- 判据：缺状态（R1）、去向为 void（R1）、标了 connected 却没有出边（R1），都算失败。
- 基线：首屏状态 6/6 的低端是 void，`current-bce3211-default-firstscreen.json` 期望报 R1；地形章节状态 6/6 是 ponding-flat，记为「未接」，不算「已排出」。
- 交付时首屏和地形章节**两种加载状态都要测**。
- **registry 模式**（LY-006 v1 冻结后加）：`python -I check_port_graph.py --registry D:/GitHub/creation-notebook-workpacks/LY-006/registry <交付图>`。
  - R8 正例：LY-006 列出的 4 个消费端口（C02-010:drip-outlet、stable:drain-outlet、kiln:front-drain、biyong:bank-outlet，都是 version 1）在图里各有一个 `registryPortId`，ownerSeat 等于 registry 的 producer，kind=drain（`fx-reg-pos.json` 通过）。
  - R8 负例：少一个端口（`fx-reg-neg-missing.json`），版本号 2≠1（`fx-reg-neg-version.json`），把 LY-073 的端口记到 LY-087 名下（`fx-reg-neg-producer.json`），都必须报 R8。
  - 当前基线：首屏 R1×6 + R8×4，地形章节 R8×4（4 个端口都还没交）。交付前地形章节必须清零 R8；首屏的 R1 只有在端口所属席位交出支承面之后才能清，本席位不能自己补地面。
  - 6 条现有 TC03 浅沟没有 registry 端口：如果 LY-006 出了 v2 给它们补登，也要把这 6 个加进 R8 的完整性检查；没补登就只出现在只读台账里，不进对缝。

## T3 终端的实际落点与阻挡
- 低端外 0.02/0.05/0.10/0.25/0.5/1/2/2.9 m 处取最高支承面（高度 ≤ 槽底 + 0.30），分别记城市地面和院内节点；在槽底 + 0.03 处顺流向发水平射线，6 m 内找第一阻挡。
- 基线：落差 -0.002 m；第一阻挡为 2.51 m 外的夯土前墙（6/6）。
- 新出口（LY-046/052 的端口）判据：落点支承面必须存在，台阶 ≤ 0（不能逆台阶）；端口与下游面之间的缝 ≤ 0.005 m。下游面就是阻挡墙、又没有涵口时，判 blocked。

## T4 不得自动接河（R4）
- 任何指向 kind=river/canal 的边，两端都要带 LY-003/LY-088 的 admittedOutlet=true 才算通过。
- 负例：`fx-neg-autoriver.json` 必须报 R4。另外用 grep 检查交付文本，不得出现「流向洛河」「接入阳渠」之类的断言（X15）。

## T5 循环与动画掩盖（R3/R5）
- 对有向图做 DFS 找环，必须为 0。
- 闭合水体（辟雍方形水符号 360/360 方位有水）只能是静态符号，并带 E-R05 的争议说明，否则判失败。
- 动画：在交付 overlay 的 JS 和 GLB 里检索 animations、UV offset、requestAnimationFrame 中的流动参数。凡是落差 ≤ 0 的边或闭合环上带动画，都判 R5。
- 负例：`fx-neg-cycle.json` 报 R3，`fx-neg-anim.json` 报 R2 和 R5。

## T6 所有权（R6）与对缝（R7）
- 每个 ownerNodes 只能属于一个席位（按 LY-006 表核对）；本项只拥有 `ly087_*` 节点。
- 对缝两侧的 portId 和 version 必须相同，位置差 ≤ 0.005 m，槽底差 ≤ 0.002 m。
- 负例：`fx-neg-owner.json` 报 R6，`fx-neg-seam.json` 报 R7。
- **R9（本席位不得持有几何）**：LY-006 seats.json 里 LY-087 的 writeZones、produces、ownsCityNodes 都为空。图里只要出现 ownerSeat=LY-087 且带节点，或者任何 `ly087_*` 节点，就判失败。负例 `fx-reg-neg-ly087geom.json` 必须报 R9。registry v2 如果给了写入区，R9 自动放开，但新节点还要通过 LY-006 的 check_registry 写入区互检。
- 对现有几何（ownerSeat=`existing:*`）：每个节点在 ownership.json 里都必须是 frozen，否则发出警告，本席位只能读这些节点。

## T7 地形不能当出口
- 跑 `out/B-terrain-fall.json`。任何「顺地形排走」的去向，都必须指到一个坡度 > 0 的连续面，并且有下游端口。
- 10 个回升 ≥1 mm 的局部低点只能记为 ponding。平坡面积占比 82–100% 的区段，不承认地形定义的流向。

## T8 安装与撤回（局部演示组合）
- 在严格输入上装一次 overlay，再撤回一次。撤回后 6 个 TC03 节点的矩阵、excludeNodes、GLB 的 SHA 必须逐字节不变；新旧方案不得叠载。
- 宫墙水道没有准入就不写世界位置，只在本地组合里做相对对缝。

## T9 终端距墙对账
- `python -I reconcile_wall_gap.py`。基线：TC03 / TC03-2 沟低端到前墙内面 2.50 m、外面 3.00 m，墙厚 0.50，墙顶 2.40（`out/E-wall-gap-reconcile.json` 9317c521…）。容差 0.01 m。
- 用途：如果哪个前置席位报的「终端到墙」数字和这里差超过 0.01 m，先确认它量的是内面、外面还是中线，再判是不是真的有差异。

## T10 包级规范（LY-008）
- `python -I D:/GitHub/creation-notebook-workpacks/LY-008/source/ly_check.py package D:/GitHub/creation-notebook-workpacks/LY-087` 加 `privacy`。本席位不交 GLB，所以 glb/lodset 不适用；如果交了任何 GLB，就说明 R9 被违反了。
- 负例：在 delivery-manifest.json 里加一个不存在的文件或一条私密路径，必须判失败。

## 全量回归
`python -I make_port_registry.py && python -I make_fixtures.py && python -I check_port_graph.py fixtures/*.json && python -I check_port_graph.py --registry D:/GitHub/creation-notebook-workpacks/LY-006/registry fixtures/*.json`。
当前基线（11-06）：两种模式下 16/16 都符合预期，rc=0（`out/check-port-graph-baseline.txt` bb27e9ea…，`out/check-port-graph-registry.txt` 1677fb62…）。上一版 11/11（59bfd8b5…）已经作废：那一版的正例让 LY-087 持有 `ly087_sump_a`，与 registry v1 冲突，现在已经改归 LY-046。

## 不做的认证
不测水密、流量和卫生，不测 GPU 或手机；表面射线不等于实体碰撞穷尽；局部一致也不等于已入城或历史复原成立。
