# FOLIO 006 · 数字几何门禁与真实反例

2026-11-01 UTC。检查器作者与造型/渲染作者分工；本记录不是制造、承载、稳定性、人体工学或实时图形验收。以下区分候选/边界和正式资产；不能用候选记录替代正式资产的哈希同一性检查。正式 Folio / Atlas / Spire 已分别用最终锁定检查器复跑并通过，三个正式 GLB 均与对应已审候选逐字节相同。

## 已建立的门禁

`source/check.py` 只接受本 recipe 的单件壳体：恰好 1 个 mesh、1 个材质槽、每件恰好 1 个连通分量，无 modifier / shape key / constraint / parent / object 或 mesh animation_data 与 driver、identity 对象世界矩阵、有限世界坐标、正世界空间有向体积、全部二面边局部绕序一致；实际顶点与对应 recipe 顶点误差 ≤ 0.2 µm，全部无向索引面循环相同。这个配方恒等约束会拒绝合法重索引后的网格，也会拒绝新增/偷换几何；它**不是通用几何正确性证明**。

独立数值项包括三角面积、重复三角、非流形边、非相邻 BVH 自交候选，以及双精度平面/二维 SAT 正面积重叠。006 没有装配 pair 白名单；同一 object 增加穿出实体或完全包容岛不能借用 005 的连接例外放行。

`source/check_glb.py` 验证真实 GLB 二进制坐标/法线/索引、内嵌资源、声明极值与字节值、有效 stride、offset 非负且对齐、bufferView 边界和导出三角面积。它不是 GPU 渲染器，也不是 native 与 GLB 全拓扑同构证明。

## 实际模型回归

`gate-regression.json` 记录每份模型和检查器 SHA-256。下列 6 个候选/边界 Blender 模型全部通过最终锁定 native 检查器；另对正式 assets/{folio,atlas,spire} 分别重跑通过（共9次当前锁定版本真模型测试）；各自 GLB 也通过当前 payload 门禁。

| 文件位置 | 三角形 | 最小三角面积 m² |
|---|---:|---:|
| review/first-version | 11,276 | 6.38893e−9 |
| work/refined-draft / Folio | 12,044 | 6.38893e−9 |
| work/atlas-draft | 10,988 | 6.38893e−9 |
| work/spire-draft | 13,004 | 6.38940e−9 |
| work/gate-boundary-low | 10,460 | 4.21551e−9 |
| work/gate-boundary-high | 13,148 | 6.38962e−9 |

三个正式造型候选和两个边界模型均单连通；退化、重复、非流形、局部绕序错误、非相邻自交、共面正面积重叠均为 0。只是这些有限样本通过，不代表整个连续 9 维参数域已证明。

## 不能掩去的共面数值失败

第一次继承 005 的 `cos ≥ 1−1e−10`、点平面距离 ≤10nm 门禁，在 006 很短的弯曲三角上出现专项漏检。将一片真实斜向三角围绕中心缩小至 55% 后存为 Blender float32 顶点，原面到新三角的最大点平面偏差约 **8.823nm**，但两单位法向量 dot 为 **0.9999999955347064**。双精度算术不能还原已量化的顶点；仅继承 005 的 double precision 修复不足以处理这项尺度。

整体门禁当时仍拒绝（额外岛、非流形和 BVH 候选），但**共面专项字段为空**，不能计作专项覆盖。原证据保留：

- `gate-fault-tests-initial.json`：第一次 14 项测试，仅斜共面专项未命中。
- `gate-coplanar-initial-validation.json`：原实际失败报告。
- 原反例/日志及检查器快照分别在 `work/gate-faults-initial/` 和 `work/gate-check-initial.py`；坏二进制不应公开作正常资产。

修复改为 `cos ≥ 1−1e−7`，且**两组三角对彼此平面**的所有顶点距离均须 ≤50nm，投影 SAT 正重叠阈值仍为10nm。空间 AABB 网格只加速候选，不再把法线/平面放入硬桶。精确说这是**近共面正面积门禁**，不应称符号几何共面证明。

