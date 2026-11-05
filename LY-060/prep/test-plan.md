# LY-060 测试计划（按「本项验收」，制作期直接跑）

本项验收原文：「完整独立区域包可安装/撤回，互斥场所不能同时启用；未取得地块准入时保持独立，不增加虚构城市新区。」

约定：
- 坐标单位是米。测量都在 Blender 5.2.1 里做（`-b --factory-startup --python-exit-code 1`），Z-up。glTF 对应 (x, z, -y)。
- SHA 一律取 lab 的提交 blob（`git -C D:/GitHub/creation-notebook-lab show HEAD:<path> | sha256sum`）。前置包的 SHA 取它们 delivery-manifest.json 里写的值。
- 每条检查都要写出：输入 SHA、脚本 SHA、结果 JSON 路径、通过或失败。
- 现成的脚本：`measure_ly060.py`（逐节点包围盒和底面）、`grid_ground.py`（网格射线地面覆盖）、`probe_workyard.py`（点射线）、`body_extents.py`（去掉展示地坪后的本体、足碓重复判定）。

## T0 输入绑定（先跑，失败就停）
- 正例：assembly.json 引用的每个 GLB，SHA 等于 inputs.json 或前置包 manifest 里的值。现件基线：workyard-LOD0 `7eb9739ec09a1ebbbcf16891d14be1488fc484be72c4bae273ec1a993139d17e`、foot-pestle-LOD0 `6f0e41834121fa26cb36303606133256e8a8226e4c49464f68dc93646d181068`、stable A `672beeb46faaee0a…`、kiln-A `e67d597617c3cdeb…`、hand-mill-A `0fe50c2c0604237d…`，全值见 inputs.json。
- 负例：把任意一个引用改成同名但字节不同的文件，检查必须报 SHA 不符。
- 前置门槛：LY-051 到 059 里，凡是被选用的包，status 必须是「交付完成」或「复用完成」；任何一个是「阻断」，就不能装进本包，只能写进排除清单。

## T1 安装 / 撤回指纹
- 步骤：先载入空演示域，或 LY-010 指定的基底，记录指纹 F0（节点名集合、每个节点的 world 矩阵、每个 mesh 的顶点和索引哈希、材质名和贴图哈希）。按 assembly.json 安装后记录 F1，撤回后记录 F2。
- 通过：F2 == F0，逐字节一致。F1 里新增的节点要和 assembly.json 的输出清单一一对上，不多也不少。
- 负例：故意少撤一个节点（比如演示地坪），F2 ≠ F0 必须被报出来。
- 容差：矩阵逐元素 |Δ| ≤ 1e-6，几何哈希必须完全相等。

## T2 互斥
互斥组（实测得出）：
| 组 | 成员 | 依据 |
|---|---|---|
| X1 | stable A ⟂ stable B | 同原点变体，卡片原文「A/B 为互斥设计变体」 |
| X2 | kiln A ⟂ kiln B | 同原点、同 16×19 外框 |
| X3 | hand-mill A ⟂ hand-mill B | 同原点、同 2.8×2.8 外框 |
| X4 | workyard 内的 `pestle_0` ⟂ 独立 foot-pestle（放在同一位置） | 实测是纯平移 (5.0, −1.5, 0.2)，三角面 492/308 相同 |
| X5 | workyard ⟂ compact_work ⟂ 原谷物加工院（LY-057/058 修订版） | 同一 18×24.15 外框和原点 |
| X6 | 按 LY-010 选定的用途，同一时刻只启用一个场所包 | TASKPOOL「不自动全部装入一院」 |
- 正例：每组只启用一个成员时可以装上。
- 负例：每组都试一次同时启用两个成员，检查器必须拒绝，并说出组号。X4 另加一条：独立足碓的 `pestle_stone_static` 离院内 `workyard_stone` 的中心距 < 0.5 m 时，必须报重复。

