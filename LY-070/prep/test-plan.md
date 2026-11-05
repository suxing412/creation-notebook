# LY-070 测试计划（制作阶段直接运行）

本计划对应任务池「本项验收」：
- 所有选中件都与地域准入相符，不出现多套宫殿叠加；
- LY-003 未通过时，只输出「仅局部组装」的明确状态，不能强行写成「完成宫区」。

另外还覆盖任务池总则的公共底线：三档、安装/撤回、接触分类、通行包络、15,000,000 B 上限和官方 checker。

**运行约定**
- 所有 Blender 检查使用 `D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P <script> -- …`。
- 坐标使用 Blender 世界系：Z 向上，单位米。城市矩阵按 LY-005 契约换回 glTF 系：+X 东、+Y 上、+Z 南，只绕 Y 旋转，缩放 1。
- 每项检查都写入 `qa/<id>.json`，内容包括：输入 SHA（提交字节）、脚本 SHA、Blender 版本、阈值、PASS/FAIL，以及至少一个负例的结果。
- 只报 PASS、没有跑负例的检查，一律视为无效。

## 0. 前置门（任一不满足 → 状态 `阻断`，不进入后续检查）

| ID | 检查 | 判据 |
|---|---|---|
| T0.1 | G 冻结 | LY-001/002/005/006/007/008/009/010 的 `status.json` 都是「交付完成」；把各文件的 SHA 记入 `inputs.json.upstream_workpacks` |
| T0.2 | 前置包冻结 | LY-061…069 都有 `status.json`，状态为「交付完成」或「复用完成」，且都有 `delivery-manifest.json`；每个引用的 GLB 都能按清单 SHA 复核 |
| T0.3 | LY-003 结论 | 读取 `LY-003/tables/admission.json`（23:5x 时 SHA `dd0ab8c018e714be…`）中 zone「北宫」「南宫」「两宫复道」三行的 `status`。只有三行都不是「不可落位」，且附控制点与误差，才算 `registered`；其余一律按 `not-registrable`。**23:5x 实测：三行都是「不可落位」**，北宫行 `allowed` 原文为「LY-070只交局部组装」。文件缺失或 SHA 变化时重读并写明差异 |
| T0.4 | LY-010 选型 | LY-010 为宫院区写明：选中方案、允许的未验项、`localDemoDomain` 的边界；没有选型就阻断 |
| T0.6 | 所有权（LY-006 registry v1） | 运行 `LY-006/source/validate_interface.py` 与 `check_registry.py`（SHA 见 `inputs.json.upstream_contracts`）。LY-070 的 `writeZones=[]`、`cutZones=[]`、`components=[]`：本包输出里**新增任何几何、地坪或切孔 → FAIL**；消费的端口只能是 registry 中列出的 5 个，多出或缺少 → FAIL；端口数值必须取生产方交付值，不能由本包自填（`local`/`world` 由本包写入 → FAIL）。负例：在 `assembly.json` 里加一块本包自造的盖缝板 → FAIL |
| T0.5 | 基线 | 重新读取 main HEAD；若不等于 `bce3211`，用 `scripts/build_inputs.py` 重算全部输入 SHA，并与本 prep 的 `inputs.json` 对比差异，差异逐条写明 |

## 1. 准入与唯一性（本项验收第一条）

