# LY-006｜冻结模块端口与所有权

席位类型：考据/契约。前置：LY-001、LY-005（均交付完成）。唯一写入区：`workpacks/LY-006/`。
基线：creation-notebook-lab `bce3211f818ee5a8bef1773539da70695ba37b17`。lab 仓库全程只读：没有改、建、删文件，没有运行 git 写操作，也没有运行 `build_assets.py`。见检查 C8，另附一条说明。

## 1 交付了什么

| 文件 | 内容 |
|---|---|
| `registry/seats.json` | 80 个席位（LY-011…090）各一行，包括：所属场地和场地负责人、坐标帧、写入区 ID、拥有的城市节点、源对象（改/替换，以及 keep 计数）、地坪片、切孔、卡片、构件（固定/运动/状态）、产出端口、消费端口 |
| `registry/ownership.json` | 全量所有权：2749 个源对象（generator 对象和 GLB 节点）、80 个城市/研究节点、8 个隐藏试放包、23 个地坪片、4 个切孔、1000 个卡片字段、104 个构件、数据对象；另含冻结地坪清单和冲突表（当前 0 条） |
| `registry/ports.json`、`ports.csv` | 214 个端口。来源分三类：77 个由 LY-006 在现有几何上实测冻结；55 个从 LY-005 导入，并补上了 steward；81 个由席位声明、交付时填值。另有 1 个端口只冻结了 ID，数值待补 |
| `registry/seams.json` | 418 条接缝记录（端口 × 消费方，两侧使用同一 portId 和 version），以及 12 个城门槽位：11 道对向墙缝，加上东北角缝 |
| `registry/zones.json` | 坐标帧和落位、22 个场地及其包络、173 个空间区（168 个写入区、5 个切孔区） |
| `registry/ownership-by-seat.csv` | 按席位展开的可读所有权总表 |
| `templates/interface.template.json`、`schemas/interface.schema.json`、`schemas/port.schema.json` | 后续席位直接填写的接口模板，以及两份 schema。端口 schema 在 LY-005 v1 基础上扩展 |
| `source/validate_interface.py` 和 `templates/examples/` | 对照冻结表校验席位接口文件；附一份通过样例和一份注入了 6 处违规的失败样例 |
| `qa/checks.json` | 十项检查 C1–C10，含 12 个注入负例，全部绑定 SHA256 |
| `preview/partition-plans.png` | 用 PIL 按区盒画的平面/立面示意。不是渲染图 |

## 2 冻结规则（每个对象只有一个负责人）

- **城市节点**：23 个有负责人，只享有提案权，city-data 由 LY-100 写入。其余 57 个冻结，每个都写了原因：雍门和 13 院按保护清单冻结；43 个非示范院保持原矩阵；广阳门与其他门本体不在 011–090 范围内。城垣 10 段的管理者是 LY-020，但墙身不改，各门只在冻结的墙端口上接。
- **源对象**：开阳/平城两门细到 generator 对象这一层。三角范围取自 luoyang-content 公开源 ZIP 里的 `qa/source-object-ranges.json`，我已核对 ZIP 的 SHA 与 manifest 一致，并且在公开 GLB 上逐对象重算了包围盒。其余资产按 GLB 节点分。分配方式是：改/替换由组件席位持有；装配席位以 keep 方式兜底；同一对象出现两个非 keep 声明就算冲突。开阳的分法：
  - LY-011：`C_door_head_1`，以及中门道承托空间；
  - LY-012：全部门框立颊、门叶、横带，以及左右门额；
  - LY-013：`C_upper_deck`；
  - LY-014：隐藏试放里的两端土楔（x 12.4–16），这一点经 Blender 读取试放 blend 证实；
  - LY-015：其余全部，keep。
- **地坪片**：
  - 城中 4 块原子地面、市肆 `sample_ground`、太仓 `original_city_ground_preserved` 只归 LY-090。城中地面上的任何切孔都只由 LY-090 合成。
  - 门下测试带、展示地坪等局部地坪各归一个席位。
  - 新地坪片必须命名为 `gp:<席位>:<名>`，并落在本席位的写入区内。
- **卡片字段**：p-luoyang 的全部字段归 LY-100。各资产卡的 status、statusNote、summary、files、gallery、cover、coverAlt 和 notes.* 由区域装配席位提案；身份字段（id、title、kind 等）冻结。
- **空间**：同一帧内不同席位的写入区体积交为 0。能映射到世界的帧，再按 OBB 互检。每个切孔区必须包含在申请席位自己的写入区内。各场地包络两两不交。各席位改/替换的源对象必须落在自己的写入区内（容差 0.05 m）。
- **固定件与运动件**：11 个运动件，每个都必须挂在一个 mount/opening 端口上，并保持独立节点，不并进静态合批。状态件和可拆件单列。

## 3 实测结论

**墙端口**：12 段城垣共测出 24 个端帽，配成 11 道 32.0 m 的对向缝（广阳门处是 8.0 m），外加东北角缝（上东门）。墙端截面底宽 8.0、顶宽 5.6，底 0.17、顶 6.2，与 LY-018 prep 的独立测值一致。

**帧落位校核**（C6）：
- 开阳、平城隐藏试放的落位，把本地 x=±16 的端间映射到世界后，与对应墙端帽相差 ≤0.15 mm。这说明端间 C 分区确实落在冻结墙端上。
- 店前线 v2.1 帧的平移 (214.286, 0.2, −1959.184) 由母场景分块反推得到，偏差 1e-4。分块是 city-visible 公开 ZIP 里的 `market_frontage_well_routes.glb`，SHA 0193ebc0…；井心 (196.286, −1952.184) 也与此吻合。
- 示范院帧与 C02-010 节点平移一致。仓储帧与 GLB 内的节点平移一致。

