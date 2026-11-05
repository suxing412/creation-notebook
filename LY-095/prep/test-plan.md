# LY-095 验收方案（可执行）

依据「本项验收」：报告要写明具体覆盖的体积、容差、正负例和包含/表面检测方法；每个未解决的交体都要能定位到责任包；禁止只给全城绿色结论。

## 0. 每批固定流程

1. **锁基线**：重新取最新 main。
   ```
   node prep/scripts/dump_manifest.mjs <lab> qa/<batch>/city-manifest.json
   ```
   必须满足：`docsDirty=false`；全部 GLB 的 `farShaMatchesManifest` 和 `nearShaMatchesManifest` 为 true，否则**阻断**，因为基线本身不可信。
2. **验检查器**：带 `--selftest` 跑一次。5 项注错必须全部按预期检出（见 §6），任何一项没检出都**阻断**本批结论，因为检查器失效。
3. **改前**：在当前 main 上运行
   ```
   ly095_regress.py --out before-far.json
   ly095_regress.py --lod near --out before-near.json
   ```
4. **生成 overlay**：按批次 manifest 的 `dependency_closure`，从各包的 `assembly.json` 生成 `overlay.json`：`add`（GLB 路径和矩阵）、`remove`（被替换或隐藏的节点 ID）、`replaceAsset`。每个 GLB 的 SHA256 必须与该包 `delivery-manifest.json` 一致。
5. **改后**：同一个脚本、同一套包络和容差，加上 `--overlay overlay.json`，跑远档和近档各一次。
6. **对比**：
   ```
   python compare.py before.json after.json --owners owners.json
   ```
   退出码为 1 时逐条处理（路线因失去支持而回归、又没有挡体时，看 `supportLossCandidates`，它列出被删或被替换的节点及其所有者）：要么回传责任包，要么由 LY-010 明确接受为待验并公开披露。`owners.json` 来自 LY-006 的冻结所有权表。出现 UNASSIGNED 就**阻断**。
7. **撤回**：不带 overlay 再跑一次（或使用该包的回退 overlay），与 before 对比，退出码必须为 0，证明撤回后不残留。
8. **负例重放**：§5 的负例全部必须失败，而且失败原因和挡体要对。
9. 报告绑定这些 SHA：main 提交、city-manifest.json、overlay.json、全部输入 GLB、`ly095_regress.py`、`glbmesh.py`、`compare.py`、before/after 结果。`sameScript` 和 `sameEnvelope` 必须为 true。

## 1. 容差（冻结值，修改须先经 LY-010 同意）

| 量 | 值 | 说明 |
|---|---|---|
| 接触容差 tol | 0.01 m | 侵入深度不超过此值，视为表面接触 |
| 埋地判定 | 0.05 m | 顶点低于地面超过 5 cm，判为 embedded-below-ground |
| 支持判定 | 构件下移 0.02 m 后与他物相交 | 否则记为无承托，并给出下方空隙 |
| 焊点 | 1e-4 m | 顶点合并，用于闭合性统计 |
| 共面判定 | \|na·nb\|>0.9999 且面距 <1e-3 m | 记为 coplanar 接触，其余为 transversal |
| 人体包络 | r=0.3 m，h=1.8 m，跨台阶 0.35 m，下落 0.5 m，采样间距 0.1 m | C 工程设定，不是史实 |
| 设计宽度探针 | 每侧 1.15 m（总宽 2.3 m），离地 0.9 m | 用于 network.json 声明的最小宽度 |
| 地面双覆盖网格 | 1 m | 统计 bothCovered 和 stepMismatch |

## 2. 正例（必须通过）

| ID 集 | 来源 | 基线结果 | 规则 |
|---|---|---|---|
| NET-*（14 条） | data/west/network.json `testedDoorConnections`（af8e5479…），schematic (x,y) 换算为城景 (x,−y) | 14/14 通过 | 任何一条由通过变为失败就是回归，必须给出挡体节点和责任包 |
| CALT-*（92 条） | c02v/routes.json 按 instances-calt 位移平移 | 92/92 通过 | 同上 |
| C02V 共享道路线（10 条） | c02v/routes.json 道路段 | 10/10 通过 | 同上 |
| 批次新增路线 | 各包 `assembly.json` 的端口和路线，坐标取自 LY-005 | — | 起点和终点必须是冻结的端口 ID。不能用图上自己画的点代替 |

C02V 门线（16 条）在基线上已经失败，原因是 calt 移位造成的契约过时。它们只作历史对照，**不计入回归**。

## 3. 碰撞与体积（按节点对）

- 每对节点都输出：intersectingTriPairs（coplanar / transversal）、contactRegion（AABB 形式的覆盖体积）、双向的点在内统计、最深 8 个点（含 host 和 guest 构件名）、guestComponentsFullyInside。
- 分类：`containment` > `volume-intrusion` > `surface-contact` > `aabb-only`；涉及地面的另分 `embedded-below-ground`、`ground-ground duplicate coverage`、`ground-ground edge contact`。
- **通过条件**：本批 overlay 不引入新的 containment、volume-intrusion、embedded、duplicate coverage。如果确有合法的局部嵌入（比如榫卯、基础入土），必须由该包的 `assembly.json` 按构件名逐条声明，并写明深度上限，**不能整对豁免**。
- 奇偶不一致的点超过 0 个：该对判 PLAUSIBLE，并换一组射线方向或做局部体素复核，复核后才能定 CONFIRMED。
- host 不闭合（boundary>0）时，点在内的结论无效，只报表面相交。
- **叠载检查**（OV-02 实测教训）：overlay 中每个 `add` 节点，若与任一未被 `remove` 的旧节点同类资产且 AABB 重叠率超过 50%，判为「新旧方案叠载」并**阻断**，哪怕分类只是 volume-intrusion。（这条规则目前只写在方案里，compare.py 还没有实现，G 后补上，并用 OV-02 作为它的负例。）
- 基线已知 1 项：market-N2 ↔ market-main，深 0.400 m，PLAUSIBLE。它可以继续存在，但不能变深或扩散，也不能被新包当成已合格。

