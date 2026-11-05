# LY-091 验收测试方案（可执行，v2）

对应本项验收：「门数/旧节点/整门资源与区域状态一致；真实通道、登临、地坪端口和回退均有绑定版本结果，阻断项不放行。」

v2（2026-11-06）相对 v1 的改动：修了三个检查器缺陷（见 brief §4.0），新增 C10（端口）和 C9 的真实实现，自测从 9 例扩到 18 例；绑定的 SHA 改为**提交字节**。

## 0. 重放环境（每批相同）

1. **基线**：批次 manifest 的 `baseCommit`（必须是 LY-001/LY-100 锁定的 main）。不在 `D:/GitHub/creation-notebook-lab` 工作区上验收：那里开着 `core.autocrlf=true`，文本文件的字节和提交字节不同（v1 就是在这里绑错了 SHA）。改用只读导出，这条命令只读 git 对象，不写仓库：
   ```
   git -C D:/GitHub/creation-notebook-lab -c core.autocrlf=false archive <baseCommit> \
       docs/cities/luoyang docs/library/models docs/model-library | tar -x -C <scratch>/ly091-base
   ```
   这三棵子树约 528 MB，已对 bce3211 和 cad338b 各导出过一次。官方 `build_assets.py --check` 要整仓导出，交给 LY-008 的 `source/run_official.py`（它已固定加 `-c core.autocrlf=false` 并逐 blob 核对）。本席位不在仓库里跑它。
2. **候选树**：把基线导出复制成 `<scratch>/ly091-cand`，按批次 `assembly.json` 叠加 overlay，只放 manifest `files` 白名单里的文件。
3. **撤回树**：在候选树上执行该批声明的撤回步骤，得到 `<scratch>/ly091-rollback`。
4. 三棵树各跑一遍：
   ```
   node dump_city.mjs <tree> > <tree>.dump.json
   python -I baseline_ly091.py --lab <tree> --dump <tree>.dump.json --out <tree>.measure.json
   python -I check_region.py --baseline base.measure.json --lab <cand>     --dump <cand>.dump.json --manifest batch.json --out cand.check.json
   python -I check_region.py --baseline base.measure.json --lab <rollback> --dump <rollback>.dump.json --rollback       --out rollback.check.json
   ```
   `base.measure.json` 必须在同一个 `baseCommit` 的导出上现测，不能拿本目录的 bce3211 基线去比别的提交（cad338b 演练证明：换了基线，C2/C3/C9 都会因为别人的合法提交而 FAIL）。
5. 结果文件必须写明：baseline SHA、manifest SHA、候选树 overlay 清单 SHA、脚本 SHA（`inputs.json` 的 `prepArtifacts`）、LY-006 `ports.json` SHA（C10 输出里自带）。

## 1. 每批必跑的检查（check_region.py C1–C10）

测量状态：「区域打开」= 默认载入节点 ∪ walls、yong-gate、terrain 三章的 `nodeIds`，再按渲染器 `rebuild()` 去掉被 `replaces` 的节点。另外单列默认状态（不开章）的地面支持 `groundSupportDefaultState`。

