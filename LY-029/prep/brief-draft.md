# LY-029 八铺四棚候选的互斥与回退包 · 开工准备稿（prep，未制作）

状态：**待输入**。G（LY-001/002/005/006/007/008/009/010）没有冻结，前置席位 LY-021—028 也都还在 prep，没有交付物。本稿不含任何交付几何，只读输入、实测缺口、准备测试。
核对基线：creation-notebook-lab main `bce3211f818ee5a8bef1773539da70695ba37b17`。该仓库工作区里 `lab/data/assets.json`、`glb-cache.json`、`report.json` 有未提交的修改，不是本席位造成的；本稿用到的 48 个输入逐个对 HEAD 核过，都没有改动（inputs.json 的 `cleanVsHEAD`）。
复现：`sh prep/scripts/run_prep_checks.sh`。脚本只读仓库，基线不对就拒绝运行，结果写到 `prep/out/`。

## 1. 本项目标（照任务池原文）

- 类型：复用装配。依赖 G 和 LY-021—028。
- 产物：新街市（八铺四棚）、现有五店三摊、其他布局三者之间的节点映射，以及「一次只启用一套」的启用包和还原包。
- 边界：三套候选不能叠加，不能增加历史铺数；旧井、道路和边界都要保留；版本对不上必须拒绝执行。
- 验收：每一套都从严格基线安装、再撤回，旧节点、材质、矩阵都要恢复；两个市肆变体不能同时出现；井和道路不能被误卸。

## 2. 核到的现有成果（SHA256 全值见 inputs.json）

| 候选 / 成果 | 路径 | SHA256（前 16 位） | 当前城景 |
|---|---|---|---|
| **V1 五店三摊 v1 基础组**（默认） | docs/cities/luoyang/assets/market/market-cluster.glb | 77b8bf2e9e1488df | **已加载**：主城 city-data.mjs:511（excludeNodes 30）、节点 :3663、章节 :3957；v1 west-layer.mjs:33 |
| V1 的 N2 替换件 | …/market/N2-replacement.glb | d33cbad1ea14e943 | 已加载：city-data.mjs:562、:3690；west-layer.mjs:33/36 |
| V1 流线 B（可选） | …/market/flowB-routes.glb | 43d7799f85feccb0 | 只有 v1 在 flow=B 时加载（west-layer.mjs:36）；主城没有 B |
| **V2 五店三摊 v2**（m-market-functional，三档） | docs/model-library/updates/m-market-functional/files/market-LOD{0,1,2}.glb | acdd4391… / e925451b… / ea0c235f… | 未加载，也没有落位记录 |
| **F 八铺四棚店前线 v2.1**（三档） | docs/library/models/m-luoyang-market-frontage/files/street_frontage-LOD{0,1,2}.glb | 46f08f41… / 03ad28cf… / b5b13b1c… | 未加载；只在母版可见分块里出现 |
| 母版可见分块（F 已落位＋开孔地面＋7 路＋5 界＋井 A） | ZIP 内 chunks/market_frontage_well_routes.glb（LY-021 解出的只读副本） | 0193ebc0cfe20029 | 未加载（adapter 节点 initial:false） |
| 三铺组合样例（其他布局） | docs/library/models/m-luoyang-market-modular-assembly/files/generated_788bb4c4f5f9f6c3-LOD{0,1,2}.glb | b599ade0… 等 | 未加载，没有落位 |
| 本地 A+N2 副本 | docs/model-library/assets/market-A-N2-local.glb | 493798b8f09f594b | 未加载 |
| 契约 | data/west/N2-contract.json、market-flow-plan.json、market-interface.json、ground-atomic-contract.json | 10678d73… / bff5bb22… / 31c6786d… / bfc7fc83… | N2 与流线契约由 west-layer.mjs:40 读取 |

## 3. 实测（结果见 prep/out/，脚本见 prep/scripts/）

### 3.1 候选到底有几套（variants.json、v2-triset.json、local-vs-city.json）

