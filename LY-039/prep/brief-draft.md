# LY-039 开工准备：东北既有约196米 C 路重绑定（brief 草稿，第2版）

状态：**待输入**（开工准备阶段）。本目录只有读取、测量和测试脚本，**没有制作或修改任何交付几何**。

## 第2版改了什么

第2版（2026-11-05 晚）在第1版基础上做了独立复核和补测。

- **南端判断改了。**第1版说「南端没有任何地面」，这只对当前城景成立。同一个已提交的 handoff ZIP 里有旧试放的武库支持片 `C_WUKU_ISOLATED_SUPPORT_PATCH`。它和路短头的端盖**齐平相接**：11/11 探针，高差 0.000，接触面 0.541 m²，没有体积侵入。
- **读了已交付的前置席位。**LY-003、LY-005、LY-006、LY-009 都已交付。按 LY-003 的要求，用实测路面复核了 NE-C-SCREEN。
- **发现 LY-006 的南端端口选错了面。**它冻结的 `end-E` 是路的东侧面，不是接武库的那个面。
- **新增体积侵入检查和负例 N7。**N7 是把路北移 0.10 m。这时接缝探针和连通图都查不出问题，只有体积侵入检查能查出。

## 基线

- 本项基线是 creation-notebook-lab `bce3211f818ee5a8bef1773539da70695ba37b17`，只读。本机 lab 检出的 HEAD 也是 bce3211（分支 lab/site-redesign）。
- 本地 `main` 停在更早的 44c66da。`origin/main` 已经前进到 cad338b，漂移情况见第8节。
- SHA 全部记在 `inputs.json`。
- 文本文件以提交字节为准，因为本机检出有 CRLF 差异。`lab/data/assets.json` 的检出字节在 22:29 被重写过，提交 SHA `53d86312…` 没变。
- GLB 的检出字节和提交字节一致。

## 1. 本项目标（按任务池原文）

复用已有的 `C_NE_APPROACH_LOCAL`，给出它的当前端点、缓坡、接面和可回退安装包。

- **不重造这条路**（锁 LOCK-NE-196C）。
- 不延长成 1.7 公里主干路。
- 不声称历史物流或通行权已经证明。
- 有区域准入才能落城。

## 2. 核到的现有成果

| 成果 | 路径 | SHA256 | 城景是否加载 |
|---|---|---|---|
| 约196米路（唯一实体） | `modeling-lab/review-batches/2026-11-04-city-visible/city-visible-web-handoff-v1-public.zip.part01..05`，**在 bce3211 提交树里**（commit 5ac1ea6 归档）。分卷拼成 zip `5895ef23…`，取其中 `chunks/northeast_C_access.glb` | `58f2f58a464183e20d5489b13902f62f2570573cb8bf96fb237df781027d076e`，413 628 B，与 LY-006/qa/chunks 的副本一致 | **否**。bce3211 和 cad338b 的 city-data.mjs 都没有 NE_APPROACH 或 northeast_C 的引用。adapter.json 标的是 `deploymentStatus: "not published"` |
| 源节点 | 同包 `qa/source-node-manifest.json`（`6cd13e10…`） | 世界平移 (2285.714111, 3486.0, 0)；有向三角 SHA `0f806978…`；32 个三角；材质 `REUSED_C_earth.003` | 只在母版可见集里 |
| 北端地坪（现太仓地坪） | `docs/cities/luoyang/progress-assets/granary-city-v1/granary-city-LOD0.glb`，节点 `original_city_ground_preserved` | `5937211c7366a5920ae222185176f198cc3d16e8763605fa248e61031c74bc93` | **是**。资产 `storage-main` 在 city-data.mjs L582，节点在 L3717，列在 storage 章的 loadNodeIds 里 |
| 南端旧试放支持片 | 同 zip `chunks/wuku_C_with_support-01.glb`，节点 `C_WUKU_ISOLATED_SUPPORT_PATCH`：12 个三角，x 2307.327–2329.327，y 3490–3510，z −0.4–0 | 文件 `29709e25f77f6becaf2566555a4d55b0525e244f73ede92ae344a78cc1a57b37`；节点三角 SHA `1f46fa3e…` | **否**。由 LY-036 处理，不是 LY-039 的资产 |
| 旧仓储组（只作对照） | `docs/cities/luoyang/assets/storage/storage-group-organized.glb` | `b8482824…` | 只有 v1 归档入口加载 |
| 武库 B v2.2 / A v2 | `docs/library/models/m-luoyang-wuku/files/wuku-B-LOD0.glb` 等 | B-LOD0 `e5de60b6…` | 否，用局部原点 |
| 冻结端口（LY-006 registry v1） | `workpacks/LY-006/registry/ports.json`（`28bcfb68…`） | `ne-approach:start:road-end` 在 (2285.714, 0.2, −3647.469)；`ne-approach:end-E:road-end` 在 (2317.827, 0.0, −3487.25)，朝 +X。公差：位置 0.005 m，高程 0.002 m | — |
| 准入（LY-003） | `workpacks/LY-003/tables/admission.json`（`dd0ab8c0…`） | 结论是「宫墙条件未决（不是放行）」，只允许在 NE-C-SCREEN 内做可回退的 C 局部包 | — |
| 「东北长路预检」 | — | — | **哪里都找不到**：lab 的 bce3211、origin/main、origin/luoyang-content 和全部 workpacks 都没有。LY-084 prep 的结论相同 |

