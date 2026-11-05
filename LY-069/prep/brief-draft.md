# LY-069 复道端部宫门廊口兼容包：开工准备 brief（草案 v2）

状态：**待输入**。G 八席里 LY-001/002/005/006/007/009 已写「交付完成」，LY-008 没有 status.json，LY-010 目录不存在，所以 G 没有冻结。前件 LY-062/063/067/068 都只有 prep。本目录只做了读取、实测和测试准备，**没有制作或修改任何交付几何**。

基线：creation-notebook-lab main `bce3211f818ee5a8bef1773539da70695ba37b17`（只读，`git rev-parse HEAD` 复核一致）。

v2 相对 v1（2026-11-05 21:31）的变化：
- 按 LY-006 registry v1 的端口和写入区重新对齐了候选端接组合。
- 改正了 v1 的三处测量错误（见 §5「v1 更正」）。
- 新增候入院帧内的 K-W 试放实测。

## 1. 本项目标（按任务池原文）

选一个局部端接组合，验证**楼板、门口、屋檐、地面路线**是否连续。所有端点、门叶/屋檐和转向空间都要在同一坐标下实测。跨未知地区的连续复道**不生成**，未接端要记录。不铺「七里」，不把 B 关系线当精确路线，不为迎合模型改宫墙坐标。

本项类型是**复用装配**：不新造复道、登临节点、门卫或侧廊。

LY-006 registry 对本席位的登记（`LY-006/registry/seats.json`，SHA256 a1426412c84cab875713a63846fc9c487c6d01a9f8c445d5268c02187d959069）：
- site：S-PALACE；siteOwner：LY-070；role：assembly。
- 帧：`local:palace-composite`。zones.json 对它的说明是「composed frame defined by LY-069/LY-070; unplaced」。
- 写入区：`LY-069:write:001`，glTF 盒 [-6,-0.3,-6]–[6,9,6]，原点就是所选接点。
- 组件：P069-junction（fixed）。
- 不拥有任何源对象、地坪片、切孔或卡片字段。
- 产出端口：`gallery-end:junction:floor` v1，消费方 LY-070。
- 消费端口：
  - `gallery-A:feet:ground`（LY-067）
  - `gallery-B:landing:floor`（LY-068）
  - `sidehall:ends:floor`（LY-063）
  - `admission-court:side-opening-W:opening`（LY-062）
- 这些端口目前都是「declared (values filled by producer at delivery)」，local/world 值都是 null。

## 2. 核到的现有成果（GLB 字节 SHA256 = 提交 blob；inputs.json 46 件逐一重核一致）

