# Study 005 · 独立几何 QA 审查

审查日期：2026-11-01 UTC。只读检查 worker 的源代码、原生模型与报告；所有派生反例、检查器快照、独立日志均在同级 `study-005-independent-review-assets/`，未修改 worker 文件。反例不是交付资产，不应发布。

## 当前结论

**已闭环本次发现的门禁缺口；5 个实际模型的最终静态门禁独立通过。** 审查实际复现了三类原生门禁漏检、两类 GLB payload 漏检，以及一项共面专用检测漏报。worker 修复后，我独立重跑了 Hush / Poise / Reach 与两个边界模型的 native + GLB 检查，全部通过；4 个 native 反例均被拒绝且相应专用检测触发；2 个坏 GLB 也被拒绝。正式目录的三份 `.blend` 与三份 `.glb` 已逐一确认与已审暂存资产 SHA-256 完全一致；源码检查器也未变。最初错误 PASS 的证据完整保留，不把它改写成“从来无误”。

这些是**门禁覆盖缺口**，不等于原始 Poise 模型已经出现这些错误。对原始 Poise 的独立顶点、拓扑和 GLB payload 检查未发现所注入缺陷。

## 1. 检查版本与证据链

- 稳定基线：`study-005/work/repro-a/model.blend`、`model-info.json`，recipe 1.1.0，Blender 4.3.2。
- 最初 native 检查器快照：`check-snapshot.py`，SHA-256 `b288b16db83649f4eec525352cc0389da2f78da38fb434f980fd2c1b5942231d`。
- 最初 GLB 检查器快照：`check-glb-snapshot.py`，SHA-256 `26c304b14b41c16477405add52c95deb294961191e755db6b3efe55ce37cb98b`。
- 第一轮 native 修复快照：`check-fixed1-snapshot.py`，SHA-256 `bb3598b20060038602199a533bf0c93eb2a69111a0458131df27520279e6bde7`。
- 第一轮 GLB 修复快照：`check-glb-fixed1-snapshot.py`，SHA-256 `c14e3d285ea753e60e96a1ac54284cf08a3f1e1916b83b6ba5b344de9859be53`。
- 最终 native 检查器：`check-final-snapshot.py`，SHA-256 `faad6c4a1d54b384a5311970ed331ed72ff59171c39789ada27d148552e963ce`。
- 最终 GLB 检查器：`check-glb-final-snapshot.py`，与上面的 fixed1 GLB SHA-256 相同。
- 所有快照/反例路径以下均相对 `study-005-independent-review-assets/`。

## 2. 实际反例，不以别项拒绝冒充本项覆盖

| 用例 | 原检查结果 | 关键实证 | 已独立确认的修复结果 |
|---|---|---|---|
| `same-pair-pin-diffuser-extra-prism.blend` | **错误通过** | 在 pin1 同 object 内加入 1.4×1.4×12 mm 闭合实体，保留首尾端点与原接触。它穿出透光片上下表面。pin1–diffuser 相交候选 54→82，区域仍通过，缺陷数组全空。 | fixed1 拒绝：2 个连通分量、8 个有限 pin 包络外顶点、1 个接触区域失败。 |
| `allowed-hub-shell-contained-island.blend` | **错误通过** | 在 hub 同 object 中加入 0.4 mm 闭合岛，完全位于罩体内部，远离实际 socket；既无额外表面交线，也不改变原顶盖。 | fixed1 拒绝：2 个连通分量、8 个有限 hub 包络外顶点。 |
| `reversed-base-face.blend` | **错误通过** | 仅反转底座一片上盖面的绕序，位置/闭合二面边/总正体积仍保留。 | 最终版独立拒绝，明确报告底座 3 条绕序不一致边；不是依靠其他缺陷兜底。 |
| `nan-position.glb` | **错误通过** | 实际 POSITION 二进制中的一个坐标改成 NaN；原 accessor min/max 未变。 | fixed1 退出码 1：`Nonfinite accessor bytes`。 |
| `out-of-range-index.glb` | **错误通过** | 实际索引改成 65535，超过该 primitive 的 POSITION 数量。 | fixed1 退出码 1：`Index exceeds POSITION count`。 |
| `oblique-coplanar-overlap.blend` | 整体拒绝，但**共面专用检测漏报** | 罩三角内缩得到正面积斜向叠面。共面数组空；实际靠 3 条非流形边与 1 个 BVH 自交候选拒绝。 | 最终版独立拒绝，`coplanar_positive_area_overlaps` 明确为 1。 |

原始错误 PASS 报告保留为各用例的 `*-validation.json`；修复报告带 `-fixed1-` 或 `-final-`，没有覆盖旧证据。生成脚本为 `make-probes.py`、`make-reversed-face.py`、`probe-glb.py` 和 `probe-coplanar-threshold.py`。

