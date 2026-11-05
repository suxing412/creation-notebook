# LY-096｜资源预算与官方规范总检（开工准备稿，2026-11-06 复核版）

席位类型：独立验收。依赖：G（001/002/005/006/007/008/009/010）、LY-008、LY-091～094。当前阶段：**开工准备**，状态「待输入」。

本版在 2026-11-05 的准备稿基础上复核。两天之间的变化：G 席位中 001、002、005、006、007、008、009 已交付；**LY-010 仍然没有目录**；091～094 都只有 prep/。所以 G 还没冻结，也没有可验的批次。

本稿只做三件事：
1. 把验收方案和脚本接上已交付的 LY-007 规则和 LY-008 检查器；
2. 在 `bce3211` 上重跑「改前」基线，证明结果能逐字节复现；
3. 与 LY-008 对拍，补上本席位检查器的两个漏检。

我没有制作或修改任何几何，也没有写共享文件。lab 仓库全程只读：
- 开工前和收尾时各记一次 HEAD、origin/main、`git status --short` 以及 `lab/tools/__pycache__` 的时间戳，两份记录逐字节相同（`baseline/rerun-20261106/lab-status-{before,after}.txt`）；
- `git diff --quiet bce3211 -- docs lab/tools` 通过。

另有一处 lab 状态变化，不是我造成的：11-05 的 `lab-status-before.txt` 里，`lab/data/{assets,glb-cache,report}.json` 带「M」标记（工作树有改动）；今天这三个文件已经没有 M 标记。我没有运行 build_assets.py，也没有做任何 git 写操作。

## 1 本项目标（TASKPOOL 第978行）

每一批拟合并的工作包都要交一份报告，内容包括：每个 GLB 的大小、三档 LOD 的区别、纹理与材质、公共路径隐私、孤儿文件、官方 checker 结果、总载入预算。

验收四条：
1. 官方 checker 没有阻断错误；
2. 公共文件白名单与 SHA 一致；
3. 低档和压缩造成的差异如实写明；
4. 新源工程为零，私密路径和凭据为零。

边界：源工程不能进 docs；压缩件要核对解码后的几何和材质，不能悄悄降低近景；传输上限和官网的 15MB 规则分开核。

**本席位不判的事**：「模型能读取」「局部通行通过」「已入城」「真实结构安全」「历史复原成立」是五件不同的事。本席位只证明第一件里的一部分，即文件可读、数值有限、引用完整、体积合规、不含私密内容。其余四件分别归 091～095、097、098。

## 2 基线身份

| 项 | 值 |
|---|---|
| 指定基线 | `bce3211f818ee5a8bef1773539da70695ba37b17`，即 lab 的 HEAD（11-06 复核，未变） |
| 字节口径 | 一律用 git **提交 blob**（`git cat-file`）。本机 `core.autocrlf=true`，文本的工作树字节和提交字节不同。导出副本必须用 `git -c core.autocrlf=false archive`，与 LY-008 的结论一致 |
| 漂移 | 本机 `origin/main` 仍是 `cad338ba683f`，比 bce3211 多三个提交：新增 17 个文件，其中 4 个是 GLB；改动 5 个文件。我没有 fetch，所以远端可能已经更新。正式验收必须用 LY-100 当批的 base 重测 |
| 复现 | 今天在 bce3211 上重跑，public-files、glb-inventory、lod-tiers、orphans、privacy、source-files、load-budget、c15-gzip-estimate 八个输出与 11-05 的 SHA256 **逐字节相同**；官方 checker 重放出的 report.json 只差 generated 时间戳（`baseline/rerun-20261106/bce3211/`）。随后把检查器改严，又跑了一遍（`bce3211-lib2/`），六个 JSON 只有 `meta.libSha256` 变了，内容完全相同，说明新加的规则在 442 个真实 GLB 上一次也没有命中 |

## 3 已有成果核对与复用判定

