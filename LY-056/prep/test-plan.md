# LY-056 测试计划（准备版，制作时直接跑）

工具：`D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P scripts/measure_pestle.py -- ...`，比对用 `python -I scripts/compare_runs.py`。
所有数字采用 Blender Z-up 足碓局部坐标。安装后的结果必须写明世界变换 T 和 yaw；LY-005 冻结后，再按其轴向约定给出 glTF 世界坐标。

## 0. 绑定 SHA（输入一旦变化就重跑全部测试）

- foot-pestle-LOD0 `6f0e41834121fa26cb36303606133256e8a8226e4c49464f68dc93646d181068`
- foot-pestle-LOD1 `d8759dd6e0b0880325bb033e5031723e327f132c66a3cafd1aa97fed985cdd7c`
- foot-pestle-LOD2 `e94416ef307479eb4a3bf01652153d9c2ff0ba26300b4240920d580a5ae83453`
- workyard-LOD0 `7eb9739ec09a1ebbbcf16891d14be1488fc484be72c4bae273ec1a993139d17e`（只作互斥参照）
- 选定地坪 GLB：待 LY-010/LY-005 给出，把它的 SHA 填到这里：`<TBD>`
- 测试脚本：measure_pestle.py `6382e6d0e650935b69584da41ad1685e06de6bcfe8c360ddbd2a8f1bc23931d5`；compare_runs.py `f3b85df5…`；probe_ground.py `315fdf5b…`

## T1 原件不变（复用前提）

- **正例**：交付包引用的三档 GLB，SHA 与 §0 一致；`compare_runs.py` 比对 LOD0 与安装包内回读结果，缺件 0、多件 0、bbox 偏差 ≤1 mm。
- **负例**：任一构件 bbox 偏差 >1 mm，或节点名、材质名有变 → FAIL。
- 基准值：21 个构件；LOD1/LOD2 只有扶栏偏差，分别 ≤1.2 mm 和 ≤7.4 mm，属于已知差异。

## T2 枢轴孔保留

- **正例**：安装后（含地坪、垫片和附件）满足：
  - `pivot.leverHoleRadialFromAxis_m_x0` 16 个方向都是 0.079±0.001；
  - `axle_vs_lever.vol_m3 == 0`；
  - 轴线上 X 向射线 `dz+0.000 == []`。
  - 另外，地坪和附件构件与「轴 + 鞍口」包络 x∈[−0.56,0.56]、y∈[−0.2,0.2]、z∈[0.90,1.10] 的体积交叠为 0。
- **负例**：在该包络里放一个 0.05 m 的测试方块，必须报出交叠（制作时把它加成一项负例运行）。
- **分类**：轴与鞍口之间 4 mm、孔与轴之间 4 mm 的间隙，记为「C 轴承间隙/无接触」，不得记为接触支承。

## T3 落地支承（选定地坪）

- 命令：`measure_pestle.py LOD0.glb out.json --host-glb <ground.glb> --T x,y,z --yaw deg`
- **正例**：14 个脚印每个 9 点向下射线都命中，地面高与脚底高之差在 ±5 mm 以内，`supportVerdict == PASS`。
  - 现有正对照 `--ground-plane 0` 为 PASS（`out/install-pos-plane0.json`）。
  - 旋转 90° 后的对照见 `out/install-pos-yaw90-plane.json`。
- **负例**（已实测，必须保持 FAIL）：
  - 地面高 +3 cm → BURIED（`install-neg-plane-buried.json`）；
  - 地面高 −2 cm → FLOATING（`install-neg-floating.json`）；
  - 用 workyard 当宿主，因无地面 → NO_SUPPORT（`measure-workyard-LOD0.json`）。
- 容差：±5 mm（C；最终值以 LY-005/LY-008 为准）。地面有坡时，逐脚印报告 min/max 高差，同一构件内高差 >5 mm 判 FAIL。

- **备选宿主对照**（已实测）：
  - 命令：`--host-glb workshed-LOD0.glb --T 1.55,2.0,0 --yaw 0`，结果在 `out/install-probe-workshed-bayR.json`。
  - 必须是 supportVerdict FAIL（14/14 NO_SUPPORT，棚体没有地面）。
  - 同时应得到：doubleLoad PASS；离柱平面距离 0.745 m；台面上方净高 2.45–2.88 m。
  - 若 LY-010 选了 workshed 作为遮蔽，必须和选定地坪一起装，再跑一次 T3；但 workshed 不能单独装。
  - workshed 的 SHA：`89e0a43923fb3868452903186b07299162fdf208a667c0d82630791b554ce726`。

