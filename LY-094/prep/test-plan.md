# LY-094 验收测试方案（可执行）

依据「本项验收」原文：每个资产都要有直接依据、类型类比、C 设计或未知中的定性，并写准入理由；新宫墙、城南、北郊三类资料不混；未定址的保持未入城。
所有命令都**只读** lab 仓库。所有 JSON 都按提交 blob 字节计算 SHA，不按 CRLF 检出的字节。脚本统一用 `python -I` 运行。

## 0 绑定（每次运行都写进报告）

| 项 | 本次基线值 |
|---|---|
| lab 提交 | `bce3211f818ee5a8bef1773539da70695ba37b17` |
| city-data.mjs blob | `c849706b6210813c74851b86cfd3353183a47badc0e019a1151247db1e34bf00` |
| evidence-geometry.json blob | `fa8b7002869e01e981d2b2679c327a2f1db957119e55537e06289ca59e5ba7c7` |
| research-unplaced.json blob | `27f9e7f3429eccd8e7b5cbc1f5bbf88019a90ee9191c090b067d838d1a7bb43b` |
| p-luoyang.asset.json blob | `8edb06abf5e7d874334a932e3108079590b327ec5afbb78290df2f66424f95bd` |
| 改前基线 `out/baseline-bce3211.json` | `b2217d24240a288fd832f318e33edb4d75a88a561a5a2707cb376664b2d37005` |
| 改前判定表 `out/admission-baseline-bce3211.json` | `3541af15333f18b53bf1782721dc4bb484f3691b3cccd20497be23268f9a8d2e` |
| 地面探测 `out/ground-probe-bce3211.json` | `e646b933ef1abef537005a127f4d61f0e9cdbb51505aab99e631039ee1cef89e` |
| LY-002 evidence-ledger / family-binding | `237a4811…` / `3aeddcc0…` |
| LY-003 tables/admission.json | `dd0ab8c018e714be1366cb491107ff09131e5e176b9106894a2e5b2b86e88dd3` |
| LY-001 dump_city_data.mjs | `5943be43…` |
| LY-004 tables/site-constraints.json（11-06 新绑定） | `633c3302ff1219e8d93d2a59107eae85a6d7c077f418f7b53300f642708eb77f` |
| LY-004 delivery-manifest.json / status.json | `cb8a7e7f1c11…` / `c9358ea5095a…` |
| LY-006 registry/seats.json / zones.json | `a1426412c84c…` / `6b3595ac735d…` |
| 复测 baseline `out/rerun-1106/before.json` | `5e9587bc780e30057162b3199ae70f6c3ac12c871618863bf885d03ea3f907b0`（与 v1 只差 measuredAt 和 B10 详情） |
| LY-004 交叉复核 `out/rerun-1106/crosscheck-ly004.json` | `2ffbf4b680244239cfeeced25d6e1ebf8aa8f40b5bd7d60772b815645f8b4303` |
| 检查器 v2 自测 `out/rerun-1106/selftest-v2.json` | `02701733c803a38f1e849657f89ad5f48e3ef261049c5a7190d82ece8b7a00e9` |
| check_admission.py v2 / v1 | `e5d2e8ca82d5…` / `57802e3bd58c…` |

脚本本身的 SHA 记在 `inputs.json` 的 `prepFiles` 里。正式验收前如果改了脚本，要先在 bce3211 上重跑第 1 节，确认自测和改前结果都不变，再拿去测候选。

## 1 同一基线重放（改前、改后用同一套方法）

