# LY-099｜源包与可复现交付核验 · 开工准备（brief 草稿）

阶段：**开工准备**。本席位没有制作或修改任何交付几何，只读输入、实测缺口，并写好检查脚本。所有写入都在 `workpacks/LY-099/prep/`。lab 仓库全程只读：没有运行 `build_assets.py`，没有执行 git 写操作（包括 `git fetch`），也没有联网或调用 `gh`。收尾复查：HEAD 仍是 `bce3211`，`git status` 只有 `?? .claude/`。（第一轮时 `lab/data/assets.json`、`glb-cache.json`、`report.json` 三处未提交改动在席位开始前就有，第一轮收尾时已被别的会话或使用者恢复，本席位没有写过这三个文件。）

## 0 第二轮复核（2026-11-06）

第一轮草稿写于 2026-11-05 22:35。本轮在同一基线上重放，结论如下：

| 项 | 结果 |
|---|---|
| G 状态 | LY-001/002/005/006/007/008/009 的 `status.json` 都是「交付完成」；**LY-010 目录不存在**，所以 G 仍未冻结。LY-096、LY-098 只有 `prep/`，依赖也未满足 |
| 基线可重复 | 旧版工具在 bce3211 上重跑，输出 SHA 仍是 `fea57ded…958a5`，与第一轮逐字节相同（运行约 40 s） |
| 扫描器缺口（新发现，已修） | 把 LY-008 的 `privacy-docs-bce3211.json`（checker `39aaa491…`）拿来对照：README 里有**两处**盘符路径，`D:/GitHub/creation-notebook-待传/…` 和 `D:/待删-<日期>-已传源文件/`。本席位 v1 的 `any-drive-path` 正则要求路径段是 ASCII，**漏掉了第二处**。已改为允许 UTF-8 字节的 v2（`tools/source_baseline.py`，SHA `0f6e26a9…`），并加了 3 个用例：中文盘符路径必须被抓到；`https://github.com/…/` 和 `textures/LOD0/a.png` 不能被抓到。还核了 v1 正则在中文用例上确实没有命中，说明新用例能区分新旧两版。selftest 从 17/17 变为 **20/20** |
| 新的「改前」基线 | `qa/baseline-bce3211.json` 已用 v2 重算，SHA `0ba607b3…82ac`。与 v1 结果逐键比较，**只有 `privacyText` 不同**（多了 `D:/待删-` 一条例子），其余档案、GLB 分层和身份解析都没变。漂移基线 `qa/drift-cad338b.json` 也已用 v2 重算（`01dd95c9…`），漂移差异文件逐字节不变（`d1083119…`），仍是 6 条阻断，退出码 1 |
| 重放的确定性（新测） | 雍门包 `luoyang-yong-gate-study-v1` 在新的空沙箱里再跑一次 Blender 5.2.1，退出码 0，用时 1.3 s。3 个重建 GLB 与第一轮的重建结果**逐字节相同**（LOD0 `6d248504…`），与包内 4.3.47 原件仍然只是语义相同。记录在 `qa/replay-determinism-2026-11-06.json`。由此 T4 可以分两层要求：两次 5.2.1 重放之间必须字节相同；与 4.3 时代原件之间只能要求语义相同 |
| compare 的负例（新增） | 新写了 `tools/compare_selftest.py`，在真实基线的副本上构造 5 个负例：旧档案字节被改、旧档案被删、S1 降成 S4、新增文本隐私命中、新增 S4 城中 GLB。每个都必须让 `compare_baselines.py` 以退出码 1 结束，并给出对应的阻断行；同一基线自比必须退出码 0。结果 **6/6**（`qa/compare-selftest.json`） |
| 语义比较器 | `semantic_selftest.py` 重跑 7/7，输出 SHA 与第一轮相同（`81fdeefa…`） |
| 已交付的 G 输入 | LY-008 的 checker `ly_check.py` 已交付，带 `privacy`、`package`、`glb`、`official` 四个子命令。测试计划已加 T12，在每批里调用它，与本席位的 T5 互相印证。LY-007 已冻结 D-EXPORTER，但 **P-GENERATOR**（新件接受 5.2.1 导出、generator 写 v5.2.40，还是要求在 4.3.2 上做最终导出）仍「待制作人拍板」，它决定 T4 能不能把「5.2.1 下语义相同」当作通过 |

