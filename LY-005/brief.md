# LY-005｜统一全城坐标与高程契约

席位类型：考据/契约。前置：LY-001（交付完成）。唯一写入区：`workpacks/LY-005/`。lab 仓库全程只读：没有改、建、删文件，没有 git 写操作，没有运行 `build_assets.py`。开工前后的 `git status` 一致，见检查 C9。

## 1 输入版本

| 项 | 值 |
|---|---|
| 基线 | `bce3211f818ee5a8bef1773539da70695ba37b17`，即工作树 HEAD，也是任务指定的 main |
| city-data.mjs | 提交 blob `c849706b…`，CRLF 检出 `e4115705…`。导出的 dump `28ce130c…` 与 LY-001 的 dump 逐字节相同（C1） |
| city-renderer.mjs | 提交 blob `04c6c643…`，CRLF 检出 `fa0a8dcb…` |
| 注意 | 开工时 `origin/main` 已经前进到 `f28d650`（「Fix C15: connect Yong gate road…」）。本契约以 bce3211 为准；f28d650 只用 `git show` 读到本目录，拿来检查旧节点有没有漂移、冻结端口能不能被后续件接上，不当作基线 |

## 2 交付了什么

- `coordinate-contract.json`：契约正文。内容包括单位、轴向、原点、二维 (east, north) 记号、Blender 换轴、世界矩阵组成规则、R1–R7 落位规则、两类原点（city-absolute / local-origin）、高程零点和 E1–E4、端口种类、float32 精度、证据分类，以及本契约不声称的事项。
- `port-schema.json`：端口格式。每个端口同时带 `local`（资产帧）和 `world`（= N·local），并带所用的 N 矩阵和测量文件的 SHA256。
- `qa/ports-bce3211.json`：在现有几何上实测的 55 个端口实例。雍门 10 个：三门道内外门槛 6、地坪内外边 2、两端接墙 2；44 院各有一个 ground-base；广阳门体有一个 floor-base。
- `qa/frames-bce3211.json`：42 个资产（48 个 GLB 文件，含 6 个近景 LOD0）和 80 个节点的实测帧，包括 SHA、节点种类、包围盒、矩阵分解、原点类别和 float32 ULP。
- `qa/elevation-survey.json`：用竖直射线在 4 块已交付地面上做的高程采样。
- `qa/roundtrip-results.json` 和 `qa/roundtrip/`：Blender GLB 往返的用例、导出的 GLB 和报告。
- `qa/negatives-and-drift.json`：负例和新旧快照漂移检查。
- `qa/f28d650-port-consumption.json`：新提交的接路件是否接在冻结端口上。
- `qa/checks.json`：C1–C9 九项检查，每项都绑定所读文件的 SHA256。
- `preview/ports-and-elevations.png`：PIL 按实测数值画的示意图，不是渲染图。

## 3 实测结论（全部可用 `source/` 重算）

**世界变换**：城市里实际用的是 world = N · S · v。S 是 GLB 场景层级，在 `loadAsset()` 里 `applyMatrix4(matrixWorld)` 烘一次；N 是节点矩阵，`node.matrix` 按列主序读取，没有就用 `compose(position, rotationY, scale)`，由 `setMatrixAt` 施加一次。80 个节点全部满足以下几条：
- 缩放偏差最大 2.6e-9，只出现在雍门两节点，来自 cos/sin 的 float32 舍入；
- 只绕 +Y 旋转（倾斜分量 0），det 都是 1，轴点积 0；
- city-absolute 资产全部是单位节点，双重施加 0 例；
- 节点 bounds 与按顶点实算的差最大 1.37e-6 m。

偏航值只有 0°、±90°、180° 和雍门的 90.6662°。

**两类原点**：19 个城市资产是 city-absolute，包括城垣、广阳门 direct、三块大地面、市肆、仓储。坐标最远约 3954 m，float32 ULP 为 0.24 mm。44 院、D08 地面、雍门两件和 14 个研究模型是 local-origin。新资产一律按 local-origin 制作。

