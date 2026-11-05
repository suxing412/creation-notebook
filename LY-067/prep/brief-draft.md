# LY-067 复道A柱脚地面适配 · 开工准备简报（草稿）

状态：**待输入**（G 未冻结）。本目录只有读取、实测和测试准备，没有制作或修改任何交付几何。
基线：creation-notebook-lab `bce3211f818ee5a8bef1773539da70695ba37b17`（checkout HEAD 停在该提交，SHA 一律按 `git show bce3211:path` 的提交字节记）。

第二轮复核（同日，G 部分交付后）：origin/main 已前进到 `cad338b`（f28d650、b70c495、cad338b 三个提交，只动雍门接路、北部三院和 city-data.mjs）。复道、登临、ground-atomic 文件在 bce3211..cad338b 之间 **0 改动**，cad338b 的城景代码里复道 ID 仍 0 引用，所以下面所有结论在 cad338b 上同样成立。本轮把 4 个旧脚本全部重跑一次，含 Blender 5.2.1 的导入复核，输出与第一轮逐字节相同。

## 1. 本项目标（照抄任务池第 705 行一节，不扩写）

- 对 A 局部片段的 16 个旧的、没命中地表的支点，逐个给出实际支持或基础接口，做不到就写明缺失报告。
- 不重做 A 服务木梯，不加假的展示大底板；宫区没配准时，只在冻结的局部演示域里做。
- 验收：逐脚对账；没有旧城市地形就报依赖缺失，不能靠假底板算合格；A 现有木梯保持不变。

## 2. 已核对的现有成果

| 成果 | 路径 | SHA256（提交字节） | 结论 |
|---|---|---|---|
| 复道A LOD0 | docs/library/models/m-luoyang-palace-gallery/files/gallery-A-LOD0.glb | 0c09279723e2334c35f21c7602c195cc867d97808ac0f99ccf6f0208d3ff3849 | 16 个柱础，模型内自洽 |
| 复道A LOD1 | …/gallery-A-LOD1.glb | 227c3c4ecc2625629d00ef6beb274575587e4f1095f68b7a50359781e94b3e68 | 柱脚与 LOD0 逐个相同 |
| 复道A LOD2 | …/gallery-A-LOD2.glb | cb26b56e1634f27a878d83997649804eaeef29f5a0bb1420b8aa959a65e137ea | 柱脚与 LOD0 逐个相同 |
| 复道B 三档 | …/gallery-B-LOD{0,1,2}.glb | c7cb279c… / fe72e192… / ff15e1c4… | 归 LY-068，这里只读作对照 |
| A服务登临节点（木梯） | docs/library/models/m-luoyang-gallery-access/files/access-A-{LOD0,LOD1,LOD2,collision-candidate}.glb | c973d325… / 7b5e26f4… / b39c34c2… / 7327547e… | 受保护，不改，只记指纹 |
| 复道卡 | m-luoyang-palace-gallery.asset.json | 100a78c3ed3a18e04bf5a98b8dd2c4d75e1d4b73461d96b0cf9c8893a7da3a0c | 卡上写「城市候选柱脚支承未解决，因此未入城」 |
| 登临卡 | m-luoyang-gallery-access.asset.json | 707f298fe235a2444c1f88c357cc75dcaea270d92754835671fbdb7480ca366e | 卡上写「未解决既有复道城市柱脚地表问题」 |
| 城市地面×4 | docs/cities/luoyang/assets/ground-atomic/{network-ground-stitched,retained,south,D08}.glb | fdfc3ce5… / aed8b3d4… / 4313826d… / 3ab93310… | 宫区没有地面（见第 5 节） |

三档 GLB 从 52fceaa 入库后，到 da1877a、bce3211 一直逐字节没变。完整清单和加载位置见 `inputs.json`，共 36 项。

**复用判定：没有可复用的合格成果。** GLB 内部的 16 个柱础只能说明构件本身自洽，属于「模型能读取」。它们不构成地面支持，也不是城市或演示域的基础接口。两张卡都明写这个问题未解决。

## 3. 改与不改

- **可以改（G 冻结后）**：每个 A 柱脚的地面以下基础件，或者逐脚缺失报告；局部演示域里的安装参数，即 assembly.json；端口 gallery-A:feet:ground@v1 的 local 值。范围以 LY-006 的 LY-067:write:001 为硬边界：local:gallery-A 里 x ±6.45、z ±3.824、y −0.6..0。新地坪件一律命名为 gp:LY-067:<name>。
- **不改**：gallery-A 三档 GLB 本体、柱网、楼板（顶面 y=4.0）；access-A 四个 GLB，包括木梯、平台和碰撞候选；B 三档（归 LY-068）；城市四块地面（地形差异片归 LY-089，开孔合成归 LY-090）；city-data.mjs、项目卡、资产卡（只能由 LY-100 写）。
- **不做**：整块展示底板；把示意线 palaces_connector_B 当成落位依据；宫区实名或绝对坐标。