下文 §1–§8 是第一轮的正文。凡与上表冲突的地方，以上表为准。具体是：§6 的 selftest 数改为 20/20，基线 SHA 改为 `0ba607b3…`，§6.5 README 命中改为 2 处，§8 中「LY-008 未交付」一条作废。

## 1 本项目标（按任务池 §LY-099）

每一批放行的交付都要核这几样：源码、参数、原生件、依赖与 SHA、重建命令、许可证，以及净化后的交付包。验收口径如下：
- 在隔离目录里重建，导出的哈希可以核对；字节不同时要有差异说明。
- 源包里没有私密材料。
- 来源缺失就阻断该源包，不能假装找回了原生文件。
- 只核已授权的目录，不覆盖旧源包，Release 上传不由本席位代行。

LY-099 是持续服务席位。每批只核本批 manifest 的 `selected_tasks` 及其 `dependency_closure`，与本批无关的记为「本批未纳入」。

## 2 基线身份

| 项 | 值 |
|---|---|
| 基线提交 | `bce3211f818ee5a8bef1773539da70695ba37b17`（工作树 HEAD；r2026.11.05-5 的 tag 就打在这次提交上） |
| 字节基准 | 一律取**提交 blob**，用 `git cat-file --batch` 读出，不用 CRLF 检出的字节（理由见 LY-001 检查 C8） |
| 开工时的 origin/main | `cad338ba683f…`，**已比基线多出 3 个提交**（r2026.11.05-6/-7/-8）。漂移的测量见 §6.9 |
| 前置成果 | LY-001 已交付（`LY-001/status.json`=交付完成），城中 GLB 的分类直接取自 `LY-001/qa/glb-files.csv`（373 个 GLB） |
| 工具 | Python 3.11.9（`-I`）；Blender 5.2.1 LTS（`D:/Blender/blender.exe`）。原包是用 Blender 4.3（导出器 v4.3.47）做的 |

## 3 已核到的现有成果（路径 + 提交 blob SHA256）

| 路径（lab@bce3211） | SHA256 | 用途 |
|---|---|---|
| `docs/asset-spec/source-archive.json` | `8b80a86d…89653` | 104 个 docs 源文件和 8 个拼合 ZIP 对应到 Release `sources-2026.11.05`；**其中没有任何洛阳条目** |
| `docs/asset-spec/batches/r2026.11.05-5.json` | `8d708271…34d89` | 列出待传源包 `luoyang-yong-city-v1.1-private-source.zip`，**没有 SHA** |
| `lab/tools/build_assets.py` | `ed7664a7…c579e` | 官方检查器。源文件正则在第 35 行，只扫 `docs/`；没有私密路径或凭据检查 |
| `docs/cities/luoyang/city-data.mjs` | `c849706b…bf00` | 城市清单，以及 13 条 provenance.sourceContracts |
| `docs/cities/luoyang/progress-assets/yong-city-v1/source.json` | `325fb5ca…f238` | 雍门入城记录：`reusedAdapterSource` 的 .blend 声明 SHA 为 `2bbd57e4…` |
| `docs/cities/luoyang/progress-assets/granary-city-v1/source.json` | `30e74bda…2639` | 太仓：私有 composer，记录中写明「Private native and generation/validation sources are outside repository」 |
| `docs/cities/luoyang/projection-map.json` | `6f216ee5…101c` | `sourcePreservedPrivately=true`，私有档案 `a65b89f8…` 和更早的 `052c6d6c…` |
| `modeling-lab/review-batches/2026-11-04-north13-gates/intake.json` | `a0cfea35…93b4` | 8 个 north13 源包的分卷与 zipSHA256 |
| `docs/library/models/m-luoyang-yong-gate/files/yong-Y-LOD0.glb` | `45743d73…f9e` | 城中首屏的雍门门体，1,570,856 B |

完整清单（67 个 lab 输入，带 SHA、是否被城景加载、加载代码的行号）见 `inputs.json`。

## 4 改／不改范围