首个数值失败可用 `python source/test_coplanar_quantization.py` 纯源码复建：脚本生成 revision 0 基线，固定原窄斜 loop triangle 298，并校验其斜率、宽度和短边范围，再做55%内缩、旧阈值/当前阈值和 +1µm 控制组三次实际检查。无需发布任何坏 `.blend`；报告为 `gate-coplanar-quantization-reproduction.json`。

修复后同一反例明确报 1 个共面正面积重叠；当前所有真模型继续通过。对同一内缩三角沿自身法向移动 **1µm** 的控制组，共面与 BVH 字段均为0（模型仍因新增岛/配方不符而整体拒绝），证明并非“所有叠影一律标共面”。见 `gate-coplanar-fixed-validation.json`、`gate-coplanar-offset-control.json`。

## 新反例揭示世界/局部体积门禁盲区

这是**人为构造的新反例揭示检查器盲区**，并非发现交付 FOLIO 已经损坏。首个门禁读取世界顶点进行包络与 BVH 检查，却使用 `bmesh.calc_volume(signed=True)` 的**局部空间**体积判定朝向。将正式 Folio 原网格局部 X 镜像、对象 X 缩放设为 −1，再反转全部面，世界顶点仍与原资产完全一致、局部绕序仍一致、局部有向体积仍正；原 checker 实际错误 PASS。

`gate-world-inversion-before.json` 保存真实旧 PASS；局部体积约 **+0.000340456822m³**，实际世界体积约 **−0.000340456822m³**。`work/gate-check-before-world-volume.py` 保存当时检查器；没有改写冻结的 005。

现在以世界三角顶点的双精度行列式和计算有向体积，并另行要求本 recipe 的对象世界矩阵为 identity（各项容差1e−8）。`gate-world-inversion-after.json` 明确命中 `non_positive_world_volume`，而不只依赖 transform 例外拒绝。全套真实模型及反例已用新 SHA 重跑；正式 Folio 在纯模型状态契约加入后再次通过，最终锁定检查器报告是 `gate-locked-asset-folio.json`；`gate-world-fixed-asset-folio.json` / `gate-asset-folio.json` 是历史检查版本，不应被当作新 checker 的结果。

`source/test_faults.py` 已包含反例构造，并在 work 下派生旧 local-volume-only 策略工作快照，实际复现旧错误 PASS，再断言当前 checker 拒绝。公开源码无需附带旧坏二进制即可重建此失败；最终测试 JSON 的 `historical_policy_reproduction` 明确区分旧策略与当前门禁。

## 18 个真实故障注入

`gate-fault-tests.json` 以正式 **assets/folio** 为基线实际生成并检查 12 个 native / 6 个 GLB 反例，全部被拒绝且指定检测项触发。首版/改进版基线的历史15项结果分别保留 `gate-fault-tests-first-version-final.json` / `gate-fault-tests-refined-final.json`，不把旧记录改写为18项。

- 反转局部面 → `inconsistent_winding_edges`。
- 完全包容的0.4mm小岛 → `invalid_connected_components`；无表面交叉，BVH不能替代此项。
- 同一 object 加入穿出壳体的棱柱 → `nonadjacent_self_intersection_candidates`。
- 斜向正面积内缩叠片 → `coplanar_positive_area_overlaps`。
- 缺面 → `nonmanifold_edges`。
- 零面积三角 → `degenerate_triangles`。
- 重复真实三角 → `duplicate_triangles`。
- 两片不共享顶点的相交三角 → `nonadjacent_self_intersection_candidates`。
- 保持原拓扑/连通性、移动一个顶点10mm → `recipe_vertex_envelope_failures`。
- 局部 X 镜像 + 负 X 对象缩放 + 全反面（世界顶点不变）→ `non_positive_world_volume`，另有 identity transform 契约拒绝。
- Solidify modifier（原网格不变）→ `model_state_contract_failures.reason = modifiers_present`。
- Shape Key deformation（原网格不变）→ `model_state_contract_failures.reason = shape_keys_present`。两项添加前后原顶点/面SHA完全相同，其余几何缺陷字段均空；不是借由碰撞或配方变形误打误撞拒绝。
- 实际 GLB POSITION NaN、越界索引、零长度法线、过小 stride、accessor 超出 bufferView、负 offset → 对应明确 payload 拒绝。

