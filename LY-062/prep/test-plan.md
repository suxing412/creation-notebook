# LY-062 测试计划（prep r2；制作时直接运行）

依据是任务池 LY-062「本项验收」，共三条：
- 主门、侧口、工作口各自做开闭状态测试；
- 门关后能否进入，要和声明一致；
- 不能用动画效果掩盖围界缺口。

坐标与身体：
- 坐标用 Blender 导入帧，即 (X,Y,Z) = glTF (x,−z,y)，按 LY-005 b6d7fe9d…。端口值交付时，按 LY-006 port.schema 同时写 glTF 帧 local 值，world 值待落位。
- 身体包络 0.8 m 宽 × 1.8 m 高（沿用 QA），栅格 0.1 m；步高代理 0.30 m，属 C。

运行方式：`D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P <脚本> -- <in.glb> <out.json>`。

被测对象：原组合 GLB、LY-061 外围 GLB、LY-062 关闭件 GLB 三者在同一场景装配后**导出的组合 GLB**，每个状态一份。正式测试必须**去掉**夹具，检查场景里不得另加挡块。

## 0. 绑定 SHA（任一不符即停止）

| 输入 | SHA256 |
|---|---|
| closed-LOD0/1/2 | 6ea892982b46e554bbe8c94ade9cb94ed94e3dbc6a8015b3bb963943d96500a8 / 455a12153d4132d2b653cdf8bbcf4b4994a5c33451efc1ec16119ebbf21453d2 / 108e28a567dcef237868b2414332ae51925686d256891736355a5b40d9c0101d |
| open-LOD0/1/2 | 59c8b758a5a2523105eac0e516e9961bf769bd5e422ba2913d292492ed45c4b0 / d95bd22f9317683ece8b8d14a6d4a6719522e47c8410f976e064708890148281 / 01b2017fac9d8ee6190726d233973c9b048936ce76b3ec7da8fb91aedec3a33d |
| guard-slice-closed-LOD0/LOD2（对照） | 48c511c54010cc00b5a6262dc280cab2b1d0a7c13050d847fc5856e264ce82cd / bf47d91d784b224fcfc0bbe81997c6e5a9a81c68375641134e29e396d9e5d63d |
| LY-006 zones / ports / seams / ownership（registry v1） | 6b3595ac735d180866e823ddeb4e3676ffc0e816d083f6be2d57d6e4df0821c0 / 28bcfb68cd7d7fe0026f62de23ae3e45ba8f714a139e38c0b0957039f12fc633 / ca4d81f8f955333c089d782aa69c50c2ca83225d4da07f595f66d1ba87f3f4c1 / ecbbbcf5614d41bf7c7bf3b04416504ae70891e212c7551456de4ff1a417b4ca |
| LY-006 port.schema / LY-005 coordinate-contract | 9fcdf932adbb4cdc58fecf19d52c7a1442955d273e75be7bc6bb9a1a5f494fdc / b6d7fe9db9523569383bf656df39aef63e7d80e8a1d5877196ba0bcab8747712 |
| LY-007 材质 / LOD 规则 | f0a04f599595d41b9d7cad39b9afd5ae3829b343222d92e174f1b49d6d9b1bf3 / fbf53757be2e243429b751899f1690d30f827849962c0e77a8ca811462789146 |
| LY-061 wall-end 端口值与外围 GLB | 待交付后填入 |
| C1/C2 裁决（方案 A 或 B、registry v2） | 待填。若 zones.json 的 SHA 变化，本表与第 2 节一并重定 |

脚本 SHA256：

| 脚本 | SHA256 |
|---|---|
| measure_enclosure.py | 108dcad5d22e80ad298020a457214503784f0f4b23c1e96e9f7072670c2b1771 |
| ray_slots.py | 136cb30538ce620a477c1d246027f9a6c311832f8eee3c664b3812bb55d148ad |
| opening_frames.py | b0ca84493598825ffbc6007e5820555afad9c8c1117a95eeb625b3ca15ccc953 |
| outer_face_probe.py | 2feb63ab14d0664c9614231b888d5fc1ec5be81f1b58c8a045975c8442a7d45d |
| zone_probe.py | a461cb0959f130f9bf9d183b70f532131b4e58f2725619f04d0a8d31e94f3384 |
| gap_probe.py | 37edfd4d20adcbdecdb1c33b220e57bf9ae37c3e28c33f2f9b5176797c48e2cb |
| state_matrix_fixture.py | 11e379a9edea931ad7e46828808a6feea659bdfb1a6aafb92772db4cbb55b95b |

