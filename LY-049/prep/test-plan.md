# LY-049 验收测试计划（制作时直接跑）

对应「本项验收」（TASKPOOL.md:541）：从院门到冻结院界的路线、阶差、足下支持完整；边界输出供 082 接续；双方不各铺一层重叠地面。

坐标是 glTF 世界坐标：x 向东，y 向上，z = −北。示范院 C02-010 的节点矩阵为 translate(531, 0, −818.45)。所有容差都是 C 值，取自 LY-005 E3：位置 5 mm，高程 2 mm；未声明的台阶容差 5 mm。

## 0. 开工前置检查（任一不满足就停在「待输入」）

| ID | 检查 | 通过条件 |
|---|---|---|
| P0 | G 冻结 | LY-001/002/005/006/007/008/009/010 的 status.json 都是交付完成。现在 008 和 010 未完成 |
| P1 | 示范院 | LY-010 冻结的院是 C02-010，矩阵为 `[1,0,0,0, 0,1,0,0, 0,0,1,0, 531,0,-818.45,1]`。否则换矩阵，全部重跑 |
| P2 | 基线 | lab main 仍是 bce3211，或者下面 §5 的 SHA 全部不变。任一 SHA 变了，就在新 main 上重跑 §1–§4 |
| P3 | 冻结接口 | registry 里 `LY-049:write:001` 仍为局部 x −5…−1、y −0.3…3.2、z 9…12；端口 `C02-010:gate-boundary:road-end` 是 v1；LY-082 的写入区从 z −806.45 起 |
| P4 | 前置席位 | LY-041 交了院坪基准（预期 0.200，复用）；LY-042 交了门叶互斥清单（预期不涉及院门）；LY-048 交了 service-opening 端口，并写明主门有没有门槛或门叶、有没有关闭态 |

## 1. 正例（现状复用路线，必须 PASS）

```
cd workpacks/LY-049/prep
python measure_gate49.py --lod LOD0 --out measure-gate-LOD0.json
python measure_gate49.py --lod LOD1 --out measure-gate-LOD1.json
python check_gate49.py measure-gate-LOD0.json
python check_gate49.py measure-gate-LOD1.json
D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P blender_xcheck49.py -- blender-xcheck-LOD0.json LOD0
D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P blender_xcheck49.py -- blender-xcheck-LOD1.json LOD1
python gate_components.py > gate-components.json
```

判定项见 `check_gate49.py`：

| ID | 内容 | 判据（基线实测值） |
|---|---|---|
| K0 | SHA 绑定 | 原型和四个地面原子的 SHA 与 §5 一致 |
| K1 | 足下支持完整 | 院内段（局部 z 6…9）和门道段（z 9…12）无支持格数 = 0。基线为 31,500 / 19,147 格，全部有支持 |
| K2 | 单层地面 | 两段的 maxLayers = 1，也就是门道里没有第二层地面 |
| K3 | 院界外不叠层 | 院界外 0…0.6 m 的 maxLayers ≤ 1，且全部有支持。这是 049 和 082 的叠面负检 |
| K4 | 阶差 | 相邻格高差 ≤ 5 mm，且建筑台阶格 = 0。如果交付时声明了台阶，必须用 `--declared-steps h` 逐一列出，实测与声明之差 ≤ 2 mm。基线为 0.000 |
| K5 | 净空 | 门道最小净空 ≥ 1.80 m，且 0.60 × 1.80 m 体探针在每一排都放得下。基线为 2.05 m，失败排 0 |
| K6 | 宽度 | 门道最小自由宽 ≥ 0.60 m。基线栅格值 2.12 m，精确值 2.13 m |
| K7 | 院界高程 | 院界两排（z 11.99 和 12.01）的 y 在 0.200 ± 0.002 以内，也就是与 `C02-010:ground-base` 一致 |

Blender 交叉检查 B1–B3（不在检查器里，要人工对照 JSON，或者以后并进检查器）：

- B1：`summary.allFloorOnSouth = true`，且 `floorY = [0.2]`。
- B2：z 9.55 和 11.65 两处楣下净空 = 2.05 ± 0.002。
- B3：z 10.6 和 11.0 处的横向命中 x = 526.435 / 528.565（± 0.005）；z 11.9 处为 526.0 / 529.0。

`gate-components.json` 里 `nonRoofComponentsIdenticalLOD0LOD1` 必须为 true。

## 2. 负例（必须被判 FAIL，用来证明检查器不是只会报 PASS）

```
python measure_gate49.py --lod LOD0 --drop-ground --out neg-no-ground-LOD0.json
python measure_gate49.py --lod LOD0 --inject threshold --out neg-threshold-LOD0.json
python measure_gate49.py --lod LOD0 --inject double-slab --out neg-double-slab-LOD0.json
python measure_gate49.py --lod LOD0 --inject overrun-slab --out neg-overrun-LOD0.json
python measure_gate49.py --lod LOD0 --standalone --out standalone-LOD0.json
python check_gate49.py --selftest      # 期望 selftestOK=true，输出 selftest-check.json
```

