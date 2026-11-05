# LY-092 验收方案（可执行，第二轮 2026-11-06）

本项验收原文：「原44院及所选市肆计数不变，互斥与所有孔洞联合检查；单独区域通过不能代替共同基线中的结果。」

## 0 运行方式

所有命令都在 `workpacks/LY-092/prep/` 下执行。Python 一律用 `-I`。lab 仓库只读。

```
# 1) 冻结基线：从 LY-001 新快照的 city-data.mjs 导出 manifest，再测「改前」
#    检出 HEAD 不是快照提交时：git show <sha>:docs/cities/luoyang/city-data.mjs > out/originmain-<sha>/cities/luoyang/city-data.mjs
#    （放在 cities/luoyang/ 下，dump 里的 URL 才能按原相对路径解析）；快照里新增的 GLB 同样用 git show 取出，写进 overrides
node   scripts/dump_city92.mjs <city-data.mjs> > out/city-data.<sha>.dump.json
python -I scripts/baseline92.py <sha> out/city-data.<sha>.dump.json <lab>/docs/cities/luoyang out/baseline-<sha>.json <overrides.json>
#    overrides.json 的格式：{"<sourcePath>": "<本地文件>", ..., "__grid__": <out/grid-frozen-v1.json 里的 __grid__>}
#    __grid__ 必须带上，否则栅格原点会随包围盒漂移，格数无法跨基线比较

# 2) 自检：P0 正例要通过，10 个负例要全部被拒
python -I scripts/check92.py selftest out/baseline-<sha>.json out/selftest-<sha>.json     # 要求 ALL_SELFTESTS_OK=true

# 3) 计划孔位探针（改前应判为「封住或无井沿」，改后应判为开放且井沿 8/8）
python -I scripts/check92.py check out/baseline-<sha>.json tests/probe-planned-holes.overlay.json out/probe-holes-<sha>.json

# 4) 联合验收：一个批次一份 overlay（格式见 check92.py 文件头）
python -I scripts/check92.py check out/baseline-<sha>.json batch-<id>.overlay.json out/check-<id>.json

# 5) 撤回：分别对「空 overlay」和「撤回后的 manifest」各跑一次，所有哈希都要等于基线
python -I scripts/summarize92.py out/baseline-<sha>.json out/<cand>.json         # 状态哈希逐项对比
python -I scripts/drift92.py     out/baseline-<sha>.json out/<cand>.json out/drift-<id>.json

# 6) Blender 交叉核对（可选，抽样）
D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P scripts/blender_xcheck92.py -- out/bx-<id>.json <glb> [<glb>...]
```

overlay 不写进 lab。脚本把候选 manifest 写成本席位目录里的 `_cand.dump.json`，测完删除。overlay 里的 `files` 把包里的 GLB 映射到磁盘上的本地路径。

## 1 绑定

| 绑定项 | 准备期的值 | 正式验收时 |
|---|---|---|
| lab 提交 | bce3211f818e…（检出）；cad338ba683f…（origin/main，2026-11-06）。两个都测过 | 用 LY-001 届时冻结的 SHA。G 包目前都绑定 bce3211，LY-010 未交付 |
| manifest dump | bce3211：`28ce130c13bfe9d2…`；cad338b：`d40088a45d012f88…` | 重新导出；overlay 的 `baseDumpSha256` 必须相等（检查 I0） |
| city-data.mjs blob | bce3211：`c849706b…`；cad338b：`d8933a32a6a133b3…` | 重新取 |
| 区域指纹 | bce3211 `b1f59a7e1deb4379…`；b70c495 `b37a817723146fed…`；cad338b `5ff321bb54188710…` | 重新算 |
| 各状态几何哈希（1 mm 量化） | bce3211：S0 c254ccf3b0c1… / S_market bed5a4503bab… / S_terrain df8d3a36609e… / S_all c5b049c97247…。cad338b：S0 22133420b24e… / S_market dc0e41b3cf4c… / S_terrain d8d82956aeaa… / S_all aaad474d5d41… | 重新算 |
| 原 44 院 | `scripts/original44.json`（键汇总 `9194384cc200f455…`，来自 bce3211） | 不变。如果 LY-001 新快照里原 44 院有合法变化，必须由 010/100 出具书面裁定后才能重发这个文件 |
| 固定栅格 | `out/grid-frozen-v1.json`：住宅 x0 468.999999、z0 −1276.010701、格 0.5、656×1179；市肆 x0 154.285995、z0 −2011.18396、格 0.25、480×416 | 区域外扩时只能按整数格扩，原点保持在同一格点上 |
| 每个包 | 包内每个 GLB 的 sha256，加上 delivery-manifest 的 sha256 | overlay 的 `files` 和资产记录里的 `sha256`/`nearSha256` 必须等于文件实测值（I5） |
| G 契约 | LY-005 coordinate-contract `b6d7fe9d…`；LY-006 ownership `ecbbbcf5…`、zones `6b3595ac…`；LY-008 ly_check.py `39aaa491…` | 以 G 冻结时的版本为准 |

