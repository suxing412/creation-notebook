# LY-001 快照台账（自动生成，勿手改；由 source/render_ledger.py 从 qa/*.json 生成）

- 仓库：`D:/GitHub/creation-notebook-lab`，HEAD `bce3211f818ee5a8bef1773539da70695ba37b17`（2026-11-05T18:51:05+08:00，分支 `lab/site-redesign`；origin/main=`bce3211f818ee5a8bef1773539da70695ba37b17`；本地 main 引用 `44c66da842eca5799d353e07ec1550b000b8855b` 落后）
- 工作树：`lab/data/*.json` 3 个文件有未提交改动（仅时间戳），docs/ 无改动；哈希一律取提交 blob 字节，检出字节另记（autocrlf 使 258 个文本文件检出字节不同）。
- 计数：哈希文件 973，GLB 373；城市清单 assets 42、nodes 66、researchModels 14、chapters 7。

## 1 校验结果（qa/checks.json）

| 检查 | 结果 | 说明 |
|---|---|---|
| C1 城市清单每个 GLB 引用都能定位 | pass | 48 个 far/near 引用；缺失 [] |
| C2 声明字节数与提交字节一致 | pass | 不符 [] |
| C3 声明 SHA256 与提交字节一致（有声明者） | pass | 48/48 个引用带 SHA 声明；无声明：[] |
| C4 excludeNodes 在 GLB 中全部命中（渲染器严格校验） | pass | 13 个带排除节点的引用 |
| C5 运行实测首屏请求集合 = 静态推断首屏 far 集合 | pass | 首屏实测 21 个 GLB；差集 实测-静态=[] 静态-实测=[] |
| C6 运行实测遍历后请求的 far 集合 = 清单全部 far | pass | 清单 far 42 个；未被请求 [] |
| C7 全城下载字节与清单 allCityModelBytes 一致 | pass | 实测“本次已载入模型 13.47 MB”，清单 allCityModelBytes=13466348；首屏 3.87 MB 对 initialModelBytes=3872084 |
| C8 provenance.sourceContracts 的 SHA 与提交（线上）字节一致 | fail | 1/13 与提交字节一致；12 个只与本机 autocrlf 检出字节一致 |
| C9 隐藏试放包模型 SHA 与 source.json 声明一致 | pass | 20 个模型文件 |
| C10 隐藏试放在当前入口不被加载 | pass | 实测请求集合与 north13 试放模型文件无交集（城景用的是 flat 转换件） |
| C11 研究模型全部 cityPlacement=null | pass | 14 件 |
| C12 lab 仓库未被本席位改动 | pass | 快照时与收尾时的已跟踪改动一致：['M lab/data/assets.json', 'M lab/data/glb-cache.json', 'M lab/data/report.json']（均为既有时间戳改动）；docs/cities/luoyang、docs/library、docs/model-library 无改动；HEAD 不变 |
| C13 单 GLB ≤ 15,000,000 字节（快照内全部 GLB） | pass | 373 个 GLB，超限 [] |

## 2 当前入口城市节点（66 + 研究视图 14；全量 SHA 见 qa/city-nodes.csv）

| 状态 | 数量 | 节点 |
|---|---|---|
| 已入城·首屏默认加载 | 59 | yong-gate-body、yong-gate-interface、C02-018、C02-019、C02-020、C02-021、C02-022、C02-023、C02-024、C02-025、C02-026、C02-001、C02-002、C02-027、C02-028、C02-029、C02-030、C02-031、C02-003、C02-004、C02-005、C02-006、C02-007、C02-008、C02-009、C02-010、C02-011、C02-012、C02-013、C02-032、C02-014、C02-015、C02-016、C02-017、C02-033、C02-034、C02-035、C02-036、FROZEN-D08-S1、FROZEN-D08-S2、FROZEN-D08-S3、FROZEN-D08-S4、FROZEN-D08-M、FROZEN-D08-E、FROZEN-D08-NW、FROZEN-D08-NE、wall-A-wall-00、wall-A-wall-01、wall-A-wall-02、wall-A-wall-03、wall-A-wall-04、wall-A-wall-05、wall-A-wall-06、wall-A-wall-07、wall-A-wall-10、wall-A-wall-11、wall-direct-gate-body-only、wall-direct-wall-08、wall-direct-wall-09 |
| 已入城·按章加载（initial=false） | 7 | ground-network-ground-stitched、ground-retained、ground-south、ground-D08、market-main、market-N2、storage-main |
| 仅模型·独立研究视图（cityPlacement=null，城中不渲染） | 14 | research-lingtai、research-taixue-A、research-taixue-B、research-north13-kaiyang-K、research-north13-court-A2、research-north13-court-B、research-north13-court-B2、research-north13-court-TC03-2、research-north13-court-A、research-north13-pingcheng-P、research-north13-shangxi-X、research-north13-yong-Y、research-north13-zhongdong-Z、research-mao-gate |

### 2.1 城市资产（42 个 assetId）

