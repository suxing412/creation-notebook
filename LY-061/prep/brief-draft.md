# LY-061｜无名候入院外围墙体 · 开工准备（brief 草稿 v2）

阶段：开工准备。G 包没有冻结：LY-001、002、005、006、007 已交件（005 自标 frozen-candidate）；LY-008、LY-009 没有 status.json；LY-010 目录不存在。本席位**没有制作或修改任何交付几何**，只读输入、实测缺口、写测试。lab 仓库只读，工作区 HEAD = `bce3211f818ee5a8bef1773539da70695ba37b17`。本地 main 已到 44c66da，但 bce3211..44c66da 只删了 yong-city-v1 进度副本，没有碰本席位的任何输入，已用 `git diff --stat` 核对。

v2 与 v1（21:10）的区别：LY-006 registry v1 在 22:41 成为冻结候选，给了本席位七个写入区。v1 设想的「南墙接到值守单元外侧面 x=±7」**不在任何写入区内，作废**。外围改为贴在平板外侧的一圈 2 m 带，见 3.5。

## 1. 本项目标

给现有「无名宫院通行组合」（m-luoyang-palace-admission-court）补一圈**完整外围**，包括四段墙身、四个转角和基脚。门卫、庭地、两侧廊和殿阶都复用，不重造。实名和绝对位置都不确定，所以只作**局部 C 试案**（frame `local:admission-court`，world 为 null）。

不做：
- 不重造殿和廊；不把组合命名为德阳或玉堂；不放进南宫或北宫；不复用 31 组重复宫殿。
- 不做三个开口的关闭件（LY-062:write:001..003）。
- 不做侧廊端部转折（LY-063），不做阙前庭（LY-064）。

## 2. 核到的现有成果（只读）

