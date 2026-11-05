# LY-080 测试计划（制作时直接跑）

对应任务池“本项验收”的四条：
1. 四陛全部独立核支持；
2. 文件和坐标明确属北郊；
3. 不出现南郊位置、虚构的围营或祠舍；
4. 未知位置保持未知。

此外还有公共底线：安装一次、撤回一次，原件不变。

**绑定的原件 SHA256**（任何一项不符，全部检查立即失败）：
- LOD0：d62dce7d2130828c4e309edf42701fd8890454d39d51d2763f16fe351a8e6ebe
- LOD1：4842be77757597237ddcedcd1e2d2f66402db0dcde57986e9fbb926cc096d6dd
- LOD2：7c7f3a51ac7cce90137a8a0210f3031129058b5d7e21a1eb850bc222953a1287

**容差**：采用 LY-005 E3，高程 2 mm，平面位置 5 mm。几何恒等比较的阈值为 1e-6 m。

**工具**：
- `prep/measure_altar.py`：numpy 版测量。
- `prep/blender_readback.py`：Blender 交叉回读。
- 制作时另写 `qa/check_ly080.py`，读取 `assembly.json` 和端口 JSON 后执行下面各项。

## A. 原件与回读

| ID | 检查 | 通过条件 | 负例（必须失败） |
|---|---|---|---|
| A1 | 三档 GLB 字节 SHA | 等于上面的绑定值，交付包只引用不复制。复制时 SHA 也必须一致 | 把 LOD0 翻转 1 字节，应报 SHA 不符 |
| A2 | 双路回读 | numpy 与 Blender 都得到 26×1.2×26 m、268 三角形、1 个连通体、非流形边 0、体积 506.88±0.01 m³ | 删除一个三角形的副本，应报非流形边 > 0 |
| A3 | 节点名与 extras | 唯一节点 `north_altar_platform_four_stepped_approaches_C`，`accessCount==4`，`cityPlacement=="null"`，或改为与 LY-004 结论一致的明确状态 | 把 accessCount 改成 8，应失败 |
| A4 | 官方检查 | 用 LY-008 `source/ly_check.py official <导出副本>`（SHA256 39aaa491…dea83）跑。副本由 `git -C <lab> -c core.autocrlf=false archive bce3211` 导出；目录里有 `.git` 时检查器会拒绝运行。不在 main 上跑 | 在原仓库目录上调用时应被拒绝 |
| A5 | LY-008 交付检查 | 对本包运行 `ly_check.py` 的 GLB、隐私和清单子命令，全部通过；任何新地坪 GLB ≤ 15,000,000 字节 | 往清单里写一个私密绝对路径（如 `C:/Users/...`），应被判失败 |

## B. 四陛支承（逐陛独立）

对 E、W、S、N 四陛分别执行：

| ID | 检查 | 通过条件 |
|---|---|---|
| B1 | 级数与踢面 | 6 个踢面，每级 0.200±0.002 m，累计 1.200 m；最高一级与坛面高差 0±0.002 m |
| B2 | 踏面 | 5 级踏面深 0.500±0.005 m，加 1 级与坛面齐平的顶级；宽 3.200±0.005 m；切向中心 0±0.005 m |
| B3 | 足下支承 | 陛投影范围（坛心外 3.0 m × 3.2 m）与 y=0 底面重合，支承比 ≥ 0.999 |
| B4 | 无悬空 | 本件 y>0 处朝下的面积 ≤ 1e-6 m²；装配后，任何新增地坪片与坛底的竖向缝隙 ≤ 2 mm |
| B5 | 端口接地 | 4 个独立端口，portId 以 LY-006 增登为准，建议 `north-altar:stairs:ground:E/W/S/N`。如果 LY-006 仍只登记单一的 `north-altar:stairs:ground`，本项判**阻断**，不把 4 个脚下塞进 1 个 pose。本地坐标分别为 (13,0,0)、(-13,0,0)、(0,0,13)、(0,0,-13)，forward 朝外，宽 3.2 m。地面上竖直射线取最高向上面，`portMinusTerrain` 在 ±0.002 m 内 |
| B6 | 端口外延支承 | 每个端口外侧至少 1.0 m × 3.2 m 有可支承面（向上面、法线 y>0.99），采样间隔 ≤ 0.1 m，命中率 100%。地面来源必须写明：本包 C 地坪片，或 LY-081 的实际地面 |
| B7 | 陛顶端口 | 端口 `floor:E/W/S/N-top` 位于 (±10.0, 1.2, 0)、(0, 1.2, ±10.0)，与坛面高差 0±0.002 m |

B 组负例（每一项都必须被判失败）：
- 把整件的 N 的 Y 设为 +0.21 m，或把地坪放在 0.21 m，使第一级被埋：B5 报 -0.21 m 超差。实测缺口 G2 就是这个场景。
- 删除北陛对应的地坪片：B6 报北端口命中 0%，其余三陛仍然通过，以此证明四陛是独立检查的。
- 把端口平移 0.01 m：B5 报平面超差。
- 用一个只在中心线上的射线点冒充整条宽度：B6 的采样必须覆盖全宽，否则检查器自身判为失败。

