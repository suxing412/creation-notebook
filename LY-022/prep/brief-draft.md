# LY-022 市肆前街连续地坪接口 · 开工准备 brief（草稿）

状态：**待输入**（G 未冻结，LY-021 未交付）。本目录只有测量、清单和检查器，没有任何交付几何。
基线：creation-notebook-lab `bce3211f818ee5a8bef1773539da70695ba37b17`，只读。所有坐标为 glTF（X 东、Y 上、Z 负向为北），"局部"= 减去市肆中心 (214.286, —, -1959.184)。

## 1. 本项目标（按任务池原文）

在「店前线 v2.1 八处入口的门前组件（LY-021）」与「现有 7 条路带」之间，补局部地坪或边缘差异件，使八铺前街连续可走；不重铺已有道路，不移动井和铺面，不形成双层路面，外街归 LY-083。

## 2. 核到的现有成果

| 成果 | 路径 | SHA256 | 是否在城景里加载 |
|---|---|---|---|
| 城中市肆（五店三摊 + sample_ground + 7 路带 + 5 段界墙） | docs/cities/luoyang/assets/market/market-cluster.glb | 77b8bf2e9e1488df02c99ffa1b83af9517fabbb23e9d6b7f86dd3c3361c5a5c8 | 是。city-data.mjs:511 资产 market-main，:3953 market 章 |
| N2 替换件 | docs/cities/luoyang/assets/market/N2-replacement.glb | d33cbad1ea14e9436219e895791aafa3c4de20dfe7648635909d6b734e1c99d1 | 是。city-data.mjs:562 |
| 店前线 v2.1 原件（三档） | docs/library/models/m-luoyang-market-frontage/files/street_frontage-LOD0/1/2.glb | 46f08f41…f6f2 / 03ad28cf…6126 / b5b13b1c…a1f0 | 否，只有资产卡 |
| **已摆放的店前线组合**：店前线 v2.1 + 井 A + 带井口的地面 + 同一套 7 路带 + 界墙 | modeling-lab/review-batches/2026-11-04-city-visible/city-visible-web-handoff-v1-public.zip.part01–05 里的 `chunks/market_frontage_well_routes.glb` | 0193ebc0cfe200292defd595ff4f4011b2b2d05388d4f53e7b4c3a19a255b4c5（ZIP 5895ef23…0b69） | 否。adapter.json 写明 "not published"；母版 city-C032-entry-LOD0.blend（1e8c4d2c…b01b）不在仓库 |
| S84/S86 修订前框 | docs/library/models/m-luoyang-market-modular-assembly/files/S84-LOD0.glb、S86-LOD0.glb | 8ef1f3c8…6fa84 / 7f1c2e70…77ee8 | 否 |

完整清单和每个文件的 HEAD/工作区双 SHA 见 inputs.json。我用 extract_chunk.py 在内存里拼回 ZIP，取出这一块存到 prep/inputs/，SHA 和清单一致；LY-021 独立取出的副本也是同一个 SHA。

**「7 条既有路带」到底是哪 7 条**：`route_public / route_east / route_rearN / route_rearS / route_exitPublic / route_exitN / route_exitS`。market-flow-plan.json 的 retireOriginalNames 正好列了这 7 个名字。它们在城中五店三摊和店前线组合块里**逐顶点相同**：12 个路带和界墙节点的指纹全部一致（chunk-continuity.json）。

## 3. 改 / 不改范围

- **可改（LY-022 唯一写入）**：新的局部地坪或边缘件，只放在前街带内：局部 x∈[-22.7, 24]，|z|∈[2, 5]，再加东端 x∈[22.15, 24]、|z|≤5 的小块。这片面积最多约 280 m²。另外交它的三档、装配记录和撤回记录。
- **不改**：7 条路带、5 段界墙、`C_market_ground_well_A` / `sample_ground`、店前线三节点、井 A 的 121 个节点、N2、五店三摊、city-data.mjs、项目卡，以及 x=244.286 以东的外街（LY-083）。
- **必须避开**：井口圆心在局部 (-18.00, +7.00)，半径 0.5875–0.5925 m；井体平面在局部 x[-19.32, -16.68]、z[5.75, 8.25]。棚柱伸进前街带 0.02 m，只在南侧 z∈[-5.12, -4.98]，x 为 [-22.57,-22.43]、[-19.57,-19.43]、[18.83,18.97]、[21.03,21.17]，这部分归 LY-023。

