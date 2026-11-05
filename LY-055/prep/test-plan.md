# LY-055 测试计划（制作时直接跑）

适用对象：`workpacks/LY-055/` 下的装配包，即 assembly.json、新台脚或支持面 GLB、操作面 GLB 和安装场景。
运行器：`D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P <script> -- ...`。所有结果都写进 `qa/`，并记录输入和输出的 SHA256。

## 0. 必须绑定的 SHA（只读输入）

| 文件 | SHA256 |
|---|---|
| hand-mill-A.glb | 0fe50c2c0604237d9c6d011803550261b48304669b8dcb64f2155332af11c396 |
| hand-mill-B.glb | 598cadc7593300bc399773fc469a77830cabb540ad42baffeec3dbaccd478d36 |
| hand-mill-A-LOD1.glb | 5885f619799ef79071e6b2960866ff7cfb75fd4dcc838b341755924139fd1ede |
| hand-mill-B-LOD1.glb | 5ec42d1118def47115038f65c68bcd82aacf5cac208891cd2c9eb9066c0b57d3 |
| 基线 | bce3211f818ee5a8bef1773539da70695ba37b17（origin/main 已到 cad338b，石磨文件没有变化；开工时按 LY-001 的新快照替换并重跑 T1） |
| 测量脚本 | 绑定 `inputs.json` 的 prep_tools.scripts 里记录的 SHA；脚本一改，基准数就要重跑 |
| G 冻结件 | LY-005 坐标与高程契约、LY-006 端口表、LY-007 档位与材质表、LY-010 准入表：开工时填入各自的 SHA |

## 检查项

**T1 输入未变**：四个 GLB 的 SHA 必须等于上表。不等就停下，重跑 prep 测量，并更新本计划里的基准数。

**T2 节点保持**（`dump_nodes.py`）：安装后回读，每档仍是 18 个节点。除 `*_presentation_ground` 外，17 个节点的名称、世界包围盒（相对安装根矩阵）、材质名和三角面数都与 prep 的 `measure/nodes-*.json` 一致，容差 0.5 mm。
- 负例：任意节点平移 1 mm，或换材质，都必须判失败。

**T3 展示地坪处理**：`*_presentation_ground` 在安装状态下不可见或被剔除，并且是唯一一个被隐藏的节点。
- 负例：地坪仍可见，且它的顶面与城市地面的距离小于 2 mm（z-fight），必须判失败。
- 负例：多隐藏了任何一个 `*_C` 节点，必须判失败。

**T4 台脚支持**：从每根柱底 0.10×0.10 m 范围内的 5×5 个点向下打射线，必须先命中本包的台脚或支持面，**不能命中展示地坪**。容差：间隙 ≤1.0 mm，嵌入 ≤2.0 mm。四柱底的高差 ≤1 mm（A 和 B 原本都是 0）。
- 负例：把台脚下移 5 mm，必须判失败。
- 负例：把展示地坪留作唯一支持，必须判失败。

**T5 支持面接地**：台脚或支持面的底面打 7×7 射线，必须落在城市地面或本包地坪片上，间隙 ≤1 mm，并且不能有射线什么都没命中。支持面顶面在柱距范围内的平整度：A 柱距 0.77×0.72 m、B 柱距 1.07×0.72 m，高差 ≤2 mm（C 值，等 LY-005 定坡度后再确认）。

**T6 继承缺陷不变，但要披露**（`measure_mill.py` 的 support_rays 和 pairs）：
- 上石与下石的间隙：最小 2.0 mm ±0.3；最大 LOD0 5.6/6.0 mm，LOD1 2.0 mm。
- 上石与轴的最近距离：A 1.9 mm，B 3.0 mm，三角面相交 0。
- 上石与柄的最近距离：A 1.4 mm，B 3.0 mm，三角面相交 0。
- 轴嵌入承接盘 1 mm，与承接盘的三角面相交 48–50。

上面这些数字必须**原样保留**，并写进 qa 和公开限制说明，写作「上磨石组件展示间隙 2 mm，无承托」。数字被改小、改大，或者文案写成「无悬空」，都判失败。

**T6b 继承接触分类不变**（`classify_contacts.py`，网格 4 mm）：每档 30 对，分类计数必须是 face_contact 16、local_embed 1（承接盘与轴）、volume_intrusion 8（围板和横撑插进柱身）、bbox_only_no_contact 5（柄与上石、轴与上下石等，证明孔是空的）、containment 0；18 个节点全部闭合。侵入深度：围板 0.0498×0.0699×0.100 m（B 的 z 为 0.0998），横撑 0.0699×0.0498×0.0699 m，±1 个网格步长（4 mm）。
- 新件规则：台脚或支持面和柱底只能是 face_contact，或者 z 向厚度 ≤2 mm 的 local_embed；操作面和场景件与磨的任何节点都不能出现 volume_intrusion 或 containment。
- 负例（prep 已跑通，用 `make_negatives.py` 生成）：柱底套一块 0.12×0.12×0.04 m 的垫块，伸进柱身 20 mm，必须报 volume_intrusion（prep 结果：内点 2304，被包含比例 0.32）。
- 负例（prep 已跑通）：柱身里放一个 0.03 m 的立方体，必须报 containment（prep 结果：被包含比例 1.0，表面相交 0）。检查器要是只看表面相交，这一条就会漏掉。
- 公开文案必须写「围板、横撑与柱身实体交叠（示意榫接）」，写成「台脚无穿插」就判失败。

