# LY-082 测试计划：示范住宅外巷短接续

这份计划逐条对应任务池「本项验收」。开工时直接按本文跑。脚本都在 `workpacks/LY-082/prep/`，对 lab 只读。
下文 `LAB=D:/GitHub/creation-notebook-lab`。所有 Python 都用 `-I` 运行。

## 0. 前置：G 冻结后先重绑

1. 重新读取最新 main。用 `git -C $LAB rev-parse HEAD` 记下提交号。不得沿用 bce3211 快照。
2. 重新导出节点：`node export_city_nodes.mjs $LAB city-nodes-near.json`。导出结果里 `cityDataSha256` 必须等于 LY-001 台账登记的值。
3. 从各前置席位读取冻结值，写进 `expect.json`，交给 `check_lane82.py --expect`：
   - LY-010：示范院 ID；
   - LY-049：院界端口，包括 ID、版本、世界坐标、高程、宽度；
   - LY-081：巷面边 ID；
   - LY-005：地面基准；
   - LY-006：门前这一段 ground-south 的写入归属。
4. 当前绑定的 SHA（bce3211）如下。任何一项变了，所有结果作废重跑。

| 输入 | SHA256 |
|---|---|
| ground-atomic/south.glb | 4313826ddf5fbe0c0d8dcb4983d6cdbd647713d49faa1980cd34f587a3273a0e |
| ground-atomic/retained.glb | aed8b3d4cb12aeaddf5c696a8a86355b15b7cb4fc8ebd76cc364d23789d630cc |
| ground-atomic/network-ground-stitched.glb | fdfc3ce5c63305f79aa746b31c3be60f3d11a6acb75f190886124f2d3446db60 |
| ground-atomic/D08.glb | 3ab933108b88c5c359fc7512d324e14f15157eaa54fb17f80f2adeb6c4626d9a |
| c02v/A2-LOD0-prototype.glb | 19b052022b2f6955e4a72f1a48280f7f8c229e11f001aa02ac95e357b890d9c7 |
| c02v/A2-LOD1-prototype.glb | 277e9e73e8f2d8b8e07ec828671d37cc7c9e3f1653dcebfe4290c51de412d85d |
| city-data.mjs | e4115705aeab28f2f6cc2635fbedfabf4158a08af9c626f6dd493ee27d430a1a |

**前提条件（不满足就停）**：示范院和 C02_access 巷面都要拿到 LY-010 的区域准入，LY-081 要把这段巷面列为已通边。少了任何一项，本项状态写「阻断」，不生成任何地面，任务池原文是「没有实际目标或区域准入时停止」。

## 1. 「当前院界端口与实际巷面相接」

命令：

```
python -I measure_corridor82.py $LAB city-nodes-near.json corridor-<院>.json <院> --reach <门到巷心距离>
python -I check_lane82.py corridor-<院>.json --expect expect.json
```

C02-010 的 reach 用 6.45 m（门到巷心 z −800）。要连巷对面一起检查时用 12.75 m。

| 检查 | 正例判据 | 容差 | 现值（bce3211，C02-010） |
|---|---|---|---|
| K1 SHA 绑定 | 四原子 SHA 等于 expect | 完全相等 | 通过 |
| K2 承托连续 | 门洞宽 × reach 内无地面格 = 0 | 5 cm 格 | 0 / 15,300 |
| K3 台阶 / 坡度 | 相邻格高差 ≤ 5 mm，坡度 ≤ 5% | C 工程值，不是规范 | 1.7 mm / 3.49% |
| K4 端口高程 | 门洞线 y = LY-049 端口高程 ± 2 mm | ±0.002 m | 0.200 / 0.200 |
| K5 不叠层 | 通道内同一格出现两个以上文件的上表面：0 格 | 0 | 0 |
| K6 净空 | 体积盒内（y 0.205…2.2）的建筑三角包围盒命中为 0，LOD0 和 LOD1 都查 | 保守判定 | 0 / 0 |
| K7 巷面目标真实 | 通道终点落在巷面拱顶 z −803.0…−797.0 内，且该点在 LY-081 网络里是已通边 | 由 LY-081 判 | 几何上成立；网络待 081 |
| K8 有效宽度 | 过沟段 2 mm 平整宽度 ≥ 门框最窄净宽（LY-048 实测 2.10 m） | — | 2.46 m ≥ 2.10 m |

K8 用下面的命令跑，结果要求 `flatWithin_2mm` 的宽度 ≥ 2.10：

```
python -I crossing_width82.py $LAB crossing-<院>.json 525.0 530.0 -804.4,-804.0,-803.7,-803.3
```

还要做一次 Blender 独立复核，结果要求最大差 ≤ 1 mm：

```
D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P blender_xcheck82.py -- $LAB blender-xcheck.json
python -I xcheck_compare82.py $LAB blender-xcheck.json xcheck-compare.json
```

## 2. 「范围短且经准入」

- 如果判为复用，就没有新件，范围是 0。门洞到巷面边缘这段距离由现有 ground-south 承托：C02-010 是 3.45 m，C02-021 是 2.05 m。
- 如果要新造补件（见 brief 第 5 节的转造条件），补件必须满足：
  - XZ 包围盒只落在测得的断点格内。用新件加入前后两次 `measure_corridor82.py` 的 `noGroundCells` 差来定位，补件面积不得超过断点格面积加每边 0.10 m；
  - 长度不超过「院界端口 → 巷面边缘」的距离，C02-010 是 3.45 m；
  - 不进入 C02_access 巷面拱顶（z −803.0…−797.0）。巷面归 LY-081 或巷网，不归本项；
  - 不进入邻院地块，不进入 land-contract 中其他院的 entry 区。
