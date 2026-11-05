# LY-098 验收测试方案（可执行）

对应任务池「本项验收」的三句话：
1. 名称、年代、计数、章状态和证据各有来源。
2. 已建模、已入城、可达、结构安全没有串用。
3. 未验事项仍在公开说明中。

## 0 怎么跑

```sh
# 改前基线（已跑，结果在 prep/baseline/bce3211/）
python -I prep/tools/ly098_audit.py --ref bce3211f818ee5a8bef1773539da70695ba37b17 --latest origin/main --out prep/baseline/bce3211
# 检查器自测：17 个负例必须失败，5 个正例必须转为不失败
python -I prep/tools/ly098_selftest.py --out prep/baseline/bce3211/selftest.json
# 正式终审：在 LY-100 本批合并基线上跑，或在同一基线上叠加候选文件重放
python -I prep/tools/ly098_audit.py --ref <批次基线提交> --overlay <候选目录，按仓库相对路径放文件> --out LY-098/qa/<批次号>

# 第二轮补充：覆盖面与 R15–R18（自测 28 例），史源接入 R19/R20（自测 8 例）
python -I prep/tools/ly098_surface.py --selftest --out prep/baseline/bce3211
python -I prep/tools/ly098_surface.py --ref <批次基线提交> --out LY-098/qa/<批次号>
python -I prep/tools/ly098_ledger_join.py --selftest --out prep/baseline/bce3211
python -I prep/tools/ly098_ledger_join.py --ref <批次基线提交> --ly002 <冻结的 LY-002 目录> --ly001 <冻结的 LY-001 目录> --out LY-098/qa/<批次号>
```

- `ly098_surface.py` 和 `ly098_ledger_join.py` 现在只读提交，还没有 `--overlay`。正式终审前要么在 LY-100 的合并提交上跑，要么补上和主检查器相同的 overlay 逻辑，然后重跑两份自测并更新 SHA。

- 只读：用 `git show`/`git ls-tree` 读取提交字节，city-data.mjs 先写进临时目录，再用 node 导入（`tools/eval_city_data.mjs`）。不写仓库，不运行 build_assets.py，不联网。
- 退出码：0 表示没有 FAIL，1 表示有 FAIL，2 表示运行错误。
- 绑定：report.json 里记 `commit`、`toolSha256`（检查器本身），以及 `inputsRead`（每个输入的 SHA256、字节数、git blob、来源是 commit、overlay 还是 patch）。终审结论只对这一组 SHA 有效。
- 同一基线重放：`--overlay` 只覆盖候选目录里实际有的文件，其余都取同一个提交。两份 report 的 `commit` 必须相同，差异只能来自 `inputsRead` 中 origin=overlay 的文件。

## 1 规则表（每条都有负例；带 P 的还有正例）