```sh
LAB=D:/GitHub/creation-notebook-lab; WP=D:/GitHub/creation-notebook-workpacks; S=$WP/LY-094/prep/scripts
MQ=<scratchpad>/mq/cards
# A. 改前（已跑过，结果已冻结）：
node $WP/LY-001/source/dump_city_data.mjs $LAB/docs/cities/luoyang/city-data.mjs > before.dump.json
python -I $S/baseline.py --lab $LAB --commit bce3211 --dump before.dump.json --mq $MQ --workpacks $WP --out before.json
python -I $S/ground_probe.py --lab $LAB --dump before.dump.json --out before.ground.json
# B. 改后：对 LY-100 的批次分支或 overlay 检出（只读工作树），提交号写进 --commit
node $WP/LY-001/source/dump_city_data.mjs <cand>/docs/cities/luoyang/city-data.mjs > after.dump.json
python -I $S/baseline.py --lab <cand> --commit <cand-sha> --dump after.dump.json --mq $MQ --workpacks $WP --out after.json
python -I $S/ground_probe.py --lab <cand> --dump after.dump.json --out after.ground.json
# C. 判定表检查（判定表 = workpacks/LY-094/admission.json）
python -I $S/check_admission.py --table admission.json --before before.json --after after.json \
   --ly003 $WP/LY-003/tables/admission.json --ly004 <LY-004 registration json> --report qa/check.json
# D. 检查器自测（每次都跑；v2 必须 31/31，带真实 LY-003 和 LY-004 表）
python -I $S/check_admission.py --selftest --before before.json --ly003 $WP/LY-003/tables/admission.json \n   --ly004 $WP/LY-004/tables/site-constraints.json --report qa/selftest.json
# E. LY-004 交叉复核（LY-004 每次改包都重跑；必须 X1—X6 全过）
python -I $S/crosscheck_ly004.py --lab <lab 或候选> --commit <sha> --dump after.dump.json --ly004 $WP/LY-004 --baseline after.json --out qa/crosscheck-ly004.json
# F. 项目卡分组（R23；改前是 FAIL，改后必须 PASS，或在判定表里写明交 LY-100 未修）
python -I $S/projectcard_grouping.py --lab <lab 或候选> --commit <sha> --out qa/projectcard-grouping.json
```

`after` 只是装配包装入以后的城景清单。哪个包没被本批选中，就记为「本批未纳入」，不能当成「通过」。
检查器 v2 认三种配准格式：LY-094 自己的 `{status, sites:{}}`、LY-003 的 `{rows:[{ids,status}]}`、LY-004 的 `{sites:[{id, region, assets, coordinate, admission180}]}`（`normalize_ly004`）。LY-004 站点只有在 `install180=放行`、`point_en` 有限、`historicalPositionError_m` 有限三条同时成立时才算配准。v1 读不懂 LY-004 的列表格式，会把真正配准过的站点也拦掉（brief G14）。如果以后格式再变，就加一个适配器，并补一条该格式的负例。不能手工改它的数据。

## 2 判定表规则（check_admission.py；`--selftest` 中的正例 P、负例 N）