## 4. 证据与未知

- **原始考古 / 原文**：无。没有约 180 年洛阳市肆街面的标高、铺装或宽度依据。
- **异地异期类比**：成都博物馆《市肆画像砖》（任务池给的 URL）只能说明同时期异地市场的图像，不能用来定洛阳的路宽、高差和铺装。本轮我没有打开它，也不引用。
- **C 工程设计**：0.20 m 地面、0.21 m 路带、0.22 m 台基、10 m 前街、4 m 路带宽，全部是 C 设计。
- **未知**：真实路面材质和排水；店前是否有台阶。
- 五件事要分开看：「模型能读取」已验证（GLB 能回读）；「局部通行通过」只做了有限射线；「已入城」不成立，店前线不在城里；「真实结构安全」和「历史复原成立」都没有声称。

## 5. 实测缺口（数字来自本目录脚本）

1. **方案不同**：城里现在默认是五店三摊（market-main）。店前线只出现在一个没有发布的组合块里。两者放在同一处会互相穿插，N2 和店前线南排在 z 方向重叠约 2.5 m。所以 LY-022 的落位依赖 LY-010 和 LY-029 先选定方案。〔nodes-*.json，measure_p0_fit.py〕
2. **高程基准**：原件台基 0.00→0.22。组合块整体抬高 +0.20，台基顶 0.42。地面 0.20，路带 0.21。五店三摊用的是另一套：台阶 0.30，铺面 0.39。〔nodes-frontage-LOD0/1/2.json，nodes-chunk-market.json〕
3. **前街支承已经连续**：局部 x[-24,24]、|z|<4.875 范围按 0.25 m 网格打了 7720 个点，**0 个落空**。4608 点落在地面 0.20，3072 点落在 route_public 0.21，40 点落在 route_east 0.21。相邻点之间超过 5 mm 的高差一共 408 对，**全部都是 0.010 m**，也就是路带边沿那一圈 1 cm 的坎。〔chunk-continuity.json，measure_chunk.py〕
4. **八处入口**：每处台基都是 0.42，比外侧地面高 0.22。八处的台基前沿到 route_public 边沿都是 **3.00 m**，中间是连续的 0.20 地面。这个 0.22 m 高差归 LY-021。〔chunk-continuity.json〕
5. **井口没有被盖住**：地面开口半径 0.5875–0.5925 m。从开口上方往下打射线，碰不到地面，也碰不到任何井以外的几何。井口离 route_public 5.0 m，离 route_rearS 8.0 m。井体比前街带外沿再往外 0.75 m。城中五店三摊的 sample_ground 只有 12 个三角，没有开口，那里也没有井。〔chunk-well-hole.json，measure_hole.py〕
6. **路带本来就叠在地面上**：7 条路带都是 0.20–0.21 的薄板，压在 0.20 的地面顶上，共面接触面积 772 m²。这是继承下来的叠层。「双层路面」到底算不算它，要由 LY-006 定义，LY-022 不能私自改。
7. **前街上方净空**：前街带内最低的檐口在 2.55 m（离地 2.35 m），位置在局部 (-20.5, -4.875)，是棚檐。
8. **外接点**：城网地面 C_stitch_primary 只在 x=244.286、z -1961.18…-1957.18 一段碰到市肆（5 个采样点，0.21），归 LY-083。市肆内部没有和城网重叠的地方。〔network-in-market.json〕
9. **三档**：组合块只有店前线 LOD0。LOD1 和 LOD2 只有原件，原件台基同样是 0.22，没有已经摆放好的三档。

**结论（条件性复用）**：如果 G 选定的是组合块的落位（+0.20，不旋转），而且 LY-021 的踏步外端落在这 3.00 m 宽的 0.20 地面上，那么现在的地面加 7 条路带已经能连续支承。LY-022 需要的新几何可能是**零**，最多只是处理 1 cm 路沿（如果 LY-006 或 LY-008 的容差小于 0.01 m）。最终是「复用」还是「补件」，要等 G 和 LY-021 交付后跑 test-plan.md 才能定。

## 6. 测量脚本（都放在 prep/，只读输入）

measure_nodes.py、measure_islands.py、measure_p0_fit.py、measure_chunk.py、measure_hole.py、measure_network_overlap.py、extract_chunk.py、make_frozen_baseline.py、build_inputs.py；检查器 check_patch.py（自测 7/7 结果符合预期）。运行命令统一为 `D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P <脚本> -- <参数>`。
