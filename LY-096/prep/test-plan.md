# LY-096 验收测试方案（每批次可直接重跑；2026-11-06 版）

每一批对两个版本各跑一遍：
- **BASE**：LY-100 这批开始合并时的最新 main，不能沿用 bce3211。
- **CAND**：这批的候选提交，即 LY-100 在独立分支上合好、还没推送的那一个。

两边用同一套脚本、同一份规范文件。门禁只判本批新出现的问题；既有问题标为 `inherited` 另列，不算在本批头上。批次范围以 manifest 的 `selected_tasks` 和 `dependency_closure` 为准；`excluded_regions` 记为「本批未纳入」，不算「已通过」。

## 0 环境与绑定（每次报告都要写进 meta）

| 绑定项 | 现值（bce3211 提交字节） |
|---|---|
| 官方 checker `lab/tools/build_assets.py` | `ed7664a7d15c6f01…`（全长见 `baseline/input-shas.json`）。注意：工作树 CRLF 字节是 `6dc990b4…`，不能用来绑定 |
| `lab/tools/glb_audit.py` | `99d64d7c868ac9b7…` |
| `docs/asset-spec/categories.json` | `63f41789873383a0…`；spec 1，glbMaxMB 15，glbWarnMB 5，trianglesMax 500,000 |
| `docs/asset-spec/source-archive.json` | `8b80a86d7b93e918…`（104 个文件） |
| `slim_site.py` / `pages.yml` | `e6942333e17cfe4b…` / `33baf52c6db5a2fd…`；gltfpack@1.3.0 `-cc -kn -km -ke -vp 16 -vt 14` |
| 城景解码器 `docs/vendor/meshopt_decoder.module.js` | `d428e73a000057c6…` |
| LY-008 `ly_check.py` | `39aaa491859e1a796080dd91ccabd1c47423cf7f9ef2af61c5f123b04b3dff4b`（版本 ly-check 1.0） |
| LY-007 `lod-rules.json` | `fbf53757be2e…`（全长见 inputs.json）；PZ-07 清了之后要换成新版 |
| 本席位脚本 | `prep-status.json` → scripts |

运行一律加 `python -I -B`，不写 pyc，lab 只读。临时文件（取出的 blob、导出树、12MB 的 meshopt 负例）放在工作包**外面**。

导出树（T01 要用）：
```
git -C <lab> -c core.autocrlf=false archive <CAND> | tar -x -C <TMP>/tree-<CAND>
```
导出后按 LY-008 `run_official.py` 的做法逐个核对 blob id。lab 的 HEAD 如果不是 CAND，就只能走导出树这条路。

## 1 跑法

```
S=D:/GitHub/creation-notebook-workpacks/LY-096/prep/source
K=D:/GitHub/creation-notebook-workpacks/LY-008/source/ly_check.py
python -I -B $S/selftest.py                         # 37/37 才继续：先证明检查器会失败
python -I -B $S/crosscheck_ly008.py <TMP>/x         # 与 LY-008 对拍：unexplained 必须为 0
for R in BASE CAND; do
  python -I -B $S/baseline_scan.py $R OUT/$R
  python -I -B $S/load_budget.py OUT/$R/glb-inventory.json OUT/$R/load-budget.json <TREE_$R>/docs/cities/luoyang/city-data.mjs
  python -I -B $S/gzip_estimate.py OUT/$R/load-budget.json $R OUT/$R/c15-gzip-estimate.json
  python -I -B $K --json OUT/$R/official.json official <TMP>/tree-$R        # T01 主路线（LY-008，导出副本）
  python -I -B $S/checker_replay.py OUT/$R/checker-replay <TMP>/tree-$R    # T01 计数对照
done
python -I -B $S/ly008_batch.py OUT/BASE OUT/CAND <TMP>/blobs WL.json        # T16 / T05b
node $S/decode_meshopt.mjs <decoder> <本批每个压缩 GLB> > OUT/CAND/meshopt-decode.json   # T07
python -I -B $K --json OUT/CAND/privacy.json privacy <TMP>/tree-CAND/docs  # T10 第二检查器
for P in <本批每个席位包>; do python -I -B $K --json OUT/CAND/pkg-$P.json package <workpacks>/$P; done   # T03b
python -I -B $S/compare_baselines.py OUT/BASE OUT/CAND OUT/gate.json WL.json   # exit 0 通过 / 1 阻断 / 2 缺输入
```

