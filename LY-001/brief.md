# LY-001｜锁定当前全城与资产快照

席位类型：考据/契约（无前置）。唯一写入区：`workpacks/LY-001/`。lab 仓库全程只读，没有改、建、删文件，没有执行 git 写操作或 `build_assets.py`。收尾时复查了一遍，见 `qa/lab-status-before-after.txt` 和检查 C12。

## 1 快照身份

| 项 | 值 |
|---|---|
| 仓库 | `D:/GitHub/creation-notebook-lab` |
| HEAD | `bce3211f818ee5a8bef1773539da70695ba37b17`，2026-11-05T18:51:05+08:00，「integrate Yong gate and close batch r2026.11.05-5」 |
| 检出分支 | `lab/site-redesign`。HEAD 与 `origin/main` 是同一提交；本地 `main` 引用停在 `44c66da`，已落后，不能拿它当基线 |
| 工作树 | `lab/data/assets.json`、`glb-cache.json`、`report.json` 有未提交改动，只改了时间戳，是席位开始前就有的；`docs/` 没有改动 |
| 字节基准 | 一律取**提交 blob**（即仓库和线上实际提供的字节）。本机 `core.autocrlf=true`，有 258 个文本文件的检出字节与提交字节不同，两种哈希都记在 `qa/file-hashes.json` |

## 2 城市里实际加载了什么（以代码和数据为准）

当前入口是 `docs/cities/luoyang/index.html`。加载链：`app.mjs` 导入 `city-data.mjs`，再按需动态导入 `city-renderer.mjs`。渲染器的规则直接读自代码：
- 节点只要不是 `initial === false`、tier 也不属于未定位类，首屏就加载；
- 某章的 `loadNodeIds` 会在进入该章时并入城中集合；
- `researchModels`（`space: local-study`，`cityPlacement: null`）只在独立研究视图里单独渲染，不进城市坐标；
- `excludeNodes` 列出的子树在城中隐藏，这一项渲染器会严格核对。

| 状态 | 数量 | 内容 |
|---|---|---|
| 已入城·首屏默认加载 | 59 节点 / 21 个远档 GLB（另有 6 个近景 LOD0，选中院落时换档） | 雍门门体＋接口地坪 2；院落 44（C02 36 + D08 8，6 种变体）；城垣 12 段（A 10 + direct 2）；广阳门 direct 门体 1 |
| 已入城·按章加载（initial=false） | 7 节点 / 7 GLB | 道路与地面 4（ground-atomic）；市肆 market-main + N2 替换 2；仓储 granary-city-LOD0 1 |
| 仅模型·独立研究视图 | 14 件（progress-assets/flat） | 灵台、太学长堂 A/B、开阳/平城/上西/雍/中东/旄门 6 门、北区院落 5 型 |
| 隐藏试放（north13，activation=false 或未激活） | 8 包 / 20 GLB | 开阳、平城、上西、雍、中东 5 门的门位包；北侧 13 院的覆盖包（四院 v2、周边 v1、第二排 v1） |
| 仅模型（资产卡） | 40 个家族只有卡 | 见 `qa/ledger.md` §5 |

**运行实测**（`qa/runtime-load-capture.raw.json`）：用本机 Chromium 打开 127.0.0.1 上的只读服务，依次点开六章、全部 14 个研究视图和一次院落近景。首屏请求的 21 个 GLB 与静态推断完全一致（检查 C5）；遍历完以后，清单里 42 个远档全部被请求过（C6）；页面报告的下载量是 3.87 MB 和 13.47 MB，与清单里的 `initialModelBytes` 3872084、`allCityModelBytes` 13466348 对得上（C7）。这些只说明文件能请求到、页面进入 ready 状态，**不算 GPU、手机或画面正确性的验收**。另外 5 种院落的近景换档没有逐一触发，只核对了文件和 SHA。

**旧版 v1 归档入口**：`v1/`，带 `?mode`、`c01stage` 或 `c02stage` 参数的地址会跳转到这里。它仍能加载 v1 专用的环境、通道和旧仓储件。按提交字节服务时，v1 能正常启动，西连接、市肆、太仓几个视图都实测过（`qa/runtime-load-capture-v1.raw.json`）。直接用本机 CRLF 检出的字节服务时，v1 会报「冻结证据校验不一致，拒绝落位」，原因是换行符不同，不是线上故障。

