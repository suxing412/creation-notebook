# LY-098 历史表述与完成量终审 · 开工准备草稿（第二轮）

阶段：开工准备。G 还没有冻结：LY-010 目录不存在；LY-001/002/005/006/007/008/009 的 status.json 都自报“交付完成”，但在 workpacks 分支上都没有提交（`git status` 为 `??`），按“未冻结”处理。LY-091—094 只有 prep。所以这一步不出终审结论，也不改任何公共文件。

本轮在上一轮（2026-11-05 22:19）的基础上做了四件事：
1. 在同一基线上重跑主检查器和自测，确认结果逐字段可复现。
2. 实测主检查器的覆盖面，发现它只读 9 个城景文本文件，另有 48 个带公开中文的文件没读。为此补了检查器 `ly098_surface.py`（R15–R18）。
3. LY-002 已经交了证据与禁用表（未提交）。补了 `ly098_ledger_join.py`（R19/R20），把禁用表接到公开文字上，并按成员卡核绑定。
4. 两个新检查器都写了负例和正例，自测 28/28 和 8/8，并在 bce3211 和 cad338b 上各跑一遍。

## 1 本项目标（任务池原文要点）

- 产物：核对卡片、章节、说明、证据层和计数，输出逐条更正清单。
- 边界：有据、类比、C、未知四类要分清；模型、入城、可通行、结构安全不能互换；艺术封面不能当作现况或考古证据。
- 验收：名称、年代、计数、章状态和证据都要有来源；已建模、已入城、可达、结构安全没有串用；未验事项仍写在公开说明里。
- 依赖：G、LY-002、LY-091、LY-092、LY-093、LY-094。按批次求依赖闭包，每次只审本批 manifest 的 `selected_tasks` 和 `dependency_closure`。

## 2 基线与字节口径

| 项 | 值 |
|---|---|
| 终审基线（任务池指定，也是 lab 检出的 HEAD） | `bce3211f818ee5a8bef1773539da70695ba37b17` |
| 本机 `origin/main` 跟踪引用 | `cad338ba683f7277aea098f45c8feb6c915a847c`，比基线多 3 个提交（r2026.11.05-6/7/8）。LY-001 写的是“bce3211 = origin/main”，现在本机引用已经不是这样。本席位没有联网，不知道远端是否又有更新，所以 cad338b 只做漂移对照 |
| 本地 `main` 引用 | `44c66da`，已经落后，不用 |
| 字节口径 | 一律用 git 提交 blob（`git show`），不用检出字节。本机开着 autocrlf，city-data.mjs 提交是 106,463 B，检出是 111,034 B |

## 3 核到的现有成果（提交字节 SHA256）

| 文件 | SHA256 | 作用 / 是否被城景加载 |
|---|---|---|
| docs/cities/luoyang/p-luoyang.asset.json | `8edb06abf5e7d874334a932e3108079590b327ec5afbb78290df2f66424f95bd` | 项目卡（资产库项目页） |
| docs/cities/luoyang/city-data.mjs | `c849706b6210813c74851b86cfd3353183a47badc0e019a1151247db1e34bf00` | 城景数据；app.mjs L1 import |
| docs/cities/luoyang/index.html | `cfbf73763675397dde8f5ab08bb13f6b51fbcfa9954227552e32be756666b1bf` | 城景页静态文字 |
| docs/cities/luoyang/app.mjs | `cc0379c02c97d9560898b16b26f05dec8f74fc27289fbb3f94074388ad2849d8` | index.html L115 加载 |
| docs/cities/luoyang/city-renderer.mjs | `04c6c643e44f007e2f579842bfc9d943038a0e5a30aa6776624b432bb9fecbcc` | app.mjs L177 动态 import；证据层笔触与状态提示。**上一轮没核** |
| docs/cities/luoyang/scene.mjs | `00114cb9112da34194ef47f371d0850ac4fa55d5db87fea5084b9a7a3064e6b9` | 资产库项目页的 3D 便签 |
| docs/cities/luoyang/README.md | `e31b11a20f8a637f51fe1ba5cb49e4a3c490b0241e2163ab9fe26ece7396f56b` | 带日期的建城日志，无代码加载 |
| docs/cities/luoyang/assets/posters.json | `633142d86e0fb318d46c950c636a48fb2959bb6f0466598761f6970f687cb670` | 海报出处 |
| docs/cities/luoyang/assets/city-overview.webp | `93454110e79ba62efcc6cdb7a9373035313dac0933fdd9bd52adb8274df91743` | app.mjs L270 全城海报 |
| docs/cities/luoyang/assets/west/wall-city-direct-A.png | `83fdbbaedef9fb3f8930fae17e4b897578023b4bbc6b9c9c0dfe4f6ca7c8c1bf` | 上图的出处原图，2026-11-03 提交 51bb74c |
| docs/cities/luoyang/project-stage-contract.json | `fd284f15ccb466e5999366fad5be3d7ce2f5648c7fc99a7920caf4225668dcdb` | validation：gpu=false、realMobile=false、continuousGlobalCollision=false |
| docs/cities/luoyang/data/research-unplaced.json | `27f9e7f3429eccd8e7b5cbc1f5bbf88019a90ee9191c090b067d838d1a7bb43b` | 设计快照“circa 180 CE before 185 southern-palace fire” |
| docs/cities/luoyang/data/evidence/evidence-geometry.json | `fa8b7002869e01e981d2b2679c327a2f1db957119e55537e06289ca59e5ba7c7` | 证据层，含 gate_xuan_B“旋门”；city-data provenance 记它的 SHA 为 662562fa…（见缺口 G-N4） |
| docs/cities/luoyang/data/west/city-wall-constraints.json | `e9c84bddc7bb7d867e3ba8abf8cbeb604b222ad0960901f32e979dbb995e0af3` | 城垣约束，也有“旋门”；v1/wall-layer.mjs L15 链接 |
| docs/manifest.json | `0d14a81237c16f9ab5ffffa75d3f9405d372157ab643298f2d3a1ab6af30a9ee` | 全站机读清单 ongoingProjects，最后修改 2026-11-03。**上一轮没核** |
| lab/data/assets.json | `53d863121bb583b362bf9929bf18c1d91aaf6f36fb8d3808e70a8a3e4825df78` | 资产库汇总（提交版） |
| 55 张成员卡、其余公开文字文件 | 逐个见 `inputs.json`、`baseline/bce3211/surface.json` 的 files | 49 张在 docs/library/models/，6 张在 docs/model-library/ |