### 共面阈值为何值得单独修复

原检查将 `mathutils.Vector.normalize()` 后的法向量直接用 `abs(n1.dot(n2)) >= 1−1e−8` 判断平行。对基线罩体 16,128 个三角逐一实测，**7,259 个法向量连 `n.dot(n)` 都低于该阈值**。例如三角 2 的结果为 `0.9999999723968358`。这不是角度偏差，而是 float32 法向量归一化/计算误差与过紧阈值不匹配。证据：`coplanar-normal-threshold.json`。最终版已改为 Python 双精度法向量/点积/平面计算，统一两三角的投影轴；搜索相邻法线桶和反向桶，不再把平面距离硬分桶。独立斜向反例现明确命中共面检测。

## 3. 装配政策审核

最初检查器已经不是“允许一个名字就整对放行”：8 构件的 28 对逐一报告；9 对允许指定装配关系，19 对必须分离；允许对要求真实三角交点处于区域内，并检查 137 个关键端点/顶盖点的实体内嵌深。

但原 `pin-hub` / `pin-diffuser` 区域只限制 XY 半径，没有 Z 限制；允许 pair 的内部采样不触发拒绝；每件也未限制连通分量。于是“保留原连接，同时新增同 pair 异常几何”能漏过。

fixed1 已增加：每构件恰好一个连通分量；pin 接触点的 Z 窗口；全部 pin 顶点的有限轴段及半径包络；全部 hub 顶点的有限圆柱包络。它们是针对本 recipe 的额外契约，不应宣传成适用于任意模型的碰撞证明。

## 4. 最终真实模型回归与独立基线数据

最终矩阵见 `final-independent-results.json`，记录每份输入模型、info 和检查器 SHA-256、退出码与具体检测项。9 个 native 用例全部符合预期（5 真模型通过、4 反例拒绝）；5 个真模型 GLB 全通过。所有真模型均 8 构件、40,256 三角，137 个端点/顶盖检查全通过，所有缺陷列表空。

| 实际模型 | Native / GLB | 罩–透光片采样最小距离 mm | 端点/顶盖通过数 |
|---|---|---:|---:|
| Hush | 通过 / 通过 | 16.3124 | 137 |
| Poise | 通过 / 通过 | 18.2093 | 137 |
| Reach | 通过 / 通过 | 18.8074 | 137 |
| 全低边界 | 通过 / 通过 | 15.6521 | 137 |
| 全高边界 | 通过 / 通过 | 20.3938 | 137 |

这张表是有限离散样本的检查结果，不是整个连续参数域证书。

`native-baseline-inspection.json`：原始 Poise 共 8 件、40,256 三角；每件均一个连通分量；所有坐标有限；每件有向体积正；非流形边均为 0。最小三角面积为约 `2.96414e−8 m²`，约为 `1e−12 m²` 退化阈值的 29,641 倍。旧门禁的未修改基线也已独立重跑通过，结果为 `native-baseline-rerun.json`。

`glb-independent-inspection.json`：独立解码全部 POSITION、NORMAL 和索引，原始 repro-a / repro-b 均为有限坐标、有效索引，法线长度约 `0.999999924..1.000000140`。两文件均 730,544 字节，SHA-256 都为：

`53aef1b5fc4ef9d70bef6dae9562d393c80c93016d46bba2b41b67f97cd1a078`

因此“同环境两次 GLB 字节相同”有实证；这**不是**跨硬件像素等价或渲染器等价。

Poise 原报告的罩/透光体**采样**最小面距离为 18.2093 mm，0 交叉候选、采样内点为 0/0；不能将这个采样值改称解析全局最小净距。

## 5. 圆角、扫掠与输入域

- 旋转构造使用单顶点极点，不是零半径重合整圈；环形透光片的内轮廓始终为正半径。罩壁明确为垂直 6 mm 厚，而非等法向壁厚。
- 保留的初版报告确实记录 recipe 1.0.0 的 Pin 1 出现 76 个退化三角，而不是只在复盘中口述错误。当前 sweep 根据切线方向选择 Y 或 X 参考轴，已避免早期沿 Y 销的平行轴奇异性。对 256 个参数盒角点先走实际 validator，96 个接受、160 个拒绝；仅对这 96 个角点的生成公式独立复算，最小切线/线段长度约 0.0053002 m，最小 `|tangent×reference|` 为 0.8528147，最小透光片内轮廓归一化半径为 0.1383333。证据：`analytic-sweep-corner-check.json`。
- 上项只是**扫掠相关公式检查**，未为 96 套实际网格跑全 QA，更不是连续 8 维参数域证明。当前 `tube()` 也不是面向任意路径的平行运输框架，不能直接把受约束结论推广到会跨参考轴切换阈值的任意曲线。
- 独立输入测试 54/54 符合预期，包含 8 参数上下界/越界、NaN/±Inf、布尔/字符串/null、名称路径/换行/Unicode、额外/缺失键、seed 类型、recipe/Blender 版本和 3 项耦合条件。证据：`input-contract-independent-tests.json`。未改写 worker 的 47 项原报告。

