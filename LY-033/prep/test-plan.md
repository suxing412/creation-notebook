# LY-033 测试计划（制作时直接跑）

所有命令都在 `D:/GitHub/creation-notebook-workpacks/LY-033/prep/` 下运行，Python 一律加 `-I`。lab 仓只读。
`$CITY0 = D:/GitHub/creation-notebook-lab/docs/cities/luoyang/progress-assets/granary-city-v1/granary-city-LOD0.glb`（同目录还有 LOD1、LOD2）。
制作产物约定放在 `workpacks/LY-033/models/`：`granary-city-doors-{open,closed}-LOD{0,1,2}.glb`；如果 LY-006 冻结的是 excludeNodes 方案，就改为每档一个双态文件。

## 0. 绑定的基线 SHA（任何一个变了，先停工，重新核对）

| 输入 | SHA256 |
|---|---|
| granary-city-LOD0.glb | 5937211c7366a5920ae222185176f198cc3d16e8763605fa248e61031c74bc93 |
| granary-city-LOD1.glb | a1265bbf53d10ddb6398efa6f505c1b6dee86b81b37397f7af9855acc34f2e45 |
| granary-city-LOD2.glb | 6b2564d3ffd76e6e982a4a7f703cfd0790ac0e0b2dfa75add4df169c4c82efe7 |
| granary-A-LOD0.glb | 2eee31460a64201c2ba25fbc1bccc9c52f4cebc0f7b9af1f9eb9beeca68b7bf6 |
| granary-B-LOD0.glb | 407403ceeb418f6e1d3f0e86bff7d535642c0236d94691fd2b9a10c2f7866dc6 |
| storage-group-organized.glb（v1，必须保持不变） | b8482824513a101d36eb4c768a4f641e77aaac66c3e834718d7f3964104a644b |
| city-data.mjs（只读对照） | e4115705aeab28f2f6cc2635fbedfabf4158a08af9c626f6dd493ee27d430a1a |
| city-renderer.mjs（只读对照） | fa0a8dcbfaa5f5f8bd410f3d2295d788f32480c4dab316dd291a561d40d026ca |
| LY-031 / LY-032 门件 | 交件时把 SHA 填到这里，并写进 assembly.json |

T0：`python -I -c "import glbread as R;print(R.sha256(r'$CITY0'))"` 的输出必须等于上表。另外每次都重跑 `measure_all.py`，确认门洞 1.49/2.10、楼梯和地板数值与 `measure-all.json` 一致。

## 1. 前置件入口检查（LY-031/032 交件后，装配之前）

- T1.1 门件在**仓局部坐标**交件。A 的门平面在 z=3.0，B 在 z=2.5；门洞 x 为 ±0.75；A 的地板顶 0.85、门楣底 2.95，B 分别是 1.10 和 3.20。门件包围盒必须在门洞外扩 0.30 m 的范围以内，单侧框料允许多吃进墙内 0.20 m。
- T1.2 门件节点的命名前缀：A 用 `LY031_`，B 用 `LY032_`。门叶要做成独立节点，每档每态各一份，不能和固定件合成一个节点。
- T1.3 不能拿 LOD0 改名充当 LOD1/2：三档三角数必须不同，或者另附说明解释为什么相同。
- 负例：如果 B 门件是把 A 门件直接缩放而来，就判 FAIL。办法是比较两件的 POSITION 哈希和尺寸比；任务池要求 B 必须单独实测（属 LY-032 的验收，这里复核）。

## 2. 导回检查：原件一点不少

- T2.1 正例：`python -I preserve_check.py $CITY0 models/granary-city-doors-open-LOD0.glb`，结果必须是 **PASS**，closed 态和 LOD1、LOD2 照此各跑一遍（基线换成对应档）。PASS 的含义是：原四个节点（granary-group-static_timber/_tile/_paper__cargo_proxy、original_city_ground_preserved）的矩阵、材质，以及 POSITION/NORMAL/UV/indices 解码后的哈希全部一致；九张图像的字节全在；新增节点只有 `LY031_`、`LY032_`、`LY033_` 前缀。
- T2.2 恢复：撤回之后的 GLB（或者 city-data 回指原文件）跑 `preserve_check.py $CITY0 <restored> --expect-identical`，必须 PASS，并且文件 SHA 等于 5937211c…。
- T2.3 已自测的负例（prep 阶段已跑）：拿 LOD0 和 LOD1 比，结果 FAIL（图像和几何变了）；拿 LOD0 和 v1 旧组比，结果 FAIL（节点被替换）。正式制作时再补一个负例：从候选件里删掉一扇门叶或一根柱子，T2.1 必须 FAIL。
- T2.4 逐三角对应：`python -I frame_check.py <docs> out.json`。把候选城景档的原节点部分拿去替换输入后，仍然要得到 `sameTriangleSetMm: true`，最大残差不超过 1e-6 m。
- T2.5 体积和规范：单个 GLB 不超过 15,000,000 字节；门件材质要有名字，不得出现无材质的 primitive；不允许退化三角；UV 必须有限值；双面材质要说明原因。这一项交给 LY-008 检查器复核。