## T3 高程基准与悬空
- 基准：按 LY-005 契约（`coordinate-contract.json` SHA256 `b6d7fe9db9523569383bf656df39aef63e7d80e8a1d5877196ba0bcab8747712`）。`local:work-site` 帧只定一个基准：取 0.20（与 workyard 院框和城中地块地面一致，四族 N.y=+0.20）或取 0（workyard −0.20），写进 assembly.json；按 E4 不许为贴地悄悄改 N 的 Y。
- 容差按 LY-005 E3：高程 2 mm，平面 5 mm；超出就记为台阶并写级高。下面「≤ 0.005 m」一律改用 0.002 m。
- 检查：每个落地节点（名字或 extras 里的 role 表明它接地，比如 earth_platform、post、board_leg、workyard_earth、mortar）的最低点 z，到它正下方承托面的距离必须 ≤ 0.002 m（E2：承托面在实际地面网格上用竖直射线取最高向上面，不抄节点 Y）。
- 已知要处理的问题：workyard 底面在 +0.200。安装时要么整体平移 −0.200，要么在 +0.200 放承托地坪，二选一，并写进 assembly.json。
- 负例：把 workyard 按原点直接放到 z=0 的地坪上，检查必须报「悬空 0.200 m」。

## T4 地面覆盖（院地 / 棚地）
- 用 `grid_ground.py`，步长 0.5 m，范围是安装后 workyard 和 workshed 的外框。
- 现状基线：workyard 1728 格里有 1012 格空、251 格只有屋顶；workshed 160 格里 159 格只有屋顶。
- 通过：围墙以内、可走区域里的每一格，最低命中都在地面 ±0.01 m 以内。只有声明过的开口和坑（比如窑的操作坑）可以例外，而且必须写明坑底高程。
- 负例：把演示地坪撤掉，空格数应该回到 ≥ 1012。

## T5 展示地坪已移除
- 安装后的节点集合里，不能有名字里含 `presentation_ground` 的节点（现件有 kiln A/B 和 hand-mill A/B 四处）。它们的位置要换成 LY-053/055 的接地件。
- 负例：保留 `A_presentation_ground`，检查必须报失败，并给出它和其他模块重叠的面积（现件是 304 m² 的外框）。

## T6 模块间接触 / 穿插
- 两两做 BVH 三角相交，再按体素算体积：分出合法局部接面（表面距离 ≤ 0.002 m）、正体积侵入、完全包含三类。只做表面 BVH 时要明说，不能称实体碰撞已经查完。
- 通过：除 assembly.json 里逐对声明过的接面外，没有正体积侵入，也没有完全包含。各模块本体的外框之间留出声明的 C 净空，建议 ≥ 1.0 m，最终值等 LY-006/010 定。
- 负例：把窑 A 平移到和 workyard 外框重叠 2 m，检查必须报侵入。

## T7 窑口 / 烟口不被埋
- 从操作坑底 (0, −3.7, −0.8)、火膛口 (0, −1.0, −0.8) 向上打射线，只允许命中窑体自身的构件，不能命中地坪或其他模块。三个 `short_flue` 的顶面（z=1.22）向上打射线必须通天。
- 负例：在窑上方 2 m 处放一块地坪，检查必须报遮挡。

## T8 外接端口
- assembly.json 列出的每个端口都要有：id、位置、朝向法线、高程、宽度、通行包络（人 0.6×1.8 m；搬运另写）、连接对象（LY-052/054/059 的端口或者「未接」）。格式按 LY-006（`schemas/port.schema.json` `9fcdf932…`、`schemas/interface.schema.json` `1e525d50…`、`templates/interface.template.json` `df2fa1b5…`），并用 `LY-006/source/validate_interface.py` 自检；每个端口同时写 local 和 world（LY-005 `port-schema.json`）。
- 接缝绑定：本包消费的两条接缝必须用 registry 里的同一 portId/版本：`stable:entrance:ground@v1::LY-052->LY-060`（seams[273]）、`work-site:service-gate:opening@v1::LY-059->LY-060`（seams[391]）。负例：把版本写成 v2 或换 portId，校验器必须拒绝。
- 本包 produces 的外接端口：registry v1 里 LY-060 `produces=[]`。开工前必须由 LY-006 补登；没补登时本条判「阻断」，不能自造端口 ID。
- 通过：每个端口位置向下 0.05 m 以内有承托面，向外 1.0 m 以内没有遮挡。端口高程和对侧端口的差 ≤ 0.01 m，台阶例外，台阶要声明级高。
- 负例：把端口放进围墙体内，检查必须报遮挡。

