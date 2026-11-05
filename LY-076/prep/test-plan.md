# LY-076 测试计划（制作时直接跑）

脚本都在 `prep/scripts/`，运行方式：`D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P <脚本> -- <参数>`。后处理用 `python -I`。
网格步长 0.1 m。身体参数：r = 0.25 / 0.30（基准）/ 0.45 / 0.55，迈步上限 0.21 m（0.15 缺口踢面和 0.20 台阶踢面可以过，0.30 地坪踢面过不去）。这些是离散检查，**不等于**连续人体步态、承载或规范认证。

## 要绑定的 SHA

- 修订前（基准）：LOD1 `ffaff723c6a0c77a514d0a56fb03fad55fdbf0d880e3ee614887551884c6de0f`、LOD2 `134ca945603a696a8dc164087a8fc3334a8a1e1b57b4439ae2b97fab2803b4cc`；近景源要么是重建件（产出时登记 SHA），要么是找回的 26,176,944 B 原件（登记 SHA）。
- 回退和互斥对照：quality-v1 LOD1 `515ffbbb…a7ce`、近景 `f5fdc18a…e081`、城景投影 `c1b58de1…fe85`。
- 新件：LY-076 交付的 near/LOD1/LOD2 各自的 SHA，每一份 qa JSON 都要写明所测文件的 SHA。
- 基准测量结果：`out/risers-card-LOD1.json` `2a4d9cbf…e6ff`、`out/posts-card-LOD1.json` `17cbdacd…c5a1`、`out/analysis-card-LOD1.json` `e61f60e9…1a15`、`out/geodesic-card-LOD1.json` `704e8157…54bc`。

## G 冻结后要接上的标准（2026-11-06 读到的 G 输出，只读）
- 端口 `lingtai:edge:ground`（LY-006 ports.json `28bcfb68…`）：交付时要把 local 和 world 两个坐标、节点矩阵、measuredFrom 都填上。验收容差：位置 ≤ 0.005 m，高程 ≤ 0.002 m。
- 写入区 `LY-076:write:001`（zones.json `6b3595ac…`）：新件三角全部在 [−34,−0.3,−34]..[34,6,34]（glTF）以内，并且在 T1 五个排除盒以外。这两条都满足才算合规。
- `LOCK-LINGTAI-STEPS`（LY-009 locks.json `5eb5ae32…`）：锁内路径不许被覆盖。负例：如果包里的文件路径落在 `docs/library/models/m-luoyang-lingtai/**`，又与锁内 SHA 不同，判越界。
- LY-007 lod-rules（`fbf53757…`）：通行和接触检查只认 LOD0 的结果；夯土类 LOD0→1→2 不变；文件名和节点名沿用 `lingtai-A-LOD<n>.glb` / `lingtai-A-static_<mat>`。
- LY-010（未交）：选定方案和允许的未验项，以 LY-010 为准；在它交付之前，本计划不能执行到「交付」。

## T0 读回与预算
- 官方式检查器（LY-008 `ly_check.py` `39aaa491…`）：
  ```
  python -I D:/GitHub/creation-notebook-workpacks/LY-008/source/ly_check.py --json qa/ly008-glb.json glb --profile ly-p01 <near> <LOD1> <LOD2>
  python -I D:/GitHub/creation-notebook-workpacks/LY-008/source/ly_check.py --json qa/ly008-lodset.json lodset <near> <LOD1> <LOD2>
  python -I D:/GitHub/creation-notebook-workpacks/LY-008/source/ly_check.py --json qa/ly008-privacy.json privacy <包目录>
  ```
  基准（ffaff723 / 134ca945）的结果：base 档 0 error 0 warning；ly-p01 档只有一个 `LY_NOT_GROUNDED`（最低点 y=−0.30，继承下来的），见 `out/recheck/ly008-glb-*.json`。
  新件允许保留这个继承 warning，但最低点不能低于 −0.30。只要新出现任何 error，或者新出现 base 档 warning，就判失败。
- lodset 比例（LOD1/LOD0 0.17–0.62，LOD2/LOD0 0.05–0.20）：基准用 qv1 近景作代理，比例是 0.056 和 0.005，本来就低于下限。
  - 如果 lodset 报的就是这一项，如实记为「继承偏差」，并给出与基准相同的比例。
  - 如果新件让比例变得更差，判失败。
- 正例：三档 GLB 都能导入。无退化三角，位置和 UV 有限，每个图元都有 UV0，材质在 4 种语义之内（earth/path/timber/tile）；单个 GLB ≤ 15,000,000 B。
- 近景单独登记字节数。如果超预算，如实标注「不上架」，**不许降低近景细度去凑预算**。
- 负例：LOD1 和 LOD0 的三角数相同，或 LOD2 是 LOD1 改名，判失败。

