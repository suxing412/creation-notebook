# LY-057 测试计划（按「本项验收」，制作时直接跑）

本项验收原文有三条：
1. 瓦与承件真实接点、行缝遮盖、旧缺陷一一对应；
2. 新三档不破坏近景源码；
3. 新旧 SHA 与已发布的其他作业院明确区分。

工具：
- Blender：`D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P <脚本> -- <参数>`
- 判定脚本：`python -I prep/scripts/check_roof.py`（纯 Python，没有 Blender 依赖）

容差是本席位提出的 C 工程值。G 冻结后，要改绑到 LY-007/008/010 的冻结值，并把冻结文件的 SHA 写进 qa/。

## 00. 第 2 版：先按裁定选分支（T0）

LY-007 已经冻结了住屋瓦垄做法（D-RIB、D-RIB-LOD1、D-RIDGE-HOUSE，手册 §5.8）。旧棚与这套规则逐值吻合，见 `prep/out/style-zone-workshed.txt`。

因此 T1 / T2-pitch / T3 在两个分支下的判定**相反**。开工时必须先在 `qa/decision.json` 里写明采用哪个分支，以及依据（制作人原话或 LY-010 / LY-007 决议号），再跑后面的测试。

| 分支 | 含义 | 瓦这一层的判据 | 承件 |
|---|---|---|---|
| **A 沿用冻结做法** | 瓦落座、行缝不改 | `check_style_zone.py --expect-conform` 必须 exit 0（S1 全部 PASS，偏差 ≤ 1 mm）；T1/T2-pitch/T3 **不适用**，在 qa 里写「冻结做法，不改」；旧瓦字节不变，判复用 | 只做 T4b + T9 + T14 |
| **B 偏离冻结做法** | 另立 shed 档 | `check_style_zone.py --expect-deviate` 必须 exit 0；T1、T2、T3 必须 PASS；qa 里附偏离记录编号 | 同上 |

**本次已经跑过（分支 A 的正例，作用于旧件）：**

```
blender -b --factory-startup --python-exit-code 1 -P prep/scripts/style_conformance.py -- <workshed-LOD0.glb> prep/out/style-workshed-LOD0.json workshed_tile
blender ... style_conformance.py -- <workshed-LOD1.glb> prep/out/style-workshed-LOD1.json workshed_tile 0.56
blender ... style_conformance.py -- LY-007/models/samples/S84-LOD0.glb prep/out/style-S84-LOD0-ref.json tile
python -I prep/scripts/check_style_zone.py --style0 prep/out/style-workshed-LOD0.json --style1 prep/out/style-workshed-LOD1.json \
  --ref prep/out/style-S84-LOD0-ref.json --parts prep/out/parts-workshed-LOD0.json --tile workshed_tile --expect-conform
```

- 结果：S1 六项 PASS，偏差 0.0000 m，坡度 0.4741 等于参考值；Z1 PASS。exit 0。
- 关于 LOD1 用的 pitch 0.56：对 0.75 m 和 6.6 m 两种板段宽度，它给出的根数等于 n0//2（2→1，23→11）。如果新件的板段宽度不同，要改用直接按 n0//2 计算的规则。
- 绑定的 SHA：S84 参考件 93e02959878e86b790d727a40be6bab15d1a81449abfc7aa45977f45bcf45a5b；LY-007 decisions.json cb2870fc6966b59a5bd54d7071947c4f5cf588cf13a769ca41b08fc55b824598；手册 50e51a9358b1ba50fe5fbfcf1afad93dbb1c8a616d4a50d3faae17a9641f276d。

**分支 B 的负例**：对旧件跑 `--expect-deviate`，必须 exit 1，输出「still the frozen rule: revision is a no-op」。这条负例用来防止把旧瓦重新导出一遍就当成修订。

## 0. 绑定的 SHA

**旧件（负例，必须保持不变）**