| 成果 | 路径 · SHA256 | 用法 |
|---|---|---|
| LY-008 检查器 | `LY-008/source/ly_check.py` · `39aaa491859e1a79…`（与其普查记录的 checkerSha256 相同） | 正式门禁中 GLB 层的主检查器（T16）；另用于 lodset（T05b）、package（T03b）、official（T01） |
| LY-008 普查 | `LY-008/qa/census-bce3211.json` · `618688c54cd1…` | 与本席位 glb-inventory 逐件对拍：442/442 的 sha、bytes、triangles **零差异**（`crosscheck/crosscheck-ly008.json`） |
| LY-008 官方运行记录 | `LY-008/qa/official-runs.json` · `41a54d87dfde…` | 在 bce3211 导出副本上，官方 checker 退出码依次为 0、注入后 1、撤回后 0，作为 T01 的负例证据复用；本席位不再导出 1.8GB 副本重做 |
| LY-007 LOD 规则 | `LY-007/baseline/lod-rules.json` · `fbf53757be2e…` | T05/T05b/T06 的判据：三角比 LOD1/LOD0 在 [0.17, 0.62]，LOD2/LOD0 在 [0.05, 0.20]；LOD0 复制判据；LOD0 原件不得覆盖 |
| LY-009 任务板 v2 | `LY-009/board/taskboard.v2.json` · `bd2fcbbe02a1…` | 本席位白名单 `LY-096/**`；PZ-07（advisory，材质待拍板）；状态「待输入」，缺 LY-010 和 091～094 |
| 官方 checker 重放 | `baseline/rerun-20261106/bce3211/checker-replay/checker-verdict.json` | exit 0；89 张卡，0 张有错误，50 张有提醒；repoErrors 0，orphans 0 |

**复用判定：无。** LY-096 按批次验依赖闭包，目前还没有任何批次 manifest，所以没有现成合格成果可以替代本席位的产物。LY-008 的检查器、普查和官方运行记录都只**作为输入复用**，不能顶替本项交付。

## 4 改 / 不改范围

- 写入：开工准备阶段只写 `LY-096/prep/`，正式阶段写 `LY-096/`。
- 不改：任何 GLB、资产卡、city-data.mjs、项目卡、构建数据、lab 工具；其他席位的文件（包括 LY-008 的检查器）也不改。发现的问题只记录，并写明责任方。
- 官方 checker 不在 lab 里直接运行。正式做法是对导出副本跑 LY-008 的 `ly_check official <导出副本>`。本席位的 `checker_replay.py` 只用来对照计数：它在工作树上执行，记下的 `checkerSha256 6dc990b4…` 是 CRLF 工作树字节，不是提交字节 `ed7664a7…`，所以正式报告必须绑定提交字节的 SHA。

## 5 证据分类

本席位的结论全部属于「C 工程实测」，依据是提交字节和本机 CPU 脚本。以下没有实测，一律写「未验」：
- 线上 Pages 的实际响应体（C15 口径）：任务不许下载。
- 部署时 gltfpack 压缩出的产物：本机没有 gltfpack@1.3.0。
- 浏览器、GPU、手机：归 LY-097。
- 纹理显存：只是估算（按 RGBA8 加完整 mip 链）。

本席位不涉及历史证据，不判原始考古、类比或复原是否成立。

## 6 实测缺口（bce3211；数字绑定 `baseline/rerun-20261106/` 与 `crosscheck/`）

### 6.1 今天新发现