- 负例：
  - 把补件平移到巷心以外，或者拉长到 10 m，检查必须报「越界」；
  - 准入状态写「未放行」时，检查必须报「阻断」，不出 PASS。

## 3. 「不与 049 叠面」

- 把 LY-049 的冻结件和本项件，或者本项的复用声明，一起加载，跑 K5。
- 两方都有件时，要求共用端口线两侧各 ±0.05 m 以外不存在两个文件同时出现上表面的格。端口线上只允许零宽接缝，接缝两侧高差 ≤ 2 mm。
- 只做上表面叠层检查是不够的。还要做完全包含检查：判断一层地面是不是被整体包在另一层的体积里。表面检查和完全包含检查的方法都要等 LY-008 的检查器。
- 负例：把 LY-049 的件复制一份，原位当作本项补件加载，K5 必须 FAIL。现判定器自测里的 N4_double_floor_patch 已覆盖这一点，`selftest-check.json` 中 7/7 例符合预期。

## 4. 「关闭补件后能恢复原断开状态」

- 先记录「原断开状态」的指纹。在当前城景默认加载下，地面原子都是 `initial: false`，相当于去掉 ground-south：

  ```
  python -I measure_corridor82.py $LAB city-nodes-near.json corridor-NEG.json C02-010 --reach 12.75 --drop-ground south
  python -I check_lane82.py corridor-NEG.json --neg
  ```

  这里 `--neg` 要求返回 PASS，表示确实检出断开。现值是 15,300 / 15,300 格无地面，从 v = 0.025 m 开始断开。用正常模式判同一个文件必须返回 FAIL。
- 如果有新件，验收时跑三次：
  - 加载新件；
  - 关闭新件；
  - 再加载新件。
  - 关闭态的 corridor JSON 去掉 `inputs` 字段后，与没有新件时的基线逐字节相同。地面原子、A2 两档和 city-data 的 SHA 都不变。
- 如果判为复用：把「关掉 ground-south 即断开」这个负例写进交付，并写明恢复方法是重新加载 ground-south。不能把加载配置的缺口说成几何已修。

## 5. 不得越界（每次都跑）

- 写入白名单只有 `workpacks/LY-082/**`。lab 工作树在 `docs/` 下保持 `git diff --quiet HEAD -- docs/` 为真。lab/data/* 已经被别人改过，与本项无关，不得顺手提交。
- 不触 13 院片区（x 480…640、z −1060…−962），不触雍门接街（x −26…−6、z −1414…−1382）。新件的包围盒必须和这两个范围都不相交。
- 不改 C02-010 矩阵和院数。用 `export_city_nodes.mjs` 前后两次导出的 nodes 段比对，要求相等。

## 5b. K9 写入区与所有权（对 LY-006 registry v1，每次都跑）

```
python -I zone_check82.py D:/GitHub/creation-notebook-workpacks corridor-<院>.json crossing-<院>.json zone-check.json
```

要绑定的 SHA：

| 文件 | SHA256 |
|---|---|
| zones.json | 6b3595ac735d1808… |
| ownership.json | ecbbbcf5614d41bf… |
| ports.json | 28bcfb68cd7d7fe0… |
| seams.json | ca4d81f8f955333c… |

完整值见 `zone-check.json` 的 `registrySha256`。registry 一旦升版，就要重跑。

| 检查 | 判据 | 现值 |
|---|---|---|
| K9a | 门洞在 `LY-082:write:001` 的 x 范围内，且门洞线就是本区的 z_min 面（−806.45） | 通过 |
| K9b | 每条过沟剖面的 2 mm 平整段都在本区内 | 通过 |
| K9c | 与其他席位的区相交体积为 0，只允许面接触 | 0；面接触 5 个 |
| K9d | `gp:city-node:ground-south` 的 owner 是 LY-090；本项交付里不得出现 south.glb 的差异件 | 通过 |
| K9e | 端口 `C02-010:gate-boundary:road-end` v1 已声明，consumers 含 LY-082 | 已声明；数值未填 |

- 049 交付后，K4 的期望高程改用端口 world 值，不再用默认值 0.200。
- 如果要新造补件，补件必须叫 `gp:LY-082:<name>`，XZ 只能落在本区的 z −806.45…−803.0 这一段，不得伸进 ground-south 的巷面拱顶。

负例：把检查盒改成伸进 LY-049:write:001 0.1 m，K9c 必须 FAIL。这条注入例要在开工时补进 `--selftest`。

## 6. 判定器自测（每次改检查器后跑）

```
python -I check_lane82.py --selftest
```

必须返回 0。当前覆盖的例子：

| 例子 | 预期 |
|---|---|
| P0 现状 | 通过 |
| N1 去掉 ground-south | 失败 |
| N2 注入 5 cm 台阶 | 失败 |
| N3 端口偏 15 mm（例如误用原型院坪 0.215） | 失败 |
| N4 双层地面 | 失败 |
| N5 SHA 漂移 | 失败 |
| N6 体积命中 | 失败 |

## 7. 报告里必须写明的局限

- CPU 高度场，5 cm 格，格心重心插值。不是实体碰撞，也不是连续人体或车辆扫掠，也没有做 GPU 或浏览器测试。
- 体积检查是三角包围盒对盒子，属于保守判定。
- 「局部通行通过」只在四原子都加载时成立。默认加载状态下不成立。
- 巷面宽度、浅沟和过沟段都是 C 设计，不是考古尺寸。