`WL.json` 由本批各包的 `delivery-manifest.json` 汇总而成，键见 `compare_baselines.py` 和 `ly008_batch.py` 文件头：
- `files[{path,sha256}]`、`removed[]`、`declaredNearChanges[]`
- `budget{initialMaxBytes,chapterMaxBytes}`
- `ly008Profile{path:{profile,lod}}`、`privateTokens[]`、`lodFamily{group:house}`
- `lodWaivers[{group,codes,decider,ref}]`

## 2 检查项（对应「本项验收」四条和「具体产物」）

| ID | 检查 | 正例（已跑） | 负例（必须失败） | 容差 / 口径 | 阻断 |
|---|---|---|---|---|---|
| T01 | 官方 `build_assets.py --check` 在 CAND 导出副本上 exit 0 | bce3211：exit 0，89 张卡，0 张有错误，50 张有提醒（本席位重放与 LY-008 结果一致） | LY-008 `official-runs.json`：注入 12 张卡和 1 个 `.blend` 后 exit 1，撤回后回到 0。本批复跑时，在导出副本里加一张缺 cover 的卡，必须 exit 1 | 计数必须与 CAND 提交的 `lab/data/report.json` 一致，否则判「无法判定」；绑定提交字节 SHA | 是 |
| T02 | repoErrors 为空；新增的 warning 逐条列出 | bce3211：[] | 同 T01 的 `.blend` 负例 | 新增 warning 不阻断 | repoErrors 阻断 |
| T03 | 公共文件白名单与 SHA 一致 | cad338b 用真实差集白名单，4 条全部通过 | 改错一个 SHA 并删掉一条，2 条失败；不给白名单，失败 | 按 git 提交字节算 sha256 | 是 |
| T03b | 本批每个席位包的清单一致（LY-008 `package`） | LY-008 自检 P00、P10 通过 | LY-008 P01–P09：大小、SHA 不符，文件缺失，`..`、绝对路径、反斜杠，含坏 GLB | 包内路径只能是相对路径 | 是 |
| T03c | 城景合同 SHA（city-data.mjs 中的 path/sha 对） | 73/85 一致 | 新增的对只与 CRLF 字节一致，判失败 | 既有 12 条标 inherited（PZ-09），由 LY-100 处理 | 新增的阻断 |
| T11 | **全部**公共 GLB ≤ 15,000,000 B，不管有没有卡片引用 | bce3211：0 个超限，最大 11,954,084 B | 15,000,004 B 判 `GLB_OVER_15000000`（本席位）和 `GLB_OVER_FORMAL_LIMIT`（LY-008 N11）；恰好 15,000,000 B 通过 | 等号算通过 | 是 |
| T16 | 本批触及的每个 GLB 跑 LY-008 `ly_check glb`，exit 0；新 LY_P01 件加 `--profile ly-p01 --lod N` | cad338b 的 4 个 yong-road-link GLB：exit 0 | LY-008 的 46 个负例；把 ly008 证据删掉，判 T16 阻断（dryrun/20261106/gate-cad338b-no-ly008.json） | 证据的 rev 必须等于 CAND | 是 |
| T11b | 本批触及的 GLB 用本席位检查器复核 | 同上 | `negatives/` 下的 14 个夹具：长度、NaN、Inf、索引、无 UV、外链、不是 GLB、私密路径 2 个、凭据、min/max 错、JSON 中的 NaN | 两个检查器的结论不一致时，按 `crosscheck` 的解释表处理，解释不了就阻断 | 是 |
| T12 | 传输承载与 15MB 分开核 | 报告每个改动 GLB 的原始字节数和 base64 字节数 | A1 加 `--upload-limit 15000000 --upload-encoding base64`，判 `UPLOAD_OVER_CHANNEL_LIMIT`（15,938,780）。这个上限是假设值 | 没有真实通道上限就写「未验」，交 LY-010 裁定 | 有真实上限后才判 |
| T05 | 三档没有复制或改名充档（本席位指纹） | 真减面档的几何指纹不同 | selftest 中重新导出的 LOD1，几何相同 | 字节相同，阻断 | 是 |
| T05b | 本批触及的 LOD 组跑 LY-008 `lodset`（LY-007 冻结判据） | granary-city、palace-admission-court-closed：exit 0 | yong-road-link（cad338b）判 `LOD_SAME_GEOMETRY` 和 `LOD_NOT_DECREASING`；不带 waiver 阻断 | LY-007 tri_ratio、bbox；house 族 LOD2 ≤0.10 m 要在 `lodFamily` 中声明 | 是。只有 `lodWaivers` 写明决定人才能放行 |
| T05c | waiver 公示 | 演练夹具（标明不是真实决定）进 warn | — | 卡片上必须写「纹理档」 | 不阻断，但必须出现在报告中 |
| T06 | 原高细近景保留（LY-007 near_view_retention） | 既有 LOD0 和 near 文件的 SHA 不变 | 没有在 `declaredNearChanges` 中声明就改动 LOD0，失败 | 超过 15MB 时不得悄悄降档：原 LOD0 必须保留 | 是 |
| T07 | 压缩件核对**全部属性**的解码结果 | A1：228,112 三角，非有限数 0，非单位法线 0，全属性指纹 `0f952bd7…` | `negatives/meshopt-negatives.json`：视图长度减半、流内翻转、count 加 64 共 3 项，都判 `decode failed`；原样重新打包，判 clean | 三角数、材质数、贴图数不得少于未压缩源或卡片声明；全属性指纹与解码参照一致 | 是 |
| T08 | 部署瘦身（slim_site）后近景不降 | — | — | 需要 gltfpack@1.3.0；没有就写「未验」，交 LY-097 读线上产物 | 按 LY-010 |
| T09 | 新源工程为零 | 官方规则 104 个命中，全部已归档 | selftest 中的 `.blend`、`.zip`、`.part001`、`.psd`；LY-008 T01-source-file | 官方正则加 source-archive 豁免；`.py` 一类宽名单上的新增文件由人工判定（基线 209 个） | 官方规则阻断 |
| T10 | 新私密路径和凭据为零 | 凭据 0；README:145 的 2 处标 inherited | 本席位：extras、generator 里的路径，`ghp_`，`apiKey`；LY-008：节点名、PNG tEXt、用户名（`--private-token`） | 按 (文件, 模式, 匹配串) 去重后与 BASE 比较；凭据只有本席位能查 | 是 |
| T13 | 不新增孤儿 GLB，卡片指向的目标都存在 | 官方孤儿 0；扩展孤儿 1 个，标 inherited | 新增一个没有卡片也没有引用的 GLB，失败 | 扩展规则：没有卡片引用，并且文件名不出现在任何文本里 | 是 |
| T14 | 总载入预算 | 首屏 3,872,084 B、全章 13,466,348 B，都与声明一致 | 声明值与重算不符，失败；超出批次预算，失败 | 原始字节是确定值；gzip6 只是估算；C15 离线判「未验」 | 声明不符阻断；C15 按 LY-010 |
| T15 | 本席位没有动过 lab | before 与 after 逐字节一致（rerun-20261106） | — | HEAD、origin/main、status、__pycache__ 的 mtime | 是 |