没有以“整体被别项拒绝”冒充指定检测覆盖。当前 native 检查器 SHA-256 为 `c15823a58e072f1ca21ec63a1696eff90e7928f0f86e594b6a898f33bd07f99c`；GLB 检查器为 `5fa7561e3c23dd7a1059e7d8a8075dc0ca235db098c9f4a80845b5660d926feb`。

纯 `model.blend` 与摄影 `scene.blend` 明确区分：前者严格只允许一个 MESH 对象，不能偷偷加入可改变 evaluated geometry 的上述状态。摄影场景含地面、相机和灯光，不走此门禁。这里只对明确列出的纯模型契约负责，不宣称支持任意 Blender evaluated scene。

## 输入与站点实测

`gate-input-tests.json`：108/108 输入测试符合预期，覆盖9参数上下界/越界、NaN/±Inf/布尔/字符串/null、名称路径和字符、seed类型、严格键集合及版本。512个参数盒角点仅通过 validator 检查，其中320接受、192拒绝（128个内弯半径约束、64个邻弯修剪后直段不足）。**没有生成320个网格，更没有做连续域证明。**

`gate-station-measurements.json` 实际读取5个改进版候选/边界 native 网格，在全部对应站点测量顶底点间距和4个弯的内外半径。Folio对应点厚度为 **2.9999855–3.0000103mm**，各弯半径约为 **6.5 / 9.5mm**。Folio地平面样本的前/后 Y 区间分别为 **[−127.812, −90.908]mm / [108.619, 135.812]mm**。这是离散网格站点实测，不是全表面连续最小厚度、接地面积或制造公差证明。

## 正式资产检查与同一性

三个正式资产分别见 `gate-locked-asset-{folio,atlas,spire}.json` 与 `gate-asset-{folio,atlas,spire}-glb.json`。正式 `.blend` 是重新保存的文件，不能宣称与低采样候选字节相同；每份正式文件均以其自身 SHA-256 在锁定 checker 下重新通过。三个正式 GLB 与候选逐字节相同，配置、尺寸、包围盒一致。`gate-asset-*-identity.json` 保留这些比较；摄影元信息已补齐，三份 model-info 最终哈希已刷新；`gate-final-asset-identity.json` 汇总正式字节、当前 checker 与候选GLB身份，全部通过。

## 可复跑命令

```sh
python source/test_contract.py
python source/test_coplanar_quantization.py
python source/test_faults.py --baseline assets/folio --output work/gate-faults-folio
blender -b --python-exit-code 1 --python source/check.py -- --model PATH/model.blend --info PATH/model-info.json --report report.json
python source/check_glb.py PATH/model.glb glb-report.json
```

在 `study-006` 目录运行。反例脚本默认将坏模型放在 work 下，报告放 review；不得将坏二进制当正式模型发布。

## 剩余限制

- BVH 项排除共享任意顶点的三角，非共面相邻折叠未被完整独立证明；配方全顶点/拓扑恒等约束降低受约束资产被偷偷改形的风险，但不能代替通用相交证明。
- 共面/近共面检测为容差数值计算；像素渲染、硬件深度精度、GPU、WebGL、iPhone、动态闪烁均未测。
- 测量和碰撞通过不表示材料加工、折弯余量、回弹、公差、载荷、稳定性或人体工学验证。
- 候选与正式文件的记录已分开。三个正式native均在锁定checker下以自身SHA重跑；三个GLB候选身份与最终metadata哈希已核验，不借用中间报告冒充正式资产。