**Blender 往返**（5.2.1 headless，factory 场景 METRIC、scale_length 1.0）：做了雍门门体、雍门接口地坪、C02-018（180°）、C02-021（-90°）和城垣 wall-A-wall-10（city-absolute）五个节点，每个都走了一遍：导入 → 只导出本地 → 再导入，再把城市 N 作为唯一父空物体导出 → 再导入。结果：
- 导入与原始 GLB 顶点一致（按 5 位小数取整比较）；
- 换轴 Blender(X,Y,Z) = glTF(x,−z,y) 精确成立；
- 本地往返无漂移；
- 落位往返与城市世界坐标差 ≤ 6.94e-5 m，这是 float32 的量级；
- 导出的城市节点矩阵与 city-data 的差 ≤ 1.4e-5，缩放为 1，落位后包围盒与 city-data 节点 bounds 差 ≤ 5.6e-5 m；
- 雍门来源合同里声明的 Blender 原生矩阵与 C·M·C⁻¹ 差 0.0。

负例：给 C02-018 故意套错原型（A 代替 B），包围盒差 1.03 m，检查判为不通过。

**负例与漂移**：矩阵施加两次、静默缩放 1.001、x 向拉伸 1.0005、city-absolute 再平移、Z-up 未换轴、镜像，这六种错误全部被拦下。其中镜像只靠 det 才查得出，包围盒差仅 2e-6 m，所以 R3 不能省。从 bce3211 到 f28d650，66 个旧节点的 N、资产 SHA 和 bounds 全部不变，55 个端口用新矩阵重算差 0.0。只有雍门两节点改成按需近景（initial true→false，加了 replaces），ground-network 新增 replaces 接路片。这些是可见性变化，不是坐标漂移。

**高程**（全部是 C 工程零点）：
- 道路和缝合地面顶面 0.21，地块地面 0.20；
- 44 院基底 0.20，220 个采样点全部落在地面上（−0.25 mm 到 0）；
- 城垣底 0.17、顶 6.2；广阳门体从墙顶 6.2 起，顶 10.3；
- 雍门门体底和门道行走面 0.17，门体在门道内没有地面几何，行走面来自接口地坪；地坪底 −0.03；
- 广阳门侧 direct 墙脚比地面低 1.33 cm；
- 多数城垣墙脚下没有已交付地面网格。

城垣/城门一族（0.17）和地面一族（0.20/0.21）之间有 3–4 cm 的系统差。本契约不抹平它，只要求在端口里写清。f28d650 的雍门接路片从内侧地坪边端口起坡，起点高差 8.1e-7 m，坡末 0.21 接上缝合路，说明冻结端口能被后续件按本地和世界两套坐标接上。

## 4 没做到 / 不声称

- 只证明数值一致：坐标、单位、轴向、矩阵施加次数和高程读数。不等于局部通行通过、已入城、结构安全或历史复原成立。
- 没有浏览器/GPU 实测；渲染器行为按源码复现。高程采样只是竖直射线，不是实体碰撞。
- Blender 往返只核几何和矩阵。导出时出现「More than one shader node tex image」警告，材质与采样器没有核，往返导出的 GLB 只作 QA，不是替换件。
- 城垣端口只给了雍门这一侧的接墙中心线点。各墙段的端口和墙段间接缝的 portId 归属，留给 LY-006。
- 地理原点、真北偏角、约 180 年洛阳的绝对高程都未知。没有考古控制点，所以本契约里没有一条数据属于「原始考古/原文」或「异地异期类比」。

## 5 证据

- glTF 2.0 规范 3.4 节：https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html ，原文「glTF uses a right-handed coordinate system.」；同页另有「The units for all linear distances are meters.」，以及 TRS 按 T * R * S 顺序后乘的规定。
- Blender 4.2 手册 glTF 页：https://docs.blender.org/manual/en/4.2/addons/import_export/scene_gltf2.html ，+Y Up 选项说明为「Export using glTF convention, +Y up.」。手册的 latest 链接返回 404，未能访问。
- 其余结论都来自本机实测，对应文件和 SHA256 见 `qa/checks.json`。

## 6 如何重算

```
python -I source/measure.py qa/city-data.dump.json D:/GitHub/creation-notebook-lab/docs/cities/luoyang qa/frames-bce3211.json bce3211
python -I source/elevation_ports.py qa/city-data.dump.json qa/frames-bce3211.json qa/elevation-survey.json qa/ports-bce3211.json
D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P source/bl_roundtrip.py -- qa/roundtrip/cases/<node>.json qa/roundtrip/out
python -I source/compare_roundtrip.py qa/roundtrip/cases qa/roundtrip/out qa/roundtrip-results.json
python -I source/negatives_drift.py qa/frames-bce3211.json qa/ports-bce3211.json qa/f28d650/dump-bce3211-blob.json qa/f28d650/dump-f28d650.json qa/negatives-and-drift.json
python -I source/checks.py <LY-005 目录>
```