上游工作包（workpacks，未提交，只作对照）：
- LY-001 status `a32d742a…`，family-ledger `8eaa7c7a…`，54 个家族。
- LY-002 status `0ac63db8…`，evidence-ledger.json `237a4811…`，family-binding.json `3aeddcc0…`，selftest `88c55da0…`：33 条证据、24 条禁用（X01–X24）、9 条仓库出入（D-01—D-09），其中 D-02、D-07 指名交给 LY-098 处理措辞。
- LY-005—009 status 自报交付完成；LY-010 不存在。

## 4 改 / 不改范围

- 改：只写 `workpacks/LY-098/`（现在是 `prep/`）。
- 不改：lab 仓库、city-data、项目卡、资产卡、UI、证据层。更正清单只是提案，由 LY-100 合并。
- 本席位不判断历史事实对不对。史源和用字裁定归 LY-002（例如“旋门/旄门/秏门”），宫区和礼制能否落位归 LY-094。本席位核四件事：公开表述和实测是否一致；五件事有没有串用；证据层有没有定义；每条公开说法能不能追到 LY-002 的条目。
- 不重建几何，所以不需要私密源包。

## 5 证据与未知

- 原始考古或原文：本席位不重查。LY-002 已经逐字核了 132 条原文摘录，本席位只接它的条目 ID（R20）和禁用项（R19）。LY-002 自己也写明：原考古报告没有读，礼制数字都是二手转引。
- 异地或异期类比：项目卡的证据图例没有“类比”这一级（R08）。LY-002 的等级有五级（有据（文献）、考古（二手）、推断、C、未知），卡片只有三级（有据、推测、未知），两者还没有对应表。
- C 工程设计：city-data 有 3 处 `tier: "C"`，图例里没有这一级。city-renderer.mjs L140 `isInferred` 把 `'C'` 和“推测”画成同一种笔触（R08b，本轮新测）。
- 未知：research-unplaced.json 里 12 个要素的 renderable 都是 false。

## 6 实测到的真实缺口

### 6.1 主检查器基线（bce3211，上一轮结果，本轮重跑一致）

命令：`python -I prep/tools/ly098_audit.py --ref bce3211… --latest origin/main --out <dir>`。重跑后 report.json 的 rules、facts、findings、inputsRead 和存档逐字段相同。selftest 重跑结果也和存档相同（22/22）。

- 14 条规则里有 5 条 FAIL，共 16 条 FAIL、41 条 WARN、51 条更正草稿（`baseline/bce3211/report.json`、`corrections.json`）。
- 主要 FAIL：城景页和便签里有 6 处“六门 / 六座城门研究候选”，卡片写的是“城门研究 10 座”（R07）；city-data 有 3 处说“只有一座广阳门门体”，实测门体 2 座（R07）；有 3 处写“六章 / SIX CHAPTERS”，实际 7 章（R07）；雍门已经入城，研究视图里还是“已建研究候选”（R05）；礼制章是“已建模”，城市节点 0 个，引导语却是“记进城中”（R03）；tier=C 没有图例定义（R08）；限制里没写真实手机未验（R11）。
- 计数（R04）：14 件（12 段城垣加 2 座门体）、44 院（36+8）、8 处（GLB 节点前缀算出 5 店 3 摊）、1 组仓储、4 件地面，5 条都和实测一致。

### 6.2 覆盖面缺口（本轮新测，`ly098_surface.py`）

