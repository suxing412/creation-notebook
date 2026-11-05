# LY-065 测试计划（按「本项验收」，制作时直接跑）

本项验收原文有三条：维护接口不挡原主阶和柱网；所选 A/B 原型准确保留；未知的上层用途不被转成已认证通路或御用设施。

## 0. 绑定

- 原型输入要等 LY-010 选定后只绑一套。
  - A：`77369980…f061b5ae`（LOD0）、`6f605ed7…3460`（LOD1）、`134b0375…2d452d`（LOD2）。
  - B：`6ef34781…35d`、`d9a73c76…b00368`、`1fd99998…754ad`。
  - 全称见 `inputs.json`。
- 基线测量：`measure/hall-{A|B}-LOD{0,1,2}.json`，SHA 见下表。脚本 `scripts/measure_hall.py`，sha256 `bef00a1f5a9aa3d67b1e362456465c16faca542c33c12a5b0f647406c9c18d1f`。

| 基线文件 | SHA256 |
|---|---|
| hall-A-LOD0.json | 5aa009789e4152755a20bb2fd50089c666d5976de53ff54c2b091e41eff9fdac |
| hall-B-LOD0.json | ca041c93ac6497a9f505bb8e93b9aabaa9791f85f39485037d648a504e4b753f |
| court-open-LOD0.json | d8f5f0055b5a7d80a47c9f5e403106a519050429c63b0f7e96300b5583156b16 |

- 每次运行都记录被测 GLB 的 SHA、Blender 版本、脚本 SHA。不绑 SHA 的结果作废。
- 运行命令：`D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P <script> -- <glb> <out.json>`

## T1 原型保留（阻断级）

- **正例**：在装配输出里，原型的三个节点 `*-static_earth/_timber/_tile` 和原 GLB 做有向三角形双射比对，位置、法线、UV 误差都是 0，容差 ≤ 2e-5 m（沿用宫院组合复核的口径）。材质和嵌入贴图字节相同，节点矩阵是单位阵或 LY-006 冻结的那一个矩阵。
- **负例**：把 earth 某个顶点移动 1 mm 后重跑，必须判失败。
- **互斥**：输出中只出现所选那一套的节点名，没有 `deyang-{另一套}-*`。A/B 叠载判失败。

## T2 主阶与柱网不被挡（阻断级）

- 主阶踏面必须保持原样：A 是 11 个踏面加台顶，每级 0.15 m；B 是 14 个踏面加台顶，每级 0.14 m；x 在 [−3.5, 3.5] 之间，Blender y 方向分别是 A [−16.58, −12.84]、B [−17.0, −12.24]。用重跑 `measure_hall.py` 的输出对照 `front_stair` 和 `earth_up_tiers`。
- 新件和主阶包络（x ±3.5，前缘外 0.5 m、台顶以上 2.2 m 的盒）求交，正体积必须为 0。
- 柱网不能变：A 的 x 轴线是 ±14、±8.4、±2.8，y 轴线是 ±9、±3；B 的 x 轴线是 ±16.8、±12、±7.2、±2.4，y 轴线是 ±8.4、±2.8（Blender 坐标）。新件到最近柱表面的水平净距至少 0.30 m；柱础边 A ±14.38、B ±17.18 不能被覆盖。
- **负例**：故意把一个新踏步放在 x = 0 的前廊上，或者贴住角柱，T2 必须报失败。

## T3 侧/后台缘实际连通（本项核心）

- **基线**（未装时）：`ascent_tiers_by_side` 只有 `front(-y)` 一项；`outside_edge_support_0.30m` 的左、右、后都是 0/31。装配以后，这个基线状态必须仍然可以从原型单独复现。
- **正例**：每处声明的侧口或后口，都要从 z = 0 的地坪连续通到台顶（A 1.80 m，B 2.10 m）。
  - 每级高差不超过所选主阶的级高：A 0.15 m，B 0.14 m，容差 ±0.005 m。坡道坡度另行声明。
  - 净宽至少等于声明宽度，用有限身体包络盒检查：宽 0.6 m、高 1.8 m、厚 0.3 m。
  - 足下支持：每个踏面不少于 9 根下打射线，全部命中新件或地坪；和台顶交接处没有缝，缝隙 ≤ 0.2 mm。
  - 到台顶后进入侧/后带的净宽 ≥ 3.12 m（实测值），包络不碰墙、柱、柱础。
- **负例**：
  - 删掉一级踏步，必须测出高差 > 0.15 m（A）而判失败。
  - 把口子放在侧墙正前方并留 0.1 m 缝，必须报支持失败。
  - 侧带内的身体包络往墙内推 0.1 m，必须检出墙体侵入。
- **组合语境**（只有 LY-010 选择装入宫院组合时才跑）：新件 y > −11.2，侧廊瓦面 (|x| ≥ 18.191, y ≤ −12.2, z ≥ 4.44) 到新件包络的距离不少于 0.5 m；新件底面与 `new_court_support_C` 顶面 z = 0 是合法接面，不算正体积侵入。原组合 99 个有限带、73 条邻接重跑，结果不变。

## T4 检修接点

- 接点只能是端口或落足地坪件，要声明 ID、坐标、法线和用途，用途只写"C 维护落足/检修端口"。
- 接点位置：在台缘带内、檐口滴水线以内（A |x| ≤ 16.0 或 y ≤ 11.0 的那一侧；B 对应 18.8 / 10.4），或者明说放在滴水线外的露天带上。檐口高度按台顶以上 A 7.02 m、B 7.42 m 记录，不声称梯子可以登顶。
- **负例**：接点卡片或元数据里出现"登楼""上层""御""宿卫路线""后门"这类字样，判失败（grep）。