## 3. 实测几何（两条独立路径结果一致）

两条测量路径：

- **Blender 导入**：`measure_ne_approach.py`，输出 `out/measure-ne-approach.json`。这是第1版的产物；本版用 check 脚本重跑，结果与原基线逐键一致。
- **裸 GLB 解析，不经 Blender**：`glb_raw_check.py`，输出 `out/glb-raw-check.json`。结果：1 个节点，32 个三角，18 个唯一顶点，1 个材质，3 张内嵌图；x 2284.2141–2317.8269，y 3484.5–3647.469，z −0.18–0.20。

坐标用原生 Z 向上（GLB 内部是 x, z, −y）。

- **形状**：路是一根 3.0 m 宽、0.18 m 厚的 L 形土带。中线分三段，161.469 + 30.613 + 4.0 = **196.08 m**。顶面面积 588.246 m²。
- **缓坡**：北段顶面从 y=3647.469 处的 z=0.200 线性降到 y=3487.5 处的 z=0.000，159.969 m 降 0.20 m，坡度 0.125%。东段和短头都是 z=0.000。每 2 m 取一个断面，都是单一连续截面。
- **北端**：接太仓地坪，位置 y=3647.469，宽 3 m。21 个探针的最大高差是 **1×10⁻⁵ m**，没有缺失。
- **南端有两个面，要分清**：
  - **短头北端盖**：在 y=3490.0，x 2314.827–2317.827，顶面 z=0，朝北。武库 B 点 (2316.327, 3500) 在它北边 10.0 m。旧支持片的南沿正好在 y=3490。
  - **东侧面**：在 x=2317.827，y 3484.5–3490.0，长 5.5 m，朝东，外面是空的。LY-006 的 `end-E` 冻结的就是这个面。
- **城墙**：用 `scan_city_bounds.py` 扫了 124 条带 bounds 的记录，外扩 20 m，结果在 `out/city-bounds-scan-bce3211.json`。包围盒压到路区的城市节点只有 wall-A-wall-01 和 storage-main 本身。wall-01 的实际几何离路 123.5 m。
- **路的周边**：路下面和两侧都没有城市地面，两侧边缘各有 0.18 m 的自由落差。不能写成「两侧可走」。

## 4. 接缝、接触与通行实测

方法是离散网格：0.25 m 一格，向下打射线，腐蚀半径 0.45 m（相当于 0.9 m 宽的身体带），相邻阶差不超过 0.02 m，坡度不超过 8°。**这不是连续人体、车辆、负重或结构的证明。**

射线只取最高的面，所以武库屋顶下面的支持片区域测不到。patch_west 和 patch_east 两个目标显示不可走，就是这个原因。支持片内部的通行交给 LY-036 和 LY-040 测。

| 运行（`out/`） | 北段中点 | 短头端 | 武库侧 (2316.327, 3491) | 北接缝 | 南接缝 |
|---|---|---|---|---|---|
| `bind-baseline.json`（只有太仓地坪；本版重跑，逐键一致） | 通 | 通 | **不通** | 1e-5 m，0 缺 | 11/11 缺 |
| `bind-oldpatch.json`（加上旧支持片） | 通 | 通 | **通** | 1e-5 m，0 缺 | **0 缺，最大高差 0.000** |
| `bind-oldpatch-neg-road-closed.json` | 断 | 断 | 断（起点只能走到 7457 格） | 11 缺 | — |
| `bind-oldpatch-neg-y+0.10.json`（路北移 10 cm，两端都压进去） | 通 | 通 | 通 | 0.0 | 0.0，**探针和连通图都查不出** |

第1版的负例（关路、抬高 5 cm、南移 0.10 m、南移 0.60 m、换 v1 旧仓储组）见第1版的表，结论不变。

**体积侵入检查**：`intrusion_check.py`，输出 `out/intrusion-check.json`。做法是用解析出的路体对两块实测板盒，按 5 cm / 1 cm 体素采样。

| 偏移 | 太仓地坪 | 旧支持片 |
|---|---|---|
| 0 | 合法局部面接触 0.540 m²，侵入 0 | 合法局部面接触 0.541 m²，侵入 0 |
| y +0.10 | **正体积侵入 0.054 m³** | **正体积侵入 0.054 m³** |
| y −0.10 | 分离（有缝） | 分离（有缝） |
| z ±0.05 | 面接触，没有侵入；这类偏移靠接缝高差检出 | 同左 |

结论：连通图、接缝探针、体积侵入这三项检查互相补位，少一项就会漏检。

- N3（小缝）只有接缝探针能查出。
- N7（压入）只有体积侵入检查能查出。

