# LY-091 城门城垣区域验收 · 开工准备草稿 v2（G 未冻结）

状态：**待输入**。本目录只有验收方案、检查脚本，以及对当前 main 的「改前」基线和一次 origin/main 漂移演练。没有制作或修改任何交付几何，没有写仓库，也没有运行 `build_assets.py`。

v2（2026-11-06）为什么重写：重放 v1 时，我在 origin/main（cad338b）上做了一次漂移演练，暴露出 v1 检查器的三个缺陷和一处 SHA 绑错（§4.0）。都已修好并补了负例。改后对 bce3211 的门址测量与 v1 逐字段相同，说明 v1 的数字本身没错，错的是比较层。

## 1. 本项目标

独立验收城门城垣一区的候选批次：区域级三档装配、接墙接地、出入与登临、撤回、旧节点不变。只验已放行（交付完成、带 SHA）的候选包。文件能打开不算入城；门家族总数始终 12，版本与附件不加门数。

依赖：G（LY-001/002/005/006/007/008/009/010）+ LY-015、017、018、019、020、085、089。按任务池「按批次求依赖闭包」，每批只验本批 `selected_tasks` 及其硬前置。未纳入的门记为「本批未纳入」，不是「已通过」。

## 2. 基线与现有成果

- **本地检出在本次运行中途被别人快进了**：reflog 显示 `2026-11-06 00:34:10 merge origin/main: Fast-forward`，HEAD 从 bce3211 变成 cad338b。本席位没有执行任何 git 写操作。改前基线（00:28 生成，`head` 字段为 bce3211）和自测（00:32）都在快进之前跑完；`inputs.json` 第一次重生成落在快进之后（00:37），读到了 cad338b，已作废。v2.1 的 `make_inputs.py` 改为只读 bce3211 的 git 对象，不再读工作区，并核对过全部 GLB SHA 与基线测量值一致。之后的复现一律在 bce3211 只读导出上跑（§3）。
- 仓库 `D:/GitHub/creation-notebook-lab`：本次开工时本地 HEAD = `bce3211f818ee5a8bef1773539da70695ba37b17`，`docs/` 与 HEAD 一致；本次 `git status` 只有 `.claude/` 未跟踪（v1 记下的 `lab/data` 三个改动已经不在了，LY-006 也记到「被别处还原」）。仓库开着 `core.autocrlf=true`。
- **origin/main 已前进 3 个提交到 `cad338b`**：f28d650 雍门接路（r2026.11.05-6）、b70c495 接路并入门附件（-7）、cad338b 北三院（-8）。前两个改了本区雍门节点。这是雍门接街原负责人的受保护成果，本项只读、不验收、不代做。LY-005 也记下了这次前进，并请 LY-100/协调者决定 G 以哪个提交为准。
- G 现状：LY-001、002、005、006、007、008、009 都已「交付完成」，各有 delivery-manifest。**LY-010 目录不存在**，所以 G 没有冻结，也就没有区域准入，也没定基线是 docs 城景还是母版 1e8c4d 的 city-visible 交接。
- 依赖包：015/017/018/019/020/085/089 都只有 prep（全部有 prep-status），没有 delivery-manifest。
- 城景加载链：`index.html` → `app.mjs:1` 导入 `city-data.mjs` → `app.mjs:177` 动态导入 `city-renderer.mjs`。默认载入 `city-renderer.mjs:221`（`initial !== false`）；近档 `:289/:293`（`nearUrl`）；`rebuild()` 在 `:409–:416` 去掉被 `replaces` 的节点。v1 档案页走 `v1/wall-layer.mjs:20`，硬查 A=13 / B=12。
- 已有区域成果：雍门 yong-city-v1 已入城，自报墙端残差 7.59e-05 m；本项复测 ≤7e-05 m。cad338b 上它又被接路与远近档改造过。它在本项里是「旧节点不变」的保护对象，不是本项成果。
- **没有现成的城门城垣「区域验收报告」**，复用判定为「无」。

## 3. 改前基线（bce3211，实测）