| 资产 | 文件（docs/…） | SHA256 | 实测关键量（Blender Z-up，米） |
|---|---|---|---|
| 复道A LOD0 | library/models/m-luoyang-palace-gallery/files/gallery-A-LOD0.glb | 0c09279723e2334c35f21c7602c195cc867d97808ac0f99ccf6f0208d3ff3849 | 楼板 x±6.00、y±3.30，**楼面 z=4.000**。<br>16 柱位于 x∈{±2,±6}×y∈{±1.1,±3.3}，柱底 0.20；柱础 0.5×0.5×0.2，底 z=0。<br>楼面三条带净宽 **1.92 m**（x=±2 柱行），端部 x=5.95 处为 1.946 m。<br>檐出 x±6.45，梁底 3.80 |
| 复道A LOD1 / LOD2 | gallery-A-LOD1.glb / gallery-A-LOD2.glb | 227c3c4ecc2625629d00ef6beb274575587e4f1095f68b7a50359781e94b3e68 / cb26b56e1634f27a878d83997649804eaeef29f5a0bb1420b8aa959a65e137ea | 楼面同为 4.000 |
| 复道B LOD0/1/2 | gallery-B-LOD0/1/2.glb | c7cb279cfd1103158a3f93e071f2d56ba8a07de05c5d7422f26b9c3fe5a56a21 / fe72e192573df077335f7882fdd2d9db6e18ba3c1f05758e529f1e18ae2ddb08 / ff15e1c4ca8cb4f95a5ee486d9a53447b5a24a3671b7ec46c837b0572b9491f7 | 楼板 x±4.50、y±3.60，**楼面 z=3.500**；12 柱 |
| 登临A LOD0 / LOD1 | library/models/m-luoyang-gallery-access/files/access-A-LOD0.glb / access-A-LOD1.glb | c973d325d1d08cfd53c129df5270f6276677694a5d4a96cab35fde47d3d11076 / 7b5e26f443a1e1bcecd47c7e2072aaf00d2496c944afe6bfa4068ce72553834b | 平台 x 0–3.5、y±3.3，z=4.000。<br>**19 踏面 + 平台 = 20 踢**，每踢 0.200，踏深 0.32，梯宽 2.0。<br>最低一级踏面 z=0.2，前缘 x=9.58。<br>梯脚是**两块 1.00×0.65×0.20 土垫**（x 8.92–9.92，y ±0.505…±1.155，**z −0.20…0**）；帮木最低 −0.1302 |
| 登临A LOD2 | access-A-LOD2.glb | b39c34c28ab38963be7bc90ff2650eb6360eb71d4a1d16a294c76ab344809fd9 | **9 踏面 + 平台 = 10 踢 × 0.400**，踏深 0.64 |
| 登临A 碰撞候选 | access-A-collision-candidate.glb | 7327547eee27c4c0bb259b757de4533c95f640600c94882c24b881bd8b8a8209 | 19 踏面 × 0.200，与 LOD0 相同 |
| 候入院（闭） | cities/luoyang/progress-assets/palace-admission-court/palace-admission-court-closed-LOD0.glb（与 library 同名件字节相同） | 6ea892982b46e554bbe8c94ade9cb94ed94e3dbc6a8015b3bb963943d96500a8 | 庭地 new_court_support_C：x±34、y −67…20、z −0.2…0。<br>西侧廊 earth x −29…−18.1、y −51…−13，tile 4.44–6.33，北端檐到 y −12.2。<br>殿 earth x±17.5、y −16.58…12.5 |
| 候入院（开） | palace-admission-court-open-LOD0.glb | 59c8b758a5a2523105eac0e516e9961bf769bd5e422ba2913d292492ed45c4b0 | 同上，门叶开 |
| 值守切片 | library/models/m-luoyang-palace-guard/files/guard-slice-open-LOD0.glb / guard-slice-closed-LOD0.glb | 1ffc1c3118766d418dd5fbb08b5f4a9b8790643465cc29a1d7c76f0bb28e53f3 / 48c511c54010cc00b5a6262dc280cab2b1d0a7c13050d847fc5856e264ce82cd | 开门最小净宽 2.68、净高 2.84，门槛 0.10；闭门中缝 0.04 |
| 侧廊庑 | library/models/m-luoyang-palace-sidehall/files/sidehall-A-LOD0.glb | bd000b1bf36419eebe884dbe1c92368f30ceab7597290aa6eafdbdbd971e32c2 | 台面 0.45；端部无踏步（LY-063 实测 0.45 m 直落） |
| B 关系线 | cities/luoyang/data/evidence/evidence-geometry.json → palaces_connector_B | 完整值见 inputs.json（fa8b7002…） | B 类示意 LineString，约 377.69 示意米，`architectural_completion: not_modeled` |

城景加载情况：复道A/B、登临、门卫、侧廊、候入院 GLB **一件都没有被城景加载**。`grep -rE "palace-gallery|gallery-access|gallery-A|access-A|admission-court|palace-guard|palace-sidehall" docs/cities/luoyang` 只命中项目卡和 progress-assets 内部的 QA/source。城景只经 `v1/evidence-view.mjs:28` 加载含 B 关系线的 evidence-geometry.json，只画关系，不画建筑。

## 3. 改 / 不改范围（拟）

**改**（只在 workpacks/LY-069/ 内）：
- `assembly.json`：A → 登临A → 庭地 → 侧廊端口 / 西侧口的变换、端口和互斥规则。
- 接缝分类声明。
- 同坐标 QA 与未接端清单。
- 产出端口 `gallery-end:junction:floor` 的 local/world 值。

**不改**：
- 复道A/B、登临A 的源对象（keep，steward 是 LY-067/LY-068）。
- 候入院全部源对象（keep，owner 是 LY-061）的节点、几何、材质、矩阵。
- 宫墙/庭地坐标。
- city-data.mjs、项目卡、全站数据。

B 端在 LY-068 交付前不接。

## 4. 证据与未知