| ID | 检查 | 正例 | 负例（必须 FAIL） |
|---|---|---|---|
| T1.1 | 每个选中件都有准入来源 | `assembly.json` 的每个节点都带 `admittedBy`（LY-010 条目 ID）和 `regionGate`（LY-003 结论） | 加入一个没有 `admittedBy` 的 yutang-A 节点 → FAIL |
| T1.2 | 殿堂互斥：一个殿位只放一套 | 选中节点里，前缀 `hall__deyang-A`、`deyang-A-*`、`deyang-B-*` 只出现一组；yutang A/B 只出现一组；它们之间的共享体积 < 0.01 m³ | 基准负例：候入院内嵌 deyang-A + 独立 deyang-B 同原点，0.1 m 网格共享体积约 **1545 m³**（`prep/out/containment-s5.json`）→ FAIL；候入院 + 独立 deyang-A → FAIL |
| T1.3 | 宫殿件不重复计件 | 卡片与清单里，同一 GLB 的 SHA 只出现一次；progress-assets 下的重复副本不算第二件 | 把 `progress-assets/palace-admission-court/*-LOD0.glb` 与 `library/…/files/*-LOD0.glb` 同时列为两个组件 → FAIL |
| T1.4 | 不使用被停用的 31 组重复宫殿，不使用实名 | 节点名、卡片字段、`assembly.json` 里都没有实名殿名或宫门名（以 LY-002 禁用表 X04/X05 的词表加「德阳殿 / 玉堂殿」作实名检查词）；`historicalPalace=null` | 在输出卡片里写「德阳殿」→ FAIL |
| T1.5 | 单一实验组 | `assembly.json` 只有一个 `group`，帧为 `local:palace-composite`，带闭合的 `bounds`（xz 多边形加 y 范围），所有节点的世界 bbox 都在 bounds 内（容差 0.01 m）。S-PALACE 的 `envelope` 在 registry v1 里是 null，所以 bounds 作为 envelope 提案提交 LY-006，经 `check_registry` 与其他场地包络互检交为 0 后才算通过 | 有一个节点越出 bounds 0.5 m → FAIL；bounds 与其他场地包络相交 → FAIL |

## 2. 状态输出（本项验收第二条）

| ID | 检查 | 判据 |
|---|---|---|
| T2.1 | LY-003 = `not-registrable` | 输出 `status: "localOnly"`，`cityPlacement: null`，不出现 `cityMatrix` 字段；README 和卡片文案里不出现「完成宫区 / 宫区已入城 / 南宫 / 北宫已落位」 |
| T2.2 | LY-003 = `registered` 且 LY-010 放行（**本轮不可触发**：LY-003 已判不可落位；保留本条只为将来复核） | 才允许出现 `cityMatrix`（4×4，只含 Y 轴旋转，缩放 1，所有平移有限）。平移必须落在 LY-003 给出的允许区内，误差字段从 LY-003 原样引用 |
| T2.3 | 负例 | 人工把 LY-003 结论改成 `not-registrable` 后再生成 → 产物里出现 `cityMatrix` 就 FAIL；`localOnly` 状态下写入 `city-data.mjs` 或项目卡的提案 → FAIL |
| T2.4 | 公共文件禁写 | 对 `D:/GitHub/creation-notebook-lab` 运行 `git status --porcelain`，前后输出一致（只读核对）；本包没有任何写往 lab 的文件 |

## 3. 装配几何（复用 prep 脚本，绑定实际 SHA）

