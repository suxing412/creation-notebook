# LY-064 test plan（制作时直接跑）

坐标是 glTF 约定，单位米。Blender 调用方式：`D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P <脚本> -- <参数>`。
每份结果都要写入输入的 SHA。开工时先按 LY-001 的新快照，重新核对下面要绑定的 SHA。

## 0. 要绑定的输入 SHA（不能变）

| 文件 | SHA256 |
|---|---|
| palaceque-Q-LOD0.glb | a022d9870594f986658be288528048ca3ea6ca69c576b46a5b1aef700e0ca23d |
| palaceque-Q-LOD1.glb | 09839d70748ea5c5ac6c3281c4c10655859e179b9c40046f1428478d8f27a68c |
| palaceque-Q-LOD2.glb | 9b75671b3d12f393c5b9649611f96cb84eec161042a4fae2bc35cd0fbdd01a8b |
| palace-admission-court-open-LOD0.glb（如果对接） | 59c8b758a5a2523105eac0e516e9961bf769bd5e422ba2913d292492ed45c4b0 |
| city-data.mjs | e4115705aeab28f2f6cc2635fbedfabf4158a08af9c626f6dd493ee27d430a1a |
| p-luoyang.asset.json | 9b5e311f077aa6c2fb433ba36cca6dc291542848769134335418a558b92b089d |

## T1 原件保持（正例）
- 三档对阙 GLB 的 sha256 与第 0 节一致。如果新交付把对阙并进合成 GLB，三个原节点的顶点、索引、UV、材质和贴图字节都要逐项比对，差异为 0。原节点的世界矩阵只允许多出 `assembly.json` 里声明的那一个平移或旋转。
- 负例：把任一原节点的顶点改动 1 mm 再跑一遍，检查必须报错。

## T2 足迹支持（本项验收第一条）
- 运行 `scripts/probe_support.py out.json <对阙GLB> <前庭GLB> tx tz 0.25`，三档都跑，三档前庭各配对应档的对阙。
- 通过条件：每座阙 1,296 个探针中，`supported` 等于 1,296，`no_ground_hit`、`ground_below_base`、`ground_above_base` 都为 0，容差 ±5 mm。
- 基脚如果埋入地坪（阙底低于地坪顶），把判据改成：探针打到的是基脚或地坪的顶面，而且阙底与基脚之间的竖向缝不大于 5 mm。脚本参数要按这种情况改。
- 负例 A（已实测）：只用候入院、不加新前庭，对阙放在 tz=72，必须得到 0/1296。
- 负例 B（已实测）：tz=66 时必须得到 792/1296，不能报成 100%。
- 负例 C：把前庭整体下移 0.05 m，必须出现 `ground_below_base`>0，并报出 worst_hanging_gap 约等于 0.05。

## T3 中央与侧边通道（本项验收第二条）
- 中央通道：在 x∈[−9.5+ε, 9.5−ε] 内，高 0–2.2 m（人体包络；货物或车辆包络由 010 指定后再加一档），沿前庭全长 z 做盒体重叠检查。新基脚、包边、端口件与这个盒体的正体积重叠必须为 0。已测原值：地面净距 19.0 m，y=2.2 m 时 19.73 m。基脚每侧外扩不超过 e，就要求 19.0−2e 不小于 010 规定的最小净宽（待定）。
- 侧边通道：在 |x|∈[18.5+e, 前庭半宽] 内做同样的盒体检查。瓦檐最远 |x|=18.4，这一点保持不变即可。
- 判据必须用体积重叠或扫掠盒，不能只用中心射线。可执行入口：`D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P scripts/volume_overlap.py -- specs/<spec>.json out/<out>.json`。在 spec 里加上新前庭、基脚和包边作为 solid，沿用 `specs/que-lanes-and-court.json` 的盒体，结果的 `allPass` 必须为 true。
- 基线（已实测，`out/volume-overlap.json` sha 628d98a2）：三档原阙的中央盒（2.2 m、4.0 m、13 m 三种高度）和两侧侧边盒，体积、盒内顶点、面相交都为 0。负例 ±9.8 必须报 4.701 m³，负例 18.2 必须报 2.3505 m³，容差 ±0.01 m³。新件加入后，这些数字不能变差。
- 新件必须闭合：`nonManifoldEdges`=0。相关盒体的 `odd_parity_columns` 也必须为 0，否则体积结论不算数。
- z=40 的教训：bbox 推出「0.4 m 侵入」，实测只有 0.0503 m³，落在东廊入口踏步一角。射线探针只报了 3 个异常。所以 bbox 和射线都不能替代体积判定。
- 负例：故意把基脚沿 x 外扩 0.3 m，检查必须报中央通道侵入。

## T3b 前庭与邻件（如果 LY-010 选择接候入院）
- 用 `volume_overlap.py` 的 pair 模式，对新前庭、基脚与候入院的每个 earth 和 timber 节点（廊庑、门卫、殿）逐对算交体积，结果必须为 0；共面接触另记到 T4。
- 负例：把对阙放回 tz=40，与 `east_gallery__sidehall-A-static_earth` 必须报 0.0503±0.005 m³。

## T4 接触分类
- 阙底（每座 81 m²，y=0）与基脚或地坪顶面之间：要么共面，归为「合法局部接面」，并写明面积 162 m²；要么基脚包住阙底，归为「完全包含」，写明体积。不能整对豁免。
- 基脚与 LOD0 木构（y 从 1.15 起）之间：正体积重叠必须为 0。
- 如果接到候入院：新前庭与 `new_court_support_C` 前缘（z=+67）之间，顶面高差不大于 1 mm，平面缝不大于 0.2 mm，不能有叠铺的重合顶面（参照候入院 qa 里 `outer_ground_join` 的判法）。

## T5 端口
- 每个端口都有 LY-006 模板里的 ID 和版本、位置、法向、宽度和高程。至少要有：前庭前缘的接街口、后缘的接院口（或独立收口），中央和两侧通道各一个端口。
- 端口高程与地坪顶面差不大于 1 mm。端口宽度在 T3 的净宽之内。
- 负例：两个端口共用同一个 ID，或同一个地坪片有两个所有者，检查必须报错（交给 LY-006 的唯一性检查）。

## T6 三档与预算
- 每个 GLB 不超过 15,000,000 B。LOD1、LOD2 不能是 LOD0 复制改名：三档三角数要不同，用 sha 判。
- UV、法线、退化三角、有限值检查沿用 audit 字段，`issues` 要为空。
- 足迹支持（T2）三档都要通过，不能拿远档的结果冒充近档。

## T7 安装与撤回
- 在严格输入上按 `assembly.json` 安装一次、撤回一次。撤回后所有原件的 sha 回到第 0 节，前庭的新节点全部移除。
- 不能同时载入旧方案和新方案。

## T8 史证与命名（本项验收第三条）
- 用 grep 检查交付物（卡片草案、assembly、manifest）：不出现宫门名、宫名、绝对坐标，不出现「阊阖」，不出现「两座宫门」「宫门×2」这类计数。`building_family_increment` 等于 0，阙只计为一对。
- 负例：在草案里写进「朱雀门」，检查必须报错。

## T9 共享文件
- 交付前对 city-data.mjs 和 p-luoyang.asset.json 做 sha 比对，与第 0 节一致，证明本席位没有改动它们。