| assetId | far 路径 | far SHA256 | near 路径 | near SHA256 | 排除节点 | 使用节点数 |
|---|---|---|---|---|---|---|
| courtyard-A | `assets/r01/R01-A-LOD1-prototype.glb` | `0827fa4994b2de31…` | `assets/r01/R01-A-LOD0-prototype.glb` | `93b70de24ee56573` | 3 | 12 |
| courtyard-B | `assets/r01/R01-B-LOD1-prototype.glb` | `25f018fa8fad0ec6…` | `assets/r01/R01-B-LOD0-prototype.glb` | `a8d94bb3897825c6` | 3 | 10 |
| courtyard-TC03 | `assets/d08/TC03-LOD1-prototype.glb` | `8daea250825976b3…` | `assets/d08/TC03-LOD0-prototype.glb` | `367a7d2534443bca` | 2 | 4 |
| courtyard-A2 | `assets/c02v/A2-LOD1-prototype.glb` | `277e9e73e8f2d8b8…` | `assets/c02v/A2-LOD0-prototype.glb` | `19b052022b2f6955` | 3 | 9 |
| courtyard-B2 | `assets/c02v/B2-LOD1-prototype.glb` | `8328237369a33571…` | `assets/c02v/B2-LOD0-prototype.glb` | `d99affcae95cfe22` | 3 | 7 |
| courtyard-TC03-2 | `assets/c02v/TC03-2-LOD1-prototype.glb` | `d2432b7c22017c46…` | `assets/c02v/TC03-2-LOD0-prototype.glb` | `bf6287a5f40c5a73` | 5 | 2 |
| wall-A-wall-00 | `assets/city-wall/A/wall-00.glb` | `12d84a0b27f7e5d6…` | `` | `` | 0 | 1 |
| wall-A-wall-01 | `assets/city-wall/A/wall-01.glb` | `cfbbc45a874a32a0…` | `` | `` | 0 | 1 |
| wall-A-wall-02 | `assets/city-wall/A/wall-02.glb` | `8a17587a995e6851…` | `` | `` | 0 | 1 |
| wall-A-wall-03 | `assets/city-wall/A/wall-03.glb` | `cd4cb2b629c15cbf…` | `` | `` | 0 | 1 |
| wall-A-wall-04 | `assets/city-wall/A/wall-04.glb` | `50d8c7aa2c7d7dce…` | `` | `` | 0 | 1 |
| wall-A-wall-05 | `assets/city-wall/A/wall-05.glb` | `4e000b0c34b26504…` | `` | `` | 0 | 1 |
| wall-A-wall-06 | `assets/city-wall/A/wall-06.glb` | `d7d3cc79fe7ea85c…` | `` | `` | 0 | 1 |
| wall-A-wall-07 | `assets/city-wall/A/wall-07.glb` | `e7db9cff3eed1e7f…` | `` | `` | 0 | 1 |
| wall-A-wall-10 | `assets/city-wall/A/wall-10.glb` | `afb20f8e3b19dfd8…` | `` | `` | 0 | 1 |
| wall-A-wall-11 | `assets/city-wall/A/wall-11.glb` | `2cfa846184cf28e3…` | `` | `` | 0 | 1 |
| wall-direct-gate-body-only | `assets/city-wall/direct/gate-body-only.glb` | `cdba2d5c3bbf14bb…` | `` | `` | 0 | 1 |
| wall-direct-wall-08 | `assets/city-wall/direct/wall-08.glb` | `221b8dc8c5702bbd…` | `` | `` | 0 | 1 |
| wall-direct-wall-09 | `assets/city-wall/direct/wall-09.glb` | `d4fb5c1cbf3c08ff…` | `` | `` | 0 | 1 |
| ground-network-ground-stitched | `assets/ground-atomic/network-ground-stitched.glb` | `fdfc3ce5c63305f7…` | `` | `` | 0 | 1 |
| ground-retained | `assets/ground-atomic/retained.glb` | `aed8b3d4cb12aead…` | `` | `` | 0 | 1 |
| ground-south | `assets/ground-atomic/south.glb` | `4313826ddf5fbe0c…` | `` | `` | 0 | 1 |
| ground-D08 | `assets/ground-atomic/D08.glb` | `3ab933108b88c5c3…` | `` | `` | 0 | 1 |
| market-main | `assets/market/market-cluster.glb` | `77b8bf2e9e1488df…` | `` | `` | 30 | 1 |
| market-N2 | `assets/market/N2-replacement.glb` | `d33cbad1ea14e943…` | `` | `` | 0 | 1 |
| storage-main | `progress-assets/granary-city-v1/granary-city-LOD0.glb` | `5937211c7366a592…` | `` | `` | 0 | 1 |
| study-lingtai | `progress-assets/flat/study-lingtai-c1b58de1bff4.glb` | `c1b58de1bff44b80…` | `` | `` | 0 | 1 |
| study-taixue-A | `progress-assets/flat/study-taixue-A-ee4163421d16.glb` | `ee4163421d1652b9…` | `` | `` | 0 | 1 |
| study-taixue-B | `progress-assets/flat/study-taixue-B-11b01e4948be.glb` | `11b01e4948be0e0e…` | `` | `` | 0 | 1 |
| study-north13-kaiyang-K | `progress-assets/flat/study-north13-kaiyang-K-94693c58dd63.glb` | `94693c58dd630815…` | `` | `` | 0 | 1 |
| study-north13-court-A2 | `progress-assets/flat/study-north13-court-A2-db02f24fde89.glb` | `db02f24fde899b73…` | `` | `` | 0 | 1 |
| study-north13-court-B | `progress-assets/flat/study-north13-court-B-6f7f84af4e7f.glb` | `6f7f84af4e7f5792…` | `` | `` | 0 | 1 |
| study-north13-court-B2 | `progress-assets/flat/study-north13-court-B2-7d3758ce668d.glb` | `7d3758ce668d0654…` | `` | `` | 0 | 1 |
| study-north13-court-TC03-2 | `progress-assets/flat/study-north13-court-TC03-2-98bedd183667.glb` | `98bedd1836674388…` | `` | `` | 0 | 1 |
| study-north13-court-A | `progress-assets/flat/study-north13-court-A-19a42b6b0b1c.glb` | `19a42b6b0b1cc1f2…` | `` | `` | 0 | 1 |
| study-north13-pingcheng-P | `progress-assets/flat/study-north13-pingcheng-P-c8ab88f4b326.glb` | `c8ab88f4b326e0c2…` | `` | `` | 0 | 1 |
| study-north13-shangxi-X | `progress-assets/flat/study-north13-shangxi-X-9a892e7f27f7.glb` | `9a892e7f27f7b8fa…` | `` | `` | 0 | 1 |
| study-north13-yong-Y | `progress-assets/flat/study-north13-yong-Y-1983dab58385.glb` | `1983dab583853beb…` | `` | `` | 0 | 1 |
| study-north13-zhongdong-Z | `progress-assets/flat/study-north13-zhongdong-Z-856cfff1f015.glb` | `856cfff1f015f8ce…` | `` | `` | 0 | 1 |
| study-mao-gate | `progress-assets/flat/study-mao-gate-0ae54089b66a.glb` | `0ae54089b66a54f1…` | `` | `` | 0 | 1 |
| yong-gate-near | `library/models/m-luoyang-yong-gate/files/yong-Y-LOD0.glb` | `45743d730f7694fe…` | `` | `` | 0 | 1 |
| yong-gate-apron | `progress-assets/yong-city-v1/yong-apron-LOD0.glb` | `e52eaaf514c3e514…` | `` | `` | 0 | 1 |