命令（全部只读；导出用 `git archive`，不建 worktree）。本地检出已是 cad338b，所以复现**必须**用 bce3211 导出：
```
git -C D:/GitHub/creation-notebook-lab -c core.autocrlf=false archive bce3211 docs/cities/luoyang docs/library/models docs/model-library | tar -x -C <scratch>/ly091-bce3211-export
node dump_city.mjs <export> > <export>.dump.json
python -I baseline_ly091.py --lab <export> --dump <export>.dump.json --out baseline.json
python -I check_region.py --selftest --baseline baseline-bce3211.json --lab <export> --dump <export>.dump.json --out selftest.json
python -I make_inputs.py D:/GitHub/creation-notebook-lab bce3211f818ee5a8bef1773539da70695ba37b17
```
复现结果：
- 本目录的 `baseline-bce3211.json` 是快进前在 bce3211 检出上测的，同一输入连跑两次字节相同。
- 在 bce3211 导出上重测：门址、门卡、计数、几何指纹逐字段相同。只有环境字段不同：`lab`、`head`、`gitBlobAtHead`（导出里没有 git，为空），以及 CRLF 原字节的 `projectCardSha256Raw`。LF 归一后的 `projectCardSha256` 相同。
- 在导出上重跑自测，结果与 `selftest-bce3211.json` 字节相同。
- v1 的基线与自测改版前也在原输入上字节级复现过一次（692964ac…、45b88fe7…）。

方法：纯 numpy 读 GLB，拒读压缩和长度不符的文件，按城景矩阵转世界坐标。门址取 `city-wall-constraints.json` 中 12 个 B 点的 C 投影，只当取样中心。墙切线用 70 m 内墙顶点做 PCA。地面支持用 0.5 m 网格向下取样，只取 y<1.0 的面。穿门检测在 0.3 m 和 1.8 m 两个高度、每 0.25 m 一条横穿墙的线段。登临只做粗阶梯指标。这些都是**表面检测和离散取样，不是连续人体包络，也不是实体碰撞穷尽**。

**门数与状态**
- 门卡 12 张，缺 0、多 0。
- 三档齐全的 6 张：上西、雍、津、小苑、平城、开阳。只有 LOD1/LOD2 的 5 张：夏、谷、广阳 A-v2、上东、中东。旄门只有 LOD0/LOD1。最大单文件 2,140,916 B（旄门 LOD0），全部 ≤15,000,000 B。
- 城中有门体的门址 2 处：雍门、广阳门。项目卡「城垣与两座城门」14 件 = 12 段墙 + 2 门；「城门研究」10 座 = 12 − 2，自洽。cad338b 上同样自洽。
- 研究模型 6 个（开阳、平城、上西、雍、中东、旄），按需在独立空间打开，不入城。

**12 处门址**（u 沿墙，v 横穿墙；网格 0.5 m，穿门取样 0.25 m，宽度误差 ±0.25 m）

| 门址 | 墙缺口宽（LY-006 帽距） | 城中门体 | 地面支持：开章 / 默认 | 穿门净宽 0.3/1.8 m | 墙端接缝残差 | 登临最大一级 |
|---|---|---|---|---|---|---|
| 雍门 | 31.950（32.0） | 门体 + 两翼 | 2148 / 2148 of 5040（42.6%）；门道列 760/1600 = 47.5%；\|v\|>9.75 m 两侧各缺 10.5 m | 2.75 / 4.00 / 2.75 | ≤0.00007 m | 1.25 m（没有梯段） |
| 广阳门 | 7.984（8.0） | `gate-body-only`，y 6.2–10.3，骑在墙顶 | **1200 / 0** of 1200：只有开 terrain 章才有地面 | 一洞 7.75，没有门叶 | 顶面接触 0；切口侧壁露出至 6.08 m | 5.99 m（没有） |
| 夏、谷、上西、中东、旄（秏）、津、小苑、平城、开阳 | 31.96–31.97（32.0） | 无 | 0 / 0 of 5040 | 31.75（空缺口） | — | 6.03 m |
| 上东门 | 26.97（LY-006 无值，非对端帽） | 无 | 0 / 0 of 4240 | 26.75 | — | 6.03 m |

## 4. 实测到的真实缺口

### 4.0 本项检查器自身的缺口（v1 → v2 已修）

用 `git -c core.autocrlf=false archive cad338b …` 只读导出到 scratch，对 bce3211 基线重放，得到以下结果：