- **改**：只写 `LY-099/prep/`，包括 brief、inputs、test-plan、prep-status、`tools/*.py`、`qa/*.json`。
- **不改**：lab 仓库、任何 GLB、源包、`city-data.mjs`、项目卡、Release、待传文件夹 `D:/GitHub/creation-notebook-待传/`（只列了目录，里面只有 `说明.txt`）。
- **不接管**：源包净化与 Release 归档另有人在做（见任务池保护清单），雍门接街和 13 院压缩由原负责人继续做。本席位只核对，不重打包。

## 5 证据定性

本席位处理的是**交付工程上的可追溯性**，不涉及史实。
- 下文所有「重建一致」，都只说明一件事：用同一份源包，在新环境里能生成**同一几何、UV、材质和贴图**。它属于「模型能读取」这一层的延伸。它**不证明**局部通行、已入城、结构安全或历史复原成立。
- 包内自带的 `NATIVE-EQUIVALENCE.json`、`clean-rebuild.json`、「byte-exact」等声明，属于**生产方自述**。本席位对其中 8 个包做了独立重放（§6.4），其余仍按「未独立核」记录。
- 包里的建筑尺度、门制都是 C 工程设计，引用资料都是异地类比（例如四院 README 引用的博物馆明器文章）。本席位不对它们做历史定性。

## 6 实测到的真实缺口（全部可由 `tools/` 重算）

测量命令：

```
python -I tools/source_baseline.py --ref bce3211 --out qa/baseline-bce3211.json   # 约 40 s，结果确定，两次运行 SHA 相同 fea57ded…
python -I tools/source_baseline.py --selftest --selftest-out qa/selftest.json     # 17/17 负例与正例
python -I tools/isolated_rebuild.py --pack <pack> --root <dir> --build <script> --auto [--stage GITDIR=REL] --sandbox <空目录> --out qa/rebuild-<pack>-bce3211.json
python -I tools/semantic_selftest.py --tmp <空目录> --out qa/semantic-selftest.json  # 7/7
python -I tools/compare_baselines.py qa/baseline-bce3211.json qa/drift-cad338b.json
```

### 6.1 城中 GLB 的来源层级（110 个城中可达 GLB，即 LY-001 中除「仅资产卡」外的类别）

层级定义：S1＝仓库内源包里有逐字节相同的副本，且包里带 .blend 原生候选；S2＝包里只有 GLB 副本和辅助脚本，没有原生件；S4a＝有记录指向仓库内的上游输入，但没有本件的重建源；S4＝只在清单或合同里声明了 SHA，仓库里没有源。

| 类别（LY-001） | S1 | S2 | S4a | S4 |
|---|---|---|---|---|
| 已入城·首屏（27） | **1**（雍门门体） | 12（院落原型） | 1（雍门地坪） | **13**（城垣 A 10 段，direct 门体与 2 段墙） |
| 已入城·按章（7） | 0 | 0 | 3（D08 地面、N2、market-cluster） | **4**（network-ground-stitched、retained、south、granary LOD0） |
| 隐藏试放（20） | **20** | 0 | 0 | 0 |
| 研究视图（14） | 0 | 0 | 14（flat 投影） | 0 |
| v1 及其他合同引用（42） | 3 | 0 | 10 | 29 |

**结论**：现在入城的 34 个 GLB（17,544,456 B）里，只有 **1 个（2.9%）** 能用仓库内的原生源和生成器重建。S2 的 12 个院落原型，在 `C2-courtyards/reproduction.zip` 里只是「originals/」副本，包里的 `project.py` 和 `verify_batch.py` 是 UV 投影与核验脚本，不是这些 GLB 的生成器（`UPSTREAM-README.md` 已确认）。城垣、地面、市肆和太仓共 **21 个入城 GLB，仓库里没有原生源**。110 个城中可达 GLB 里，有 107 个的 generator 字段是「Khronos glTF Blender I/O v4.3.47」，另 3 个是「Luoyang private granary city composer v1」。

### 6.2 源包的完整性（全部 35 个仓库内档案）