**T7 开口不被堵**（`measure_sweep_reach.py`）：
- 进料通孔：A 130 格（0.00325 m²），B 154 格（0.00385 m²），±5%，下方第一面仍是下石。
- 下石轴孔开口半径 12.5 mm，误差 ±0.5 mm。
- 柄与侧孔的三角面相交仍为 0。
- 新增件：台脚、操作面和场景件与磨的任何节点之间都不能产生新的三角面相交，台脚与柱底的接面除外，而且该接面要归为合法局部接面。

**T8 柄扫掠**：柄绕轴转一整圈，每 5° 一次，不能碰到任何静止件，包括新台脚、操作面、场景件和墙。prep 基准为 0 次命中（prep 用的是 10° 步长，共 36 个角位；制作时改成 5° 步长后重跑）。
- 负例：在柄端圆内放一个 0.05 m 的立方体，必须命中。

**T9 人体包络**（C 占位，不是认证）：躯干圆柱 r=0.20 m、高 1.70 m，放在 assembly 声明的每个站位上，对磨主体和整圈柄扫掠都必须 0 相交、0 包含。站位离床边不能小于 prep 的最小值：A 为 ±x 0.015、±y 0.040；B 为 +x 0.005、−x 0.070、±y 0.065，单位 m。
- 负例：躯干压入床面 5 cm，必须命中 `*_wood_bed_C`。
- 负例：躯干放在轴心，必须命中 7 个主体节点。

另外还要检查：站位的躯干圆柱底面 7×7 射线，必须落在操作面上，间隙 ≤1 mm，并且操作面不能被场景件占用。

**T10 够及超限保留**：每个站位都要输出「可够角度 / 超限角度」，C 占位够及为 0.60 m。prep 基准：A 四面均为 115°/245°；B 的 +x 为 55°/305°，其余为 115°/245°。qa 和公开文案必须写「单站位不能整圈够及」，不能写「可操作」或「已验证人体操作」。
- 负例：如果文案出现「可操作」，或者出现动画循环，检查判失败。

**T11 LOD 一致**：LOD1 与 LOD0 的节点集合相同，包围盒差 ≤1 mm，三角面数不同（4670 对 1524）。如果有 LOD2，也按同样规则检查。
- 负例：把 LOD0 改名充作 LOD1，三角面数相同，必须判失败。

**T12 安装与撤回**：在严格输入上先安装再撤回，撤回后回读 17 个 `*_C` 节点的矩阵、几何哈希和材质，必须与 T1 输入相同。城市原节点也必须不变。
- 负例：新旧两套方案叠载，比如展示地坪和新支持面同时可见，必须判失败。

**T13 规范**：每个单 GLB ≤15,000,000 字节；新件用米制，原点写明，贴图内嵌，有材质语义；`lab/tools/build_assets.py --check` 只在 LY-100 的合并分支上运行，本席位不运行。

**T14 范围**：输出里不能有产量、粮种、制粉效率、力学或安全认证这类说法。站立、就座等姿态只写作「C 占位」；B 低台不默认站姿。

## 基准测量的重跑方法

```
B=D:/Blender/blender.exe; F=D:/GitHub/creation-notebook-lab/docs/library/models/m-luoyang-hand-mill/files
for n in hand-mill-A hand-mill-B hand-mill-A-LOD1 hand-mill-B-LOD1; do
  $B -b --factory-startup --python-exit-code 1 -P prep/scripts/dump_nodes.py -- $F/$n.glb prep/measure/nodes-$n.json
  $B -b --factory-startup --python-exit-code 1 -P prep/scripts/measure_mill.py -- $F/$n.glb prep/measure/measure-$n.json
  $B -b --factory-startup --python-exit-code 1 -P prep/scripts/measure_sweep_reach.py -- $F/$n.glb prep/measure/sweep-$n.json
  $B -b --factory-startup --python-exit-code 1 -P prep/scripts/classify_contacts.py -- $F/$n.glb prep/measure/contacts-$n.json 0.004
done
```

制作阶段要把三个脚本扩展成能接收「安装场景 GLB + assembly 矩阵」，并且对新件（台脚、操作面）做同样的射线和 BVH 检查。只做表面 BVH 时，不能称实体碰撞已经穷尽。
