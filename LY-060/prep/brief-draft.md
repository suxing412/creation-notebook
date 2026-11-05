# LY-060｜作业设施区局部交付 · 开工准备草稿

阶段：开工准备。G 开工包（LY-001/002/005/006/007/008/009/010）没有冻结，LY-051 到 LY-059 九个前置包都没有交付。**第二轮核对（23:3x）见 §7**：LY-001/002/005/006/007 已标「交付完成」，LY-008、LY-009 没有 status.json，LY-010 目录为空，所以 G 仍未冻结；§3 的演示地坪归属和 §5 第 3、10 条按 §7 修正。本席位没有制作或修改任何交付几何，只读了输入、做了实测、写好了测试。基线是 lab `bce3211f818ee5a8bef1773539da70695ba37b17`（只读），workpacks 是 `09536a8`。

## 1 本项目标（据 TASKPOOL.md:638-645）

- 类型：复用装配。依赖 G 和 LY-051 到 LY-059。
- 产物：按选定用途装一套作业场所包，或者一组写明互斥关系的场所包，并交出外接端口。
- 边界：没有城市准入就只放在独立演示域里。不凭空建工业新区，不拿模型数量去填空地，也不把所有设施塞进一院（LY-059 同样有这条限制）。
- 验收：完整的独立区域包能安装、能撤回；互斥场所不能同时启用；没有地块准入时保持独立，不增加虚构的城市新区。

## 2 现有成果（lab 提交 blob 的 SHA256。GLB 的工作树字节和提交字节一致）

| 家族 | 文件 | SHA256（前 16 位，全值见 inputs.json） | 字节 |
|---|---|---|---|
| 厩棚与饲槽 A/B `m-luoyang-stable` | files/A.glb | 672beeb46faaee0a… | 4,898,748 |
| | files/B.glb | bd82280a76f06778… | 7,043,436 |
| 砖瓦窑 A/B `m-luoyang-tile-kiln` | kiln-A.glb / kiln-A-LOD1.glb | e67d597617c3cdeb… / 562b4b398bb97ea4… | 1,208,676 / 821,880 |
| | kiln-B.glb / kiln-B-LOD1.glb | 4886d95d22383a9b… / 8d9db85bf26e911f… | 1,207,668 / 820,856 |
| 人力石磨 A/B `m-luoyang-hand-mill` | hand-mill-A.glb / -A-LOD1 | 0fe50c2c0604237d… / 5885f619799ef790… | 1,778,876 / 1,605,992 |
| | hand-mill-B.glb / -B-LOD1 | 598cadc7593300bc… / 5ec42d1118def471… | 1,779,100 / 1,605,928 |
| 足碓与踏台 `m-luoyang-foot-pestle` | foot-pestle-LOD0/1/2 | 6f0e41834121fa26… / d8759dd6e0b08803… / e94416ef307479eb… | 655,508 / 248,208 / 79,500 |
| 开敞作业棚与足碓院 `m-luoyang-workyard-shed` | workshed-LOD0/1/2 | 89e0a43923fb3868… / a21c2893a1cc7c7d… / 7c054863f1088ddc… | 721,404 / 262,480 / 19,776 |
| | workyard-LOD0/1/2 | 7eb9739ec09a1ebb… / 6baefbd0fc1bc086… / 574d81d91d3898bf… | 1,850,040 / 713,292 / 167,792 |

- 这五个家族都只有资产卡，都是「待审」，城市节点数为 0。城景代码里一处引用都没有：在 `city-data.mjs`、`app.mjs`、`city-renderer.mjs`、`index.html` 里 grep 卡号和文件名，0 命中；渲染器只装载 `manifest.nodes` 和 `researchModels`（city-renderer.mjs:218、221、601）。`p-luoyang.asset.json:542-568` 只把它们登记为成员，不算落位。
- 体检 `mq/cards/<id>/audit.json` 里记的 SHA 和这 19 个现件逐一相符，issues 都是空的。
- 另外对照过 `m-luoyang-court-layout-kit/compact_work-LOD0.glb`（e799b5880cd12a5c…）。它的外框和 workyard 一样是 18×24.15 m、底面 +0.20，但里面没有足碓，不是谷物院。