## 1. 检查器自检（负例先行；结果与下列预期不符即说明脚本失效，停止）

- **T1.1** 对 closed-LOD0/1/2 跑 ray_slots：
  - 必须报出 6 条 ≥0.8 m 的通道：S1 ±2.10…3.14，S2 ±3.46…4.48 和 ±5.12…6.04；
  - 两端各有 ≥5.16 m 的开放带；
  - 0.04 m 的缝必须列出，但标记为不可通过。
- **T1.2** 对 closed-LOD0 跑 measure_enclosure：interior_reaches_offground 应为 true；四边开放长度 87.0 / 87.0 / 67.8 / 67.8 m，容差 ±0.2。
- **T1.3** 夹具矩阵：用 state_matrix_fixture 跑 closed-LOD0、open-LOD0、closed-LOD2，结果必须复现 measure/statematrix-*.json：
  - 情景 1 和 7（闭门）为封闭；
  - 情景 7 在开门时出界；
  - 情景 0、2、3、4、5、6、8、9 出界。
- **T1.4** outer_face_probe：端墙外皮 LOD0 为 ±6.797、LOD2 为 ±6.76（±0.005）；台基 ±7.0 只出现在 z ≤ 0.18。

以上结果写入 qa/baseline-negative.json，并绑定输入 SHA。

## 2. 状态矩阵（正式，LOD0/1/2 每档都跑；每个组合导出一份 GLB，各自 SHA 入账）

符号：

| 符号 | 含义 |
|---|---|
| M | 主门叶，P062-main-leaves-state |
| SW / SE | 西、东侧口（write:001 / 002） |
| X | write:003，名称以 C1 裁决为准 |
| G | 门卫线关闭件，只在方案 B 中存在 |

每个状态取 O（开）或 C（闭）。连通判据用 measure_enclosure 的洪泛加上**切断法**：把被测口临时栅格化为障碍再跑一次，连通与不连通都必须双向证明。

### 方案 A（外墙控制，v1 区内）

| ID | M | SW | SE | X | 声明 | 期望 |
|---|---|---|---|---|---|---|
| A1 | C | C | C | C | 全闭 | 院外四个种子到庭内 (0,−35) 全部不连通；周边泄漏 0 m |
| A2 | C | O | C | C | 只西侧口 | 连通；切断 SW 后不连通；路径经板边窄带，绕到廊南端 y<−51 |
| A3 | C | C | O | C | 只东侧口 | 同 A2，镜像 |
| A4 | C | C | C | O | 只南轴口，主门关 | **连通**（声明「主门闭合不控制入院」）；切断 X 后不连通 |
| A5 | O | C | C | C | 只开主门 | **不连通**（主门在院内，外口全闭） |
| A6 | O | O | O | O | 全开 | 原 99 条 QA 带零命中、无支承失败；新口门槛带零命中 |

### 方案 B（门卫线控制，需 v2 区）

| ID | M | G | X | 期望 |
|---|---|---|---|---|
| B1 | C | C | O | 不连通（对应夹具情景 7） |
| B2 | O | C | O | 连通，且所有连通路径都经过主门洞 x∈[−1.82, 1.82]；把门洞切断后不连通 |
| B3 | C | 只开工作门 | O | 连通，路径落在 guard_*_work_* → patrol_floor/midstep/ground → guard_inner_cross_patrol 带内；切断工作门后不连通 |
| B-neg | C | 去掉任一 S1、前檐、后檐或横墙件 | O | 必须连通（对应夹具情景 8、9） |

容差与规则：
- 身体半径 0.40 m，有效容差 ±0.05 m。
- 宽度小于 0.8 m 的缝不计为通道，但必须列表；继承的 0.04 m 缝不得报告为已修。
- 殿廊转角对角 0.78 m 一处继续列为「不可通身」，并注明这是 0.8 m 身体的判定，不是围界。

