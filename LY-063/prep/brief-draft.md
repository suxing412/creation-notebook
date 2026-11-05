# LY-063 侧廊端部转折安装模块 · 开工准备 brief（草稿）

状态：**待输入**（G 未冻结，LY-061 未交付）。本目录只有读输入、实测和测试准备，没有任何交付几何。
第二轮核对（2026-11-05 23:50）：LY-001/002/005/006/007/009 已交付，LY-008 无 status、LY-010 目录不存在，所以 G 仍未冻结。本轮按 LY-006 registry v1 补了写入区实测（第 7 节），并把文本类输入的提交字节 SHA 写进 inputs.json（`sha256Commit`；本机 core.autocrlf=true，文本类工作区字节与提交字节不同，QA 一律绑提交字节）。第一轮的两份输出复跑后逐字节一致（见 inputs.json `reproducibility`）。
核对基线：creation-notebook-lab main `bce3211f818ee5a8bef1773539da70695ba37b17`；任务池 `TASKPOOL.md` sha256 `00c2e171…66c7`，`taskboard.json` sha256 `1d1fcb9c…5ae4`。
测量环境：Blender 5.2.1 LTS（`-b --factory-startup`，只导入不保存）。坐标一律是 Blender 世界坐标（Z 向上，米）；glTF Y-up 由导入器转换。

## 1. 本项目标

任务池原文（LY-063）：对选定八间侧廊端部提供可替换收口/转折和地坪过渡件。已修入口台阶不重做，不缩放柱网；转折是 C 连接试验，不能外推完整宫院平面。

本次准备把这句话落到实测对象上：

- 「八间侧廊」= `m-luoyang-palace-sidehall`（宫廷侧廊庑，sidehall-A，9 柱 8 间）。
- 「端部」= 它在 `m-luoyang-palace-admission-court`（无名宫院通行组合）里的两座实例 `west_gallery`、`east_gallery` 各两端，共 **4 个端部**：西北 W-N、西南 W-S、东北 E-N、东南 E-S。哪几端真正做、做收口还是转折，要等 LY-010 选方案、LY-006 冻结端口与所有权。
- 产物分三类，都是 C 级工程设计：
  1. **收口件**：封住端部开放的廊道，或者给它一个下到庭地的台阶。
  2. **转折件**：一个 C 连接试验，在端部转 90°，接向 LY-061 的外围或殿堂台缘。
  3. **地坪过渡件**：台基 0.45 m 与庭地 0.00 m 之间的踏步或边缘过渡。

## 2. 核到的现有成果（只读）