- 22 组分卷共 68 片，另有 13 个单 ZIP。拼合 SHA、`testzip` CRC 和分卷连续性**全部通过**。7 份内嵌 manifest 共 205 行，SHA 全部相符，缺失 0，不符 0。
- **6 个档案的 SHA 在任何已跟踪文本里都找不到声明**：`docs/fusions/F01/source.zip`、`docs/fusions/F02/source.zip`，以及 `modeling-lab/review-batches/2026-11-04/C3`、`C5`、`C6`、`C7-C8` 下的 `evidence-and-source.zip`。这些包可以打开，但无法证明是不是原件。
- 有 22 个档案（3.10 亿字节）在 `modeling-lab/`，**不在 `docs/` 下**。官方检查器的 `SOURCE` 正则只扫 `docs/`，而且 `\.part\d{3}$` 匹配不到两位编号的 `city-visible-web-handoff-v1-public.zip.part01…05`。所以这些源包的规范完全靠人工核对，必须由 LY-008/096/099 显式检查。

### 6.3 声明的原生件与私有档案

- **SHA 不一致（实测）**：雍门入城记录声明 `luoyang-yong-gate-study-v1/city/yong-Y-mid-hidden-trial.blend` 的 SHA 为 `2bbd57e497fb…`，但仓库内源包里同一路径的成员是 `e6b220d5a4b9…`。包内 `NATIVE-EQUIVALENCE.json` 把这个文件写成「Blender 4.3 内容相等的公开投影」，所以声明的 SHA 应该对应一个**私有原件**，而仓库里没有。
- **8 个私有档案身份无法在仓库内解析**：`projection-map.json` 中的 `a65b89f8…` 和 `052c6d6c…`；lingtai `f404f55a…`；taixue 长堂 `19ffc9dc…`；`PROJECTION-CHANGES` 中的 `bc58bba1…`；`iteration-C01` 中的 `efa2d4f6…`；`iteration-luoyang` 中的 `fb825b99…`；gallery 中的 `42fc810c…`。
- **只有文件名、没有 SHA 的待传源包**：@bce3211 有 1 个（`luoyang-yong-city-v1.1-private-source.zip`）。@origin/main 又多了 2 个：`luoyang-yong-road-release-source-v2.zip` 和 `luoyang-north-three-placement-source-v1.zip`。待传文件夹里没有对应批次的子目录。Release 里有没有这些文件，本席位**未验**，因为没有联网。
- 太仓 composer 是私有的，仓库里**连档案 SHA 都没有记录**。

### 6.4 隔离重建实测（Blender 5.2.1，空沙箱，只用基线提交上的字节）

| 源包 | zip SHA（=intake 声明） | 构建 | 重建 GLB | 字节相同 | 语义相同（几何+UV+材质+贴图，1e-5 m） |
|---|---|---|---|---|---|
| yong-gate-study-v1 | `4a9a0571…` | `source/build.py` 退出码 0，1.3 s | 3 | 0 | **3** |
| kaiyang / pingcheng / shangxi | `bad99bb9…`、`19646f31…`、`cc7265a7…` | 0 | 各 3 | 0 | 各 3 |
| zhongdong-v1.1 | `257e4df2…` | `source/build-lods.py`，读包内 `native/gate-Z.blend` | 3 | 0 | 3 |
| north-four-courts-v2 / perimeter / second-row | `e24f386f…`、`9b172032…`、`401e8c64…` | **单独放进沙箱时失败**（读不到 `C2-courtyard-family-v4/assets/*-C2.glb`）。从同一提交补入 12 个上游文件 `modeling-lab/review-batches/2026-11-04/C2-courtyards/assets/` 后，退出码 0 | 9 / 3 / 3 | 0 | 15 |

- 合计重建 30 个 GLB，**字节相同 0 个，语义相同 30 个**，覆盖全部 20 个隐藏试放件和 1 个入城件（雍门 LOD0）。字节不同的原因有两条，都已实测：导出器版本字符串（v5.2.40 与 v4.3.47），以及材质表顺序。雍门 LOD0 重建后 1,570,860 B，原件 1,570,856 B。
- 有 3 个包**缺依赖声明**：包里既没有写明要先放好 C2 上游资产，也没有写重建命令。实际重建命令和所需 Blender 版本都要读脚本才能知道，包里没有**固定写明 Blender 版本**。
- 语义比较器有 7 项正例与负例，全部通过（`qa/semantic-selftest.json`），包括 1 mm 顶点偏移、一个贴图字节翻转、材质互换、材质表重排后重映射。