## 3 运行实测（本机 Chromium，127.0.0.1 只读服务）

- **initial-open**：新请求 21 个（当前画面含 59 个已建模型实例；本次已载入模型 3.87 MB）
- **chapter:walls**：新请求 0 个（当前画面含 59 个已建模型实例；本次已载入模型 3.87 MB）
- **chapter:residential**：新请求 0 个（当前画面含 59 个已建模型实例；本次已载入模型 3.87 MB）
- **chapter:market**：新请求 2 个（当前画面含 61 个已建模型实例；本次已载入模型 4.98 MB）
- **chapter:storage**：新请求 1 个（当前画面含 62 个已建模型实例；本次已载入模型 6.64 MB）
- **chapter:terrain**：新请求 4 个（当前画面含 66 个已建模型实例；本次已载入模型 13.47 MB）
- **chapter:ritual (defaultResearchModel)**：新请求 1 个
- **study:太学长堂 A**：新请求 1 个
- **study:太学长堂 B**：新请求 1 个
- **study:开阳门**：新请求 1 个
- **study:平城门**：新请求 1 个
- **study:上西门**：新请求 1 个
- **study:雍门（研究候选，与已入城雍门同家族）**：新请求 1 个
- **study:中东门**：新请求 1 个
- **study:旄门**：新请求 1 个
- **study:北区院落 生活院修订(A2)**：新请求 1 个
- **study:北区院落 储藏作业院(B)**：新请求 1 个
- **study:北区院落 储藏作业院修订(B2)**：新请求 1 个
- **study:北区院落 周边院落(TC03-2)**：新请求 1 个
- **study:北区院落 生活院(A)**：新请求 1 个
- **level:city**：新请求 0 个
- **level:courtyard (默认 C02-001，近景换档)**：新请求 1 个
- v1 归档入口：同一 v1 入口用工作树（autocrlf 检出，source/serve_readonly.py，端口 8766）启动时显示「未完成：冻结证据校验不一致，拒绝落位」：v1/evidence-view.mjs 内置期望 evidence-geometry.json=fa8b7002…、stage-contract.json=32274606…，等于提交字节；工作树 CRLF 字节为 662562fa…/6ade3f6e…。按提交字节服务后正常启动。
  - v1 默认启动：6 个新请求
  - v1 C02 · 固定几何变体四簇：6 个新请求
  - v1 ?mode=west 启动：8 个新请求
  - v1 west 西连接候选：13 个新请求
  - v1 west 金市候选附近·市肆C样板：2 个新请求
  - v1 west 太仓候选附近·仓储作业C样板：1 个新请求；v1 归档入口仍载旧仓储组 storage-group-organized.glb；当前入口 storage-main 已换成 granary-city-LOD0.glb。两入口仓储版本不同。