## C. 北郊归属与南郊隔离

| ID | 检查 | 通过条件 |
|---|---|---|
| C1 | 包内命名 | 所有文件名、portId、nodeId 带 `north-suburb`、`northern-altar` 或 `LY-080`；端口 `frames.local` 为北郊局部框架 |
| C2 | 世界坐标 | 用 LY-006 `schemas/port.schema.json`（9fcdf932…fdc）校验每个端口 JSON。<br>• `frames.local=="local:north-altar"`<br>• `frames.world=="luoyang-local-schematic-v01"`（schema 定为 const，只是框架名）<br>• `world==null` 且 `nodeMatrixColumnMajor==null`<br>• 同时断言 `LY-006/registry/zones.json` 中 `frames["local:north-altar"].placement==null`<br>LY-004 已判北郊未配准（north-suburb.json eb4ae791…），本项不得填写任何城市数值 |
| C4 | 写区 | 本包所有新增顶点都在 `LY-080:write:001` 盒子内（local:north-altar 中 [-17,-0.3,-17]–[17,0.3,17]）。坛体原件节点不改。负例：把地坪片外扩到 x=17.5，或抬到 0.35 m，应失败 |
| C3 | 若 LY-004 放行 | 世界坐标在北城垣以北：Z < 北墙在该 X 处的 Z。并附 LY-004 证据条目 ID 和三说中采用哪一说的理由 |

C 组负例（N1–N3 都必须被判失败）：
- **N1**：在包中出现南郊圆坛四个 GLB 的任一 SHA、`m-luoyang-southern-altar`、`south-altar`，或南郊坐标。
- **N2**：世界坐标 Z > 北城垣，即落在城内或城南。
- **N3**：未经 LY-004 放行就填写非 null 的 world。目前 LY-004 的结论就是不放行，所以任何非 null 的 world 都应被判失败。
- **N4**：端口世界坐标落进 LY-004 的任一北郊三说包络，并被当成“已定址”。三说互斥、不出点，应失败。
- **N5**：LY-004 `qa/separation.json` 测得南北最近距离 4738.9 m；本包安装后这个值不得变小。

## D. 不虚构

| ID | 检查 | 通过条件 |
|---|---|---|
| D1 | 无围营、祠舍 | 包内新增网格只能是 C 地坪片，节点名白名单为 `north-suburb-ground-pad-C*`。三角形最高处 ≤ 0.05 m，不能有任何竖向墙体 |
| D2 | 说明文本 | brief 和 delivery-manifest 中不出现“完整北郊”“已定址”“180年形制已证”；必须出现“围营、祠舍未知，不建模” |

D 组负例：加一个 0.5 m 高的围墙盒子，D1 应失败。

## E. 安装与撤回

| ID | 检查 | 通过条件 |
|---|---|---|
| E1 | 安装 | 在 bce3211 的副本中按 `assembly.json` 加入 researchModels 条目（`space:"local-study"`, `cityPlacement:null`）。原有 80 个节点的矩阵和 48 个 GLB 的 SHA 不变（对照 LY-005 frames-bce3211.json） |
| E2 | 撤回 | 删除本包条目后，`city-data.mjs` 字节与原件相同：检出版 e4115705…0a1a，blob 版 c849706b…bf00 |
| E3 | 不叠载 | 同一 nodeId 不出现两次，LOD 三档不同时加载 |
| E4 | 浏览器 | 未在实际浏览器或 GPU 上测过就写“未测”，不写通过 |

## F. 继承缺陷披露（不修，只核对）

- F1：LOD1、LOD2 几何与 LOD0 相同。测量结果 `lodGeometryIdentical:true`，交付清单必须如实写“纹理档”。
  - 按 LY-007 copy_ban 判据，贴图分辨率 512/256/64 不同，所以不算“LOD0 复制”。负例：如果某档贴图也是 512 且材质名相同，应判为复制。
  - 三角形比 1.0，超出新件区间，按“夯土不降档”披露。
  - B、D 组的通行与接触检查只在 LOD0 上做。
- F1b：继承 LY-007 普查标记 `legacy_grey_texture`、`texture_not_in_library`、`material_names`、`suffix_vs_tier`、`uv_not_1m_box`。逐项写进交付清单，不修。
- F1c：坛体如果出现在新地坪片里，地坪片与坛底在 y=0 有共面接面。必须分类为“合法局部接面”，并记录面积：开孔方案为 0 m²，全铺方案为 400 m²。不能整对豁免。
- F2：材质 doubleSided；UV 重复平铺。
- F3：2R+T = 0.90 m，坛边 1.2 m 落差无栏杆。只写明这是 C 设计，不写“通行认证”。