| ID | 检查 | 正例（必须 PASS） | 负例（必须 FAIL，自测已有的标 ✓） | 容差 |
|---|---|---|---|---|
| C1 | 门家族 = 12，缺 0、多 0 | bce3211：12 | ✓ N8：多一张 `m-luoyang-guangyang2-gate` → 13 | 精确 |
| C2 | 未声明替换的旧节点：文件 SHA、节点记录、资产记录（不含 `url`/`nearUrl`）、逐网格几何 SHA、材质名全不变 | ✓ P1 自身；✓ P2 同一树换检出路径 | ✓ N1：wall-05 平移 0.01 m | 精确（几何按 float32 字节哈希） |
| C3 | 新节点都在 `addedNodes` 里声明过，负责任务在 `selected_tasks` 内；区域节点按 chapter 列表**和**节点自身 `chapter` 字段两路收集 | — | ✓ N2：未声明的雍门副本；✓ N9：只靠 `chapter` 字段挂进来的远档副本 | 精确 |
| C4 | 互斥：默认可见（`visibleByDefault`，已扣 `replaces`）的同 SHA 不能出现两次；同一 `exclusiveGroup` 最多一个；旧件和替代件不能同时可见 | bce3211 | ✓ N2、N9 | 精确 |
| C5 | 区域状态一致：实测有门体的门址 = manifest 声明 = 项目卡「件」（墙段 + 门数）；「座」= 12 − 入城门数；门卡 = 12 | bce3211、cad338b：雍+广阳，14 件 / 10 座 | ✓ N4：声明开阳入城，城里没有门体 | 精确 |
| C6 | 本区每个 GLB ≤15,000,000 B，无外链图片，无未解码的压缩扩展，几何值全部有限 | bce3211、cad338b 全过 | ✓ N7：GLB 头长度不符，读取器拒读 | 精确 |
| C7 | manifest `files` 白名单的 SHA 与磁盘一致 | — | ✓ N5：wall-05 SHA 改成全 0 | 精确 |
| C8 | 每个声明的门址：门体存在；0.3 m、1.8 m 两高度最大穿门净宽 ≥ 声明；门道列地面支持 ≥ 声明；声明登临时粗阶梯最大一级 ≤ 声明 | 雍门声明 2.5 m / 0.475 时 PASS | ✓ N3：真正删掉雍门两翼节点后支持不足；✓ N6：雍门声明登临 0.25 m，实测 1.25 m | 宽 ±0.25 m（取样步长）；支持网格 0.5 m |
| C9 | 撤回：撤回树的 inventory（SHA、记录、可见性、几何）、门卡、门址测量、计数、项目卡 SHA（LF 归一）与基线逐项一致 | ✓ P3 自身；✓ bce3211 搬到 scratch 导出后 `--rollback` PASS | ✓ N10：撤回后多留一个节点；✓ N11：撤回后旧墙被设成 `initial:false` | 精确 |
| C10 | 声明的端口：portId 与 version 在 LY-006 `registry/ports.json` 中；world 与登记值的平面差 ≤ position 容差、高差 ≤ elevation 容差；ground/threshold/floor 端口正下方有绘制面，高差 ≤ elevation 容差 | ✓ P4：雍门 3 个门槛端口 | ✓ N12：高程偏 1 cm；✓ N13：不存在的 portId；✓ N14：version 2 | LY-005：position 0.005 m，elevation 0.002 m；world = N·local 残差 ≤1e-6 m |

自测命令（对 bce3211 跑通，`selftest-bce3211.json`，allOk=true，P1–P4 + N1–N14 共 18 例）。它先在快进前的 bce3211 检出上跑过，又在 bce3211 只读导出上重跑，两次输出字节相同。本地检出已被别人快进到 cad338b，以后只用导出：
```
python -I check_region.py --selftest --baseline baseline-bce3211.json --lab <scratch>/ly091-bce3211-export --dump <export>.dump.json --out selftest-bce3211.json
```
换检出路径的实测正例（只读导出到 scratch，`check-relocated-bce3211.json`，PASS-FOR-CLAIMED-SCOPE）：
```
python -I check_region.py --rollback --baseline baseline-bce3211.json --lab <scratch>/ly091-bce3211-export --dump <export>.dump.json --out check-relocated-bce3211.json
```

## 2. 按依赖包的专项重放（交付后，只验 manifest 选中的包）

每项都用该包自己的 `qa/` 脚本在**本项的候选树上**重跑，不采信包内数字；再用本项脚本交叉复测下表关键量。墙缺口一列已和 LY-006 `seams.json` 的 `gateSlots` 对过：LY-006 量墙端帽中心距，得 32.000 m（广阳 8.000 m）；本项量带内顶点，得 31.95–31.97 m（广阳 7.984 m）。本项一律窄 0.016–0.05 m，在 ±0.25 m 取样容差内。