| 负例 | 模拟什么 | 期望失败项（基线 selftest 实得） |
|---|---|---|
| N1 去掉 ground-south | 默认加载、地面未打开 | K1、K2、K3、K5、K7 |
| N2 门槛 3 cm，未声明 | 有人偷偷加了门槛 | K4。同一个文件加 `--declared-steps 0.03` 后 PASS，说明声明机制有效 |
| N3 门道内叠一层 2 mm 厚板 | 049 在 ground-south 上再铺一层 | K2、K7 |
| N4 板越过院界 0.5 m | 049 侵入 082 写入区 | K2、K3 |
| N5 原型单独查看，不剔除 site 节点 | 拿资产卡预览冒充城里状态 | K0、K2、K3、K4、K7（15 mm 台阶，2 层） |

## 3. 制作后才跑的检查（只有转为新造时才需要；复用时记为「不适用」并写明原因）

| ID | 检查 | 通过条件 |
|---|---|---|
| M1 | 写入区 | 新 GLB 所有顶点经 N 变换后落在 `LY-049:write:001` 内（容差 5 mm）。z 不得超过 −806.45，x 不得超出 526.0…530.0 |
| M2 | 不碰原件 | 新件与 earth_wall、plain_timber 门区构件的三角-三角相交数 = 0。只允许合法接面：用 LY-008 的检查器分为接面、正体积侵入、完全包含三类，不能整对豁免 |
| M3 | 不双层 | 新件上表面与 ground-south 在同一格出现、且高差 < 0.10 m 的格数 = 0。如果新件要替换 ground-south 的局部，必须由 LY-090 出切孔或替换件，049 不能直接叠放 |
| M4 | 端口 | 填好的 `C02-010:gate-boundary:road-end` 的 local 和 world 都能用 N 重算，残差 ≤ 1e-6。world y 与实际地面竖直射线所测值相差 ≤ 2 mm |
| M5 | 撤回 | 关掉新件后重跑 §1，结果与基线 JSON 逐字段相同；原型和地面的 SHA 不变 |
| M6 | 官方检查 | 如果有公共文件，由 LY-100 跑 `lab/tools/build_assets.py --check`。本席位不跑，也不改 lab |
| M7 | 留空区 | 新件不进入 land-contract 的 `C02-010-entry`（x 526.3…528.7，z −807.65…−798.8），除非做过新的局部净空检查并写明 |

## 4. 端口交付值（预填候选；G 冻结后才正式填入）

```
portId   C02-010:gate-boundary:road-end  v1  kind road-end
local    position [-3.5, 0.2, 12.0]   up [0,1,0]   forward [0,0,1]
world    position [527.5, 0.2, -806.45]
opening  局部 x -5.0…-2.0（院界处 3.00 m）
         有效净宽为立柱之间 2.13 m（局部 x -4.565…-2.435）
         楣下净高 2.05 m
elevationClass  C-engineering
tolerance       position 0.005  elevation 0.002
measuredFrom    A2-LOD0 19b05202… / A2-LOD1 277e9e73… / south.glb 4313826d…
```

LY-082 那一侧的期望：在 z −806.45 这个面上，用同一个 portId 和版本；不在 z < −806.45 一侧放任何东西。

## 5. 要绑定的 SHA256（基线 bce3211）

| 文件 | SHA256 |
|---|---|
| assets/c02v/A2-LOD0-prototype.glb | 19b052022b2f6955e4a72f1a48280f7f8c229e11f001aa02ac95e357b890d9c7 |
| assets/c02v/A2-LOD1-prototype.glb | 277e9e73e8f2d8b8e07ec828671d37cc7c9e3f1653dcebfe4290c51de412d85d |
| assets/ground-atomic/south.glb | 4313826ddf5fbe0c0d8dcb4983d6cdbd647713d49faa1980cd34f587a3273a0e |
| assets/ground-atomic/retained.glb | aed8b3d4cb12aeaddf5c696a8a86355b15b7cb4fc8ebd76cc364d23789d630cc |
| assets/ground-atomic/network-ground-stitched.glb | fdfc3ce5c63305f79aa746b31c3be60f3d11a6acb75f190886124f2d3446db60 |
| assets/ground-atomic/D08.glb | 3ab933108b88c5c359fc7512d324e14f15157eaa54fb17f80f2adeb6c4626d9a |
| city-data.mjs | e4115705aeab28f2f6cc2635fbedfabf4158a08af9c626f6dd493ee27d430a1a |
| city-renderer.mjs | fa0a8dcbfaa5f5f8bd410f3d2295d788f32480c4dab316dd291a561d40d026ca |
| LY-006 registry/ports.json | 28bcfb68cd7d7fe0026f62de23ae3e45ba8f714a139e38c0b0957039f12fc633 |
| LY-006 registry/zones.json | 6b3595ac735d180866e823ddeb4e3676ffc0e816d083f6be2d57d6e4df0821c0 |
| LY-005 coordinate-contract.json | b6d7fe9db9523569383bf656df39aef63e7d80e8a1d5877196ba0bcab8747712 |

## 6. 不在本计划之内，不能声称

- 没有连续人体或车辆扫掠，没有动画行走，没有 GPU 或手机测试。
- 不评估结构安全，例如立柱与楣梁之间的 5 cm 空隙。
- 不判定历史门制。
- 「已入城」只指院和地面在城景里同时加载的状态；默认加载下 N1 就是实况。
