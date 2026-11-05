# LY-095｜全城碰撞与通路回归 · 开工准备（草稿）

状态：**待输入**（G 未冻结；LY-091—094 未交付）。本目录只有测量脚本、改前基线和验收方案，没有制作或修改任何交付几何，也没有写 main、city-data.mjs、项目卡。

## 1. 本项目标

对每一批拟合并区域，在**同一当前基线**上重放三类检查，并给出可定位到责任包的结论：

1. 实际三角面交叉，分成表面接触、体积侵入、完全包含三类；
2. 有限的连续通路：按规定人体包络扫掠，检查足下支持、台阶、头顶净空和身体净空；
3. 关闭态和错误端点的负例必须失败。

报告只写覆盖到的体积、路线、容差和方法，不出全城绿色结论。「模型能读取 / 局部通行通过 / 已入城 / 真实结构安全 / 历史复原成立」五件事分开写。本席位只回答前两件事里的几何部分，不回答结构安全和历史复原。

## 2. 基线与输入（详见 inputs.json）

- 仓库：`D:/GitHub/creation-notebook-lab`，HEAD `bce3211f818ee5a8bef1773539da70695ba37b17`。`docs/` 没有改动（2026-11-06 复核：`git status` 只有未跟踪的 `.claude/`，与本项无关）。
- 城景清单：`docs/cities/luoyang/city-data.mjs`，工作区 SHA256 `e4115705aeab28f2f6cc2635fbedfabf4158a08af9c626f6dd493ee27d430a1a`，git blob `HEAD:` 已记入 inputs.json。两者只差检出时的换行。
- 加载语义按 `city-renderer.mjs`（SHA256 `fa0a8dcbfaa5f5f8bd410f3d2295d788f32480c4dab316dd291a561d40d026ca`）复现：
  - 初始集合（221 行）：`initial !== false` 且 tier 未落位；
  - 章节打开时累加 `loadNodeIds`，并集可达（595–614 行）；
  - `excludeNodes` 删掉自身或祖先节点同名的网格，并核对全部命中（309–346 行）；
  - `transformFor` 用列主序矩阵，或 position+rotationY+scale（372–388 行）；
  - 只有选中的院落用近档（416 行）。
- 全城装配集合 = 66 个节点（59 个初始，另 7 个在章节打开时载入），实际用到 28 个 GLB 远档和 6 个院落近档。50 个 GLB 的 SHA256 全部与清单的 `sha256 / nearSha256` 一致。
- 14 个研究模型的 `space` 是 local-study，`cityPlacement` 为 null，**不进入城市装配**，不纳入碰撞检查。

### 现有成果核对（只能部分复用，不能代替本项）

| 文件 | 内容 | 与本项的关系 |
|---|---|---|
| `data/west/network.json`（af8e5479f47ccae1dd5c41766da60e6a871e74808018737a85514895334afc73） | 14 条院门到广阳门的图路径，标注 "Graph reachability not GPU walk test" | 用作正例路线；它本身不是扫掠检查 |
| `data/west/route-coverage-correction.json` | 新路只与 44 院 AABB 屋顶包络比对 | 只到 AABB，没有三角面或体积检查 |
| `data/west/road-junction-verification.json` | 101 点中线和接缝高差 | 局部接缝，不是全城 |
| `data/west/ground-overlap-classification.json` | 地面残余投影分类 | 与本项地面对比对照（本项结果：重复覆盖 0） |
| `data/c02v/routes.json`（f567ae955ae8bc1045c196d47da3b1493a514dd894fc9134274d219e98e89301） | 102 条院内/院门线，按 c02v 布局写成 | **已过时**：calt 移动了 14 院，见 §5 |

结论：**reuseCandidate = 无**。现有记录是局部或图层级的检查，没有一份是在全城同一基线上做的三角/体积/扫掠回归，也没有负例。

## 3. 改 / 不改范围