## 4. 证据与未知

- 原始考古或原文：本轮没有核到复道柱脚、基础形制或尺寸的原始资料。仓库里 `evidence-geometry.json` 的 palaces_connector_B 是依据 gao2023_fig1 数字化的 **B 级示意线**，它自己写明「No elevated bridge or precise engineering alignment reconstructed」。`road-preconstraints.json:174` 也明确禁止据此造桥墩或坡道。
- 异地、异期类比：无。北魏、西汉长安和画像砖的材料都不拿来用。
- C 工程设计：A 的柱网 4.0 m × 2.2 m、柱础 0.50×0.50×0.20 m、柱 0.32 m、楼面 4.0 m，全部是现有模型的 C 推测值。
- 未知：复道的城市位置、所在宫区地坪高程、地基做法。stage-contract 写明 absolute_crs=null、geographic_origin=null。

五件事分开说：GLB 能读取，已实测；局部通行，卡上称楼板支持和 2 米头部射线已过，本席位没有复测；已入城，否，城中引用为 0；真实结构安全，无认证；历史复原，未成立。

## 5. 实测到的真实缺口（全部可重跑）

脚本都在本目录：`measure_footings.py`（sha256 b948421b…）、`bl_import_check.py`（96cf4847…）、`probe_ground.py`（5720bdb9…）、`check_feet.py`（b0e9948e…），以及第二轮新增的 `zone_check.py`（SHA 见 inputs.json）。