## 3 可追溯性

- `qa/snapshot-ledger.json` 是主台账：42 个 assetId 的远档/近档路径、声明与实际的字节数和 SHA256、排除节点命中情况；66 个城市节点和 14 个研究节点的矩阵、章节和状态；13 份来源合同；20 个试放模型；资产卡逐文件的 SHA，以及它们与城中文件是否逐字节相同；373 个 GLB 的分类与引用方；未能解析的引用。
- `qa/city-nodes.csv`、`qa/glb-files.csv` 是带完整 SHA 的表格版。`qa/family-ledger.json` 记家族去重和各文件去向。`qa/checks.json` 列出 13 项可重算的检查。`qa/ledger.md` 是给人看的汇总。
- 重算方法：先用 `node source/dump_city_data.mjs <city-data.mjs>` 导出清单 JSON，再依次运行 `python -I source/inventory.py <lab> qa <dump> <mq/cards>`、`families.py qa`、`render_ledger.py .`、`draw_map.py`（参数写在各脚本头部）。

## 4 发现的问题（不在本席位修，交 LY-100 或协调者）

1. **合同 SHA 依赖换行符（检查 C8 未通过）**：`city-data.mjs` 的 `provenance.sourceContracts` 共 13 条，有 12 条声明的 SHA 只与本机 autocrlf 检出的字节一致，和提交或线上字节都对不上；只有 `progress-assets/flat/source.json` 一条与提交字节一致。v1 代码自己内置的期望值是提交字节的 SHA（例如 evidence-geometry 是 `fa8b7002…`，清单里写的却是 `662562fa…`），两处互相矛盾。GLB 是二进制，不受影响，48 个 far/near 引用的 SHA 全部吻合。
2. **雍门同家族重复展示**：雍门已经入城并在首屏加载，城墙章却还列着「雍门 · 研究候选」，研究视图里还显示「城市位置尚未配准」（实测）。按同一家族的旧研究档记账，不另计门数。
3. **两个入口的仓储版本不同**：当前入口加载 `granary-city-LOD0.glb`；v1 的太仓视图仍然加载旧的 `storage-group-organized.glb`。仓储 LOD1/2 在城中都没有用到。
4. **字节重复的副本**：`progress-assets/palace-admission-court/` 下 6 个 GLB 与资产卡文件逐字节相同，任何入口都不加载。`d08/D08-environment.glb` 与 `ground-atomic/D08.glb` 也是同一份字节。
5. **旧全库体检的标记**（体检时的 SHA 与当前文件一致）：市肆 `market-cluster.glb` 有 HIGH_DRAWCALLS 500，**这个文件在城中按章加载**；武库 B 三档都有 14 个退化三角面；A1 街区需要 meshopt 解码。这些标记还没有复核，只记录现状。
6. **31 组停用的重复宫殿**：在 bce3211 的 docs、lab/data 和 git 历史里都没有找到对应的文件或清单，没法逐条入账，需要协调者给出来源。
7. 城墙数据本身有缺口（见现状图），对应未建门位。北宫新墙、古水系，以及城南礼制建筑和北郊的位置都还没有配准，研究件因此保持 `cityPlacement=null`。

## 5 证据定性与边界

- 本席位只给出两件事：一是「模型能读取」（文件解析成功，浏览器请求成功、进入 ready）；二是「已入城」（当前入口会加载并放到城市坐标）。**局部通行是否通过、真实结构是否安全、历史复原是否成立，都没有验证**，不能用前两件替代。
- 城市坐标是 `luoyang-local-schematic-v01`，单位是示意工程米，`geographicOrigin` 和 `rotationToTrueNorth` 都是 null。门位和院落落位属于 C 级或推测级设计，证据类别是「C 工程设计」。城门名和相对方位只说明有文献依据，不代表门楼形制已有考古证明。本席位没有引用任何外部史料，也没有任何北魏、西汉或四川的尺寸移作东汉事实。
- 现状图 `preview/region-status-map.png` 是 CPU 栅格化真实三角面画出的俯视图，不是浏览器或 GPU 截图。