- **V1 和 V2 是同一个布局，只是不同版本。** V2 LOD0 平移到锚点 (214.286, 0, −1959.184) 以后，和城里的 V1 结构（market-cluster 去掉 30 个 N2 节点和 13 个共享层，再加上 N2 替换件）比：三角形一共 18140 对 18140 个，在 1 mm 和 1 cm 容差下都**没有任何一方独有的三角形**；XZ 足迹 IoU = 1.000。V2 把这些合并成 4 个按材质分的网格（earth/timber/tile/paper），加了贴图，但**不带**地坪、路带和边界（y 最低 0.2）。LOD2 的 IoU 是 0.974。
- **本地 A+N2 副本就是 V1 平移到原点**：524 对 524 个网格，节点名全同，顶点最大差 0.0 m；optional-B 和 flowB 也一样，差 0.0 m。它不是第三种布局，只是 V1 的副本，任何时候都不能和 V1 同时入城。
- **F 和 V1/V2 落在同一块地上**：F 结构（y>0.25）和 V1 有效结构＋N2 在 XZ 上的重叠是 **185.1 m²**（F 404 m²，V1 348 m²，0.25 m 网格），其中和 N2 重叠 22.9 m²，和共享屋面重叠 180.3 m²。逐组看，N1、N3、S1、S2、T1、T2、T3、north_*、south_*、sharedRoof 每一组都和 F 相交。也就是说，**换成 F 必须把 V1 的全部 487 个结构节点（其中 30 个已经被 N2 排除）和 N2 的 54 个一起卸掉**，留一部分不行。这和 LY-025 记录的母版做法一致（母版隐藏了 market-cluster 的 457 个、N2 的 54 个）。
- 三铺组合样例（25.3×12.75 m）和 S84/S86 都在局部原点，**仓库里没有任何城市落位记录**。要把它当第三套入城，需要 C 落位，而且要先经过 LY-010 准入；否则只能停在独立资产层面。

### 3.2 共享层：哪些不能卸（variants.json、baseline-fingerprints.json）

- market-cluster 里有 13 个共享层节点：`sample_ground` 1 个、`route_*` 7 个、`boundary_*` 5 个，合起来的指纹是 b88718bf…5a81。
- 母版分块里的同名 7 路 5 界，和 market-cluster 里的完全一样：12 对节点三角数相同，包围盒差 0.0 m。
- F（全高度足迹）和 7 条 A 路带、6 条 B 路带、5 条边界的 XZ 重叠都是 **0.0 m²**。也就是说，换 F 的时候可以原样保留路带和边界，不需要改路。
- 井 A（母版位置）和 V1 结构＋N2、F、A 路带、B 路带的 XZ 重叠都是 0.0 m²。井和市肆变体互不相干，唯一的冲突是旧地坪 sample_ground，归 LY-025 负责。
- 市肆框里（184.286…244.286 × −1981.184…−1937.184），原子地面四片、6 m 走廊、joined-route-terrain 都是 **0 个三角形**（stitched 的包围盒虽然盖住了这里，但框里没有面）。所以 sample_ground（或 LY-025 的开孔地坪）是这块地上唯一的地面；变体切换要是误卸了它，地面就会消失。

### 3.3 严格基线指纹（baseline-fingerprints.json；跑两次结果逐字节一致）

| 状态 | 网格数 | 三角数 | 状态指纹 |
|---|---|---|---|
| 主城 chapter=market（market-main−30 ＋ market-N2） | 524 | 18296 | 200f269d78185334… |
| v1 layout=calt view=market flow=A（含 4 片原子地面） | 530 | 264766 | df7e9c34ac660d22… |
| v1 同上，flow=B | 529 | 264754 | 6a5462e00e88bbcb… |
| v1 只算市肆部分，flow=A | 524 | 18296 | 200f269d…（和主城相同） |
| v1 只算市肆部分，flow=B | 523 | 18284 | dbaeae0c7b60c0cb… |

指纹的算法：每个网格按（资产 SHA、节点名、材质名、世界坐标三角形取整到 1 mm、排序）求 SHA256，再把全部网格的值排序后求一次。安装再撤回以后，这些值必须一个不差地回来。

### 3.4 现有加载器在互斥和回退上的真实缺口（代码只读核对；逻辑负例写在 baseline-fingerprints.json 的 negatives 段）

