# LY-051 测试计划（制作时直接跑）

**对象**：`models/LY-051-kit-A*.glb` 和 `models/LY-051-kit-B*.glb`，各三档。最终文件名以 LY-007 slug 规则为准。宿主 A/B 原 GLB 只读。

**帧**：LY-006 的 `local:stable-A|B` 使用 GLB 原生坐标：x 是开间，y 向上，+z 是敞口正面。Blender 导入后对应 (x, −z, y)。`check_kit.py` 在 Blender 坐标下计算，读入写入区时只换算一次。

**工具**：
- `prep/check_kit.py`，SHA256 `d79a4f9938f896c48e642f94e0c87b9cc3c4eccc3e05ac96946d9d0e84b423b8`。
- `prep/measure_stable.py`，SHA256 `af2d79dc…5486`。

**运行命令**：
```
D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P prep/check_kit.py -- \
  --host <lab>/docs/library/models/m-luoyang-stable/files/A.glb --variant A \
  --zones ../LY-006/registry/zones.json --out qa/check-A-LOD0.json --kit models/<kit-A-LOD0>.glb [--selftest]
```
B 套同样运行，每档 LOD 各跑一次。

## 0. 必须绑定的 SHA（任一不符：停下，不出结论）

| 文件 | SHA256 |
|---|---|
| 宿主 A.glb | `672beeb46faaee0a15f7de649099c486c639b40a39b045b89525fbe7f15b2563` |
| 宿主 B.glb | `bd82280a76f0677821788c62c39b42e8fb2314d297bbad704a92aa7d452c2cb4` |
| LY-006 zones.json / ports.json / seats.json / ownership.json | `6b3595ac735d180866e823ddeb4e3676ffc0e816d083f6be2d57d6e4df0821c0` / `28bcfb68cd7d7fe0026f62de23ae3e45ba8f714a139e38c0b0957039f12fc633` / `a1426412c84cab875713a63846fc9c487c6d01a9f8c445d5268c02187d959069` / `ecbbbcf5614d41bf7c7bf3b04416504ae70891e212c7551456de4ff1a417b4ca` |
| LY-002 evidence-ledger.json | `237a4811acad3d7f6733d4c5c95a64df0b2c67adf48b2682264eb0f0c8512b77` |
| LY-007 LY-style-bible.frozen.md | `50e51a9358b1ba50fe5fbfcf1afad93dbb1c8a616d4a50d3faae17a9641f276d` |
| 基线 measure-A.json / measure-B.json | `5dba80fec2a3d247761275450e7ed95ed4bdf234680d3189831198da8c248aee` / `bd9f05fc1cff7027abf090c840993717dfb9fd8a7e91a29f2839be27a2db82f2`。重跑必须逐字节一致（本轮已复现） |
| 自检基线 selftest-A.json / selftest-B.json | `f7fbd479…7948` / `7162197a…52aa`（13/13 符合预期） |
| LY-008/009/010 冻结包 | 冻结后补记版本与 SHA；check_kit 要改成调用 LY-008 的官方检查器，或与它的结果对照 |

**前置**：每次正式运行都要带 `--selftest`。只要 `selftestAllOk` 不是 true，这一轮的 kit 结论一律作废。

## 1. 宿主不变

- **T1.1**：宿主 A/B 的 SHA 在制作前后不变。assembly.json 里不得出现对 39 个宿主对象或两块台基地坪片的替换、隐藏、删除项；按 LY-006，这些都归 LY-052 keep。
- **T1.2**：`hostUnchangedAfterImport` 为 true。逐对象指纹（矩阵 1e-6、顶点、材质名）与 `hostFingerprint` 一致。
- **负例 N8**：宿主后墙移动 1 mm 时，指纹必须变化。已实测：A/B 都能检出。

## 2. 写入区与端口（LY-006）

- **T2.1**：配件的所有顶点都在 `LY-051:write:001` 或 `LY-051:write:002` 内，容差 0.002 m。A 的范围是 x ±4.5、y 0.05–2.70、z ±2.4；B 是 x ±6.3、y 0.05–2.70、z ±2.7（均为 GLB 帧）。
  - **负例 N4**：分栏落到台基顶 y=0 时必须报「outside zone」。已实测拦下（A：顶点 (1.35, −1.85, 0.0)）。
- **T2.2**：端口 `stable:partition-footprint:mount` v1 的值写进 assembly.json，按分栏列出 x、z 和底高 y。实测值与声明值之差：位置 ≤0.005 m，高程 ≤0.002 m。
  - 如果采用零落地方案，就声明 `footprints: []`，并写明分栏底离地 0.05 m。
  - **负例 N7**：声明 y=0、实测 y=0.05 时必须报错。已实测拦下。
