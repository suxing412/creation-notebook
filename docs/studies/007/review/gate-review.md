# ORISON 007 · 原生闭合扫掠门禁与真实反例

2026-11-01 UTC。门禁作者与建模/摄影作者分工。正式 Orison / Latitude / Ascend 已在各自最终文件上重新检查；本记录不是制造或实时图形认证。

## 本家族契约，不是折板白名单

[完整机器可读契约](gate-contract.json)。单位米，native Z-up；中心线主要位于 XZ 面并有 Y 起伏。截面是带真实几何圆角的矩形：每象限8段圆弧离散，合计36个截面顶点，并非着色器假圆角或无限分辨率曲面。320个唯一中心线站点周期扫掠，以 modulo 索引连接最后/第一环，无端盖和重复终点环。恰好一个连通、封闭、可定向 genus-1 网格；没有任何装配或碰撞 pair 豁免。

frame 是固定 Y 参考向量投影、叠加周期 roll 的**解析周期 frame，不是 RMF / 平行运输**。检查解析 position / tangent / N / B 与截面在首尾参数的残差；逐一验证36条接缝连接边的双面邻接与全部接缝面。对实际网格320个环拟合截面局部 N/B 和中心，检查实际环形变、旋转失配与重复端环。

[check.py](../source/check.py) 只接受 raw 纯模型：恰好1个 MESH 对象、1个材质槽、identity 世界矩阵；禁止 modifier、shape key、parent、constraint、object/mesh animation_data 与 driver。摄影 scene.blend 不走此门禁。全部世界空间顶点按既定索引与配方距离≤0.2µm、全部面索引循环及重数一致；这会拒绝合法重索引模型，属于受约束配方身份，不是任意网格的独立正确性证明。

另检查退化/重复三角、非流形边、每条二面边局部绕序、正**世界空间**有向体积、连通分量和 χ=V−E+F=0；以闭合/连通/可定向条件解释 genus=1。通用组件遍历、BVH、双精度世界体积、双向近共面 SAT 取自006经修复的数值基础；007的周期/截面/frame/genus/曲率与间隙契约独立编写，没有沿用折板构件或顶点白名单。

## 数值限制写在判据旁

- 非相邻 BVH 项排除共享任意顶点的三角。非共面相邻折叠未被完整独立证明；全顶点/拓扑身份约束不能被宣传成通用相交定理。
- 近共面判据：|normal dot|≥1−1e−7，**双方**所有顶点到对方平面≤50nm；二维投影 SAT 的正重叠阈值10nm。计算提升至float64，但输入仍是Blender float32，不能恢复其量化损失。没有动态深度闪烁验收。
- 在960个周期参数上重新计算 κ×当地截面外接半径，要求<0.72；frame参考正弦≥0.65。有限非局部中心线距离减两处半径≥6mm；排除弧长≤2.8×最大截面半径的局部邻域。
- 上述960采样的算术与配方640点 diagnostics 分开实现，但都使用配方解析 point/derivatives/profile；不是独立推导的曲线、连续 swept-volume 定理或连续参数域证明。

## 最终正式资产

| 正式变体 | native / GLB 顶点 | 三角形 | 最大 κr（960点） | 有限非局部间隙 mm |
|---|---:|---:|---:|---:|
| Orison | 11,520 / 11,520 | 23,040 | 0.339074 | 24.4165 |
| Latitude | 11,520 / 11,520 | 23,040 | 0.469099 | 27.8325 |
| Ascend | 11,520 / 11,520 | 23,040 | 0.532113 | 21.0208 |

三个正式对象均 V=11,520、E=23,040、F=11,520，χ=0，一个连通分量、genus1；接缝、frame、退化、重复、非流形、绕序、非相邻交叉及近共面重叠门禁均通过。实际数值、输入SHA、检查器SHA、recipe SHA与每次新run_id分别在：

- [Orison 最终身份](gate-locked-orison-v2-identity.json)
- [Latitude 最终身份](gate-locked-latitude-v2-identity.json)
- [Ascend 最终身份](gate-locked-ascend-v2-identity.json)
- [三资产与原26项及输入证据同一性汇总](gate-final-asset-identity.json)

正式 `.blend` 是新保存文件，不能借候选报告冒称同一字节；三份均以自身SHA重新通过。最终metadata把生成时的pending说明更新为指向外部权威报告的说明后，三份以最终metadata运行locked-v2，已有v1保留历史；模型/配置未改变。三个正式GLB均与对应已审候选逐字节相同；配置、包围盒和尺寸也逐项一致。