## 4 隐藏试放（north13 8 包，activation=false/未激活）

| 包 | 文件 | LOD | SHA256 | 目标/原点 |
|---|---|---|---|---|
| luoyang-kaiyang-gate-study-v1 | `kaiyang-K-LOD1.glb` | 1 | `d82f13fcbadaf5dd` | [2010.4, -21.3] |
| luoyang-kaiyang-gate-study-v1 | `kaiyang-K-LOD2.glb` | 2 | `13ff78a7a1fe9159` | [2010.4, -21.3] |
| luoyang-north-four-courts-v2 | `court-A2-LOD1.glb` | 1 | `d76580bbb5a7c893` | C02-033,C02-034,C02-035,C02-036 |
| luoyang-north-four-courts-v2 | `court-A2-LOD2.glb` | 2 | `4691c63041231344` | C02-033,C02-034,C02-035,C02-036 |
| luoyang-north-four-courts-v2 | `court-B-LOD1.glb` | 1 | `2be52632e16e4329` | C02-033,C02-034,C02-035,C02-036 |
| luoyang-north-four-courts-v2 | `court-B-LOD2.glb` | 2 | `641b05a535a266dc` | C02-033,C02-034,C02-035,C02-036 |
| luoyang-north-four-courts-v2 | `court-B2-LOD1.glb` | 1 | `95b66c5d994cac56` | C02-033,C02-034,C02-035,C02-036 |
| luoyang-north-four-courts-v2 | `court-B2-LOD2.glb` | 2 | `b9651fa3ef9bc449` | C02-033,C02-034,C02-035,C02-036 |
| luoyang-north-perimeter-v1 | `court-TC03-2-LOD1.glb` | 1 | `9003d00a45b48663` | C02-001,C02-002,C02-031,C02-003,C02-004 |
| luoyang-north-perimeter-v1 | `court-TC03-2-LOD2.glb` | 2 | `b8dda6789f4f9dcf` | C02-001,C02-002,C02-031,C02-003,C02-004 |
| luoyang-north-second-row-v1 | `court-A-LOD1.glb` | 1 | `245c20b6385dcee4` | C02-027,C02-028,C02-029,C02-030 |
| luoyang-north-second-row-v1 | `court-A-LOD2.glb` | 2 | `8e098a5f382448c2` | C02-027,C02-028,C02-029,C02-030 |
| luoyang-pingcheng-gate-study-v1 | `pingcheng-P-LOD1.glb` | 1 | `7d995a1b95026cb3` | [1622.81, -13.26] |
| luoyang-pingcheng-gate-study-v1 | `pingcheng-P-LOD2.glb` | 2 | `e6f289f78dc05c2d` | [1622.81, -13.26] |
| luoyang-shangxi-gate-study-v1 | `shangxi-X-LOD1.glb` | 1 | `00a2eb67b73bac04` | [-30.37, 2632.54] |
| luoyang-shangxi-gate-study-v1 | `shangxi-X-LOD2.glb` | 2 | `99047569c6248c99` | [-30.37, 2632.54] |
| luoyang-yong-gate-study-v1 | `yong-Y-LOD1.glb` | 1 | `c277f7e31d764384` | [-16.02, 1397.77] |
| luoyang-yong-gate-study-v1 | `yong-Y-LOD2.glb` | 2 | `7406a24cf7124fcd` | [-16.02, 1397.77] |
| luoyang-zhongdong-gate-study-v1.1 | `zhongdong-Z-LOD1.glb` | 1 | `a78b7c84c1757e94` | [2580.0, 1805.37] |
| luoyang-zhongdong-gate-study-v1.1 | `zhongdong-Z-LOD2.glb` | 2 | `cefa53325287e76d` | [2580.0, 1805.37] |

## 5 家族去重（按家族计，不按 LOD/姿态/附件；qa/family-ledger.json）

