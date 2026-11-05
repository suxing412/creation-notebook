# LY-009｜建立任务锁与分支登记

席位类型：考据/契约。前置：LY-001、LY-006（均为交付完成，status.json 的 SHA 见 `inputs.json`）。唯一写入区：`workpacks/LY-009/`。
基线：creation-notebook-lab `bce3211f818ee5a8bef1773539da70695ba37b17`。lab 全程只读：没有改、建、删文件，没有 git 写操作，没有运行 `build_assets.py`（检查 C12 记录了运行前后 lab HEAD 与已跟踪文件状态）。
本席位也没有改根目录的 `TASKPOOL.md`、`taskboard.json`、`README.md`。任务板 v2 是放在本目录里的**提案**，是否替换根文件由协调者决定。

## 1 交付了什么

| 文件 | 内容 |
|---|---|
| `board/taskboard.v2.json` | 100 席任务板。每席有：原文标题、类型、所在车道（资料契约 / 模型补件 / 复用装配 / 独立验收 / 唯一整合）、所在节及节导语、原文依赖与 G 展开后的依赖、层级、下游席位、**状态**和判定规则、状态依据（status.json 的 SHA、交付清单缺件）、白名单、锁、暂停区条目、原文行号，以及逐字原文 |
| `board/board.md` | 同一份板的可读表：按车道分开显示，附锁表和暂停区表 |
| `board/dag.json` | 依赖图：拓扑序、每席层级、边表、反向依赖、一条最长链 |
| `board/locks.json` | 17 把锁：12 把保护锁（保护清单与各节导语里的排除项）、2 把共享文件锁、3 项权利（发布账户、城市写入、任务板根文件）。锁住的 500 个 lab 文件逐件按提交字节算了 SHA256；还记了基线之后 origin/main 在锁路径里的改动 |
| `board/pause-zone.json` | 暂停区：14 条。每条写明效果（阻断合并 / 阻断落城 / 阻断开工 / 仅提示）、涉及席位、裁决人、解除条件和来源引句。引句都在源文件里重新找到过 |
| `board/ownership.json` | 分支与文件归属：每席白名单只有 `LY-###/**`；根文件只归协调者；lab 写入只归 LY-100；发布只归协调者；分支登记与命名规则 |
| `templates/daily-handover.md`、`.schema.json` | 席位每日交接模板。前五项就是任务池规定的五项：完成产物、来源 SHA、未解决项、是否可接城、下一依赖。另加五件事分开填写、写入自检、锁和暂停区、证据四分类 |
| `templates/coordinator-daily.md` | 协调者日报模板（按状态变化、G、锁、暂停区、白名单、合并、明日释放填写） |
| `templates/pause-entry.template.json`、`lock-request.template.json` | 登记暂停区与申请解锁/改锁的格式 |
| `templates/examples/LY-009-2026-11-05.handover.json` | 本席位今天的交接，作为填好的样例 |
| `source/` | `parse_taskpool.py`（独立重新解析原文）、`build_board.py`、`check_whitelist.py`、`check_handover.py`、`check_board.py`、`board_diff.py`、`render_board.py`、`make_handover_example.py`、锁和暂停区的规格文件 `locks_spec.py`、`pause_spec.py`，以及一键重跑 `run_all.sh` |
| `qa/checks.json` | 12 项检查 C1–C12，含 40 个注入负例，全部被检出 |
| `qa/parse-compare.json`、`qa/taskpool.parsed.json`、`qa/whitelist-scan.json` | 解析对比、独立解析结果、整棵 workpacks 树的白名单扫描 |
| `preview/dag-status.png` | 依赖层级图：按状态着色，边框颜色表示车道。是 PIL 画的示意图，不是渲染图 |

## 2 复核：任务板解析与原文是否一致

- 根目录 `TASKPOOL.md` 与制作人提供的原件 `东汉洛阳_100席位并行生产任务池.md` 字节完全相同（SHA256 `00c2e171…`）。
- 我按原文重新写了一个解析器（不读 taskboard.json），再与根 `taskboard.json` 逐席对照：
  - 100 席的标题、类型、依赖（G 展开后）、usesG 都一致。
  - 类型计数 46/31/13/9/1 与原文开头声明一致；46+31=77。
  - 依赖图 100 个节点、925 条边，无环，没有未知依赖。最长链 15 层，与协调者的说法相符。根文件里的 `topo` 顺序也合法。
