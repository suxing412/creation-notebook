# LY-048 测试计划（制作时直接运行）

所有脚本放在 `D:/GitHub/creation-notebook-workpacks/LY-048/prep/`，只读打开输入，产物写入本席位目录。`<LAB>` 指 `D:/GitHub/creation-notebook-lab`。制作阶段把宿主 GLB、差异件 GLB 和装配后的回读 GLB 都换成**实际导出文件**的 SHA。

## 0. 前置绑定

制作开始前必须写入 `qa/bindings.json` 并逐项比对的内容：

- `city-data.mjs` 的 SHA256，现为 `e4115705aeab28f2f6cc2635fbedfabf4158a08af9c626f6dd493ee27d430a1a`。若 main 已变，要重新导出 `city-courtyards.json`（导出命令见 §6），再重跑 T1–T7。
- 选定院 ID、asset 和矩阵。草案是 C02-010 / courtyard-A2 / `[1,0,0,0,0,1,0,0,0,0,1,0,531,0,-818.45,1]`，以 LY-041/010 冻结值为准。
- 宿主原型 SHA256。以 A2 为例：LOD0 `19b052022b2f6955e4a72f1a48280f7f8c229e11f001aa02ac95e357b890d9c7`，LOD1 `277e9e73e8f2d8b8e07ec828671d37cc7c9e3f1653dcebfe4290c51de412d85d`。
- ground-south 的 SHA256：`4313826ddf5fbe0c0d8dcb4983d6cdbd647713d49faa1980cd34f587a3273a0e`。
- 前置包冻结 SHA：LY-042 门叶、LY-043 端接、LY-044 灶包、LY-045 圈厕包、LY-047 储藏包，以及 LY-005 端口、LY-006 所有权。任一缺失就判**阻断**，不开工。
- 声明规则表 `qa/opening-rules.json`，每个开口一条：`{id, side, from, to, kind: main|side, states: [open, closed?], who: person|goods, portId}`。

## T0 检测器自测（每次改脚本后都要跑）

```
python selftest_closure.py qa/selftest-closure.json
```

- 正例：closed 0 段；front_gate 1 段，宽 2.95 ± 2 格；side_gap_12cm 1 段；low_wall 在 y ≤ 0.953 时为 0 段、y ≥ 1.453 时为 1 段；threshold 在 0.233 时为 0 段、0.353 时为 1 段。
- 负例：leaf_closed 为 0 段；side_slit_4cm 为 0 段。后者记录的是检测下限，**不是**密闭证明。
- 要求 `allPass: true`。当前结果文件 SHA `effee94477fd5e9f8d85e96c9483614746d3e7b693ad96ffae29256745c0d300`。

## T1 基线复现（原样输入，证明现状）

```
python measure_closure.py <LAB> qa/baseline-closure.json 0.05
python measure_closure.py <LAB> qa/baseline-closure-0025.json 0.025
```

- 6 原型 × 2 档 × 6 高度，每格都恰好 1 段与院心连通的边缘开口，都在 front(+z)。宽度：A 为 3.325..6.275；B/B2 为 −6.275..−3.300；TC03/TC03-2 为 7.525..10.500；A2 为 −4.975..−2.000。容差 ±0.025 m。
- 不与院心连通的边缘段为 0。
- `shaMatchesCityData` 全部为 true。
- 本 prep 已跑出的结果：`measure-closure.json` SHA `9d0dc238088776a4e86448312ca2194192386108a0ad3f315191e815af143932`，0.025 m 版 `e706e9f9b86073f044edb6c752dc07a080157666b227676da13d90c21f9073a2`。
- 若结果与此不同，说明 main 变了，先查原因，再继续。

## T2 围界与声明规则一致（装配后）

把宿主保留节点、差异件，以及选定的 LY-042/043/044/045/047 件按 assembly.json 合成一个回读 GLB，由 `measure_closure.analyse_nt` 读取。T2–T4 的包装脚本到时写入 `qa/`，复用本目录的函数。逐高度检查：

- 正例：每个与院心连通的开口都必须对应 opening-rules 里的一条，侧边相同，起止误差不超过 ±0.05 m。
- 负例：任何不在规则表里的连通段都判**阻断**，并报告侧边、位置、宽度和高度。
- 低墙收口：若某段只在 y ≥ 1.453 时连通，就分类为"低墙可越"，必须在规则表里写明 `kind: low-wall`（不可通行，但可越过）。不能假装它是闭合的。
- 门槛：主口或侧口若声明有门槛，那么 y = 0.233 时必须不连通，y = 0.353（或声明的槛顶以上）时必须连通，槛顶高度由顶点直接读出。
- 两档：LOD0 与 LOD1 的开口集合必须相同，容差 ±0.05 m。LOD2 若入城，也要相同。

