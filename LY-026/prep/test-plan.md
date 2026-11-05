# LY-026 测试计划（制作阶段直接跑）

依据「本项验收」：构件修改前后的净空/接点逐项绑定；给出容器行程和轮轴有限姿态，不虚构动力学；未知原图/机制单列为停止项。
所有命令只读输入，结果写进 `workpacks/LY-026/qa/`（制作阶段）或 `prep/results/`（准备阶段）。Blender 统一用 `D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P <脚本> -- <参数>`。

## 0 绑定的 SHA（基线，执行前先比对，不一致就停，并重新登记）

| 名称 | SHA256 |
|---|---|
| well-A-LOD0.glb | 6bc463f8638df55c7e07282641d3d66d07d23ce9af8cd72a5e211be9772a38ab |
| well-A-LOD1.glb | e9252de34398ef8049876aadaf60f2e4c7c9d9aebc35cd40f34b9fca55fd3255 |
| well-B-LOD0.glb | adf2f51a029289e8afbed8a583b1195bd22b815739b72f1c19e08bf693d55139 |
| well-B-LOD1.glb | e4acc416db1024a28606a556c9c0b827482fb3da2d2232ecf00a83ea014aa9dd |
| 试放分块 market_frontage_well_routes.glb | 0193ebc0cfe200292defd595ff4f4011b2b2d05388d4f53e7b4c3a19a255b4c5 |
| market-cluster.glb（现网） | 77b8bf2e9e1488df02c99ffa1b83af9517fabbb23e9d6b7f86dd3c3361c5a5c8 |
| LY-025 原子包（待交付） | **TBD**：LY-025 交付后填写；没有这一项，T6/T7 只能跑「试放分块」替代件，并标明是替代 |
| LY-006 端口文件（待冻结） | **TBD** |
| 检查脚本 | measure_well_ops.py 1801c7562262fc34…，measure_city_ground.py 52c4ef489116ebb7…，compare_city_well.py ae560b2946ad5894…，pose_table.py afc83e86523ac63d… |

每份 qa 报告都要写：输入 SHA、脚本 SHA、Blender 版本、命令行。

## T1 来源一致（试放 = 库件）
- 命令：`python -I extract_chunk.py <tmp>`，然后 `python -I compare_city_well.py well-A-LOD0.glb <tmp>/market_frontage_well_routes.glb out.json`
- **正例**：城市 `A_LOD0__*` 节点 = 库件节点 − `demonstration_apron_opening`；旋转/缩放恒等；有向三角集合在 1e-5 下相同，或差值 ≤ 5e-5 m（float32 世界平移舍入，基线实测 3.5e-5）。
- **负例**：把容器节点平移 1 mm 后再跑，必须报 geometryMismatch。

## T2 运动件对静止件的接触分类（四个 GLB + 每个修订件）
- 命令：`measure_well_ops.py -- <glb> <A_LOD0__|A_LOD1__|B_LOD0__|B_LOD1__> out.json`
- 判据：`opPairs` 里每一对凡出现 intersectVolume > 1e-12 m³，都要在 `contact-classes.json` 登记为下列之一：固定嵌接（joint）、预期支承（bearing seat）、数值残留（≤1e-12）、**冲突**。不允许整对豁免，也不允许按名字前缀批量豁免。
- 基线已知应登记的固定嵌接（容差 ±2%）：cheek→cross_head 6.72e-4/侧；axle→cheek 1.4697e-4/侧（LOD1 1.3384e-4）；axle→hub 2.0995e-4（LOD1 1.9120e-4）；spoke→ring 3.93e-6（LOD1 4.55e-6）；spoke→hub 3.00e-6（LOD1 1.73e-6）；bottom→container 2.14e-5；lug→container 1.27e-5；bridle→lug 5.77e-7；bridle↔bridle 1.83e-8；rope→bridle 7.70e-8；rope→ring 2.1e-14（残留）。
- **正例**：容器组对 collar/rim/liner 的交体 = 0；轮组对 cheek/cross_head 的交体 = 0。
- **负例**：把 wheel_grooved_ring 沿 x 平移 +0.035 m（超过 0.030 的轴向间隙），必须报 ring→cheek 交体 > 0，并归为「冲突」。