1. **版本不对不会被拒绝（NEG-A）。** 主城 city-renderer.mjs:286-346 加载资产时不校验 SHA，只检查 excludeNodes 的名字是否全部命中（:346）。v1 market-assembly.mjs:4 也只核名字和个数（30、7）。拿同名的 market-A-N2-local.glb 冒充 market-cluster，30 个排除名和 7 个路带名照样全部命中，而这 30 个节点几何全都不同，加载器不会报错。仓库里已经有现成的 SHA 闸门写法（v1/road-layer.mjs:18、wall-layer.mjs:21、evidence-view.mjs:27），但市肆这两条路径都没用上；v1/r01-assets.mjs 里也没有任何 SHA 检查。资产记录里其实写着 sha256（city-data.mjs:514），只是渲染器从来不读它。
2. **同名冲突（NEG-B）。** N2 替换件 54 个节点里，有 30 个和 market-cluster 被卸掉的节点同名。卸载只要不是限定在「本资产根」里按名字匹配，就会把 N2 替换件一起删掉（market-assembly.mjs:1 的注释也提醒过这一点）。
3. **主城不会卸载已经加载的节点（NEG-D）。** focusChapter（city-renderer.mjs:600-605）和 focusCourtyard（:620-624）只会往 cityIds 里加 id，没有任何代码会移除。所以如果给两个变体各开一个章节，先后打开以后两套会同时在场。
4. **对称的 replaces 会把两套都清空（NEG-C）。** rebuild（:412-415）把所有在场节点的 replaces 取并集。如果 A 写了 replaces B、B 也写了 replaces A，两个就一起消失，市肆变成空地。目前 66 个节点里没有一个用到 replaces。
5. **排除表是按资产写死的。** excludeNodes 挂在资产记录上（city-data.mjs:515），不跟着变体走。要让 F 保留 13 个共享层、卸掉 487 个结构节点，只能二选一：再加一条指向同一份字节的资产记录（排除 487 个），或者给加载器加 includeNodes 功能。而 LY-025 也计划在同一个 market-main 的排除表里加 `sample_ground`。**这是所有权冲突，要 LY-006 裁定。**
6. **v1 不认识变体。** west-state.mjs:2-3 只有 level、layout、flow 三个参数。applyMarketReplacements 默认 roots[0] 就是 market-cluster，个数写死为 30 和 7。所以 F 或 V2 在 v1 里根本没法加载，必须改代码（只能写提案，由 LY-100 落地）。好的一面是 v1 的 Transaction（west-state.mjs:5-11）每次只持有一个资源，新资源成功以后才释放旧的，失败就保留旧状态，这一点可以直接用来做回退。
7. **流线 B 会卸掉共享路带（NEG-E）。** B 要卸的 7 个节点正好是 13 个共享层里的 7 条路带。F 或 V2 保留这些路带时，B 只能拒绝执行，或者重新定义，不能照搬。
8. **文案写死了五店三摊。** app.mjs:26、scene.mjs:12、city-data.mjs:3954-3955 的章节标题和副标题、p-luoyang.asset.json:134，写的都是「五店三摊」。切到 F 以后，这些文案必须跟着变体走（共享文件，交 LY-100），否则页面上写的数和实际看到的不一致。

## 4. 改与不改（草案，G 冻结后才做）

**要做**：在 workpacks/LY-029/ 下交以下内容。
- `assembly.json`：三套候选 {V1 默认、V2、F}，外加「不入城」名单 {本地 A+N2、三铺样例}。每套写明加载哪些资产（带 SHA）、排除哪些节点、保留哪 13 个共享层，以及 LY-021—028 的附件分别挂在哪一套上。
- 节点映射表：V1 的 487＋54 个节点 → V2 的 4 个合并网格（三角形集合一一对上）；V1 → F 只能整套对整套，因为 F 只有 3 个按材质合并的网格，没有单铺、单棚的节点。表里明说「八铺四棚」是另一套 C 布局，不是在「五店三摊」上加铺。
- 安装包、还原包和变体选择器的语义合并提案，两条加载路径都写：主城由「互斥组」从 cityIds 里把另一套的 id 删掉；v1 增加 variant 参数，并改造 applyMarketReplacements。每个资产都要过 SHA 闸门。
- 一个 node 模拟器，按两种加载器的语义算出当前在场的网格集合和指纹。

**不做**：不新建或修改任何几何；不改井、开孔地坪（LY-025）、路带和地坪补片（LY-022、083）、踏步（021）、摊脚（023）、闭铺件（024）、井架（026）、货架（027）、卸货地面（028）；不直接写 city-data.mjs、city-renderer.mjs、v1/*.mjs、app.mjs、项目卡；不改默认（默认仍是 V1）；不自动启用。

## 5. 证据与未知（四类）

- **原始考古／原文**：没有。金市只有区域标签点（gao2023_fig1，B 级），没有市界、地块、店数（market-precedents.json）。
- **异地异期类比**：国博市楼画像砖、四川酒肆和画像砖、宋艳萍 2023，都是跨地域的类比，不能推出店数、面积或布局。
- **C 工程设计**：V1、V2、F 的布局、店数、尺寸全部是 C；本包的互斥、回退和 SHA 闸门也是 C 工程约定。
- **未知／冲突，要上报**：market-precedents.json 的 C 提案写的是单层店「4–6」间、摊「2–3」处，还要「避免两排完全对称的现代商街」。F 有 8 间店，是南北两排对街布置，超出了这个 C 提案的范围。F 能不能作为候选入城，要 LY-002 或 LY-010 给准入结论，本席位不替它判。

五件事分开说：GLB 能读取（三套都已实测）≠ 局部通行通过（本席位不测，归 021/022/028/030）≠ 已入城（只有 V1 入城；F 和 V2 **没有**）≠ 结构安全（未验）≠ 历史复原成立（**否**，三套都是 C）。

## 6. 复用判定

没有现成合格的互斥/回退包。母版分块证明了「F＋共享层＋井」这种组合放得下（共享层同名同几何，F 和路带、边界的重叠为 0），但它把 F、地坪和井打在一个 GLB 里，没有撤回，没有 SHA 闸门，也没有和 V1 互斥，所以不能直接交付。可以复用的是零件：V1/V2/F 的原 GLB 都可以原样引用，不需要新造几何。本席位要做的全是装配和加载器语义。