- **发现一处解析缺陷**（暂停区 PZ-10）：每节最后一个席位（010、020…090，共 9 个）的 `text` 末尾多带了下一节的标题和导语。这些导语本身就是约束，例如「不触另行处理的13院片区」属于 041–050，现在却挂在 LY-040 上；「雍门接街继续保留给原负责人」属于 011–020，现在挂在 LY-010 上。
  - v2 的 `text` 与原文逐字一致，导语改为挂到本节每个席位的 `sectionIntro`。
  - 原解析器的节标题正则也会漏掉「91—100」这样的三位数节（我自己的解析器第一版也犯了这个错，已改正）。
- 根 `taskboard.json` 的工作树字节（`1d1fcb9c…`，CRLF）与 workpacks 提交里的 blob（`f6dda5f4…`，LF）不同，内容只差换行。LY-006 绑定的是工作树字节。以后引用请写明是哪一种字节。

## 3 状态是怎么定的

状态不手填，`build_board.py` 每次从各席位目录现读：

- **S1**：席位自己的 status.json 写了交付完成、复用完成或阻断，照录；写了「待验」，记作「待验收」。
- **S1b**：声明完成，但交付清单里有文件不存在，降为「待验收」。未建不计完成。
- **S2**：没有 status.json，但 `prep/` 以外已有文件，记作「制作中」。
- **S3**：依赖全部交付完成或复用完成，记作「可开工」。
- **S4**：其余都是「待输入」。`prep/` 里的准备工作允许做，但不改变状态。

本次快照（2026-11-05 23:3x）：

- 交付完成 7 个（001–007）。LY-009 写出 status.json 后为 8 个。
- 制作中：LY-008。
- 其余都是待输入。
- G 尚未冻结，还缺 LY-008 和 LY-010。所以 011–100 全部是「待输入」，这是如实结果，不是遗漏。

「可开工」只说明依赖到齐，**不等于**地域准入或可以入城。G 不包含 LY-003/004，落城要看 LY-010 的决策表和 LY-094（暂停区 PZ-11）。

## 4 排除锁

保护清单的 6 条和各节导语里的 6 个排除词（雍门接街、13院、v2.1、v2.2、196米、31组），每一项都至少有一把锁（检查 C6）。

- **LOCK-YONG-ROAD 雍门接街**
  - 持锁人是原负责人。
  - 锁住 yong-city-v1、雍门卡、雍门研究件、wall-09，以及基线之后出现的 yong-road-link-v2 / yong-link 路径。
  - origin/main 在基线后有 10 个文件落在这把锁里（f28d650、b70c495），都是持锁方自己继续做的，记作漂移，不算越界。
- **LOCK-13COURT 13院压缩**
  - 锁住 m-luoyang-residential-life（卡片自述「13院、26屋」）、research-north13-court-* 节点和 north13-gates 下的三组院落研究件。
  - 边界一部分沿用 LY-006 的判断，未经持锁人确认（PZ-13）。
  - cad338b 的北缘三院自述「与另待部署的13院区域分离」，没有纳入这把锁。
- **LOCK-12GATES 十二门本体**：12 张门卡，以及门体件、north13 门研究件、旄门，共 78 个文件。门数恒为 12。
- **LOCK-PROTOTYPES**：井、灶、圈厕、厩、窑、磨、足碓、住屋、宫殿/廊、两坛、明堂、辟雍等原型卡，共 192 个文件。
- **已修订、不再派相同修复的四项**：
  - LOCK-MARKET-V21：S84/S86 与店前线 v2.1；
  - LOCK-WUKU-B22：wuku-B 三档；
  - LOCK-LINGTAI-STEPS：灵台；
  - LOCK-GALLERY-A：复道 A。
- **LOCK-GRANARY-NEAR 太仓原位近景**，以及 **LOCK-NE-196C 东北约 196 米 C 短路**。后者不在 docs 树里，锁的是 LY-006 解出的 `northeast_C_access.glb`（SHA `58f2f58a…`，已重算一致）。
- **LOCK-SOURCE-RELEASE 源包净化与 Release 归档**：只归主协调者。
- **LOCK-31PALACES 31 组重复宫殿**：清单缺失，只能按名称禁用（PZ-08）。
- **共享文件锁**：
  - LOCK-SHARED-CITY：city-data.mjs、项目卡、v1、data、asset-spec、lab/data、lab/tools、全站页面；
  - LOCK-PUBLIC-DOCS：全部 docs/ 与 lab/，只有 LY-100 能写。
- **权利（不下放）**：
  - RIGHT-PUBLISH：push、Release、Pages、对外通信，只归主协调者；
  - RIGHT-CITY-WRITE：只归 LY-100；
  - RIGHT-TASKBOARD：根任务板文件只归协调者。

锁里的「文本提及席位」是关键词命中，只表示原文提到了这个对象，不证明该席位一定会碰到它。

## 5 分支与白名单