- **原始考古/原文**：本 prep 没核到任何能定复道端部、门口、楼面高度或走线的条目。road-preconstraints.json 第 174 行记着本轮原 PDF 文本检索没读到复道细节。B 关系线只说明两宫之间有联系。
- **异地异期类比**：无。北魏洛阳、西汉长安、四川画像砖都不能当约 180 年洛阳事实。
- **C 工程设计**：楼面 4.0/3.5、柱网、20 踢木梯、门口 2.68 m、侧廊台面 0.45，以及下文 K-W 放置参数。
- **未知**：复道实际走线和长度、端点在哪座宫门或廊、门口形制、城市地坪高程（LY-005 E1 写明 Y=0 只是工程零点）。

五件事分开说。本包最多做到「模型能读取」和「指定局部通行通过」。它不是「已入城」，也不证明「结构安全」或「历史复原成立」。

## 5. 实测缺口（脚本在 prep/scripts/，结果在 prep/out/）

- v1 脚本：ends.py、inventory.py、seam_portal.py、surfaces.py。
- verify_v2.py：SHA256 eebd9c50fb1e46971a5c81b558e02227c9b666f2e5f3d6aa3470924ea30a6d08，结果 out/verify-v2.json（b3b9f76a9221c6275ea557b3c3fe1f3838be940f1d006b3f4a87cb113ccc9c1a）。
- verify_v2b.py：SHA256 39e01fc71c6ef98a5db83bc5505ed6ab539ceab90f538a7f786268131c97a1fb，结果 out/verify-v2b.json（b80d84b17f23a27e1b7d4f0463dac0a295892bab136847ced7f2f265cfd2803f）。

### v1 更正（以 v2 为准）

1. **木构交体**：v1 报 dx=6.000 时有 0.00114 m³ 正体积交体，**v2 没有复现**。
   - 先按连通件 AABB 找出候选交区 [6.0–6.17]×±3.3×[3.88–3.90]。
   - 用 5 mm 网格加双向奇偶内点测试，同时落在两件内部的样点为 0。
   - 截面上，复道端梁尾顶面 z=3.90，登临搁栅底 z=3.92，中间有 2 cm 空隙。
   - 结论：木构只有接触/共面。v1 的数可能是 1 cm 网格在 z=4.0 共面处的奇偶误判，作废。
2. **土构交体**：不是 0.00235 m³，**而是 0.00275 m³**。
   - 来源是两处柱础重叠，每处 0.025×0.275×0.2：[6.225–6.25]×[±3.05…±3.325]×[0,0.2]。
   - 5 mm 网格 11000/11000 样点都在两件内部，属于正体积侵入。
   - 与 LY-070 的约 0.0028 一致。三角对 66 对（土 28、木 38），也与 LY-070 一致。
3. **梯脚**：v1 写的「1.00×2.31 m 落地垫、底 z=0」不对。
   - 实际是两块分开的 1.00×0.65 土垫，**顶 z=0，底 −0.20，埋入地下**，两块之间空 1.01 m。
   - 最低一级踏面前缘 x=9.58，之后直接落地。
   - 登临件**本身没有梯脚落地平台**，转向空间全部要靠外部地坪。
4. **梯级**：LOD0/1/碰撞件是 19 踏面 + 平台面 = 20 踢 × 0.200；LOD2 是 9 踏面 + 平台面 = 10 踢 × 0.400。与 LY-068 一致。

### 现行缺口

- **G0 楼板层不能直接接门/廊**：宫院节点里没有任何楼面在 4.0 或 3.5。门楼瓦顶 4.28，侧廊檐瓦最低 4.44，A 梁底 3.80。所以只能走「A → 登临A → 地面 → 门口/廊口」。
- **G1 A↔登临接缝**：dx=6.000 时，三条带（y −2.2/0/2.2）在 x 5.7–6.7 区间按 5 cm 步长取楼面顶，**全部为 4.000**，楼面连续。剩下的只有土构柱础 0.00275 m³ 正体积侵入，有两条路：
  - 由 LY-006 允许把它声明为合法局部接面，并逐件列出；
  - 改变换。但 v1 实测 dx=6.0675 时出现 6.75 cm 缝、0.10 m 落差，6/45 样本失败，这条路不可行。
  A 和登临A 都是 keep（steward LY-067），本席位不能改柱础。