1. **16 个支点逐个定位**（`footings-A.json`）。A-F01…A-F16 排成 4×4 网格：x ∈ {−6, −2, 2, 6}，z ∈ {−3.3, −1.1, 1.1, 3.3}（glTF，米）。每个柱础 0.50×0.50 m，y 从 0.000 到 0.200；柱截面 0.32×0.32 m，y 从 0.200 到 3.800；柱底与柱础顶面间隙 0.000 m。LOD0/1/2 三档 16 个都一致。
2. **模型的最低面就是这 16 个柱础底面。** 全模型 min y=0.000，151 个连通件里只有这 16 个碰到最低面，合计接地面积 4.00 m²。GLB 里没有任何地面或底板（原展示底板已去掉）。也就是说，16 个支点在模型之外**没有任何支持**。Blender 5.2.1 独立导入复核：三档各有 16 个底面落在 Z=0，网格与上面相同（`bl-import-check.json`）。
3. **城市没有引用。** 在 city-data.mjs、app.mjs、city-renderer.mjs、scene.mjs、index.html、v1/* 和 data/** 里搜复道相关 ID，0 命中；researchModels 里也没有。没有 cityPlacement，所以「旧候选城市变换」在 bce3211 里不存在。
4. **宫区没有城市地面**（`probe-ground-connectorB.json`）。沿复道示意线取 5 个点，按 z=−y 和 z=+y 两种轴向解释各测一次，共 10 次竖直射线打四块地面：**0/10 命中**。对照组：C02-018、C02-019 两个院落点 2/2 命中 retained.glb，y=0.2；ground bbox 外的负例 0 命中。离示意线中点最近的地面三角，在 z=−y 解释下 44.3 m，在 z=+y 解释下 652.3 m。network-ground 的投影面积 130,648 m²，只占它 bbox（9,876,671 m²）的 1.32%，基本只铺了道路。按本项验收，这一条要报「旧城市地形缺失 → 依赖缺失」。注意：这只是探测，没有把复道放进城市。
5. **高程基准没定。** 城市地面顶面在 0.19–0.21 m（retained 为 0.2）。如果复道局部 y0 对齐世界 0，柱础会整块埋进铺面，顶面与 0.2 齐平；如果 y0 对齐 0.2，柱础就压在铺面上。两种都可能，要由 LY-005 和 LY-006 定，本席位不自己选。〔第二轮更新〕LY-005 的新件规则写的是「本地 y=0 = 本件接地面」，LY-006 写入区顶面也是 y=0，所以在 local:gallery-A 里，地面就是 y=0，柱础坐在地面上。世界坐标里取 0 还是 0.2 的问题只在落城时才会出现，而落城被 PZ-02 挡住了。所以这一条从「待定」改成「局部帧已定，世界帧不适用」。
6. **木梯接口对照**（`footings-B-access.json`）。access-A 平台顶面 4.0，与 A 楼面顶面 4.0 一致。access-A 有 4 个柱础，0.65×0.65×0.20，y 从 0 到 0.2；另有 2 块梯脚垫，1.00×0.65 m，y 从 −0.20 到 0，底面比 A 的 y0 低 0.20 m。所以演示域地面要么给梯脚垫留 0.20 m 的嵌入，要么这块交 LY-006 判归属。木梯本身不改。
7. **旧记录缺失。** 「16 个旧未命中支点」的原始清单（含当时的射线、变换和地形版本）在仓库和本机已查目录里都没有。逐脚对账只能用 GLB 重建出的这 16 个脚做「新」一侧，「旧」一侧需要协调者提供源包。

8. **LY-006 冻结的写入区只在地面以下**（`zone_check.py measure` → `zone-measure.json`）。`LY-067:write:001` 的范围在 local:gallery-A 里是 [−6.45, −0.6, −3.824]..[6.45, 0.0, 3.824]。16 个柱础的并集是 [−6.25, 0, −3.55]..[6.25, 0.2, 3.55]，全部落在写入区平面内；写入区比柱础外缘多出 x 方向 0.20 m、z 方向 0.274 m，顶面 y=0 正好等于柱础底面。所以本席位只能做「地面以下、贴柱础底」的基础件，不能往地面以上加任何东西，也不能改柱础，因为 6 个源对象在 LY-006 里都是 keep。
9. **防假底板的数量界限。** 写入区平面面积 98.66 m²，16 个柱础合计 4.00 m²，整块铺满就是柱础面积的 24.7 倍，这就是任务池说的「假展示大底板」。每脚基础件如果外扩 0.20 m（0.90×0.90 = 0.81 m²），相邻两件之间在 x 方向还留 3.1 m、z 方向留 1.3 m，不会连成一片；16 件合计 12.96 m²。`zone_check.py selftest` 跑了 5 个用例，结果都符合预期：P1 每脚 0.20 m 垫块通过；N1 外扩 0.25 m 出界、N2 铺满整区、N3 单块高出地面 2 cm、N4 一条垫两只脚，全部判 FAIL（`selftest-zone_check.json`）。
10. **登临节点：除梯脚垫外，还有 2 根梯帮伸到地面以下**（`zone-measure.json` access_A.parts_below_y0）。在 access-A 本地帧里，2 块梯脚垫是 [8.92..9.92]×[±0.505..±1.155]，y 从 −0.20 到 0；2 根梯帮（timber）是 x 3.27..9.49，y 最低 −0.130。第一轮只报了梯脚垫，这一轮补上梯帮。**access-A 相对 gallery-A 的装配变换不存在**：LY-006 的 frames 里没有 access-A 帧，两个 GLB 的节点都没有 TRS 或 extras 变换。所以「梯脚垫是否落进 LY-067 写入区」「平台顶面与楼面在同一坐标下是否差 0」两件事现在都测不了，要等 LY-069/070 或协调者给出变换。木梯本身受 LOCK-GALLERY-A 保护，不改。
11. **端口值要由本席位填写。** `gallery-A:feet:ground` v1 的 local/world/矩阵现在都是 null，状态是「declared (values filled by producer at delivery)」；容差为平面 0.005 m、高程 0.002 m，与 LY-005 的 E3 一致。world 帧名是 luoyang-local-schematic-v01，但 local:gallery-A 的 placement=null，所以交付时 world 只能写 null 并注明「未落位（PZ-02）」，不能编造。
12. 小注：第一轮的 `footings-B-access.json` 在 B 和 access 两个文件里也用了「A-F01…」作脚编号，那只是文件内的流水号，不是 A 的柱脚。对账一律只用 `footings-A.json` 的 A-F01…F16。

## 6. 依赖与开工条件（第二轮复核）

- G 的进度：LY-001、002、005、006、007、009 已交付（各自 status.json 写「交付完成」）；LY-008 有工作目录但没有 status.json，检查器 `ly_check.py` 的 SHA 在本轮两次读取之间变了（fda345d4… → 4beeaf57…），说明还在改；**LY-010 的目录不存在**。所以 G 还没冻结，本席位状态仍是「待输入」。
- 已经冻结、可以直接绑定的：写入区 `LY-067:write:001`、端口 `gallery-A:feet:ground@v1`、接缝 `…::LY-067->LY-069`、组件 `P067-footings`（fixed）、新地坪命名规则 `gp:LY-067:<name>`、高程容差 2 mm / 5 mm、坐标规则 world = N·S·v（只绕 Y 轴旋转，缩放 1）。
- 还缺：LY-010 给出的演示域，或 S-PALACE 的支持面（envelope 现在是 null，归 LY-070 所有）；access-A 到 gallery-A 的变换；LY-008 冻结后的检查器 SHA。
- 地域：LY-003 已交付「两宫复道不可落位」，LY-009 的 PZ-02 仍是 open。所以本席位的结果在任何情况下都只能是局部包，城市一侧必须报「依赖缺失」。
- 下游是 LY-069（消费本席位的端口）和 LY-070。地形邻居 LY-081、LY-089、LY-090 都是 S-CITYGROUND，与本席位没有写入重叠。