| # | 项 | 数字 | 证据 / 脚本 |
|---|---|---|---|
| N1 | **本席位检查器的漏检**（与 LY-008 对拍时发现） | (a) JSON 里的 `NaN` 字面量：Python 的 `json.loads` 会静默接受，所以 LY-008 的 N06 在我这边判为通过。(b) POSITION 的 min/max 与实际数据不符：我原来只记 warning，而 glTF 要求 min/max 准确，LY-008 判为错误。我自己的两个「好样本」（good-textured-quad、public-github-handle）也写错了 min/max，三个轴用的是同一个标量。三处都已修正，新增 2 个负例，**selftest 37/37**。用修正前的库复测，这 2 个负例都判不出问题 | `source/ly096_lib.py`、`source/selftest.py`、`negatives/position-minmax-wrong.glb`、`negatives/nan-literal-in-json.glb` |
| N2 | 对拍结果 | 我的 14 个夹具交给 LY-008：13 个结论一致；1 个不一致可以解释，即 `credential-in-extras`，原因是 LY-008 **没有凭据规则**，T10 继续由本席位负责。LY-008 的 52 个 glb 夹具交给我：43 个一致；9 个不一致都能解释，其中 6 个属于 LY-007 的 ly-p01 风格档，PNG 文字块和上传通道这两条规则只有 LY-008 有，用户名词需要运行时传 `--private-token`；另有 3 个夹具不在包内。**无法解释的不一致：0** | `crosscheck/crosscheck-ly008.json`；`source/crosscheck_ly008.py` |
| N3 | 「纹理档」按 LY-007/008 冻结的规则是**错误**，不是只需披露 | LY-008 lodset 的结果：<br>- `yong-apron` 三档都是 68 三角，判 `LOD_NOT_DECREASING` 和 `LOD_SAME_GEOMETRY`；它的 LOD0 在首屏。<br>- `northern-altar-C` 三档都是 268 三角，判 `LOD_NOT_DECREASING`；LY-008 **没有**判 SAME_GEOMETRY，但本席位的几何指纹三档相同，两边口径有差。<br>- `granary-receiving` 三档为 700/700/60，判 `LOD_BBOX`、`LOD_NOT_DECREASING`、`LOD_SAME_GEOMETRY`。<br>- cad338b 新增的 `yong-road-link` 三档都是 12 三角，判 `LOD_NOT_DECREASING` 和 `LOD_SAME_GEOMETRY`。<br>正对照 `granary-city`（9508/1604/760）和 `palace-admission-court-closed`（23464/10776/3648）都是 exit 0。因此 11-05 稿里「声明 textureOnlyLods 即可放行」的规则**作废**：必须有 `lodWaivers`，并写明决定人（LY-010 或制作人） | `crosscheck/crosscheck-ly008.json` 中的 lodset；`dryrun/20261106/ly008-batch-cad338b-*.json` |
| N4 | 压缩件只压了一部分，旧的解码指纹看不到压缩流 | `A1-v3-LOD1.glb`（11,954,084 B）里，POSITION 和 indices 用的是**未压缩**视图：buffer0 中的未压缩视图共 6,146,220 B，其中贴图 355,428 B。只有 85 个 NORMAL/TEXCOORD 视图经过压缩，压缩流 5,755,317 B，解码后 9,291,816 B。原来的 `decodedGeometryFingerprint` 只哈希 POSITION 和 indices，**看不到**压缩流的损坏：三个负例的这个指纹都与原件相同。现已给 `decode_meshopt.mjs` 加上全属性指纹 `0f952bd7aa7d…`，并检查非有限数和法线单位长度（非单位法线 0 个）。meshopt 负例 4/4 通过：把视图长度减半、在流内翻转 64 字节、把 count 加 64，城景解码器都报 `Malformed buffer data`；原样重新打包的文件与原件字节相同 | `negatives/meshopt-negatives.json`；`source/meshopt_negatives.py`；`baseline/rerun-20261106/bce3211-lib2/meshopt-decode.json` |
| N5 | 门禁演练（cad338b，接 LY-008） | - 只给真实差集白名单：T01（没有 cad338b 的导出树）、T05、T05b 阻断。<br>- 加 lodWaivers（演练夹具，已明确标注「不是真实决定」）：只剩 T01 阻断。<br>- 删掉 LY-008 的证据：T16 阻断。<br>- BASE=CAND=bce3211 且给空白名单：exit 0。<br>- 不给白名单：T03 阻断 | `dryrun/20261106/gate-*.json` |

### 6.2 沿用 11-05 的缺口（今天复测，数字不变）