## T5 未知不被认证（阻断级）

- 重跑 `upper_walkable_faces_gt4m2` 字段：新件不能在台顶 2.5 m 以上增加任何朝上面积大于 0.5 m² 的面，也不能有任何构件通到墙顶（6.8 / 7.1 m）或梁顶（8.89 / 9.59 m）。
- 侧墙和后墙的 `enclosure_openings` 在 +0.5、+1.0、+1.6 m 三个高度的深穿采样必须和基线完全相同（A 侧 54/200、后 38/200；B 侧 57/200、后 32/200），也就是不允许开门。
- 卡片和 assembly.json 里，宫名、殿位、院界、仪礼路线字段为空；evidence 四类分开写；台缘防护如果没做，就写"未做"。

## T6 三档与交付底线

- 每档 GLB ≤ 15,000,000 字节；LOD2 不能是 LOD0 改名，三角形数必须不同。新件材质要有语义名，纹理内嵌，UV 存在，没有退化三角形。
- 安装和撤回：装上再撤掉以后，原三个节点逐字节哈希与输入一致，场景里没有残留节点。
- `python -I lab/tools/build_assets.py --check` 只在 LY-100 的隔离检出上跑。本席位不跑。
- 预览：同一机位拍前后对比、背面和侧口剖面，都标明 CPU 渲染（mq/render.py）；不声称 GPU 或手机测试。

## T0 契约与写入区（阻断级；LY-006 registry 绑定，开工前和交付时各跑一次）

- 绑定：`LY-006/registry/zones.json` `6b3595ac…`、`seats.json` `a1426412…`、`ports.json` `28bcfb68…`、`ownership.json` `ecbbbcf5…`。如果 LY-006 发了 v2，换成 v2 的 SHA，并在 brief 里记下版本号。
- **写入区包含**：每个新件的全部顶点都在 `LY-065:write:001` 盒内，容差 0.05 m（LY-006 brief 第 35 行）。用 `scripts/zone_fit.py <新件GLB> <out> '<v2 盒 JSON>'` 检查，读 `objects.*.verts_inside_zone == verts`。
  - **当前 v1 的预期结果**：任何接到台顶（A 1.80 / B 2.10）的件都会失败，因为 v1 上限是 1.6 m。这正是要申请 v2 的理由。拿不到 v2，T0 判阻断，不交几何。
- **只读节点不动**：输出 GLB 中 `deyang-{A|B}-static_*` 的 mode 是 keep，T1 逐三角比对为 0 差。
- **端口填值**：`deyang:maintenance-edge:floor` v1 要填 `local`（local:deyang 坐标）、`nodeMatrixColumnMajor` 和 `measuredFrom`（被测 GLB 的 SHA256）。`world` 保持 null，因为 local:deyang 的 placement 是 null（port.schema.json 第 30 行）。port.schema 校验必须通过。
  - 负例：给 world 填一个非 null 值，校验必须失败；measuredFrom 缺 SHA，也必须失败。
- **所有权负例**：输出里出现 `hall__deyang-A-*` 或 `new_court_support_C`（这些归 LY-061），或者任何宫院组合文件路径，判越界。
- **互斥**：只出现 LY-010 选中的那一套前缀，另一套出现即失败。

## T7 检查器调用（LY-008 冻结后用冻结版本）

```
python -I <LY-008>/source/ly_check.py --json qa/ly-check-LOD{N}.json glb models/<新件或装配>-LOD{N}.glb --profile ly-p01 --lod {N} --tex-manifest <LY-007>/textures/manifest.json
python -I <LY-008>/source/ly_check.py --json qa/ly-check-lodset.json lodset <LOD0> <LOD1> <LOD2>
python -I <LY-008>/source/ly_check.py --json qa/ly-check-package.json package <LY-065 包目录> --glb-profile ly-p01 --tex-manifest <LY-007>/textures/manifest.json
python -I <LY-008>/source/ly_check.py --json qa/ly-check-privacy.json privacy <公开目录>
```

- **正例**：errors 为空。
- **原型基线**：`baseline/ly-check-*`（检查器 `fda345d4…`，未冻结版）中，六份原型 GLB 全部 OK。B 的 lodset 有继承警告 `LOD_TRI_RATIO` 0.636，这条只能原样披露，不能当成本席新增，也不能为了消掉它去改原型。
- **负例**：新件 LOD2 直接复制 LOD0 改名，lodset 必须报错或警告。在新件里注入一个 NaN 顶点，glb 必须报错（复用 LY-008 negatives 的注入方式）。
- 报告里要写明检查器 SHA。如果 SHA 和 LY-008 的冻结 SHA 不一致，结果作废。

## T3 补充：写入区几何约束（v1 实测，v2 下可能改）

- 台外余量：A 左右各 4.8 m、后 1.4 m；B 三侧各 2.0 m。
- 直跑水平长度：A 2.25–3.3 m，B 2.75–3.9 m。
- 新件方向检查：除 A 左右侧以外，梯段必须平行台缘。梯段宽度（垂直台缘方向）不超过所在侧余量减 0.05 m。
- **负例**：在 A 后侧放一段垂直台缘、长 3.3 m 的直跑，T0 必须报越区（z < −13.9）。
- 组合语境：本席不在组合里装。宫院组合层面的检查（侧廊瓦面净距、`new_court_support_C` 接面）交给 LY-070 跑。本席只提供端口值和新件包络。