### 6.5 私密材料扫描

- 洛阳和 modeling-lab 的 22 个源包里，全部成员（含 55 个 .blend，都是未压缩的 `BLENDER` 头，所以按原始字节扫描是有效的）**没有命中**以下任何一类：Windows 用户路径、AppData、/home 与 /Users、本机用户名、本地盘符路径、沙箱路径、GitHub/OpenAI/AWS 令牌、私钥、真实邮箱。110 个城中 GLB 的 JSON 块也没有命中。
- 非洛阳的 4 个 docs 源包含有代理沙箱路径：`docs/studies/005`、`006`、`014` 和 `docs/spaces/SD02` 的源包里有 `/home/agent/`、`/workspace/scratch/`。这些不是个人路径，但净化包要不要清掉，需要协调者定口径。
- 在扫描范围内的 421 个已跟踪文本里，只有 1 处命中：`docs/asset-spec/README.md` 中的 `D:/GitHub/`，是故意写明的待传文件夹路径，会公开发布。
- 原先的邮箱和令牌规则会把 `o.matrix_world@v.co`、`sk-camera-…` 误判，已修正，并为此加了负例。

### 6.6 许可证

洛阳的源包、资产卡和 source.json 里**没有任何 license 字段**。仓库里唯一写明许可的是字体（`fonts/OFL-LXGW-WenKai.txt`）和 three.js 的 LICENSE。源包里的贴图（例如雍门包的 `textures/LOD0/*.png`）没有来源和许可说明。这一条会变成交付时的阻断问题，需要协调者给出口径。

### 6.7 CRLF 与 SHA 声明

沿用 LY-001 的结论，本席位没有重做：`city-data.mjs` 的 13 条 sourceContracts 里，有 12 条声明的 SHA 只与本机 CRLF 检出的字节一致。因此任何「重建后哈希一致」的检查都必须基于提交 blob，否则在 LF 环境里会误报失败。

### 6.8 Release 侧

`sources-2026.11.05` 和各个 r 批次 Release 的资产清单与 digest **都没有取得**。按 `upload_sources.py` 的逻辑，核验要用 GitHub 给出的 `digest` 字段。这一步只能由协调者在登录了 GitHub 的机器上运行 `gh release view <tag> --json assets`，把输出交给本席位，然后离线比对。

### 6.9 基线漂移（bce3211 → origin/main cad338b）

运行 `compare_baselines.py`，得到 6 条阻断信号（`qa/drift-diff-bce3211-to-cad338b.json`）：
- 雍门接街新增 4 个 GLB（`yong-road-link-LOD0/1/2`、`yong-road-receiver-component209`），仓库里没有源，`source.json` 自称「byte-exact」重建，但所依据的 ZIP 是私有的。
- 2 个批次文件新列了待传私有源包。

这些属于原负责人正在做的成果，本席位只记录，不处理。正式开工时，必须以 LY-001 重新拍的快照为准。

## 7 复用判定

**无可直接复用的 LY-099 成果。** 源包核验本来就是按批次做的。现有成果中，能当作输入用的有三样：
1. LY-001 的 GLB 台账；
2. 各包的自述声明（NATIVE-EQUIVALENCE、clean-rebuild、byte-privacy-check、privacy-and-bytes）；
3. 本席位已经对 8 个包做的独立重放。

自述声明不能当作独立验收。

## 8 未知与待协调

- 私有源包：雍门 v1.1 城中装配包、太仓 composer、projection-map 引用的 2 个档案、lingtai/taixue 原件、雍门接街 v2、北三院 v1。它们放在哪里、SHA 是多少、能不能交给本席位，都需要协调者回答。
- 源包许可证与贴图来源的口径。
- 代理沙箱路径（`/home/agent`）是否算「私密路径」。
- LY-008 的检查器还没有交付，所以本席位的脚本只是 LY-099 自己的补充检查，不代替官方 checker。