## T3 关闭态

- 只有规则里声明了 `closed` 的开口才测。把门叶置于关闭姿态，所有高度上该开口都必须为 0 段（栅格 0.025 m）。
- 缝隙精确检查：用门叶与框和槛之间的最短距离（顶点到面），不靠栅格。阈值是 C 工作值，例如人或货不能通过的 0.10 m，要写进报告，并说明不是防盗、隔声或结构公差。
- 负例一：门叶处于开启态时该开口必须连通。
- 负例二：把门叶平移 0.15 m 制造人为缝，必须被检出。
- 互斥：主门新门叶（若做）与 LY-042 房门门叶分属不同开口，不同时加载同一洞口的两套门叶。逐洞口列出门叶清单，重复即**阻断**。
- 若规则声明"主门无关闭态"：T3 只检查规则表和页面说明里写明了"不存在关闭态"，不输出"已关闭"结论。

## T4 工作路径与地面边界

- 路线：主门与侧口（若有）到 LY-044/045/047 声明的作业点，用实际身体或货物包络。人用 C 工作值 0.60 × 1.70 m；货用 LY-047 给的包络。沿折线按 0.10 m 步长取样，每步检查三项：
  - 净宽：用截面栅格，y = 0.953 与货物高度两层。
  - 净高：门洞楣下 y = 2.25，净高 2.05 m。
  - 足下支持：向下射线命中地面或台基，与上一步的高差不超过 C 值，例如 0.18 m 且要写出。
- 已知数值：C02-010 门框净宽 2.10 m，比旧档案 2.3 m 小 0.20 m。货物包络宽度超过 2.10 m 时，主门不能走货，需要侧口；这条结论要在报告里写明。
- 地面：在加载 ground-south（及选定院所用的地面原子）的状态下，门下、侧口下和院外 0.25 / 1.0 / 2.5 m 处都要有地面命中（`boundary_strip.py` 的探针）。门下 y 为 0.199–0.200（±0.005）。
- 负例一：去掉地面原子再测，地面必须报**缺**。这证明住宅章节初始无地面的问题不被掩盖。
- 负例二：侧口外若落在邻院地块里，或与 LY-049 的端口带重叠，判**阻断**。
- 侵邻：差异件包围盒加 0.05 m，与所有其他 43 院的地块矩形相交即**阻断**。C02-010 左右各留 5.0 m 间距。
- 双层地面：差异件的地面片与 ground-south 在 XZ 上重叠，且高差在 0.02 m 以内，即判"叠层"，**阻断**。门外地坪属于 LY-049/082，本项不铺。

## T5 安装与撤回

- 安装：只在选定院加差异件，其余 43 院的矩阵、节点、三角数和材质原样不变（对 city-data 导出做逐字段比较）。
- 撤回：去掉差异件后重跑 T1，结果必须与基线 JSON 逐字段相同（只有 `inputs` 里新增文件的 SHA 不同）。
- 若侧口要求隐藏原墙节点，就要实际删除一次、恢复一次。恢复后墙节点的三角多重集与原 GLB 相同，顶点误差不超过 1e-6 m。

## T6 交付检查

- 每个 GLB 不超过 15,000,000 字节。三档分别导出，不把 LOD0 复制改名充当其他档。
- 跑 UV、法线、闭合/退化检查，以及 LY-008 检查器。
- 跑官方 `lab/tools/build_assets.py --check`。这一项只由 LY-100 在合并分支上跑，本席位不跑。

## T7 不得混说的五件事

报告分五栏，各自有证据或写"未测"：

1. 模型能读取：回读 GLB。
2. 局部通行通过：T4 的折线取样，不是连续人体运动。
3. 已入城：只有 LY-100 合并后才算。
4. 真实结构安全：不测。
5. 历史复原成立：不成立，属于 C 设计。

## 6. 重新导出 city-courtyards.json

在 `<LAB>/docs/cities/luoyang` 下运行：

```
node -e "import('./city-data.mjs').then(m=>{const rel=u=>u?u.replace(/^.*docs\/cities\/luoyang\//,''):undefined;console.log(JSON.stringify({source:'city-data.mjs',assets:m.assets.filter(a=>a.id.startsWith('courtyard')||a.id.startsWith('ground')).map(a=>({id:a.id,path:rel(a.url),sha256:a.sha256,nearPath:rel(a.nearUrl),nearSha256:a.nearSha256,excludeNodes:a.excludeNodes,sourceContract:a.sourceContract})),courtyards:m.nodes.filter(r=>r.asset&&r.asset.startsWith('courtyard')).map(r=>({id:r.id,asset:r.asset,matrix:r.matrix,chapter:r.chapter,initial:r.initial,sourceGroup:r.sourceGroup,sourceContract:r.sourceContract,bounds:r.bounds,variant:r.variant})),grounds:m.nodes.filter(r=>String(r.asset||'').startsWith('ground')).map(r=>({id:r.id,asset:r.asset,position:r.position,chapter:r.chapter,initial:r.initial,sourceContract:r.sourceContract}))},null,1))})" > <prep>/city-courtyards.json
```

