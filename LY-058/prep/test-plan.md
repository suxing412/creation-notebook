# LY-058 test plan（以后制作时直接跑）

前提：G 冻结；LY-055、LY-056、LY-057 已交付并给出 SHA；LY-010 选定样板；LY-005 给出院地坪标高；LY-008 给出阶差和身体容差。下面 `<COURT>` 指 LY-057 交付的原谷物院 LOD0。如果 LY-001/010 改判以 workyard 作替代，就用 `workyard-LOD0.glb`（7eb9739e…）。

## 0. 绑定 SHA（任何一项不符就停）

- 输入院：`<COURT>` 的 LOD0/1/2 SHA 等于 LY-057 delivery-manifest 所列值，并且**不等于** workyard 的 7eb9739e / 6baefbd0 / 574d81d9（除非 010 书面改判）。
- 足碓：LY-056 交付件的 SHA；若沿用原模块，则为 6f0e4183（LOD0）。
- 脚本：measure_yard.py、analyze_route.py、compare_pestle.py 的 SHA 写入 qa 报告。
- 城市基线：开测时最新 main 的 `city-data.mjs` blob SHA，供安装/撤回比对。

## 1. 读取与身份（正例 / 负例）

- T1.1 `python glb_nodes.py <COURT LOD0/1/2>`：三档节点、材质语义齐全；动件（杵）是独立节点。
- T1.2 负例：把 workyard-LOD0 当 `<COURT>` 输入时，身份检查必须**失败**（SHA 不在 LY-057 清单里）。
- T1.3 `python compare_pestle.py <COURT> <LY-056 pestle>`：嵌入件与 LY-056 交付件的三角集合在 1e-4 m 内一致，或者给出明确的替换映射。

## 2. 栅格可达（每档 LOD 各跑一次）

```
blender -b --factory-startup --python-exit-code 1 -P measure_yard.py -- <COURT LODn> out/court-LODn-s10.json 0.1 1.5
python analyze_route.py out/court-LODn-s10.npz out/route-LODn.json <STEP_MAX from LY-008> 0.20
```

- 参数：HEAD 2.0 m、BODY_R 0.30 m、FOOT 0.15 m；STEP_MAX 以 LY-008 冻结值为准。LY-008 未给值时报告两档 0.20/0.25，不自选。
- 探点：来料点、舂作位（石臼侧、踏台后端）、扬谷区中心、暂存区中心，按 assembly.json 的端口坐标改写 `PROBES`。
- T2.1 正例：门外 → 来料 → 石臼侧 → 扬谷区 → 暂存，每段 `widest` 都不为 None；瓶颈宽 ≥ 1.2 m（C 服务带），踏台段 ≥ 0.8 m 并标注「单人」；有顶段最小净高 ≥ 2.0 m；每段 `rises_m` 的每一级 ≤ STEP_MAX。
- T2.2 扬谷留空：`winnow_open_sky_square_outside_band.side_m` ≥ assembly.json 声明值（基线实测 4.9 m），而且整块露天（sky=True）、不与服务带重叠、不压住任何节点几何。
- T2.3 暂存：有顶空方 ≥ 声明值（基线：0.25 m 单级时为 3.6 m，0.20 m 时为 1.4 m），并且位于足下有支持的格上。
- T2.4 负例：
  - (a) 把 STEP_MAX 降到 0.19，含 0.22 m 台基的段必须报不可达；
  - (b) 在服务带中点插入 0.6×0.6×1.0 m 的临时测试箱（只放在测试副本里），该段必须断开或瓶颈 < 1.2 m；
  - (c) 把探点放到杵梁上 (5.0, 2.6)，必须报不可达。
- T2.5 LOD 一致：三档的可达格数与 LOD0 相差 ≤ 0.5%（基线 28091/28086/28146），各段瓶颈相差 ≤ 0.1 m。近景结论只认 LOD0。

## 3. 足下支持

- T3.1 院心有地面几何的格占比：基线 17.4%。若 LY-005 冻结的地坪 y ≠ 0.200 ± 0.005 m，装配必须提供地坪来源（LY-005 片或保留的旧地坪），之后重跑，使路线上每一格都 has_floor=True，或者能命中该地坪片。
- T3.2 足碓石臼底、静架脚的落点高度与地坪差 ≤ 0.005 m，并且没有悬空；容差沿用 LY-008。

## 4. 不加机械与不越权

- T4.1 节点白名单：装配后的新增节点只能是 assembly.json 里声明的区域标记、端口、地坪片。名称或几何上出现扇车、铡刀、风车一类即判失败。
- T4.2 文本检查：交付 brief 和卡片文案中不得出现「官营」「官仓附设」「确址」等定性词；用 grep 扫描。

## 5. 安装与撤回（严格输入）

- T5.1 在最新 main 的副本上安装 overlay，比对原节点的几何哈希、材质、矩阵与安装前一致（只允许新增）。
- T5.2 撤回后整城指纹（city-data 的 blob SHA，以及加载节点的几何哈希）与安装前完全相同。
- T5.3 `lab/tools/build_assets.py --check` 只在 LY-100 合并分支上跑，本席位只交结果引用。

## 6. 报告

每项输出 PASS/FAIL、实测数字、绑定 SHA，以及局限：离散栅格、静态圆柱身体、无连续扫掠/结构/GPU。CPU 图明确标注 CPU。