| 家族 | 最高状态 | 在城节点 | 资产卡 |
|---|---|---|---|
| 城垣（A 段＋direct 转接段） | 已入城·首屏默认加载 | 12 |  |
| 住宅院落家族（R01-A/B、TC03、A2/B2/TC03-2 变体） | 已入城·首屏默认加载 | 44 | m-courtyard-family |
| 广阳门 | 已入城·首屏默认加载 | 1 | m-luoyang-guangyang-gate |
| 雍门 | 已入城·首屏默认加载 | 2 | m-luoyang-yong-gate |
| 道路与地面（ground-atomic） | 已入城·按章加载（initial=false） | 4 |  |
| 市肆功能组（五店三摊＋N2 替换） | 已入城·按章加载（initial=false） | 2 | m-market-functional |
| 仓储作业组（太仓候选附近） | 已入城·按章加载（initial=false） | 1 | m-storage-functional |
| 开阳门 | 隐藏试放（activation=false） | 0 | m-luoyang-kaiyang-gate |
| 平城门 | 隐藏试放（activation=false） | 0 | m-luoyang-pingcheng-gate |
| 上西门 | 隐藏试放（activation=false） | 0 | m-luoyang-shangxi-gate |
| 中东门 | 隐藏试放（activation=false） | 0 | m-luoyang-zhongdong-gate |
| 旄门 | 仅模型·独立研究视图（cityPlacement=null，城中不渲染） | 0 | m-luoyang-mao-gate |
| 灵台 | 仅模型·独立研究视图（cityPlacement=null，城中不渲染） | 0 | m-luoyang-lingtai |
| 太学长堂（A/B 两方案） | 仅模型·独立研究视图（cityPlacement=null，城中不渲染） | 0 | m-luoyang-taixue-a |
| 八宅三铺街区 A1 | 仅模型（资产卡文件） | 0 | m-luoyang-a1-neighborhood |
| B2门窗开口套件 | 仅模型（资产卡文件） | 0 | m-luoyang-b2-facade-kit |
| 辟雍礼堂与围护 | 仅模型（资产卡文件） | 0 | m-luoyang-biyong |
| 庖厨炉灶 A/B | 仅模型（资产卡文件） | 0 | m-luoyang-cooking-stove |
| 普通院落两种组装 | 仅模型（资产卡文件） | 0 | m-luoyang-court-layout-kit |
| 德阳殿空间研究 | 仅模型（资产卡文件） | 0 | m-luoyang-deyang-hall |
| 夯土墙身家族 | 仅模型（资产卡文件） | 0 | m-luoyang-earthwall-family |
| 足碓与踏台 | 仅模型（资产卡文件） | 0 | m-luoyang-foot-pestle |
| 复道服务登临节点 | 仅模型（资产卡文件） | 0 | m-luoyang-gallery-access |
| 谷门 | 仅模型（资产卡文件） | 0 | m-luoyang-gu-gate |
| 人力石磨 A/B | 仅模型（资产卡文件） | 0 | m-luoyang-hand-mill |
| 住宅主屋面 | 仅模型（资产卡文件） | 0 | m-luoyang-house-roof |
| 低墙生活分区单元 | 仅模型（资产卡文件） | 0 | m-luoyang-household-service |
| 住宅内门修订组件 | 仅模型（资产卡文件） | 0 | m-luoyang-inner-door-components |
| 津门 | 仅模型（资产卡文件） | 0 | m-luoyang-jin-gate |
| 八铺四棚店前线 | 仅模型（资产卡文件） | 0 | m-luoyang-market-frontage |
| 市肆模块与组装 | 仅模型（资产卡文件） | 0 | m-luoyang-market-modular-assembly |
| 明堂形制假说 | 仅模型（资产卡文件） | 0 | m-luoyang-mingtang |
| 北郊方坛四陛 | 仅模型（资产卡文件） | 0 | m-luoyang-northern-altar |
| 普通住屋与门房四型 | 仅模型（资产卡文件） | 0 | m-luoyang-ordinary-house-types |
| 无名宫院通行组合 | 仅模型（资产卡文件） | 0 | m-luoyang-palace-admission-court |
| 高架复道局部模块 | 仅模型（资产卡文件） | 0 | m-luoyang-palace-gallery |
| 宫门值守核验切片 | 仅模型（资产卡文件） | 0 | m-luoyang-palace-guard |
| 宫前土木对阙 | 仅模型（资产卡文件） | 0 | m-luoyang-palace-paired-que |
| 宫廷侧廊庑 | 仅模型（资产卡文件） | 0 | m-luoyang-palace-sidehall |
| 宫墙水道三段接口 | 仅模型（资产卡文件） | 0 | m-luoyang-palace-waterway-interface |
| 连续住宅生活片区 | 仅模型（资产卡文件） | 0 | m-luoyang-residential-life |
| 院内备食关系 | 仅模型（资产卡文件） | 0 | m-luoyang-residential-preparation |
| 圈厕关系 A | 仅模型（资产卡文件） | 0 | m-luoyang-service-court |
| 上东门 | 仅模型（资产卡文件） | 0 | m-luoyang-shangdong-gate |
| 南郊圆坛八陛 | 仅模型（资产卡文件） | 0 | m-luoyang-southern-altar |
| 厩棚与饲槽 A/B | 仅模型（资产卡文件） | 0 | m-luoyang-stable |
| 太学门外观经空间 | 仅模型（资产卡文件） | 0 | m-luoyang-stoneclassic-access-court |
| 砖瓦窑 A/B | 仅模型（资产卡文件） | 0 | m-luoyang-tile-kiln |
| 墙房相接住宅样例 | 仅模型（资产卡文件） | 0 | m-luoyang-wall-house-court |
| 开敞作业棚与足碓院 | 仅模型（资产卡文件） | 0 | m-luoyang-workyard-shed |
| 武库收纳与点验 | 仅模型（资产卡文件） | 0 | m-luoyang-wuku |
| 夏门 | 仅模型（资产卡文件） | 0 | m-luoyang-xia-gate |
| 小苑门 | 仅模型（资产卡文件） | 0 | m-luoyang-xiaoyuan-gate |
| 玉堂前后殿关系 | 仅模型（资产卡文件） | 0 | m-luoyang-yutang-halls |