| # | 项 | 数字 |
|---|---|---|
| G1 | 官方 checker 只对卡片引用的 GLB 查体积和面数 | 442 个 GLB 中有 88 个不在任何卡片里，合计 45,018,724 B，其中 75 个在 cities/luoyang；其中最大的 4,408,140 B，未超限 |
| G2 | 官方 glb_audit 漏检 | NaN/Inf、外链贴图缺失、GLB JSON 中的本机路径或凭据、LOD 复制，官方都只报 `PRIMS_NO_NORMAL`。LY-008 C5 独立得到相同结论 |
| G3 | 单个 GLB 超过 15,000,000 B | 0 个。最大的是 `A1-v3-LOD1`，11,954,084 B；5MB～15MB 之间有 9 个 |
| G4 | 传输承载 | A1 做 base64 编码后为 15,938,780 B，超过 15,000,000。用 LY-008 的 `--upload-limit 15000000 --upload-encoding base64` 复测，判 `UPLOAD_OVER_CHANNEL_LIMIT`。这里的 15,000,000 只是演示用的假设上限，真实通道的上限数字缺失 |
| G7 | 私密路径与凭据 | 凭据 0。本机路径 2 处，都在 `docs/asset-spec/README.md:145`，属既有问题，交 LY-100 或协调者处理；LY-008 的结论相同 |
| G8 | 源工程 | 官方规则命中 104 个，全部已归档；另有 209 个 `.py`，作为基线计数 |
| G9 | 孤儿与重复 | 官方口径 0 个；扩展口径 1 个（`docs/spaces/SD01-v02/assets/jointworks.glb`，1,500,180 B）；逐字节重复 21 组，多占 19,274,564 B |
| G10 | 总载入预算 | 首屏 21 个 GLB、59 个实例，共 3,872,084 B，等于 initialModelBytes；全部章节 28 个 GLB，共 13,466,348 B，等于 allCityModelBytes；入口可达 48 个 GLB，共 25,583,332 B；代码闭包 2,430,016 B；每章增量最大的是 terrain，6,825,508 B |
| G11 | C15（冷开 ≤1,900,000 B；这条规则在 bce3211 之后才定） | bce3211 首屏 gzip6 估算 2,691,126 B，超限；cad338b 为 1,440,860 B，未超。两者都是本地估算，线上未验 |
| G12 | 三角数口径 | 首屏按实例相加的上界是 74,068；LY-001 实测页面显示 123,860。LY-008 另有一处口径差：life-block-LOD0 按官方口径是 116,108，按实例绘制是 506,828 |
| G13 | SHA 合同 | 85 对里 73 对与提交字节一致；另有 12 对 sourceContracts 只与 CRLF 字节一致（PZ-09，归 LY-100） |
| G14 | 官方 audit 既有标记 | HIGH_DRAWCALLS 6 个；wuku-B 三档各 14 个退化三角；EXT_REQUIRED 1 个 |

## 7 脚本（`prep/source/`，SHA 见 prep-status.json）

既有脚本：
- `ly096_lib.py`（今天改严）
- `baseline_scan.py`
- `checker_replay.py`
- `load_budget.py`
- `gzip_estimate.py`
- `decode_meshopt.mjs`（今天加了全属性指纹）
- `sha_contracts.py`
- `compare_baselines.py`（今天加了 T16、T05b、T05c）
- `selftest.py`（37 个用例）

今天新增：
- `crosscheck_ly008.py`：与 LY-008 对拍；exit 0 表示所有不一致都已解释。
- `ly008_batch.py BASE CAND TMP [WL]`：从 CAND 的 blob 里取出本批触及的 GLB，逐个跑 `ly_check glb`；对触及的 LOD 组跑 `lodset`；结果写到 `CAND/ly008/`。
- `meshopt_negatives.py`：T07 的压缩流损坏负例。
- `update_inputs.py`：刷新 inputs.json，并复核 18 个仓库输入的提交 SHA，18/18 未变。

## 8 未知与未验

- **LY-010 缺失**：T08 部署压缩、T12 上传通道、T14 的 C15 线上响应体，这几项「未验」该算阻断还是「待审」，现在定不了。
- **PZ-07 未清**：ly-p01 档的判据可能随 LY-007 改版而变，所以 T16 的 `--profile ly-p01` 要绑定 LY-007 的版本号。
- northern-altar-C 的几何是否相同，两边结论不一致：本席位的指纹三档相同，LY-008 没有报 SAME_GEOMETRY。原因还没查，可能是 LY-008 的几何哈希包含了法线或 UV。lodset 仍判 NOT_DECREASING，所以这个分歧不影响结论。
- 部署压缩产物、线上响应体、浏览器/GPU 都没有验证，原因见第 5 节。
- 没有用 Blender：本项只验文件、规范和预算，不测尺寸、净空和交体；压缩件的解码以城景自带的解码器为准，Blender 导入器的结果不能代表城景。