- 只写 `workpacks/LY-095/`。
- 不改任何 GLB、城市清单、项目卡、构建数据，也不运行 `build_assets.py`。
- 发现缺陷只定位、只回传给责任包，不代修。

## 4. 证据分类

本项全部是 **C 工程检查**，不产生任何史实主张：

- 人体包络取半径 0.3 m、高 1.8 m、可跨台阶 0.35 m、可下落 0.5 m、2.3 m 设计宽度探针。这些是 C 工程设定，不是汉代人体或礼制尺寸，也不是现代规范认证。
- 车辆、货物、马匹包络：**未知 / 未测**。没有 LY-006 或各包给出的货物包络，就不能代测。
- 「路线可走」只说明在给定包络下几何可走，不说明历史上有这条路。

## 5. 改前基线实测（bce3211）

测量脚本：`prep/scripts/ly095_regress.py`（SHA256 `949619e2…3ec06`），配合 `glbmesh.py`（`ea5f2ac1…fa64`）、`compare.py`（2026-11-06 起 `8b73dcef…f133`）和 `dump_manifest.mjs`（`78a999c0…a1a5`）。
结果文件：`prep/out/baseline-far-bce3211.json`、`baseline-near-bce3211.json`、`selftest-bce3211.json`。SHA 记在 inputs.json。因为结果里含运行秒数，同输入重跑时 JSON 哈希会变，必须用 `compare.py` 判等，不能比文件哈希。

运行命令：
```
node prep/scripts/dump_manifest.mjs D:/GitHub/creation-notebook-lab prep/out/city-manifest.json
D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P prep/scripts/ly095_regress.py -- \
  --manifest prep/out/city-manifest.json --lab D:/GitHub/creation-notebook-lab --out prep/out/baseline-far-bce3211.json
（--lod near 跑近档；--selftest 跑注错）
```

规模：66 个节点，远档 345,022 个三角形（近档 668,734）。全城 AABB 为 x −44.8…2647.1，y −0.03…10.4，z −3953.8…1224.5（城景坐标，米，Y 向上）。远档约 5 秒跑完，近档约 11 秒。

### 5.1 节点对（136 对 AABB 相交）

- 表面接触 51 对，只有 AABB 相交 79 对，地面与地面边缘接触 5 对。**体积侵入 1 对，完全包含 0 对，埋入地下超过 5 cm 的 0 对。**
- **唯一的体积侵入**：`market-N2`（N2_gable_3.87）侵入 `market-main`（N3_gable_−3.87），1 个采样点深 **0.400 m**，位置 (218.286, 3.135, −1968.184)。射线奇偶在两个方向上有 69/1072 个点不一致，说明存在重合面，所以判 PLAUSIBLE，需要复核。责任包是市肆 N2 替换（受保护的 S84/S86 v2.1 系列，交原负责人）。
- 地面：5 对地面在 1 m 网格上的双覆盖样本为 0，没有重叠地面，也就没有 z-fighting 源。最大埋入是 wall-direct-08/09 底部 0.030 m（共 17 个顶点低于地面超过 1 cm），market-main 为 0.010 m。
- 44 院每一院都与恰好 1 块地面有表面接触，没有顶点低于地面超过 1 cm。
- 雍门门体与接口有 82 个横穿三角对，没有点侵入超过 1 cm，判为表面接触。奇偶不一致 31 个，说明有重合面。

### 5.2 构件足下支持（共 2,558 个连通构件）

由本节点其他构件承托的 2,267 个，由地面承托的 264 个，由其他节点承托的 6 个，**无任何承托的 21 个**：

