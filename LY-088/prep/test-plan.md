# LY-088 测试计划（制作时直接跑）

对应任务池“本项验收”：每条事件/关系都要分开原文和现代解释，带时期或未知标志；资料层不添加河道网格，不改变可达网络。另外要满足总则：证据四类分开，五件事不互相替代，SHA 可追溯。

被测物（制作阶段产出，路径暂定）：`workpacks/LY-088/data/water-phasing.json`、`data/schema.json`；检查脚本放在 `qa/` 下，基线脚本沿用 `prep/scan_water.py`。

## 绑定的基线 SHA（bce3211，git blob）

| 对象 | SHA256 |
|---|---|
| evidence-geometry.json | `fa8b7002869e01e981d2b2679c327a2f1db957119e55537e06289ca59e5ba7c7` |
| city-milestones.json | `23b30e705ed780f676eb7fc69a8c06a08524d04dfd34021f93859a5aa370ccfd` |
| city-data.mjs | `c849706b6210813c74851b86cfd3353183a47badc0e019a1151247db1e34bf00` |
| app.mjs | `cc0379c02c97d9560898b16b26f05dec8f74fc27289fbb3f94074388ad2849d8` |
| ground-atomic/network-ground-stitched.glb | `fdfc3ce5c63305f79aa746b31c3be60f3d11a6acb75f190886124f2d3446db60` |
| ground-atomic/retained.glb | `aed8b3d4cb12aeaddf5c696a8a86355b15b7cb4fc8ebd76cc364d23789d630cc` |
| ground-atomic/south.glb | `4313826ddf5fbe0c0d8dcb4983d6cdbd647713d49faa1980cd34f587a3273a0e` |
| ground-atomic/D08.glb | `3ab933108b88c5c359fc7512d324e14f15157eaa54fb17f80f2adeb6c4626d9a` |
| data/west/road-plan.json | `0bc4528cbf354a18c5a74f9bbf4574bfc0ea0ee817516736e9d15ef5dca6881a` |
| data/west/ground-atomic-contract.json | `7f26720bf40fc8cd7f7d0b445398d889fcc70c407f7cc7e26e4acd0eb6332367` |
| LY-002 evidence-ledger.json | `237a4811acad3d7f6733d4c5c95a64df0b2c67adf48b2682264eb0f0c8512b77` |
| LY-002 snapshots hhs03 / hhs09 / hhs125 | `66a7e4d7…` / `150f2160…` / `e33c9395…`（全值见 inputs.json） |

开工时先重读最新 main。只要上表有一个 SHA 变了，就先重跑 `prep/scan_water.py`，更新基线后再继续。不能拿旧 SHA 去报通过。

## T1 结构：每条记录都有必需字段（schema 校验）

- 每条 `event` / `relation` 必须有：`id`、`originalText`（逐字，≤60 字）、`originalLocator`（书名、卷、本子、URL 或快照 SHA）、`originalAuthorEra`（例如“范晔·南朝宋”）、`modernInterpretation`（可以为 null）、`modernSource`、`evidenceClass`（取值只能是 `original`、`analog_other_place_or_period`、`C_design`、`unknown` 之一）、`periodTag`（取值只能是 `eastern_han_dated`、`eastern_han_undated`、`cao_wei`、`western_jin`、`northern_wei`、`modern`、`unknown` 之一）、`yearCE`（数字、区间或 null）、`yearBasis`（取值只能是 `explicit`、`context_inferred`、`unknown` 之一）、`statusAt180`（取值只能是 `attested`、`not_attested`、`unknown` 之一）、`placement`（只能是 `none` 或 `label_only`）、`disputes[]`。
- **正例**：王梁条写 `originalText="及渠成而水不流"`、`yearBasis=context_inferred`、`statusAt180=unknown`，校验通过。
- **负例**：删掉 `modernInterpretation` 键（不是设成 null，而是整个键不存在），必须失败；`evidenceClass="likely"` 必须失败；`placement="polyline"` 必须失败。
- 容差：0，任何一条不合格就整表失败。

## T2 原文逐字核对