## 2 状态矩阵（每条检查都要在下列状态里跑）

渲染器从不卸载已加载的 id（city-renderer.mjs:595-624），所以要测的是**并集状态**，不只是单章：

- **S0**：冷启动，只有 initial 节点。cad338b 起 ground-retained 也在 S0 里。
- **S_residential、S_market、S_terrain**：S0 加上该章的 loadNodeIds。
- **S_all**：所有城市章节都打开过，包括 cad338b 的 north-three 章。这是**联合基线**。
- **近档换档**：对每种院落资产测一次。默认在 S_all 上加 near_id；如果 far 节点在 S_all 里已被替换（北缘三院），改在 S_residential 上测，输出里有 `baseState` 字段标明。
- **包新增的章节或变体**：按 overlay 的 `chapterLoadAdd` 自动并入。

## 3 检查项（✔ 已实现并有负例；◐ 等依赖包交付后补参数）

| ID | 检查 | 正例 | 负例（selftest 已构造） | 容差 |
|---|---|---|---|---|
| I0 ✔ | 基线绑定：dump 的 SHA 等于基线记录，也等于 overlay 的 baseDumpSha256 | P0 | 改 dump → 失败 | 完全相等 |
| I1 ✔ | 住宅总数和各资产分布等于冻结基线（bce3211：44，A12/B10/TC03 4/A2 9/B2 7/TC03-2 2；cad338b：47，另加北缘三型各 1） | P0 | N1 删 C02-018；N2 复制 C02-019 | 完全相等 |
| I1c ✔ | 原 44 院：`original44.json` 里的 44 个 ID 全部在场，chapter=residential，指纹键逐个相等 | P0（两个基线都是 44/44） | N1、N3、N5 | 完全相等 |
| I1b ✔ | 没有重复矩阵（四位小数） | P0 | N2 | 0 |
| I2 ✔ | 旧节点指纹不变：资产、矩阵（1e-6）、far/near 实测 SHA、excludeNodes、initial、chapter、replaces。允许变的节点必须列进 `allowedChangedNodes`；住宅节点（含北缘三院）的矩阵**不允许列入** | P0 | N3 平移 1 cm；N4 换文件；N5 改排除表 | 完全相等 |
| I3 ✔ | 市肆计数：S_market 和 S_all 实际组合出的店铺和摊位前缀等于 `selectedMarket`（默认 5 店 N1–S2、3 摊 T1–T3） | P0 | ◐ 029/030 交付后补：选了另一变体却仍组合出 V1 店铺 → 失败 | 完全相等 |
| I4 ✔ | 严格组合：所有状态和所有近档换档里，excludeNodes 全部命中，没有无效矩阵或剪切矩阵 | P0 | N5 | 0 个错误 |
| I5 ✔ | 声明 SHA 等于实际 SHA（渲染器不核，由这道闸门代核） | P0 | N4 同名不同字节（market-A-N2-local 493798b8…） | 完全相等 |
| I6 ✔ | 叠面：不同节点之间朝上面距小于 2 mm 的格数为 0；2–30 mm 的叠层格数在 S_all **不得多于基线**（基线 6 对、4,969 格：TC03 设计地坪 +0.012 m，Blender 已核，以及 drain_stone）。新的合法局部接面列进 `allowStacked` 并附原因 | P0 | N2、N7（重复加载 ground-retained）、N8、N9 | 2 mm / 30 mm |
| I6s ◐ | 同一条规则也查 S0。cad338b 的 S0 基线是 2 对、1,249 格 | — | — | 不得增加 |
| I7 ✔ | 互斥：overlay 的 `exclusiveGroups` 里，任何一组在任何状态下都不能有两个成员同时在场 | P0 | N8 市肆变体同章同载 | 0 |
| I8 ✔ | 永不入城清单：market-A-N2-local（493798b8）、corridor-6m-market-link（b46dd450），以及各包自己声明的旧版本，都不在任何状态的批次里 | P0 | N9、N4 | 0 |
| H ✔◐ | 孔洞，对每个声明的孔（x、z、r、rimY、depth、owner）检查：①圆心和 0.8r 圆周上 8 个点都没有「非 owner 的朝上面，高度在 rimY−depth 到 rimY+0.5 之间」（开放）；②r+0.15 m 圆周上 8 个点都有 rimY±0.05 m 的朝上面（井沿有支持，`requireRing` 默认开）。只在孔的 owner 在场的状态里查；owner 不在场时，孔和 owner 都必须不在（原子性） | P0（合成孔，不要求井沿） | N6：孔在 S_terrain 被 ground-south 封住；N10：空洞上的孔（S0 没有地面，井沿 0/8） | 0 个被封样点；井沿 8/8 |
| Hp ✔ | 计划孔位探针（tests/probe-planned-holes.overlay.json）。**改前**：井 A 在 S_market/S_all 被 `sample_ground#3` 封住，在 S0/S_terrain 井沿 0/8；厕孔区在 S_terrain/S_all 被 `ground-south#78164` 封住。**改后**：025/045/090 的孔清单必须覆盖这两处，在 owner 在场的所有状态里 H 通过 | — | 改前结果本身就是负例：两处在两个基线上都判 FAIL | 同 H |
| R ✔◐ | 路线：沿折线每 0.25 m 取一个样点，要求有支持、相邻高差 ≤ maxStep、0.35–1.8 m 净空带内半径以内没有三角形。失败时回传样点坐标、原因和「节点\|glTF 节点#三角形号」 | P-market-public-to-street（S_all）；P-C02-010-gate-out（S_terrain） | N-market-exitN-void（无支持）；N-market-through-north-shops（被 N1_sidewall#10 挡住）；N-C02-010-gate-out-cold（S0 无支持）；N-C02-010-through-wall（被 earth_wall#50 挡住） | 步长 0.25 m，半径 0.3 m，maxStep 0.2 m（C 设计包络；LY-005/006 冻结的包络到手后替换） |
| Rp ✔ | 探针 X-market-public-cold（S_market）：只记录结果，不判通过或失败。bce3211 下 71/289 个样点失败，cad338b 下 0/289。用来检出基线漂移 | — | — | — |
| U ◐ | 撤回：每个包装上再撤回，得到的 manifest 再跑一次，区域指纹和五个状态的几何哈希都必须**逐位**等于基线；任一包失败时，整批（含 090 的合成地坪）一起回退 | 空 overlay 与基线一致（P0 已证） | 留下一个残余节点 → I2/I6 失败 | 完全相等 |
| B ◐ | 字节和 LOD：单个 GLB 不超过 15,000,000 B，原高细近档保留。由 LY-008 的 `ly_check.py package/glb/lodset/privacy` 执行，本席位只读它的报告并核 SHA | — | 交给 008 | — |

