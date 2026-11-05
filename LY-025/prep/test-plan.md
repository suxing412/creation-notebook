# LY-025 测试计划（制作时直接跑）

按「本项验收」三条展开：①同时验证井口、地坪孔、下方原有地层是否封堵；②井或孔任一个加载失败时整体还原；③原始井网格和变换可追溯。
制作开工前，先重新核对 G 冻结时 main 的 SHA。下面绑定的 SHA 只要有一个变了，就停下来重测，不能沿用本草案的数字。

## 0. 要绑定的 SHA（输入）

| 键 | SHA256 |
|---|---|
| market-cluster.glb | 77b8bf2e9e1488df02c99ffa1b83af9517fabbb23e9d6b7f86dd3c3361c5a5c8 |
| market_frontage_well_routes.glb（分块） | 0193ebc0cfe200292defd595ff4f4011b2b2d05388d4f53e7b4c3a19a255b4c5 |
| city-visible ZIP | 5895ef23a684a343271183dce1e92e112fb49bba9e03e4372023d1247bb50b69 |
| well-A-LOD0.glb | 6bc463f8638df55c7e07282641d3d66d07d23ce9af8cd72a5e211be9772a38ab |
| N2-replacement / flowB-routes | d33cbad1…c99d1 / 43d7799f…898f845e |
| ground-atomic 四片 | fdfc3ce5… / aed8b3d4… / 4313826d… / 3ab93310… |
| city-data.mjs / city-renderer.mjs / west-layer.mjs / market-assembly.mjs | e4115705… / fa0a8dcb… / d8c14142… / 0145ac84… |

交付件（models/well-market-atomic.glb 一类）做出来后，它的 SHA 要写进 qa/ 的每一个结果文件。

## 1. 子集截取的身份检查

- **T1.1 正例**：截取件里恰好有 1 个 `C_market_ground_well_A` 和 121 个 `A_LOD0__*`，没有其他节点。V21 和 route/boundary 节点数为 0。
- **T1.2 无损**：截取件的节点 ⇔ 分块里的同名节点，accessor 原字节逐一相等；世界矩阵相等，容差 0。对照源：source-node-manifest 里的 evaluated_world_directed_triangle_sha256，按 1 mm 回读容差比对。
- **T1.3 可追溯**：跑 `compare_well_nodes.py well-A-LOD0.glb <交付件> 196.28599548339844,0.20000000298023224,-1952.1839599609375 3e-4`，期望 identicalOrWithinTol = 121、differs = []、maxDevAll ≤ 2e-4 m（2000 m 量级下 float32 的精度极限约 1.2e-4）、三角面 9260、chunkOnly = []。
- **T1.4 负例：二次平移**。把交付件根部再加 (196.286, 0, −1952.184)，或者在 assembly 里再写一次 node translation，T1.3 必须报 differs = 121。如果契约允许外层变换，按 identity 拒收。
- **T1.5 字节**：单个 GLB ≤ 15,000,000 B（预计约 1.8 MB）。纹理内嵌，节点名保留。

## 2. 井口、地坪孔、下方地层（验收①）

脚本：`measure_well_opening.py`，`boolean_volumes.py`（先 weld 1e-5 m）。

组合 S 是当前基线上的安装后状态，分四个变体：{layout=calt, original} × {flow=A, B}。每个变体的组成是 market-cluster（排除 sample_ground）＋ N2 ＋（flowB）＋ 对应环境件 ＋ 交付件。

