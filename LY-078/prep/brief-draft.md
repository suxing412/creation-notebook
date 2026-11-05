# LY-078 太学观经空间外围安装包：开工准备简报（草稿）

状态：**开工准备**。G（LY-001/002/005/006/007/008/009/010）未冻结，LY-077 未交付。本目录只有读输入、实测、测试脚本，**没有任何交付几何**。所有数字由本目录脚本对 `creation-notebook-lab` bce3211 的实际文件重算得到。

## 0. 2026-11-06 复核（上游变化与新缺口）

- **重核**：lab HEAD 仍是 bce3211，工作区干净（只有未跟踪的 `.claude/`）。三档 GLB、太学 A LOD1、city-data/项目卡提交 blob 的 SHA 全部与下文一致。`check_units.py --selftest` 近景重跑，结果一致：正例通过，5 个负例全部 fail，计数 60/79,496/36/3,492，用时 17 s。
- **上游状态**（读各席位 status.json）：
  - 已交付：LY-001、002、003、004、005、006、007、009。
  - 未交付：LY-008、010（目录里没有 status.json），LY-077（只有 prep）。
  - **G 仍未冻结**。
- **LY-006 registry v1 已冻结**，以下几项按它改：
  - 端口 ID 定为 `stoneclassic:south-mouth:road-end`（v1，kind=road-end），producer 和 steward 都是 LY-078。容差：位置 0.005 m，高程 0.002 m。local/world 由制作方交付时填。本草稿原先自拟的 `LY-078:stoneclassic:street-south:v1` **作废**。
  - 构件：`T078-port-ground`（fixed）、`T078-stele-slots-empty`（state-variant）。
  - 接缝：消费 LY-077 的 `taixue-A:outer-entry:ground@v1`。
  - 场地 S-TAIXUE 由 LY-078 负责，envelope=null。
  - 写入区 `LY-078:write:001`：local:stoneclassic 帧，盒 [-20,-0.3,18]…[20,0.5,24]，标注为「independent street-side port band + ground boundary (south)」。新地坪片须命名为 `gp:LY-078:<名>`。
  - 三档源对象 `LY_stoneclassic_access_court_C_v1_{near,middle,far}` 归 LY-078，mode=**keep**，modify/replace 为空。
- **新缺口 A：拆分与 LY-006 的写入区规则冲突**。LY-006 规定改/替换的源对象必须落在本席位写入区内，容差 0.05 m。实测（`zone_check.py` → `qa/zone-check.json`）三档都只有 **2/83,084**（中景 2/17,868，远景 2/1,608）个三角落在写入区内，就是 earth 板 z=18 的南立面。源对象往北超出写入区 34 m（z 最小 -16），往上超出 6.04 m（y 最大 6.54）。覆屋、围护、南口的 83,024 个非地面三角**全部在区外**。所以 §3 的「按连通件拆成 4 个单元」一旦算作改/替换，就违反 v1，需要先向 LY-006 申请 registry v2。v2 有两种做法：一是把三档源对象改登 modify/replace，并加 z[-16,18]、y≤6.6 的写入区；二是新增「派生无损拆分副本」类别，原件仍为 keep 且逐字节不变。v2 批下来之前，本席位只能交写入区里的街向带和端口。T2、T7 里「单元可拆可恢复」的验收卡在这个审批上。
- **新缺口 B：材质与 LY-007 基线不一致**（`material_check` 结果在 §5.9）：
  - 名字：三档都用无后缀的 `LY_P01_earth/timber/tile/plaster`，基线要求 LOD0/1 用 `__PBR`、LOD2 用 `__FLAT`。
  - 贴图：三档 textures=0、images=0，近景也只有常数因子。
  - 正反面：doubleSided=false，基线是 true。
  - 粗糙度：earth/timber/tile 分别是 0.95/0.82/0.78，基线 FLAT 一律 0.88；底色因子与基线 FLAT 在 float32 精度上一致。
  - `LY_P01_plaster`（144 个三角、12 件，三档一样）是 LY-007 点名的未定调第六种材料（P-NEWMAT 待制作人拍板，暂行办法是「新件只用五种」）。
  - 复用装配按「原样搬」不改材质，但派生单元算不算「新件」要由 LY-007/LY-010 判定，否则 plaster 会阻断。
