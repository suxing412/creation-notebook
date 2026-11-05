# LY-073 测试计划（按「本项验收」）

本项验收原文有三条：岸缘/地面与跨水件之间无空隙、无双层覆盖；未定的岸线、水深、流向写明；水材质可关，且关掉后不影响实体支持检查。另外加上任务池公共底线：三档、回读、接触分类、装配可撤回。

统一命令：`D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P <脚本> -- <参数>`。坐标用 Blender Z 上、+Y＝图面北，局部中心 C 取 LY-071 冻结值（现状为 2183.673, -938.776, 0）。每份结果 JSON 都要带全部输入 GLB 的 SHA256。

## 0. 开工前要绑定的 SHA（制作时填入 qa/bindings.json）

| 输入 | 现值（prep 时） | 冻结后要换成 |
|---|---|---|
| LY-072 跨水件 LOD0/1/2 | 无（现用母版占位板，属于 biyong_C_relationship.glb 1bd1c446…） | LY-072 delivery-manifest 的 SHA |
| LY-071 礼堂/围护装配变换 | 库卡 937a3192… / 88f227d0…；母版平移 +1.2 | LY-071 assembly.json 的 SHA |
| G 端口/高程 | LY-005 coordinate-contract.json b6d7fe9d…（frozen-candidate） | 冻结版 SHA |
| LY-006 写区/端口/接缝 | zones.json 6b3595ac…、ports.json 28bcfb68…、seams.json ca4d81f8…、seats.json a1426412… | 重发 S-BIYONG 写区后的 SHA |
| LY-010 区域准入 | 无工作包 | LY-010 冻结版 SHA |
| 本项产物 | — | models/ 下各档 GLB 的 SHA |

## 1. 检查器自测（每次改检查器都要先跑）

```
check_bank.py -- fixtures/fx-pos.json        out/check-fx-pos.json         # 期望 all_pass=true
check_bank.py -- fixtures/fx-neg-gap.json    out/check-fx-neg-gap.json     # 期望 T1=false（外端缝 0.03 m）
check_bank.py -- fixtures/fx-neg-double.json out/check-fx-neg-double.json  # 期望 T1=false（1600 格共面双层）
check_bank.py -- fixtures/baseline-city-master.json out/check-baseline-city-master.json  # 期望 T1/T2/T4/T5=false
```
prep 时的实测结果和上面的期望一致。

## 2. 验收检查（正式产物写一份 config，节点名照 assembly.json 填）

| ID | 检查 | 正例判据 | 负例（必须能抓住） | 容差 |
|---|---|---|---|---|
| T1 | 跨水件两端接缝：每块跨水件、每个端头，沿宽度每隔 0.25 m 一条线，向外 0–0.5 m、1 cm 步长找第一块岸/地面 | 每条线都找到地面；水平缝 ≤ 0.01 m；端头高差落在声明的 `max_step_m` 之内（由 LY-072/G 定，未定就只记录） | fx-neg-gap（3 cm 缝）；母版基线（外端 33/33 条线空） | 缝 0.01 m，台阶 0.02 m 或声明值 |
| T1b | 双层覆盖：跨水件投影内，0.2 m 格里有没有岸/地面顶面和跨水件顶面共面（相差 < 5 mm） | 0 格 | fx-neg-double（1600 格） | 5 mm |
| T1c | 开水、关水各跑一次 T1 | 两次结果相同 | — | — |
| T2 | 外岸到达地面覆盖：水带外 `outer_band` 内三圈方环（关水跑） | 声明的到达范围内覆盖率 1.0；范围以外是有意留空的，要在 assembly.json 列出边界 | 母版基线（0/628…） | 0 |
| T3 | 水是否画在可走面之上 | 0 个采样 | 把水板顶抬到岸面以上的变体 | 0 |
| T4 | 北面无水（E-R05）：北带 y∈(70,78) 的 1 m 格 | 有水的格数为 0；或者声明 C 争议方案并在 brief 里标出（`north_dry=false` 要有理由） | 母版基线（1092/1099） | 0 |
| T5 | 实体边界：岸/地面/跨水件节点焊接后的非流形边数 | 0；bank 列表不为空 | 开口薄片 | 1e-5 焊接 |
| T6 | 高程基准：各岸/地面节点顶面减去 G 基准 | 等于声明值（0.00 或 0.20，等 G 冻结） | 用错基准 0.20 m | 5 mm |
| T9 | 写区包含：本项每个节点的 bbox（以及每个三角的顶点）都在 LY-073 写区并集之内；换算 local:biyong 用 LY-071 冻结变换。现成脚本 `scripts/zone_check.py` 先跑一遍现状 | 越界顶点 0 | 用现行 LY-006 写区跑母版跨水板：69.8–78.2 段重叠 0.000 m，必须报越界（`out/zone-check.json` 已复现） | 0.005 m（LY-006 位置容差） |
| T10 | 排水端口 `biyong:bank-outlet:drain`：端口 JSON 有 local 位置、高程、来源类=C-engineering；位置落在本项岸件表面上（距最近面 ≤ 0.005 m），高程误差 ≤ 0.002 m | 一个端口，值非空 | 端口悬在空中 0.05 m 的变体；值为 null | 0.005 / 0.002 m |
| T8 | 岸/地面与围护、礼堂表面相交 | 0 对。只做了表面 BVH，不能称已穷尽实体碰撞 | 岸件伸进围护墙脚 | 0 |

## 3. 要补跑的项（检查器外）

- **三档**：LOD0/1/2 分别跑 T1、T2、T4；外沿轮廓差 ≤ 0.02 m。LOD1/2 不能是 LOD0 改名，要比对三角数和 SHA。
- **回读**：导出后重新导入，逐节点有向三角 1 mm 匹配（参照 `compare_lib_vs_city.py` 的 tri_keys），bbox、UV、材质名集合一致。
- **写区先行**：T9 在 LY-006 重发写区之前一律记「阻断」，不能先做后补写区。
- **安装与撤回**：在严格输入（LY-071 + LY-072 冻结件）上装入本项，再撤回。撤回后输入节点的几何、材质、矩阵 SHA 要和装入前一致。母版旧岛、旧水、旧板不能和新件叠在一起，要在 assembly.json 写互斥替换清单。
- **水可关**：水节点要单独成节点，材质名不带「hydraulic」之类的含义；关掉后 T1/T2/T3 结论不变（T1c）。
- **未知披露**：brief 里要明写真实岸线、水深、流向、驳岸做法、外侧地坪都是未知，并说明 C 方案是可以替换的。
- **公共底线**：单个 GLB ≤ 15,000,000 字节；跑 `lab/tools/build_assets.py --check`（由 LY-100 在合并分支上跑，本席位不在 lab 仓库里跑）。

## 4. 不算通过的情况

- 只用中心射线验了跨水板顶面（T1 要求沿宽度逐线验）。
- 拿水材质当支持，或者用「水板下有东西」去证明跨水件有承重。
- 用远档通过去证明近档可用。
- 把母版里的占位岛、水、板换个名字交上来。
