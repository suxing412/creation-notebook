# LY-027 测试计划（按「本项验收」，制作时直接跑）

适用对象：选定的 B 组（v2.1 店前线 + 本项占位叠加件）。如果 LY-010 选 A 组，就跑 A 组那一列（第 7 节），A 组的结果现在已经能复现。
运行环境：`D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P <脚本> -- <参数>`。脚本放在 prep/scripts/，制作期复制到 `qa/` 并补上 B 组叠加件的模式。
所有结果 JSON 都必须写出输入文件的 SHA256。SHA 跟下表对不上，就判 **FAIL（输入漂移）**，不能继续出结论。

## 0. 必须绑定的 SHA（输入冻结）

| 输入 | SHA256 |
|---|---|
| street_frontage-LOD0.glb | 46f08f41aa290218e9a3ec4e4de4e2cb676f10a80a035e9b6d3e1f8a0c5bf6f2 |
| street_frontage-LOD1.glb | 03ad28cf31f05cdb518b1ee8652cdc235def6d6ca4b7aa8ca1a29c5272fb6126 |
| street_frontage-LOD2.glb | b5b13b1c74f561903ba12489846c5c841e7b7bf7c1694228e7e12357869fa0f1 |
| market-cluster.glb（A 组 / 形制来源） | 77b8bf2e9e1488df02c99ffa1b83af9517fabbb23e9d6b7f86dd3c3361c5a5c8 |
| N2-replacement.glb（A 组 / 形制来源） | d33cbad1ea14e9436219e895791aafa3c4de20dfe7648635909d6b734e1c99d1 |
| N2-contract.json | 检出 10678d73111ae0d131afc3ff823162392eab339ee66bf2046e61666c2c8d9386 / blob 498f51fcd0723da69ab1b97c56f3de004a449a86e0e322dedc6489446a00e2cd |
| 母版分块（LY-021 抽出） | 0193ebc0cfe200292defd595ff4f4011b2b2d05388d4f53e7b4c3a19a255b4c5 |
| LY-021 冻结踏步包、G 冻结文件 | 待 G 冻结后填 |
| 本项叠加件 LOD0/1/2、状态清单 | 制作时填，所有 qa 结果都要引用它们的 SHA |

## 1. 占位 ID 可删除（验收：每种占位有可删除 ID）

- T1.1 正例：叠加件里每个占位都是独立节点。命名规则 `LY027_<铺号>_<槽位类型>_<序号>`，槽位类型取 counter / floor / shelf / rear。节点名唯一，`extras` 里有 `kind`、`evidence:"C"`、`provenance`（来源，如 "N2-replacement d33cbad1 尺寸词汇"）、`unknown`（未知项列表）、`notInventory:true`。用 gltf_nodes.py 回读，统计数要等于状态清单里的数。
- T1.2 正例：对每一个 ID，单独删掉它（按 city-renderer 的 excludeNodes 语义，按名剔除），重新加载。断言：被删的只有这一个节点；其他节点的名称、三角数、包围盒（容差 1e-4 m）都不变；店前线 3 个源网格的三角集合指纹不变（1 mm 取整哈希，见 LY-021 geom_fingerprint 方法）。
- T1.3 负例：在 excludeNodes 里放一个不存在的名字，加载器必须报“替换节点不完整”（city-renderer.mjs:346 的那种行为）。制作时先在 A 组上验：给 market-main 加一个假名，预期抛错。prep 阶段只读了代码，**没有在浏览器里跑过**。
- T1.4 负例：如果两个占位共用同一个名字，或者某个占位和源网格合并成了一个网格，判 FAIL。

## 2. 满/空状态不封店员路线（验收：满、空两状态都不封店员路线）

- 状态清单 `states.json`：`full` 是全部占位；`empty` 用 excludeNodes 列出全部占位 ID；有需要的话再加 `loading`（装载中：只留地面包和进门货物包络）。三种状态互斥，不能叠载。
- T2.1 正例：B 组 12 个开口，每个都跑这条路线：开口中线 → 柜后线 → 横移到柜台中心 → （S86 型铺）货架前 0.35 m → 货架中心。体包络宽 0.50 和 0.60 各跑一次（深 0.30、高 1.75、离足 0.02），每 0.10 m 一个样，表面相交加完全包含都要检查。满、空、装载三种状态都必须 **0 碰撞**；外路这一段用 LY-021 的冻结结果，并绑定它的 SHA。
- T2.2 容差：体包络边缘离最近占位的水平余量 ≥ 0.05 m。A 组现在的最小余量是 0.26 m（N2 柜后段对台上小包），B 组目标不低于这个值。
- T2.3 负例 1：把一个地面包放到柜后店员带的中线上，必须报碰撞。A 组已经验过：体包络放在 N2_detail_floor_parcel_0 上，报出 2 件。
- T2.4 负例 2：把柜后线退到离柜背只有 0.20 m（小于半宽 0.25），必须报柜台碰撞。prep 早期一次运行（柜后线离柜背 0.20 m）在 A 组每段 23 个样里看到 15 个碰撞，但那次输出被后面的运行覆盖了，没有保留；制作时要作为负例重跑，并保存结果。
- T2.5 店员入口保护：LY-021 踏步顶面和每个开口里面 0.70 m 的落脚区内不能有任何占位（用包围盒判，容差 0）。
- T2.6 继承项，单列不计入本项：A 组中柱 `*_frontpost.001` 挡住柜台中缝到前阶的直线（18 个样里 5 个碰撞），只记录，不修。