- docs/cities/luoyang/ 在 bce3211 有 154 个文本文件。主检查器只读其中 9 个，另有 **48 个带中文的文件、共 2,587 个中文句段没扫**（cad338b 上是 50 个文件、2,663 个句段）。这 48 个里包括城景直接加载的 city-renderer.mjs、成员卡链接的 progress-assets/*/README.md 和 source.json、旧版档案 v1/*，以及研究页 research/2026-11-03/*。
- 在未覆盖文件里抽出 192 个命中句段：计数 147 条，硬词带否定 26 条，未否定的硬词 0 条，软词带范围 15 条，软词没有范围 4 条（R15 WARN），属于介词或几何用法、豁免的 2 条。
- **G-N1（R16）**：证据层 evidence-geometry.json 和 city-wall-constraints.json 的东面南门写作“旋门”（gate_xuan_B），站内其他地方都写“旄门”。全城海报 city-overview.webp 的画面里烧进的标签也是“旋门”（人工看图核实）。LY-002 D-01 独立得出同一结论：“旋门”是成皋关隘名。
- **G-N2（R08b）**：city-renderer.mjs L140 把 `'C'` 并入“推测”笔触。所以图上 C 工程设计和推测分不开，图例里也没有 C 和类比。
- **G-N3（R17）**：全站机读清单 docs/manifest.json 的 ongoingProjects.city-luoyang 标题是“洛阳 · 证据之城”，项目卡标题是“洛阳”。它最后修改于 2026-11-03T14:32，项目卡最后修改于 2026-11-05T18:51。它的描述和边界还停在“C02 换入变体、屋顶覆盖 5.10%”阶段，没写雍门和章节。evidence 指向 project-notes.html，这个页面已经重定向到 v1 旧版说明。
- **G-N4（R18）**：city-data.mjs 的 provenance.sourceContracts 一共公开了 13 对路径和 SHA256。其中 12 对只和 CRLF 换行后的字节相符，和提交字节（也就是线上实际提供的字节）不符，只有 progress-assets/flat/source.json 一对相符。cad338b 上也是 14 对里 12 对。这是“版本可追溯”的缺口，修口径归 LY-096/099，本席位只报告。
- **G-N5（海报，人工）**：全城海报（app.mjs L269–271，配的说明是“城垣、门体与院落沿原有位置展开”）的原图是 2026-11-03 渲染的。画面底部烧进了“已有14院与广阳局部更细”，标题是“土垣 A＋广阳短斜接”。基线实测是 44 院入城、门体 2 座（广阳门、雍门）。alt 只写了广阳门，和画面一致，但页面把它当作“这一版”的全城图，没有标明日期。

### 6.3 史源接入（本轮新测，`ly098_ledger_join.py`，LY-002 未冻结，只报数）

- R20：项目卡 55 个成员里，52 个能经 LY-001 家族或卡片 ID 接到 LY-002 的 facts。**3 个没有绑定**：m-gate-roof-study、m-eaves-shell、m-passage-interface（都在 docs/model-library/，是构件研究卡）。LY-002 绑了 54 个家族，没有覆盖这 3 张卡，要回传 LY-002 补“未知/C”条目。
- R19：在 68 个公开文本里扫 X01–X24 的关键词，命中 11 次，其中 8 次已有限定（INFO），3 次要人工复核（WARN）：
  - 项目卡 summary 写“市与里坊”，对应 X07 和 D-07。“坊”是北魏以后的用语，要不要改由本席位终审时决定。
  - palace-admission-court/evidence.md L31 的“东掖门”。所在文档其他句子已经排除了它的形制，可能是误报。
  - m-luoyang-kaiyang-gate 卡 L44 的“洛河”，说的是基址被今洛河破坏，没有把今河道当作 180 年水系，可能是误报。
- R19 没有 FAIL：公开文字里没有把“旋门”当门名，也没有把北魏门名当东汉门名。“旋门”只出现在数据层和海报画面里（G-N1）。

### 6.4 漂移对照（cad338b，不是终审基线）

- 主检查器：节点 77 个、47 院、8 章。新增 7 处“44 院已入城 / 44 座院落已经布置”和实测的 47 院不符。基线上的 16 条 FAIL 一条也没修。C 层从 3 处增加到 15 处。
- surface：多出 north-three-v1、yong-road-link-v2 两个 README。“实测响应体 1,408,005 字节”是技术实测，按豁免处理，不算 FAIL。G-N1 到 G-N4 都还在。

## 7 结论草案（准备阶段）

- 复用判定：没有可直接复用的合格成果。LY-001 的 checks 和 LY-002 的 D-01—D-09 是对照输入，不能代替终审。LY-002 的 D-01 和本席位的 G-N1 互相印证。
- 开工条件：G 冻结（至少要有 LY-010），LY-001 和 LY-002 提交冻结，LY-091—094 交区域结论，LY-100 给出本批 manifest 和批次基线提交。检查器已经可以直接重放，见 test-plan.md §0。
