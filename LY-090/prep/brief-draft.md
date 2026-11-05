# LY-090 多地坪开孔与替换合成器 · 开工准备草案（prep）

状态：**待输入**。G（LY-001/002/005/006/007/008/009/010）没有冻结，前置席位 LY-025/045/053/086/089 也都还没交付。本目录只读输入、实测缺口、准备测试，**没有制作或修改任何交付几何**。测试夹具只是对现有 GLB 做只读组合和平移，不输出新模型。
基线：creation-notebook-lab 本地 main `bce3211f818ee5a8bef1773539da70695ba37b17`，只读。2026-11-05 首测时 lab 工作区有 3 个改动文件（lab/data/*.json），2026-11-06 复测时只剩未跟踪的 `.claude/`，都不是本席位造成的，本席位输入不在其中；inputs.json 同时记了 HEAD blob。
**基线漂移**：origin/main 已到 `cad338ba683f7277aea098f45c8feb6c915a847c`（f28d650 → b70c495 → cad338b，32 个文件）。本席位的输入里只有 `city-data.mjs` 变了（bce3211 e4115705… → cad338b d8933a32…）：五个宿主资产块（第 425–560 行）逐字相同，节点记录行号后移（market-main 节点 3663 → 3894，ground-* 3555… → 3783…），`ground-retained` 改为默认加载（initial:true）。所有 GLB 和加载器代码都没变。开工时以 LY-001 冻结的快照为准重跑 `sh scripts/run_prep.sh`。
测量日期 2026-11-05 首测，2026-11-06 全套复跑（8 项输出中原有 6 项逐字节相同），并新增 §5.13–5.15。Python 3.11 + numpy 2.4.6，CPU。

## 1. 本项目标（按任务池原文）

把井、厕、窑、水道这几项**互不重叠**的局部切孔计划，合成**一个可逆的地坪差异包**，作为唯一输出：

- 各代理不抢写同一个地面文件；
- 后一个补丁不能把前一个孔封回去；
- 先后顺序要么可交换，要么明确固定；所有已有的孔都保持开放；
- 任一补丁失败，整组还原。

合成器是**复用装配**：孔的形状、井、窑坑、厕和水道本体都由前置席位负责，本席位不造新的建筑家族。

## 2. 核到的现有成果（只读；完整 SHA256 见 inputs.json）

| 成果 | 路径 | SHA256（前 16 位） | 在城景里 |
|---|---|---|---|
| 市肆主件，含宿主地坪 `sample_ground` | docs/cities/luoyang/assets/market/market-cluster.glb | 77b8bf2e9e1488df | 已加载：city-data.mjs:511/3663；v1/west-layer.mjs:33 |
| N2 替换件 | …/market/N2-replacement.glb | d33cbad1ea14e943 | 已加载 |
| 流线 B 路带 | …/market/flowB-routes.glb | 43d7799f85feccb0 | v1 flow=B |
| 原子地面四片 | …/ground-atomic/{network-ground-stitched, retained, south, D08}.glb | fdfc3ce5… / aed8b3d4… / 4313826d… / 3ab93310… | 已加载：city-data.mjs:431–509、3555–3660；v1/west-layer.mjs:35 |
| 原子地面契约 | data/west/ground-atomic-contract.json | bfc7fc83c3d8f34c | v1 校验：west-layer.mjs:40、road-layer.mjs:19 |
| **唯一现成的开孔地面** `C_market_ground_well_A` | workpacks/LY-025/prep/work/market_frontage_well_routes.glb（LY-025 从 city-visible ZIP 抽出） | 0193ebc0cfe20029 | **未加载** |
| 井 A 两档 | docs/model-library/well-study/assets/well-A-LOD{0,1}.glb | 6bc463f8… / e9252de3… | 未加载 |
| 圈厕 A 三档 | docs/library/models/m-luoyang-service-court/files/service-A-LOD{0,1,2}.glb | cc02f68f… / 366e1a26… / c88104ce… | 未加载 |
| 砖瓦窑 A/B 两档 | docs/library/models/m-luoyang-tile-kiln/files/kiln-{A,B}{,-LOD1}.glb | e67d5976… / 4886d95d… / 562b4b39… / 8d9db85b… | 未加载 |
| 宫墙水道四件 | docs/library/models/m-luoyang-palace-waterway-interface/files/*.glb | 79d36565… / 68ec04bb… / af5e8b65… / f90094d2… | 未加载 |

**城景里没有任何开孔或切地形机制。** 加载器只有三种手段：
1. `excludeNodes`：按资产整节点排除，且要求全部命中（city-renderer.mjs:309/346）；
2. `node.replaces`：节点级替换（city-renderer.mjs:409–413，现在没有任何节点在用）；
3. v1 的 `retire`：把节点移出，计数写死为 30 和 7（v1/market-assembly.mjs:5）。v1 的环境 GLB 整个载入，不支持排除（v1/r01-assets.mjs:5）。

## 3. 改 / 不改范围（草案，待 LY-006 冻结）

**要做（G 冻结、前置交付后）**
- 合成规则：每个宿主地坪节点**只出一个替换件**，从**原始基底（绑定 SHA）一次性**减去所有被接纳孔的并集，不链式叠补丁。
- 交付 `assembly.json`：宿主节点 → 替换节点、孔清单（owner、中心、多边形、深度、通孔/凹槽）、绑定的输入 SHA、安装顺序、互斥与撤回规则。
- 交付 `models/`：只放宿主地坪替换件。目前唯一有世界位置的孔是井，所以第一批的替换件就是 `sample_ground` 的开孔版，直接复用 LY-025 的 `C_market_ground_well_A`，不重切。
- 交付 `qa/`：hole_check 的正例和负例（见 test-plan.md）、两个加载口径的安装与撤回、单补丁故障注入后的整组回退。
- 给 LY-100 的语义合并提案：city-data `market-main.excludeNodes` 从 30 项改为 31 项，或改用 `replaces`；v1 的 retire 规则也要相应改。

**不做**
- 不造井筒、窑坑壁/坑底、厕坑、水道本体或墙块（分别属于 025/053/045/086），也不做补洞片（089）。
- 不决定任何孔的位置；不铺路（022/082/083）。
- 不写 city-data.mjs、p-luoyang.asset.json、city-renderer.mjs、v1/*.mjs 或原子地面契约。
- 不认证排水、承载、卫生、热工或 GPU 效果。

## 4. 证据与未知（四类）

- **原始考古 / 原文**：没有一个孔位有原始依据。水道卡片写的是「据考古网署名…转载纪要，原发布不可读」，只支持「东汉、青砖、三部分」，尺寸未知。
- **异地异期类比**：圈厕依据跨地域明器类型（卡片原文）；井依据灵宝张湾等同期异地陶井（LY-025 已整理）。
- **C 工程设计**：所有孔的尺寸、深度，以及井的试放点（市肆局部 −18, +7）；合成规则本身也是 C 工程设计。
- **未知**：窑、厕、水道在城里的位置（city-data 里没有任何落位；LY-045 prep 给了一个厕的候选位 C02-010，没有准入）；厕坑要不要挖、挖多深（LY-045 原文就要求「未知坑深保持未定」）；水道的地面基准（LY-086：0.76、1.80 或其他，都没有依据）。
- **证据冲突**：data/west/market-precedents.json 的 proposal.avoid 写着要避免「因名市井而强加水井」。所以井孔只能标 C 试放，要 LY-002/010 给准入。

五件事分开说：
- GLB 能读取：已实测。
- 局部开孔通过：只有井孔在夹具里通过，见 §5.6。
- 已入城：**否**。
- 结构安全：未验。
- 历史复原成立：**否**。

## 5. 实测缺口（脚本在 scripts/，输出在 out/；一键复跑：`sh scripts/run_prep.sh`）

1. **四项计划的切地需求差别很大**（cut_plans.py → out/cut-plans.json。0.05 m 网格；模型基准面 y=0；去掉各自的展示或演示地坪后测）：
   - 井 A：伸到基准面下 **0.65 m**，填实足迹 **1.10 m²**（LOD1 是 1.08 m²），外半径 0.59 m。
   - 窑 A：基准面下 **1.04 m**，足迹 **37.22 m²**，x −2.2…2.2、z −4.6…5.3；窑 B：37.04 m²，x ±2.5、z −3.9…4.7。LOD0 和 LOD1 足迹一致。
   - 水道（四件都一样）：基准面下 **0.18 m**，足迹 **7.35 m²**，x ±3.3、z ±0.759。
   - **圈厕 A 三档都是 0**：基准面以下没有任何几何。高台厕的孔开在自己 1.40 m 高的楼板上（LY-045 实测孔 0.42×0.40 m）；圈内没有自己的地面，要靠宿主地坪托底。所以厕现在**不产生地坪切孔**；要不要加坑，等 LY-045 冻结。
2. **宿主地坪都是 0.20 m 厚的封闭板**（plate_thickness.py → out/plate-thickness.txt）：sample_ground、retained、south、D08 的竖向射线都只打中 y=0.2 和 0.0 两个面；stitched 是 0.21 和 0.0。地坪下面什么都没有。所以：
   - 井（0.65 m）和窑（1.04 m）是**通孔**：切穿以后坑壁和坑底必须由 025/053 自己带，否则孔下直接看到背景。
   - 水道如果按地面顶 0.2 对齐，0.18 m 只是**凹槽**，槽底只剩 **0.02 m** 薄板，有近共面风险。这取决于 LY-005 把基准对齐到哪里。
   - 库件基准 y=0，城里地面顶在 0.2，所以落位要 +0.2。LY-025 的井试放就是平移了 +0.2。
3. **只有井有世界位置（城里也只是 C 试放）**：窑、厕、水道在 city-data 里都没有落位。2026-11-06 复测时，LY-045 prep 新给了一个厕孔候选位（C02-010，未准入），见 §5.14：与井不同宿主、相距 1,186.8 m。窑和水道仍没有任何坐标。所以「多孔合成」眼下最多是 2 个宿主各 1 个孔，同一宿主上需要做不重叠测试的孔对是 **0 对**。其余几项进来要等 LY-010 给准入、LY-005 给坐标。
4. **井位下的地层只有一层**（ground_stack.py → out/ground-stack.json）：井心周围 r≤0.59 和 r≤1.5 的 16 方位射线，只打中 `market-main:sample_ground`（0.2 和 0.0 两个面）。四片原子地面在市肆足迹里一个三角面都没有。
5. **市肆地面是叠层的**：60×44 m 足迹按 0.5 m 网格取 10,560 格，app 口径有 **4,616 格**（43.7%）有两层以上可走顶面，v1 flow=B 口径（7 条 route_* 已 retire）有 **4,680 格**。叠层的是 route_*（0.2→0.21，0.01 m 厚的板）、flowB_*、各铺 floor（0.21–0.39）和 boundary，全都压在 sample_ground 上。所以落在路带上的孔要**同时切 2–3 个文件的节点**：market-cluster 的 route_*、flowB-routes 的 flowB_*、sample_ground。这就是「多地坪」的实际含义。井孔现在不在任何路带下面：离 route_public 5.0 m，离 route_rearS 8.0 m（LY-025 实测）。
6. **合成顺序会改变结果**（hole_check.py → out/hole-check.json；夹具 tests/hole-check-config.json。孔内 129 条射线必须什么都不打中；孔外 96 条射线的最高面必须在 0.2±0.011）：
   - S0 当前 main：孔内 **129/129 被 sample_ground 堵住**，判 FAIL，符合预期。
   - S1 用 C_market_ground_well_A 换掉 sample_ground：0 堵、0 失托，PASS。
   - S2 先开孔、再叠一个从旧基底做出来的整片补丁：**129/129 被封回**，FAIL。
   - S3 同 S2，但补丁写明 `replaces`：同样封回，FAIL。
   - S4 把顺序反过来（旧补丁在前、开孔在后）：PASS。
   - S5 一块铺装从上面盖住孔（route_rearS 夹具平移 −10 m）：129/129 被盖，FAIL。
   - S6 开孔地面被二次平移 +0.2 m：96/96 外圈失托，FAIL。
   - S7 v1 flowB 口径加孔：PASS。

   8/8 都符合预期。S2 和 S4 说明：「后写者覆盖」的规则下，**顺序不能交换**。合成器必须从基底一次合并，不能链式叠补丁。
7. **开孔多边形是内接的 48 边形**（hole_polygon.py → out/well-hole-polygon.json）：孔圈 r = 0.58996–0.59004 m，48 段，弦高 **1.263 mm**。井筒外壁是真圆 r=0.59（LOD0 和 LOD1 都是），所以每条边的中段井筒会伸进地坪最多 1.26 mm。LY-025 测到的 2.655e-6 m³ 薄片就是这个原因。合成时孔应外接，r ≥ **0.59131 m**；否则这处交体要逐对归类为局部嵌接，不能整体豁免。
8. **宿主节点很大，换一个节点就要换整片**（host_inventory.py → out/hosts.json）：
   - `south:single_closed_terrain_after` 96,796 tri，整个文件 2,623,560 B；
   - `stitched:C_stitch_west` 127,544 tri（文件 3,565,544 B）；
   - `retained:C02_…` 21,192 tri（629,740 B）；
   - `D08_shared_terrain` 140 tri；
   - `sample_ground` 12 tri。

   将来厕坑或窑坑落到原子地面上，就要整节点替换。体积都在 15,000,000 B 以内，但城市清单和原子地面契约里绑的 SHA 会全部改变（ground-atomic-contract.json 的 keep 段写死了 retained、south、D08 的 SHA），只能由 LY-100 改。
9. **原子契约挡着节点替换**：`assertGroundAtomic` 要求 C_stitch_primary、C_stitch_west、C_stitch_patch 各恰好出现一次。所以 stitched 的开孔版必须**同名原位替换**，或者修改契约。
   - app 口径：excludeNodes 是全命中校验，市肆现在 30 项，加上 sample_ground 是 31 项；
   - v1 口径：环境不支持排除，retire 计数写死。两边都只能写提案交 LY-100。
10. **院落原型是多处实例共用的**：A 12 处、B 10、A2 9、B2 7、TC03 4、TC03-2 2，共 44 处。excludeNodes 按资产生效，排一个就是同时排所有实例。院落自己的 site_lot、site_neutral_lane、designed_* 已经全部排除，44 院的可见地面就是原子地面：22 院在 retained、14 院在 south、8 院在 D08（按原点射线测）。所以**单院的孔只能切在原子地面上**，不能切在院落原型里。
11. **原子地面之间不叠层**：retained 外框内按 2 m 网格取 41,250 格、西缝按 1 m 网格取 12,900 格，两层以上顶面的格数都是 **0**。四片是拼接关系，一个孔只会落在一片原子地面上（拼缝处除外，那里要单独测）。
12. **回退机制已有基础**：city-renderer `rebuild` 用 Promise.all，任一资产失败都不替换旧场景；v1 在 catch 里调用 destroyDistrictAssets。这些只读了代码，还没做故障注入。

13. **水道的切孔计划取决于还没冻结的地面基准**（datum_pairs.py → out/datum-pairs.json；near 档，0.05 m 网格竖向射线；宿主板厚按实测 0.20 m）。LY-086 prep 已经指出水道原点在渠底，地面在哪一档没有元数据。按四个候选板顶高程测「几何穿过板厚带 [顶−0.20, 顶] 的面积」和「整列都在板底以下的面积」：
   - 板顶 = 0.00（库件原点，即 §5.1 的口径）：板带内 **7.35 m²**，切深 0.18 m，凹槽；
   - 板顶 = 0.60（盖板底）或 0.76（盖板顶）：板带内 **6.54 m²**，另有 **0.81 m²**（竖井净口 0.90×0.90）整列在板底以下，切深 0.78 / 0.94 m，变成通孔；
   - 板顶 = 1.80（井口平地面）：板带内只剩竖井外壁一圈 **1.44 m²**，加净口 0.81 m² 共约 1.52×1.52 m（与 LY-086 提的 1.518×1.518 外框相符）；**5.91 m²** 的渠身整体埋在板底以下，而宿主板下面是空的，城里没有任何东西包住它。
   所以 LY-086 交给本席位的切孔计划必须同时写明基准高程；1.80 方案孔小，但「埋在空心板下的渠身」本身就是一个缺口，要由 LY-086/LY-005 决定是否需要土体，本席位不补。
14. **两个有（候选）世界坐标的孔不同宿主、相距很远**（datum_pairs.py §B；rect_tri_sat.py → out/privy-rect-tris.txt）：
   - 井 A（LY-025 试放）：宿主只有 `market-main:sample_ground`，孔内 0.005 m 采样碰到 **2 个**三角（12 个中；板顶 0.2、板底 0.0 各 1 个）；
   - 厕孔（LY-045 候选位 C02-010 rot0，孔矩形 x 533.59–534.01、z −814.62…−814.20）：宿主只有 `ground-south`，精确分离轴法和采样法都是 **4 个**三角（96,796 个中；顶、底各 2 个），孔外 1 m 内共 **14 个**。**LY-045 prep 记的是 8 和 16，与本席位不一致**，可能是计数口径不同（例如按包围盒），要在 LY-006 冻结孔清单前由两边对一次，不能各用各的数。
   - 两孔中心相距 **1,186.779 m**，共用宿主 0 个。也就是说，即使两孔都获准，合成也只是「两个宿主各一个孔」，不会出现同一宿主上的孔两两重叠测试；真正需要 O3 的是将来同一片 south / retained 上的多院厕坑、或窑坑落在原子地面上。
   - 厕孔下 south 是 2 m 规则网（LY-045 实测边长 2.0–2.828 m），整三角删除会过切（LY-045 负例 N8：206/744 个围圈底面采样失托）。合成器必须做真正的多边形差集并重新三角化，不能删三角。
15. **第二个地坪写入者 LY-089 已经声明**：它的差异片是独立 overlay 节点（terrain-diff-*.glb），并写明「不得封住 LY-090 登记的孔」。它测到的 G-3（market 底板 208 m 周长里只有东侧 4 m 接上路）正落在井孔的同一宿主 `sample_ground` 周边。所以 test-plan 增加负例 N8：089 的差异片覆盖任何已登记孔即 FAIL；孔清单要先于 089 的批准多边形冻结。

## 6. 复用判定（草案）

- **合成器本身没有可复用的现成成果**：仓库里没有任何开孔或切地形机制，也没有合成清单。
- **可以原样复用的输入**：
  - 井孔宿主：LY-025 的 `C_market_ground_well_A`（0193ebc0…）。外框和 sample_ground 一致，孔是 r 0.590 m 的 48 边形。在夹具里 S1/S7 都通过；
  - 前置席位已经冻结的孔多边形。
- 第一批（只有井）的合成结果在几何上就等于 LY-025 那个节点。本席位只多出唯一写入、绑定 SHA、顺序规则和整组回退这几件事，不应该再造一份同样的开孔地面。

## 7. 测量脚本与输出（SHA256，2026-11-06）

| 文件 | SHA256 |
|---|---|
| scripts/cut_plans.py | 9c3f6034d17fa83a13eb9441eba0119d56fbf483f3b2861835c5389fac88c86f |
| scripts/datum_pairs.py | aab4df6df868f9fa5a772572d057135d28109d25f9fb075936fbbac9328b6598 |
| scripts/dump_nodes.py | 6ead98d3d9999edf1760174fc69c8b9dae04a15aca993620390fa93ec9986031 |
| scripts/glb.py | 2af11bcb11b61659c6d2b1d19fb67eddaec12589f28f0f293e6e426ef2a4be78 |
| scripts/ground_stack.py | 538a5f0e21180fbfd16df8c4986565b55249ae837002a10ff713199041aaa351 |
| scripts/hole_check.py | 4e70e4709c1d288d7105d6143f376ad6f4547634858fa2162417771a4599126b |
| scripts/hole_polygon.py | f9d79c7e0e2c9c34bd66728bcf70d3fda7c16b5ff7175d7dc802da53f6f6a612 |
| scripts/host_inventory.py | 99691934590f9d8666f853e5e190533ca854e9d7a2d3018a2f11d587a8652107 |
| scripts/liner_radius.py | 8fe639c5984814efb441d8e1aced4be22d2b010e742417f6742471ddfa46cd94 |
| scripts/plate_thickness.py | cb71463e011ece688d105f5aa0aa6e70cd872d69b949f3fffe786245024a8c18 |
| scripts/rect_tri_sat.py | 6f140c880f1ca0755b1ed3e2bf77591a81d1b22a73d9d6e3143294e738a4fdf4 |
| scripts/write_inputs.py | 2ec2df701b82ac2c4da0d9b808d79f37f82c9862a6a52149e26ec6043823bac3 |
| scripts/run_prep.sh | c10647e2df105bdb72ebb64ab889dfd0616f9705d34a0589321d359eb11a2fe3 |
| tests/hole-check-config.json | 8e0d613c51525d4a2f050d394d7c5c302b7fd88b0839a4c7af63dee8ea6a06a1 |
| out/cut-plans.json | a3719e989142d5f8278fd27a33088dd75976f871970ec6389c2688650b869bdb |
| out/datum-pairs.json | 632134392804e250fed2214cd2ca6b0d7375e26b865b9c7209d930f3c86077a5 |
| out/ground-stack.json | 1cc4366a762b62a5b1a8996fc562d44a2a0531a69f1efa50e352abc148473387 |
| out/hole-check.json | f9ac7f8a8625c1427e0220bdc9c2aa300880437f966da497563a983290e6d4c2 |
| out/hosts.json | 9866f643b1dadddabe26143ce945ab62bb8044d77b725439a48a87475f225520 |
| out/plate-thickness.txt | f0bb89f0ccf11e2215a5ba63123775d2f3ce385df2da120162336b377f148962 |
| out/privy-rect-tris.txt | 20f4520bfa942e7561d827ebc0e426ae315d8ceed0485b185b20c670dc1bd0e6 |
| out/well-hole-polygon.json | 8c032ece09c4ecaf1ad032aa50abf05ea8706ae1de7a2741e3fdcbfb93990b8d |