当前文件 SHA `ba9d3294cd7df5ca543697ab4c6b13856b7caa59de4cc2405ae1ce7bde17c96b`。

## T8 写入区与所有权（r2 新增，依据 LY-006 registry v1）

```
python zone_fit.py <LAB> D:/GitHub/creation-notebook-workpacks/LY-006/registry/zones.json qa/zone-fit-host.json
```

**绑定输入**：
- LY-006 registry v1：`zones.json` `6b3595ac735d180866e823ddeb4e3676ffc0e816d083f6be2d57d6e4df0821c0`，`ports.json` `28bcfb68cd7d7fe0026f62de23ae3e45ba8f714a139e38c0b0957039f12fc633`，`seams.json` `ca4d81f8f955333c089d782aa69c50c2ca83225d4da07f595f66d1ba87f3f4c1`，`ownership.json` `ecbbbcf5614d41bf7c7bf3b04416504ae70891e212c7551456de4ff1a417b4ca`，`seats.json` `a1426412c84cab875713a63846fc9c487c6d01a9f8c445d5268c02187d959069`。
- LY-005：`coordinate-contract.json` `b6d7fe9db9523569383bf656df39aef63e7d80e8a1d5877196ba0bcab8747712`。
- 制作开工时若任一 SHA 变了（例如出了 v2），先重跑本节和 T1，再动手。

**基线复现**：用宿主原型跑出的结果必须与 `zone-fit-C02-010.json`（`35ce723a…`）一致：
- 墙节点 220 个顶点，落在 LY-048 区内的 3 个；
- 门框木构 32 个顶点全部落在 LY-049:write:001；
- 环带上不属于 LY-048 的取样点：四角各 8 个（LY-043），门道 16 个（LY-049）；
- `ly048YFloor` = 0.25。

**装配后正例**：对每个差异件 GLB 跑同样的顶点归属检查（脚本加 `--part` 包装后放进 `qa/`），差异件全部顶点都要落在 LY-048:write:001–005 内，容差 1e-6 m。

**负例**（每一项都必须被判为阻断）：
- 差异件有顶点进入四角（LY-043）或门道 x −5..−1、z 9..12（LY-049）；
- 差异件底部低于 y = 0.25（进入 LY-041 基底层）。如果门槛或墙段必须从地面 0.20 起，必须先拿到 v2 区；
- 任一新地面片未按 `gp:LY-048:<name>` 命名，或落在本项写入区之外；
- 隐藏或替换 `architecture_C_whitebox_earth_wall.001` 等宿主源对象，而 `seats.json` 中 LY-048 `ownsSourceObjects.modify/replace` 仍为空；
- 侧口门外的落脚点不在任何冻结的 ground 端口或 road-end 端口上。现状是：东、西侧外为 ground-south（归 LY-090），没有道路节点。

**注入负例**：把门槛样件平移到 x = −3.5、z = 11.5，必须报 LY-049 越区；把墙段样件底面放在 y = 0.20，必须报 LY-041 越区。

**端口**：交付的 `C02-010:service-opening:opening` 同时写 local 和 world，world 用 N = `[1,0,0,0, 0,1,0,0, 0,0,1,0, 531,0,−818.45,1]` 重算，残差不超过 5 mm（平面）和 2 mm（高程）（LY-005 E3）。高程在实际地面网格上用竖直射线量（E2），门下 ground-south 0.199–0.200。kind = opening 只能通过 LY-006 的 `schemas/port.schema.json` 校验，LY-005 的 `port-schema.json` 不含 opening；以哪份为准由 LY-008 判定，报告里两份的结果都要写出来。

**主门关闭态归属**：`opening-rules.json` 中主门的 states 要与 registry 对上。v2 若没有指定院门门叶的负责人，主门只能声明 `states: [open]`。T3 对主门只做“规则写明无关闭态”的检查，不得输出“已关闭”。

## T9 复跑记录（prep r2）

- T0：`python selftest_closure.py <scratch>/selftest.json`，ALL PASS，约 3 s。
- T1：`python measure_closure.py <LAB> <scratch>/mc.json 0.05`，约 7 s。与 `measure-closure.json` 去掉时间字段后逐字段相同。