| 成果 | 文件 | SHA256 |
|---|---|---|
| 候入院 开门 LOD0/1/2 | docs/library/models/m-luoyang-palace-admission-court/files/palace-admission-court-open-LOD{0,1,2}.glb | 59c8b758…45c4b0 / d95bd22f…148281 / 01b2017f…3a33d |
| 候入院 闭门 LOD0/1/2 | …/palace-admission-court-closed-LOD{0,1,2}.glb | 6ea89298…6500a8 / 455a1215…53d2 / 108e28a5…0101d |
| 卡片 | …/m-luoyang-palace-admission-court.asset.json | 提交字节 7df2a184…f560 |
| 来源合同 / QA | docs/cities/luoyang/progress-assets/palace-admission-court/source.json、qa/summary.json、finite-routes.json、route-interfaces.json | 1653e115… / 67a3325b… / 3b57011c… / 0d42d41e… |
| 门卫切片、侧廊 A、殿堂 A 原件 | m-luoyang-palace-guard、-sidehall、-deyang-hall 的 files/*.glb | 见 inputs.json |
| LY-006 registry v1 | workpacks/LY-006/registry/zones.json、seats.json、ports.json、seams.json、ownership.json | 6b3595ac… / a1426412… / 28bcfb68… / ca4d81f8… / ecbbbcf5… |
| LY-005 坐标契约候选 | workpacks/LY-005/coordinate-contract.json | b6d7fe9d… |

67 项输入的完整 SHA 都在 `inputs.json`。原来的 55 项已在夜间复核，除 lab/data/assets.json 的工作区字节外全部一致。assets.json 的工作区字节会随 CRLF 和他人未提交的修改而变，但 `git hash-object` 等于 HEAD blob，所以绑定一律用提交字节 53d86312…。

**城景加载**：六份候入院 GLB 和所有宫院原件，城景都不加载。在 `city-data.mjs`、`app.mjs`、`city-renderer.mjs`、`v1/*` 中检索 admission、guard-slice、sidehall、deyang、yutang、palaceque，命中 0 个。v1 里有两处 "palace-" 命中，都是 north-palace-conflict-layer.json，与本组合无关。只有资产详情页 `docs/model-library/inspect.mjs` 会按卡片的 files 列表加载它们。原组合 source.json 的 `limits` 自述："No enclosing palace wall; closed center gate does not secure the full compound"。

**复用判定：无。**
- 资产库里没有宫院围墙件。
- 夯土墙身家族 m-luoyang-earthwall-family 是城垣尺度（A 厚 14 m；C 高 6 m、厚 8 m），而写入区只有 2 m 宽。不能原样使用，缩放也不允许。
- m-luoyang-palace-waterway-interface 是涵洞，不是墙。
- 只能复用夯土材质语义（LY-007 baseline 的 LY_P01 earth）。

## 3. 实测缺口

脚本在 `prep/scripts/`，都用 Blender 后台导入 GLB 测量，不保存场景；输出在 `prep/out/`。Blender 坐标为 Z 向上、米制、北为 +Y。LY-006 的区间是 glTF 坐标，按 LY-005 契约换算：Blender (X,Y,Z) = glTF (x, −z, y)。

### 3.1 庭地支承面（new_court_support_C）
- 平板为矩形：x −34…34、y −67…20，68 × 87 m，周长 310 m。
- 只有两个 z 值：顶 0.000，底 −0.200。
- 中间开孔 x ±10、y −65…−51，由门卫地板 `guard__guard-slice-ground-earth` 填上。
- 三档 LOD 的平板完全相同；开门和闭门只差两扇门叶。

### 3.2 平板外没有任何支承（zone_check）
- 沿四边每 0.25 m 取一个样点，共 1,244 个。在边外 0.05 m 处向下打射线，**命中 0 个**。
- 在边内 0.05 m 处向下打射线，全部落在 z=0.000。每边各有 1 个未命中，是采样点正好落在角点上造成的。
- 闭门 LOD0、开门 LOD0、闭门 LOD2 三份资产结果相同。
- 结论：写入区里的墙和基脚，在本局部帧中**下方没有任何地坪**。基脚只能贴在平板侧面（x=±34、y=−67、y=20，z −0.2…0），或者在写入区内自带垫层，垫层以下是未定义地形。这是契约缺口，已列入 inputsMissing。

### 3.3 外围开放度：100% 敞开（measure_court，v1 结果仍有效）
- 1,240 个由外向内的水平射线样点，高度取 0.3、1.0、1.6 m，被挡住的为 0。
- 西 87 m、东 87 m、南 68 m、北 68 m 全部敞开，合计 310 m。

### 3.4 南门线直线漏洞（gate_line_leaks，v1 结果仍有效）
- 闭门：两翼 x −34…−6.85 与 6.85…34 各 27.15 m；值守单元内 6 条直通口 ±(5.10–6.05)、±(3.45–4.50)、±(2.10–3.15)，合计 6.2 m。总计 60.5 m。
- 开门：再加中央 2.7 m（−1.35…1.35）。
- 这是下界：只统计宽度 ≥0.8 m 的直线开口。

### 3.5 LY-006 写入区与现有几何（zone_check，新增）

| 区 | Blender 盒（x / y / z） | 现有三角侵入 |
|---|---|---|
| LY-061:write:001 北 | −36…36 / 20…22 / −0.3…6.0 | 0 |
| 002 南西 / 003 南东 | −36…−3、3…36 / −69…−67 | 0 / 0 |
| 004 西北 / 005 西南 | −36…−34 / −10…20、−67…−16 | 0 / 0 |
| 006 东北 / 007 东南 | 34…36 / −10…20、−67…−16 | 0 / 0 |
| LY-062:write:001 / 002（西、东侧口） | ∓36…∓34 / −16…−10 | 0 / 0 |
| LY-062:write:003（南口，registry 标作 "rear work opening"） | −3…3 / −69…−67 | 0 |
| LY-063:write:001..004（廊端） | ±18.1…±29 / −13…−10、−54…−51 | 侧廊瓦 149 个（LOD2 为 23 个）、平板 1–2 个，属 LY-063 的事 |

由此确定：
1. **七个写入区的内皮正好贴着平板四边**（x=±34、y=−67、y=20），三份资产的区内现有三角都是 0，原节点不会被墙体侵入。
2. **外围环长**：中线长北 72 m、南 2×33 m、西 30+51 m、东 30+51 m，合计 300 m。另有三个声明开口，每个 6 m，共 18 m；闭合环全长 318 m。四个 2×2 m 角块归北区和南区。
3. **高度上限 6.0 m，基底下限 −0.3 m**。基脚最多比平板底再低 0.1 m，不能伸到平板下面，因为写入区不含平板投影。
4. **v1 的南接头作废**。值守单元外侧面（x=±7.0，y −61…−55）不在任何 LY-061 写入区内。门卫瓦檐（±7.367，底 3.05 m）距写入区 26.6 m，侧廊瓦檐（±29.809）距写入区 4.19 m，二者都**不再约束墙高**。
5. **南墙在门卫前另成一道外线**。门卫前沿 y=−61 与南墙内皮 y=−67 之间有一条 6 m 前庭带，向两翼 x ±7…±34 敞开，直通庭内。所以加了外围以后：
   - 门卫切片变成**内检查点**；
   - 只要 LY-062 的南口（±3 m）开着，闭门也**不能**封住整个组合，从两翼就能绕过门卫；
   - 3.4 的 60.5 m 门线漏洞变成院内路径，不再算外围漏洞。
   这一点必须写进 assembly.json 的声明，并通知 LY-062。
6. **南口朝向标错**。闭门 LOD0 中，从南口向内打射线：x ±1…±2 在 11.58–12.55 m 处命中门卫闸口和门叶（y −57.4…−56.5）；x ±2.5…±3 不命中，穿过的正是值守单元直通口 ±(2.10–3.15)。可见 LY-062:write:003 正对主门，是**前口**，不是 registry 写的 "rear work opening"。殿在北面（y 12.5 一带），北边没有开口。请 LY-006 改标注，几何不用改。
7. **侧口内侧**。西侧口内向射线：y −16…−13.5 段在 7.0 m 处命中廊台（x=−29）；y −13…−10 段直通 18.5 m，命中 x=−17.5。也就是说侧口正对侧廊北端，紧邻 LY-063 的廊端区（y −13…−10）。
8. **端口粒度不够**。registry 只有一个端口 `admission-court:enclosure:wall-end`，消费方是 LY-062 和 LY-063，但实际有 6 个墙端：三个开口各两端。LY-063 的写入区离外围最近 5 m（x −29 对 −34），与外围没有共面，所以 seam LY-061→LY-063 找不到几何接缝。请 LY-006 把端口拆成 6 个或加索引，并确认 LY-063 实际消费什么。

### 3.6 原通行不受影响的前提
- 原 99 条通行带里，伸到平板边 2 m 以内的只有 `outer_ground_join`（x ±0.4，y −66.5…−65）。它的外端离平板南边 0.5 m，正对南口 ±3 m。南墙两段从 x=±3 起，不会截断它。
- 其余通行带都在 x ±26、y −66.5…2 以内。

## 4. 改与不改

**改（新造）**：一件外围叠加 GLB，三档 LOD，开门和闭门共用，外围没有动件。内容：
- 七段墙和四个角，严格落在 LY-061:write:001..007 内；
- 基脚：内皮与平板侧面共面接触，底面 ≥ −0.3；
- 6 个墙端面，正对 LY-062 的三个开口；
- 交付时填写 `admission-court:enclosure:wall-end` 的端口值。

原点与组合相同，不另立坐标系；city/world 保持 null。

**不改**：
- 组合的 26 个节点（16 个网格）的几何、UV、材质和矩阵；
- 门卫切片、侧廊、殿堂原件；
- 原 99 条通行带、73 个接口、18,487 个支承点的判定；
- 卡片标题，historicalPalace 保持 null。

**登记但不关闭**：
- 三个开口，每个 6 m，归 LY-062；
- 门卫值守单元内的 6 条直通口和两翼通道，现在是院内路径，在 assembly.json 中登记为「内部、不属外围」。

## 5. 证据与未知
- **原始原文**：《后汉书·志第二十五·百官二》（source.json 已引）。只支持「宫门受控准入、夹道屯列、殿门另有宿卫」，**不**记载候入院有独立围墙，也不记载墙厚、墙高或平面。
- **异地异期类比，不能直接用**：北魏宫城墙、曹魏阊阖门、魏晋东掖门、西汉长安宫墙。source.json 已把它们列为排除项。
- **C 工程设计**：墙线位置（来自 LY-006 的 C 分区）、墙厚（≤2 m）、墙高（≤6 m）、收分、基脚、转角、端面，以及墙外支承基准。
- **未知**：约 180 年时候入院是否有独立围墙，还是由宫墙或廊庑围合；属哪座宫城；朝向；绝对坐标。
- 「模型能读取」「局部通行通过」「已入城」「真实结构安全」「历史复原成立」是五件事，分开记。本项最多只能证明前两件。

## 6. 依赖与开工判断
- **LY-005**：从 frozen-candidate 转为冻结，并补上本局部帧墙外的支承基准。
- **LY-006**：改 LY-062:write:003 的标注；拆分 wall-end 端口；说明 LY-063 消费关系的几何依据。这些不挡开工，但影响端口填写。
- **LY-007**：夯土材质与三档预算。
- **LY-008**：交付检查器。
- **LY-010**：本区只作独立演示域。
- **私密源包** luoyang-palace-admission-court-v1.zip 不在本机，但不阻断本项：外围按叠加件从 GLB 重建；原检查器改用 prep 脚本复建的等价检查，并标注「从 GLB 重建」。

## 7. 测量复现
```
B=D:/Blender/blender.exe ; F=D:/GitHub/creation-notebook-lab/docs/library/models/m-luoyang-palace-admission-court/files
$B -b --factory-startup --python-exit-code 1 -P prep/scripts/measure_court.py   -- $F/palace-admission-court-<pose>-LOD<n>.glb prep/out/measure-<pose>-LOD<n>.json
$B -b --factory-startup --python-exit-code 1 -P prep/scripts/gate_line_leaks.py -- $F/palace-admission-court-<pose>-LOD<n>.glb prep/out/gate-leaks-<pose>-LOD<n>.json
$B -b --factory-startup --python-exit-code 1 -P prep/scripts/zone_check.py      -- $F/palace-admission-court-<pose>-LOD<n>.glb ../LY-006/registry/zones.json prep/out/zones-<pose>-LOD<n>.json
```
脚本 SHA256：
- measure_court.py `5bcc8697579aded897253ced27a1032f41e8ca8f632d6b69ebeff7025b2798f2`
- gate_line_leaks.py `73acac512349d430a3c31929d43cb64263642bfd28386ac3c73046efd106a70c`
- zone_check.py `d50f5934eee14c24e741592290bd8efe9ebace33e69ceff928173db3aafd4369`