- **LY-004 已交付**：太学属「城南礼制四所」，只有 B 研究示意描点，install180 **不放行**（P08），只放行研究标记（P19）。引文：TX5「刻石立于太学门外」，TX8 谢承书（孙吴）瓦屋、栏障、南门；「180年已立石经碑数：未知」。所以端口 world 维持 null，本包只能是 local-study，§4 里「LY-004 未交」改为「LY-004 已交、不放行」。

## 1. 本项目标（任务池原文归纳）

- 复用现有「太学门外观经空间」C 方案的覆屋、围护、南口关系，不重造。
- 交付：独立的街向端口、地面边界、互斥安装方案；覆屋、围护、南口、端口各自能拆下、能恢复。
- 碑位保持空。不造完整石经，不引用三体石经尺寸。年代不支持时只保留独立候选，不能写成 180 年已在运营。

## 2. 核到的现有成果

| 输入 | 路径（creation-notebook-lab） | SHA256（提交字节） | 城景是否加载 |
|---|---|---|---|
| 观经空间近景 | docs/library/models/m-luoyang-stoneclassic-access-court/files/stoneclassic_access_near.glb（8,977,644 B，83,084 三角） | 0fcb76be7171df172e6850e206532cd724fc4de5dcc8e7d157b182694cc649d5 | 否 |
| 观经空间中景 | …/files/stoneclassic_access_middle.glb（1,934,304 B，17,868 三角） | 5a0ff55f90105d15b4da0401e2a29db5bff67d31ce6f84696e5539b69f0c1e9f | 否 |
| 观经空间远景 | …/files/stoneclassic_access_far.glb（178,124 B，1,608 三角） | 1b45de37e02524d6866800603fa6f2d456cbbd8262d17ef252f819c689321239 | 否 |
| 资产卡 | …/m-luoyang-stoneclassic-access-court.asset.json | 提交 blob f7739797…；检出 CRLF a0408197… | 只进资产库 |
| 太学 A LOD1（v3.2 入口修订） | docs/cities/luoyang/progress-assets/taixue-A-v3.2/models/taixue-A-LOD1.glb | 413c2f35ec264dfbc6f24c1ceab9a0f8ce492c975b50e34fd5320ad25be391f2 | 只在独立研究视图里加载（扁平投影件 ee416342…，city-data.mjs 第 636 行，researchModels 第 4125 行，cityPlacement=null） |