| ID | 检查 | 正例 / 阈值 | 负例 |
|---|---|---|---|
| T3.1 | 原件不变 | 每个引用的原 GLB：SHA 与 `inputs.json` 一致；装配后回读每个节点的局部几何哈希（顶点、索引、UV、材质名），与原件一致；变换只施加一次 | 对某节点施加 1.001 缩放 → 回读不一致 → FAIL；同一矩阵施加两次 → 世界 bbox 偏移 → FAIL |
| T3.2 | 楼板对接（复道 A ↔ 登临节点） | `compose_probe.py` 在冻结变换下运行，三条剖线（y=−2.2/0/+2.2）没有无支承采样点（0.01 m 步长），相邻高差 ≤ 0.005 m。prep 基准：+6.0 m 时高差 0.000 | s2：B + access-A，高差 0.500 m → FAIL（证明检查器能分辨 A/B） |
| T3.3 | B 不套 A 节点 | 装配中 gallery-B 的端口只接 LY-068 的件；B 与 access-A 同组出现时 FAIL | 即 s2 |
| T3.4 | 接触分类 | 每对跨组件的面交（`compose_probe` 的 `cross_overlaps`）都要归入三类之一：合法局部接面（共面 / 贴合，体内共享点为 0）、正体积侵入（必须在白名单中写明位置和体积）、完全包含（必须 FAIL）。闭合件用 `seam_parts.py` 的精确 AABB 交，非闭合或 L 形件用 `seam_faces.py` 逐面判定，再用 `containment_probe.py` 0.02 m 网格交叉复核；三者不一致时以逐面结果为准，并写明差异。prep 基准（dx=6.0）：土构 2 处各 **0.001375 m³**（合计 0.00275，x 6.225…6.25、y ±(3.05…3.325)、z 0…0.2），必须由 LY-069 声明或消除；木构**实体交 0**，只有共面接触（x=6.0 端面、z=4.0 柱底）以及 0.01 m（梁端↔主板）、0.02 m（梁顶↔唇板）两条缝。容差：体积 1e-6 m³，位置按 LY-006 端口容差 0.005 m | 把 access-A 平移 +5.5 m → 共享体积明显增大，又不在白名单中 → FAIL；松散件 AABB 法对 L 形非闭合件给出的 0.02244 m³ 未经逐面复核就写成侵入 → 判为分类错误 |
| T3.5 | 触地支承 | 复道 A 的 16 块柱础、access-A 的 4 块台础和 2 块梯脚，逐块在冻结地坪（LY-067 交付或候入院平板）上做 −Z 射线：网格 0.05 m，底面覆盖率 ≥ 99%，间隙 ≤ 0.005 m。埋入部分（access 梯脚 z −0.2…0，帮脚到 −0.1302）必须有地坪切孔或「合法埋入」声明 | 移除 LY-067 地坪 → 16 块全部 FAIL；地坪下移 0.05 m → FAIL |
| T3.6 | 不加假底板 | 新增的地坪件面积不超过 LY-067/LY-061 冻结的范围；不存在覆盖整个组的展示底板（单块面积 > 组 bounds 面积的 50% → FAIL） | 加一块 40×40 m 平板 → FAIL |
| T3.7 | 未接端登记 | 每个楼板端口（A 两端 x=±6.0，z=4.0；B 两端 x=±4.5，z=3.5）要么接到冻结端口，要么列入 `openEnds[]` 并说明落差（A 为 4.0 m）。不允许出现没有登记的高处开口 | 删除 `openEnds` 里的 A 西端 → FAIL |

## 4. 通行（只做有限检查，不声称连续人体运动）

| ID | 检查 | 判据 |
|---|---|---|
| T4.1 | 声明的路线 | 只检查 `assembly.json.routes[]` 里声明的路线，例如「庭地 → access 梯 → A 楼板中带 → LY-069 端口」。人体包络取 0.6 m 宽 × 1.8 m 高（与 LY-006 冻结值不同时以冻结值为准）；沿路线每 0.05 m 采样：足下支承间隙 ≤ 0.005 m，单级高差 ≤ 0.2 m，头部净空 ≥ 2.0 m（prep：A 楼板最小 2.46 m） |
| T4.2 | 三带不全通的声明 | 侧带 y=±2.2 在 access 栏杆 x≈9.04（s1 世界坐标）处为尽端，必须写成「尽端」；若写成「三带可下地」→ FAIL |
| T4.3 | 主路线不被截断 | 若复道跨越候入院主路线：原 99 带 / 73 接口用 GLB 重建的等价脚本复验，任何一条不退化；柱础之间净宽 ≥ 声明值（prep：3.5 m），净高按梁底实测 |
| T4.4 | 负例 | 删除 access 梯的第 10 级 → 单级 0.4 m → FAIL；在中带放一个 0.3 m 立方体 → 包络 FAIL；关闭候入院门（closed 档）后，声明为闭门不可通的路线仍不可通 |

## 5. 三档与公共底线