首版rev0、初次refined、soft、Latitude、Ascend和low/high两组边界，共7份有限候选网格也分别在当前规则下通过native、GLB和导出比较。首版与refined采用 `gate-first-version-v2-*` / `gate-refined-v2-*`；其余为 `gate-soft-v1-*`、`gate-latitude-v2-*`、`gate-ascend-v2-*`、`gate-boundary-low-v1-*`、`gate-boundary-high-v1-*`。**7个候选加3个正式重保存文件不是连续参数域证明。** 造型迭代和冠部ROI的视觉判断另由摄影/评审记录，不因本门禁PASS自动消除视觉疑点。只读摄影场景重开、相机和图片身份审查由建模作者独立完成，见 `photo-orison-final.json` / `photo-latitude-final.json` / `photo-ascend-final.json`；本报告仅负责几何层，不能用几何PASS冒充摄影审核。

## 真实 GLB 字节与 native 对应

[check_glb.py](../source/check_glb.py) 解码实际GLB：POSITION/NORMAL/索引有限性、格式和数目、法线长度容差、索引范围、stride、offset/对齐、bufferView与buffer边界、声明min/max和实际值、三角面积、单mesh/材质、无外部图像/纹理资源。失败也写带稳定failure code及文件/checker SHA的新报告。这是目标导出格式的payload检查，不是GPU或完整通用glTF实现认证。

[compare_exports.py](../source/compare_exports.py) 额外按 `(x,y,z)→(x,z,−y)` 转轴，比较 native 与 GLB 的**有向三角坐标多重集**，本次三份均零容差完全相同。允许记录导出拆点后的不同顶点数；本次均为11,520。此项不是索引拓扑同构，也未验证逐法线对应、材质像素或运行时画面。

## 最终正式基线上的首组26个专项故障/控制

[24项 native/GLB 实测](gate-fault-tests-asset-orison-v1.json) 使用最终 `assets/orison`，18个native项（含1个移离控制）与6个GLB项全部满足指定字段；不能用其它门禁碰巧拒绝替代命中。

| 注入 | 必须命中的字段/要求 |
|---|---|
| 去掉全部接缝连接面 | `seam_topology_failures` |
| 首环沿T旋转；单点形变 | `ring_frame_fit_failures`，分别独立测试 |
| construction 首站N反向 | `frame_metadata_failures` |
| 单面反向 | `inconsistent_winding_edges` |
| 同object内部0.4mm小岛 | `invalid_connected_components`；同时BVH交叉必须为0 |
| 同object穿出截面的棱柱 | `nonadjacent_self_intersection_candidates` |
| 真实斜三角内缩55%叠片 | `coplanar_positive_area_overlaps` |
| 同叠片沿法线移离1µm | 共面与BVH字段必须均为0；虽因新增岛整体仍拒绝，不计作共面命中 |
| 缺面/零面积/重复三角 | 分别 `nonmanifold_edges` / `degenerate_triangles` / `duplicate_triangles` |
| 两片不共享顶点的交叉三角 | `nonadjacent_self_intersection_candidates` |
| 局部X镜像+负X对象缩放+全反面，世界位置不变 | `non_positive_world_volume`；不是只借transform异常拒绝 |
| Solidify / Shape Key / parent / animation | `model_state_contract_failures` 对应专用reason；四者raw顶点/面SHA在注入前后均不变 |
| GLB NaN位置/越界索引/零法线/过小stride/超出view/负offset | 分别稳定failure code，实际二进制与新报告SHA核对 |

[另外2项有效payload但几何错误的导出反例](gate-export-comparison-tests-asset-orison-v1.json)：整体移动POSITION并修正bounds，以及仅反转一个三角。**两份payload本身均通过**，有向三角对应项必须拒绝。反转三角的顶点坐标多重集仍完全相同，证明对应门禁不是仅检查点集距离。

26项专项完成后，最终metadata仅修改了指向外部门禁的说明与引用，未改native/GLB/config/construction。专项未重复注入；最终汇总再次核对专项native/GLB SHA及旧/新metadata的config、construction、bounds、dimensions、units、recipe版本和材质完全相同，正式文件则以最终info SHA重新跑locked-v2。

