# LY-099 测试计划：源包与可复现交付核验

本计划里的检查可以直接运行。每一批交付前，都先在**该批的 base ref 上重跑一次基线**，保证前后两次测量用的是同一套工具、同一种字节基准（提交 blob）。每项检查都要绑定被检对象的 SHA256。失败不能改写成通过；本席位够不到的环境，记作「未验」，不能当作通过。

## 0 输入与运行方式

| 项 | 来源 |
|---|---|
| 批次 manifest | 由协调者或 LY-100 交来，必须含 `selected_tasks`、`dependency_closure`、`gate_results`、`excluded_regions` 四个字段（见任务池「分批合并」节） |
| base ref / batch ref | base ref 是出批时的最新 main，batch ref 是本批所在分支或 overlay 的提交。两者都写完整的 40 位 SHA |
| 城中 GLB 分类 | 取 LY-001 **为本批新拍的快照**里的 `qa/glb-files.csv`。不在台账里的 GLB 会标成 `UNCLASSIFIED-not-in-LY-001-ledger`，照样检查 |
| Release 证据 | 由协调者在登录了 GitHub 的机器上，对涉及的每个 Release（`sources-2026.11.05`、本批的 `r…`）运行 `gh release view <tag> --json assets`，把 JSON 交给本席位离线比对。本席位自己不联网 |
| 工具 | `prep/tools/` 下的全部脚本（正式开工时移到 `LY-099/source/`），Python 3.11 加 `-I`，Blender 5.2.1（记录实际用的版本） |

```
B=<base sha>; T=<batch sha>
python -I tools/source_baseline.py --selftest --selftest-out qa/selftest.json            # 必须 20/20（v2）
python -I tools/semantic_selftest.py --tmp <空目录> --out qa/semantic-selftest.json        # 必须 7/7
python -I tools/source_baseline.py --ref $B --out qa/baseline-$B.json
python -I tools/source_baseline.py --ref $T --out qa/baseline-$T.json
python -I tools/compare_selftest.py --baseline qa/baseline-$B.json --tmp <空目录> --out qa/compare-selftest.json   # 必须 6/6
python -I tools/compare_baselines.py qa/baseline-$B.json qa/baseline-$T.json --out qa/diff-$B-$T.json   # 退出码 1 = 有阻断
# 本批依赖闭包里的每个源包各跑两次（两个不同的空沙箱），第二次的 --out 用 -run2：
python -I tools/isolated_rebuild.py --ref $T --pack <包目录> --root <包顶层目录> --build <脚本> --auto [--stage <git目录>=<沙箱相对路径>] --sandbox <空目录> --out qa/rebuild-<包>-$T.json
# LY-008 checker（SHA 写进结论；当前 39aaa491…）：
python -I ../LY-008/source/ly_check.py --json qa/ly008-privacy-$T.json privacy <batch ref 的 docs 导出目录> --archived <同一目录>/asset-spec/source-archive.json
python -I ../LY-008/source/ly_check.py --json qa/ly008-package-<席位>.json package workpacks/<席位>   # 本批每个生产席位各一次
```

**同一基线重放的做法**：所有 `source_baseline` 和 `isolated_rebuild` 都按 `git show <ref>:<path>` 读提交 blob，不读工作树，所以 lab 的检出停在哪个提交都不影响结果。ref 一律写 40 位 SHA，不写分支名；`origin/main` 只在开工时由 LY-001 或协调者解析一次，之后整批都用这个 SHA。LY-008 checker 需要目录输入时，用 `git archive <ref> docs | tar -x -C <空目录>` 导出到席位自己的临时目录，扫描完删除，不写 lab。

**「改前」基线（当前 main = bce3211）**：`qa/baseline-bce3211.json` SHA `0ba607b38ffcfb16d49a6673d066758d58b7969db4ce2b1a55b4bfba4a5b82ac`，工具 `source_baseline.py` v2 SHA `0f6e26a9…`。用旧 v1 工具（SHA `a0a88025…`）跑出的是 `fea57ded…`，两者只差 `privacyText`。以后对比时，基线和批次两边必须用同一版工具；工具升级了，就两边都重跑。