- **T2.3**：组件只有 `W051-tethers` 和 `W051-partitions` 两类，都可拆卸，挂在同一个根节点下。根节点带 `requires: m-luoyang-stable/A|B`，避免被计成新建筑。

## 3. 系留件

- **T3.1（正例）**：每个系点都与宿主有面接触，可接的面只有三类：柱侧面、后墙前面（Blender y=1.94 / 2.24）、槽沿。接触间隙 ≤0.002 m，正体积侵入为 0。若用榫或钉表示嵌入，要在 qa 里单列，侵入体积由检查器给出，不能豁免整对物件。
  - 已实测：P2 后墙钉、P3「钉+环」链式支持都通过。
- **T3.2**：系点高度在 0.68–1.30（槽沿到后墙顶）之间；超出这个范围要写明是 C 选择。系点不得高于 2.70（写入区上沿）。
- **负例 N1**：系点进入槽内腔必须报错。A 的 trough_1 内腔为 x −1.025…1.025、y 1.175…1.625、z 0.18…0.68，槽壁厚 0.10。已实测拦下。
- **负例 N2**：配件与宿主断开（悬空）必须报「floating」。已实测拦下。

## 4. 分栏件

- **T4.1**：分栏中心 x 落在宿主内柱轴上，容差 0.005：A 为 ±1.4，B 为 −3 / 0 / 3。
  - **负例 N6**：kit-A 的轴线装到 B 上（或反过来）必须报端口不匹配。已实测拦下，同时还报了侵入和悬空。
- **T4.2**：板厚 t ≤0.12 m，离相邻槽端 ≥0.21 m。
  - **负例 N3**：t=0.30 时必须报正体积侵入。实测每根柱侵入 0.01035 m³，与解析值 0.18×0.05×1.15 一致，同时报挡入口。
- **T4.3**：入口净空。每个开间前柱内面之间、柱深范围内、z 0.05–2.70 的板带不得有任何配件。也就是说，入口净宽 2.62 / 2.82 m 在加载前后不变。
  - **负例 N5**：在入口处横放一根杆，必须报「blocks entrance」。已实测拦下。
- **T4.4**：分栏的支持要看得见，二选一：
  - (a) 两端挂在前、后柱内面，长 3.70 / 4.30 m；
  - (b) 由 LY-052 在地坪层承托，需要 LY-052 的承托件 SHA，联合加载复核。
  
  不允许整块板悬空。

## 5. 互斥、安装与撤回

- **T5.1**：A 和 B 不能同时加载；kit-A 和 kit-B 也不能同时加载。
- **T5.2**：删掉配件根节点后，宿主指纹与安装前一致（T4.3_host_restored 已在自检中通过）。没有宿主时，配件必须能单独读取，并且根节点带 requires。

## 6. 通用质量（LY-007 / LY-008）

- **T6.1**：每个 GLB ≤15,000,000 B，按真实导出回读，几何必须是有限值，不能有退化三角面，UV 和法线齐全。待 LY-008 冻结后，用它的检查器跑一遍，并用它的负例做对照。
- **T6.2**：做三档 LOD0/1/2，三档共用 slug，包围盒、原点、朝向一致。圆木按 16→8→方盒降档。**不许把 LOD0 复制改名充当其他档**：三档三角面数必须严格递减，LOD1 约为 LOD0 的 0.2–0.6，LOD2 约为 0.05–0.16。每档都要跑一遍 check_kit，LOD2 也不能出现悬空。
- **T6.3**：材质只用 `LY_P01_*__PBR`（LOD0/1）和 `__FLAT`（LOD2），禁用 `REUSED_C_*`。与宿主 `REUSED_C_wood` 的色差要附同机位对比图，写入 qa。
- **T6.4**：`lab/tools/build_assets.py --check` 只由 LY-100 在合并队列里跑，本席位不运行。

## 7. 证据与声明

- **T7.1**：assembly.json 里每个配件形制都标 `evidence: C`，引用 LY-002 的 E-H01 / E-H02，禁用项写 X07 / X12 / X24。不得出现「汉制」「复原」字样，用 grep 检查。
- **T7.2**：qa 报告必须写明以下几点：动物尺寸、系留强度、分栏承载、动物适宜性都没有验证；表面 BVH 加 5 mm 网格采样不是穷尽的实体碰撞；CPU 渲染图标明 CPU；没有做浏览器或 GPU 测试；本配件没有入城。