## 3 改 / 不改范围

- **改（制作期，只在 `workpacks/LY-060/`）**：assembly.json，写明输入节点到输出节点的映射、变换、端口、高程，以及保留、隐藏、移除清单和互斥规则；独立演示域的承托地坪（只有前置包没提供时才做，并且写明是 C）；qa/、preview/、delivery-manifest.json。
- **不改**：五个家族的原 GLB 和资产卡、LY-051 到 059 的交付件（只引用，不复制改名）、`city-data.mjs`、项目卡、`assets.json`、全站 UI。入城提案只交 LY-100。
- **不做**：不重造厩、窑、磨、碓、院；不用 LOD0 冒充三档；没有 LY-010 准入就不落实名地块。

## 4 证据与未知

| 内容 | 类别 | 依据 |
|---|---|---|
| 厩棚与饲槽形制 | 异地异期类比 + C | 卡片原文：以汉墓陶庄园说明作功能比较，非洛阳马厩复原 |
| 砖瓦窑形制与尺寸 | C | 卡片：非具体遗址或 180 年窑场复原 |
| 石磨 | C（类型启发） | 卡片：地区类型启发的 C 组合，不是文物复制或洛阳确址 |
| 足碓 | C | GLB extras：`C functional interpretation; dimensions and axle mechanism hypothetical` |
| 作业院外框 | C | GLB extras：`C inherited prototype`，role 为 `unchanged perimeter and gate geometry` |
| 作业区在洛阳的位置 | 未知 | LY-010 和 LY-003/004 的准入都没有；城中没有作业节点 |
| 原始考古 / 原文 | 未绑定 | 仓库里没有任何约 180 年洛阳作坊遗址的控制点；本阶段没有做外部检索 |

五件事要分开说：这些模型能读取（已核）；局部通行只有卡片里的有限检查；没有入城；真实结构安全没有认证；历史复原不成立（全是 C）。

## 5 实测缺口（脚本都在本目录，结果是 JSON）

测量命令：`D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P <脚本> -- …`。坐标是 Blender 导入后的 Z-up，换成 glTF 是 (x, z, -y)。

1. **九个前置包都没有交付**：LY-051 到 059 只有 prep/，LY-057 的 prep 是空的。按任务池规定，LY-060 只能装「已放行子包」。
2. **原谷物加工院不在仓库里**：docs 全文 grep「谷物」0 命中，git 历史也 0 命中。workyard 里只有 `pestle_0` 一具足碓，不是「双足碓」原院。
3. **高程基准差 0.200 m**（`measure-out.json`）：workyard 的三档底面都在 z=+0.200，房台面在 +0.420；另外四个家族都以 z=0 为地面（厩台面 0、底 −0.24；窑展示地坪面 0、操作坑 −1.04；磨展示地坪面 0、底 −0.12；碓和棚底面 0）。按原点直接放到同一地面上，workyard 会整体悬空 0.200 m。
4. **workyard 和 workshed 的院地/棚地都没有建模**（`grid-ground-out.json`，0.5 m 网格）：workyard 共 1728 格，其中 1012 格（58.6%）完全没有几何，251 格（14.5%）只有屋顶，加起来 73.3% 的平面下面没有地面；只有 461 格（26.7%）的最低命中在 +0.20。workshed 160 格里 159 格只有屋顶。射线探针（`probe-workyard-out.json`）在院心 (0,0)、(0,−8)、(±2.5,−6) 都没有命中；足碓臼底在 +0.20，四周没有地面。
5. **足碓重复**（`body-extents.json`）：workyard 里的 `workyard_stone`（492 三角面）和 `pestle__pestle_timber_moving`（308 三角面），就是 foot-pestle-LOD0 的 `pestle_stone_static` 和 `pestle_timber_moving` 纯平移 (5.0, −1.5, 0.2) 后的结果（glTF 是 (5.0, 0.2, 1.5)），尺寸完全一样。踏台静件已经并进 `workyard_timber`，拆不出来。所以独立足碓和院内足碓在同一处必须互斥。
6. **展示地坪会占地**：窑 A/B 的 `presentation_ground` 16×19 m = 304 m²，而窑体本身只有 7.9×10.49 = 82.87 m²（A）和 8.3×9.19 = 76.28 m²（B）。磨的展示地坪 2.8×2.8 = 7.84 m²，磨体只有 0.86 m²（A）和 1.12 m²（B）。装配前必须换上 LY-053/055 的接地件，否则展示地坪会互相叠压。
7. **三档不全**：厩 A/B 各只有一档（59,232 / 92,876 三角面，A 的瓦壳就占 58,968）；窑和磨只有 LOD0 和 LOD1，没有 LOD2。磨的 LOD1 还有 1,605,992 B，贴图 1,504,494 B 没有降。
8. **材质有两套命名**：厩、窑、磨用 `REUSED_C_{earth,stone,tile,wood}`；碓、院、棚用 `LY_P01_*__PBR/__FLAT`。要不要合并、怎么合并，等 LY-007 定。
9. **体量**：只取一套组合（厩 B、窑 A、磨 A、workyard）时，LOD0 合计 11,881,028 B；再加独立足碓是 12,536,536 B。合成一个 GLB 会逼近 15,000,000 B 上限，应保持分文件。窑体、厩 B、磨、碓、院的包围盒面积合计约 593 m²，还没算操作净空。
10. **（已被 §7.1 部分更新）准入与契约都没有**：LY-005、006、007、008、010 都还没有可读的冻结件（LY-005 只有草稿，其余目录不存在），原点、高程、端口格式和区域准入现在都定不下来。