- 观经空间 GLB 在城景代码里**一处引用都没有**（city-data.mjs、app.mjs、city-renderer.mjs、v1/*、data/* 都 grep 过）。它只出现在项目卡 members（p-luoyang.asset.json 第 534 行）和 lab/data/assets.json 里。LY-001 家族台账记为「仅模型（资产卡文件）」，城市节点 0 个。
- 节点 extras 写着：evidence_grade=C，world_coordinates=null，facility_construction_year=null，circa_180_operating_state=null，empty_epigraph_reserve="Blender x[-8,8],y[-3,3]; no steles modeled"，local_south=+Z。
- Blender 5.2.1 回读三档：每档 1 个网格物体，4 种材质（earth/timber/tile/plaster），1 个 UV 层，世界矩阵是单位阵。见 qa/blender-readback.json。

## 3. 改与不改

**改（以后制作时）**：把现有 GLB 按连通件拆成 4 个安装单元：ground / cover / enclosure / south_gate。增加局部街向端口、地面边界和 assembly.json，写明互斥规则。顶点、UV、材质原样搬过去，不改形。

**不改**：覆屋柱网和屋面形体、围护高度、南口净宽和净高、碑位范围、材质，以及太学 A/B 的任何文件。不写 city-data.mjs 和项目卡（这些只交给 LY-100 提案）。不加碑，也不给碑位填东西。

## 4. 证据与未知（引自 LY-002 E-R06 / E-R08 / X09 / X11 / X18 / X19）

- **原文（东汉事件，后世转载）**：《后汉书·蔡邕传》记熹平四年（175）奏定石经，「立于太学门外」。《儒林传》李贤注引谢承《后汉书》（孙吴）记碑上有瓦屋覆盖、四面有栏障、向南开门。覆屋、围护、南口只能作 C 依据：原文是佚文，经唐注转存，年代和设施归属都没有独立确证。
- **异期（禁用）**：杨龙骧《洛阳记》的碑高「一丈许，广四尺」属晋宋间（X18）。正始三体石经属曹魏（X11）。魏晋太学遗址的 150×220 m 不是东汉范围（X09）。185 年以后的毁损或修复状态晚于快照（X19）。
- **C 工程设计**：覆屋 24×14 m、围护 28×20 m、南口 3.6×3.1 m、地块 40×34 m、街道样段，这些全是 C。
- **未知**：180 年时已立碑数（175 年以后陆续刻立，数量未知）、观经空间在城市里的坐标（LY-004 已交付但太学不放行，只有 B 研究示意点）、它和太学门或讲堂的实际距离，以及公众能否入内。

「模型能读取」已实测。「局部通行」只做了离散的轴对齐包围盒（AABB）走廊测试。「已入城」不成立。「真实结构安全」没有验证。「历史复原成立」不成立，全部是 C。

## 5. 实测缺口（脚本都在本目录，结果在 qa/）

1. **单元不能独立恢复（主缺口）**。三档 GLB 都只有 1 节点、1 网格、4 个按材质合并的 primitive，所以覆屋、围护、南口不能单独关掉。按连通件和位置规则虚拟拆分的结果是 **0 件歧义、0 件未分类**：
   - 近景：cover 213 件 / 79,496 三角，enclosure 291 / 3,492，south_gate 3 / 36，ground 1 / 60
   - 中景：111 / 15,732，170 / 2,040，3 / 36，1 / 60
   - 远景：60 / 828，57 / 684，3 / 36，1 / 60

   check_units.py 自检：正例虚拟拆分无损、无重叠、不越界。5 个负例（去掉南口、重复 12 个三角、碑位插入一面、南口平移 0.5 m、南口并入围护）全部被拦下（qa/selftest-*.json）。脚本：measure_parts.py、classify.py、check_units.py。
2. **跨单元实体侵入 2 处**。围护的端柱（0.22×1.5×0.22 m，x ±1.99…2.21，z 9.78…10.00）插进南口门柱（0.30×3.25×0.30 m，x ±1.80…2.10，z 9.85…10.15），两侧各重叠 0.11×1.50×0.15 m = **0.02475 m³**。拆成两个单元后，这两处必须登记为合法局部接面，或者明确归属，并交 LY-006 判定所有权。单元之间其他的只是贴面接触：enclosure/ground 47，cover/ground 12，south_gate/ground 2，enclosure/south_gate 4（cross_unit_overlap.py；这是件级 AABB，不是精确实体测试）。
3. **没有端口**。GLB 里没有端口节点或 extras。街向边只能隐式推出来：局部 z=+18，x∈[-20,20]，顶面 y=0。LY-006 已冻结端口 ID `stoneclassic:south-mouth:road-end`，但 local/world 都是 null，由本席位交付时填。写入区是 z 18…24 的 6 m 南带，所以端口可以放在 z=18（现有边）或街向带外缘 z=24；放 z=24 时要新建 `gp:LY-078:` 地坪片 40×6 m=240 m²。所谓「街道样段」不是独立几何：地块是 1 种 earth 材质，由 5 块板拼成，z 分段为 [-16,-10]、[-10,10]、[10,12]、[12,17]、[17,18]，顶面都在 y=0，底面 y=-0.3，没有坡度和路缘。板间有 **8 对背靠背内部面（16 个三角、96 m²）**，位置在 z=±10、12、17，是继承下来的隐藏内部面（earth_faces.py）。
4. **地面边界只有局部坐标**。地块 40×34 m，顶面 1,360 m²。LY-005 的城市 C 地面高程是 0.20/0.21 m，而本件顶面是 0，落位时要明确 N 的 y 平移，或者交 portMinusTerrain。LY-004 没交、cityPlacement=null，所以端口的 world 姿态现在只能写 null（LY-005 port-schema 要求 world，这一项待 LY-010 准入）。
5. **南口与通行实测**。净宽 **3.60 m**（宽 3.80 的盒子碰到门柱），净高 **3.10 m**（高 3.20 的盒子碰到门楣，门楣底在 y=3.10）。0.60×1.80 m 行人包络的中心在 x∈[-1.50,1.50] 时能过门线。2.0×2.6 m 手推车包络从 z=18 到 z=3 不碰任何件。内部 z=5.5 处的柱础（x ±1.69）把走廊收窄到 3.38 m。以上都是离散 AABB 测试，不代表连续人体运动或规范认证（corridor_check.py）。
6. **碑位实测为空**。glTF 盒 x[-8,8]、z[-3,3]、y[0,3.9] 内，三档非地面件的命中数都是 **0**。屋面瓦的底面在 y=4.08，覆屋投影 x±12.085、z±7.03，碑位完全在覆屋下面。
7. **和太学 A 没有共用坐标**。A 的 LOD1 台高 0.6 m，南侧三处踏步，踏步底 z=4.85，x 中心 −10.5、1.5、10.5，宽 2.2 m，没有院外地面（LY-077 待补）。原文只说「太学门外」，现有资产里没有太学门模型。所以观经空间和 A 讲堂的任何相邻关系都只能是 C，不能焊成一院（taixue_a_steps.py）。
8. **私密源不在**。private deterministic source/build.py（Blender 4.3.2）和 .blend 都拿不到。好在 GLB 顶点不焊接（顶点数正好是三角数的 3 倍），UV 和 4 种材质齐全，按连通件拆分能**从 GLB 重建**，几何不丢。丢掉的是参数化再生成能力：比如要改柱距或门宽，就只能手改网格。
9. **材质与 LY-007 基线**（material_check.py → qa/material-check.json）。三档 4 种材质：
   - 名字：都不带后缀，基线要的 `__PBR`（LOD0/1）和 `__FLAT`（LOD2）一个都没有。
   - 底色：earth/timber/tile 的 baseColorFactor 与基线 FLAT 在 float32 上逐位相等。
   - 粗糙度：分别为 0.95、0.82、0.78，基线是 0.88。
   - 正反面：doubleSided=false，基线是 true。
   - 贴图：textures=0，近景也没有 PBR 贴图。
   - plaster：不在五种材料里，是 P-NEWMAT 点名的那一种。

   本席位不迁移材质（LY-007 P-LEGACY 暂行办法是不迁移），派生单元原样搬过去，在 extras 里登记现状。
10. **写入区冲突**（zone_check.py → qa/zone-check.json）：落在 `LY-078:write:001` 内的只有 2/83,084 个三角。详见 §0 缺口 A。

## 6. 复用判定

现有 GLB 几何**作为输入可以原样复用**（三档完整，碑位已空，南口尺度已定）。但本项验收要求的「覆屋/围护/南口与端口独立可恢复」在现有成果里**不存在**，所以不能判为「复用完成」。需要交的是拆分后的单元件、端口和装配清单，几何本身不新造。

补充（11-06）：拆分单元需要 LY-006 先发 registry v2（改登 modify/replace 或增「派生无损拆分副本」类）。v2 之前，可在 v1 写入区内独立交付的只有：
- 街向带 `gp:LY-078:*`（z 18…24，y −0.3…0.5）
- 端口 `stoneclassic:south-mouth:road-end`
- 互斥清单 X0/X1

## 7. 本目录文件 SHA256（11-06）

见 inputs.json `prepTools`。qa/ 下的报告与生成它们的脚本同目录可重跑。