| 文件 | SHA256 |
|---|---|
| workshed-LOD0 | 89e0a43923fb3868452903186b07299162fdf208a667c0d82630791b554ce726 |
| workshed-LOD1 | a21c2893a1cc7c7d8b69bb7c61b5d85f65f17fc352d003ff67ed9da4ea502671 |
| workshed-LOD2 | 7c054863f1088ddc8709592dfbfe70e2a581dc8ef91d4741c02aa65a0d0a614e |
| workyard-LOD0 | 7eb9739ec09a1ebbbcf16891d14be1488fc484be72c4bae273ec1a993139d17e |
| workyard-LOD1 | 6baefbd0fc1bc08694e2a3b226b38d308f8a214b70464c72e75e0c907dfb540f |
| workyard-LOD2 | 574d81d91d3898bf9de5e3d46b2b7d8532dd2c1b52d4ac35f7132898a1babda0 |
| foot-pestle-LOD0 | 6f0e41834121fa26cb36303606133256e8a8226e4c49464f68dc93646d181068 |
| foot-pestle-LOD1 | d8759dd6e0b0880325bb033e5031723e327f132c66a3cafd1aa97fed985cdd7c |
| foot-pestle-LOD2 | e94416ef307479eb4a3bf01652153d9c2ff0ba26300b4240920d580a5ae83453 |

**新件**：交付时把新件的三档 SHA 写进 qa/sha.json。所有测量 JSON 都带 `sha256` 字段，check_roof 的 T8 会核对文件与测量值是否一致。

## 1. 负例先跑（证明检查有效）

已在准备阶段跑过，结果保存在 `prep/out/negative-control-workshed.txt`：
- T1-seat：LOD0 和 LOD1 失败，实测 −32.4..+15.2 mm
- T2-pitch：失败，行距 0.287..0.375 m
- T3-ridge：失败，40/41 采样点是裸瓦床
- 判定为「NEGATIVE CONTROL OK」

制作完成后要重跑一次，保证检查脚本没有被放宽。
```
blender ... measure_roof.py -- <旧glb> out/roof-old-LODn.json workshed_tile workshed_timber
blender ... slab_section.py -- <旧glb> out/slab-old-LODn.json workshed_tile 0.0
python -I check_roof.py --lod0 ... --lod1 ... --lod2 ... --ridge out/slab-old-LOD0.json --ridge1 out/slab-old-LOD1.json --expect-fail
```
预期：exit 0，并且输出里 T1 或 T3 至少有一项 FAIL。

## 2. 正例：新件必须全部 PASS

```
blender ... measure_roof.py -- models/<新>-LOD{0,1,2}.glb out/roof-new-LOD{n}.json <新瓦节点> <木件节点>
blender ... slab_section.py -- models/<新>-LOD{0,1}.glb out/slab-new-LOD{n}.json <新瓦节点> 0.0
python -I check_roof.py --lod0 out/roof-new-LOD0.json --lod1 out/roof-new-LOD1.json --lod2 out/roof-new-LOD2.json \
  --ridge out/slab-new-LOD0.json --ridge1 out/slab-new-LOD1.json \
  --glb0 models/<新>-LOD0.glb --glb1 ... --glb2 ... \
  --forbid-sha <上表 9 个旧 SHA>
```

