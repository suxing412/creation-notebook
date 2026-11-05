# LY-061 测试计划 v2（制作完成后直接跑）

本项验收原文：**外围无未声明漏洞；转角和基脚与原庭地吻合；原殿廊不重造；未指定的宫址或殿名没有偷偷写进卡片。**

v2 按 LY-006 registry v1（zones.json `6b3595ac735d180866e823ddeb4e3676ffc0e816d083f6be2d57d6e4df0821c0`）的写入区改写。如果 LY-006 出 v2，先重算 T0 再跑其余各项。

## 绑定 SHA（输入，制作前后都必须不变）

| 文件 | SHA256 |
|---|---|
| palace-admission-court-open-LOD0.glb | 59c8b758a5a2523105eac0e516e9961bf769bd5e422ba2913d292492ed45c4b0 |
| palace-admission-court-open-LOD1.glb | d95bd22f9317683ece8b8d14a6d4a6719522e47c8410f976e064708890148281 |
| palace-admission-court-open-LOD2.glb | 01b2017fac9d8ee6190726d233973c9b048936ce76b3ec7da8fb91aedec3a33d |
| palace-admission-court-closed-LOD0.glb | 6ea892982b46e554bbe8c94ade9cb94ed94e3dbc6a8015b3bb963943d96500a8 |
| palace-admission-court-closed-LOD1.glb | 455a12153d4132d2b653cdf8bbcf4b4994a5c33451efc1ec16119ebbf21453d2 |
| palace-admission-court-closed-LOD2.glb | 108e28a567dcef237868b2414332ae51925686d256891736355a5b40d9c0101d |
| LY-006/registry/zones.json | 6b3595ac735d180866e823ddeb4e3676ffc0e816d083f6be2d57d6e4df0821c0 |
| LY-006/registry/ports.json | 28bcfb68cd7d7fe0026f62de23ae3e45ba8f714a139e38c0b0957039f12fc633 |
| LY-005/coordinate-contract.json | b6d7fe9db9523569383bf656df39aef63e7d80e8a1d5877196ba0bcab8747712 |
| 门卫、侧廊、殿堂原件 | 见 prep/inputs.json |

每份 QA 报告都要同时写出两组 SHA：外围件三档的输出 SHA，以及上表的输入 SHA。所有检查都在「原组合 GLB + 外围叠加 GLB」同场导入后进行，开门和闭门各三档，共 6 组。坐标换算一律用 Blender (X,Y,Z) = glTF (x,−z,y)。

## T0 写入区约束（新增，最先跑）
- 外围件的每个三角都必须完全落在 LY-061:write:001..007 的并集内，允许外扩 1 mm。
  - 判法：每个顶点都在至少一个区盒内；跨区的三角，要求在两个区的公共面上都有顶点。
  - 负例：手工把一个顶点移到 x=−36.01，必须报错。
- 外围件与 LY-062:write:001..003、LY-063:write:*、LY-064 的区盒做 SAT 三角-盒相交检测（`zone_check.py` 的同一函数，内缩 1e-4 m），结果必须为 0。
- 墙顶最大 z ≤ 6.000，墙底最小 z ≥ −0.300，容差 1 mm。

## T1 输入不变
- 6 份组合 GLB 及全部原件重新算 SHA，必须与上表逐字节相同。
- 同场导入后，原 26 个节点（16 个网格）的世界包络、三角数和材质名与 `prep/out/measure-open-LOD0.json` 中的 nodes 逐项相同，容差 0。
- 外围件不得出现与原节点同名的节点。
- 外围件不得含原几何的副本。判法：有向三角加位置哈希，与原 16 个网格的交集为 0。
- 重跑 `zone_check.py`，原几何在 LY-061 七个区内的侵入三角数仍为 0（基线：三份资产都是 0）。

## T2 外围闭合，没有未声明的漏洞
- **开口清单**：由 assembly.json 给出，必须**恰好**是三项，内容与 LY-062 的区盒一致：
  - 西侧口 x −36…−34、y −16…−10；
  - 东侧口 x 34…36、y −16…−10；
  - 南口 x −3…3、y −69…−67。
  每项宽 6.00 m，容差 ±0.01 m。
- **外向内水平射线**：沿外围中线外侧 0.6 m 一周取样，每 0.25 m 一个点，高度取 0.3、1.0、1.6、3.0、5.5 m；射程超过墙厚 0.1 m。
  - 正例：开放样点只出现在上述三段开口内。
  - 负例：开口以外的开放长度必须为 0.00 m（基线是 310 m 全开）。
- **转弯路线**（连通性搜索 BFS）：身体包络 0.8 m × 1.8 m，0.25 m 栅格。
  - 封住三处开口区盒后，外部可达集与庭内可达集的交集必须为空。
  - 只开其中任意一处，两者必须连通，用来证明开口真的通，不是被墙堵死。