| 规则 | 检查内容 | 判定 / 容差 | 负例（selftest） | 正例 |
|---|---|---|---|---|
| R01 基线 | ref 解析成提交，和 `--latest` 比较漂移 | 漂移记 WARN，终审必须在批次基线上重跑 | 无（由 R01 输出直接核） | |
| R02 章节身份 | 卡片 chapters 和 city-data chapters 的 id 集合、标题 | 集合不一致记 FAIL，标题不同记 WARN | 可加：删一章 | |
| R03 章状态 | 已入城要求本章至少 1 个城市节点，已建模要求 0 个；城景页标签（index.html 静态 + app.mjs 覆盖）和卡片用同一个词；已建模章的引导语不能暗示已落城 | 0 容差 | N01 礼制章改成已入城 | P01 |
| R04 计数 | 卡片中“已入城”的计数等于实测：城垣段数加门体（附件、换档 replaces 节点不计）、住宅节点数、市肆按 GLB 节点名前缀 `[NS]\d+_` 和 `T\d+_` 实测、仓储节点数、`ground-*` 原子地面文件数；“城门研究”等于 12 减去入城门数；provenance.counts 和实测一致；城垣备注“N段”等于实测段数 | 整数相等，0 容差。备注里写明“已含在总数”的子计数只记 INFO | N02（44→45）、N03（10→11）、N14（12段→13段） | |
| R05 门名家族 | 12 个门名各恰有 1 张卡；入城门不能再以“研究候选”出现在研究视图里；每个门体节点都能对应一个门名 | 0 容差 | N11 两张卡同名 | P02 |
| R06 成员卡和入城 | 卡片的 files 与 city-data 引用资产按 git blob 比对；写“已入城”的卡必须真被城景加载，写“未入城”的卡必须没被加载；members 列出的卡必须存在 | 逐字节，0 容差 | N06 灵台卡写已入城，N07 雍门卡写未入城，N12 成员卡不存在 | |
| R07 公开数字 | 公开文本（项目卡、city-data 文字、index.html、app.mjs、scene.mjs、README、成员卡）中的城门研究数、入城门体数、章节数、入城院落数、店摊数都等于实测 | 0 容差。README 是带日期的日志，只记 WARN | N15 写成七店三摊 | P05 |
| R08 证据层 | city-data 用到的每个 tier 都在卡片图例里有定义；缺证据层时不能默认显示“推测”；图例要能映射到任务池四类 | 未定义的层记 FAIL | N10 新增一个“考古”层 | P03 |
| R09 五件事 | 分句扫描。硬词（结构安全、承重、实测、测绘、复原成立、考古证明、考古实测、已获考古）必须有否定或限定，否定词的作用范围是本分句里其后用“、”并列的各项。软词（通过、接通、连通、可通行、可达）必须带范围词（局部、有限、离散、样点、检查、核验、测试……） | 硬词未否定记 FAIL，软词没带范围词记 WARN | N08 “结构安全验收”，N09 “考古实测复原成立” | |
| R10 图像 | 概念封面的 alt 要写“概念”，并否定“实渲/现况”；备注里要有封面说明；每张章图和画廊图都要在 posters.json 或同目录的 source.json/README 里有出处；已入城章的配图不能只是未入城的研究模型 | alt 不合规记 FAIL，无出处记 WARN | N05 封面写成“实渲” | |
| R11 未验披露 | 项目卡的“限制”要写 GPU、浏览器或线上画面、手机，并和 project-stage-contract 的 validation 对照；入城成员卡要写浏览器和 GPU 未验 | 缺 GPU 记 FAIL；realMobile=false 时缺手机记 FAIL | N04 删掉 GPU | P04 |
| R12 年代 | 摘要要有约 180 年；公开文本里提到北魏、西汉、长安、四川、画像砖等，必须带否定或类比限定；列出出现过的所有公元年份；摘要列出的组成（十二门、南北两宫）和城中现状对照 | 缺 180 记 FAIL，其余记 WARN 或 INFO | N16 删掉“约公元180年” | |
| R13 地域 | 北郊资产不能出现在城市节点里；北郊和城南礼制同章时要单列 | 北郊入城记 FAIL，同章记 WARN | N17 北郊资产落进城市节点 | |
| R14 批次 | journal 的 batch 都要有对应的 git tag；没有批次号的条目列出来 | tag 不存在记 FAIL | N13 批次 r2099.01.01-1 | |

自测结果绑定检查器 `ly098_audit.py` SHA256 `7afd3e5d8c7355a8d1d21de73e3489b2e6337d205a72d1ca3d56500e25f46fd6` 和 `ly098_selftest.py` SHA256 `96f112215a800c398407653ab70892b00ef797b199a341c40d0ff68c4874a7dd`，在 bce3211 上 22/22 符合预期（`baseline/bce3211/selftest.json`）。检查器只要改动，就必须重跑自测，并更新这两个 SHA。

## 1b 第二轮补充规则（主检查器覆盖面之外）

| 规则 | 检查内容 | 判定 / 容差 | 负例（自测） | 正例（自测） | bce3211 基线 |
|---|---|---|---|---|---|
| R15 覆盖面 | 列出 docs/cities/luoyang/ 下所有文本文件，标出主检查器是否读过。对未读的页面、模块、说明和 source.json 做分句扫描，硬词和软词的判法同 R09。豁免：“实测响应/字节”这类技术实测，“通过……查看”这类介词用法，“连通分量/连通构件”这类几何用语 | 硬词未否定记 FAIL，软词没有范围记 WARN，0 容差 | “结构安全验收”“路线可达”“将门内出口与殿前台阶接通” | “不认证结构安全”“有限区域检查接通”“对 27 个 GLB 实测响应体合计 1408005 字节”“通过雍门章节查看”“209 三角连通分量” | 154 个文件，9 个已读，48 个带中文未读；FAIL 0，WARN 4 |
| R16 门名 | 数据层 data/**/*.json 的 `"name": "…门"` 集合要等于站内十二门用字。“十二城门”这类总称不算 | 多出的门名记 WARN，用字由 LY-002 裁定 | 数据层出现“旋门” | 十二门齐全；总称“十二城门” | WARN 1：旋门（evidence-geometry.json、city-wall-constraints.json） |
| R08b 渲染笔触 | city-renderer.mjs 不能把 `'C'` 并入“推测”笔触 | WARN（主检查器 R08 已有 FAIL：C 层没有图例） | `['C','inferred','推测']` | `['inferred','推测']` | WARN 1（L140） |
| R10b 海报出处 | posters.json 每条记录的 source 在本提交存在，sourceSha256 和 sha256 都等于提交字节 | 不符或缺失记 FAIL | SHA 不符；source 缺失 | 全部相符 | 8/8 相符，PASS |
| R17 全站清单 | docs/manifest.json 的 ongoingProjects 洛阳条目：标题等于项目卡，最后修改不早于项目卡 | WARN；evidence 指向重定向页记 INFO | 标题不同且早于项目卡 | 标题相同且不早于项目卡 | WARN 2，INFO 1 |
| R18 provenance 字节 | city-data.mjs 里公开的 path+sha256 要等于本提交的提交字节 | 只和 CRLF 变体相符记 WARN（修口径归 LY-096/099），不符或缺失记 FAIL | 只对 CRLF 变体相符；完全不符；文件缺失 | 和提交字节一致 | 13 对里 12 对 WARN、1 对 OK |
| R19 禁用项 | LY-002 的 X01–X24 关键词出现在项目卡、成员卡和城景页面/说明里（不含 v1 和 research 档案）。同一句段有否定或限定（不、非、排除、异说、类比、北魏……）记 INFO | X02（北魏门名）和 X20（旋门）没有限定记 FAIL，其余没有限定记 WARN，交人工复核 | “城东南门名旋门”“门楼两重、去地百尺” | “‘旋门’不是城门名”“北魏门楼两重百尺，不移作东汉” | 68 个文本，命中 11 次：INFO 8，WARN 3（里坊、东掖门、洛河） |
| R20 史源绑定 | 项目卡 members 的每张卡，经 LY-001 家族或卡片 ID 接到 LY-002 family-binding，至少有 1 条 facts | FAIL（LY-002 冻结后才算硬门槛） | 绑定了但没有 facts；完全没绑定 | 经家族接到 | 55 张里 52 张 PASS，3 张 FAIL（m-gate-roof-study、m-eaves-shell、m-passage-interface） |
| M01 海报画面（人工） | 页面当作“这一版”展示的海报，画面里烧进的数字和门名要和实测一致，否则要在 alt 或说明里标出渲染日期 | WARN | 现状：city-overview 画面写“已有14院”，标签是“旋门” | 补上日期或换成新渲染 | WARN 1（原图 SHA 83fdbbae…，2026-11-03） |