| 编号 | 检查 | 容差 / 判据 | 对应旧缺陷 |
|---|---|---|---|
| T1-seat | 每根瓦条每个站点的最低接触线减瓦床面（实际承托面） | ±3 mm；没有任何采样点「下方无床」 | 4.2：檐端 −35 mm 嵌入、脊端 +18 mm 悬空 |
| T2-pitch | 同一坡内行距的最大值减最小值 | ≤ 5 mm。若在 assembly.json 里声明了边垄规则（数值加理由），可单独放行最外两垄，但必须写出它们的实际值 | 4.3：0.287 / 0.331 / 0.375 m |
| T2-seam | 屋面投影内俯视首击 | none = 0，timber = 0 | 漏天检查（旧件已通过，属于回归项） |
| T3-ridge | 沿脊线俯视首击 | 裸瓦床 0 个；none 最多 1 个，只允许出现在端点采样 | 4.3：92.8 mm 脊缝，40/41 个采样点裸露 |
| T4-support | 瓦床底面与每根承重檩顶面的差值 | ±3 mm；至少 3 根承重件 | 4.4（旧件已通过，属于回归项） |
| T4b-span（手工判定） | 新增椽或承瓦件后，从 measure_roof 的 slab_vs_timber_top 里列出全部承重件和最大无承托跨 | 数值写进 qa/。如果决定不补椽，要在 brief 里写明这是 C 选择 | 4.4：1.66 m 净跨、0.49 m 檐挑、0.45 m 山挑 |
| T5-envelope | 按 LY-007 lod-rules（fbf53757…）：LOD1 包围盒与 LOD0 **逐值相同**；LOD2 一般 ≤ 0.02 m，house 家族删瓦垄后最高点下降 ≤ 0.10 m（旧件实测降 0.0997 m）。三角比 LOD1/LOD0 在 [0.17, 0.62]，LOD2/LOD0 在 [0.05, 0.2]（旧件实测 0.320、0.143） | 见左 | 不以低档掩盖问题 |
| T14-zone | 所有新件和改件都在 LY-006 写入区 LY-057:write:001 内。Blender 框 x ±4.05、y −0.45..4.45、z 2.8..4.2，容差 1e-4。命令：`check_style_zone.py --new <新节点…>` 的 Z1 项。负例：在 z 2.79 处放一根测试椽，必须 FAIL | 严格 | LY-006 zones.json 6b3595ac… |
| T15-port | 交付端口 `workshed:shed-floor:floor` 的 local / world / measuredFrom 值，容差位置 0.005、标高 0.002（LY-006 ports.json 28bcfb68…）；LY-058 能读回 | 严格 | LY-006 端口 |
| T16-intersect | 按 LY-007 §10 白名单检查交体：瓦垄、脊件可以入板；檩顶可以入板底，但埋入深度 < 板厚的 90%（0.117 m；旧檐檩实测 0.099）。新椽可以入板底，同样受这个限制。白名单之外的交体一律 FAIL | 严格 | LY-007 手册第 221–222、585 行 |
| T5-distinct | 三档 SHA 互不相同，瓦条数随档位递减 | 严格 | 不准把 LOD0 复制改名 |
| T7 | 新件 SHA 不在已发布 SHA 列表里 | 严格 | 新旧要分清 |
| T8 | 单个 GLB 的大小和 SHA | ≤ 15,000,000 字节；文件 SHA 等于测量 JSON 里的 SHA | 公共底线 |

## 3. 另加的人工或脚本项（在 qa/ 里留下证据）

- **T6 近景源码不被破坏**：生成 LOD1 和 LOD2 后，重新算新 LOD0 的 SHA，必须等于冻结时的值。三档都由同一份源或参数生成，LOD0 不因降档被改写。
- **T9 木件不动**：新件里的 15 根木件，逐件比较包围盒和三角数，差值 ≤ 1e-4 m。用 `parts.py` 导出 parts-*.json 后做 diff。新增的承件必须单独成节点并写明。
- **T10 双屋作业院不变**：workyard-LOD0/1/2 的字节 SHA 不变，任何时候都不能出现在 models/ 白名单里。
  - 第 2 版更新：LY-006 已把 `workyard:workyard_tile` 定为 LY-058 keep。
  - workyard 已在 origin/main cad338b 入城（C_NORTH_INFILL_03）。
  - 所以本席位**不提供**院内换屋面装配。下面这套映射只留作给 LY-058 / LY-100 的提案模板，并且需要 LY-006 改表后才能用：
  - 原节点 `workyard_tile` 中，棚体区域 x 2.5..7.5、y −5.6..2.6 的 55 个子件被隐藏
  - 新节点按 +90°、+0.2 m 的变换放入
  - 安装后再撤回，撤回后要逐字节一致
- **T11 足碓不碰**：新件里没有任何 pestle 节点；foot-pestle 三档 SHA 不变。
- **T12 剖面图**：同一机位前后对比。用 `section_render.py`，在 x = 0、x = ±3.86（最外垄）两处剖切；另出一张脊部特写。图上标注 CPU Workbench，不说做过 GPU 测试。
- **T13 结构 / 导入**：GLB 回读必须满足：UV、法线齐全；没有退化三角，也没有非有限值；纹理内嵌；材质名要表明语义（tile / timber）。可以用 mq 的 audit 流程，或者自写回读。

## 4. 不在本项验收内（不能写成通过）

结构安全、防水、GPU 或手机渲染、入城（city-data 无引用）、历史复原。这些在 qa/ 里一律写「未测」。
