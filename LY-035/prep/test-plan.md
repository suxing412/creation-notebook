# LY-035 测试计划（制作时直接跑）

对应「本项验收」两条：
1. 选定暂存/转身体积与搬运路线之间的互斥规则写清楚；
2. 高负荷/大包络的失败原样保留，不把设计空间当成现实效率的证明。

另外还要过任务池的公共质量底线。

## 0. 必须绑定的 SHA（任何一项变了，先停下重测，不能沿用本表）

| 对象 | SHA256 |
|---|---|
| 城景 LOD0（基底，逐字节不变） | `5937211c7366a5920ae222185176f198cc3d16e8763605fa248e61031c74bc93` |
| 城景 LOD1 / LOD2 | `a1265bbf53d10ddb6398efa6f505c1b6dee86b81b37397f7af9855acc34f2e45` / `6b2564d3ffd76e6e982a4a7f703cfd0790ac0e0b2dfa75add4df169c4c82efe7` |
| v1 命名件（部件身份） | `b8482824513a101d36eb4c768a4f641e77aaac66c3e834718d7f3964104a644b` |
| 讲解分区 -local | `07b7c65b55e434bbe00b90fe2b6345825849308485bd22ca9112b83941e2e84b` |
| city-data.mjs（只读对照） | `e4115705aeab28f2f6cc2635fbedfabf4158a08af9c626f6dd493ee27d430a1a` |
| LY-033 门件 / 扫掠体积、LY-034 端口 JSON | 交付后补填；没填齐不开工 |
| 本席位脚本 | 每次运行前重新计算 `measure_forecourt.py`、`measure_zones.py`、`check_variant.py`、`glbread.py` 的 SHA，写进 qa 报告 |

## 1. 运行入口

```
cd D:/GitHub/creation-notebook-workpacks/LY-035/prep
python -X utf8 measure_forecourt.py qa/forecourt-measure.json        # 基线实测（阶梯/平台/走廊/候选）
python -X utf8 measure_zones.py qa/forecourt-measure.json qa/zones-measure.json
python -X utf8 check_variant.py --selftest --out qa/checker-selftest.json   # 检查器自测：1 个好样本过，5 个坏样本败
python -X utf8 check_variant.py --variant <models/LY035-staging-LOD0.glb> --rules <assembly.rules.json> --out <qa/variant-LOD0.json>
D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P blender_crosscheck.py -- <glb> <out.json>
```

制作时，所有临时端口（收货北口 (2285.7141, −3664.369)，A 阶脚 (2273.7141, −3674.989)，B 阶脚 (2297.7141, −3674.849)）都要换成 LY-034 和 LY-006 的冻结端口 ID，并把端口 ID 和版本写进 rules。

## 2. 检查项

容差：长度 ±0.005 m；重叠面积 ≤ 0.01 m²；栅格 0.05 m；侵入检测时原件占用格向外膨胀 1 格；行走面 y = 0.200 ± 1e-4。

