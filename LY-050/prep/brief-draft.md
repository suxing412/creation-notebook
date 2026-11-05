# LY-050 示范院完整生活组装：开工准备简报（草稿）

阶段：开工准备。G 包（001/002/005/006/007/008/009/010）还没全部冻结，041–049 也只有 prep，没有交付。本目录只放读数、测量脚本和测试计划，**没有制作或修改任何交付几何**。
lab 基线：`bce3211f818ee5a8bef1773539da70695ba37b17`，只读。工作树 `git status` 只有 `?? .claude/`，`lab/data/assets.json` 工作副本等于 HEAD blob `3a70eca9`。

## 1. 本项目标

在现有 44 院中选一院（LY-041、LY-006 registry v1 的候选都是 **C02-010**，资产 courtyard-A2，app 里是「第 24 院」），把 041–049 交付的差异件和复用设施组装成一处完整的近景院落，并交出三样清单：来源清单、矩阵清单、互斥清单。设施组要能关闭，一次只加载所选用途。安装和撤回都要可复现，撤回后城市指纹必须与基线一致。

不做：不增加院数，不升级成全城住宅范式，不改共享文件（city-data.mjs、p-luoyang.asset.json、app.mjs、renderer 都由 LY-100 合并），不新造任何建筑或设施几何。

## 2. 核到的现有成果（SHA256 前 8 位；全长见 inputs.json）

| 输入 | SHA256 | 城景是否加载 |
|---|---|---|
| docs/cities/luoyang/city-data.mjs | e4115705 | 是（app.mjs:1） |
| docs/cities/luoyang/city-renderer.mjs | fa0a8dcb | 是（app.mjs:177） |
| docs/cities/luoyang/app.mjs | 4d6b5b33 | 是（index.html:115） |
| assets/c02v/A2-LOD1-prototype.glb（远档） | 277e9e73 | 是，首屏；9 个节点共用 |
| assets/c02v/A2-LOD0-prototype.glb（近档） | 19b05202 | 只在 focusCourtyard('C02-010') 时加载（renderer:416） |
| assets/ground-atomic/south.glb | 4313826d | 只在打开 terrain 章后加载（initial:false） |
| data/c02v/layout.json（C02-010 院内路线） | 7528f0c8 | 当前入口不读，只有 v1 存档读 |
| 灶 stove-A / stove-B LOD0 | 88e6f590 / 3bde10b5 | 否（待审） |
| 圈厕 service-A LOD0 | cc02f68f | 否（待审） |
| 低墙生活分区 service-enclosure LOD0 | 507c6e70 | 否（待审） |
| 作业棚 workshed LOD0 | 89e0a439 | 否（待审） |
| 内门 paired-door / single-door LOD0 | 67bc127a / 597d81ad | 否（未入城） |
| W2 备食放置层 LOD0 | b7aa02d1 | 否；属于 13 院布局 |
| 13 院生活片区 life-block LOD0 | 27099872 | 否；受保护，不能动 |

