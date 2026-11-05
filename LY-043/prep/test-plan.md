# LY-043 测试计划（按「本项验收」）

所有命令都在 `D:/GitHub/creation-notebook-workpacks/LY-043/prep/` 下运行，用 `python -I`，只读 lab 仓库。
`DOCS=D:/GitHub/creation-notebook-lab/docs`

## 0. 先绑定输入，SHA 不对就停

每次运行先核对下表的 SHA。任何一项不一致，判「输入漂移」并阻断，必须重测后才能继续。

| 输入 | SHA256 |
|---|---|
| c02v/A2-LOD0-prototype.glb | 19b052022b2f6955e4a72f1a48280f7f8c229e11f001aa02ac95e357b890d9c7 |
| c02v/A2-LOD1-prototype.glb | 277e9e73e8f2d8b8e07ec828671d37cc7c9e3f1653dcebfe4290c51de412d85d |
| city-data.mjs | e4115705aeab28f2f6cc2635fbedfabf4158a08af9c626f6dd493ee27d430a1a |
| wall-house-LOD0/1/2.glb | 5c20fa8b… / 86f66c69… / 5f95176f…（全文见 inputs.json） |

其他 5 个变体的 SHA 见 inputs.json。改选别的院时，就绑定那个院的变体。

## T1 逐区域接面分类（验收第 1 条）

```
python -I measure_box_junctions.py $DOCS junctions-all.json
python -I summarize_junctions.py junctions-all.json junctions-summary.json
```

**正例**（选院的变体两档都要满足；以 A2 为例）：

- 每个 earth、plinth、timber 节点的 `boxTriangles == triangles`。A2 的数字是 624、72、360。
- `unmatchedRectangles == 0`，`nonAxisTriangles == 0`。
- 院墙环 5 个盒体。
- `ring-ring` 4 处都是面接触，每处 `contactArea_m2 == 0.77`，误差 ±1e-4。
- 门墩接墙 2 处都是面接触，各 0.33 m²。
- 每个墙端满足 `faceArea - contactArea == exposedClosedArea`。A2 是 0.44 m² 两处，0.77 m² 四处全覆盖。
- 住屋离墙间隙不小于 0.95 m（西屋台基）。
- 对每一个 ring-* 接面都要写出四项：区域、分类、面积、伙伴构件。没有逐区域清单就不算通过。

**换成 TC03 或 TC03-2 院时另加一条**：隔墙两端的端面覆盖都要等于 0.504 m²。顶住院墙一端是 0.504，顶住住屋后墙一端是台基 0.0616 加墙 0.4424。2 处只在竖直棱线上接触的地方，要用盒体占用探针证明角块被后墙盒体占满。

**新件**（只有 LY-010 确认有缺口时才会有）：对新件加原院跑同一套检查。新件和原院之间只允许面接触，或者在 `assembly.json` 里登记过的有限局部接面。

**容差**：

- 坐标焊接 1e-4 m，面接触 1e-4 m。
- 近邻报告阈值 0.60 m。
- 院墙内部内缩 1 mm。

## T2 实体包含和侵入（验收第 1 条）

- **正例**：全院 `intrusionOrContainment == 0`。A2 共 417 对近邻盒体，0 侵入。
- 正例：`roofVsRing.trianglesIntersectingRingInterior == 0`。A2 屋面 5,476 个三角。
- 正例：`residual.trianglesIntersectingRingInterior == 0`。墙房样例有 64 个山尖三角和全部木柱三角属于残余。
- 新件和原件之间如果有正体积重叠，overlap 大于 1.25e-7 m³（相当于 0.5 × 0.05³）就判阻断。只在 `assembly.json` 明确列出、并经 LY-006 认可的局部嵌入才允许，要写明体积和原因。

## T3 不靠删闭合面（验收第 2 条）

- **正例**：每个节点 `openEdges == 0`，`sameFacingDuplicateRects == 0`，`storedNormalOpposesWinding == 0`。
- 正例：盒体数不能少于原件。A2 是 52、6、30。
- 新件安装以后，原节点的三角数、盒体集合（逐个 min 和 max）、材质、矩阵都必须和原件**逐项相同**。可以用 `summarize_junctions.py` 的 lodIdentity 比较方法，把它扩展到原件和安装后对比。
- **负例**：`python -I selftest_junctions.py $DOCS selftest-junctions.json`，要求 `allPass == true`。
  - N1：删除墙端闭合面（2 个三角）。必须得到 `openEdges > 0`，盒体从 52 降到 51。
  - N2：门墩推进墙内 0.05 m。必须得到 ring-earth 侵入 0.0165 m³，误差 ±1e-4。
  - N3：门墩拉开 0.02 m。必须得到间隙 0.02 m，面接触消失。
  - N4：复制一个面。必须得到同向重复至少 1 个。
  - N5：翻转绕序、保留法线。必须得到法线与绕序相反至少 1 个，盒体减少。

## T4 原构件范围和适用变体（验收第 3 条）

- 交付清单必须写明适用的城景院 ID。A2 原型被 9 院共用：C02-021、024、001、028、031、010、013、015、035。修订只能做成针对单院的 overlay。
- 负例：把 overlay 用到同变体的另一院，比如 C02-013，检查器必须报「非目标院」。用节点 ID 加矩阵核对。
- C2 修订（e9981a07 / f3f31774）和城景 A2 的盒体集合相同，不能当成另一个原件重复计件。

## T5 安装和撤回

- 在严格输入上安装一次、撤回一次。撤回以后，原 GLB 的 SHA 和节点盒体集合要和第 0 步完全相同，新旧不能叠载。

## 不在本测内

GPU 或浏览器渲染、人体连续通行、结构强度、历史复原。报告里不能写成「已通过」。