确定性：v1 在 2026-11-05 和 2026-11-06 各跑一次，都得到 `fea57ded…`；v2 的 selftest 输出 `a371dae2…`。

## 1 检查项

### T1 批次闭包完整（阻断）
- **通过**：manifest 四个字段齐全；`selected_tasks` 的每个包都有带白名单和 SHA 的 delivery-manifest；依赖闭包包含每个包的全部硬前置。
- **失败**：缺字段；包的前置被裁掉；把「本批未纳入」写成「通过」。
- **绑定 SHA**：manifest 本身。

### T2 新增或改动的 GLB 都能追到源（阻断）
- 从 `diff-$B-$T.json` 和各包的 delivery-manifest 取出本批新增和改动的 GLB，每一个都要满足下面一条：
  - (a) **S1**：本批的源包里有它的逐字节副本，且包里带原生件或生成器。这种情况还要过 T4。
  - (b) 写明私有源包的**文件名、SHA256 和所在 Release tag**，并且 Release 证据里有同名资产，`digest` 与该 SHA 相等。
  - (c) 明确写「从 GLB 重建，无原生原件」，卡片、source.json 和 brief 三处说法一致。
- **失败例**（已在当前 main 上实测到）：
  - `yong-road-link-*` 共 4 个文件处于 S4，私有 ZIP 只有文件名，没有 SHA；
  - 批次文件 `r2026.11.05-5` 列出的源包没有 SHA。
- **不能算通过**：仓库内只有 GLB 副本、外加 UV 或核验脚本的（S2）；记录只指向上游输入的（S4a）；生产方自称「byte-exact」「equal」「clean-rebuild」但没有被重放过的。

### T3 源包完整性（阻断）
- **通过**：
  - 每片分卷的 SHA 等于声明值；
  - 分卷编号从 1 开始连续；
  - 拼合后的 SHA 等于 intake、manifest 或 archive 里的 zipSHA256；
  - `testzip()` 返回 None；
  - 内嵌 manifest 每一行的 SHA 都相符，缺失为 0。
  - 基线：35/35 个档案能打开，内嵌 manifest 205/205 行相符。
- **负例**（`selftest.json`，必须全部失败）：分卷倒序、第 2 片翻转一个字节、缺最后一片、ZIP 被截断、成员 SHA 与 manifest 不符、CRLF 改写后的字节。
- **失败**：拼合后的 SHA 在任何地方都没有声明。目前有 6 个档案是这种情况：F01 和 F02 的 `source.zip`，C3、C5、C6、C7-C8 的 `evidence-and-source.zip`。它们不能作为原件接收。
- **容差**：无，SHA 必须逐字节相同。

### T4 隔离重建（失败或差异没有解释时阻断）
- **步骤**：
  1. 用空沙箱，只写入 batch ref 上的提交字节；核对 zip SHA 后解压，并为每个包内 GLB 留一份副本；
  2. 用 `--stage` 从同一个 ref 补入依赖闭包里的上游输入；
  3. 运行包自己的构建命令 `blender -b --factory-startup --python-exit-code 1 -P <脚本>`；
  4. 记录 Blender 版本、退出码和耗时。
- **判级**：
  - `bytes`：文件逐字节相同，最好。
  - `semantic(geometry+uv+materials+images)`：每个网格的有向三角形多重集在 1e-5 m 下一致，UV0 多重集一致，材质在把贴图引用解析成图像 SHA 后一致，图像字节集合一致。这一级要附上字节差异的书面解释（例如导出器版本字符串、材质表顺序）才算通过。
  - `geometry-only` 或 `different`：**阻断**。
