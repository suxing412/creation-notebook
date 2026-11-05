# LY-036 测试计划（制作时直接跑）

前提：G 已冻结。开工时先重读最新 main，把下面的「绑定 SHA」与 LY-001 的新快照逐条核对。只要有一条变了，先停下，重做 prep 的测量，不能直接沿用本表。

坐标：glTF 米制，X 向东、Y 向上、Z 向南。本表的数字都写在武库本地坐标里，世界坐标 = 本地 + (2316.326904296875, 0, −3500)。如果 LY-005 改了原点或高程基准，以 LY-005 为准，并在 qa 里写明换算。

变量（Git Bash）：
```
L=D:/GitHub/creation-notebook-lab/docs
F=$L/library/models/m-luoyang-wuku/files
P=D:/GitHub/creation-notebook-workpacks/LY-036
S=$P/prep/scripts
O=2316.326904296875
NEW=$P/models/<交付地坪GLB>       # 制作后才有
```

## 绑定 SHA（任一不符即失败）

| 对象 | SHA256 |
|---|---|
| wuku-B-LOD0.glb | e5de60b6ff972e6b9446bb60c9c8b79572d345c69be7124dfc855181ac87dfd3 |
| wuku-B-LOD1.glb | 5e1cc6b99bb81c62ec2a3fff83bf361fb33bbbc5805d00fa00deffadcf7ee980 |
| wuku-B-LOD2.glb | e5c8730605f39fb304e7c0ef98a33c4b779fe199fc91ff12a613ca4585956c5d |
| wuku-A-LOD0/1/2.glb（只核不改） | 5daa542d…cea5c / 51110119…6686 / ee0da058…f3486 |
| 旧试放 chunk01（旧支撑） | 29709e25f77f6becaf2566555a4d55b0525e244f73ede92ae344a78cc1a57b37 |
| 旧试放 chunk02 | 34160b9d5c1ec0add696c2a7aec272c882d2ed68d4344b1d7d3b96d7da749429 |
| 东北 C 路 chunk（LY-039 所有） | 58f2f58a464183e20d5489b13902f62f2570573cb8bf96fb237df781027d076e |
| evidence-geometry.json（提交 blob） | fa8b7002869e01e981d2b2679c327a2f1db957119e55537e06289ca59e5ba7c7 |
| storage-precedents.json（提交 blob） | db8024490dad09484f9c1b24a915872c4010024817cadb7abb2ce58cd70fbd39 |

## T1 修订 B 身份（验收①：「修订B的SHA与公开门框版本一致」）

- 正例：`sha256sum $F/wuku-B-LOD*.glb` 与上表完全相同。三档节点的 `extras.version` 都等于 `2.2.0-C-entry-candidate`。交付清单 `assembly.json` 里 B 的来源 SHA 填资产卡的这三个值，不能填 trial 的 `29709e25…`。
- 等价核对：`python -I $S/glb_compare.py $F/wuku-B-LOD0.glb <chunk01> $O,0,-3500` 要求：earth 和 timber 两个节点的 `indicesEqual=true`、`maxUVResidual=0`、`maxIndexOrderResidual_m ≤ 2e-4`（float32 在 x≈2316 处的精度）。对 chunk02 跑同样的命令，核 tile 节点。
- 负例：(a) 把 B 换成 A-LOD0 跑 glb_compare，必须报 `b: null` 或顶点数不等。(b) 交付清单里如果出现 v2.1 的任何文件名或 SHA，或 `extras.version` 不是 2.2.0 开头，判失败。

## T2 外到达支撑（验收②：「外到达缺支持点被真实地面覆盖」）

窗口文件格式见 `prep/qa/m4-probes.window.json`。把标签 `T1` 换成新地坪 `G`，命令如下：
```
D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P $S/measure_wuku.py -- $P/qa/t2.json \
  B0=$F/wuku-B-LOD0.glb "G=$NEW@<LY-005给定的本地化偏移>" "R=<chunk northeast_C_access>@-$O,0,3500"
```
- 正例 A：台阶脚外侧取 x ∈ {−1.45, 0, 1.45}、z ∈ {7.55, 8.5, 9.95}，共 9 点。G 的最上层命中值都应在 0.000 ± 0.005 m，命中面朝上（`up` ≥ 0.99）。从最低踏面 0.1333 下到地面，高差 0.1333 ± 0.005 m，与踢面一致。
- 正例 B：台基外缘 0.1 m 处，东、西、北各取 5 点，南侧在台阶以外取 4 点。G 都必须命中，高度 0.000 ± 0.005 m。
- 正例 C：与路的接缝。x ∈ {−1.45, 0, 1.45} 时，z = 9.95 命中 G，z = 10.05 命中 R，两者高差 ≤ 0.005 m。如果 LY-006 冻结的端口坐标不是 z = 10，就以端口为准。
- 正例 D（连续性，代替单点）：沿台阶中线 x = 0，从 z = 7.52 到端口每 0.05 m 采一点，再在 x = ±1.45 各采一条。全部命中，相邻两点高差 ≤ 0.02 m。这只说明离散采样连续，**不能**说成连续人体运动或车辆通行已验证。
- 负例：(a) 去掉 G 只留 B0，正例 A 的 9 点必须全部落空。现状实测 9/9 落空。(b) 把 G 向北平移 3 m，台阶脚那一排（z = 9.95）必须落空或失败。(c) 把 A0 放在原点配旧支撑，z = 10.3 和 10.45 必须落空。现状实测 2/2 落空，用来证明测试不会把 B 的结论套到 A。

