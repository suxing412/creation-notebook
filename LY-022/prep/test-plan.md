# LY-022 test plan（开工后直接跑）

统一前缀：`B="D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P"`，工作目录 `workpacks/LY-022/prep/`。

## 0. 先绑定输入（任一不符就停）

| 输入 | 必须等于 |
|---|---|
| chunks/market_frontage_well_routes.glb（由 extract_chunk.py 取出） | 0193ebc0cfe200292defd595ff4f4011b2b2d05388d4f53e7b4c3a19a255b4c5 |
| city-visible ZIP（五片拼接） | 5895ef23a684a343271183dce1e92e112fb49bba9e03e4372023d1247bb50b69 |
| market-cluster.glb | 77b8bf2e9e1488df02c99ffa1b83af9517fabbb23e9d6b7f86dd3c3361c5a5c8 |
| street_frontage-LOD0/1/2.glb | 46f08f41…f6f2 / 03ad28cf…6126 / b5b13b1c…a1f0 |
| frozen-baseline.json（137 个节点指纹） | 11e47a62528294b591f3639ff6417c3a0c22009f91dd570ff921a10c4deebc6e |
| G 冻结件：LY-005 高程、LY-006 端口和所有权、LY-010 选中方案 | 开工时补填 SHA；**拿不到就整项阻断** |
| LY-021 踏步外端端口 | 开工时补填 SHA；**拿不到就整项阻断** |

如果 G 选的不是组合块的落位（+0.20、不旋转、中心在 214.286 / -1959.184），frozen-baseline.json 和端口都要先重算，旧数字一律作废。

## 1. 原道路指纹不变（本项验收：原道路指纹不变）

- 跑法：`$B check_patch.py -- inputs/chunks__market_frontage_well_routes.glb frozen-baseline.json qa-F.json --patch <patch.glb> --ports <LY-006 ports.json>`，看 F1。
- 正例：7 条路带、5 段界墙、C_market_ground_well_A、店前线三节点、121 个井节点，指纹全部等于 frozen-baseline.json。其中 7 条路带的指纹是 route_public e4566394…f8a6、route_east ba213721…2538、route_rearN 31f4b074…68f8、route_rearS ab79f62a…947e、route_exitPublic b8f82f90…3fa2、route_exitN c291ad93…cb6a、route_exitS 712ada57…1dd6。
- 负例（自测已有）：把 route_public 的一个顶点挪 0.01 m，F1 必须失败。
- 容差：比较时顶点取到 1e-4 m，指纹必须完全相同。
- 另外要做一次安装→撤回：撤回后整块 SHA 回到 0193ebc0…，城中 market-cluster 回到 77b8bf2e…。

## 2. 端点与冻结路带一致（所有补件端点与被冻结路带一致）

- 看 F7。每个端口线段按 0.25 m 取点，两端各内缩 5 mm。补件在端口内侧 1 cm 处的顶面高度，和端口 topY 的差不超过 0.002 m，并且**每个点都要命中**。
- 端口来源：LY-006 冻结件。现在的 provisionalPorts（route_public 南北沿、route_east 西沿）**只能用于自测**。
- 负例（自测已有）：补件离端口 0.05 m，F7 必须失败。
- 再加一个负例：补件顶面 0.215（高出路带 5 mm），F7 必须失败。

## 3. 不覆盖井孔（没有覆盖井孔）

- 看 F2。以井口圆心（局部 -18.00、+7.00）为中心，在半径 0.5925 + 0.05 m 的圆柱里，补件不能有任何面。
- 再跑一次 measure_hole.py，确认地面在开口内没有被打中（groundHitsInsideOpening 为空），井上方也没有非井几何（nonWellGeometryAboveOpening 为空）。
- 负例（自测已有）：盖在井口上的板，F2 必须失败。
- 如果 LY-025 换了井或地面版本：改用 LY-025 冻结的开口参数，不能沿用这里的数字。

## 4. 不形成双层路面、不重铺道路

- F3：补件的底面不能落在任何路带顶面上（向下 0.05 m 内碰到路带就算失败）。负例已有：把板压在 route_public 上。
- F5：补件叠在地面顶上的面数要单独报出来。允许不允许，由 LY-006 的「双层」定义决定；现在的 allowGroundOverlay=true 只是自测用的临时值。
- F4：每个底面离下方地面不超过 0.002 m，否则算悬空。负例已有：0.25 m 处的悬空板。
- 交付时另外报一项：继承下来的路带和地面共面接触 772 m²，**照原样保留，不算 LY-022 的新问题**。

## 5. 没有移动铺面

- F6：补件的顶点不能伸进店前线台基或木构的平面投影，并且高于 0.205。负例已有：伸进北排第一铺的块。
- F1 同时锁住了店前线三节点的指纹。

## 6. 连续支承回归（安装补件后重跑）

- `$B measure_chunk.py -- <装好补件的组合 glb> <market-cluster.glb> out.json`
- 前街网格 7720 点，MISS 必须为 0。相邻点高差上限由 LY-006 或 LY-008 给出；没给的话用 0.010 m，并如实标注这是临时容差。
- 八处入口：入口外 0.05 m 处的支承高度，必须等于 LY-021 冻结的踏步外端高度（±0.002 m）；从 3.00 m 处到 route_public 边沿之间，不能有落空点。

## 7. 身体包络（以后补跑；本轮没跑）

- 体积沿用 LY-021：0.5 × 0.3 × 1.75 m，抬脚 0.02 m（取自 LY-021 prep 的 entry-master-chunk.json）。
- 每处入口走一条路线：铺内 → 踏步 → 补件 → route_public → route_east → route_exitPublic，在 x=244.286 停住，那里归 LY-083。
- 全程每 0.1 m 检查一次足下有支承，头顶净空不低于 1.75 + 0.05 m（现在前街带最低处是 2.35 m）。
- 负例：路线压到井口或棚柱，必须失败。
- 这只是有限的离散检查，不能说成连续人体或车辆仿真。

## 8. 三档与规范

- 补件三档的端口顶面必须完全相同；LOD1 和 LOD2 不能直接复制 LOD0 改名。店前线 LOD1/2 原件台基同样是 0.22，用来确认 +0.20 落位后三档都是 0.42。
- 跑 LY-008 检查器，再跑官方 `lab/tools/build_assets.py --check`（由 LY-100 在合并分支上跑，**本席位不跑**）。单个 GLB 不能超过 15,000,000 字节。

## 9. 复用判定

如果 G 加 LY-021 冻结后，**不放任何补件**就能通过第 6 节（MISS=0、高差在容差内、端口落在地面上），本席位就交「复用」：只交来源、指纹和这次实测报告，不造几何，也不登记成新件。
