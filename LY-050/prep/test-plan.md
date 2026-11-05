# LY-050 测试计划（制作时直接跑）

本项验收原文：「可复现单院完整包，无隐含源依赖；旧院数、矩阵与旁邻保持；恢复后指纹一致，所有采用设施都有使用限制。」

基线绑定：lab `bce3211f818ee5a8bef1773539da70695ba37b17`；city-data.mjs `e4115705…`；A2 LOD1 `277e9e73…`；A2 LOD0 `19b05202…`；ground-south `4313826d…`；基线指纹 total `50486e228fc5749c9a2087300eff4ff119c9ebc66ab87ecd265551e9c0502ef0`（prep/out/fingerprint-bce3211.json）。全长 SHA 见 inputs.json。
前置包：041–049 交付后，把它们 delivery-manifest.json 的 SHA 记进 qa/upstream.json。T0 不通过就不往下跑。

坐标：court:C02-010 = 世界坐标减去 (531, 0, -818.45)，yaw 0（LY-005 契约，LY-006 frames）。院坪基准 y = 0.200，不是原型剔除节点的 0.215。

| # | 检查 | 正例 | 负例（必须被拦下） | 容差 | 绑定 |
|---|---|---|---|---|---|
| T0 | 输入一致 | inputs.json 中每个 lab 文件的 SHA256 与磁盘一致；041–049 manifest SHA 与 qa/upstream.json 一致 | 改动任一输入的 1 字节 → 不通过 | 0 | inputs.json、upstream.json |
| T1 | 无隐含源依赖 | assembly.json 引用的每个文件，要么在 workpacks/LY-050/ 下，要么是带 SHA 的公开 docs 路径；公开文件中 grep `C:/Users`、`D:/`、`.blend`、`scratchpad` 都是 0 | 注入一条指向不存在文件或私密路径的引用 → 不通过 | 0 | delivery-manifest.json |
| T2 | 院数、矩阵、旁邻不变 | 安装后 `fingerprint.py diff 基线 安装后`，差异只能落在白名单里（C02-010 的资产字段或新增设施资产/节点）；residential 章节点数 = 44；44 院矩阵逐字相同；另外 8 个 A2 院（C02-001/013/015/021/024/028/031/035）和 C02-009/011/005/006 的记录 SHA 不变 | selftest 的 5 个负例（`fingerprint.py selftest` 必须 exit 0）；把设施节点标成 chapter:'residential' → 院数 45，不通过 | 矩阵 0（逐字） | fingerprint-bce3211.json |
| T3 | 撤回后恢复 | 撤回后 `fingerprint.py diff` 输出 `[]`，total 等于基线；A2 两档和 ground-south 的 GLB SHA 不变（LY-045 若切过孔，撤回必须恢复 4313826d） | 撤回时故意留一个设施节点，或者不恢复地面切孔 → 不通过 | 0 | 同上 |
| T4 | 一次只加载所选用途（互斥） | 每个互斥组加载数 ≤ 1：灶 A 或 B；新门叶和旧门叶（LY-042）；储藏候选（LY-047）；圈厕有孔态和地面完整态（LY-045）。加载的设施集合等于 LY-010 选定的用途清单 | 同时加载灶 A 和 B；加载未选候选；加载圈厕但孔下地面没切（孔被旧地面封回）→ 都不通过 | 0 | assembly.json exclusiveGroups |
| T5 | 空间：写入区、侵入、互相重叠 | 每个设施的足迹在它的 LY-006 写入区内（registry v1 或 v2）；在身体带 0.25–2.0 m 内和宿主墙、木作、台基的正体积侵入为 0；设施两两包围盒重叠 0，三角级侵入 0；合法面接触逐处列出 | 把设施向墙内推 0.05 m → 能检出；把储藏分区按 v1 的 LY-047 区放置 → 应检出放不下（prep 实测 0 个可放位） | 面接触 ≤ 1 mm 算接触，不算侵入 | measure_ly050.py 的区域与栅格逻辑（复用） |
| T6 | 足下支承 | 每个设施的底点在地面（打开 ground-south 时）上方的间隙 ≤ 2 mm，埋入 ≤ 2 mm；基准按 0.200 | 按 0.215 放置 → 灶 A 的 87 个、灶 B 的 88 个底点全部悬空 ≥ 15 mm，必须检出 | 2 mm | ground-south 4313826d |
| T7 | 出入与路线 | gate_to_main、yard_to_side 以及各设施取用路线（来自 044/045/047 的包）：半宽 0.4 m 走廊在身体带内阻挡 0 m²；足下覆盖 100%；阶差逐段列出（已知台基阶 0.22 m）；新件拼缝竖向错台 ≤ 0.05 m，除非声明为台阶；头顶 ≥ 2.0 m 的构件单列 | 在路线上放 0.3 m 方块 → 检出；yard_to_side 穿过的 LY-046 浅沟（prep 实测 0.64 m²）若下凹 > 0.05 m 又没有盖板或声明台阶 → 不通过 | 0.05 m 错台；栅格 0.05 m | layout.json 7528f0c8、probe_routes.py |
| T8 | 端口对接 | gate-boundary:road-end（LY-049，供 LY-082）、drip-outlet:drain（LY-046，供 LY-087）、service-opening（LY-048）：组装后的位置和方向与生产席交付值一致；没有出口时如实标「无出口」 | 端口偏移 2 mm，或方向偏 1° → 不通过 | 位置 1 mm，方向 0.5° | LY-006 ports.json 28bcfb68 |
| T9 | 加载机制 | 设施节点不带 chapter:'residential'（app.mjs:78）；聚焦 C02-010 时设施取近档（要么并进 C02-010 专用资产，要么由 LY-100 改近档规则）；地面与 C02-010 同进同出（LY-041 提案） | 默认视图院坪下 lotCoverage 0 却声称「已接地」；设施在聚焦时仍是远档却声称「近景完整」→ 不通过 | — | city-renderer.mjs fa0a8dcb :221/:412/:416 |
| T10 | 预算 | 每个 GLB ≤ 15,000,000 字节；报告近档合计字节和三角数（prep 上限：5,685,460 字节、宿主 6,532 加设施 20,748 三角）；注明贴图在城景渲染里被丢弃 | 用远档冒充近档、把 LOD0 改名成 LOD1 → 不通过（逐档 SHA 必须互不相同） | — | 各卡 GLB SHA |
| T11 | 使用限制 | assembly.json 中每个采用的设施都有 usageLimits（摘自卡片「限制与待解决」）和证据类别（C、类比或未知；引用 E-H01、X12、X24）；不出现燃烧、卫生、结构、人体合格的结论 | 删掉一条 usageLimits，或写入「防火合格」→ 不通过 | 0 | LY-002 evidence-ledger 237a4811 |
| T12 | 五件事分开 | 交付文本里分别写明：可读取、局部通行、入城、结构、历史复原；没有经 LY-100 合并前不写「已入城」 | grep「已入城」「历史复原成立」「结构安全」→ 命中即不通过 | 0 | brief.md |
| T13 | 官方检查 | 进合并队列前，由 LY-008 或 LY-100 跑 `lab/tools/build_assets.py --check`，结果绑定 SHA。本席位不在 lab 里运行 | — | — | LY-008 qa/official-runs.json |

运行顺序：T0 → T1 → 安装（overlay）→ T2、T4–T11 → 撤回 → T3 → T12。prep 里的脚本（measure_ly050.py、probe_routes.py、fingerprint.py）是 T2、T3、T5、T7、T10 的现成基础，制作时再加上设施底点和三角级侵入两个模块。