## 6. 仍须明确保留的限制

1. BVH 自交排除共享任意顶点的三角；非共面相邻折叠没有完整证明。共面独立检测也不等于精确符号几何。
2. 原共面分桶边界漏检与 float32 法向量问题已针对性修复；最终仍为数值容差检测而非精确符号几何。射线多数票和顶点子采样仍可漏小型/细薄异常。需要明确写“有限测试”，不能只写“无自交”。
3. 内部实体采样、近面距离不是所有边/面连续极值搜索；所有局部形变、制造公差或装配可行性没有被证明。
4. native 检查针对当前 recipe 的对象排序、顶点环约定和构件数量；不是通用 Blender 文件检查器。
5. 未测 GPU、WebGL、动态深度闪烁、真实 iPhone。没有修改浏览器 GL、调用额外 AI/API/账号、外传或发布文件。
6. 本审查只独立验收纯模型、静态门禁、GLB 字节和正式目录同一性；CPU 图的逐像素视觉评审由模型/主任务负责，不在这里借用静态 QA 宣称图像质量或实时状态。

## 7. 最终阈值与判定的准确含义

- 退化：三角面积 `<1e−12 m²`；重复：世界坐标逐分量 round 到 8 位小数后的顶点集合相同，**不是**欧氏距离球内相同。
- 非流形：任一非二面边拒绝；绕序：二面边但非 `is_contiguous` 拒绝；每构件必须单连通且总有向体积正。
- 非相邻 BVH：epsilon 0，排除共享顶点的三角。相邻非共面折叠仍不是完整证明。
- 共面：双精度法线；`abs(dot) >= 1−1e−10`，点到平面偏差 `<=1e−8 m`；法线桶宽 `1e−4`，搜索同向/反向邻桶；二维 SAT 要求各分离轴正重叠 `>1e−8 m`。
- 三角交点参数与重心坐标接受余量 `1e−6`；内部射线为三方向多数票，起点偏移 `3e−8 m`、每次命中后前进 `3e−7 m`、每方向最多 80 次命中，单射线距离 5 m。
- pin 全顶点包络：有限轴段端点余量 2 µm，半径上限 1.402 mm；hub 全顶点包络：有限高度上下余量 2 µm，半径上限 11.002 mm。
- 接触 Z 窗口：pin 名义中心高度 ±1.42 mm；pin 端点实体内深度 0.5–2.5 mm，stem 端点 3–5 mm，hub 顶盖 0.2–4.5 mm。

## 8. 正式资产同一性已核对

2026-11-01 20:54 UTC，独立执行 `verify-final-identity.py`：`assets/{hush,poise,reach}/model.blend` 与 `model.glb` 的哈希全部与已审暂存文件一致；参数、尺寸、包围盒一致；正式 native/GLB 报告均通过，`realtime_verified` 均仍为 false；两个门禁源码的哈希与最终快照一致。结果记录在 `final-asset-identity.json`。这关闭了“拿中间资产报告冒充最终冻结资产”的版本风险，但不重新证明渲染、WebGL 或 iPhone。

| 正式变体 | `.blend` SHA-256 | `.glb` SHA-256 |
|---|---|---|
| hush | `2fdfa7d7448c8c6fbc1fa879c187b33a59341658b1d10ecf66f803a449629c76` | `ddb9a99b9d89002d5076cba06ba3264396e5701854693d8621cf86ea10d3be73` |
| poise | `1c1ad3d58a9d9d2dd331612d49e2bfc862d1d868d5d37dfb58988b474a1ce791` | `53aef1b5fc4ef9d70bef6dae9562d393c80c93016d46bba2b41b67f97cd1a078` |
| reach | `4d99db4b5f22dd7a5d569c49bb640a1ecb77bba31b6753fd15719109b3aeeab0` | `a1421fa2bbd5a2c85df6b404b508be670d79a30d43b8feb5c13576663b8c29a8` |

可复现命令入口：

```sh
python study-005-independent-review-assets/run-final-independent.py
```

该独立 runner 使用固定检查器快照，写入独立目录；扫描当前 assets 下各变体的 model-info，复检 3 变体、2 边界与 4 native 反例。坏 GLB 的生成脚本和修复日志也在同目录。