## T1 五处已修踏步不变（排除清单）
- 用 `tri_dump.py` 和 `step_regions.py`（基准 = ffaff7…）：五个盒区内的土/路面三角，新件与基准逐三角相同（容差 1 mm）。盒区为 X-W x[−16.6,−16.15] y[−0.85,0.85]，X-E 与之对称，X-N x[−0.85,0.85] y[14.95,15.4]，X-SW x[−7.85,−6.15] y[−16.6,−16.15]，X-SE 与之对称。
- 用 `notch_skin.py`：上部覆盖必须是 0/45，下踢面 30/30。
- 负例：把任一缺口还原成 qv1 的平地坪（比如拿 515ffb 来测），T1 必须报错。

## T2 改动三角范围可核
- 用 `tri_diff.py 基准 新件 earth,path` 和 `tri_diff.py 基准 新件 timber,tile`：列出新增/删除簇的包围盒。所有簇都必须落在 assembly.json 声明的改动盒区里（每边容差 0.05 m）；在声明区以外出现任何簇，判失败。
- 北殿瓦作和屋面三角（`timber,tile` 类，y>14.5）必须与基准相同：旧屋面不回退，北殿那 24 个三角的材质归属也不变。

## T3 台缘支持
- 用 `post_support.py`：针对 assembly 选定的柱，柱脚支撑率 ≥ 0.999，柱脚下最大空隙 ≤ 0.01 m。
- 基准是 20/80 根柱只有 0.459–0.541 的支撑。没纳入改动的柱照原样报告，不许被算作通过。
- 支撑集只取朝上的水平土面（法线 z>0.99），**不包括 infill**。原因：卡片把 infill 并进了土材质，会把北殿端柱虚报成 0.672。
- 负例：拿基准 ffaff7 跑，那 20 根柱必须报失败。

## T4 新台缘或绕行件的支持与踢面
- 用 `raster.py`、`riser_inventory.py`、`analyze.py`：新件的每一级踢面 ≤ 0.21 m（如果 LY-008/010 另有标准，按其执行）。踏面进深 ≥ 0.30 m。新踏面和原地坪之间不能有超过 0.01 m 的缝，也不能双层覆盖（同一 xy 出现两个支撑面、相差在 0.005–0.05 m 之间，判失败）。
- 用 `analyze.py` 的 `riser_edge_length_total_m` 检查 0.30 踢面总长：在基准 245.6 m（几何口径）的基础上，只能减去声明的改动长度，不许出现别处凭空变化。

## T5 选定绕行点的通行（以 G2 为例）
- 用 `geodesic.py`：从南门外 (0,−33.5) 到 (6,−14)。
  - 基准：r0.30 = 22.8 m；r0.45 = 34.3 m，窄通道不通。
  - 方案目标：要么在 r0.45 下也能穿过窄通道，要么明确写成「保持 1.0 m、受阻」。窄通道内点 (2.3,−18) 的可达性逐档报告。
- 负例：r=0.55 时必须如实报告结果，不许改参数来变绿。
- 中心射线或离散点的结果不能写成连续通过。

## T6 不回退
- 用 `analyze.py` 检查可达性：在 r0.30 / 迈步 0.21 下，五座廊地坪的可达单元数 ≥ 基准（西 8236、东 8236、北 13836、西南 3192、东南 3192），台顶 48508。
- 主台阶 30 级、踢面 0.20，三角不变。

## T7 北侧绕行限制保留
- 用 `geodesic.py`：北门外 (0,33.5) 到北殿踏面 (0,15.17)，r0.30 必须仍是 40.8 m ± 0.3 m；到 (0,18) 必须是 43.3 m ± 0.3 m。
- 用 `analyze.py` 的 transects：`x=0` 和 `x=7` 两条北向剖线的地面段（3.0 m / 12.96 m / 10.75 m）、`x=15.1` 剖线不变。
- 北殿后檐 y=21 踢面长 28.0 m 不变，后墙 infill 不变。
- 负例：如果北侧出现新开口或者被加宽，T7 必须失败。

## T8 低档不能替代近景
- T1 到 T7 要分别在 near（重建件或原件）、LOD1、LOD2 上各跑一遍。只给出 LOD1/LOD2 结果的，验收记为「近景未验」。
- 三档之间土/路面几何要一致（基准 LOD1 与 LOD2 相同），或者列出差异。

## T9 安装与撤回
- 在严格输入（ffaff7 / 134ca9 / near）上叠装差异件，再撤回；撤回后的结果必须与原 SHA 逐字节一致，或者三角逐个一致，并写明是哪一种。
- 新旧方案不能同时加载（A/B 互斥，LOD 互斥）。
- 不碰城景 `city-data.mjs` 和资产卡，这些交给 LY-100。

## 已知局限（如实写进 qa）
- 网格 0.1 m。净空只采了 3 个高度。headroom 是单条射线。
- 在土材质合并之后，柱的识别依赖「焊接后的松散部件 + 尺寸」启发式。
- 没做 GPU 或手机测试。