- **T2.1 井口通**：井心加上 r = 0.1/0.2/0.3/0.4/0.44 × 8 个方位，共 41 条竖向射线。z ∈ [−0.45, 0.25] 内命中地面类网格的次数必须为 0。允许命中的只有 `A_LOD0__` 机构件（容器、绳、轮），而且命中高度都在 z ≥ 0.30。
- **T2.2 孔径**：开孔地面 16 个方位、步长 5 mm，第一次命中的半径 ∈ [0.585, 0.600] m（实测 0.590–0.595）。孔圈顶点 96 个，r ∈ [0.5899, 0.5902]。
- **T2.3 地面未被暗改**：开孔地面的外框 8 个顶点和 sample_ground 的 8 个顶点逐一相等（取 4 位小数）；otherVerts = 0。体积差 = π·0.59²·0.2 ± 0.002 m³（实测 0.2181）。
- **T2.4 井和地面的接触分类**：井筒 ∩ 开孔地面的体积 ≤ 1e-5 m³（实测 2.655e-6，按「48 段多边形数值薄片／局部嵌接」逐对写明）；井栏、柱、柱脚 ∩ 地面 = 0。正体积超过阈值就阻断，不能整对豁免。
- **T2.5 下方地层**：S 的每个变体里，所有非 A_LOD0 网格在井心 r ≤ 0.59 内 z < 0.2 的命中数都为 0（原子地面、6 m 路、joined-route-terrain 都不能补一层）。另外记一条事实：井底 −0.45 m 以下无几何。这是已知的视觉缺口，不在本包修。
- **T2.6 负例：旧地面堵井**。S 去掉排除 sample_ground 的那一步 → T2.1 必须失败（实测 41/41 命中），而且井筒 ∩ sample_ground ≈ 0.0912 m³。检查器必须报阻断。
- **T2.7 负例：有孔无井**。只装开孔地面、不装井 → 「孔无井」检查（井位 r ≤ 0.59 内没有 A_LOD0__short_liner 和 circular_collar）必须报阻断。
- **T2.8 负例：有井无孔**。即 T2.6。
- **T2.9 负例：双层地面**。sample_ground 和开孔地面同时在场 → 同一 XZ 上 z=0.2 处有两个面，检查器必须报阻断（同名或同包围盒的地面不能共存）。
- **T2.10 负例：整块分块载入**。直接加载 0193ebc0… → 应检出 12 个 route/boundary 和 market-cluster 重复（同名、同包围盒），外加 V21 和五店三摊叠载，必须拒收。

## 3. 安装、撤回、失败还原（验收②）

两个口径都要跑。改动以 LY-100 的语义提案形式交，本席位只在隔离的副本或 overlay 上测。

- **T3.1 安装（app.mjs/city-renderer 口径）**：market-main.excludeNodes = 原 30 个 N2_* ＋ sample_ground；新增资产和节点（tier C，chapter market，loadNodeIds 加入）。期望：rebuild 成功，matchedExclusions = 31。
- **T3.2 撤回**：去掉新增资产，excludeNodes 恢复为 30 个 → 渲染组的节点集合、几何指纹（位置和三角 SHA）、材质名、矩阵都和安装前完全一致。原道路和 market-cluster 的指纹不变。
- **T3.3 失败还原：井件 404 或 SHA 不符**。Promise.all 必须 reject，旧 modelGroup 保留，场景里没有任何一帧出现「孔无井」或「井无孔」。用断网或篡改 URL 做故障注入；验证方法是在浏览器里读取 scene 的节点集合。
- **T3.4 失败还原：sample_ground 未命中**（比如 market-cluster 被换了版本）。city-renderer 应该抛出「模型替换节点不完整」，旧组保留。
- **T3.5 v1 口径**：market-assembly 加一条按精确名 retire `sample_ground` 的规则（期望数 1，来源只限 market 原根），井件作为 extraEnvironment。load 失败时 destroyDistrictAssets 必须清空。在 calt 和 original 两种 layout、A/B 两种 flow 下 assertGroundAtomic 仍然通过，removedN2 = 30、removedRoutes = 0 或 7 不变。
- **T3.6 互斥**：新旧方案（井包和 city-visible 整层）不得叠载。adapter 那一层 replacesLegacyCityNodeIds 如果将来启用，必须和本包互斥。

## 4. 不能声称的内容

- 不是 GPU、手机或浏览器验收，除非 T3.3–T3.5 真的在浏览器里跑过并留了记录。CPU 和 Blender 的结果都要标 CPU。
- 不能说「真实结构安全」「历史复原成立」。井位是 C 设计试放，并且和 market-precedents 的 avoid 规则有冲突，需要先拿到准入。
- 表面 BVH 统计不等于实体碰撞已穷尽；布尔只做了列出的 6 对（井部件 × 地面）。

## 5. 人体与通行（交给 LY-029 或区域验收，本包只出接口）

- 井外缘（亭顶半宽 1.65 m）到 route_public 的 XZ 净距 ≥ 3.0 m（实测 3.35 m）。人体包络、汲水操作区和货物流线不在本包测，只把接口数据交出去。
