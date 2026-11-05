# LY-025 市肆井和开孔地面原子包 · 开工准备草案（prep）

状态：**待输入**（G = LY-001/002/005/006/007/008/009/010 未冻结）。本目录只有读输入、实测和测试准备，没有制作或修改任何交付几何。
基线：creation-notebook-lab main `bce3211f818ee5a8bef1773539da70695ba37b17`（只读）。测量日期 2026-11-05，Blender 5.2.1（headless，CPU）。

## 1. 本项目标（按任务池原文）

复用现有的井和已经切好孔的地面，打成一个按当前基线重新绑定的「同进同退」包：井口、地坪孔和下方原有地层要一起验证；井或孔任一个加载失败，整包还原；原始井网格和变换要能追溯。不重新造井，不能出现旧地面堵井、只有孔没有井、只有井没有孔，也不能二次平移。

## 2. 核到的现有成果

| 成果 | 路径 | SHA256 | 在当前城景里 |
|---|---|---|---|
| 井 A 近景（库件） | docs/model-library/well-study/assets/well-A-LOD0.glb | 6bc463f8…2a38ab | 未加载（cityPlacement=null） |
| 井 A 低档（库件） | …/well-A-LOD1.glb | e9252de3…fd3255 | 未加载 |
| 井 B 两档（库件，本包不用） | …/well-B-LOD0.glb / LOD1 | adf2f51a… / e4acc416… | 未加载 |
| 井库契约 | docs/model-library/well-study/contract.json | b09677db…f76175 | — |
| 井 A LOD1 合批候选 256/128 | modeling-lab/review-batches/2026-11-04/C3/assets/well-A-LOD1-batched-{256,128}.glb | d7445554… / c193956c… | 未加载，只是候选 |
| **井入母场景试放（开孔地面＋井）** | modeling-lab/review-batches/2026-11-04-city-visible/ 分卷 ZIP → chunks/market_frontage_well_routes.glb | 0193ebc0cfe200292defd595ff4f4011b2b2d05388d4f53e7b4c3a19a255b4c5 | **未加载**（adapter 写明 not published） |
| 分卷 ZIP（5 卷，校验通过） | …/city-visible-web-handoff-v1-public.zip.part01–05 | ZIP 5895ef23…bb50b69 | — |
| 当前市肆主件（含旧 sample_ground） | docs/cities/luoyang/assets/market/market-cluster.glb | 77b8bf2e…c5a5c8 | **已加载**：city-data.mjs:511 `market-main`；v1/west-layer.mjs:33 |
| N2 替换件 | docs/cities/luoyang/assets/market/N2-replacement.glb | d33cbad1…c99d1 | 已加载：city-data.mjs:562；west-layer.mjs:33/36 |
| 流线 B | …/market/flowB-routes.glb | 43d7799f…898f845e | 已加载（flow=B） |
| 原子地面四片 | docs/cities/luoyang/assets/ground-atomic/*.glb | fdfc3ce5… / aed8b3d4… / 4313826d… / 3ab93310… | 已加载（layout=calt，west-layer.mjs:35–36） |

母场景试放的来源：`city-C032-entry-LOD0.blend`（SHA 1e8c4d2c…3b01b），集合 `C_MARKET_WELL_ATOMIC_TRIAL`，122 个可见网格 = `C_market_ground_well_A` ＋ 121 个 `A_LOD0__*`（visibility.json 实读）。

## 3. 改 / 不改范围（草案）

**要做（G 冻结后）**
- 从 0193ebc0… 分块里**无损截取**两组节点：`C_market_ground_well_A`（1 个）和 `A_LOD0__*`（121 个）。不带 V2.1 店前线和 12 条路带/边界，因为它们和 market-cluster 同名同位，带上就会叠两层。截取方法沿用 city-visible 包已有的 split-lossless 做法：accessor 原字节不变，世界矩阵不变。
- 交装配契约：在 market-main 上排除 `sample_ground`（1 个节点），同时加入井＋开孔地面这个新资产；两个加载口径（app.mjs/city-renderer 的 excludeNodes；v1/west-layer＋market-assembly 的 retire）都写语义合并提案，交 LY-100 落地。
- 做安装/撤回、单件失败整体回退、负例（旧地面堵井、有孔无井、有井无孔、二次平移、双层地面）的实测。

**不做**
- 不重新造井，不改井的几何、材质、轮轴、容器（LY-026 的范围）。
- 不加井深、水面、井底，不做动力学。
- 不改 market-cluster 的店铺、柜台、N2、路带，不改店前线 v2.1，不铺连续地坪（LY-022 的范围），不碰原子地面四片。
- 不写 city-data.mjs、p-luoyang.asset.json、city-renderer.mjs、v1/*.mjs（共享文件，只交提案）。

## 4. 证据与未知（四类）

- **原始考古 / 原文**：没有。仓库里没有任何「约 180 年洛阳市内有井、井在什么位置」的原始材料。井的类型依据是河南博物院馆文（灵宝张湾东汉中晚期陶井，见 inputs/reference-contract.json）。那是明器，馆文图片也没实际读到。
- **异地异期类比**：灵宝张湾、刘家渠属于同期异地；烧沟出土的陶井馆页只标「汉」，木架是后配，不能当东汉原构。
- **C 工程设计**：井 A 的全部尺寸（内孔 0.90 m、外筒半径 0.59 m、短井筒 0.65 m、亭檐 2.45 m）；开孔半径 0.59 m、48 段；井位在市肆局部坐标 (−18.0, +7.0)、地面标高 0.20 m；井筒截在 −0.45 m。
- **未知**：井在市内的位置和数量；井深、水位；试放为什么选这个点；开孔是用哪个脚本、哪组参数切的（母版没给）。
- **证据冲突（要上报）**：data/west/market-precedents.json 的 proposal.avoid 里明确写着「因名市井而强加水井」。所以把井放进市肆只能标 C 设计试放，不能拿「市井」一词当依据。这件事要不要做，需要 LY-002/LY-003 或制作人给一句准入。

五件事分开说：GLB 能读取（已实测）≠ 局部开孔通过（已实测，见 §5）≠ 已入城（**否**，当前城景不加载）≠ 结构安全（未验）≠ 历史复原成立（**否**，C）。

## 5. 实测缺口（带数字；脚本见 scripts/，结果见 work/）

复现：`sh scripts/run_prep_checks.sh`。

1. **当前城景没有井，也没有孔**。market-cluster 的 `sample_ground` 是 60×44×0.2 m 的实心板，12 个三角面，8 个顶点。在试放井点（native XY 196.286, 1952.184）打 41 条井口竖向射线，41 条全部打中 sample_ground（z=0.2 和 0.0）。（work/measure-baseline.json → boreRays）
2. **不换地面直接放井 = 旧地面堵井**。精确布尔：井筒 `A_LOD0__short_liner` 和 sample_ground 的交体积是 **0.09122 m³**（理论环形体积 π(0.59²−0.45²)·0.2 = 0.0915）；井筒和 sample_ground 有 384 对三角面相交，井栏圈有 192 对接触。（work/boolean-volumes.json）
3. **开孔地面本身合格**。`C_market_ground_well_A` 的 8 个外框顶点和 sample_ground 完全相同；另外 96 个孔圈顶点在 r = 0.5900–0.5901 m，高度只有 0.0 和 0.2 两档；其他顶点 0 个。16 个方位、步长 5 mm 实测开孔半径为 0.590–0.595 m。体积 527.7819 m³，比旧板少 0.2181 m³（理论 π·0.59²·0.2 = 0.2187）。（work/ground-pair.json，groundHoleRadius）
4. **井和开孔地面之间的接触**。井筒 ∩ 开孔地面 = **2.655e-6 m³**（48 段孔和井筒多边形之间的数值薄片，要按局部嵌接或数值残留分类，不能整体豁免）；井栏、两根柱、两个柱脚和地面的交体积都是 0（z=0.2 面接触）。表面 BVH 统计：井筒 79 对、柱和柱脚各 8 对、井栏 2 对，全是面接触。
5. **下方地层：没有封堵，但井底是空的**。11 个输入里，井口半径内 z<0.32 m 的命中数是 0。原子地面 `C_stitch_primary` 和 6 m 路 `C_main_road_width_6` 只是包围盒覆盖井位，井心 1.5 m 内没有任何面。所以去掉 sample_ground 以后井口是通的；但井筒在 −0.45 m 处截断、没有底，往下看会看到场景背景色。封底属于新的 C 设计，不在本包范围，记为风险。
6. **井网格可以追溯**。分块里的 121 个 `A_LOD0__*` = 库件 well-A-LOD0 的 122 个节点去掉 `demonstration_apron_opening`。三角面 9260 = 9644 − 384；平移 glTF (196.286, 0.200, −1952.184) 以后，逐节点顶点集合的最大偏差是 **1.0e-4 m**（坐标约 2000 m 时 float32 的精度极限）；没有旋转，没有缩放。（work/library-vs-placed.json）
7. **母场景和当前基线绑定的不是同一个市肆**。母场景可见的是店前线 v2.1（3 个合并网格，15288 个三角面），market-cluster 的 457 个店铺网格和 N2 的 54 个都隐藏了；当前 main 加载的却是 market-cluster 五店三摊＋N2。整块载入分块会叠两套市肆，还会让 12 条同名同包围盒的路带/边界重复。所以必须截取子集，并且按 market-cluster 重新绑定。
8. **和当前五店三摊的净距**（XZ 包围盒，从井心量）：route_public 5.00 m（扣掉亭顶半宽 1.65 m 后剩 3.35 m）；route_rearS 8.0 m；S1 铺 9.8 m。N2 和流线 B 不在 1.7 m 足迹内。这是包围盒净距，不是人体或货物通行实测。
9. **两个加载口径都要改契约**。city-renderer.mjs:309/346 的 excludeNodes 要求全部命中，否则抛错，现在是 30 项，加上 sample_ground 是 31 项。v1/market-assembly.mjs 的 retire 写死了 30 和 7，而且 environment 根不支持 excludeNodes，所以 v1 口径一定要改代码，交 LY-100。
10. **回退机制有现成基础**：city-renderer.mjs:422 `rebuild` 用 Promise.all，任一资产失败都不会替换旧的 modelGroup；v1 load() 在 catch 里调用 destroyDistrictAssets。这一点只读了代码，还没有实测故障注入。

## 6. 复用判定（草案）

几何上**可以完全复用，不需要新造**：开孔地面 = 旧 sample_ground ＋ 精确 0.59 m 孔，井 = 库件 A LOD0 去掉演示地坪，误差在 1e-4 m 以内。缺的只是**按当前基线绑定的原子包**（子集 GLB、排除契约、两个口径的安装和回退、负例）。这一部分是装配工作，不算新建筑家族。