## 3. 支承可复核（验收：货架/货物与地面支持可复核）

- T3.1 正例：每个占位从底面取 5 个样点向下打射线。中心样点、或 4 个角样点里至少 3 个的间隙 ≤ 2 mm，并且命中的必须是允许的支承面（店内地面 z=0.22、柜台顶 1.08、已解决支承的货架板顶、母版 sample_ground 或 LY-005 冻结的地面），才算通过。A 组现在满状态 68/68、空状态 27/27 通过。
- T3.2 负例：把一个占位抬高 0.01 m，必须判悬空。
- T3.3 货架板：B 组 6 块板现在 5 mm 内没有任何支承面（侧 0.22、后 0.12、下 0.33/0.40）。**只要支承负责人没交件，T3.3 就是 FAIL**，货架板槽位也不得发布。交件以后再查：每块板至少接 2 个支承件，接触面积 > 0；立柱底面落在 z=0.22（间隙 ≤ 2 mm）。立柱穿板这类正体积交叠要逐处列出并分类成合法接面（A 组的先例是 60 处，每处 0.08×0.045×0.08）。
- T3.4 侵入分类：占位和柜台、墙、地面之间只允许“面接触”（交叠体积 ≤ 1e-6 m³）。出现正体积侵入或完全包含就 FAIL，不能整对豁免。
- T3.5 地面上下文：库文件里没有外地面，所以占位接地只在店内地面上判；店后或摊位上的占位要在母版分块或 LY-005 地面上复测。

## 4. 取放空间与装载状态

- T4.1 每个货架、柜台槽位前面留 0.60 m 深、地面 +0.02 到 +1.75 的取放区，扣掉本货架立柱以后 0 碰撞（A 组 5/5 通过；B 组 S86 两铺现在 0 碰撞）。
- T4.2 装载包络：market-flow-plan 的 small_hand_load 宽 1.6 m，比 A 组后门净宽 1.40 还宽；B 组侧口净宽只有 1.10。所以制作时必须冻结一个进门货物包络（C 参数，宽度小于开口净宽减去 2×0.05）。负例：用 1.6 m 包络穿 1.10 m 侧口，必须报碰撞。
- T4.3 状态切换：full → empty → full 来回切换以后，节点集合和矩阵逐项相同，旧状态和新状态不会同时存在。

## 5. 不当作古代库存

- T5.1 静态检查：每个占位节点的 `extras` 都有 `evidence:"C"`、`notInventory:true`、`unknown` 非空；状态清单和资产文字里不能出现“库存”“实物”“出土”这类断言词（grep 负例：故意写一个，应该报错）。
- T5.2 数量：每铺占位不超过“台上 2、地面 4、每层架 3”这个 C 上限，不追求画面繁密。超出上限就 FAIL。
- T5.3 LOD2：没有柜台和货架的那一档，占位只能“隐藏”或“只留地面大件”，二选一写进清单；不能悬浮在不存在的柜台上（射线复测）。

## 6. 安装与撤回（公共底线）

- T6.1 在严格输入（上表 SHA）上安装一次、撤回一次：撤回以后，店前线 3 个网格的指纹、矩阵、材质和撤回前完全一致；A 组节点集合不变。
- T6.2 互斥：B 组叠加件与 A 组 market-main/market-N2 不能同时加载（坐标同址）。负例：同时加载，检查器必须报“旧新方案叠载”。
- T6.3 体积与字节：每档叠加件不超过 15,000,000 字节（预计远低于这个值）；`lab/tools/build_assets.py --check` 由 LY-100 合并前跑，本项不跑。

## 7. A 组回退列（现在就能复现）

```
blender -b --factory-startup --python-exit-code 1 -P prep/scripts/shelf_audit.py -- cluster \
  <lab>/docs/cities/luoyang/assets/market/market-cluster.glb \
  <lab>/docs/cities/luoyang/assets/market/N2-replacement.glb \
  <lab>/docs/cities/luoyang/data/west/N2-contract.json out/cluster-full.json full [w=0.60]
（把 full 换成 empty，就是删掉全部 closed_stock、parcel、closed_generic_container 共 41 个节点）
```
预期：removedCount 30，addedCount 54；support 不通过数 0；每个铺 rear_to_behind_counter、behind_counter_west/east、door_to_shelf_front 四段 fails 0；through_to_front_step_INHERITED 段 fails 5（继承项）；shelfReachZone 的 hits_excluding_own_posts 为空；negativeControl 的 hits 非空。

B 组现状复测：
```
blender ... -P prep/scripts/shelf_audit.py -- frontage <street_frontage-LOD0.glb> out/shelves-LOD0.json
blender ... -P prep/scripts/v21_interior_free.py -- <street_frontage-LOD0.glb> out/v21-interior-LOD0.json
```
预期（支承修好之前）：6 块板的 surfacesWithin5mm 全部为空；8 铺 staffBand 的 crossing 和 contained 都是 0。

## 8. 不在本项声称

连续人体运动、人群或车辆、承载强度、GPU 或手机实测、历史货物种类都不在本项声称。CPU 截图要标明“CPU”。