| ID | 检查 | 判据 |
|---|---|---|
| T5.1 | 三档独立 | LOD0/1/2 各自完成 T3.2–T3.5 与 T4.1；不能拿 LOD2 的结果代替 LOD0。prep 已知：access-A 的 LOD2 梯级合并为每级 0.4 m（踏面顶 z 0.4…3.6，`prep/out/gallery-measure.json`），LOD0/1 为每级 0.2 m，所以 LOD2 不作通行路线，只作远景，必须写明 |
| T5.2 | 大小 | 每个输出 GLB ≤ 15,000,000 B；装配表不复制原件时，只核对被引用原件的字节数 |
| T5.3 | 回读 | 所有输出 GLB 用 LY-008 检查器回读：NaN、退化三角、缺纹理、路径隐私。必须连同 LY-008 的负例一起运行 |
| T5.4 | 官方 checker | 在 LY-100 合并分支上运行 `lab/tools/build_assets.py --check`。本席位不在 main 上运行 |
| T5.5 | 安装 / 撤回 | 在严格输入（原件按 SHA 锁定）上安装一次、撤回一次：撤回后原节点集合、矩阵、几何哈希、材质与安装前逐项相等；安装后不出现旧新方案同时启用（同一互斥组 >1 → FAIL） |
| T5.6 | 预览 | 同一机位做前后对比、反面和必要剖面（楼板接缝、柱础）。CPU 图标注 CPU；没有做 GPU 或手机测试就不写「已测」 |

## 6. 要绑定的 SHA（提交字节，制作时逐项复核）

- 复道 A：gallery-A-LOD0 `0c09279723e2334c…`、LOD1 `227c3c4ecc262562…`、LOD2 `cb26b56e1634f27a…`
- 复道 B：gallery-B-LOD0 `c7cb279cfd110315…`、LOD1 `fe72e192573df077…`、LOD2 `ff15e1c4ca8cb4f9…`
- 登临节点：access-A-LOD0 `c973d325d1d08cfd…`、LOD1 `7b5e26f443a1e1bc…`、LOD2 `b39c34c28ab38963…`、collision `7327547eee27c4c0…`
- 候入院：open-LOD0/1/2 `59c8b758…` / `d95bd22f…` / `01b2017f…`；closed-LOD0/1/2 `6ea89298…` / `455a1215…` / `108e28a5…`
- 殿堂：deyang-A-LOD0 `7736998077a8414f…`、deyang-B-LOD0 `6ef34781443e13cd…`、yutang-A-LOD0 `6e7f06c054d07984…`、yutang-B-LOD0 `92091dbe9c51e72b…`
- 全部 64 位 SHA 见 `inputs.json`。LY-061…069 的交付件 SHA 在 T0.2 时从各自的 `delivery-manifest.json` 补入。
- 脚本：见 `brief-draft.md` 第 7 节。制作时脚本若有改动，以新 SHA 为准，并保留 prep 版本用于对照。

## 7. 已知局限（写入 QA）

- BVH overlap 只检测表面三角相交。体内判定依赖网格闭合，timber 网格不一定闭合，所以「未发现正体积」不等于「无穿插」。
- 射线和剖线只是离散采样，不代表连续步态、轮椅、车辆、结构荷载或现代规范认证。
- 原生 .blend 和原检查器缺失，「原通行不退化」只能用从 GLB 重建的等价脚本复验，并照实标注。

## 8. 23:5x 复核新增的绑定

- 上游契约文件 SHA：`inputs.json.upstream_contracts`，共 18 项，例如 LY-003 `tables/admission.json` `dd0ab8c0…`、LY-006 `registry/seats.json` `a1426412…`、`ports.json` `28bcfb68…`、`seams.json` `ca4d81f8…`。制作时任一项 SHA 变化，就先重跑 T0.3、T0.6。
- 接缝基准脚本：`scripts/seam_parts.py` `53ea46a1…`、`scripts/seam_faces.py` `fa192c61…`；对应结果 `out/seam-parts-dx6.0.json` `b5cdbeb4…`、`out/seam-faces-accA-dx6.0.json` `e74db094…`。
- 复跑命令（只读，原件不改）：

```
D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P prep/scripts/seam_parts.py -- <out.json> <gallery-A-LOD?.glb> <access-A-LOD?.glb> <dx>
D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P prep/scripts/seam_faces.py -- <out.json> <glb> <dx> x0 x1 y0 y1 z0 z1
python -I prep/scripts/refresh_upstream.py D:/GitHub/creation-notebook-lab D:/GitHub/creation-notebook-workpacks prep/inputs.json
```