- **G2 屋檐不连续**：A 檐出止于 x=±6.45。登临平台和梯段全部见天（91/91 条上射线见天）。K-W 中从梯脚到侧廊北端的 2.92–3.42 m 地面也见天。本包不补屋顶。
- **G3 转向空间**：
  - A 三条带各宽 1.92 m。
  - 登临平台上，外侧两带在 x≈9.04（A 帧）被栏杆挡住，只有中带接 2.0 m 梯。
  - 平台深 3.5 m，放得下 1.5 m 的 C 转向圆。
  - 梯脚没有自带平台，转向必须落在候入院庭地上。
- **G4 B 端**：B 楼面 3.50，比登临A 平台低 0.50 m；按 0.200 踢高要 17.5 级，不是整数，不能套用。LY-068 交付前，B 两端都是未接端。
- **G5 门口**：
  - 西侧口（LY-062:write:001，x −36…−34、y −16…−10）目前**只是 LY-061 外围上的一段 6 m 空档**。候入院外围现在 100% 敞开（LY-061 prep：1240 条外向内射线 0 遮挡）。
  - 门叶开闭件归 LY-062，还没产出，所以「门关后能否进入」现在测不了。
  - 负例只能用体宽测试，不能用中心射线。
- **G6 远档梯**：LOD2 踢高 0.40，不能作通行/碰撞依据，只认碰撞候选件。
- **G7 埋入与支持**：
  - A 的 16 块柱础底 z=0，放在庭地上是共面支持。K-W 试放的 22 个土件底面都有下向命中。
  - 登临A 的两块梯脚垫（共 0.26 m³）和帮木（到 −0.1302）**完全落在庭地平板体内**（平板 z −0.2…0）。要么切孔，要么声明合法埋入。
  - 庭地 new_court_support_C 的 owner 是 LY-061，本席位 cutZones 为空。
- **G8 未接端**：
  - A 的另一端（K-W 中为北端，y≈12，z=4.0 敞口落差）。
  - B 两端。
  - 两宫间整条联系：B 关系线约 377.69 示意米，按 A 段 12 m 约合 31.5 段，**不生成**。
- **G9（新）写入区几何约束**：K-W 中，A↔登临接缝在 y=Y0−6，梯脚垫南端在 y=Y0−15.92，两处相距 9.92 m。12 m 写入盒要同时装下这两处，又不能侵入 LY-063:write:001（y −13…−10），条件是 **Y0 ≥ 5.92**。实测 Y0=5.5 时梯脚到 −10.42，侵入 0.42 m。
- **G10（新）SHA 口径不一**：LY-006 registry 的卡片 SHA 用的是 CRLF 工作区字节。例如 m-luoyang-palace-gallery.asset.json，registry 记 0a310067…，提交 blob 是 100a78c3…；GLB 两边一致。绑定时一律用提交 blob，不一致项提给 LY-006/LY-100。

## 6. 候选端接组合 K-W（C 试放，只在内存里，待 LY-010 选定、LY-006 落帧）

在 local:admission-court（Blender Z-up）中：
- 复道A 原点放在 (Xc=−25.5, Y0=6.0, 0)，绕上轴转 −90°，A 的 +x 朝南。
- 登临A 放在 A 帧 +6.0 处，梯朝南下到庭地。
- 地面路线有两条：
  - ① 向南 3.42 m 到西侧廊北端：LY-063 `sidehall:ends:floor`，台面 0.45，目前是直落。
  - ② 向西 8.5 m 到西侧口 x=−34：LY-062 `admission-court:side-opening-W:opening`。

实测结果（verify-v2b.json）：
- 与候入院中庭地以外的节点**三角交叠 0 对**。
- 平面最小间距：侧廊 tile 2.28 m，侧廊 earth 3.08 m，殿 earth 4.18 m，殿 tile 5.66 m。
- 组合包围盒 x −29.32…−21.68、y −9.92…12.45、z −0.2…8.10，全部在庭地范围内。
- 与庭地的接触只有柱础共面支持，以及 G7 所述的埋入。
- Xc 取 −25.5 和 −26.0 结果相同（殿檐间距见 json）。

junction 原点拟定为 (−25.5, −4.0, 0)。这样写入盒是 x −31.5…−19.5、y −10…2，与 LY-063 区界相贴、不重叠。

这只是工程试放，不代表复道在候入院里有任何史据。选择权在 LY-010/LY-006。

## 7. 复用判定

没有可直接复用的「端接组合」成果：bce3211 里没有 A↔登临、登临↔门口/廊口的装配记录或 QA，LY-070 的 prep 也独立核到同一结论。可复用的只是各原件本体，全部引用原件，不复制，不重新登记。