- 现状：100 个席位共用一个 `workpacks` 分支（`D:/GitHub/creation-notebook-workpacks` 是 lab 仓库的 worktree），靠目录分开写入。白名单规则 v1（`source/check_whitelist.py`）：
  - R1：只能写自己的 `LY-###/`；
  - R2：根文件只归协调者；
  - R3：不放源工程和压缩包；
  - R4：单个 GLB 不超过 15,000,000 字节；
  - R5：单个文件不超过 100 MiB；
  - R6：缓存垃圾只提示，不算违规；
  - R7：工作包树以外一律不可写。
- 如果改用各席位独立分支，命名用 `wp/LY-###`。**不能用 `workpacks/LY-###`**：git 不允许一个 ref 名既是文件又是目录，已有 `workpacks` 分支时建不出来。这一点在临时仓库里实测过（C9）。
- 共享分支在最后一次扫描时有 2,654 个改动路径（qa/whitelist-scan.json），全部落在某个席位目录内，根任务板文件内容没有被改（C8）。
- 树内内容违规（PZ-14）：
  - 175 个文件违反 R3/R4，分布在 7 个席位：解出的 .blend/.zip 源包、`tmp/` 临时件、超限 GLB。
  - 23:17 起根目录出现了一个未跟踪的 `.gitignore`，不是 LY-009 写的，作者未核实。它挡住了其中 174 个文件。
  - 仍未被挡住的只有 `LY-076/prep/work/qv1src/assets/lingtai-A-quality.glb`（25,848,260 字节）。
  - 任务池允许 `native/`，README 和 `.gitignore` 却把它排除在分支外，这条冲突待协调者确认。
  - LY-009 没有动别的席位的文件。

## 6 暂停区（14 条，详见 board/pause-zone.json）

- **阻断合并**：
  - PZ-01：基线漂移。origin/main 已到 cad338b，住宅由 44 院变为 47 院；
  - PZ-09：LY-100 合并前须处理的既有更正（CRLF SHA、雍门研究候选重复、秏门名、R-01…R-05）；
  - PZ-14：工作包里的源工程与超限件。
- **阻断落城**：
  - PZ-02：宫区配准未通过；
  - PZ-03：城南礼制与南北郊位置未放行。
- **阻断开工**：
  - PZ-04：平城旧斜路端口没有数值；
  - PZ-05：示范院帧待 LY-010 冻结。
- **仅提示**：
  - PZ-06：LY-087 是否应依赖 LY-086。我没有改原文依赖；
  - PZ-07：材质待拍板项；
  - PZ-08：31 组宫殿清单缺失；
  - PZ-10：根 taskboard 的 text 串节；
  - PZ-11：地域准入不在依赖图里；
  - PZ-12：持锁人身份没有登记；
  - PZ-13：13院锁边界待确认。

## 7 没做到 / 不声称

- 持锁人「原负责人」的姓名或会话，在我能读的文件里没有记载，锁里只写了角色（PZ-12）。
- 各席位的 `assignee` 都留空，只有 LY-100 按 README 记为 Claude。负责人登记是协调者的事，我没有替他登记。
- 状态是快照：其他席位正在并行写入，扫描期间文件数从 2,793 涨到了 7,487。需要最新状态时重跑 `run_all.sh`。
- 锁只覆盖路径和节点；城市文件里的字段级归属沿用 LY-006 registry，本席位没有重做。
- 白名单检查只看路径、扩展名和大小，不检查内容里的私密路径或凭据（那是 LY-008/096 的事）。
- 本席位不涉及模型能读取、局部通行通过、已入城、真实结构安全、历史复原成立这五件事，一项也不声称。
- 没有用外部网页资料，也没有做浏览器或 GPU 测试。

## 8 证据分类

- 原始考古/原文：无（本席位不下史实结论）。
- 异地异期类比：无。
- C 工程设计：状态规则、锁的路径划分、白名单规则、分支命名、暂停区效果分级。
- 未知：持锁人身份；13院锁的确切边界；31 组宫殿清单。

## 9 重算

在 workpacks 根目录运行：

```
sh LY-009/source/run_all.sh D:/GitHub/creation-notebook-lab bce3211 <临时目录> "C:/Users/suxin/Downloads/东汉洛阳_100席位并行生产任务池.md"
python -I LY-009/source/write_manifest.py .
```

单项用法：

- 检查某席位的改动：`python -I LY-009/source/check_whitelist.py --seat LY-021 --paths <清单>`，或 `--git <repo> <base> <head>`；
- 检查交接文件：`python -I LY-009/source/check_handover.py <交接.json> --root .`；
- 比较两天的板：`python -I LY-009/source/board_diff.py <昨日v2> <今日v2>`。
