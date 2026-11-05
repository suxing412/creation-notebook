# LY-018 谷门门墩接地与墙端适配 · 开工准备稿（未制作）

状态：**待输入**（G 包 LY-001/002/005/006/007/008/009/010 未冻结）。本稿只读输入、实测缺口、写测试；没有制作或修改任何交付几何。
读取基线：`D:/GitHub/creation-notebook-lab` main `bce3211f818ee5a8bef1773539da70695ba37b17`。工作树里 `lab/data/assets.json`、`glb-cache.json`、`report.json` 有本地未提交改动（1 行），本稿的文本 SHA 一律取 HEAD blob（LF）；`core.autocrlf=true`，工作树 CRLF 版本 SHA 另记在 inputs.json。

## 1. 本项目标（照任务池原文）

基于已做的 G-v1 和隐藏试放，补底部支承、门槛地坪和必要的接墙差异件；复用能用的原接口，不复制夏门；工程原点和 B 示意点分开记录，不移动考据点去迎合墙端。验收：以当前墙端（不是旧截图）为输入；底投影支持、门道端点、接面残差、隐藏/撤回测试都能重现；源 G 门不能被换成别的门。

## 2. 核到的现有成果

| 成果 | 路径 | SHA256 | 是否入城 |
|---|---|---|---|
| G-v1 LOD1（中景） | docs/library/models/m-luoyang-gu-gate/files/gu-G-LOD1.glb | 5195ce552b76fc60240248d671812fa9e1912e2be327a061cd52524f65a42432 | 否，仅资产卡 |
| G-v1 LOD2（远景） | …/files/gu-G-LOD2.glb | 945b3346ab16676dc62cc78aca69b5eef665758607686badea79065193587f6e | 否 |
| G-v1 LOD0 | 不在仓库（卡片说 13,213,712 字节，未上架） | 未知 | — |
| 资产卡 | …/m-luoyang-gu-gate.asset.json | HEAD e192ac647b774d66a27bf6a24249de679f2c014f82cd2882ea1010d28a036d28 | 状态「待审，未入城」 |
| 母版里的谷门试放（带接墙帽和底板） | city-visible 公开包 chunks/city_gate_gu-G.glb（由 modeling-lab/review-batches/2026-11-04-city-visible/*.zip.part01-05 拼接解出，拼接后 ZIP 5895ef23a684a343271183dce1e92e112fb49bba9e03e4372023d1247bb50b69） | 97c4837931dbc99d02a525b7f60e79d0557713ecef153d8e16aa844361f6cfce | 否；adapter.json 里 initial=false，renderer 也没有接入 |
| 当前墙端 A（城景默认加载） | docs/cities/luoyang/assets/city-wall/A/wall-00.glb、wall-01.glb | 12d84a0b…abc74 / cfbbc45a…3a95 | **是**：city-data.mjs 资产 171/191 行，节点 3204/3231 行，`initial:true`，章节 walls 3778–3779 行 |
| 当前墙端 B（v1 互斥样本） | …/city-wall/B/wall-00.glb、wall-01.glb | 16a29621…2127 / 91eefa47…c14569 | 只在 v1/wall-layer.mjs 选 B 时加载 |
| 母版墙 C_wall_A_00/01 | city-visible chunks/city_wall_C_profiles.glb | e42d9f50…1278 | 否；实测和网站 A 墙**逐顶点一致**（最大偏差 0.0 m） |

母版来源：city-C032-entry-LOD0.blend（SHA 1e8c4d2c…b01b，私密，不在仓库）。visibility.json 显示 gu-G 三个节点在母版里 render 和 viewport 都可见。所以「隐藏试放」指的是网站没有加载，不是母版里隐藏。

## 3. 实测（脚本见 scripts/，结果见 measure-gu.json、measure-gu-2.json、lib-floor.json）

坐标：glTF Y 向上，X 向东，Z 向南为正（z = −north）。门局部系就是 LOD1 的帧：X 沿墙，Z（Blender 里是 y）穿门，Y 向上。

**工程原点与 B 点（分开记录，B 点不动）**
- 母版试放矩阵：平移 (1693.2231, 0.17, −3894.5303)，绕竖轴偏航 −10.8136°，缩放 1；三个节点矩阵相同。
- 这个平移和 city-wall-constraints 的 C 投影点 (1693.223055, 3894.530178) 相差 ≤0.0001 m，偏航和 B 城垣第 2 段方向（−10.8139°）相差 0.0003°。
- B 示意点 gate_gu_B (1693.878, 3897.959)。原点减 B 点为 (−0.6549, −3.4287)，距离 **3.4907 m**。这是示意单位，不是测绘误差。

**母版 earth 和资产卡 LOD1 不是同一个网格**
- timber 和 tile：母版与 LOD1 顶点一一对应，最大偏差 0.00038 m。
- earth：母版 276 顶点、140 三角；LOD1/LOD2 都是 204 顶点、104 三角。母版多出 16 个面，分两类：
  1. 两端接墙帽：x∈[±11, ±16]，底宽 ±4.0，顶宽 ±2.8，高 6.03（世界 0.17→6.20），和 A 墙断面相同。
  2. 一整块底板：32 × 12 × 0.17 m，局部 y −0.17→0，世界 y 0.00→0.17，体积 **65.28 m³**。
- 所以资产卡 LOD1/LOD2 按母版矩阵放进去时，墙端两侧各有 **5.0 m** 空缺（earth/timber 到 ±11），屋瓦处是 **4.0 m**（到 ±12）。门道里也没有地面：15 个下射点全部没有命中（lib-floor.json）。

**墙端接面（当前 A 墙）**
- A/wall-00 端面在局部 x = −15.99994，A/wall-01 在 +15.99988。端面垂直于门 X 轴，歪斜 ≤0.0009°。
- 端面梯形：底 ±4.000，顶 ±2.800，高 6.03，和接墙帽相差 ≤0.0003 m，**没有外露墙端面**（0.0 m²）。
- 分离平面检查：墙顶点和门 earth 顶点沿 x 的最大重叠深度是 0.00012–0.00018 m。这是共面接触加浮点误差，没有正体积侵入。3 向射线奇偶采样（0.1 m 网格）在接触面附近给出 0.003–0.017 m³，判定为共面采样误差，不算侵入。
- 母版 earth 有 10 条边被超过 2 个面共用（LOD1 是 2 条），位于帽、底板和墩的接缝。闭合（open edge）为 0。

**墙端接面（B 样本，互斥）**
- B 墙端面底 ±5.0，顶 ±3.25，高 7.83。比 A 帽每侧宽 1.0 m（底）、0.45 m（顶），高出 1.80 m。每端约 **23.59 m²** 墙端面没有帽承接。选 B 时现在的帽不够用。

**门道**
- 三条门道：墩间距 3.2 / 5.2 / 3.2 m。0.3–3.5 m 高度的净宽是 **2.5 / 4.5 / 2.5 m**，0.05 m 高处是 2.75 / 4.75 / 2.75 m（两侧木框和静止开着的门扇各占约 0.35 m）。
- 顶下净高：穿门方向 0 和 +3 处是 5.20 m，−3 处是 4.92 m。
- 门道中心线端点（外端 = 北 = 城外），示意坐标 (east, north)：
  - 西：内 (1685.418, 3889.913)，外 (1687.670, 3901.700)
  - 中：内 (1692.097, 3888.637)，外 (1694.349, 3900.424)
  - 东：内 (1698.777, 3887.361)，外 (1701.028, 3899.148)
- 母版里门道地面是底板顶面，世界 y 0.17，和墙基同高。底板在穿门 ±6 m 处结束，结束处向下 0.17 m 到世界 y 0，外面什么也没有。

**底投影支持**
- 门全部覆盖面（32 × 12 m，0.5 m 网格 1536 点）向上第一次命中都在局部 −0.17，也就是底板底面。
- 城景在谷门附近 60 m 内**没有任何地面网格**。v1 的 sector 地板只在原点 ±92 m 内；母版 C_gate_local_ground 只有雍、平城、开阳三片。所以相对城景地面的支持率是 **0/1536 = 0%**。唯一的参照是隐含的墙基基准 y = 0.17，而底板比它低 0.17 m。
- 路网：road_east_north_link_B 在 road-preconstraints 里是 hold_palace_interface，「新东墙未配准」。门外和门内都没有可接的路端。

## 4. 改 / 不改范围（草案，待 LY-006 冻结端口和所有权）

**不改**：gu-G-static_timber/tile/earth 三个原节点（几何、材质、矩阵）；B 点 gate_gu_B；A/B 墙 wall-00/01（端面已按 ±16 切好，只读作接触面）；C_gate_local_ground.glb 里另外三门的地片；夏门（LY-019）；city-data.mjs 和项目卡（只交给 LY-100）。

**拟改（只做差异件，原件留存）**
1. 接墙帽三档。从公开 GLB 重建：几何直接取母版 earth 多出来的帽面，做成独立节点（例如 gu-G-wallcap-A-minus/plus），覆盖 LOD1/LOD2，和墙 A 共面接触，不和墙叠出体积。
2. 门槛底板：决定是保留母版 0.17 m 底板，还是改成和墙基齐平。底板底面 y=0 与墙基 0.17 的关系，要等 LY-005 的高程契约。
3. 门内外最小承托地片：只到门道端点外一个身体包络，不铺路。和 LY-089 地形差异片、LY-085 接路线划清边界，路线归 LY-085 或后续任务。
4. （可选）B 样本帽：只在 LY-010 准入 B 时做，否则写成 B 下的已知缺口。

## 5. 证据与未知

| 内容 | 类别 |
|---|---|
| 谷门名、相对方位、B 示意点（gao2023 图1 描点） | 原文/图版的二次示意（B 类），不是发掘坐标 |
| 三道门、门墩宽、32 m 断口、帽、底板、A/B 墙高宽 | C 工程设计 |
| 门叶状态、楼层、登临、材质色彩 | C 设计或未知 |
| 约 180 年谷门实际门宽、门道数、门槛形制、门外地面高程、门前道路 | 未知 |
| 异地异期类比 | 本项不使用；北魏洛阳、西汉长安、四川画像砖都不作谷门尺寸依据 |

没有新做网络查证，也没有声称看过发掘原图。

五件事分开说：
- 模型能读取：LOD1、LOD2、母版 chunk 都能导入。
- 局部通行通过：没测，因为没有地面。
- 已入城：没有。
- 真实结构安全：不评估。
- 历史复原成立：不成立，属 C 推测。

## 6. 缺的输入

- G-v1 源包（.blend 或源 ZIP，含 LOD0 13,213,712 字节和原生隐藏试放 delta JSON）。用途：拿到原生 earth 帽与底板参数、LOD0 档帽件，以及 delta 的 SHA 和撤回清单。能否从 GLB 重建：帽和底板都是简单梯形柱和长方体，可以从公开 chunk 的 72 个顶点精确重建，但 LOD0 档只能「从 GLB 重建」，不能冒称找回原件。
- city-C032-entry-LOD0.blend（SHA 1e8c4d2c…）。私密母版。用途：核对母版里有没有别的谷门相关隐藏节点（2505 个隐藏 placement）。能否从 GLB 重建：不能，只能用公开 visibility.json 的名单代替。
- city-wall-interface.json 引用的 qa/gate-projections.json，仓库里没有。可以用 city-wall-constraints.json 的 gate_projection_diagnostics 代替。
- G 包：LY-005 高程契约（墙基 0.17 和地面基准）、LY-006 端口 ID 和所有权、LY-007 三档基线、LY-008 检查器、LY-010 准入（A 还是 B，是否允许局部地片）。

## 7. 测量脚本

- scripts/measure_gu.py（bc38674d…a296）：原点和偏航、母版与 LOD1 对比、墙端、门道、底面
- scripts/measure_gu_2.py（faf91cb8…8cb2）：开放边、3 向奇偶、端面梯形、分离平面、LOD 空缺
- scripts/lib_floor_check.py（7b7566e6…e5）：LOD1/LOD2 门道有没有地面

运行：`D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P <脚本> -- <out.json> D:/GitHub/creation-notebook-lab D:/GitHub/creation-notebook-workpacks/LY-018/prep/work/city-visible`（lib_floor_check 的参数是 out 和两个 GLB）。
work/city-visible/ 是从仓库 ZIP 解出的只读副本，只用于测量，不是交付件。