此前 refined/soft 基线的实际反例报告分别保留 `gate-fault-tests-refined-v1.json` / `gate-fault-tests-soft-v1.json`；不覆盖旧结果或把旧样本SHA当正式SHA。所有坏二进制与原始Blender日志只在work，不作正式模型发布。

## 封包前补充：2个真实native数值限制专项

原24项故障/控制里，`curvature_radius_failures`、`frame_reference_failures`、`nonlocal_centerline_clearance_failures` **都没有实际触发**。输入validator拒绝不能代替native字段覆盖。因此另以 [test_numeric_geometry_faults.py](../source/test_numeric_geometry_faults.py) 直接调用 `recipe.geometry`，只在work隔离目录构造两个参数仍在数值盒内、但不满足几何规则的真实`.blend`。正常生成器会在生成前调用完整validator并拒绝；这里绕过它仅为测试，不开放生产生成入口，也不修改正式资产或checker。

[补充专项最终报告](gate-numeric-geometry-faults-final-v3.json) 两项都被native门禁拒绝，且指定字段确实非空：

- **曲率反例**：960点最大 κr = **2.3199633216**，超过0.72，真实触发 `curvature_radius_failures`。同样出现BVH交叉候选，但专项通过以曲率字段本身命中为条件，不借其它缺陷算命中。
- **frame参考反例**：960点最小参考正弦 = **0.6215063210**，低于0.65，真实触发 `frame_reference_failures`。它另有曲率不合格，但专项必须单独确认reference字段。

两份坏网格的输入层、全顶点与面拓扑身份约束均通过；实际文件、info、checker、recipe SHA和新run_id均核对。正式Orison四个冻结文件在测试前后SHA完全不变。对应正常生成路径的拒绝也实际执行并记入报告，不是只从源码推断。

**`nonlocal_centerline_clearance_failures` 尚未有独立坏样本触发覆盖。** 本次没有进行参数搜索；两个新增反例的有限非局部间隙仍分别约9.689mm与20.410mm，均高于6mm。已有有效样本只覆盖其通过路径，不能把这项写成专项故障已覆盖，也不能声称全部checker字段均有专用故障测试。至此是原26项加2项补充，不改写原报告为28项。

首轮补充测试曾因Blender入口未插入源码目录而遇到 `ModuleNotFoundError: recipe`；尚未创建坏网格或执行native checker，属于测试脚本导入路径故障，不是检查器错误PASS。[首次失败记录](gate-numeric-geometry-faults-initial-harness.json) 保留，原日志与脚本快照在work；修复入口后以新标签重跑。v2成功记录也保留，v3对应最终测试源码与标签路径校验。

## 输入接受不等于网格接受

[当前soft正式配置对应的输入报告v3](gate-input-tests-v3.json)：196项显式测试通过，覆盖10参数上下/中值、越界、NaN/±Inf、bool/string/null/list/dict、每个missing key、extra、名称、seed、版本与revision，及真实曲率/reference拒绝例。单参数端点使用独立宽松截面fixture，避免把随最终配置变化的交叉约束混为单参数上下界。

1024个二进制盒角点仅调用 `check_geometry=False`：704个输入层接受、320个被圆角/直段交叉约束拒绝。**该1024项没有生成任何网格，也没有对其跑640/960点几何规则**。另有三正式配置与两边界配置调用完整640点validator；实际网格通过与图像人工接受必须继续分别报告。旧v1/v2输入报告保留，其配置SHA不冒充最终soft配置。

## 复跑与身份核对

在study-007目录运行；label和报告名须用未使用的新值，避免覆盖历史证据：

```sh
python source/run_gates.py --asset assets/orison --label fresh-audit-orison
python source/test_faults.py --baseline assets/orison --report review/fresh-fault-tests.json
python source/test_export_comparison.py --baseline assets/orison --label fresh-export-audit
python source/test_contract.py --report review/fresh-input-tests.json
python source/test_numeric_geometry_faults.py --label fresh-numeric-audit
```

所有Blender调用都带 `--python-exit-code 1`。包装器同时验证退出码、新报告、显式PASS、run_id、模型/info/checker/recipe SHA，以及检查期间输入未改变；这些条件互不替代。

## 明确未验/不适用

GPU/WebGL真实渲染、动态闪烁和实体iPhone未验；没有修改GL安全限制。制造、公差、承载、稳定性与人体工学未验。开放面/装配接触白名单不适用于本家族。本门禁工作未发布GitHub或Site，也未启动HTTP服务；发布仍需另行批准与整包隐私审查。