## 4. 支持与悬空

- 基线已有 21 项无承托构件（见 brief-draft §5.2）。这份清单按 (节点, 构件名, min) 冻结。
- 通过条件：不新增无承托项。新包里凡是写着「落地 / 接地」的构件，必须在 `componentSupport` 中由 ground 或指定节点承托。
- 新件落在隐式基准上（下方没有任何建模地面）时，要单独列出，不能算作已接地。

## 5. 负例（必须失败，且原因要对）

| ID | 构造 | 期望失败原因 | 基线 |
|---|---|---|---|
| NEG-wall09-cross | 在 z=−900 处横穿西墙 wall-09，避开门洞 | 身体和头顶被 wall-direct-wall-09 挡住 | 已失败，挡体正确 |
| NEG-court-C02-005 | 直线穿过 C02-005 院体 | 被 C02-005 挡住 | 已失败，挡体正确 |
| NEG-offground | 从路网走进未建空地 | 失去支持 | 已失败 |
| NEG-closed-<门>（批次新增） | 把门叶、栅栏的关闭态（互斥状态）装入 overlay，再沿该门的正例路线走 | 被该门的关闭态构件挡住 | G 后按 LY-006 的运动件 ID 构造 |
| NEG-wrong-port（批次新增） | 把路线终点偏移到相邻端口或错误门角 | 失去支持或撞墙 | G 后构造 |
| INJ-block | 在广阳门洞注入 3×3×9 m 挡块 | 14 条 NET 路线全部回归失败 | 注错已检出 |

如果负例**通过了**，说明检查器失效或包里有缺口，本批**阻断**。

## 6. 检查器注错（每批必跑 --selftest）

| 注入 | 期望 | bce3211 实测 |
|---|---|---|
| INJ-contained（0.1 m 立方，放在闭合构件内部） | containment | containment |
| INJ-intrude（0.5 m 立方，骑在构件顶上） | volume-intrusion | volume-intrusion |
| INJ-touch（贴地立方） | surface-contact，有承托，埋深 ≤ tol | 最大埋深 7.6e-6 m，有承托 |
| INJ-float（离地 0.5 m） | 无承托，空隙约 0.5 m | 空隙 0.499 m |
| INJ-block（广阳门洞） | 路线被挡 | 挡体 INJ-block，NET 14 条全部回归 |

## 6a. overlay 通道演练（每次改 harness 后必跑）

在当前 main 上用 `prep/overlay-tests/` 的三份 overlay 重放，`compare.py --owners overlay-tests/owners-test.json`：

| 用例 | 必须得到 | 2026-11-06 实测 |
|---|---|---|
| OV-01-noop | 退出码 0，计数与 before 完全相同 | 0 |
| OV-02-dup-court | 退出码 1；newBadPairs 含 C02-005↔OVL-dupB；路线回归的 blockerOwners 为 LY-TEST-dup | 1；volume-intrusion 深 1.089 m；2 条路线 |
| OV-03-remove-ground | 退出码 1；routeRegressions 每条都带 supportLossCandidates=ground-network-ground-stitched | 1；15 条路线、3 个新悬空 |

任何一项不符，说明 overlay 通道或 compare.py 失效，**阻断**本批结论。

## 7. 报告格式（以后放在 qa/）

- 覆盖：被检节点 ID、被检节点对数、各路线长度和样本数，以及覆盖 AABB。不在覆盖范围内的区域写成「本批未纳入」，不写「通过」。
- 每条结论都带上：方法（表面 BVH / 奇偶 / 高度场 / 扫掠）、容差、正例和负例结果、局限。
- 禁止出现的写法：「全城无穿插」「所有人体 / 车辆可通行」「结构安全」。

## 8. 需要绑定的 SHA（基线 bce3211）

- city-data.mjs（工作区）e4115705aeab28f2f6cc2635fbedfabf4158a08af9c626f6dd493ee27d430a1a
- city-renderer.mjs fa0a8dcbfaa5f5f8bd410f3d2295d788f32480c4dab316dd291a561d40d026ca
- network.json af8e5479f47ccae1dd5c41766da60e6a871e74808018737a85514895334afc73
- routes.json f567ae955ae8bc1045c196d47da3b1493a514dd894fc9134274d219e98e89301
- instances-calt.json c830b4e37090da5e070156b7f6199f36c5d0191c339f5a9399f0becded50ff85
- 全部 GLB：见 inputs.json `glb[]`（48 条记录，其中城市装配实际用到 34 条）
- 检查脚本和基线结果：见 inputs.json `harness[]` 和 `baselineOutputs[]`；compare.py 当前版 8b73dcef4ed23ff8bb626e1a7c68ed6c6fe7378a143f1894b344f838eea1f133，ly095_regress.py 949619e2e9a3bd52815f8a84a2cf591ae593d0a434a79aaaf32e211ae00ecb01
- overlay 演练与 11-06 重放结果：见 inputs.json `overlayTests[]` 和 `replay20261106`