计数：已入城·首屏默认加载 4；已入城·按章加载（initial=false） 3；隐藏试放（activation=false） 4；仅模型·独立研究视图（cityPlacement=null，城中不渲染） 3；仅模型（资产卡文件） 40；合计 54 个家族。

## 6 重复、被替代与失败版本的去向

- **同家族重复展示**（F-gate-yong）：雍门已以 yong-Y-LOD0＋yong-apron 在城中首屏加载；城墙章仍列出“雍门 · 研究候选”，研究视图状态文字为“城市位置尚未配准”（运行实测）。旧 north13 雍门试放包 activation=false。 → 按同家族旧档/低档记账，不另计门数；建议 LY-100 合并时把 research-north13-yong-Y 标为“已入城同家族·旧研究档”或撤出 walls.researchModelIds。
  - `cities/luoyang/progress-assets/flat/study-north13-yong-Y-1983dab58385.glb` 144900 B `1983dab583853beb`
  - `cities/luoyang/progress-assets/north13-gates/luoyang-yong-gate-study-v1/models/yong-Y-LOD1.glb` 501844 B `c277f7e31d764384`
  - `cities/luoyang/progress-assets/north13-gates/luoyang-yong-gate-study-v1/models/yong-Y-LOD2.glb` 58612 B `7406a24cf7124fcd`
- **被替代版本（仅旧版 v1 入口仍载）**（F-storage）：当前入口 storage-main=granary-city-LOD0.glb；v1 ?mode=west 太仓视图运行实测仍请求旧 storage-group-organized.glb。 → 保留为 v1 归档原字节，不作为当前仓储输入；新生产只读 granary-city-v1。
  - `cities/luoyang/assets/storage/storage-group-organized.glb` 1786124 B `b8482824513a101d`
- **未加载的同家族中远档**（F-storage）：城中只装 LOD0（完整近档），无远档切换；LOD1/2 只在 source.json 记录。 → 同家族 LOD，不计家族；是否接远档由 LY-100/资源审计决定。
  - `cities/luoyang/progress-assets/granary-city-v1/granary-city-LOD1.glb` 756484 B `a1265bbf53d10ddb`
  - `cities/luoyang/progress-assets/granary-city-v1/granary-city-LOD2.glb` 462440 B `6b2564d3ffd76e6e`
- **被替代版本（仅合同/旧接口记录）**（F-gate-guangyang）：只出现在 data/west/guangyang-replacement-contract.json；当前城中广阳门为 city-wall/direct/gate-body-only.glb。 → 历史替换前版本，只读归档，不作输入。
  - `cities/luoyang/assets/west/guangyang-C-form.glb` 1142756 B `717f6562187ffde3`
- **被替代版本（v1/合同引用）**（F-citywall）：当前城中 08/09 两段用 direct/wall-08、direct/wall-09（广阳 direct 转接）；A 版 08/09 只见于 city-wall-interface-original 与 guangyang-replacement-contract。 → 只读归档。
  - `cities/luoyang/assets/city-wall/A/wall-08.glb` 2956 B `b18cde3efacdd32e`
  - `cities/luoyang/assets/city-wall/A/wall-09.glb` 1736 B `b83e221200e54812`
- **备选方案（未入城）**（F-citywall）：B 组 12 段只被 city-wall-interface(-original).json 引用，当前入口不加载。 → 同家族备选，不计家族；不得与 A 叠载。
  - `cities/luoyang/assets/city-wall/B/wall-00.glb` 2388 B `16a296210c132098`
  - `cities/luoyang/assets/city-wall/B/wall-01.glb` 2732 B `91eefa47f86de7a2`
  - `cities/luoyang/assets/city-wall/B/wall-02.glb` 2056 B `b363a1155d1d278e`
  - `cities/luoyang/assets/city-wall/B/wall-03.glb` 2056 B `1770a24388299e51`
  - `cities/luoyang/assets/city-wall/B/wall-04.glb` 2908 B `7c7c4df9c9d7e715`
  - `cities/luoyang/assets/city-wall/B/wall-05.glb` 1716 B `c84cb71d45dd3c66`
  - `cities/luoyang/assets/city-wall/B/wall-06.glb` 1720 B `57ff3b4556e58f2c`
  - `cities/luoyang/assets/city-wall/B/wall-07.glb` 1720 B `8591bacfe7102408`
  - `cities/luoyang/assets/city-wall/B/wall-08.glb` 2924 B `53384c08e388a6ea`
  - `cities/luoyang/assets/city-wall/B/wall-09.glb` 1724 B `626b1812c0d04b5d`
  - `cities/luoyang/assets/city-wall/B/wall-10.glb` 1728 B `47994da901ebccb7`
  - `cities/luoyang/assets/city-wall/B/wall-11.glb` 2732 B `9f0a8fffa8157e46`