| 规则 | 内容 | 正例 | 负例（必须 FAIL） | 容差 |
|---|---|---|---|---|
| R00 | 判定表绑定的 baselineCommit 等于改前基线 | P0 | N19（绑 44c66da） | 完全相等 |
| R01 | 17 个范围资产每项恰好出现一次，不许多出范围外的项 | P0 | N11（漏太学 B）、N12（重复） | 0 |
| R02 | verdict 只能是 可接城 / 只能独立研究 / 仍阻断 | P0 | — | 枚举 |
| R03 | 至少有一条证据，且每条都带四类之一的 class 和 ref | P0 | N7（证据为空） | — |
| R04 | 北魏、西汉、长安、四川画像砖、曹魏、西晋、魏晋、唐代等来源不能归入「原始考古/原文」 | P0 | N8（北魏台基） | 关键词表见脚本 FOREIGN |
| R05 | LY-002 禁用条目（X04/05/09/10/11/15/16/17/19）不能用作支持证据 | P0 | N9（X09 太学范围） | role=support |
| R06 | admissionReason 和 phaseReason 都不能为空 | P0 | N13 | — |
| R07 | 地域码必须等于基线地域码。要改，先由 LY-003/004 出新裁定，再重做基线 | P0 | N4 | 完全相等 |
| R08 | 北郊方坛的地域码必须是 north-suburb | P0 | N4 | — |
| R09 | 同一组内不能同时有 north-suburb 和城南（礼制群或南郊）资产 | P0 | N5 | — |
| R10 | 判「可接城」必须有对应配准包（宫区看 LY-003，礼制和郊看 LY-004），而且该站点的状态是 registered | P1 | N1（缺 LY-004）、N20（真实 LY-003 表：全部不可落位） | 只认「可落位/已配准/registered」 |
| R11 | palace-unassigned（无名宫院件）永远不能判「可接城」 | — | N6 | — |
| R12 | 「可接城」坐标必须写明 frame、有限的 cityXYZ、不确定度 ≤ 75 m，来源须是 LY-003/004 | P1 | N3（把 B 示意点当地块，误差为 null） | ≤ 75 m（LY-010 冻结更严的值后改用新值） |
| R13 | 「可接城」的分期必须是 c180-pre185 | P1 | N18（post-185） | — |
| R14 | 坐标须落在配准站点的不确定圈内 | P1 | N2（偏 130 m） | ≤ 站点 uncertaintyM |
| R15 | 非「可接城」的项，坐标必须为 null | P0 | — | — |
| R16 | 非「可接城」的项，判定表里不能写城市节点 | P0 | N14 | 0 |
| R17 | 判定表列出的每个文件 SHA，都要等于改前或改后基线实测的 SHA | P0 | N10 | 完全相等 |
| R18 | 改后城景里，非「可接城」资产的城市节点数为 0；「可接城」资产至少有 1 个 | P2 | N15（明堂被放进城） | 0 |
| R19 | 改后研究视图中，非「可接城」资产的 cityPlacement 仍为 null | P2 | — | — |
| R20 | 本批 `batchTouches` 以外的资产，文件 SHA 前后完全不变 | P2 | N16 | 完全相等 |
| R21 | 改后北郊方坛不能出现在 ritual（城南）章（city-data 章节） | P2 | N17 | — |
| R22 | 「可接城」所用配准站点的地域码必须等于资产地域码；站点列了资产名单的，名单里必须有本资产 | P1、P5 | N23（灵台借北郊站点）、N25（太学 B 借 `taixue` 站点） | 完全相等 |
| R10（LY-004 真实格式） | 真实 LY-004 表下任何城南、南郊、北郊资产都不能判「可接城」 | P4 | N21（真实表）、N22（伪改「放行」但误差为 null）、N24（北郊方坛借南郊站点） | — |
| R23 | 项目卡 progress 里写北郊的条目，不能和城南礼制条目同章，也不能在 ritual 章（`projectcard_grouping.py`） | 改后 | 改前 bce3211 本身就是 FAIL：「北郊方坛四陛」chapter=ritual（index 10，blob `8edb06ab…`），即 LY-004 R-04 | 词表匹配 |
| R24（待包到后实装） | 各装配包 assembly.json 的 frame 必须等于 LY-006 `seats.json` 里该席位的 frames（如 LY-080=`local:north-altar`），且 placement 为 null，除非本表判了「可接城」；`ownsCityNodes` 以外的城市节点不得出现 | — | 注入一条城市矩阵；把 LY-080 的 frame 改成 `local:south-altar` | 完全相等 |

已在 bce3211 上实跑：v1 自测 `selftest/selftest-bce3211.json` 24/24；11-06 v2 自测 `out/rerun-1106/selftest-v2.json` 31/31（`allOk: true`）。改前判定表带真实 LY-003、LY-004 表、after=复测基线检查，195/195 条通过，报告 `out/rerun-1106/check-baseline-v2.json` 与 v1 的 `out/check-baseline-bce3211.json` 逐字节相同（`dfdd42ca…`）。R23 改前为 FAIL（见上表）。

## 3 逐资产准入检查（正式判定时按资产跑；数字是现在的基线值）

1. **宫区 9 项**（候入院、值守、侧廊、对阙、德阳、玉堂、复道、登临、水道）
   - 先读 LY-003 的 `tables/admission.json`。只要相应分区不是「可落位」，判定上限就是「只能独立研究」。当前五个分区全部不可落位，共同控制点 0。
   - 读 LY-070 的包：确认它是「单一有边界的 C 局部组」、没有城市矩阵、没有多套宫殿叠加。叠加用 A/B 互斥表核：同一槽位只放一个方案。
   - 读 LY-086 的包：只做局部墙块，不写世界位置。
   - 负例：往 LY-070 的包里注入一条城市矩阵，R16/R18 必须失败；把德阳 A、B 同时放进同一槽位，互斥检查必须失败（这项在拿到 070 的 assembly.json 后补进脚本）。