| 输入 | 路径 | SHA256 | 在城景中加载？ |
|---|---|---|---|
| 侧廊庑 LOD0 | docs/library/models/m-luoyang-palace-sidehall/files/sidehall-A-LOD0.glb | bd000b1bf36419eebe884dbe1c92368f30ceab7597290aa6eafdbdbd971e32c2 | 否，只在资产详情页加载：lab/asset.html:35/112（lab 站）与 docs/model-library/inspect.mjs:136（公开站） |
| 侧廊庑 LOD1 | …/sidehall-A-LOD1.glb | 547935049e53cee8d8a8c7613154365696065256722cf09f52914dc3dd3dddd1 | 否 |
| 侧廊庑 LOD2 | …/sidehall-A-LOD2.glb | b4c64f499c9c706649e637a9f379bf5328dbf386f9161cc50db346907c612973 | 否 |
| 侧廊庑卡 | …/m-luoyang-palace-sidehall.asset.json | d353b3a0a80647996f254f6c70b47588053933f658137abb0f510eca643f5b85 | 否（项目卡 members 列出） |
| 宫院组合 open LOD0/1/2 | docs/library/models/m-luoyang-palace-admission-court/files/palace-admission-court-open-LOD{0,1,2}.glb | 59c8b758…c4b0 / d95bd22f…8281 / 01b2017f…3b3d | 否 |
| 宫院组合 closed LOD0/1/2 | …/palace-admission-court-closed-LOD{0,1,2}.glb | 6ea89298…00a8 / 455a1215…53d2 / 108e28a5…101d | 否 |
| 同一组合的 progress-assets 副本 | docs/cities/luoyang/progress-assets/palace-admission-court/*.glb | 与上面六份逐字节相同 | 否：city-data.mjs 中没有任何 palace/sidehall 引用（grep 计数 0） |
| 组合 QA | progress-assets/palace-admission-court/qa/finite-routes.json 等 | 见 inputs.json | — |

已核实：宫院组合 `independent-geometry-review.json` 锁定的 `inputs/sidehall-A-LOD{0,1,2}.glb` SHA，与当前资产卡上的三份侧廊庑 GLB 一致。也就是说，组合里用的就是「入口踏步已修」的最新版侧廊庑，没有旧版混入。

其他「现有输入」（德阳 A、门卫切片、对阙、玉堂 A/B）的 SHA 见 inputs.json。对阙和玉堂不在本组合里，跟本项端部没有几何关系，只登记版本备查。

## 3. 改 / 不改范围（拟）

**不改**（逐项绑定 SHA 或指纹检查，见 test-plan.md）：
- 侧廊庑三档 GLB 的 earth/timber/tile 原网格、UV、材质。
- 入口踏步。指纹：本地 `aae2fb16…`；组合世界坐标西廊 `c68de40c…`、东廊 `4855d60c…`。
- 柱网：间距 4.5 m，三排，每排 9 柱。
- 实例矩阵：缩放 = 1。
- 宫院组合六份 GLB 本体：以 overlay 方式安装，不重导出组合。
- 殿堂、门卫、新庭地 `new_court_support_C`。
- city-data.mjs、项目卡、cityPlacement（保持 null）。

**改/新增**（G 冻结后才做）：
- 在端部外侧新增独立节点：收口件、转折件、地坪过渡件，各三档，可安装、可撤回，互斥变体同一端只启用一个。
- 只在端部外侧的庭地上落脚。如需在庭地切孔，以 LY-006 判给本席位为前提。

## 4. 证据与未知

| 事项 | 分类 | 说明 |
|---|---|---|
| 侧廊庑形制、八间、台基 0.45 m、入口位置 | C 工程设计 | 资产卡原文：「偏移入口与相应台阶尺寸仅为C功能设计，不是汉代规制」 |
| 宫院组合的空间关系（廊距、殿距、朝向） | C 工程设计 | evidence.md：「庭地长宽、门殿间距…侧廊角度…和所有坐标均为C」 |
| 宫门准入、夹道值守、殿门宿卫 | 原始原文（功能层面） | 《后汉书·百官二》，组合 source.json 已引。只支持功能，不支持任何廊庑转角形式 |
| 廊庑端部收口/转角做法 | **未知** | 本次没有检索到约 180 年洛阳的直接材料。汉画像砖、明器院落属于异地异期类比，北魏、西汉长安材料都不能当事实用。转折件只能标 C 连接试验 |
| 宫院整体平面是否闭合、廊是否接殿 | **未知** | 不能由转折件反推；转折件不得暗示完整宫院平面 |

本次没有用 WebSearch/WebFetch，所以没有新的外部引文。LY-002 已交付的证据表（`LY-002/tables/family-binding.json`）把侧廊庑家族绑定到 E-P01、E-P04–E-P07，禁用 X04（曹魏至北魏阊阖门/太极殿中轴）、X05（魏晋东掖门）、X19（185 年后焚毁/重修状态）。其中没有一条讲廊庑端部或转角做法。E-S03 引《五行志》光和三年「公府驻驾庑自坏，南北三十余闲」，只说明约 180 年洛阳有多间连续的庑。它说的是三公府，不是宫院，也不涉及转角，不能用来定形。

## 5. 实测缺口（数字和脚本）

测量脚本在 `prep/scripts/`，输出在 `prep/out/`，SHA 见 inputs.json 的 prepArtifacts。

### 5.1 侧廊庑本体（standalone，`out/ends-sidehall-A-LOD{0,1,2}.json`）
- 台基顶 z = **0.45**，平面 **38.0 × 10.3 m**（本地 x −19…19，y −5.3…5.0）。
- 柱网：三排柱，本地 y = −3.5、0.0、+3.5，每排 9 柱，x = −18 … +18，间距 **4.5 m**。柱础 0.65 × 0.65 m，高 0.20 m（z 0.45→0.65）。
- 端柱中心距台基端 **1.0 m**，所以柱础外皮到台基端的净距只有 **0.675 m**。
- 入口踏步只有一处：本地 x 0.25…4.25（宽 4.0 m），踏面 0.15/0.30，三级 0.15 m 级高，单级进深 0.30 m，总进深 0.60 m。**两端都没有踏步**。
- 瓦面在端部外挑 **0.8 m**。端部最低瓦 z = 4.44，比台基高 **3.99 m**。
- 三档的 earth 网格完全相同：780 三角，指纹 `8c31be28…`。timber 2052/1188/468，tile 5624/792/32。

### 5.2 端部现状（组合内，`out/ends-palace-admission-court-{open,closed}-LOD{0,1,2}.json`）
四个端部情况相同，下面以东廊为例：
- 端部有三条沿长轴贯通的开放通道。台基以上 0.3/1.0/1.6 m 的射线穿过整座 38 m 廊都没有撞到东西：
  - 前檐台明：宽 **1.6 m**（x 18.7–20.3）
  - 檐廊：宽 **3.1 m**（x 20.7–23.8）
  - 后檐台明：宽 **1.3 m**（x 27.7–29.0）

  合计 **6.0 m 开口 / 端**，端外直接是 **0.45 m 垂直落差**到庭地 z = 0.00，没有踏步，也没有栏挡。
- 四个端部 × 六份 GLB 结果一致，开门与闭门不影响端部。
- 原组合的 99 条有限通行带只覆盖入口 → 檐廊 → 八间房门。廊道带范围是 y −47.75…−16.25（西廊），**两端最后 3.25 m 一直没测过**（y −51.0…−47.75 与 −16.25…−13.0）。

### 5.3 邻接（`out/neighbours-open-LOD0.json`）
- **北端与殿堂**：殿台顶 z = **1.80**，台平面 x ±17.5，y −12.84…12.5。殿前踏步在 x ±3.5，与本项无关。
  - 廊北端 y = −13.0，廊内侧台边 x = ±18.7。
  - 与殿台角 (±17.5, −12.5) 的平面距离 **1.3 m**：x 向 1.2 m，y 向 0.5 m。
  - 高差 **1.35 m**（1.80 − 0.45）。中间是 z = 0.00 的庭地。
  - 屋面不相接：廊瓦 x ≥ 18.19、z 4.44–6.33；殿瓦 x ≤ 16.01、z ≥ 8.82。平面隔 **2.18 m**。
- **南端与门卫**：最近的门卫瓦件在 **12.07 m** 外，中间庭地连续，z = 0。
- **后侧与庭地边**：廊后台边 x = ±29.0，庭地边 x = ±34.0，余 **5.0 m**。这一带属于 LY-061 的外围。

### 5.4 人体包络基线（`out/envelope-baseline-{open,closed}-LOD0.json`，脚本 turn_envelope_check.py）
包络：0.8 m 宽 × 0.5 m 深 × 1.8 m 高；3 × 3 支承探针；最大级高 0.16 m；步长 0.05 m；转角每 5° 一采样。开门、闭门两份结果完全相同。

| 路径 | 结果 | 失败计数 |
|---|---|---|
| P1/P2 东/西檐廊直行 y −40→−16（正例） | 通过 | 0 |
| N1–N4 四个端部沿檐廊继续走出端部（负例） | 失败 | 各 overhang 10、riser 1（0.45 m） |
| T1/T2 东廊北/南端在台基上转 90° 到前台明 | 失败 | overhang 30、riser 2（柱础 0.20 m）、collision 12 |
| T3 东北端直接转向殿台 | 失败 | overhang 10、riser 1（−0.45）、collision 26（撞殿台侧壁） |
| NC1 穿过前檐柱列（负对照） | 失败 | overhang 45、riser 3、collision 34 |

结论：**现有台基上做不出转折**。端柱外净距 0.675 m，小于 0.8 m 包络，转体时还会探出台基端。所以转折件必须在台基端外另加支承面，并且不改原台基 earth 指纹。北端直连殿台要爬 1.35 m：按 0.15 m 级高要 9 级、约 2.7 m 进深，而现有空隙 y 向只有 0.5 m。不移动建筑就装不下，需要 LY-010/LY-006 决定，本席位不自行移动原件。

## 6. 复用判定

**无可直接复用的合格成果。** 侧廊庑卡只有三份整体 GLB，组合里也没有任何端部件。`m-passage-interface` 虽然有 elbow/end 预设，但卡片自述是「盒状地坪与挡板无顶通行试验，不是汉代廊房或建筑成品」：没有柱网、檐口和材质语义，不合格。可以复用的只有参数：现有入口踏步的 0.15 m 级高、0.30 m 踏面，可作为地坪过渡件的 C 模板，但不计新证据。

## 7. LY-006 registry v1 对本席位的约束与实测（第二轮新增）

LY-006 已交付 registry v1（`LY-006/registry/*.json`，SHA 见 inputs.json `gSeatInputs`）。和本席位有关的条目如下：

- **构件**：`P063-end-turns`，fixed。
- **产出端口**：`sidehall:ends:floor` v1，消费方 LY-069。数值是 null，交付时由本席位填。
- **消费端口**：`admission-court:enclosure:wall-end` v1，生产方 LY-061。数值同样是 null。
- **源对象**：`palace-sidehall:sidehall-A-static_{earth,timber,tile}`，本席位是 keep 管家，**不得改**。
- **组合节点**：组合内的 `west/east_gallery__*` 与 `new_court_support_C` 都归 LY-061，keep。所以本席位在庭地上**没有切孔权**，cutZones 和 groundPieces 都是空的。
- **写入区**：4 个，frame 是 `local:admission-court`，用 glTF 轴（+Y 上，+Z 图面南）。换成 Blender 坐标（X, Y, Z）=（x, −z, y），对应关系如下：

| 写入区 | Blender 盒（x / y / z） | 对应端部 |
|---|---|---|
| LY-063:write:001 | −29.0…−18.1 / −13.0…−10.0 / −0.2…6.4 | W-N |
| LY-063:write:002 | −29.0…−18.1 / −54.0…−51.0 / −0.2…6.4 | W-S |
| LY-063:write:003 | 18.1…29.0 / −13.0…−10.0 / −0.2…6.4 | E-N |
| LY-063:write:004 | 18.1…29.0 / −54.0…−51.0 / −0.2…6.4 | E-S |

每个写入区都是 10.9 × 3.0 m，高 6.6 m。

实测脚本是 `scripts/zone_fit.py`。输出 `out/zone-fit-{open,closed}-LOD0.json`、`zone-fit-open-LOD1.json`、`zone-fit-open-LOD2.json`。四个区、六种姿态和档位组合的结果一致（瓦檐数值 LOD1/2 取整到 0.8 m）：

1. **区内地面**：0.1 m 网格共 3,270 个样点，全部向下命中 `new_court_support_C`，顶面 z = 0.000，无空洞。
   在 z 0.01–1.81 m 的身体高度内，3,269 个样点没有任何原有三角形，可用面积 32.69 m²。剩下 1 个样点贴着台基端面 y = ±13.0 / −51.0，属于接面。
2. **区内的原有几何**：只有侧廊瓦檐。它是端部外挑的 0.8 m，覆盖 y −13.0…−12.2（南端是 −51.0…−51.8），z 4.44–6.33，命中 864 个样点（8.64 m²）。新件屋面不得与它交体。
3. **缺口 A：后檐挑出写入区**。原瓦檐在端部带内一直挑到 x = ±29.809，z 4.44–4.65，比写入区外缘 ±29.0 多 **0.809 m**（LOD1/2 为 0.800 m）。端部收口件只要沿原檐口线做山面或檐口回转，后檐一侧就会越出写入区 0.81 m。前檐一侧（x = ±18.19）在区内。
4. **缺口 B：通向外围的 5 m 无主带**。廊后台边 x = ±29.0 到 LY-061 外围写入区 x = ±34…±36 之间，四个端部带上的 x 29–34、y 各端 3 m 范围，**没有任何席位的写入区**。
   LY-062 的西/东侧口（glTF z 10…16，即 Blender y −16…−10）与北端写入区的 y 范围重叠 3 m，两者相隔 **5.0 m**。
   本席位还要消费 `admission-court:enclosure:wall-end`。按现在的写入区，接到外围墙端的转折件无处可放。
5. **北端与殿堂**：北端写入区距殿台（z < 2.5 的几何）平面 **0.6 m**。殿台角在 (±17.5, −12.5)，殿台属 LY-065 / LY-070，不在本席位区内。第 5.3 节的直连殿台方案（要 9 级、约 2.7 m 进深）在现有写入区内不可能实现。
6. **南端**：南端写入区四周 5 m 内只有 LY-061:write:005/007（x ±34…±36）。距 LY-061 南墙区 13.0 m。

**在现有写入区内可以做的**（仍需 LY-010 选定）：

- **收口-封闭**：在 y = −13.0 / −51.0 端面外加墙或栏，挡住三条通道（共 6.0 m 宽）。
- **收口-踏步/地坪过渡**：0.45 m 分 3 级，每级 0.15，踏面 0.30，总进深 ≥ 0.6 m，落在 z = 0 的庭地上。写入区进深 3.0 m，够用。
- **区内 90° 转折**：在端部外的 3 m 带内新做 0.45 m 台面，再转向庭内（−x / +x 方向），下踏步到庭地。
  0.8 × 0.5 m 包络的转体圆直径是 2 × √(0.4² + 0.25²) = **0.94 m**，区内 3.0 m 进深足够。

**不改写入区就做不了的**：

- 接 LY-061 外围墙端或 LY-062 侧口的转折：要越过 5 m 无主带。
- 沿原后檐线回转的檐口：要越出 0.81 m。
- 接殿台：要越进 LY-065 的台缘。

这三项要先让 LY-006 修订 registry，并由 LY-010 选方案。本席位不自行扩区。

## 8. 依赖与开工判断

| 依赖 | 状态（2026-11-05 23:50） | 对本席位的作用 |
|---|---|---|
| LY-001 快照 | 交付完成 | 基线 bce3211、提交字节 SHA 口径 |
| LY-002 证据/禁用 | 交付完成 | E-P01、E-P04–07；禁用 X04、X05、X19；端部形制仍是未知 |
| LY-005 坐标契约 | 交付完成 | glTF↔Blender 映射；缩放 = 1，只绕 Y 旋转；新件本地 y = 0 是接地面，端口要写本地和世界两种坐标 |
| LY-006 端口/所有权 | 交付完成（registry v1） | 写入区、端口 ID、keep 对象（第 7 节）；缺口 A、B 要它修订 |
| LY-007 材质/三档 | 交付完成（宫院族数字标「待复核」） | LY_P01 语义、LOD 命名规则 |
| LY-008 检查器 | **未交付**（无 status.json） | 交付检查入口和负例 |
| LY-009 任务锁 | 交付完成 | 白名单 `LY-063/**`，禁 `*.blend*` 和 `*.zip`，单个 GLB 不超过 15,000,000 B；PZ-02 暂停区：不得入城 |
| LY-010 方案/准入 | **未开始**（目录不存在） | 做哪几个端部，收口还是转折，是否批准缺口 A/B |
| LY-061 外围 | 只有 prep | 端口 `admission-court:enclosure:wall-end` 的数值 |

结论：**G 冻结、LY-061 交付之后可以立即开工。** 测量脚本、基线输出、正负例路径都已就绪。

前提是 LY-010 只选「收口/地坪过渡/区内转折」三项之一，或者 LY-006 同时补上缺口 A、B。如果 LY-010 选了「接外围墙端」，但 LY-006 没有扩区，本席位会转为**阻断**，不会自行越界。

`.blend` 文件不能存进本工作包（LY-009 deny 规则）。原生源要用生成器脚本加参数（放在 `source/`）交付，并注明「从 GLB 重建」。

## 9. 复现

所有命令都在 `D:/GitHub/creation-notebook-workpacks` 下运行，`L=D:/GitHub/creation-notebook-lab/docs/library/models`：

```
D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P LY-063/prep/scripts/measure_gallery_ends.py -- <glb> LY-063/prep/out/ends-<name>.json
D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P LY-063/prep/scripts/measure_neighbours.py -- $L/m-luoyang-palace-admission-court/files/palace-admission-court-open-LOD0.glb LY-063/prep/out/neighbours-open-LOD0.json
D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P LY-063/prep/scripts/turn_envelope_check.py -- <court.glb> LY-063/prep/scripts/paths-court-baseline.json LY-063/prep/out/envelope-baseline-<pose>-LOD0.json
D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P LY-063/prep/scripts/zone_fit.py -- <court.glb> LY-006/registry/zones.json LY-063/prep/out/zone-fit-<pose>-<lod>.json
```

脚本和输出的 SHA256 全部列在 inputs.json `prepArtifacts`。