- **v1 专用环境/接入件**（F-courtyard）：只在旧版 v1 入口使用（C02 四簇视图运行实测请求 C02-environment/D08-environment/access-D08）；当前入口改由 ground-atomic 地面承担。其中 d08/D08-environment.glb 与城中按章加载的 ground-atomic/D08.glb 逐字节相同（同一文件两处路径）。 → 只读归档，不计家族。
  - `cities/luoyang/assets/c02v/C02-environment.glb` 326588 B `8c9d2028a346852a`
  - `cities/luoyang/assets/c02/C02-environment.glb` 41704 B `4185c082f86aa8a9`
  - `cities/luoyang/assets/d08/D08-environment.glb` 6664 B `3ab933108b88c5c3`
  - `cities/luoyang/assets/d08/access-D08.glb` 2044 B `ec674a1ef3372576`
  - `cities/luoyang/assets/c01/access-C.glb` 2064 B `ce265e891c32d2fa`
  - `cities/luoyang/assets/r01/district-environment.glb` 8520 B `dc528a33b8b5d65d`
- **v1 专用道路件**（F-ground-road）：当前入口不加载；被 v1 west-layer 或 data/west 合同引用。main-roads/corridor-6m 与 road-junction/corridor-6m 同为 6832 字节但 SHA 不同，是两份文件。 → 只读归档，不计家族。
  - `cities/luoyang/assets/road-junction/joined-route-terrain.glb` 4408140 B `f872935883fc6b4e`
  - `cities/luoyang/assets/market/corridor-6m-market-link.glb` 8272 B `b46dd450d7e8636b`
  - `cities/luoyang/assets/market/flowB-routes.glb` 9344 B `43d7799f85feccb0`
  - `cities/luoyang/assets/main-roads/corridor-6m.glb` 6832 B `17f3219792c90d9f`
  - `cities/luoyang/assets/main-roads/corridor-10m.glb` 6468 B `bd79de9518a706e3`
  - `cities/luoyang/assets/road-junction/corridor-6m.glb` 6832 B `d047e206ed331c36`
  - `cities/luoyang/assets/west/route-corridor.glb` 4292780 B `ec883eaff95f335e`
- **字节重复副本**（C:m-luoyang-palace-admission-court）：城目录 progress-assets 下 6 个 GLB 与资产卡 library/models/m-luoyang-palace-admission-court/files 下同名文件逐字节相同；任何城市入口都不加载。 → 按 1 个家族、1 份资产计；城目录副本标为冗余（是否删除由 LY-100/协调者定，本席位不改）。
  - `cities/luoyang/progress-assets/palace-admission-court/palace-admission-court-closed-LOD0.glb` 2578388 B `6ea892982b46e554`
  - `cities/luoyang/progress-assets/palace-admission-court/palace-admission-court-closed-LOD1.glb` 1126500 B `455a12153d4132d2`
  - `cities/luoyang/progress-assets/palace-admission-court/palace-admission-court-closed-LOD2.glb` 278616 B `108e28a567dcef23`
  - `cities/luoyang/progress-assets/palace-admission-court/palace-admission-court-open-LOD0.glb` 2578472 B `59c8b758a5a25231`
  - `cities/luoyang/progress-assets/palace-admission-court/palace-admission-court-open-LOD1.glb` 1126584 B `d95bd22f9317683e`
  - `cities/luoyang/progress-assets/palace-admission-court/palace-admission-court-open-LOD2.glb` 278700 B `01b2017fac9d8ee6`
- **非城市入口的质量参照**（none）：v1 shell.mjs 质量参照（孙吴陶院落释读，非东汉洛阳）。 → 只读，不计入洛阳家族。
  - `cities/luoyang/assets/quality-reference-013-A.glb` 293452 B `f7dc654269259ec8`

### 6.1 既有全库体检标出的问题（mq 卡片 audit.json，SHA 与当前提交字节逐一比对）

- m-luoyang-a1-neighborhood `library/models/m-luoyang-a1-neighborhood/files/A1-v3-LOD1.glb` `e7ccf822ab1cc4fd` 体检 SHA 一致：['EXT_REQUIRED:EXT_meshopt_compression']
- m-luoyang-wuku `library/models/m-luoyang-wuku/files/wuku-B-LOD0.glb` `e5de60b6ff972e6b` 体检 SHA 一致：['DEGENERATE_TRIS:14']
- m-luoyang-wuku `library/models/m-luoyang-wuku/files/wuku-B-LOD1.glb` `5e1cc6b99bb81c62` 体检 SHA 一致：['DEGENERATE_TRIS:14']
- m-luoyang-wuku `library/models/m-luoyang-wuku/files/wuku-B-LOD2.glb` `e5c8730605f39fb3` 体检 SHA 一致：['DEGENERATE_TRIS:14']
- m-gate-roof-study `model-library/assets/gate-roof.glb` `8bf9b4160718fce5` 体检 SHA 一致：['HIGH_DRAWCALLS:342']
- m-gate-roof-study `model-library/assets/gate-near-local.glb` `fcdfe870b7b7ee1c` 体检 SHA 一致：['HIGH_DRAWCALLS:342']
- m-gate-roof-study `model-library/assets/gate-middle-local.glb` `250fddbde01322a3` 体检 SHA 一致：['HIGH_DRAWCALLS:342']
- m-market-functional `model-library/assets/market-A-N2-local.glb` `493798b8f09f594b` 体检 SHA 一致：['HIGH_DRAWCALLS:554']
- m-market-functional `cities/luoyang/assets/market/market-cluster.glb` `77b8bf2e9e1488df` 体检 SHA 一致：['HIGH_DRAWCALLS:500']（此文件在城中按章加载）