**现有几何上的端口值**：
- 开阳、平城门下测试带顶面 0.042，外沿 0.040。平城中门道下没有地面。
- 八铺 12 个门口内侧台面为店前线本地 0.22，即市肆帧 0.42。
- 太仓 A、B 窄阶宽 1.5 m，阶脚分别在 (−11.95, 0.2, −1.5) 和 (12.05, 0.2, −1.35)。
- C_NE_APPROACH_LOCAL：x 2284.21–2317.83，z −3647.47 到 −3484.5，起点顶面 0.20，东端帽顶面 0.0。这是我从公开 ZIP 自行解出后读取的，SHA 58f2f58a…，与 LY-039 prep 的值一致。

**示范院**：用 A2 近档原型做了 0.1 m 占用栅格（`qa/court-A2-free-space.json`），据此给厨灶、圈厕、储藏、滴水、院门、墙环、四角划了互不相交的 C 区。圈厕组 6.75×7.56 m，只有放在东院这一个朝向时才放得下。

**咨询项**：有 12 处世界写入区与城市节点包围盒相接。逐一用三角-OBB 精确 SAT 检查，节点三角落进区内的都是 0 个，只是相接（见 `qa/checks.json` 的 advisory）。

## 4 没做到 / 不声称

- 所有区盒都是 **C 分区**，即工程上的写入范围，不是设计，也不是史实。示范院、市肆卸货边、辟雍跨水与岸缘（LY-071 的变换还没锁）、作业样板帧和宫院组合帧，都是按现有几何推出的保守划分。席位若证明不可行，向 LY-006 申请 registry v2，不得自行越区。
- 示范院以 C02-010 为候选（来自 LY-041 prep 的建议），由 LY-010 冻结。若 LY-010 另选，041–050 的帧和区要整体重发 v2。
- **旧斜路找不到**：平城的 `old-ramp` 只冻结了 ID 和版本，数值待补。我查过以下几处都没有：
  - bce3211 的 docs GLB：缝合路网在两座南门前探测都无面；
  - 平城源 ZIP 里的隐藏试放 blend：只有 3 个网格对象；
  - city-visible 的 `C_gate_local_ground` 分块。

  这项由 LY-016 交实测文件和 SHA，steward 为 LY-017。
- 八铺门口的 x 范围取自 LY-021 prep，我没有独立复测，只复测了台面高度。谷门和夏门没有落位，只有墙缝包络。LY-089 不预先给区，按认领协议走。
- 只做了包围盒与三角级的空间检查。不是实体碰撞，也不证明通行、结构安全或历史复原。没有做浏览器或 GPU 测试。
- **lab 工作树的变化**：开工时 lab 工作树有 3 个既有未提交修改（`lab/data/*.json`），在本席位进行期间被别处还原了。HEAD 没有变，也没有新增条目。C8 的判据写成「HEAD 不变，且没有新增条目」，消失的条目如实列出。

## 5 证据分类

- 原始考古/原文：无。没有考古控制点进入本表。
- 异地异期类比：无。
- C 工程设计：全部区盒、场地包络、端口种类扩展、门槽命名。门槽命名依据现有 C 墙布局和各席位 prep。
- 未知：门址、坛址、宫址等真实位置；旧斜路的数值；各门真实的门道与地坪高差。

## 6 引用

- glTF 2.0 规范：https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html 。坐标系与单位沿用 LY-005 契约，本席位没有重新访问该页。
- 本席位没有使用外部网页资料。所有结论来自本机文件，SHA 见 `qa/checks.json` 和 `inputs.json`。

## 7 重算

```
python -I source/dump_glb_nodes.py <lab>/docs ../LY-001/qa/snapshot-ledger.json qa/glb-node-index.json
python -I source/wall_ends.py <lab>/docs ../LY-001/qa/city-data.dump.json qa/wall-end-ports.measure.json
python -I source/source_objects.py qa/source-objects/kaiyang-K-v1.source-object-ranges.json qa/source-objects/kaiyang-K-v1.objects.json LOD0=... LOD1=... LOD2=...   (平城同理)
python -I source/measure_ports.py <lab>/docs qa/frozen-ports.probes.json qa/frontage-openings.from-LY-021-prep.json
python -I source/measure_chunks.py qa/chunks/northeast_C_access.glb <market_frontage_well_routes.glb> <lab>/docs qa/chunk-measure.json
python -I source/court_free_space.py <lab>/docs/cities/luoyang/assets/c02v/A2-LOD0-prototype.glb qa/court-A2-free-space.json
D:/Blender/blender.exe -b --factory-startup <trial.blend> --python-exit-code 1 -P source/bl_list_objects.py -- qa/<gate>-hidden-trial.objects.json
python -I source/check_registry.py . <lab>/docs <lab> qa/lab-status-before.txt      (内部先重建 registry/)
python -I source/make_examples.py . ; python -I source/render_tables.py . ; python -I source/write_manifest.py .
```

源 ZIP 与 city-visible 分块的取法：用 `git show origin/luoyang-content:<part>` 依次拼接分卷，再用 zipfile 解出。只解到会话临时目录，不进入本包；本包只保留 413 KB 的 `qa/chunks/northeast_C_access.glb` 和两份 range/placement 元数据。