## 3 「改前」基线

- `baseline/bce3211/`：11-05 的结果。
- `baseline/rerun-20261106/bce3211/`：11-06 用旧库重跑，八个文件 SHA 逐字节相同，checker 结果只差 generated 时间戳。
- `baseline/rerun-20261106/bce3211-lib2/`：用改严后的库再跑，内容相同，只有 `meta.libSha256` 不同；另附加了全属性 `meshopt-decode.json`。**以后的「改前」对比以这一份为准。**
- `baseline/cad338b/`：漂移对照，只有 blob 部分，没有 checker 重放。

## 4 门禁演练结果（dryrun/20261106/，证明门禁能失败也能通过）

| 输入 | 阻断项 |
|---|---|
| bce3211 → cad338b，真实差集白名单 | T01、T05、T05b |
| 同上，加演练 waiver | T01 |
| 同上，删掉 LY-008 证据 | T01、T16 |
| bce3211 → bce3211，空白名单 | 无（exit 0） |
| bce3211 → bce3211，不给白名单 | T03 |

## 5 还没覆盖的部分

- T01 在 CAND 上的负例要一棵导出树（约 1.8GB），批次到了再做；bce3211 上的负例证据目前用 LY-008 的。
- T08 与 C15：要等 LY-010 定策略，并且需要 gltfpack 或线上读回的产物。
- northern-altar-C 两边几何判定的口径差，有空时对拍 LY-008 的几何哈希定义。