| 无承托项 | 数量 | 实测 | 归属判断 |
|---|---|---|---|
| A 段城垣 wall-A-00…07、11 | 9 | 底面 y=0.17，下方**没有任何建模地面**（隐式基准） | 城垣与地面接口，归 LY-011—020 / LY-081—090 |
| TC03 院 designed_side_passage / designed_rear_work_ground（C02-020、C02-008、FROZEN-D08-NW、NE） | 8 | 0.2–0.212 m 的薄铺面悬在地面切孔上，下方空隙 **0.199 m** | 院落 excludeNodes 与地面切孔不一致，归 TC03 院落族与 ground-atomic 所有者（由 LY-006 指定） |
| TC03-2 architecture_C_plain_timber.001（C02-003、C02-012） | 2 | 0.9×1.9×0.055 m 的板件，底部离地 **0.029 m**，没有任何接触 | 资产内继承缺陷（同一构件出现在两个实例上） |
| market-main route_public | 1 | 铺面在 sample_ground 上方 0.199 m | 资产内 |
| storage-main original_city_ground_preserved | 1 | 本身就是地面（y 0–0.2），落在隐式基准上 | 资产内，可接受 |

### 5.3 通路（包络 r=0.3、h=1.8、台阶 0.35、下落 0.5，间距 0.1 m）

- NET（network.json 中的 14 条院门→广阳门路径）：**14/14 通过**。共 12.74 km、127,463 个样本；足底 y 在 0.185–0.212 之间，最大台阶 0.012 m，2.3 m 宽度探针失败 0 次。
- C02V（c02v/routes.json 原坐标）：86/102 通过。**16 条失败，全部落在 instances-calt 移过位的院落**（C02-005/006/007/009/010/011/012/013/014/032），被本院或邻院墙体挡住。按 calt 位移平移后的 CALT 集合 **92/92 通过**；另有 10 条共享道路线不需要平移，它们在 C02V 中已经通过。结论：routes.json 是过时的契约，不是几何缺陷。
- 探针 PROBE-guangyang-through：门洞内身体和头顶净空都通过，但城外地面只建到 x=−39.0，此后 10 个样本没有支持。
- 探针 PROBE-yong-centre：雍门中门道在接口铺面 x −6.37…−25.66 段净空通过。但铺面**两侧都没有地面**：到最近一个 stitched 路网地面顶点 59.2 m，向东空缺约 49.5 m，与卡片所写「门外接街仍待建」一致，而且城内一侧同样未接。
- 负例 3/3 失败，失败原因都符合预期：NEG-wall09-cross 被 wall-direct-wall-09 挡住身体和头顶；NEG-court-C02-005 被 C02-005 挡住；NEG-offground 在路网外失去支持 7,961 次。

### 5.4 检查器自身的注错（--selftest）

注入 5 例，全部按预期检出：
- 屋脊棱柱内放 0.1 m 立方体 → 判为完全包含；
- 骑在屋脊上的立方体 → 判为体积侵入；
- 贴地立方体 → 判为表面接触、有承托；
- 悬空 0.5 m 的立方体 → 判为无承托，下方空隙 0.499 m；
- 广阳门洞内的 3×3×9 m 挡块 → 路线被挡，且 14 条 NET 路线全部回归失败。

`compare.py` 对比基线和注错结果时退出码为 1（正确报出回归）；基线和自身对比时退出码为 0。

### 5.5 同基线重放与 overlay 安装/撤回演练（2026-11-06）

**重放**：在同一 bce3211 上重新生成 city-manifest.json，SHA256 与原件逐字节相同（`2520a4e1…8d2a`）。用同一脚本（`ly095_regress.py` `949619e2…b01`）重跑远档、近档和 `--selftest`，结果与 11-05 基线相比，除 `manifest` 路径字符串和 `seconds` 外**完全相同**（逐键比对）。`compare.py` 判定：远档和近档退出码 0，selftest 退出码 1（检出 5 个新坏对、2 个新悬空、15 条路线回归，与注错设计一致）。结果在 `prep/out/replay-20261106/`。

**overlay 演练**（`prep/overlay-tests/`，结果在 `prep/out/overlay-20261106/`）。此前 overlay 通道只在代码里存在，没有实际跑过；这次用三份人造 overlay 验证安装→对比→撤回链路：