## 3. 分层通行体积（开门态）

把门件和城景一起载入：`python -I strip_probe.py $CITY0 qa/strip-open.json <门件城景坐标GLB...>`，或者直接传入合并后的候选文件。

体积分四层：L0 是楼梯外地面（踏步底外 0.6 m），L1 是楼梯，L2 是门平面（墙厚 0.20 m 加门框），L3 是门内 1.0 m。

| 包络 | 足下支持（容差 0.02 m） | 门口净空（地板以上 0.1/0.5/1.0/1.5/1.7 m） | 判据 |
|---|---|---|---|
| 0.9 m 单列人力 | A 0/1463，B 0/1767 | 0/95 | 必须**保持 0**。开着的门叶和门框都不能侵入 x ±0.45 |
| 1.5 m（梯宽） | 0 | 只允许 x=±0.75 两根边界柱失败；门框落在 1.5 m 以内时如实记录增加的失败 | 只记录，不判通过与否 |
| 1.8 m 压力样本 | A **≥192**，B **≥288**；楼梯段的失败位置集合必须和基线逐点一致 | A、B 都 **≥40** | 必须**仍然失败**。如果计数比基线少，就判 FAIL（说明切掉了东西或者改了楼梯） |

- T3.1 开门态的门口最小净宽不小于 1.00 m（0.9 m 加每侧 0.05 m 余量），净高不小于 1.90 m。用 `measure_all.py` 的 clearWidthByHeightAboveFloor 字段读数，运行前把门件 GLB 加进 FILES。
- T3.2 门槛：0.9 m 条带在门平面上 0/1463（0/1767）的支持结果必须保持。如果 LY-031/032 做了凸起门槛，这一项会失败；只能作为「带说明的失败」交付，不能改容差掩盖。
- T3.3 资产卡里的「A 51、B 77」只能照原样引用；本方法的计数单独列出，不互相替代。

## 4. 闭门负例

- T4.1 闭门态下，0.9、1.5、1.8 三种条带的门口净空失败必须是**全列**：A、B 都是 95/95、155/155、185/185。参考数据是内存测试盒的结果，见 strip-baseline-closed.json。
- T4.2 闭门不能改动足下支持的计数，即 0.9 m 仍为 0，1.8 m 仍为 192/288。门叶不允许落地变成「支撑」。
- T4.3 门叶停放负例：用 `--fixture intrude` 的参考数据（0.9 m 条带 80/95）证明探针能发现门叶停在路径上。真实开门态必须是 0/95。
- T4.4 两态互斥：同一档里开门节点和闭门节点不能同时加载。excludeNodes 方案要求每个记录恰好排除一组；双文件方案要求 city-data 只指向一个文件。可以用 city-renderer 的节点遍历逻辑做离线复现：两组都没被排除时判 FAIL。

## 5. 门叶扫掠

- T5.1 assembly.json 必须写明转轴位置、开启方向、扫掠角度和扫掠体积（仓局部坐标）。
- T5.2 扫掠体积不能碰到：货物代理（A 在 x≥2.6、z≤1.05；B 在 x≥4.1、z≤1.05）、墙体、门楣、楼梯，以及外开时的第一级踏步（A 在 z 3.2–3.52，B 在 z 2.7–3.02）。外开时如果扫过楼梯顶就判 FAIL，除非另行披露并说明。
- T5.3 扫掠过程中会横穿 0.9 m 路径，这一点只记录，不判通过与否；判通过与否的只有停放态（全开、全闭）。

## 6. 同机位前后图

- T6.1 运行 `D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P render_fixed.py -- <qa/preview> installed-open <候选GLB>`，closed 态和 restored 态照此各出一套。
- T6.2 机位表冻结在 render_fixed.py 里（文件 SHA 为 6631ee7a…，改过就重出 before 图）。before 图在 baseline/before-*.png，日志在 before-render-log.json。
- T6.3 restored 和 before 七张图要逐像素对比，差异像素占比不超过 0.1%（Workbench 是确定性渲染，期望值为 0）。installed 与 before 的差异只允许出现在门洞的投影区域。
- T6.4 所有图都要标注「Blender Workbench CPU 渲染，非浏览器/GPU」。

## 7. 运行时可读（不等于已入城）

- T7.1 用当前 GLTFLoader 解析候选 GLB：静态网格，没有蒙皮和形变；离线复现 city-renderer.mjs:287-330 的遍历过程，确认 excludeNodes 能命中门件节点名。
- T7.2 bounds 仍落在 storage-main 的范围 [2249.714, 0, -3699.469]–[2321.714, 5.15, -3647.469] 之内。节点数和计数不变（newNodes 0，countChange 0）。
- 交付表述只能写到「模型能读取」和「0.9 m 有限条带局部通行通过」。负重、双人交错、车辆、结构安全、历史复原一律不写。
