# LY-078 测试计划（按「本项验收」逐条）

验收原文：覆屋/围护/南口与端口独立可恢复，碑位保持空；来源/年代不确定不会被组合图抹去，不声称180年设施状态已定。

## 绑定 SHA（制作前先重算；任何一个变了就停，回到 prep 重新实测）

| 角色 | 文件 | SHA256 |
|---|---|---|
| 原件近景 | docs/library/models/m-luoyang-stoneclassic-access-court/files/stoneclassic_access_near.glb | 0fcb76be7171df172e6850e206532cd724fc4de5dcc8e7d157b182694cc649d5 |
| 原件中景 | …/stoneclassic_access_middle.glb | 5a0ff55f90105d15b4da0401e2a29db5bff67d31ce6f84696e5539b69f0c1e9f |
| 原件远景 | …/stoneclassic_access_far.glb | 1b45de37e02524d6866800603fa6f2d456cbbd8262d17ef252f819c689321239 |
| 太学 A（只读，LY-077 对接） | docs/cities/luoyang/progress-assets/taixue-A-v3.2/models/taixue-A-LOD1.glb | 413c2f35ec264dfbc6f24c1ceab9a0f8ce492c975b50e34fd5320ad25be391f2 |
| 城市清单（不得被本席位改动） | docs/cities/luoyang/city-data.mjs（提交 blob） | c849706b6210813c74851b86cfd3353183a47badc0e019a1151247db1e34bf00 |
| 项目卡（不得改） | docs/cities/luoyang/p-luoyang.asset.json（提交 blob） | 8edb06abf5e7d874334a932e3108079590b327ec5afbb78290df2f66424f95bd |
| LY-077 端口文件 | workpacks/LY-077/…（未交付） | 待填；缺它时 T7 只跑「无 A 端口」分支 |
| LY-006 所有权表（v1，已交付） | workpacks/LY-006/registry/ownership.json | ecbbbcf5614d41bf7c7bf3b04416504ae70891e212c7551456de4ff1a417b4ca |
| LY-006 端口表 | workpacks/LY-006/registry/ports.json | 28bcfb68cd7d7fe0026f62de23ae3e45ba8f714a139e38c0b0957039f12fc633 |
| LY-006 接缝表 | workpacks/LY-006/registry/seams.json | ca4d81f8f955333c089d782aa69c50c2ca83225d4da07f595f66d1ba87f3f4c1 |
| LY-006 区表 | workpacks/LY-006/registry/zones.json | 6b3595ac735d180866e823ddeb4e3676ffc0e816d083f6be2d57d6e4df0821c0 |
| LY-006 端口 schema | workpacks/LY-006/schemas/port.schema.json | 9fcdf932adbb4cdc58fecf19d52c7a1442955d273e75be7bc6bb9a1a5f494fdc |
| LY-006 接口校验器 | workpacks/LY-006/source/validate_interface.py | d6a6a0781ac7aa34ea1eaf7998d8ce2ed82ea6f3a4741889d0a1bdacaba6cd84 |
| LY-007 材质语义 | workpacks/LY-007/baseline/LY_P01-material-semantics.json | 见 qa/material-check.json `baselineSha256` |
| LY-004 场地约束 | workpacks/LY-004/tables/site-constraints.json | 633c3302ff1219e8d93d2a59107eae85a6d7c077f418f7b53300f642708eb77f |
| LY-006 registry v2（如申请） | workpacks/LY-006/registry/*（未发） | 待填；T2/T7 拆分单元以 v2 为准，v2 未发则只跑 T6/T10 街向带分支 |

脚本的 SHA 记在 inputs.json 的 `prepTools` 里。正式 QA 使用的脚本必须与登记的 SHA 一致，或者另行登记新版本。

## 测试项

单元名固定为 `ground`、`cover`、`enclosure`、`south_gate`，外加端口 `port:street-south`。交付可以是每档 4 个 GLB，也可以是每档 1 个 GLB 含 4 个具名节点；两种形式都要先导出成单元 GLB 再跑测试。

### T1 无损拆分（三档各跑一次）
- 命令：`python -I check_units.py --original <原件档> --units ground=… cover=… enclosure=… south_gate=… --out qa/split-<lod>.json`
- 正例：C1 到 C5 全部 pass。三角按材质并按 0.1 mm 量化，多重集合必须与原件完全相等：missingTris=0，extraTris=0，sharedKeys=0。
- 期望计数：
  - 近景 cover 79,496 / enclosure 3,492 / south_gate 36 / ground 60
  - 中景 15,732 / 2,040 / 36 / 60
  - 远景 828 / 684 / 36 / 60
- 计数变了，必须在 assembly.json 里说明是哪一件、为什么改归属。
- 负例：`--selftest` 的 5 个 NEG 都必须 fail。现状已经全部被拦下（qa/selftest-*.json，selftestOK=true）。
- 容差：位置 0.1 mm；uv 和法线另在 T5 比对。

### T2 独立拆装与恢复（每档 4 个单元，每个单元做一次关、一次开）
- 每次只关掉一个单元，回读剩下的部分：
  - 碑位仍为空（C4 hits=0）
  - 其余单元三角数不变
  - 节点矩阵不变（单位阵）
- 再把该单元装回去：多重集合与原件相等（C1 pass）。
- 覆屋、围护、南口任意子集都可以组合，但都必须有 ground；子集共 2³=8 种，全部跑。
- 「去掉 south_gate」之后，南面围护在 x∈[-1.99,1.99] 要留出开口；端柱留在 enclosure，不能出现悬空栏杆。检查办法：南面横档和栏杆的端点在 x=±2.10，必须落在端柱 x[±1.99,±2.21] 内（实测如此）。
- 负例：
  - 把端柱划给 south_gate，关掉南口后南面横档端头就没有柱子，必须报错
  - 只交 cover 不交 ground，C5 fail

### T3 跨单元接触分类
- 命令：`python -I cross_unit_overlap.py qa/parts-<lod>.json …`；正式验收另跑精确实体或 BVH 测试，并写清覆盖范围。
- 正例：正体积侵入只允许 2 处，就是端柱与门柱，每处 0.11×1.50×0.15 m = 0.02475 m³，在 assembly.json 里登记为「合法局部接面（榫接示意，C）」。归属：端柱→enclosure，门柱→south_gate。
- 负例：出现第 3 处正体积侵入，或这 2 处体积变化超过 1e-4 m³，都算未解释穿插，记为阻断。
- 只做了 AABB 时，不能写「实体碰撞已穷尽」。

### T4 碑位保持空
- 盒：glTF x[-8,8]、z[-3,3]、y[0,3.9]，与卡片 extras 的 Blender x[-8,8]、y[-3,3] 一致。
- 正例：三档所有单元、所有子集、所有安装方案下，非地面三角命中数都是 0。
- 负例：插入一个 1.0×2.0 m 的立面（qa/selftest NEG_stele_face_in_reserve），必须 fail。另外 grep 交付物，不能出现 stele、三体、正始、碑高等实体节点名，也不能出现尺寸字段。

### T5 回读一致
- Blender 5.2.1 跑 `bl_import_check.py` 导入每个单元：
  - 网格数正确，矩阵是单位阵
  - 每个物体 1 个 UV 层
  - 材质名只用 LY_P01_earth、LY_P01_timber、LY_P01_tile、LY_P01_plaster
  - 所有单元合起来的包围盒等于原件：glTF min (-20,-0.3,-16)，max (20,6.54,18)；远景 ymax 6.52
- 每个顶点的 UV 与原件对应三角逐一比对，差 ≤1e-6。
- 单 GLB 不超过 15,000,000 B。近景原件 8,977,644 B，拆分后总和预计不变量级。

### T6 街向端口与地面边界
- 端口 `stoneclassic:south-mouth:road-end`，version=1，kind=road-end，producer=steward=LY-078（LY-006 ports.json 冻结）。按 LY-006 `port.schema.json` 校验（`validate_interface.py`），容差 position 0.005 m、elevation 0.002 m；frames.local=`local:stoneclassic`，frames.world=`luoyang-local-schematic-v01`：
  - local.position = (0, 0, 18)（现有地块南边），或 (0, 0, 24)（v1 写入区外缘，前提是交了 `gp:LY-078:street-band`，40×6 m，顶面 y=0）；up = (0,1,0)，forward = (0,0,1)
  - 端口宽 40 m（x∈[-20,20]），顶面 y=0
  - world = null，直到 LY-004 和 LY-010 放行
- 正例：端口中心在 earth 顶面上，竖直高差 ≤1 mm；从端口到门线（z 18→10）的地面连续，没有洞。
- 负例：
  - 端口落在 z=18.5，那里没有地面，必须 fail
  - 端口 y=0.2，比地面高 0.2 m，必须 fail
  - 删掉 ground 后端口失去支持，必须 fail
- 地面边界多边形：x[-20,20]×z[-16,18]，面积 1,360 m²。8 对内部面（16 三角，96 m²）作为继承缺陷登记，不算外边界。
- 通行：
  - 净宽 3.60 m 正例；3.80 m 负例，碰门柱
  - 净高 3.10 m 正例；3.20 m 负例，碰门楣
  - 0.60×1.80 行人中心 x∈[-1.50,1.50] 能过门线
  - 2.0×2.6 推车盒从 z=18 到 z=3 命中 0
  - 都写明「离散 AABB，不是连续运动」

### T7 互斥安装方案
- X0：不安装（现状）。
- X1：独立研究视图，space=local-study，cityPlacement=null，N=单位阵。
- X2：局部 C 关系包。用 C 街段把 `street-south` 接到 LY-077 冻结的太学 A 院外端口；只有 LY-077 和 LY-010 都放行才可用。
- 正例：清单里 X1 和 X2 不会同时加载同一资产（同一 assetId 只出现 1 个激活实例）；X2 不改 A 的任何字节，A 的 SHA 仍是 413c2f35…。
- 负例：
  - 同时激活 X1 和 X2，必须报叠载
  - 把观经空间 ground 与 A 的地面合并成一个节点，或写成「太学一院」，必须报焊接越界
  - X2 缺 LY-077 端口 SHA，必须报阻断
- 撤回：每个方案装上再撤下以后，原节点、几何、材质、矩阵逐字节不变；city-data 的 dump 与 bce3211（或当时的新基线）一致。

### T8 证据不被组合图抹去
- assembly.json、preview 图注、单元节点 extras 必须保留这些字段：evidence_grade=C、facility_construction_year=null、circa_180_operating_state=null、world_coordinates=null（未放行时）、来源「谢承书（孙吴）经李贤注转引」。
- 组合预览图的图注必须写「C 方案；碑位留空；年代与设施归属待考；未入城」。
- 负例：用文本检查 grep 交付文字，下面任何一种都算 fail：
  - 出现「180 年已运营」「熹平石经原貌」「复原」「已入城」这类定性
  - 引用杨龙骧碑尺寸
  - 引用魏晋 150×220 m

### T10 写入区与所有权（LY-006 v1/v2）
- 命令：`python -I zone_check.py <每个交付 GLB> --out qa/zone-<名>.json`，然后跑 LY-006 的 `validate_interface.py` 校验本席位接口文件。
- 正例：
  - 新地坪片都命名为 `gp:LY-078:*`，所有三角落在 `LY-078:write:001` 内（[-20,-0.3,18]…[20,0.5,24]，±0.05 m）。
  - 原三档源对象（mode=keep）SHA 不变：0fcb76be… / 5a0ff55f… / 1b45de37…
- 现状基线：源对象落在区内的三角三档都是 2 个（只有 earth 板 z=18 的面）；z 方向超出 34 m，y 方向超出 6.04 m。
- 负例：
  - 没有 v2 就把 cover/enclosure/south_gate 当作 modify/replace 交出，必须 fail，因为 83,024 个三角落在区外。
  - 地坪片顶面写成 y=0.2，即把城市 C 地坪烘进网格，要报 LY-005 R4 违例。
  - 写入区与 LY-077 写入区体积交 > 0，必须 fail。

### T11 材质基线（LY-007）
- 命令：`python -I material_check.py <LY-007 semantics> <单元 GLB…> --out qa/material-<名>.json`
- 正例（原样搬）：每个单元的材质名、因子、doubleSided 都与原件逐值相等，现状差异照实写进 extras：名字不带后缀、粗糙度 0.95/0.82/0.78 对基线 0.88、单面、无贴图、plaster 未定调。
- 负例：
  - 派生单元悄悄改名成 `__PBR` 却不挂贴图，必须 fail，因为与 LY-007 的 PBR 结构不符。
  - 新地坪片用 plaster，或用五种以外的材料，必须 fail（P-NEWMAT 暂行办法）。
  - 新地坪片应该用 `LY_P01_earth__*` 或 `LY_P01_path__*`，按档命名。

### T9 公共检查
- 合并前由 LY-100 在隔离副本里跑 `lab/tools/build_assets.py --check`，本席位不跑。还要跑 LY-008 检查器（未交付），结果绑定单元 SHA。