2. **城南礼制群 6 项**（辟雍、明堂、灵台、太学 A、太学 B、观经）
   - 读 LY-004 的站点状态：已交付，四所各有独立条目，全部 `install180=不放行`、B 研究示意点、误差 null。所以在 LY-004 改包以前，这 6 项（含太学 B、观经）判定上限都是「只能独立研究」。
   - 分期：明堂圆基 61—62 m、辟雍遗迹可能属魏晋或北魏（LY-004 引《伽蓝记》），判定表里只能归「异地异期类比」或「未知」，R04 的词表要能拦住写成「原始考古/原文」的情况（人工复核）。
   - 地面：按 LY-004 标记圆半径，灵台、明堂圆各与 `network-ground-stitched` 8 个三角形相交（2 m 网格覆盖 228/21,039 和 367/37,862），辟雍、太学 0。这条平城门外 C 地面带是既有接口，任何礼制装配不能与它叠放。
   - 改前对照数字：明堂到平城门示意 1045.1 m，对文献 828—864 m；辟雍到明堂 406.6 m，对文献 414—432 m。LY-004 如果采用示意点，必须解释明堂这 181 m 的超差。
   - 「可接城」还要求有城中地面支持：用 `ground_probe.py` 在候选坐标 75 m 半径内覆盖率大于 0，并读该装配包自己的端口和支承 qa（LY-074/077/079 的高程容差 2 mm、平面 5 mm，按 LY-005 的契约）。改前覆盖是 0，最近地面 141—747 m。
   - 灵台：城景研究视图与资产卡必须是同一版本。改前不一致（`c1b58de1` 21,332 三角对 `ffaff723` 21,424 三角）。如果 LY-100 没修，判定表里要写明「城景展示件为修订前版本」。
   - 太学：「开阳门外」只有西晋来源，R04 会拦住把它归为原文。太学 B 没有装配席位，判定为「只能独立研究」，不能被组合图吞掉。
3. **南郊 1 项**：独立于礼制群，有自己的配准站点（LY-004 `nanjiao`，文本带，不出点）。改前没有证据层要素，「七里」C 带内地面覆盖 0/8,070（v1 带的起点量错，偏差 ≤31 m）；按 LY-004 文本带（南垣以南 2691—3240 m）重测 0/13,504。还要求 LY-079 交出剔除展示地面后的八陛支承结果（改前 0/24）。
4. **北郊 1 项**：只接受 LY-004 的北郊站点（`beijiao`，三说互斥，不出点），三说里必须选定一种，或者给出包络。改前北墙以北 0—3 km 地面覆盖 0/80,700；按 LY-004 三个多边形重测：四里带 0/11,783、六里带 0/12,635、西北角扇形 0/2,957。判定表中北郊的证据只能引 E-R02，不能引任何城南条目（R09 和人工核）。

## 4 「资料不混」专项（人工核对加脚本）

- 宫区判定只引 LY-003 和 E-P、E-H 条目；城南和南郊只引 LY-004 和 E-R01/03—08；北郊只引 LY-004 的北郊站点和 E-R02。脚本会列出每项引用的 ref 集合，出现交叉就人工复核，并在报告里写明处理结论。
- 新宫墙段（`north_palace_excavated_walls_A_unplaced`）只要还没有坐标，任何项都不能用旧 B 北宫包络来代替它（LY-003 的 hold-zones）。
- 旧 B 北宫的南北边 1398.1/1398.3 m 与北魏的 1398 m 吻合，在没有原图说明以前，只作「可能混入后期数字」的提示，不当作证据。

## 5 报告要求

- `qa/admission-report.json` 写明：绑定的全部 SHA、每项的规则结果、未纳入本批的资产，以及阻断项和对应的责任席位。
- 每项判定写清五件事中的哪一件：本席位只裁「位置/分期准入」。「模型能读取」「局部通行」「结构安全」「历史复原成立」只引用各包自己的 qa，不由本席位升级。
- 不允许只给一个全绿结论。凡是「只能独立研究」或「仍阻断」，都要写下一依赖：缺哪个包、哪个控制点、哪个图版。