- 有本地快照的条目（hhs03、hhs09、hhs125，以及 LY-002 的条目）：GB18030 解码，去掉标签和空白后做子串匹配，必须命中，并记录命中位置。
- 只有 WebFetch 转述的条目（王梁传、张纯传、水经注·穀水）：制作前要先由协调者授权取得本地快照，记下 SHA，再逐字匹配。没有快照的条目一律标 `quoteVerified=false`，而且不能把 `evidenceClass` 标成 `original` 来算通过；顶多算“原文·待核”。
- **负例**：把“水不流”改成“水大流”，必须失败；把北魏郦注的话填进 `originalText`，同时把 `originalAuthorEra` 写成东汉，T5 必须拦下。
- 容差：逐字匹配，异体字（註/注、陽/阳、穀/谷）按显式写出的映射表对照，映射表随包提交。

## T3 原文与现代解释分开

- 同一条记录里，`originalText` 中不能出现 `modernInterpretation` 里的任何一个连续 8 字以上片段，反过来也一样。
- 黄学超 2026 只能出现在 `modernSource` 一栏，并带 `readStatus=abstract_only`。
- **负例**：把“东汉、魏、晋、北魏分期”写进 `originalText`，必须失败。

## T4 不画河道：资料层零几何

- 被测 JSON 里不能有 `coordinates`、`geometry`、`polyline`、`depth`、`velocity`、`flow_rate`、`width_m` 这些键（递归检查）；数值字段只允许 `yearCE`。
- 交付白名单里不能有 `.glb`、`.gltf`、`.obj`、`.blend` 文件。
- **基线不变**：重跑 `prep/scan_water.py`，要求：
  - `riverOrCanalMeshInEnteredCity == []`；
  - `enteredCityGlbWithWaterNames` 仍然正好是那 4 个 TC03 文件，SHA 和上表一致；
  - `enteredCityGlbCount == 34`（如果 LY-100 已经合入别的批次，以当时的新快照为准，但本包本身不能让这个数变化）；
  - 四片原子地面、road-plan、ground-atomic-contract 逐字节一致。
- **负例**：在临时副本的 JSON 里塞一个 `geometry: {type: "LineString"}`，T4 必须失败；在临时 GLB 列表里加一个名叫 `yang_canal` 的 mesh，`riverOrCanalMeshInEnteredCity` 必须非空。

## T5 时期与禁用

- `periodTag=northern_wei` 的条目不能有 `statusAt180=attested`。千金堨、太和年间的碑铭只能标 `northern_wei` 或 `cao_wei`。
- 涉及今洛河的条目（X15）只能是 `evidenceClass=unknown`，或者 `excluded=true`。
- **“奏请罢渠”专项**：任何 `kind=petition` 的事件，都不能派生出 `abandonedYear`，也不能写 `statusAt180=not_in_use` 或“干涸”字样（中英文关键字都要 grep：罢渠已行、废、干涸、dried、abandoned）。负例：写 `abandonedYear: 1xx`，必须失败。
- 明堂“壍中无水”和郦注“引水为辟雍”必须做成一条 `relation`，`disputes` 至少列两方，不能合并成一条结论。
- 辟雍环水必须保留“北无”和“考古未见闭合”两条，不能出现 `closedRing=true`。

## T6 可切换且可撤回（非几何资料）

- 交给 LY-100 的接入提案只能是两种：开关默认关闭的文字/列表面板，或者 v1 那种 null 几何文字条目。在被测页面的离线副本上：开关打开时，DOM 新增的只有文字节点，Three 场景的对象数和三角形数与关闭时相同（差值为 0）；关闭后 DOM 恢复原样。
- 没有真浏览器测试，就只写 CPU 或静态检查，不能声称 GPU 或手机已测。
- 本包不修改 city-data.mjs 和 app.mjs。T6 只在 `workpacks/LY-088/` 下的临时副本上跑，跑完删掉临时副本。

## T7 与已有研究去重

- 每条记录都要有 `reuses` 字段，指向 `evidence-geometry#ancient_water_corridors_B_unplaced`、`city-milestones#P2`、`LY-002#E-H03` / `E-P07` / `E-R03` / `E-R05` 中的一个，或者写“新增”并说明为什么新增。
- 和 LY-002 同出处的条目，结论不能与 LY-002 冲突；如果有冲突，写进 `disputes`，并交 LY-002 和 LY-100，本包不自行改动 LY-002。

## T8 SHA 绑定与产出清单