## 3. 关闭件几何检查（每件、每档）

- **G1 端口**：
  - 侧口端口 `admission-court:side-opening-W/E:opening` v1，填 local（glTF 帧）的 position/up/forward，按 LY-006 port.schema 校验，kind 为 opening。
  - 门框和 LY-061 wall-end 端口的位置差 ≤ 0.005 m，高程差 ≤ 0.002 m。
  - 与 LY-061 墙体的接面间隙 ≤ 5 mm，正体积侵入为阻断。
- **G2 写入区**：
  - 每个 ly062_ 节点的世界 AABB 必须落在自己的 v1 区内（容差 0），越界即阻断。
  - 新地坪命名为 gp:LY-062:*，同样不出区。
  - 区外的接路不是本席位产出，不得顺手延长。
- **G3 净宽与门槛**：
  - 开态净宽 ≥ 0.8 m，净高 ≥ 1.8 m，从门槛顶面起算。
  - 门槛与庭地板 z=0.0 的高差，或与 LY-061 外缘带的高差，≤ 0.30 m（C），且有足下支承：门槛带下射命中率 100%。
  - 闭态时 ray_slots 在 z=0.25～1.75 区间零通道；门扇底缝 ≤ 0.05 m。
- **G4 侧口内路**：
  - 开态时从侧口内侧到庭内必须有 ≥0.8 m 的连续路径；按现状只能绕廊后。
  - 不得为了取得通路而改廊台或殿台，它们归 LY-061 或 LY-063 所有，状态为 keep。
- **G5 门叶语义**：
  - 动叶为独立节点，以 ly062_ 开头。
  - 开、闭两份 GLB 中的固定件节点必须相同：矩阵、顶点哈希都一致。
  - 主门状态只选用原 open 或 closed GLB，不改原门叶节点。
- **G6 三档一致**：
  - LOD0/1/2 的足迹在 XY 平面上相差 ≤ 10 mm。
  - 各档分别贴合：LOD2 的门叶和端墙外皮与 LOD0 不同，见 T1.4。
- **G7 规范**：
  - 单个 GLB ≤ 15,000,000 字节；无 NaN，无退化三角面；纹理内嵌。
  - 材质语义按 LY-007 LY_P01，LOD 命名按 lod-rules。
  - 跑 LY-008 检查器（未交付，届时绑定其 SHA）和官方 `lab/tools/build_assets.py --check`。官方检查器在隔离的 checkout 里跑，不在只读仓库里跑。

## 4. 原件保持（安装与撤回）

- **P1** 原 21 个 admission-court 节点：安装前、安装后、撤回后三次比对，顶点数、三角数、AABB（4 位小数）、世界矩阵必须完全一致。撤回后导出的 GLB 逐节点几何哈希必须相同；字节差异要写明原因。
- **P2** 主门叶 AABB 不变：
  - 闭：x [−1.515, −0.02] 与 [0.02, 1.515]，y [−56.465, −56.185]；LOD2 的 y 到 −56.265。
  - 开：x [±1.385, ±1.665]，y [−56.465, −54.97]。
- **P3** 原 99 条 QA 带在 A6（或 B2 加全开）状态下全部复现零命中；负例 negative_hall_column 仍命中 56 次，容差 ±0。
- **P4** 旧方案和新方案不叠载：同一状态里同一个口只能有一个关闭件节点，互斥用 state-variant 表达。

## 5. 不能宣称的事项（固定写进报告模板）

- 「模型能读取」「局部通行通过」「已入城」「结构安全」「历史复原成立」是五件不同的事，不能互相替代。
- 2D 截面洪泛和直线射线不能证明以下任何一项：连续人体步态、门扇扫掠、翻越、攀爬，或实体碰撞已穷尽。
- 夹具情景只是预演，不能当作成品结果。
- 没有做 GPU 或手机测试。
- 口的位置是 C 设计，不对应任何史载门名。LY-002 E-P03 只支持「宫门凭符准入」这一功能。
