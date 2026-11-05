# LY-047｜住宅储藏与棚下安装变体：开工准备稿

状态：**开工准备**。G（LY-001/002/005/006/007/008/009/010）还没冻结，LY-041、LY-043 也没交付。本稿只读输入、实测、准备测试，**没有制作或修改任何交付几何**，也没有写 `workpacks/LY-047/prep/` 以外的地方。基线是 lab `bce3211f818ee5a8bef1773539da70695ba37b17`，数字都在这个基线上测得。

## 1. 本项目标（任务池原文要点）

- 选用已登记的储藏作业院或棚模块，按当前院的空间给一套安装包和操作净空包。
- 不重造棚，也不把所有生活设施塞进同一院。只能用 LY-010 选定的用途组合；没选的保留为候选，不接城。
- 验收：所选储藏或棚模块的支承和取放空间可以验证；未选候选完全不加载；不造成院内功能冲突，也不制造新增建筑数量的假象。

## 2. 「已登记储藏作业院 / 棚模块」实际是什么

我在仓库里核到四类候选。它们的形态不同，处理方式也不同。

| 候选 | 文件 | 城景状态 | 性质 |
|---|---|---|---|
| **B 院原型**「居住兼储藏作业院」 | `assets/r01/R01-B-LOD1/LOD0-prototype.glb`（25f018fa / a8d94bb3） | **已入城 10 院**，全部 `initial:true` | 院内本来就有西侧作业棚（4 柱、2 储物箱、1 台案）和东侧抬高储藏屋（地台 0.65，三级踏步） |
| **B2 院原型** | `assets/c02v/B2-LOD1/LOD0-prototype.glb`（83282373 / d99affca） | **已入城 7 院**，全部 `initial:true` | 同上，作业棚移到院中，2 箱 1 台案 |
| B2 前 C2 功能预设：基准、北、南 | `model-library/updates/m-courtyard-family/files/{baseline,north,south}.glb`（9be87724 / b119cbef / c2db3239） | 不加载 | 整院替换件。棚、箱、台案整体沿 z 移 −0.8 / 0 / +0.8 m，待审 |
| **独立开敞作业棚** workshed | `library/models/m-luoyang-workyard-shed/files/workshed-LOD0/1/2.glb`（89e0a439 / a21c2893 / 7c054863） | 不加载，城景代码零引用 | 6 柱开敞棚。檐口 8.1 × 4.9 m，柱脚在 y=0，**不带任何储物件**。卡片状态「待审」 |
| 北区研究院「储藏作业院」 | `progress-assets/flat/study-north13-court-B-6f7f84af4e7f.glb` 等 | `space: local-study`，`cityPlacement: null` | 研究视图，不能拿来落城 |
| 完整作业院 workyard、紧凑作业院 compact_work | 同卡 workyard-LOD*、court-layout-kit | 不加载 | 是**整院**，装进现有院就等于加院，排除 |

R01 合同（`data/r01/model-contract.json`）里写着：变体 A 是「低层偏门生活院」，变体 B 是「居住兼储藏作业院」。

**关键冲突**：LY-041、LY-043、LY-044 的准备稿都把示范院定为 **C02-010（A2）**。A2 是生活院，院里**没有任何棚或储物件**。所以：

- 如果 LY-010 把示范院定在 B 或 B2 院，储藏和棚下作业本来就在，属于**原位复用**。
- 如果示范院仍是 C02-010（A2），唯一可装的已登记棚模块是 workshed。它不带储物件，装进去就是在该院**新增一座棚**，必须由 LY-010 明确选用，并在 LY-050 里登记为设施变体，不能计成新建筑。

## 3. 核到的现有成果（文件 + SHA256）

完整清单见 `inputs.json`（41 项，含加载代码位置）。下面列主要的：