## 5. 准入复核（LY-003 要求本席位用实测几何来做）

用 `ne_screen_check.py` 对路面每 0.25 m 取一个点，共 10 384 个点，结果在 `out/ne-screen-check.json`。

- **10 384 个点全部在 NE-C-SCREEN 内**：都在城垣 B 内，x ≥ 1744.898，y ≥ 2051.020，不在 9 个悬置区里。
- **最紧的是 HZ-Y**（永安宫标签点外扩 400 m）：路离基点 412.87 m，**余量只有 12.87 m**，位置在路的南沿 y=3484.5。
- 其他悬置区余量都很大：
  - 北宫悬置区 HZ-N 余量 340.48 m。按路面算，离旧 B 北宫 540.48 m；第1版按中线算的是 542.1 m。
  - HR-east_north_link 余量 367.73 m。
- 离城墙示意线 127.54 m。
- **这只是 C 筛查**，不证明路在宫外，也不等于准入。LY-003 的结论仍然是「宫墙条件未决」，所以安装包要带 `admission=blocked_pending_palace_wall` 和 `activate=false`。
- **需要更正 LY-003 的一处说法**：它的 ne-checks 写「C_NE_APPROACH_LOCAL 在 bce3211 提交中未找到」。实际上路在 bce3211 提交树的 zip 分卷里，`git ls-tree bce3211` 可以证明；只是不在 docs 树下。

## 6. 改 / 不改范围（草案，依据 LY-006 registry v1）

**所有权**
- LY-039 持有源对象 `C_NE_APPROACH_LOCAL`，模式是 keep，不持有任何城市节点。
- 场地是 S-NE-ROAD，场地负责人是 LY-040。
- 写入区是 `LY-039:write:001/002`，范围就是路本身外扩 0.5 m。

**不改**
- 路的 32 个三角、材质和缓坡。
- 太仓地坪的 12 个三角，指纹必须不变。
- 旧支持片，它归 LY-036。
- 仓址、城墙和武库本体。

**要交**
- 安装包：路节点进城的 overlay 提案，经 LY-100 写入 asset、node 和 storage 章的 loadNodeIds。当前设为 `activate=false`。
- 两端的端口绑定记录：
  - 北端 `ne-approach:start` 绑 `storage-site:forecourt-north`（LY-034）。
  - 南端短头北盖绑 `wuku-B:outer-arrival:ground`（LY-036），以及 `forecourt-side`（LY-037）。
- 撤回清单。
- 与 city-visible 分块层的互斥声明。
- 准入状态字段。

**预计零几何改动**
- 只要 LY-036 交的支持片在 x 2314.827–2317.827、y=3490 处顶面是 z=0.000±0.002 m，路就不用改。现在的旧支持片满足这个条件。
- 不满足时，只能在写入区 002 内改短头端盖的 4 个顶点，也就是 y=3490 那 4 个。超出这个范围就算重造，禁止。

## 7. 证据与未知

- **原文或研究图（B 级示意，不是发掘）**：高崇文 2023 年文章的图1和第50页，给出太仓、武库在东北隅的研究关系（storage-precedents.json 里已读到这一行）。B 点坐标的小数是描点算出来的，不是历史精度。
- **异地异期类比**：密县后士郭的陶仓楼等明器，对道路没有证据作用。
- **C 工程设计**：3 m 宽、0.18 m 厚、0.125% 坡、L 形走线、短头止于 y=3490、旧支持片顶面 z=0，这些全部是 C。
- **未知**：
  - 约180年时太仓与武库之间有没有路，怎么走。
  - 新北宫东墙、南墙的位置。LY-003 的结论是共同控制点为 0，无法配准。
  - 「与太仓标签相邻不证明二者相接」。

**五件事分开记**
- 模型能读取：是，Blender 5.2.1 导入和裸 GLB 解析都通过。Three GLTFLoader **没有测**。
- 局部通行通过：只在离散网格上，而且加上旧支持片后也只到武库侧 1 m 处为止。
- 已入城：否。
- 真实结构安全：没有评估。
- 历史复原成立：否。

## 8. 漂移检查（bce3211 → origin/main cad338b）

- cad338b 增加了雍门接路和北缘三院。三院在 x≈586–647、y≈1222–1246，离本路 2000 m 以上。
- `granary-city-v1/`、`m-luoyang-wuku/` 和 `modeling-lab/` 三处都没有改动。
- 在 cad338b 上重跑 `scan_city_bounds.py`（145 条记录），命中只多了 `north-three` 章节的并集包围盒，没有新的实体。结果在 `out/city-bounds-scan-cad338b.json`。
- 开工时要按 LY-001 的新快照重跑 T0 和 T5。

## 9. 缺项

详见 `inputs.json` 的 `missing`。

- 母版 .blend：几何可以从 GLB 完整重建，生成参数不能。
- 「东北长路预检」。
- LY-034、LY-036、LY-037 的端口值和交付物。
- LY-006 缺短头北盖的端口。
- LY-008 的检查器，以及 LY-010 的区域准入决定。