### 6.2 字节重复 GLB

- `3ab933108b88c5c3`：`cities/luoyang/assets/d08/D08-environment.glb`；`cities/luoyang/assets/ground-atomic/D08.glb`
- `6ea892982b46e554`：`cities/luoyang/progress-assets/palace-admission-court/palace-admission-court-closed-LOD0.glb`；`library/models/m-luoyang-palace-admission-court/files/palace-admission-court-closed-LOD0.glb`
- `455a12153d4132d2`：`cities/luoyang/progress-assets/palace-admission-court/palace-admission-court-closed-LOD1.glb`；`library/models/m-luoyang-palace-admission-court/files/palace-admission-court-closed-LOD1.glb`
- `108e28a567dcef23`：`cities/luoyang/progress-assets/palace-admission-court/palace-admission-court-closed-LOD2.glb`；`library/models/m-luoyang-palace-admission-court/files/palace-admission-court-closed-LOD2.glb`
- `59c8b758a5a25231`：`cities/luoyang/progress-assets/palace-admission-court/palace-admission-court-open-LOD0.glb`；`library/models/m-luoyang-palace-admission-court/files/palace-admission-court-open-LOD0.glb`
- `d95bd22f9317683e`：`cities/luoyang/progress-assets/palace-admission-court/palace-admission-court-open-LOD1.glb`；`library/models/m-luoyang-palace-admission-court/files/palace-admission-court-open-LOD1.glb`
- `01b2017fac9d8ee6`：`cities/luoyang/progress-assets/palace-admission-court/palace-admission-court-open-LOD2.glb`；`library/models/m-luoyang-palace-admission-court/files/palace-admission-court-open-LOD2.glb`

### 6.3 未找到

- 被停用的 31 组重复宫殿：在 bce3211 的仓库内容与历史中没有找到对应文件、资产卡或清单；不在本快照内，无法逐条落账。

## 7 合同 SHA 的换行依赖

| 合同 | 声明 | 提交字节 | 检出字节 | 依据 |
|---|---|---|---|---|
| `data/far44/instances-calt.json` | `c830b4e37090` | `e39fdafb016c` | `c830b4e37090` | 仅Windows检出字节(CRLF) |
| `data/far44/preflight-contract.json` | `90dfa0774643` | `c9aafa7d2210` | `90dfa0774643` | 仅Windows检出字节(CRLF) |
| `data/west/city-wall-interface.json` | `ad18cc659157` | `ca75d115d49d` | `ad18cc659157` | 仅Windows检出字节(CRLF) |
| `data/west/ground-atomic-contract.json` | `bfc7fc83c3d8` | `7f26720bf40f` | `bfc7fc83c3d8` | 仅Windows检出字节(CRLF) |
| `data/west/N2-contract.json` | `10678d73111a` | `498f51fcd072` | `10678d73111a` | 仅Windows检出字节(CRLF) |
| `data/west/market-interface.json` | `31c6786db03b` | `2957184accc8` | `31c6786db03b` | 仅Windows检出字节(CRLF) |
| `data/west/storage-interface.json` | `b910896799cd` | `4f3ccae9891c` | `b910896799cd` | 仅Windows检出字节(CRLF) |
| `data/evidence/evidence-geometry.json` | `662562fa87cf` | `fa8b7002869e` | `662562fa87cf` | 仅Windows检出字节(CRLF) |
| `data/evidence/stage-contract.json` | `6ade3f6e62c4` | `3227460643f5` | `6ade3f6e62c4` | 仅Windows检出字节(CRLF) |
| `progress-assets/north13-gates/source.json` | `9b07b7349ef5` | `dc1699009802` | `9b07b7349ef5` | 仅Windows检出字节(CRLF) |
| `progress-assets/mao-gate/source.json` | `9b3a40273182` | `95589c004a93` | `9b3a40273182` | 仅Windows检出字节(CRLF) |
| `progress-assets/taixue-A-v3.2/source.json` | `5f2a8078e2fa` | `535e10ae94ef` | `5f2a8078e2fa` | 仅Windows检出字节(CRLF) |
| `progress-assets/flat/source.json` | `ddd1445c1ddd` | `ddd1445c1ddd` | `f2734dd41fd5` | 提交字节(LF) |