## 6 判定

不能复用现成品交差。workyard 是一个已经装好的作业院，可以作为互斥候选场所之一，但它缺地面，基准差 0.200 m，内嵌足碓又和独立件重复，也没有安装/撤回清单和准入，不满足 LY-060 的验收。

## 7 第二轮核对（2026-11-05 23:3x，G 部分交付后）

只读了新交付的 G 件和前置席位的 prep，没有改任何交付几何。新增脚本 `compare_trial_chunk.py`（SHA256 `90e88ca9…`）和 `add_g_inputs.py`（`2d4b78fb…`），新增结果 `trial-chunk-compare.json`（`3855105e…`）；新输入的全值 SHA 见 inputs.json 里 `pass2: true` 的条目。

### 7.1 G 现状
| 席位 | 状态 | 对 LY-060 的影响 |
|---|---|---|
| LY-001 | 交付完成 | 五个作业家族 cityNodes=0，与 §2 一致 |
| LY-002 | 交付完成 | 证据表可用于 T11 |
| LY-005 | 交付完成 | +Y 上；新件按 local-origin，**本地 y=0 = 本件接地面，不是 0 就在端口里写明**；地块地面世界 Y=0.20；E3 容差：高程 2 mm、平面 5 mm |
| LY-006 | 交付完成 | 见 7.2 |
| LY-007 | 交付完成 | `REUSED_C_*` 记为旧调色板现状、新模型禁用；生产族数字标「待复核」 |
| LY-008 | 无 status.json | 检查器 `ly_check.py` 存在但未冻结 |
| LY-009 | 无 status.json | taskboard.v2 把 LY-060 记为「待输入」（S4：缺 008/009/010/051–059）；PZ-10 提示根 taskboard.json 中 LY-060 的 text 串入了下一节导语，以 TASKPOOL 原文为准 |
| LY-010 | 目录为空 | 没有选定样板，也没有区域准入 |