## T3 接地边与「不以展示底板掩盖悬空」

- 正例：交付地坪外缘没有与城市地面（LY-005 高程）相接的部分，自由竖边长度要 ≤ LY-006/010 允许的值。默认 0 m，路端口除外。旧支撑现状是 81 m 自由竖边、高 0.4 m，必须减到允许值以内，或用收边坡/裙边接到周边高程。坡度与 LY-005 给定的地面衔接，最大坡度写进 qa。
- 正例：地坪顶面面积 ≤ 设计需要（台基轮廓外扩到达区和收边），每一块都要说明用途。旧支撑是 440 m²：台基 221 m²，余量 219 m²。超出部分要逐条说明理由，否则判为展示底板。
- 负例：(a) 拿旧支撑原样跑这一项，自由竖边 81 m，必须**失败**，证明检查器会抓展示底板。(b) 人为把 B 抬高 5 cm，此时 B 底面与地坪之间有缝，接触面积必须降到 0 并报悬空，不能被大底板「盖住」而通过。

## T4 接触分类（不一律豁免）

命令：`python -I $S/contact_check.py $P/qa/t4.json "$NEW#<地坪节点>" <偏移> B0=…@… B1=… B2=… road=…`（当前只支持轴向盒地坪；地坪如果做成非盒体，制作时改成按三角形逐一做 SAT，并保留本脚本作回归）。
- 正例：B 三档的每个节点，以及路，都要满足 `vertsStrictlyInside = 0`、`trisEnteringInterior = 0`。B 的 earth 共面接触 `coplanarDownContactOnTop_m2` = 224.06 ± 0.05。分类记为「合法局部接面」，只覆盖 B 的 earth 底面和路的端面。其他节点对没有接触，不需要豁免。
- 负例：B 下沉 5 cm，必须得到 >0 的侵入。现状实测 48 个顶点、40 个三角形。
- 限制：这是表面加盒体的精确测试，不是任意实体碰撞穷尽；qa 里要写明。

## T5 旧门体、工作台基和城市定位证据不被改写（验收③）

- B 三档 GLB 的 SHA 不变（T1）。交付包里**不包含**重新导出的 B。如果装配需要 B 的副本，就用 glb_compare 逐节点核对：indicesEqual 为真，UV 残差为 0，位置残差 ≤ 2e-4 m（世界平移带来的 float32 误差），材质语义名保持 `LY_P01_*`。
- 台基几何（earth 节点）：顶面 y = 0.4，面积 222.02 m²；三级踏面各 1.02 m²，高 0.1333 / 0.2667；底面 224.06 m²。三档都要与现状相同（脚本见 `prep/qa/m*` 的 earth 统计）。
- `evidence-geometry.json`（提交 blob `fa8b7002…`）与 `storage-precedents.json`（`db802449…`）在交付分支上字节不变。`region_wuku_B` 仍是 (2316.327, 3500)，`architectural_completion` 仍是 `not_modeled`。交付包不能写「武库位置已确认」。
- 负例：改动 region_wuku_B 的坐标或 evidence_class，再跑上面的 SHA 比对，必须失败。

## T6 安装与撤回（严格输入上至少一次）

- 在 LY-008 的检查器和 LY-100 的 overlay 规则下：在 bce3211（或开工时的 main）上把地坪作为 overlay 安装，然后撤回。撤回后城市清单里 66 个节点的矩阵、几何和材质 SHA 与安装前逐项相同。用 LY-001 的 `dump_city_data.mjs` 导出，再做 diff。
- 互斥：旧试放 chunk01 里的 `C_WUKU_ISOLATED_SUPPORT_PATCH` 与新地坪不能同时加载，即不能叠载。也不能再引入 trial 里那份 B 的拷贝，否则 B 会被计两次。
- 不激活城市：安装记录要写明本包只是局部装配。是否入城由 LY-010 的区域准入和 LY-003 的配准决定。

## T7 公共质量底线

- 每个 GLB ≤ 15,000,000 字节，跑 LY-008 检查器（含负例），再跑官方 `lab/tools/build_assets.py --check`。后者由 LY-100 或协调者在合并分支上运行，本席位不在 lab 里运行。
- 地坪三档：如果近、中、远三档几何相同，按 LY-007 的规则只交一档并说明理由，不能复制改名凑三档。UV 有限、非退化，材质语义用 LY_P01 earth 或 LY-007 规定的地面材质，纹理内嵌。
- 隐私：交付物里不出现 `C:/Users`、`D:/GitHub` 等绝对路径。

## T8 与邻席位的边界（交 LY-006 判定）

- LY-037：只在 y ≥ 0.4（台基以上）的台前、侧棚、点验台内做高差过渡。本席位只做 y ≤ 0 的外地面，以及台基外的接地边。共享边是台基外缘线（周长 60 m）和台阶脚 z = 7.52。
- LY-038：A 的台阶脚在 z = 10.52。如果选 A，到达区要另测，不能复用本包的 T2 结论。
- LY-039：路的端口在 z = 10、x −1.5…1.5、y = 0。端口 ID、版本由 LY-006 冻结，两方用同一份。