现有的「完整生活组装」只有 13 院生活片区（life-block）。它是另行处理的受保护片区，不在 44 院之内，也没有入城。按 LY-044 的实测，W2 的 87 个底点里有 0 个下面有城景地面。所以它**不能当作本项的复用成果**。44 院里没有任何一院装了灶、厕或储藏设施：城景的 *.mjs 和 data/*.json 里对这些设施的引用数是 0。

## 3. 改 / 不改范围

- **改（只交 overlay 和合并提案，不写共享文件）**：C02-010 一院的设施节点组、它们的世界矩阵、互斥组、开关规则，以及地面同载规则。
- **不改**：A2 两档 GLB（9 院共用：C02-001/010/013/015/021/024/028/031/035，改了就会波及另外 8 院）、其他 43 院的记录和矩阵、ground-south 的字节（LY-045 的切孔若要撤回，必须原样恢复）、13 院片区、W2 放置层。
- **所有权**（LY-006 registry v1）：LY-050 是 S-COURT 场地负责人，拥有城景节点 C02-010 和 6 张卡；writeZones 为空，不直接拥有地坪片或源对象。消费 3 个端口：gate-boundary:road-end（LY-049 产出）、drip-outlet:drain（LY-046 产出）、service-opening:opening（LY-048 产出）。

## 4. 证据与未知

- 住宅本身：LY-002 E-H01 定为「未知＋类比」，本轮没有约 180 年洛阳城内住宅的发掘平面。禁用条目：X07（北魏里坊）、X12（明器等比放大、绿釉当真色）、X24（三杨庄乡村院落当模板）。
- 44 院形态与落位：C 工程设计（city-data.mjs basis 字段：「住宅形态与落位为设计研究」）。
- 灶、圈厕、低墙分区、作业棚、内门：卡片都写明尺寸和形体是 C 选择。圈厕参考的是跨地域明器类型，属于异地异期类比。都不认证燃烧、卫生、结构、连续人体、GPU。
- 院内用途组合（一院同时有哪些设施）：未知。由 LY-010 选定；未选的设施只能留作候选，不接城。
- 五件事分开记：模型能读取（已核，GLB 都能解析）；局部通行（只做了栅格走廊检查，不是连续人体）；已入城（否）；真实结构安全（不评估）；历史复原成立（否，C 加类比）。

## 5. 实测缺口（脚本：measure_ly050.py、probe_routes.py、fingerprint.py；结果在 out/）

栅格 0.05 m，坐标用 court:C02-010（世界坐标减去 (531, 0, -818.45)，yaw 0）。

1. **前置都没交付**：G 中 001/002/005/006/007 状态是「交付完成」；008 没有 status.json；009 没有 status 和 qa；010 连目录都没有。041–049 只有 prep，models/ 和 assembly.json 都还没有。本项现在无料可装。
2. **城景没有「可关闭设施组」机制**：renderer 只能按章节累加 loadNodeIds（:595），近档只给被聚焦的那一个节点（:416）。`replaces` 机制在（:412），但 0 个节点在用。所以如果设施做成单独节点：
   - 聚焦 C02-010 时设施仍是远档；
   - 设施节点一旦带上 `chapter:'residential'`，app.mjs:78 就会把它算成院落，「第 N 院」的编号会错位，44 这个数也会变（app.mjs:25/:297 写死「44 座」）。
   - 开关和互斥只能由 LY-100 选方案：给 C02-010 单独做一个资产记录（A2 共用数从 9 降到 8），或者新增一种不进 residential 章、不计入院数的设施节点类型。
3. **默认视图下院子没有地面**：4 个地面节点全是 initial:false。打开 terrain 章后，ground-south 覆盖 C02-010 地块 172,800/172,800 格，顶面 y 全部是 0.200。不打开时，院坪和设施底下都是空的。这一条和 LY-041 的结论一致，属于加载配置问题，要靠 LY-100 合并时让地面同进同出。
4. **宿主占地**（LOD0 和 LOD1 完全相同：实体投影一致，屋面覆盖相差 0 格）：实体 93.23 m²（墙 41.9、台基 62.28、木作 2.265），开敞 338.77 m²，其中有屋面遮盖的 30.24 m²，开敞处屋面底面最低 2.65 m。台基顶 0.42 m，比院坪高 0.22 m。
5. **院内路线**（layout 的两条路线换算到 GLB 坐标，半宽 0.4 m）：gate_to_main 和 yard_to_side 在身体带 0.25–2.0 m 内都没有阻挡（0 m²）。进屋处是 0.22 m 的台基阶（1.1 m² 和 1.06 m²）。门楣和侧屋檐下有 2.0 m 以上的头顶构件（0.72 m² 和 0.24 m²）。这只是栅格走廊检查，不是连续人体检查。
6. **路线与他席写入区相交**：
   - yard_to_side 穿过 LY-046 滴水试片区：半宽 0.4 m 时 0.64 m²，0.6 m 时 0.96 m²。浅沟落在路线上，必须证明足下有支承。
   - gate_to_main 在半宽 0.6 m 时擦到 LY-045 圈厕区 0.18 m²。
   - gate_to_main 和 LY-049 门道区相交 2.4 m²、和 LY-042 门带相交 0.96 m²。这两处本来就是交接段。
7. **LY-047 写入区放不下任何候选**（registry v1 的 box 是 x 4.1..8.0、z -11..-4）：
   - 区内西侧 0.7 m（x 4.125–4.775、z -9.675..-4.925）是正屋东山墙（y 0.42–3.22，1.68 m²）和台基（3.36 m²），整列都空的只有 x 4.8–8.0，宽 3.20 m。
   - 低墙生活分区 3.7×3.25 m：两个朝向都是 0 个可放位，差 0.05 m。
   - 作业棚 8.1×4.9 m：0 个可放位。
   - 写入区东界停在 8.0，院墙内皮在 8.65。如果放宽到 8.65，宽度有 3.85 m，分区放得下。院内别处（避开路线）分区有 31,354 和 34,471 个可放位。
   - 结论：要 LY-006 出 registry v2，或者 LY-047 另选模块。
8. **LY-045 圈厕只在 yaw 0 放得下**：6.749×7.562 m，0.05 m 网格上只有 4 个可放位，余量 x 0.15 m、z 0.04 m；yaw 90 是 0 个。
9. **LY-044 灶区宽裕**：stove-A 有 2,904 / 3,640 个可放位（两个朝向），stove-B 有 2,064 / 3,024 个。
10. **设施区合计**：044、045、047 三个区占开敞地 95.1 m²，是开敞面积的 28.07%。一次只加载所选用途，就是为了不把设施全塞进一院。
11. **预算**：A2 LOD0 保留节点 6,532 三角；5 个设施候选合计 20,748 三角，其中灶 A/B 二选一、分区和棚二选一，所以这是上限。字节合计 5,685,460，低于 15,000,000。设施 GLB 每个带 0.6–1.0 MB 的 PNG 贴图，但城景只用 position/normal 和按材质名取的颜色（renderer:147-161、:322-333），贴图会被下载然后丢掉。A2 本身没有贴图。
12. **邻院**：C02-009 和 C02-011 在 x 方向距 5.0 m，C02-005 和 C02-006 在 z 方向距 11.6 m 和 12.6 m。S-COURT 包络（世界 x 522–540、y -1.6–5.6、z -830.45..-806.45）只和 3 个地面节点相交，不碰任何邻院。
13. **基线指纹**：66 节点、42 资产、7 章、44 院、首屏 59 节点；fingerprint total = `50486e228fc5749c9a2087300eff4ff119c9ebc66ab87ecd265551e9c0502ef0`（out/fingerprint-bce3211.json）。C02-010 记录 SHA 是 `cc440aaf…`，courtyard-A2 资产记录 SHA 是 `d71edda1…`。自检 5 个负例都被检出：C02-010 平移 1 mm、邻院平移 1 mm、多一个节点、院数加 1、excludeNodes 改动。只调换键序的正例差异为 0。
14. **原生源缺失**：A2 原型、灶、圈厕、分区、作业棚的 .blend 和源 ZIP 都不在仓库。本项只做节点级组合，可以「从 GLB 重建」，不需要原件，也不得冒称找回原件。

## 6. 复用判定

无。没有现成的合格成果：44 院里没有装好的生活设施，13 院生活片区受保护而且不在 44 院内。本项本来就是「复用装配」：设施 GLB 原样引用，不新造几何。

## 7. 重跑

```
node dump_city.mjs D:/GitHub/creation-notebook-lab/docs/cities/luoyang/city-data.mjs out/city-dump.json
python -I measure_ly050.py D:/GitHub/creation-notebook-lab out/city-dump.json D:/GitHub/creation-notebook-workpacks/LY-006/registry/zones.json out/measure-ly050.json
python -I probe_routes.py D:/GitHub/creation-notebook-lab out/probe-routes.json
python -I fingerprint.py make out/city-dump.json D:/GitHub/creation-notebook-lab/docs/cities/luoyang out/fingerprint-bce3211.json
python -I fingerprint.py selftest out/city-dump.json D:/GitHub/creation-notebook-lab/docs/cities/luoyang
```