### 7.2 LY-006 registry v1 给 LY-060 的登记（这是新的真实缺口）
- LY-060 是 site `S-WORK` 的 siteOwner，但 `envelope=null`，`local:work-site` 的 `placement=null`，状态写「由 LY-058/LY-060 定义的组合帧；未落位」。
- LY-060 的 `writeZones=[]`、`ownsGroundPieces=[]`、`produces=[]`。也就是说：**§3 里「独立演示域的承托地坪由 LY-060 做」在 registry 里没有登记**，任务池要求的「交外接端口」也没有对应的 produces 端口。LY-060 只 `consumes` 两个端口：`stable:entrance:ground`（LY-052，seams[273]）和 `work-site:service-gate:opening`（LY-059，seams[391]），两者的值都是「生产方交付时填」。
- 地坪归属：厩台 `gp:stable-A/B:*_earth_platform` 归 LY-052；窑、磨的 `presentation_ground` 归 LY-053 / LY-055；院心流线地坪 `W058-flow-ground` 归 LY-058；棚地 `workshed:shed-floor:floor` 归 LY-057。LY-060 不得自做这些地坪，只能引用。
- LY-060 持有五张作业卡（stable、tile-kiln、hand-mill、foot-pestle、workyard-shed）的卡片字段归属，但卡片属公共文件，改动仍只能作语义提案交 LY-100。
- 处理：开工前请协调者/LY-006 给 LY-060 补登（a）一个演示域写入区和外接端口 produces，或（b）明确演示域只由前置包地坪拼成、LY-060 不出几何。没补登前，LY-060 的产物只能是 assembly.json + qa，不能带任何地坪 GLB。

### 7.3 高程「0.200 m 差」的重新定性（修正 §5 第 3 条）
§5 第 3 条的数字不变（workyard 底面 +0.200，其他四族 0）。但按 LY-005，这不是 workyard 的错，而是两套约定：
- workyard 沿用院落框约定：它和城中 courtyard-B（R01-B）、court-layout-kit 共用同一院框（LY-059 prep 实测），本地基底 0.20，用 N.y=0 落位时正好贴在世界 0.20 的地块地面上。
- 另外四族是「本地 y=0 = 接地面」，入城要 N.y=+0.20，演示域则直接放在 0。
- 所以在同一个 `local:work-site` 帧里，必须二选一定一个基准，并且按 E4 不能悄悄改 N 的 Y：要么帧基准取 0.20（四族各加 +0.20，写进 assembly.json），要么取 0（workyard 加 −0.20）。workyard 的基底与 LY-005 的 0.20 已对齐，倾向前者，最终由 LY-005 端口和 LY-010 定。

### 7.4 私有母版里已有一次「作业院入城试放」，但不能拿来用
- lab 已跟踪的 `modeling-lab/review-batches/2026-11-04-city-visible/adapter/adapter.json`（提交 blob 见 inputs.json）里有节点 `visible-current-node-res_workyard_034`，sourceNodeIds 为 `C02-034__workyard_trial__*`，deploymentStatus「not published」，网页城景不读取 modeling-lab/。
- 我只从同目录的分卷 zip 里解出 `chunks/res_workyard_034.glb` 一个成员到 scratchpad（SHA256 `6ed43d99447c…`，1,849,736 B，与 adapter 记录一致），用 `compare_trial_chunk.py` 比对：5/5 网格与 workyard-LOD0 的顶点数、三角数、本地包围盒逐值相同（Δ=0.0），只多了节点平移 (601.8912, 0, −1080.2)，恰好等于 `city-data.mjs:2742` C02-034「住宅院落 34」的矩阵；材质名多了 `.027/.030` 后缀。
- 结论：这是「用 workyard 顶替一处已入城住宅院」的私有试放，不是新的合格成果，也不能当准入：LY-006 把 C02-034 冻结（owner=null，「44 院原矩阵与计数不变」），而且它与 C02-034 的 courtyard-B 互斥。这条写进 T9 的负例。

### 7.5 前置席位 prep 的结论（只读，影响 LY-060 能装什么）
- LY-057、LY-058：`readyAfterG=false`。原谷物加工院及缺陷记录在 lab 全部分支、review 仓、待传目录里都找不到；LY-057 实测 workshed 瓦条 54/54 落座失败（−32.4…+15.2 mm，容差 ±3 mm），正脊 40/41 裸露。
- LY-056：独立足碓与 workyard 内足碓 21/21 构件差 < 1 mm，同位安装就是双载，印证 X4 互斥；碓的 14/14 脚印无支承。
- LY-059：外围墙实测无缺口，C02-034 现址门前高差 0.000 m；服务口、门扇闭态都不存在，要新做。
- LY-051–056、059：`readyAfterG=true`。
- 推论：如果 LY-057 判阻断，LY-058、LY-059（依赖 058）跟着卡住，LY-060 只能交「厩 + 窑 + 磨 + 独立足碓」子集，或在演示域里标「谷物院场所：阻断」。