| 包 | 必须重放的正例 | 必须重放的负例 | 本项交叉复测（bce3211 改前值） |
|---|---|---|---|
| LY-015 开阳 | 三档门体 + 接墙件 + 地坪安装；门道、上层路线、撤回；C10 用 `kaiyang-K-v1:passage-{W,C,E}:threshold`、`:outer-apron-edge:road-end` | 关门阻断；去掉接墙件后墙端缺口重现 | 缺口 31.964 m，支持 0/5040，没有门体 |
| LY-017 平城 | 旧路 → 两侧门 → 旧路回路；中门仍阻断；C10 用 `pingcheng-P-v1:passage-{W,E}:threshold` | 关掉旧路必须失败；中门可穿必须失败；`old-ramp:ground` 在 LY-006 还是「仅冻结 ID、数值待补」，数值没补齐前 C10 判 FAIL | 支持 0/5040；docs 门口没有旧路（基线选择交 LY-010） |
| LY-018 谷门 | 墙帽三档、底部支承、门槛地片；撤回 | 帽与母版合并 earth 叠载必须失败（C4） | 缺口 31.964 m，支持 0 |
| LY-019 夏门 | 两翼 + 门槛垫三档；撤回恢复原状 | 叠载 city-visible 适配块必须失败（C4） | 缺口 31.964 m，支持 0 |
| LY-020 转角 | 上东门短转角件只在已测参数域内；原墙身不变（C2） | 超域参数（A arm2 < 2.70 m）必须失败 | 上东门缺口 26.97 m（LY-006 无 midpoint，非对端墙帽） |
| LY-085 城南接路 | 平城、开阳各自从门口到具体路端的支持与连续体积 | 移除接路片后断开；灵台、太学段不计入 | 两门址门外支持 0 |
| LY-089 地形差异片 | 只在认领区内（LY-006 无预分配区，走认领协议）；原地面高程与孔洞不变（C2 对 terrain 节点） | 越出认领范围的片必须失败 | terrain 节点几何 SHA 见基线 inventory |

不在 LY-011–090 任何席位范围内的门址：中东、旄（秏）、小苑、津、上西（LY-006 `gateSlots.siteOwner = null`）。雍、广阳是受保护的现有成果。这 7 处本轮一律写 `NOT_IN_BATCH`，或作 C2 保护对象。

## 3. 登临、通道、地坪端口、三档的判定口径

- 「真实通道」：必须同时满足 ①本项 C8 的离散穿门检查；②包内连续身体包络检查（人体包络、路线、阶差、足下支持在包里写明）；③门叶关闭态负例阻断。只有 ① 不能写「可通行」。
- 「登临」：必须用包内逐段路线（每段有足下支持、转身空间、端点对齐）。本项的粗阶梯指标只做否决：最大一级 >0.25 m 时，不得写登临通过。
- 「地坪端口」：C10 通过，且两侧包用同一 portId/version；端口两侧实际高差逐个写出。LY-005 记录城垣/城门族基底 0.17、地面族 0.20/0.21，有 3–4 cm 系统差，不抹平，只照实列出。
- 「三档」：每个入城门的 LOD0/1/2 都要存在，文件 SHA 与几何 SHA 互不相同，不能把 LOD0 改名充当别档。还要写明城景实际怎么切档。现状：bce3211 不切档。cad338b 的雍门只有两档入城：远档 LOD2 默认可见，近档 LOD0 在开章时替换远档；LOD1 不在城中。所以「区域级三档」仍是 0。
- 「默认可见」与「开章可见」分开报：广阳门门下地面在开 terrain 章时 1200/1200，默认状态 0/1200（bce3211、cad338b 都是这样）。

## 4. 放行规则

- C1–C10 任一 FAIL → 本批城门城垣区 **BLOCK**，回传具体节点、网格、三角范围、端口或门址。
- 未选中的门址写 `NOT_IN_BATCH`，不能写成通过。
- 浏览器/GPU 未测、结构安全未验，属于 010 允许的「待验」，照实列出，不改写成通过。
- 结论写成「本批声明范围内通过」，不写「城门城垣完成」。

## 5. 要绑定的 SHA（bce3211 改前，提交字节）

完整列表见 `inputs.json`：`sha256` 是提交字节，`sha256Worktree` 是本机 autocrlf 检出字节，22 个文本文件两者不同。主要的几个：

- `city-data.mjs` c849706b6210…（工作区 e4115705…），`city-renderer.mjs` 04c6c643e44f…（bce3211 与 cad338b 相同），`p-luoyang.asset.json` 8edb06abf5e7…，`city-wall-interface.json` ca75d115d49d…
- 雍门 LOD0 45743d730f76…，雍门 apron LOD0 e52eaaf514c3…，广阳 gate-body-only cdba2d5c…，direct wall-08 221b8dc8…，wall-09 d4fb5c1c…（GLB 是二进制，两种字节相同）
- G 包 delivery-manifest：LY-001 97e94edc…，002 ccbf4b2c…，005 642c07f0…，006 230777d4…，007 8100f197…，008 6ac4a4f9…，009 637e02b0…；LY-006 `ports.json` 28bcfb68…、`seams.json` ca4d81f8…；LY-008 `ly_check.py` 39aaa491…
- 区域节点几何指纹：`baseline-bce3211.json` 的 `inventory[].meshNodes[].geomSha256`