- `qa/checks.json` 里每项检查都写上被测文件的 SHA256、脚本的 SHA256 和基线 SHA 表。
- 统一用 git blob SHA；如果本机 CRLF 检出导致不一致，同时列出两个值，不能只写 CRLF 值（避免重复 LY-001 C8 那个问题）。

## 2026-11-06 补充（上游 LY-003/004/006 交付后）

### 追加绑定 SHA

| 对象 | SHA256 |
|---|---|
| LY-003 tables/admission.json | `dd0ab8c018e714be1366cb491107ff09131e5e176b9106894a2e5b2b86e88dd3` |
| LY-003 tables/control-points.json | `a92fff1937d3823f0cbae622d87751f6b0fc518b0074481f0a6b8cdbefe26307` |
| LY-004 tables/site-constraints.json | `633c3302ff1219e8d93d2a59107eae85a6d7c077f418f7b53300f642708eb77f` |
| LY-002 source/snapshots/hhs02.html | `96b9128099e2e44642e88cfeafd37965ead747a1ce03fe13feb15e41cd3523df` |
| LY-006 registry/seats.json | `a1426412c84cab875713a63846fc9c487c6d01a9f8c445d5268c02187d959069` |
| prep/scan_drift.py | `dab9387aba18e3d6cee614f4df69dd22c63824947174eebe7c01e2023e78549c` |
| lab origin/main 漂移参照 | `cad338ba683f7277aea098f45c8feb6c915a847c` |

### T2 补：异体映射表必须包含 `爎→壍`

- **正例**：明堂条的 `originalText="四面起土作爎，上作桥，爎中无水"`，在 hhs02.html 中按 GB18030 解码，原样子串命中 1 次。`normalizedText` 用映射写成“壍”，并记录 `variantNote="来源站字形爎，读作壍"`。
- **负例 1**：`originalText` 直接写“壍中无水”，又没有映射记录，逐字匹配必须失败（来源字节里 0 次命中）。
- **负例 2**：映射表里出现 `爎→壍` 以外、未在包内列明的替换，必须失败。

### T9 落位状态与 LY-003 一致

- 凡是 `reuses` 指向 `ancient_water_corridors_B_unplaced`、CP-08 或 CP-09 的记录，`placement` 必须是 `none` 或 `label_only`，并写 `admissionRef="LY-003 admission 宫墙水道 不可落位"`。
- 辟雍环水（BY3、BY7、BY8）和明堂壍（MT4）的记录必须带 `admissionRef="LY-004 P06/明堂"`，并写 `statusAt180=unknown`（BY7、BY8 原报告未读，分期未核）。
- `periodTag` 必须与上游一致：CP-08 写 `eastern_han_undated`，并在 `disputes` 中列出报道里汉、魏晋、北魏几期并列；CP-09 写 `unknown` 或 `han_jin_unsplit`（**这个枚举要新增**，T1 的 periodTag 枚举随之加上）；Q13 写 `northern_wei`，并加 `excluded=true`；NJ9 写 `northern_wei`。
- **负例**：把 CP-09 标成 `eastern_han_dated` 必须失败；把 Q13 挂到太仓条目必须失败；任何记录出现 `controlPointUsable=true` 必须失败（LY-003 给的是 false）。
- 容差 0。

### T10 漂移重跑

- 开工第一步：`python -I -X utf8 prep/scan_drift.py D:/GitHub/creation-notebook-lab bce3211 <LY-001 届时快照> qa/drift.json`。
- 通过条件：`diff.waterNamedGlbAdded == []`，`diff.riverCanalGlbAdded == []`，且 evidence-geometry 的 blob SHA 仍为 `fa8b7002…`。如果 evidence-geometry 变了，先重读它的水系条目，再更新 `reuses`。
- 11-06 实测（bce3211 → cad338b）：GLB 引用 71→81，新增水名 GLB 0 个，新增河渠名 GLB 0 个，evidence-geometry 未变。T10 现在就能通过；以后用新快照重跑时，结果作为基线写入 `qa/`。
- **负例**：在临时副本的 city-data 里加一条 `'.../yang-canal.glb'` 的引用，并让它指向一个 mesh 名为 `canal` 的 GLB，`riverCanalGlbAdded` 必须非空。（只在 `workpacks/LY-088/tmp/` 下用 `git worktree` 之外的拷贝做，不碰 lab。）
