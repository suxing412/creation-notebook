# LY-026 井架操作构件兼容检查与修订：开工准备 brief（草稿）

状态：**待输入**（G 未冻结，LY-025 未交付）。本目录只有读取、实测和测试准备，没有制作或修改任何交付几何。
核对基线：creation-notebook-lab `bce3211f818ee5a8bef1773539da70695ba37b17`（`git diff --quiet bce3211` 对 well-study、docs/cities/luoyang、city-visible 批次三处均无差异；工作树另有 lab/data/*.json 本地改动，与本项无关）。
日期：2026-11-05。Blender 5.2.1（测量）；GLB 由 Blender I/O v4.3.47 导出。

## 1 本项目标（按任务池原文）

只围绕**已有**轮轴、绳槽、容器的有限姿态，修**确有冲突**的导向/支承小件。先核原图与现件，未知机构不乱补；不加水深/水位，不声称取水动力学、承载、卫生通过。验收要求修改前后净空/接点逐项绑定 SHA、给容器行程和轮轴有限姿态、未知原图/机制单列停止项。

## 2 现有成果（全部只读）

| 成果 | 路径 | SHA256 |
|---|---|---|
| 井 A 近景 | docs/model-library/well-study/assets/well-A-LOD0.glb（1,710,964 B，122 节点，9644 tri） | 6bc463f8638df55c7e07282641d3d66d07d23ce9af8cd72a5e211be9772a38ab |
| 井 A 低档 | …/well-A-LOD1.glb（1,346,488 B，78 节点，3216 tri） | e9252de34398ef8049876aadaf60f2e4c7c9d9aebc35cd40f34b9fca55fd3255 |
| 井 B 近景 | …/well-B-LOD0.glb（1,681,036 B，108 节点，9228 tri） | adf2f51a029289e8afbed8a583b1195bd22b815739b72f1c19e08bf693d55139 |
| 井 B 低档 | …/well-B-LOD1.glb（1,310,032 B，60 节点，2784 tri） | e4acc416db1024a28606a556c9c0b827482fb3da2d2232ecf00a83ea014aa9dd |
| 资产卡 | docs/model-library/well-study/m-well-family.asset.json（status 待审，「尚未公开」） | dfaaa0e99e3723c1d90639ba517825ac00ec150c436c3ede98df2e77e7fe06cb |
| 契约 | …/contract.json | b09677db7a8febaf7ec063141500cd6798c63e176d1fa2a878220bb038f76175 |
| 参考契约 | …/inputs/reference-contract.json | 75b3bd8fa750b0b7886cd33456cbf9ca51755cccb0fa5729679401e817e0087b |
| 接点/包络 QA | …/qa/local-contact-checks.json | 8850528ec7a13434a433c4c9a5616c5150a94b4be81247fa505a01e31f3d62fd |
| 选定布尔 QA | …/qa/local-boolean-intersections.json（只有 LOD0） | 921e7bba1351fba34efc608371820a974b955c478551d60625a62ec37f376650 |
| 母场景试放分块 | city-visible-web-handoff-v1-public.zip（5 个分卷，ZIP 5895ef23…）里的 chunks/market_frontage_well_routes.glb（3,695,576 B） | 0193ebc0cfe200292defd595ff4f4011b2b2d05388d4f53e7b4c3a19a255b4c5 |
| 分块适配清单 | modeling-lab/review-batches/2026-11-04-city-visible/adapter/adapter.json（节点 initial:false，tier C） | 703caeed4a7834e9e5324e1d2f1a1df78412c50d756768c6c98c3638f216934f |
| 现城市肆 | docs/cities/luoyang/assets/market/market-cluster.glb（含 `sample_ground`，没有井） | 77b8bf2e9e1488df02c99ffa1b83af9517fabbb23e9d6b7f86dd3c3361c5a5c8 |

**入城状态：** 现在网页城景**没有加载任何井**。`city-data.mjs:512` 和 `v1/west-layer.mjs:33` 加载 market-cluster.glb，里面只有实心 `sample_ground`。井 A 只出现在「母场景可见集」分块里，这个分块不被任何 docs 代码引用，adapter 也标成 `initial:false`。井 GLB 只由 well-study/viewer.js 和 index.html 加载。所以按五件事分：**模型能读取 = 是；局部通行 = 未测（不是本项范围）；已入城 = 否；真实结构安全 = 未验；历史复原 = 不成立（C 设计）**。

**城市试放 = 库件吗？** 已用 compare_city_well.py 比对：分块里 121 个 `A_LOD0__*` 节点就是库件 A-LOD0 的 122 个节点去掉 `demonstration_apron_opening`。世界偏移在 Blender Z-up 下是 (196.286, 1952.184, 0.200)，旋转和缩放为恒等。115 个节点的 5 位小数有向三角集合完全相同；另 6 个节点（容器 4 件、轮辐 2 件）的节点平移不同，最大顶点差 3.5e-5 m，这是 float32 在约 1952 m 坐标处的舍入，没有改形。

## 3 改 / 不改范围（草案，待 LY-006 冻结所有权）

- **会碰：** 只碰井家族的操作件节点：`*_wheel_grooved_ring/hub/spoke*/axle/cheek_±1`、`*_rope_C_static`、`*_drawing_container/container_bottom/bridle*/lug*`，以及它们直接支承的 `*_cross_head` 接面。只交差异件或姿态数据，不重导整井。
- **不碰：** 井栏、井筒、柱、屋面、瓦；`C_market_ground_well_A` / `sample_ground` 地坪及开孔（归 LY-025）；店前线、路带（LY-021/022）；city-data.mjs、项目卡和网页（归 LY-100）。
- **不做：** 水面、水位、井深延长、绳索动力学、承载、卫生，也不新加机构（棘轮、摇把、配重等）。

## 4 证据与未知（四类）

- **原始考古/原文：** 目前没有。洛阳约 180 年的井架实物或发掘图，本轮一份也没取得。
- **异地异期类比：** 河南博物院张延红文（https://www.chnmus.net/ch/collection/appraise/details.html?id=512156440644025062）。本轮用 WebFetch 读了正文文本，记灵宝张湾东汉陶井模型「亭内中贯滑轮，其周缘有绳槽」，并有两耳通孔小罐。同一页墓号前后写成 2 号/3 号，不一致；正文还说两柱井架「呈梯形」，现件是直柱。我**没有亲眼看到图版**，WebFetch 只给文字。这件是灵宝出土的明器，不是洛阳实物，也不给尺度。烧沟灰陶井那页只泛标「汉」，木架为后配（据 reference-contract 转述，本轮未重读）。
- **C 工程设计：** 轮径（槽底半径 0.18，绳心半径 0.186）、轴径 0.052、侧托、容器尺寸、绳长、井口高度，全部是 contract.json 写明的 C 参数。
- **未知（停止项）：** ① 轮轴怎样转：轴同时实体嵌进两侧托和轮毂，模型里没有轴孔，不知道轴转还是轮转，也没有轴承形制；② 原图版细节没核：滑轮是否有轴、侧托形状、梯形架和直柱的差别；③ 绳的材料、长度，以及收绳端怎么处理；④ 水位/井深（契约禁止推断）。这些都不靠补几何来解决。

## 5 实测结果与真实缺口

脚本：`measure_well_ops.py`（SHA 1801c756…），`measure_city_ground.py`（52c4ef48…），`compare_city_well.py`（ae560b29…），`pose_table.py`（afc83e86…），`summarize.py`（38cb5f6e…），`extract_chunk.py`（406452ba…，只在内存里合并分卷）。结果在 `results/`，汇总看 `results/summary.json`。

### 5.1 运动件和静止件之间（A/B × LOD0/LOD1 × 城市试放，结论一致）
- **容器竖向行程：** 容器组半径包络 0.336 m。在 A 的井筒内最小净空 0.1138（LOD1 0.1118），B 为 0.1886（LOD1 0.1854），城市试放 A 为 0.1137。从静置位起向下到模型井筒底（−0.65/−0.70）和更低都无表面交叠；向上 +1.30 m 内自由，+1.35 m 时撞上轮环，这是预期的行程上限。**无冲突。**
- **提出井口：** 容器底抬到口沿顶 +0.03（A dz 0.59，B dz 0.51）后，沿 ±y 横移 1.8 m 都无碰撞；沿 ±x 在 0.7 m（A）/0.8 m（B）处碰柱，属正常边界。**无冲突。**
- **轮的有限转角：** 轮环、轮毂、4 根辐绕轴转 0–345°（步长 15°），只与轴接触（固定嵌接），从不碰侧托、横梁、绳。轮环顶到 cross_head 底 0.035 m，轮环到侧托轴向 0.030 m。**无冲突。**
- **绳：** 两股分别在 y=±0.186，下端都在 z=0.52。绳对槽交体 2.1e-14 m³（数值残留）；绳到辐最小 0.0289 m；绳顶 2.142，到横梁底有 0.058 m。

### 5.2 源 QA 没有分类的实体嵌接（真实缺口 1：分类，不是冲突）
源 `local-boolean-intersections.json` 只列了轴—侧托一对（0.000147 m³/侧），而且只测 LOD0。本次精确布尔测得：
- 侧托上端插入 cross_head **0.000672 m³/侧**（0.07×0.16×0.06 m，榫入 0.06 m），四个文件都有，源 QA 没登记；
- 轴穿过轮毂 **0.000210 m³**（LOD1 0.000191），是实心毂、没有孔，源 QA 没登记；
- 辐入轮环 3.9e-6（LOD1 4.5e-6），辐入毂 3.0e-6（LOD1 1.7e-6）；
- 容器底入罐 2.14e-5，耳入罐 1.27e-5，提梁对耳 5.8e-7，提梁对提梁 1.8e-8，绳对提梁 7.7e-8；
- LOD1 两档的轴—侧托为 0.000134 m³，源 QA 没测。
这些都是局部固定接面，不是运动件冲突。制作阶段要逐对写进接触分类，不能整对豁免。

### 5.3 有限姿态（真实缺口 2：姿态数据缺，不是几何冲突）
`results/pose-table.json`：静态绳长 3.444 m，绳心半径 0.186。
- 容器 dz −0.77（底到 −0.65）：轮转 −237°，收绳端在 z 1.29；
- 静置 dz 0：收绳端在 0.52，低于口沿顶 0.68，悬在井口内；
- 提出 dz +0.59：轮转 182°，按定长绳，收绳端落到 −0.07，在井筒里；
- 最高 dz +1.30：轮转 400°，收绳端 −0.78，超出模型井筒底。
用手握住收绳段中部并不算冲突。但现件只有一个静态姿态，没有姿态参数和绳长状态，验收要的「容器行程 + 轮轴有限姿态」现在还交不出来。

### 5.4 城市地坪前置（归 LY-025，本项只当前提）
- 试放地坪 `C_market_ground_well_A`：顶 0.0（世界 0.2），底 −0.2，开孔半径 **0.590**，正好等于井筒外径。和井筒、井栏、柱脚的交体都是 0（共面接触）。井口 17 条竖射线畅通。井筒在地坪底以下还**悬出 0.45 m**，下面没有地层。
- **负例：** 把库件 A-LOD0 按同一变换放进**现网**市肆（market-cluster + N2 + corridor + joined-route-terrain，678 个 mesh），实心 `sample_ground` 堵住全部井口射线，容器下行只到 dz −0.10，−0.15 就撞上。此外演示环坪（−0.08..0）和 sample_ground（−0.2..0）会形成双层地面。市肆其他物件不进入井的 1.65 m 包络。

### 5.5 判断
在当前四个 GLB 和城市试放上，**没有测到需要新造或修改导向/支承小件的几何冲突**。本项大概率要判成「复用 + 分类 + 姿态数据」，只有 LY-006/007 改了接口，或 LY-025 换了落位、地坪，才会重开。

## 6 输入缺口
- 私密源包：source/build.py、check.py、check-contacts.py、check-local-booleans.py、manifest.json 和 4 个 .blend（native SHA ba15e0dd…）都不在仓库。没有它们就不能按原参数重生成；如真要改件，只能**从 GLB 重建**，并如实标注。
- 母版 city-C032-entry-LOD0.blend（1e8c4d2c…）不在仓库，城市试放只能以分块 GLB 为准。
- G 包：LY-005 坐标契约、LY-006 端口/所有权、LY-007 材质和三档、LY-008 检查器都还没有；LY-025 原子包也没有。