## 4 联合 overlay 的期望内容（各依赖包交付时要提供的数据）

- **LY-030**：
  - 选定的变体（V1/V2/F）和互斥组；
  - 市肆井孔：x、z、r、rimY、depth、owner，应与 LY-006 的切孔区 `LY-025:cut:003` 一致；
  - 操作区；
  - 有限路线和负例，写明东出口、北出口、南出口各怎么处理（exitN/exitS 在两个基线上都是 0/80）；
  - `selectedMarket`。
- **LY-050**：
  - 选定的示范院节点 ID。必须是原 44 院之一（registry 的候选是 C02-010），不新增节点，矩阵不变；
  - 可关闭设施组的互斥组；
  - 院内井、厕、灶的孔。注意厕孔区的地坪实测在 ground-south 上，不在 registry 写的 retained 上；
  - 院内路线；
  - 冷启动 S0 下 C02-010 没有外环支持，要写明怎么处置。
- **LY-082**：院界端口到巷面的短接续 GLB 和端口 ID；关闭补件后恢复断开状态的负例，应得到「无支持」。
- **LY-083**：外街接点的复用判定或补件；exitN/exitS 的处置。冷启动公共出口从 b70c495 起已经有支持（0/289 失败），083 必须在新快照上重测。
- **LY-090**：
  - 单一的合成地坪差异包，加上全部孔的清单（必须包含井 A、C02-010 厕孔）；
  - 被替换的原子地面：用 `replaces`，或者新资产加旧地面组成互斥组；
  - 应用顺序；
  - TC03 双层地坪（C02-008/020、FROZEN-D08-NE/NW）的归属说明。

## 5 判定输出

`out/check-<batch>.json` 记录每一项检查的 PASS/FAIL 和输入 SHA。批次结论写进 `workpacks/LY-092/qa/`，供 LY-095–099 和 LY-100 使用，格式按任务池的五项交接：完成产物、来源 SHA、未解决项、是否可以接城、下一个依赖。

只要有一个 FAIL，就**不放行**。待验项（GPU、手机、v1 入口、北缘三院在 S_all 下的 focusCourtyard 行为）照原样标注，不能写成通过。

## 6 已知局限

- 测量是渲染器规则的 numpy 重实现，不是浏览器。渲染器改了组合规则，lib92.py 要同步（文件头列有对应的行号）。
- 格心采样，不是连续人体扫掠；没有做实体相交。
- Blender 只抽查了 TC03 两份文件的高度；正式验收时，对联合状态的 3 个样点用 Blender 重算支持高度，容差 1 mm。