## T3 容器竖向行程（有限姿态，刚体平移，不是动画）
- 来源：`containerStroke`，步长 0.05 m，dz 取 −1.0…+2.0。
- **正例**：从静置开始连续自由的区间 ⊇ [−0.77, +1.30]（−0.77 对应容器底到模型井筒底 −0.65；+1.30 是轮环下的上限）；在井筒内（底 > 井筒底、顶 < 0.68），最小净空 A ≥ 0.110、B ≥ 0.180（基线 0.1138/0.1118/0.1886/0.1854，容差 −0.002）。
- 上限必须是「首个碰撞 = wheel_grooved_ring，且 dz ∈ [1.30, 1.40]」；如果首个碰撞变成 cross_head、柱或瓦，判定失败。
- **负例**（地坪封堵）：用 `place` 模式把库件放进现网 market-cluster（实心 sample_ground），必须在 dz ≤ −0.10…−0.15 处撞上 sample_ground，竖射线命中 sample_ground z=0.0。这一项证明检查器能发现「旧地面堵井」。

## T4 提出井口
- 来源：`liftOut`。容器底抬到口沿顶 +0.03，然后横移 1.8 m。
- **正例**：A、B 都至少有一个方向（基线 ±y）在 1.8 m 内无碰撞；±x 的首个碰撞只能是 main_post（A 0.70，B 0.80，±0.05）。
- **负例**：dz 只抬到口沿顶 −0.05 时，横移必须先碰 rim/collar。（制作时给脚本加 `--lift-margin` 参数。）

## T5 轮轴有限转角
- 来源：`wheelRotation`，0–345°，步长 15°（4 根辐，0–90° 已能覆盖周期，保留整圈）。
- **正例**：任何角度下的接触对只有 {hub, axle}（固定嵌接），不碰 cheek、cross_head、柱、瓦。轮环顶到 cross_head ≥ 0.030（基线 0.035），轮环到 cheek 轴向 ≥ 0.025（基线 0.030）。
- 姿态表：`pose_table.py` 输出 dz ↔ 轮转角 θ = dz/0.186 rad ↔ 收绳端 z（定长绳 3.444 m）。至少交四个姿态：−0.77 / 0 / +0.59（A；B 为 +0.51）/ +1.30。表内要写明「无载荷、无摩擦、无绳垂、无水位」。
- **负例**：把轴缩短到 0.30 m（够不着侧托），必须报 axle→cheek 交体 = 0，并把 axleReachesCheek 判为失败。

## T6 城市试放 / LY-025 地坪前提
- 命令：`measure_city_ground.py -- <LY-025 包或试放分块> out.json ox oy oz`
- **正例**：开孔半径 ≥ 井筒外径（A 0.59、B 0.685，容差 +0.002/−0）；地坪和井筒、井栏、柱脚的交体 = 0；井口 r ≤ 0.44 的 17 条竖射线不命中任何地坪。容器下行到 −0.77 也无碰撞。
- 需要登记的状态：井筒在地坪底以下悬出 0.45 m（基线），由 LY-025 决定是否补地层，LY-026 只登记。
- **负例**：同 T3 负例（实心 sample_ground）。另外，演示环坪和城市地坪同时存在时，必须报双层地面（apron −0.08..0 与 ground −0.2..0 重叠）。

## T7 修订前后对照（只有确有冲突、要改件时才跑）
- 对每个被改的节点：修订前后各跑一次 T2–T6，逐项输出差值表 `before-after.json`（净空、交体、行程上下限、转角接触）。没有被改的节点，有向三角集合必须与基线 SHA 版本完全相同（复用 compare_city_well.py 的 canon 比对）。
- 撤回：去掉修订件，回到基线，T2–T6 数字必须复现基线值（容差为 0，或浮点 1e-9）。

## 停止项（触发就停，不补几何）
1. 要决定「轴转还是轮转」、开轴孔或做轴承形制时——证据未知，只登记。
2. 要按图版修改侧托、井架梯形或滑轮形制，但还没亲眼核到原图版时。
3. 要加绳长/收绳端的手持状态，需要人体尺度或操作制度时——只交 C 姿态数据，不声称通行或操作已验证。
4. 任何涉及水位、井深、承载、卫生的数值。

## 不能用来冒充的结论
- 只做了表面 BVH 加选定对的精确布尔，**不是**全场实体碰撞穷尽。
- 刚体平移和转角扫描是离散步长（0.05 m / 15°），不是连续运动。
- CPU/Blender 结果不等于 Three/GPU 显示验收。