| 文件（docs/ 下） | SHA256 | 在城景中 |
|---|---|---|
| cities/luoyang/assets/r01/R01-B-LOD1-prototype.glb | 25f018fa8fad0ec62317bd6b5d69e3c948f79b57df125bc91d9893c8db0c3de6 | 加载，city-data.mjs:36 `courtyard-B.path`；排除 site_lot、site_neutral_lane、designed_loading_yard（:39–43） |
| cities/luoyang/assets/r01/R01-B-LOD0-prototype.glb | a8d94bb3897825c6682a9fa9a0fafb310b9a8ac6bbf77c66e5bdf5e81499eeed | 只在 focusCourtyard 时加载近档，city-data.mjs:56，city-renderer.mjs:416 |
| cities/luoyang/assets/c02v/B2-LOD1-prototype.glb | 8328237369a33571421b2ef9b4f2e2df4761f070db2556c9cd6eff326fdfa3db | 加载，city-data.mjs:116 |
| cities/luoyang/assets/c02v/B2-LOD0-prototype.glb | d99affcae95cfe2265e5ed36906a219305e387554c44a5ca9c84552453e791f7 | 近档，city-data.mjs:136 |
| cities/luoyang/assets/c02v/A2-LOD1 / LOD0-prototype.glb | 277e9e73… / 19b05202… | C02-010 所用原型（city-data.mjs:2322） |
| library/models/m-luoyang-workyard-shed/files/workshed-LOD0.glb | 89e0a43923fb3868452903186b07299162fdf208a667c0d82630791b554ce726 | 不加载 |
| library/models/m-luoyang-workyard-shed/files/workshed-LOD1.glb | a21c2893a1cc7c7d8b69bb7c61b5d85f65f17fc352d003ff67ed9da4ea502671 | 不加载 |
| library/models/m-luoyang-workyard-shed/files/workshed-LOD2.glb | 7c054863f1088ddc8709592dfbfe70e2a581dc8ef91d4741c02aa65a0d0a614e | 不加载 |
| cities/luoyang/assets/ground-atomic/{south,retained,network-ground-stitched,D08}.glb | 4313826d… / aed8b3d4… / fdfc3ce5… / 3ab93310… | 四个地面节点都是 `initial:false`，只在 terrain 章加载（city-data.mjs:3555–3645） |
| cities/luoyang/city-data.mjs | 工作树 e4115705…，HEAD 提交版 c849706b… | — |
| cities/luoyang/city-renderer.mjs | 工作树 fa0a8dcb…，HEAD 提交版 04c6c643… | — |

**SHA 注意**：这台 Windows 机器上 `core.autocrlf=true`，文本文件在工作树里是 CRLF，SHA 和 HEAD 里的 LF 版本不同。GLB 没有这个问题。`inputs.json` 给文本文件同时记了两种 SHA（`sha256` 和 `headBlobSha256`）。city-data.mjs 自己记录的 provenance SHA（例如 instances-calt 的 c830b4e3）和工作树 CRLF 版一致，和提交版 e39fdafb 不一致。正式验收前要由 LY-008 统一用哪一种。

## 4. 改 / 不改范围

- **改**：本席位只写 `workpacks/LY-047/`。
  - 路线 R（示范院是 B/B2）：不新造几何。交付选定院 ID、矩阵、棚和储藏屋子件清单、净空包和检查器。
  - 路线 W（示范院是 A2 C02-010，且 010 选了棚下用途）：交 workshed 原件引用（不复制），外加一份放置变换（含 **y +0.200**）、互斥规则和净空包。储物件要不要加由 010 定；如果要加，只能从 B 院 GLB 里切出现有的箱和台案（「从 GLB 重建」，必须标明），不能新设计箱型。