自测和基线绑定的检查器：`ly098_surface.py` SHA256 `5d402767df0996034a88cf248100255a62e55c6789f25b9c5d29cdf0198525fd`（自测 28/28，`baseline/bce3211/surface-selftest.json`）；`ly098_ledger_join.py` SHA256 `077fc497d8f2dfe6a6520b136ae6ee205fe3e19e409847eea46c6b0e3079c61e`（自测 8/8，`baseline/bce3211/ledger-join-selftest.json`）。R20 绑定的上游输入是 LY-002 evidence-ledger.json `237a4811…`、family-binding.json `3aeddcc0…`、LY-001 family-ledger.json `8eaa7c7a…`，SHA 全值写在 `ledger-join.json` 的 upstreamInputs 里。上游冻结后如果字节变了，就必须重跑。

已知局限：R15 和 R19 的“有限定”是按句段判断的启发式。比如“复用既有**无**名门卫切片……接通”这一句，会因为“无名”里的“无”被当成有限定，这是漏报。所以所有 INFO 和 WARN 都要在终审时人工抽查。

## 2 终审时还要人工做的（检查器不代替）

- **史源栏**：LY-002 交表以后，名称、年代和事实每条都要带原文或图版定位。现在用 R20 按卡片接 LY-002 的条目 ID。LY-002 已经交了，但还没有提交冻结，所以 R20 现在只报数，**不能写成通过**。还要补一张对应表：卡片三级图例（有据/推测/未知）和城市数据的 tier（C 等）对到 LY-002 的五级（有据（文献）/考古（二手）/推断/C/未知），再对到任务池四类。
- **LY-002 指名给本席位的措辞项**：D-02（平城门 177/178 年损坏可能是同一件事记在两年，开门年有建武十三、十四两说）和 D-07（“市与里坊”的“坊”）。终审时要逐条给出“改”或“不改”和理由。D-01（旋门）改证据层，归 LY-100。
- **R09 的 WARN 句子逐句复核**：判断是不是真把局部检查写成了整体通过。
- **区域结论对照**：LY-091—094 每个区域的“可接城 / 只能独立研究 / 阻断”结论，要和卡片 chapters、progress 的状态逐条对上。检查器以后会加 R15，读入批次 manifest 的 `gate_results`；未纳入本批的区域记“本批未纳入”，不能记“通过”。
- **艺术封面**：要人工确认封面仍是概念图，而且没有出现在任何“现况”或“证据”位置上。

## 3 终审输出（交 LY-100）

- `qa/<批次号>/report.json`、`corrections.json`：逐条更正清单，每条有位置、现文、实测、建议改法。
- 结论只分三种：**放行**（0 FAIL）、**带更正放行**（FAIL 都有 LY-100 已排期的更正）、**阻断**。WARN 不阻断，但要列出来，不许删掉。
- 改前和改后：同一个检查器跑合并前基线和合并后提交，两份 report 的 FAIL 差集就是“已更正”的部分。新增的 FAIL 阻断合并。