## T4 不叠载 / 可撤回

- **正例**：安装包启用时，宿主中没有与足碓构件 bbox 偏差 <2 mm 的重复件，`doubleLoadVerdict == PASS`。撤回（移除安装节点）后，宿主所有节点的名、矩阵、网格和材质 SHA 都不变。
- **负例**（已实测）：把独立足碓装到 workyard 的 T=5,−1.5,0.2 → doubleLoad 21，FAIL（`install-neg-workyard-doubleload.json`）。
- 规则：workyard 烘焙版和 LY-056 节点化安装互斥，不能同时启用。

## T5 有限姿态（0/4/8°）

- **正例**：在 0、4、8° 三个姿态下，活动件（杠杆、杵头）与所有静态件、地坪和附件的体积交叠为 0。8° 时杠杆最低点 ≥ 台面 +1 mm（现测 0.723 / 0.720）。
- **负例**：8.5° 必须报出 杠杆×台面 交叠 >0（现测 5.6e-5 m³）；−4° 必须报出 杵头×臼 交叠 >0（现测 9.8e-4 m³）。这说明扫掠检查确实能抓到碰撞。
- 必须写明的事实：0° 时杵头悬在臼底上方 5 cm；舂落接触角约 −2.1°，不在允许姿态内；行程 0.175 m。这些是有限姿态，不是连续动力学。

## T6 身体空间（有限包络，不是人体认证）

- C 包络：站立人体取 0.45 × 0.30 m 足底框，高 1.75 m（必要时按 LY-010 的值替换）。
- 检查项：
  - 台面上方净高 ≥ 1.75 + 0.1 m（workyard 中测得 2.92–2.98 m）；
  - 踏步前方净距 ≥ 1.0 m；
  - 杠杆端头前方无杠杆区（1.19 × 0.40 m）可以放下足底框；
  - 侧带宽 0.485 m ≥ 足底框宽 0.30 m；
  - 杵臼两侧取料净距 ≥ 0.6 m。workyard 中测得：左 7.93 m、右 3.18 m、臼后 11.38 m、支柱外侧 1.26 m。
- 转身：直径 0.6 m 的转身圆**放不进台面**，结果必须报「需跨杠杆或下台转身」，不能写「可转身」。负例：在台面中心放 0.6 m 圆柱，必须与杠杆或扶栏相交。
- 必须披露：台面后沿 y=−0.55 无栏杆，离地 0.72 m，后面有 0.35 m 空档。

## T7 扶栏与静态交体分类

- 安装后的 `restPairs` 与准备基准逐项一致：
  - 支柱×底座 0.0088 m³ ×2（完全穿入）；
  - 扶栏柱×台面 ≈3e-4 m³ ×4；
  - 扶栏柱×踏步 9e-5 m³ ×2；
  - 栏顶×立柱 2.1e-4 m³ ×4；
  - 杵头×杠杆 2.75e-3 m³（同一活动件）。
- 任何**新增**的交叠对，都要分类为合法接面、正体积侵入或完全包含；没有解释的 → 阻断。
- 栏顶比台面高 0.985 m，净宽 1.19 m：只报告数值，不做规范认证。

## T8 三档与语义

- LOD0/LOD1 的 `pestle_timber_moving` 是独立节点；LOD2 没有这个节点，只能静态显示，必须写在交付清单里。
- 枢轴端口要用世界坐标和 glTF 坐标各写一次。不得沿用 workyard 的 Blender 轴数值，却标成 glTF。
- 单个 GLB ≤ 15,000,000 B（现在最大 655,508 B）。官方 `lab/tools/build_assets.py --check` 由 LY-100 在合并队列里跑，本席位不跑。

## 产出绑定

每次运行都把 `out/*.json` 和 `SHA256SUMS.txt` 一起交付，并写明 Blender 版本、脚本 SHA 和输入 SHA。图像一律注明 CPU/Workbench，不写成 GPU 或浏览器实测。