## T9 城市独立性
- `docs/cities/luoyang/city-data.mjs` 的提交 blob SHA 安装前后都等于 `c849706b6210…`（全值见 inputs.json）。本包不产生 city-data 差异。
- 本包的空间声明是 `local-study` 或演示域，`cityPlacement` 为 null，除非 LY-010 发了准入。不新增 region 或 chapter id。
- 负例：在清单里写一个城市坐标，但没有准入编号，检查必须拒绝。
- 负例（C02-034）：把私有试放 `res_workyard_034`（chunk SHA256 `6ed43d99447cda1db2daccc6209e28d039bf66fad62d2abd33df7ac6cef5bb5f`，平移 (601.8912, 0, −1080.2)）或任何与 `city-data.mjs:2742` C02-034 矩阵相同的放置写进本包，检查必须拒绝：LY-006 `ownership.json`（`ecbbbcf5…` 等，见 inputs.json）把 C02-034 记为 frozen、owner=null，且它与已入城 courtyard-B 互斥。
- 写入白名单：本包所有文件都在 `workpacks/LY-060/**`；registry v1 里 LY-060 `writeZones=[]`、`ownsGroundPieces=[]`，所以本包出现任何地坪 GLB 时，必须能指向 LY-006 补登的写入区编号，否则判越界。

## T10 文件与档位
- 单个 GLB 不超过 15,000,000 B。LOD0、1、2 三档的 SHA 互不相同，三角面数严格递减。现件里厩只有一档，窑和磨没有 LOD2，这些档位要由前置包补齐，或者如实标「仅 LOD0 / LOD1」。
- 贴图内嵌，材质名属于 LY-007 基线里的语义集合。LY-007 `texture-uv-rules.json`（`a5bfae60…`）把 `REUSED_C_*` 定为旧调色板现状、新模型禁用：复用的厩、窑、磨原件保持原名不改；LY-060 若新出任何几何，只能用 `LY_P01_<m>__PBR/__FLAT`。负例：新件里出现 `REUSED_C_` 前缀必须报错。
- 生产族的 LOD 数字在 LY-007 标「待复核」，T10 结论里要注明。

## T11 证据标注
- 每个输出节点的 extras.evidence 只能取四类：原始考古/原文、异地异期类比、C 工程设计、未知。文案里不能出现洛阳确址、官营制度、产量、热工或动物安全之类的断言。
- 五件事分开写：模型能读取 / 局部通行通过 / 已入城 / 真实结构安全 / 历史复原成立，各自给出状态。

## T12 官方检查
- `lab/tools/build_assets.py --check` 只由 LY-100 在独立分支或副本上跑，本席位不跑。结果绑定到它当时的提交 SHA。

## T13 前置状态门（每次开工前跑）
- 读 LY-009 `board/taskboard.v2.json`（当前 `bd2fcbbe…`）和各前置包的 status.json：LY-008、LY-009、LY-010 必须出现 status.json 且为「交付完成」，否则 LY-060 保持「待输入」。
- LY-057 或 LY-058 若为「阻断」，assembly.json 必须把谷物院场所列入 `excluded`，并写原因；不能用 workyard 原件顶替谷物院场所，除非 LY-001/010 书面改判。
- 负例：把一个 status 为「阻断」的前置包写进 selected，检查必须拒绝。