- **正负例**（`semantic-selftest.json`，都必须得到预期的级别）：
  - 文件与自身比较：`bytes`；
  - LOD0 对 LOD1：`different`；
  - 只改 `asset.generator`：`semantic`；
  - 材质表重排并重映射索引：`semantic`；
  - 两个图元互换材质：`different`；
  - 一个顶点移动 1 mm：`different`；
  - 一个贴图字节翻转：`geometry-only`。
- **已测基线**：8 个包、30 个 GLB，字节相同 0 个，语义相同 30 个。3 个院落包单独放进沙箱会失败，要补入 `C2-courtyards/assets` 的 12 个上游文件才能通过。这条依赖应写进包自己的构建说明；写进去之前，按 T4 的发现记录。
- **重放之间的确定性（阻断）**：同一个包、同一个 ref、同一个 Blender 版本，在两个不同的空沙箱里各跑一次，两次的重建 GLB 必须**逐字节相同**。不同就说明构建脚本依赖了时间、随机数或沙箱路径，算阻断。基线：雍门包 3/3 字节相同（`qa/replay-determinism-2026-11-06.json`，LOD0 两次都是 `6d248504…`）。
- **已知局限**：按 1e-5 m 网格取整，所以小于容差、但恰好跨过网格线的变化会报成 different。这样偏保守，不会出现误判通过。只比较 UV0，不比较法线、切线、顶点色和动画；有动件的包要另加检查（LY-007 D-U01 的条件）。能否用 5.2.1 代替原来的 4.3 环境，由 LY-007 的 **P-GENERATOR** 决定，目前「待制作人拍板」。拍板前一律写「5.2.1 下语义相等，4.3 未重放」，状态记「未验」，不能写成「通过」。

### T5 无私密材料（阻断）
- **范围**：本批源包的全部成员，包括 .blend 的原始字节（先确认文件头是 `BLENDER`；如果是 zstd 或 gzip 压缩，要先解压，做不到就记「未扫描」）、每个 GLB 的 JSON 块、公开的文本文件。
- **检查的模式**：Windows 用户路径、AppData、/home 和 /Users、本机用户名、本地盘符路径（GitHub、Blender、Temp）、.blend 里的绝对盘符路径、沙箱路径（/mnt/data、/tmp/x/、/workspace/x/）、GitHub/OpenAI/Anthropic/AWS 令牌、私钥、真实邮箱。
- **负例**（必须全部被抓到）：注入的 `C:/Users/someone`、二进制里的 `C:\Users\bob`、`ghp_…`、`/mnt/data`、.blend 里的 `D:\art\…`、看起来真实的邮箱，以及路径段含中文的 `D:/待删-<日期>-已传/`。最后这一条是 v2 新加的：v1 正则漏掉了它，是对照 LY-008 结果时发现的。
- **正例**（都不能被抓）：`o.matrix_world@v.co`、`sk-camera-safe-area-proposal`、`//textures/` 这类相对路径、`https://github.com/…/`、`textures/LOD0/a.png`。
- **基线**：洛阳的源包命中 0 处；非洛阳的 4 个 docs 源包含有 `/home/agent/` 或 `/workspace/scratch/`；`asset-spec/README.md` 里有 2 处盘符路径，`D:/GitHub/…` 和 `D:/待删-…`，与 LY-008 的 `PRIVATE_PATH_PUBLIC_FILE` 结果相同。本批**新出现**的命中直接阻断；继承下来的命中继续列出，等协调者定口径。
- **交叉核对**：同一批同时跑本席位扫描器和 LY-008 的 `ly_check privacy`（T12）。只要有一边报了强命中，就要逐条解释；不能拿一边的「0 命中」去抵消另一边的命中。