| ID | 检查 | 正例（应 PASS） | 负例（必须 FAIL） |
|---|---|---|---|
| T0 | 基底 SHA 与本表一致 | 5937211c | 换成别的 LOD0 字节，或改了 LY-033 后没有重新绑定 |
| T1 | **不改原件**：变体开启和关闭时，基底 GLB 逐字节相同；城景节点表与 storage-main 的 path/sha/bounds 不变；建筑三角形多重集（1e-4 m）与 v1 相同（9496 个） | 只新增独立节点 | 把附加件合进 `granary-group-static_*`，或改动 storage-main 的 path |
| T2a | 附加件全部在地块内（x 2249.714–2321.714，z −3699.469…−3647.469） | 两仓之间 3×3 m | 伸出东界的 3×3 m 块（selftest「outside plot」） |
| T2b | 不低于行走面 y=0.200 | 底面 0.205 | 底面 0.10（selftest「below ground」） |
| T2c | 不和地坪共面：2 mm 内没有水平面 | 底面 ≥ 0.202（与讲解层同一做法）或 ≥ 0.205 | 底面正好 0.200（selftest「z-fight」） |
| T3 | 在 0.05–2.0 m 高度带内不侵入原件：墙、阶 A_step_0..3 / B_step_0..5、棚柱、计验台、货物代理 U0–U3 / checking | 两仓之间 | 叠在 U2/U3 上（selftest「on U2/U3 bags」） |
| T3b | 不侵入 LY-033 门叶扫掠体积（开、闭、中间档全部检查） | — | 转身圆伸进向外开的门叶扫掠范围 |
| T4 | **互斥**：每个启用的暂存体积 S 与每条路线走廊 C（LY-034 路线，宽 0.9 m）、每个转身圆 T 的重叠面积 ≤ 0.01 m²。规则表在 assembly.json 里写成成对 exclusive | 两仓之间 S1，与 C_A、C_B、T_A 都不重叠 | 把 S 声明在收货→B 走廊上（selftest「staging declared on B corridor」） |
| T4b | 开启变体后路线仍然可达：0.9 m 包络从收货端口走到 A、B 阶脚，记录最短路径长度和比关闭时增加多少 | 现状 A 16.184 m，B 16.180 m（0.9 m） | 暂存块把唯一通路堵死，结果 reachable=false |
| T5 | 现有冲突照实写：U2/U3 压在收货→B 直线上（距离 0.000），不能改写成"已解决"；变体也不能删除或移动 U2/U3（它们在合并网格里） | 报告里保留这一条 | 交付文字写"B 线直通"；或 LOD0 的 paper__cargo_proxy 三角形数 ≠ 676 |
| T6 | **大包络失败保留**：变体开启和关闭时，阶梯横向探针结果相同。0.9/1.2/1.5 m 为 0 处失败；1.8 m 时 A 80/380（落差 0.65）、B 120/570（落差 0.90）。卡片原记录 A 51 / B 77 原文照录，不覆盖 | 两组数字都在 | 任何"1.8 m 可登阶"的说法；把阶梯或平台加宽、加深 |
| T6b | 门前平台深度保持 0.52 m，转身体积不能放在平台或阶面上（只能在 y=0.200 地面） | 转身圆中心在阶脚以南 ≥ D/2+0.05 m | 转身圆中心落在阶面上 |
| T7 | **货物包络和通路分开**：S 的高度 ≤ 门洞净高 2.10 m；货物包络尺寸单独列出（基准 0.9×0.6×0.62 m 代理）；搬运时人加货的高度，对照门 2.10 m 和檐下 2.42 / 2.62 m 只列为约束 | S 高 0.62 m | S 高 2.5 m（应报 FAIL） |
| T8 | 转身圆（C 值，例如 D=1.5 m 单人，另测 2.4 m 和 3.0 m 压力样本）完全落在空地上，且与 S 互斥 | A 阶脚以南 1.0 m、D=1.5 | 让 S 同时启用并压到 D=3.0 的圆上，必须报重叠，不能静默缩小 D |
| T9 | **可关闭和撤回**：在严格输入上做一次安装→撤回；撤回后节点、几何、材质、矩阵逐项相同；新旧方案不叠加载入 | 关闭态等于现状 | 关闭后还残留附加节点 |
| T10 | GLB 质量：单文件 ≤ 15,000,000 字节；数值有限；无退化三角；有 UV 和法线；纹理内嵌；LOD0/1/2 不是简单复制改名（三角数和轮廓差异写进说明）；材质语义按 LY-007 的 LY_P01 | — | 三档字节相同；有 NaN；外链纹理 |
| T11 | 文字诚实：交付文案必须带"C 作业变体"；不出现吞吐、效率提升、产能、货量、历史证明、太仓实测、车辆可行、负重可行这类说法；五件事（能读取 / 局部通行 / 已入城 / 结构安全 / 历史成立）分开写 | grep 0 命中 | 命中任何一个词都算 FAIL |
| T12 | 官方 `lab/tools/build_assets.py --check` 和 LY-008 检查器：只在 LY-100 合并队列或 LY-008 入口运行，prep 阶段不跑 | — | — |

## 3. 已验证的检查器自测（2026-11-05，本机 CPU）

`qa/checker-selftest.json`：1 个好样本 PASS；5 个坏样本（叠货物代理、低于地面、出地块、与地坪共面、暂存压走廊）都按预期 FAIL。T3b、T6b 和 T8 的 D=3.0 负例要等 LY-033 / LY-034 交付后补进 selftest。

## 4. 局限

- 走廊目前用直线胶囊近似，交付时要换成 LY-034 的实际路线折线。
- 栅格分辨率 0.05 m，只覆盖 0.05–2.0 m 高度带：这是表面采样，不是实体碰撞穷举，也不是连续人体或车辆仿真。
- 全部只在 CPU 上测，没有 GPU 或浏览器实测。