| 用例 | 构造 | 期望 | 实测 |
|---|---|---|---|
| OV-01-noop（正例） | `replaceAsset` 指向同一个 courtyard-B 远档 GLB | 退出码 0 | 退出码 0；计数与基线完全相同（66 节点、345,022 三角形、21 悬空、192/223 路线通过） |
| OV-02-dup-court（负例：新旧方案叠载） | 在 C02-005 东 3 m 处再放一份 courtyard-B | 新坏对，能定位到双方 | 退出码 1；新增 C02-005↔OVL-dupB **volume-intrusion**，最深 **1.089 m**，位置 (512.695, 0.65, −778.461)，host 构件 architecture_C_whitebox_earth_wall，guest 构件 architecture_C_plain_timber；NET-C02-005 和 CALT-C02-005-gate 两条路线被 OVL-dupB 挡住（身体，首个失败点 x=518.8）；owners-test.json 中的责任号正确带出 |
| OV-03-remove-ground（负例：删地面） | `remove` 掉 ground-network-ground-stitched | 路线因失去支持回归 | 退出码 1；15 条路线回归（14 条 NET 加 1 条，每条 NET 失去支持 7,952 个样本，首个失败点 (485.91, −800.0)），新增 3 个无承托项（wall-direct-08、wall-direct-09、market-main sample_ground） |

**撤回**：不带 overlay 的重放与基线一致（见上）。overlay 本身不写入任何城市文件，因此撤回就是不带 overlay 再跑。

**演练中发现并修复的检查器缺口**：OV-03 的路线回归没有挡体，原版 `compare.py` 因此报不出责任包（`blockerOwners` 为空）。现在 `compare.py` 会列出 `removedNodes`，并把「失去支持且没有挡体」的回归记到被删节点的所有者上（`supportLossCandidates`）。退出码规则没有改。修改后对基线自身对比仍为 0，对重放仍为 0。

**一个分类上的提醒**：OV-02 的整院叠载判为 volume-intrusion，**不是** containment。原因是 containment 只在 guest 某个构件完全落在 host 内时成立，而偏移 3 m 的复制院大部分构件露在外面。所以「新旧方案叠载」的判据不能只看 containment，还要同时看：(a) 新节点与被替换节点的 AABB 重叠率，(b) 批次 manifest 是否在 `remove` 里列出了旧节点。这条已写入 test-plan §3。

## 6. 局限（必须原样写进以后的报告）

- 判断点在内部用的是两个方向的射线奇偶，只对闭合壳可信（66 个节点的边界边全为 0）。奇偶不一致的点要单列。
- 只检查顶点和三角形重心。三角对横穿可以兜住「没有顶点在内」的穿插，但不给侵入深度。
- 通路是离散胶囊扫掠，间距 0.1 m。相邻两个 r=0.3 m 球之间最多漏掉 0.004 m，不是连续刚体运动，也不含车辆转弯。
- 近档基线让 44 院同时用近档，是渲染中实际不会出现的超集，比实际更保守。
- 没有 GPU 或浏览器检查（那是 LY-097 的范围）。

## 7. 开工前还缺

- G：LY-005 端口坐标（门槛、楼面、路网端点）、LY-006 节点和资产到 LY-### 的所有权表（compare.py 用 owners.json 定位责任包）、LY-008 检查器入口和官方规范版本。
- LY-091—094 的批次包，以及批次 manifest（selected_tasks / dependency_closure / gate_results / excluded_regions），用来生成 overlay.json。
- 车辆、货物包络：哪个包声称车可以通过，哪个包就必须给出包络，否则只测人行。
- 私密源包（.blend / 源 ZIP）不在仓库。本项**不需要**它们：所有检查都直接跑在城景实际渲染的 GLB 三角形上。只有当责任包要在源工程里定位具体对象时，才由该包自己提供。