### T6 不覆盖旧源包（阻断）
- **仓库内**：`compare_baselines` 里的每个档案字节都不能变，也不能消失。
- **Release 内**：Release 证据里的旧资产名都还在，digest 不变。待传文件夹里如果出现同名但内容不同的文件，必须「留在待传文件夹」，这是 `upload_sources.py` 现有的行为。
- **负例**（`tools/compare_selftest.py`，在真实基线的副本上构造，必须 6/6）：同一基线自比，退出码 0；旧档案字节被改、旧档案被删、城中 GLB 从 S1 降到 S4、新增文本隐私命中、新增 S4 城中 GLB，这 5 种都必须退出码 1，并给出对应的阻断行。基线结果 6/6（`qa/compare-selftest.json`，绑定 `compare_baselines.py` `3fdc5366…` 和基线 `0ba607b3…`）。

### T7 许可证与贴图来源（阻断，除非协调者事先接受）
- 每个源包和每张新卡片都要写明代码、模型、贴图的许可证，以及贴图从哪里来（程序生成还是第三方）。
- **基线**：洛阳的许可证字段为 0 个。目前只能记「未验/阻断」，不能写成通过。

### T8 哈希基准（阻断）
- 包里声明的每个 SHA 都必须等于**提交 blob** 的 SHA。只与 CRLF 检出字节相符的算失败，LY-001 的 C8 已经查出 12/13 条合同是这种情况。
- **负例**：`selftest` 里的 CRLF 用例。

### T9 重建命令与版本有书面记录（第一个正式批次起为阻断）
- LY-008 已交付，但它的 checker 不检查重建命令和版本记录，所以这一项仍由本席位自己检查。
- **通过**：包的 README 或 manifest 写明确切命令、脚本入口、要求的 Blender/Python 版本、要先放好的输入，以及预期输出的 SHA。
- **基线**：8 个包都没有固定写明 Blender 版本；3 个包没有声明上游输入；zhongdong 有两个脚本，没有写明先后顺序。

### T10 官方检查器的扫描缺口（记录下来，交给 LY-008/096）
- `build_assets.py` 只扫 `docs/`，`\.part\d{3}$` 匹配不到两位编号的分卷。在官方检查器覆盖这些之前，LY-099 对 `docs/` 以外的源文件自己跑 T3 和 T5。这份报告不能代替官方检查器的运行结果。

### T11 Release 核验（拿到证据前一律「未验」）
- 有协调者交来的 JSON 时：本批 `sources` 里的每个名字、每个指名的私有包，都必须有对应资产，且 `digest` 等于 `sha256:<声明值>`。
- 没有 JSON 时：记「Release 未验」，整个源包保持**阻断**，不能写成通过。

### T12 LY-008 checker 交叉运行（阻断）
- **怎么跑**：对本批每个生产席位跑 `ly_check.py package workpacks/<席位>`；对 batch ref 用 `git archive` 导出的 docs 目录跑 `ly_check.py privacy … --archived …/asset-spec/source-archive.json`。checker 的 SHA 写进结论，当前是 `39aaa491859e1a796080dd91ccabd1c47423cf7f9ef2af61c5f123b04b3dff4b`。
- **通过**：`package` 没有 error；`privacy` 和 bce3211 基线相比没有新的 error。基线上已有 README 的 2 处 `PRIVATE_PATH_PUBLIC_FILE`，以及 studies 下几处 `/home/agent/` 的 `PRIVATE_PATH_WEAK`，这些属于继承项。
- **负例**：直接用 LY-008 自带的 `qa/negatives/`（`run_selftest.py`）。checker 的 SHA 变了，就先重跑它的 selftest，再拿来用。
- **边界**：这只是 LY-008 的规范检查，不代替官方 `build_assets.py --check`（那一项由 LY-096 负责），也不代替 T4 的重建。

## 2 每批结论的格式

写入 `qa/ly099-<batch>.json`：`{batch, baseRef, batchRef, toolsSha256{}, checks:[{id, status: 通过|阻断|未验|本批未纳入, evidence:[路径+sha], note}], blocking:[…], unresolved:[…]}`。只有在没有任何「阻断」、且所有「未验」项都是 LY-010 明确允许的情况下，交接时才能写「可接城」。