1. **C2 假阳性**：v1 把资产记录里的 `url` 一起哈希了。`url` 是 `city-data.mjs` 按 `import.meta.url` 解析出的绝对 `file://` 路径，于是**任何换路径的重放都会让全部 19 个区域与地面节点（13 墙 + 2 雍门 + 4 地面）C2 FAIL**，墙一字未改也一样。v1 自测始终在同一路径上跑，所以没发现。v2 哈希时去掉 `url`/`nearUrl`，并加了正例 P2（改检出路径）。把 bce3211 实际导出到 scratch 后跑 `--rollback`，结果 PASS（`check-relocated-bce3211.json`）。
2. **漏收区域节点**：cad338b 的 `yong-gate-body-far`、`yong-gate-interface-far` 字段写 `chapter: walls`，却不在 walls 章的 `nodeIds` 里，而且默认可见。v1 只按章列表收集，这两个默认可见的门体远档会被漏掉。v2 两路收集，并加了负例 N9。
3. **没按渲染器的 `replaces` 计算**：v1 把所有节点都当成画出来了，也没区分默认状态和开章状态。v2 模仿 `rebuild()` 扣掉被替换的节点，并单列 `groundSupportDefaultState`。
4. **SHA 绑错**：v1 的 `inputs.json` 给全部 22 个文本文件（city-data、renderer、项目卡、wall-interface 等）记的是 autocrlf 检出字节，不是提交字节；LY-001 C8 报的也是同一个坑。v2 的 `sha256` 改成提交字节（`git cat-file blob`），检出字节另记为 `sha256Worktree`；项目卡哈希先做 LF 归一。
5. **v1 的 N3 负例不成立**：v1 只把雍门两翼从章列表里删掉，但该节点 `initial:true`，渲染器照样会画。v2 改成删除节点本身。
6. **C9 原来只是注释**，v2 实现了，带正例 P3、负例 N10/N11。**C10 端口检查**是新增的，带 P4、N12–N14，读 LY-006 `ports.json`，容差用 LY-005 的值。

自测：18 例全部符合预期（v1 是 9 例）。

### 4.1 城门城垣区的缺口（bce3211）

1. 10 处门址在城中只有约 32 m 的墙缺口，地面支持 0，没有门体。开阳、平城、谷、夏、上东对应 015/017/018/019/020，都还没交付。另外 5 处（中东、旄、小苑、津、上西）在 LY-006 `gateSlots` 里 `siteOwner = null`，**本轮没有任何席位负责**，每批都只能写 `NOT_IN_BATCH`。
2. 雍门：门道列地面只覆盖 \|v\|≤9.75 m，两侧各缺 10.5 m；没有登临（粗阶梯最大一级 1.25 m）。
3. 广阳门：默认城景里门下地面 0/1200；没有门叶，没有登临。LY-005 另测出 direct 墙 08/09 墙脚比地面低 1.33 cm。
4. 城中任何门都没有三档。
5. `city-wall-interface.json` 的 `gateProjections` 指向的 `qa/gate-projections.json` 不在 docs 里，本项改用 constraints 里的 `gate_projection_diagnostics`。
6. 旋门/旄门：已由 LY-002 D-01 解决。`gate_xuan_B` 应为「秏门（旄、耗异写）」，「旋门」是成皋关隘名，属误读。本项对旄门卡的映射成立，证据层改名交 LY-100。

### 4.2 origin/main 漂移（cad338b，`drift-cad338b.json`，只读演练，不是验收）

- 12 段墙与广阳门：文件、几何、节点记录全不变。
- 雍门：门体与两翼节点改为 `initial:false` 且 `replaces` 远档；新增 5 个节点（`yong-gate-body-far`、`yong-gate-interface-far`、`yong-road-link`、`yong-road-link-near`、`yong-road-receiver`）。城中雍门变成**两档**：远档 LOD2 默认可见（58,612 B / 788 三角），开章换成 LOD0（1,570,856 B / 8,228 三角）。LOD1 不在城中，区域级三档仍为 0。
- 雍门地面支持 2148 → 2274 / 5040；门道列 0.475 → 0.5537。但 \|v\|>9.75 m 两侧仍各有 10.5 m 是不连续支持：接路片只有约 3 m 宽，只覆盖一部分门道列。穿门净宽不变。
- `ground-retained` 改为默认载入，广阳门默认地面仍是 0/1200。
- 对 bce3211 基线：C2/C3/C9 FAIL，C1/C4/C5/C6 PASS。这只说明 cad338b 不等于 bce3211，结论是**下一批必须在锁定的新 main 上重测基线**，不能拿本目录的 bce3211 基线去比。

## 5. 改 / 不改范围