- **不改**：17 个 B/B2 院的矩阵和原型节点；A2 原型；四个地面文件；city-data.mjs、p-luoyang.asset.json、lab/data/*；13 院片区；workshed 原件；B2 三预设；邻院 C02-009（B）和 C02-011。

## 5. 证据与未知

| 内容 | 分类 | 依据 |
|---|---|---|
| B 院的总体院落关系 | 异地同期类比 | R01 合同写着：参照河南东汉张茂院落明器，「not Luoyang city residential foundation」 |
| B 院的布局、作业台、储物箱 | C 工程设计 | 合同原话「design conjecture, not period furniture evidence」 |
| 储藏屋地台抬高 0.45 m、三级 0.15 m 踏步、门洞 1.66 × 2.24 m | C | 仓库里没有出处，按 C 处理 |
| workshed 的棚形、尺寸和用途 | C | 卡片原话：「棚形、场所用途及全部尺寸为C」 |
| 本稿的人体包络（r 0.30 / 0.45 m、头顶 1.90 m、取放距离 0.70 m、操作带 0.90 m） | C 工程设计 | 本席位选的检查参数，不是规范，也不是史证 |
| 约 180 年洛阳普通住户的储藏方式、棚的有无和位置 | **未知** | 本席位没有查外部资料，留给 LY-002 证据表 |

不能拿北魏洛阳、西汉长安或四川画像砖的仓、棚形制来补。这里说的「支承可验证、取放可达」只是几何检查，不等于真实结构安全，也不等于历史复原成立。

## 6. 实测到的真实缺口（脚本都在本目录，可重跑）

脚本：`measure_ly047.py`（主测量，de2adbd1），`selftest_ly047.py`（负例，47eb6399），`blender_crosscheck.py`（Blender 5.2.1 自带导入器复核，078a16d8），`plot_ly047.py`（平面图），`make_inputs.py`。结果分别在 `measure-ly047.json`、`selftest-ly047.json`（allBehaved=true）、`blender-crosscheck.json` 和 `preview/plan-*.png`（Pillow 栅格图，不是 GPU 或浏览器渲染）。

方法：0.05 m 栅格。身体带取地面以上 0.25–1.90 m，0.22 m 以内的台阶和柱础按可踏处理。用圆盘膨胀加连通域，从院门向内求可达；支承用竖直射线对城景地面三角求高差。**这不是实体碰撞穷尽，也不是连续人体运动检查。**

### 6.1 原位棚和储藏（B、B2）

- **棚不是独立节点**。B LOD0 的棚由 4 柱、4 柱础、2 梁、2 储物箱、台面和 4 腿，加上 1,844 个屋面三角组成，共 2,072 三角。它们全部并在全院共用的 `architecture_C_plain_timber`（540）、`floor_plinth`（132）和 `roof`（7,896）里。B2 LOD0 是 1,688 三角。所以要单独卸载或替换这个棚，必须改原型节点。按本项边界，这不归 LY-047 做。
- **支承**：棚和储藏件落地的底部顶点，B 有 40 个，B2 有 40 个，都在 y=0.200。4 根柱都坐在柱础上，间隙 0.0。没有任何底点落在被剔除的 designed_loading_yard（顶 0.215）上，所以剔除它不影响棚的支承。
- **城景 17 院逐院实测**（地面打开时）：每院 36–40 个底点，无地面 0、悬空大于 5 mm 0、埋入 0，间隙在 −3e−9 到 0 m 之间。承托来源：ground-retained 9 院（C02-002、004、018、022、025、029、033、034、036），ground-south 5 院（C02-005、006、009、016、032），ground-D08 3 院（FROZEN-D08-S2、S4、E），共 17 院。
- **默认视图没有地面**：四个地面节点都是 `initial:false`。默认视图和近景下，17 院的棚和储物箱下面都是空的。这是加载配置问题（LY-041 也测到了），要 LY-100 解决，不能靠补底板。
- **净空**：梁底离地 2.15 m，棚内屋面最低处离地 2.45 m。储物箱（高 0.54 m）上方净空 1.91 m，台案（面高 0.78 m）上方 1.67 m。LOD0 和 LOD1 一致。
- **取放可达**：从院门出发，r 0.30 的身体中心可以走到每个箱子和台案四个面的 0.325–0.375 m 以内，在 0.70 m 取放距离之内。r 0.45（搬着 0.6 m 的东西）时：
  - B 两个箱子各有 3 个面可达。朝台案那一面（+z/−z）要绕 4.1 m，因为箱子和台案只隔 0.5 m。
  - B2 两个箱子朝台案的那一面（间距 0.5 m）同样不能带货到达。
  - 0.9 m 操作带里有遮挡的格数：B 箱朝台案一侧 48 格（约 0.12 m²），B2 箱朝台案一侧 40–45 格。
  - 这是现有布局本来的状况，不算缺口，但必须写进使用限制：带货只能从外侧三面取放。
- **储藏屋**（B 和 B2 东屋）：
  - 地台顶 0.65，比院面高 0.45 m。三级踏步，每级高 0.15、深 0.36，宽 2.0 m，踏步底落在 0.200。
  - 门洞净宽 1.66 m，净高 2.24 m。门扇处于开启状态，向屋内转入约 1.05 m。
  - 屋内可达面积：B 为 18.76 m²（r 0.30）或 15.52 m²（r 0.45），地台 32.4 m²。B2 为 14.44 或 11.75 m²，地台 25.92 m²。屋内净高 3.6 m。和院子连通。
  - 抬高 0.45 m 的地台对搬运是一处限制。踏步对人体有效，对车辆没有做检查。
- **B2 北、南预设**：棚整体沿 z 移 ∓0.8 m。可达和净空数字和基准相同（可达面积 309.84 / 282.92 m²）。它们是整院替换件，和城景里的 B2 不能叠载。

### 6.2 workshed 装进 C02-010（A2）的可行性

- workshed 柱脚在 y=0.0，城景地面和院面在 0.200。**必须平移 y +0.200**，否则 6 根柱全部埋入 0.2 m。自检 N1 已经验证会检出。
- workshed 檐口 8.1 × 4.9 m（约 39.7 m²）；系梁底 2.62 m，减去 0.2 后离地 2.42 m。三档外包相同；LOD2 屋脊低 0.10 m。
- 测试方法：在 A2 院内按 0.5 m 步长、0°/90° 两个朝向，试了 3,626 个放置位。条件：
  1. 檐口矩形在任何高度都不碰现有构件；
  2. 加上 6 根柱后，r 0.45 的人从院门仍能走到两座屋的门前；
  3. 棚下面至少一半面积可以走到。
- 结果：**可行 409 个**（0°：198 个，90°：211 个）。在 A2 LOD1 上复核，409 个全部仍然可行。不可行的原因：2,148 个出了院界，1,068 个檐口碰到现有构件，1 个切断了屋门路线。
- 409 个可行位的 2,454 个柱脚点，城景地面全部是 ground-south，平移 +0.2 后间隙 −3e−9 m。
- 和 LY-044 灶台试放点（局部 2.0、3.45）保持 1.5 m 以外的，只剩 **65 个**。参考放置位：0°，原点 (−4.5, 7.5)，檐口在局部 x −8.55…−0.45、z 3.05…7.95，换成世界坐标是 x 522.45…530.55、z −815.40…−810.50。自检 P1 通过。
- A2 院里任何高度都空着的面积是 303.95 m²。一座 39.7 m² 的棚大约占掉 13%。LY-044 灶台、LY-045 圈厕、LY-048 服务口也要用这块院子，归属必须由 LY-006 冻结，否则就会出现「所有设施塞进一院」。

### 6.3 「未选候选不加载」的现状

- workshed、B2 三预设、C2 修订件：城景代码（docs/cities/luoyang 下的 *.mjs 和 data）里**零引用**。workshed 只出现在 p-luoyang.asset.json 的 related 里。
- 北区 B/B2 研究院：`researchModels`，`initial:false`，`cityPlacement:null`（city-data.mjs:4233、4260）。
- 已入城的 17 座 B/B2 院自带棚和储藏。它们是保护清单里的现有 44 院，不能因为「未选」就卸掉。所以「未选候选不加载」只能用在示范院新加的候选上。

## 7. 待依赖与风险（简）

- LY-010：示范院是哪一院，以及有没有选储藏或棚下用途。不定，路线 R 和路线 W 就选不了。
- LY-041：选院和地坪基准（0.200 还是 0.215）。LY-043：A2 有没有墙房端接改动，会不会影响檐口净空。
- LY-006：A2 院面的格子归谁（灶、厕、棚、服务口）。
- LY-005：高程契约。y +0.200 的依据要来自它，不能是本席位自定。
- 私密源包：B/B2 原生 .blend 不在仓库。只有 010 要求「可单独卸载的 B 棚」时才需要它；箱体可以从 GLB 重建，屋面切片的作者意图重建不出来。