- **缝隙**：墙段之间、墙与角块之间的缝 ≤ 2 mm。缝 > 2 mm 且 0.10 m 探针能穿过的，算漏洞。
- **人为破坏负例**：测试场景里删掉一段 2 m 墙，T2 必须报出这 2 m，而且报出的位置要对。
- **门线声明检查**：重跑 `gate_line_leaks.py`。值守单元内的 6 条直通口 ±(5.10–6.05)、±(3.45–4.50)、±(2.10–3.15) 与两翼 ±6.85…±34 必须保持基线宽度（容差 0.05 m），证明外围没有偷改门卫。它们在 assembly.json 中必须登记为「内部路径、不属外围」。
- **声明文字**：assembly.json 必须明文写出「闭门 + 南口开 = 组合可从两翼进入」。缺这句判失败，因为它对应 LY-062 的开闭测试。

## T3 转角、基脚与原庭地吻合
- **转角**：四个角块各沿 45° 和两条边方向打射线，高度从 0.1 m 起每 0.5 m 一层直到墙顶，都不得穿出；角缝 ≤ 2 mm。
- **内皮共面**：墙基内皮与平板侧面（x=±34、y=−67、y=20）在 z −0.2…0 段共面接触。
  - 间隙 ≤ 1 mm。
  - 正体积侵入平板 ≤ 1e-6 m³。
  - 「完全包含」为 0。
  - 接触按三类分别计数：合法局部接面、正体积侵入、完全包含。
- **墙内脚高程**：墙内脚顶面（若有散水或踏面）与平板顶面 z=0.000 的高差 ≤ 1 mm，或者在 assembly.json 中声明为台阶。
- **基脚支承**：沿墙底每 0.25 m 向下打射线。
  - 墙底如果在 z<−0.2 处伸出平板以外，下方必须是外围件自带的基脚或垫层实体。
  - 垫层以下的地形，按 LY-005 届时冻结的墙外基准登记，在 QA 中如实写成「本局部帧无地坪，基准为 C」。
  - 基线：平板外 1,244 个下向样点命中 0 个。
- **原平板下方**：外围件不得伸到平板下方（x 在 ±34 以内且 z<0），否则判侵入。

## T4 原通行不退化
- 原 finite-routes 的 99 条带（0.8 m × 1.8 m）和 73 个接口，在加了外围的组合上逐条复跑。私密检查器（bf82ede6… / ec77a791…）不在本机，所以用 prep 从 GLB 重建的等价脚本，并标注「从 GLB 重建」。
  - 正例：全部 supports=true，且 surface_hit_count=0。
  - 负例：`negative_hall_column` 和闭门中央通路仍然被挡。
- `outer_ground_join`（x ±0.4，y −66.5…−65）往外延 2.5 m 到 y=−69 后必须仍然畅通，即穿过南口区盒时不碰外围件。

## T5 历史身份与卡片
- 在外围件、assembly.json 和任何卡片草案里检索：「德阳」「玉堂」「南宫」「北宫」「阊阖」「东掖」及宫门实名。
  - 只允许出现在 provenance 或排除项字段里。
  - 在 title、summary、节点名中的命中数为 0。
- historicalPalace、cityPlacement 必须为 null，cityInstalled 必须为 false。
- 不写 city-data.mjs 和 p-luoyang.asset.json，改动只作为提案交 LY-100。
- 证据栏写明：墙线来自 LY-006 的 C 分区，墙厚、墙高、基脚、转角都是 C；《后汉书·百官二》不支持任何围墙形制。

## T6 公共质量底线
- 每份 GLB ≤ 15,000,000 字节。三档各自独立导出，不得把 LOD0 复制改名成另外两档。
- 米制，原点与组合相同。纹理内嵌，UV 无缺失，退化三角 0，数值全部有限，有法线，墙体闭合且绕序一致。
- 填写端口 `admission-court:enclosure:wall-end` 的 local 值：6 个墙端面的中心和法线。容差为 position 0.005 m、elevation 0.002 m（照 ports.json）。每个端面必须与对应的 LY-062 区盒面共面，误差 ≤ 1 mm。
- 安装与撤回：只装外围件，跑 T0–T4；撤掉外围件后重跑 T1，结果必须与基线逐字节一致。新旧方案不得叠载。
- 在隔离副本里跑 `python -I lab/tools/build_assets.py --check`，以及 LY-008 冻结后的检查器。不得在只读的 lab 主仓库里跑。
- 预览：四个转角、三个开口端面、南前庭带各出一张同机位前后对照图和一张剖面图，用 mq/render.py 渲染，并注明 CPU 渲染。没有做过 GPU 或手机测试，就不写已测。

## 机器可读阈值
```
T0.out_of_zone_tris == 0 ; T0.foreign_zone_tris == 0 ; T0.zmax <= 6.001 ; T0.zmin >= -0.301
T2.declared_openings == 3 (each 6.00±0.01 m) ; T2.undeclared_open_len_m == 0.00 ; T2.bfs_sealed_cross == 0 ; T2.seam_gap_mm <= 2
T3.slab_face_gap_mm <= 1 ; T3.slab_penetration_m3 <= 1e-6 ; T3.footing_support_failures == 0 ; T3.under_slab_tris == 0 ; T3.corner_gap_mm <= 2
T4.routes_pass == 99/99 per asset ; T4.interfaces_pass == 73/73 ; T4.negatives_blocked == true ; T4.outer_join_extended_clear == true
T5.name_hits_in_title_summary_nodes == 0 ; T6.max_glb_bytes <= 15000000 ; T6.wall_end_ports == 6 (coplanar <= 1 mm)
```