- 改：只写 `workpacks/LY-091/`；重放导出放 scratch。
- 不改：城景、项目卡、资产卡、任何 GLB、`city-wall-interface.json`、构建数据、其他席位目录；不在仓库里运行 `build_assets.py`。
- 不验：真实浏览器/GPU（LY-097）、全城碰撞（LY-095）、预算总检（LY-096）、史证终审（LY-098）。本项结论只引用它们的结果。

## 6. 证据与未知

- 原始考古/原文：门名与相对方位（雍门 source.json 引《后汉书·百官志》注；十二门表、秏门异写见 LY-002 `tables/evidence-ledger.json`）。有据的只是门名和方位，门楼、楼层、门叶、楼梯都**没有**。
- 异地异期类比：一门三道、门楼两重百尺属北魏实证（LY-002），不能前推为约 180 年的东汉形制；《水经注》北魏迁门记载只作回溯。
- C 工程设计：全部墙体参数、门址 C 投影、雍门两翼与接路、广阳 direct 接合、所有地面高程（0.17 / 0.20 / 0.21，LY-005）。
- 未知：12 门实际门宽、洞数、门址精确坐标；平城门约 180 年是否修复（177/178 年有损坏记载）；地理原点与绝对高程。
- 五件事分开记：模型能读取（12 卡 GLB 全可读）/ 局部通行通过（只有雍、广阳两处的离散穿门线段无遮挡）/ 已入城（2 门）/ 真实结构安全（未验，不验）/ 历史复原成立（未证）。

## 7. 下一步（G 冻结后）

1. 取 LY-010 的区域准入与基线选择，以及 LY-001/LY-100 锁定的 main（bce3211、cad338b 或更新），用 `git archive` 导出，重跑 `dump_city.mjs`、`baseline_ly091.py`、自测，得到新基线。
2. 每拿到一份批次 manifest，按 test-plan 跑：安装 → C1–C10 → 撤回 → `--rollback`。端口用 LY-006 registry，容差用 LY-005。
3. 包内连续通行、登临与关门负例，在本项候选树上重跑，不采信包内数字。

## 8. 本目录产物 SHA256

`*.v1-superseded.json` 是 v1 的旧基线和旧自测，只为追溯而保留，不再使用。

| 文件 | SHA256 |
|---|---|
| `baseline-bce3211.json` | bcd6296996f19d4b1405b254cd9917f0d5b6708af7db9b616a92f434b8fd462e |
| `selftest-bce3211.json` | be791e0741e6d2e322aaf35dbfba7e8125edd4cc02ec2362bc085244024e3f7d |
| `check-relocated-bce3211.json` | 2f068aefd1300c6c8e8455eef90e739196d103e0b9015d2b877ef1a5cf86d8d1 |
| `drift-cad338b.json` | 656c5dd5de187ba9c2b7c6ba7c27cc651c8b1275b8f908ec286b55428f0b0f31 |
| `_city-dump.json` | bc854f1f05d85816d8a3eebd0f5820d4a0475ed59419313ef9cbb141e75f6938 |
| `inputs.json` | 63194148e26b36674e02c8f342d3db75095ea6c65fe3fa9e97bb7174dfa9e9ab |
| `test-plan.md` | 5602a841ef10ca87abab30812cc183592af51c78c399c5c7817bebc67e51ebf5 |
| `prep-status.json` | 92ae668930070d10e3e1935e06b14e6db98b3ac0ecf2bcdacce1dd0f61126873 |
| `glbread.py` | b9c873fe350b52836be0abbd6baff6861d0ab4a72128807870f14ca26818029c |
| `baseline_ly091.py` | b63ea18de9bf0c39baef55a00f84dc215dc92df81b5e19162350f49dc647277d |
| `check_region.py` | e8d4a8623b42022006ffafb57ff0fb55c0a30b0ab7e11054f88975f3a66b611b |
| `dump_city.mjs` | 137fa6a8bdf019adb15bca2511c259c3a397650aaed6472751413c4beceef886 |
| `make_inputs.py` | 4061fde9ef9aefd11725336466d4dc2edb39e47623582d255a7df4ae99aaea51 |
| `baseline-bce3211.v1-superseded.json` | 692964ac1747cd22649aae61823bba1dd79823b240b5a422ebf2956b17fc95ba |
| `selftest-bce3211.v1-superseded.json` | 45b88fe76ece480a2a096e7afb7782834a0f256fd4536016fa731b819f0bad91 |
