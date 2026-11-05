| 席位 | 名称 | 类型 | 规模 | G 后可开工 | 复用判定 | 关键缺件（G 交付物之外） |
|---|---|---|---|---|---|---|
| LY-011 | 开阳中门道承托框架修订 | 补件/修订 | M | **否** | 新做 | bearing-section-v1. This is the failed support sample itself. It is needed to locate what is being replaced and to provi |
| LY-012 | 开阳门框门叶兼容子件 | 补件/修订 | M | 是 | 新做 | bearing-section-v1：中门道承托剖面和门框安装面。lab bce3211、origin/luoyang-content、creation-notebook、review、待传目录都找不到；没有公开 GLB，不能从 GLB 重 |
| LY-013 | 开阳单一楼板与木土接口 | 补件/修订 | M | 是 | 复用候选 | bearing-section-v1: not in lab main, the luoyang-content/reviews/workpacks branches or 待传. Needed to find the 'new deck' |
| LY-014 | 开阳登临与墙顶过渡 | 补件/修订 | L | 是 | 新做 | bearing-section-v1：LY-011 承托剖面的输入，我要用它确认最终楼面和梁的位置。lab 的 main/luoyang-content/reviews/workpacks 四个分支、creation-notebook-待传 |
| LY-015 | 开阳完整门组局部装配 | 复用装配 | L | 是 | 新做 | bearing-section-v1：任务池点名的失败承托样例，用于定位旧门楣/梁 0.0936m³ 交体和 LY-011 的替换对象；main bce3211、origin/luoyang-content、creation-noteboo |
| LY-016 | 平城侧门通口完整地面 | 补件/修订 | M | 是 | 复用候选 | 地面附件的源包（生成器、.blend、原来那套 3114 样点检查器和它的报告）。用途：逐字重现卡片写的「565/3114 依赖旧路」，以及在原生源上做修订。几何能从 GLB 重建：LOD2 就是 6 个盒体，三档占地一致；新增件本来就做成 |
| LY-017 | 平城门墙旧路联合装配 | 复用装配 | M | 是 | 新做 | Mother eabb2a90 city-C032-wuku-facade.blend (base of the P-v1 hidden trial). Not in the repo. For gate-area contacts it  |
| LY-018 | 谷门门墩接地与墙端适配 | 补件/修订 | M | 是 | 复用候选 | city-C032-entry-LOD0.blend（sha256 1e8c4d2c…b01b，私密母版）。用途：核对 2505 个隐藏 placement 里有没有谷门其他试放。不能从 GLB 重建，只能用公开 visibility.js |
| LY-019 | 夏门接缝与底部支承修订 | 补件/修订 | M | 是 | 复用候选 | B-library-v1 LOD0 GLB (16,054,944 B, private, not on card): needed for the near-tier seam and ground check. LOD1 and LOD |
| LY-020 | 城垣转角与坡地脚接口族 | 补件/修订 | S | 是 | 复用候选 | earthwall family native source (.blend / generator + params). Purpose: a family-consistent Shangdong stub (rammed-layer  |
| LY-021 | 八铺门前起步踏步组件 | 补件/修订 | M | 是 | 新做 | Frontage v2.1 private source (.blend or generator). Needed for per-shop and per-counter node identity, because the GLB m |
| LY-022 | 市肆前街连续地坪接口 | 补件/修订 | S | 是 | 复用候选 | city-C032-entry-LOD0.blend (sha 1e8c4d2c...b01b), the mother scene that placed 店前线v2.1 + well + ground at +0.20. It woul |
| LY-023 | 棚摊基础与可拆脚端适配 | 补件/修订 | S | 是 | 复用候选 | LY-022's selected ground for the frontage street. It is not a formal dependency of LY-023, but without it the frontage s |
| LY-024 | 一类铺型闭铺构件试案 | 补件/修订 | M | 是 | 新做 | S84/S86 v1.1-entry-repair native .blend, generator and parameters: needed for native/GLB consistency and exact ports. Th |
| LY-025 | 市肆井和开孔地面原子包 | 复用装配 | M | 是 | 复用候选 | city-C032-entry-LOD0.blend（SHA 1e8c4d2c…3b01b）母版：用来追溯开孔地面的原生切孔操作；可以从 GLB 重建（分块里已有精确几何：sample_ground 外框 + r0.59、48段孔） |
| LY-026 | 井架操作构件兼容检查与修订 | 补件/修订 | S | 是 | 复用候选 | well-study source/ (build.py, check.py, check-contacts.py, check-local-booleans.py) + manifest.json. Needed to regenerat |
| LY-027 | 铺内货架与货物占位兼容包 | 复用装配 | M | 是 | 复用候选 | v2.1八铺四棚私密源包(.blend/生成器)与72段入口包络QA定义：用来给悬空三层板补支承、判断设计意图；占位可以作独立叠加件从GLB重建，改源件不行 |
| LY-028 | 市肆卸货与棚下操作地面 | 补件/修订 | S | 是 | 复用候选 | City master C032 source .blend (sourceMasterSHA256 1e8c4d2c..., not in the repo). Only needed if LY-006 asks for a pad o |
| LY-029 | 八铺四棚候选的互斥与回退包 | 复用装配 | L | 是 | 新做 | F（店前线 v2.1）的私密源包（.blend 或生成器加参数）：要靠它拿到单铺、单棚的节点身份。从 GLB 只能在整套层面重建：GLB 是 3 个按材质合并的网格；分块里的落位等于库件 LOD0 平移 (214.286, 0.2, −19 |
| LY-030 | 完整市肆区域局部交付 | 复用装配 | L | 是 | 复用候选 | city-C032-entry-LOD0.blend 1e8c4d2c...3b01b (native of C_MARKET_WELL_ATOMIC_TRIAL): editable source of the frontage + we |
| LY-031 | 太仓A门扇枢接子件 | 补件/修订 | M | 是 | 新做 | 太仓v2原生.blend与私密 'granary city composer v1' 生成器：用途是可编辑旧墙/门楣；本项不改旧体，门件可按GLB实测端口从GLB重建，不阻断 |
| LY-032 | 太仓B门扇枢接子件 | 补件/修订 | M | 是 | 新做 | granary v2 / 城景合成器 v1 的私密原生源与生成、验证源（.blend / 源 ZIP）：原本用来编辑 B 门间、复跑原检查。可以从 GLB 重建：B 仓体是轴对齐方块，已精确实测；门件是新增几何，不需要重写仓体。交付时须标「 |
| LY-033 | 两仓启闭与搬运联合包 | 复用装配 | M | 是 | 新做 | LY-031 A 门件、LY-032 B 门件（三档 × 开/闭）：都还没有工作包。这是本项要装的件，不能从 GLB 重建，只能由这两个席位交件 |
| LY-034 | 收货核验前场接口重绑定 | 复用装配 | S | 是 | 复用候选 | 私密原生 .blend 和「Luoyang private granary city composer v1」生成与校验源（source.json 注明在仓库外）。用途：命名子件、作者端口。对本项可以从 GLB 重建：端口、支持、指纹已从  |
| LY-035 | 仓前有限搬运与暂存变体 | 补件/修订 | M | 是 | 新做 | granary-city-v1 私密原生工程与 composer/验证源（source.json 写明不在仓库）：用于按原生层级编辑合并网格。本项只新增附加件、不改原件，参照几何可以从 GLB 重建（已实测），不阻断 |
| LY-036 | 武库B外围支持地坪包 | 补件/修订 | M | 是 | 新做 | B v2.2 native .blend + generator + private QA report (point list of 'outer-arrival support missing'): used for the autho |
| LY-037 | 武库B台前侧棚接续包 | 补件/修订 | S | 是 | 复用候选 | wuku-B v2.2 native .blend + generator + private route QA (declared body envelope, route polylines, mid-angle list): need |
| LY-038 | 武库A备选安装契约 | 复用装配 | M | 是 | 新做 | 武库 A/B 原生 .blend 和源 ZIP：用作可编辑源和原生/GLB SHA 对；本项只装矩阵、不动 A 字节，所以可以从 GLB 直接装，不需要重建 |
| LY-039 | 东北既有196米C路重绑定 | 复用装配 | S | 是 | 复用候选 | city-C032-entry-LOD0.blend (private mother .blend, SHA 1e8c4d2c...). Needed for: the native C_NE_APPROACH_LOCAL object,  |
| LY-040 | 仓储武库功能区局部装配 | 复用装配 | M | 是 | 复用候选 | private mother city-C032-entry-LOD0.blend (1e8c4d2c…): native parameters of C_NE_APPROACH_LOCAL and C_WUKU_ISOLATED_SUPP |
| LY-041 | 示范住宅地基与地坪适配 | 补件/修订 | S | 是 | 复用候选 | A2 原型的原生源（.blend 或生成器）：仓库里没有。只有确实要新造地脚时才用得上；几何是简单闭合盒体，可以从 GLB 重建。按实测结论是复用，不需要它。 |
| LY-042 | 住宅内门修订接回原院 | 复用装配 | M | **否** | 复用候选 | A2 原型原生源：仓库里没有。用途：做 C02-010 专用派生宿主，把旧叶 timber#5、#13 拆成独立节点。可以从 GLB 重建：按岛拆分 architecture_C_plain_timber.001，其余 15 岛用逐岛指纹证 |
| LY-043 | 住屋与院墙端接组件 | 补件/修订 | S | 是 | 复用候选 | 院落原型（r01、c02v、d08）的原生 .blend 或生成器：仓库里没有。只有确实要新造端接件时才用得上。可以从 GLB 重建：城景原型 earth、plinth、timber 的三角 100% 是精确的轴对齐闭合盒体（A2 有 52 |
| LY-044 | 备食与灶体院内接地包 | 复用装配 | S | 是 | 新做 | W2 placement QA package (14 routes, 2 fixed-orientation work positions, 2 turn-back bays, 65 protected routes, wrong-wor |
| LY-045 | 圈厕与真实地面开口包 | 复用装配 | M | 是 | 新做 | 圈厕关系 A native source (.blend/generator/batch source ZIP): only needed if service-A geometry changed (it must not) or for |
| LY-046 | 住宅门前与檐下排水试片 | 补件/修订 | M | 是 | 复用候选 | LY-041 冻结的选院与地坪差异件：用来确定试片在哪个院、落在什么地坪上 |
| LY-047 | 住宅储藏与棚下安装变体 | 复用装配 | M | 是 | 复用候选 | R01-B 和 B2 原型的原生源（.blend 或生成器；合同里 B 的 source_sha256 是 65e4e69b…）：仓库里没有。只有在 LY-010 要求把 B 院原位棚改成可单独卸载、替换时才用得上，用来把棚件从全院共用节点 |
| LY-048 | 住宅服务口与边界闭合 | 补件/修订 | M | **否** | 复用候选 | 6 个院落原型的原始源 GLB/.blend（preflight 记了 source_sha256，如 A2 LOD1 98257941…）。用途：在原生工程里开侧口、加门槛或门叶。能从 GLB 重建：差异件按原型同一原点、米制、Y-up  |
| LY-049 | 院门至巷道边缘端口包 | 补件/修订 | S | 是 | 复用候选 | LY-041 院坪基准、LY-042 门叶互斥清单、LY-048 service-opening 端口（主门是否加门槛/门叶/关闭态）都只有 prep，未交付 |
| LY-050 | 示范院完整生活组装 | 复用装配 | M | 是 | 新做 | 041–049 的交付包（models/、assembly.json、delivery-manifest.json）：组装的全部原料，现在只有 prep。不能从 GLB 重建，这些是别的席位的产物，必须等交付 |
| LY-051 | 厩棚系留与分栏配件 | 补件/修订 | M | 是 | 新做 | stable A/B native .blend + source ZIP (not in repo): editable host geometry/params; NOT needed for the kit, which is a s |
| LY-052 | 厩棚操作地面与槽前接口 | 补件/修订 | M | 是 | 新做 | native .blend / generator params for stable A/B (private source package): used to keep floor deltas in the same parametr |
| LY-053 | 砖瓦窑坑位与基底包 | 补件/修订 | M | 是 | 新做 | Kiln native source (.blend/generator/source ZIP): not in the repo or anywhere under D:/GitHub. It would be used to re-ex |
| LY-054 | 窑前作业与暂存地面 | 补件/修订 | M | 是 | 新做 | 窑 A/B 的原生 .blend 或生成器：仓库里没有。用途是作为与窑对齐的前地面件的可编辑源。可以从 GLB 重建：前区节点都是轴对齐盒体，平面坐标已从 GLB 实测 |
| LY-055 | 人力石磨安装与操作台脚 | 复用装配 | M | 是 | 新做 | Hand-mill native .blend / generator + parameters. Not in the lab repo, not in creation-notebook-待传 (only 说明.txt), not in |
| LY-056 | 足碓踏台连续支承包 | 复用装配 | M | 是 | 复用候选 | foot-pestle native .blend / generator (private source pack). It is the editable source for future revisions. The reuse a |
| LY-057 | 原谷物院屋面缺陷修订 | 补件/修订 | M | **否** | 复用候选 | 原谷物加工院 original model. Searched every lab ref, the other repos and D:, found nothing; git history has only one version o |
| LY-058 | 谷物院扬谷暂存通路包 | 复用装配 | M | **否** | 新做 | 原谷物加工院的三档 GLB、原生源（.blend 或源 ZIP）和缺陷记录（瓦落座、行缝、承件）。用途：本项要复用的院体、作业区和旧地坪。查过 lab 全部分支、creation-notebook、review、modeling-lab 和 |
| LY-059 | 作坊围界与服务口补件 | 补件/修订 | M | 是 | 复用候选 | 「原谷物加工院」及其缺陷记录：仓库内中文（谷物/加工院/扬谷）和英文（grain/threshing/winnow）搜索都是 0 命中。如果 010 选它，需要它的院框、门位、地坪和缺陷清单。院框若与 court-B/R01-B 相同，可以 |
| LY-060 | 作业设施区局部交付 | 复用装配 | L | 是 | 新做 | LY-051..059 九个前置包的交付物（models/、assembly.json、qa/、delivery-manifest）：目录里仍然只有 prep/。LY-060 的装配输入全部来自这里，不能用 GLB 代替 |
| LY-061 | 无名候入院外围墙体 | 补件/修订 | M | 是 | 新做 | luoyang-palace-admission-court-v1.zip（私密源包）。内容：native/*.blend（LOD0 932ec511）、builder d4cd1cc4、config 9de34dcc、lock 54837 |
| LY-062 | 候入院侧口与工作口关闭件 | 补件/修订 | M | **否** | 新做 | LY-061 交付物：admission-court:enclosure:wall-end 端口值、墙厚与墙高、侧口和南口两侧墙端几何。这是侧口门框贴合的必需前件；现在只有 prep，墙还不存在，不能从 GLB 重建 |
| LY-063 | 侧廊端部转折安装模块 | 补件/修订 | M | 是 | 新做 | sidehall-A native .blend + generator/params (entry-step revision source pack): use = authoring end modules on native col |
| LY-064 | 成对阙前庭接地接口 | 补件/修订 | M | 是 | 新做 | Possible local forecourt combination in the private delivery package. The que card note says 局部前庭组合不代表全城激活, but git grep |
| LY-065 | 殿堂侧后台缘与维护接口 | 补件/修订 | M | **否** | 新做 | deyang A/B 原生 .blend、生成器与参数（私密，不在仓库）：用于 native/ 源交付。原型是 keep，不需要改；新件是独立节点，原型 GLB 原样引用，所以装配可以从 GLB 重建，并如实写明不是原件 |
| LY-066 | 玉堂关系组可安装副本 | 复用装配 | S | 是 | 复用候选 | yutang v2.0.0 的私密原生源（.blend、生成器、参数；节点 extras 记 version 2.0.0），以及同名源 Release（提交 52fceaa 自述待补）。用途：核对「屋顶端部旧修订」具体改了什么；如果 LY- |
| LY-067 | 复道A柱脚地面适配 | 补件/修订 | M | 是 | 新做 | Old record of the unsupported post feet: the original list of the 16 support points that missed the ground, with rays, c |
| LY-068 | 复道B层高登临兼容件 | 补件/修订 | M | 是 | 新做 | 复道A/B与登临节点的私密源包（.blend、生成器、原生QA）：用于原生三角对账、构件命名与参数沿用。lab 全分支历史、modeling-lab/review-batches 全部 ZIP、D:/GitHub 下 creation-no |
| LY-069 | 复道端部宫门廊口兼容包 | 复用装配 | M | **否** | 新做 | 复道A/B 与登临A 的私密原生源包（.blend、源 ZIP、生成器参数）。用途：核对端梁伸到 x=6.17、柱础在 dx=6.0 重叠 0.00275 m³ 是不是设计意图，并取原拟 A↔登临装配矩阵。几何已从 GLB 重测，可以「从  |
| LY-070 | 宫院复道局部整合包 | 复用装配 | L | 是 | 新做 | m-luoyang-palace-gallery 的私密原生源包（6 个 .blend、生成器、参数、原 QA 脚本），仓库里没有登记包名，卡片只写「源文件 Release 待单独补齐」。用途：复跑原楼板支持、2 m 头部射线、2.2 m  |
| LY-071 | 辟雍礼堂围护装配契约 | 复用装配 | M | 是 | 复用候选 | 私密母版 city-C032-entry-LOD0.blend（声明 SHA 1e8c4d2c…）。用途：作为试配变换的原生来源，并确认隐藏 placement 库里有没有别的辟雍候选。能从 GLB 重建：本项只需要变换，已用导出分块加公开 |
| LY-072 | 辟雍跨水通道试案 | 补件/修订 | M | **否** | 新做 | LY-071 frozen transform, enclosure version and filled biyong:hall-enclosure:ground port (inner port values). Measurement |
| LY-073 | 辟雍岸缘与外侧地面 | 补件/修订 | M | **否** | 新做 | 城市母版 city-C032-entry-LOD0.blend（SHA 1e8c4d2c…）：用途是核对岛/水符号/跨水板原生参数、生成器和原节点矩阵；不在仓库。本项是新件，可以从 GLB 实测外沿、开口、端头重建边界，不需要原件 |
| LY-074 | 明堂四侧入口外到达地面 | 补件/修订 | M | 是 | 新做 | 明堂 A/B 原生源（.blend/生成器/源ZIP）：只有协调者要求把地面并进明堂导出时才用得上，用来证明原生=GLB。本席位方案是独立节点，原 GLB 不动，所以不需要，也不必「从GLB重建」——阶脚线已从 GLB 顶点精确读出 |
| LY-075 | 明堂九房完整内部安装检查 | 复用装配 | S | 是 | 复用候选 | 明堂原生源工程（.blend、生成器、源 ZIP）：仓库、creation-notebook-待传、review 副本里都没有。原件的用途是：万一要做差异件，可以保持原拓扑、UV 和材质。本项检查全部从 GLB 回读，不需要原件；将来如果真 |
| LY-076 | 灵台未修台缘与绕行补件 | 补件/修订 | M | 是 | 新做 | Private source pack for the five-step revision: the LOD0 near GLB (26,176,944 B according to the card), its .blend and g |
| LY-077 | 太学A门外到达接口 | 补件/修订 | S | 是 | 复用候选 | Native city mother .blend, sha 1e8c4d2ce198 (private), holding node C_TAIXUE_ISOLATED_SUPPORT_PATCH. Needed for two thin |
| LY-078 | 太学观经空间外围安装包 | 复用装配 | M | **否** | 新做 | 私密源 private deterministic source/build.py（Blender 4.3.2，GLB generator 字段所写）：用于参数化再生成（柱距、门宽）和原生出处；几何/UV/材质可从GLB无损重建（顶点不焊接 |
| LY-079 | 南郊圆坛八陛接地包 | 复用装配 | M | 是 | 复用候选 | 私密源包 south-altar A/B（.blend、生成器、参数）和卡片提到的旧 qa 报告：只有改几何（补 LOD2、阶足切地）时才需要。本包不改坛，所以不需要；以后真要用，也只能标「从GLB重建」 |
| LY-080 | 北郊方坛四陛接地包 | 复用装配 | S | 是 | 复用候选 | 私密源 config/altar.json（GLB 中 scene.extras.sourceConfig），以及生成器或 .blend。用途：原参数与可编辑源。本项不改几何，所以不是必需。能从 GLB 完全重建：几何全部轴对齐，参数已实测 |
| LY-081 | 建立实际地面可达网络 | 考据/契约 | M | 是 | 新做 | Native .blend of C-ground-stitch-v1 (network/retained/south/D08). Not in the repo, but NOT required: this seat must read |
| LY-082 | 示范住宅外巷短接续 | 补件/修订 | S | 是 | 复用候选 | LY-049：填出端口 C02-010:gate-boundary:road-end v1 的 local/world 数值。registry 已声明这个端口，院界也已定在世界 z -806.45，但数值仍是 null |
| LY-083 | 市肆外街真实接点补件 | 补件/修订 | S | 是 | 复用候选 | LY-030 frozen market boundary + retained exit list: decides whether route_exitN/exitS are real exits needing outside sup |
| LY-084 | 东北功能区对外连接候选 | 考据/契约 | S | 是 | 新做 | 「既有三条长接路规划」: not in lab repo, git history, mother visibility list (2958 meshes / 27 collections) or D:/GitHub; plans can |
| LY-085 | 平城开阳城南端接路线 | 补件/修订 | M | 是 | 复用候选 | Mother city-C032-entry-LOD0.blend 1e8c4d2c... (left out of the handoff, per its README): needed to install and roll back |
| LY-086 | 宫墙三段水道安装接口 | 复用装配 | M | 是 | 复用候选 | Private native source (.blend / generator 'LY private deterministic lossless static batch v1' / source ZIP): needed for  |
| LY-087 | 局部排水端口一致性包 | 复用装配 | M | 是 | 新做 | Frozen deliveries of LY-046, LY-052, LY-054 and LY-073 (port IDs, inverts, SHAs). These are what this seat aggregates; o |
| LY-088 | 水系分期可视资料层 | 考据/契约 | M | 是 | 新做 | Full text and figures of Huang Xuechao 2026 (water works around Han-Wei Luoyang): the modern Eastern Han / Wei / Jin / N |
| LY-089 | 地形支承差异片与边缘闭合 | 补件/修订 | M | 是 | 复用候选 | LY-081 实际地面可达网络与断点（还在准备期）：用来区分安装边界和展示底板 |
| LY-090 | 多地坪开孔与替换合成器 | 复用装配 | M | 是 | 复用候选 | LY-025 正式交付的孔清单和开孔地面 SHA（现在只有 prep 抽取物 0193ebc0）。几何可以从 GLB 重建；母版 city-C032-entry-LOD0.blend 不在仓库，只用来追溯原生切孔操作，不影响重建 |
| LY-091 | 城门城垣区域验收 | 独立验收 | L | 是 | 新做 | 依赖交付：LY-015/017/018/019/020/085/089 的 delivery-manifest、models、assembly.json、qa 都还没有；目前只有 prep 草稿 |
| LY-092 | 市肆住宅区域验收 | 独立验收 | M | 是 | 新做 | LY-030 市肆区域包（变体选择、井孔、操作区、路线和负例）：联合装配的主输入，不能重建 |
| LY-093 | 东北与作业区验收 | 独立验收 | M | 是 | 新做 | Delivered packages LY-040, LY-060, LY-084, LY-089 and their closures (031-039, 051-059, 081): only prep/ exists. These a |
| LY-094 | 宫区礼制位置与装配准入审查 | 独立验收 | M | 是 | 新做 | Delivered packages of LY-070..080 and LY-086 (manifest SHA, assembly.json, qa). These are what this seat rules on; none  |
| LY-095 | 全城碰撞与通路回归 | 独立验收 | M | 是 | 新做 | LY-091..094 packages and batch manifest (selected_tasks, dependency_closure, gate_results, excluded_regions) needed to b |
| LY-096 | 资源预算与官方规范总检 | 独立验收 | L | 是 | 新做 | LY-091～094 的批次 manifest（selected_tasks/dependency_closure/gate_results/excluded_regions）：四个席位目前都只有 prep；不能从 GLB 重建 |
| LY-097 | 真实运行与视觉回归 | 独立验收 | M | 是 | 新做 | LY-091–094 与 LY-096 的放行批次 manifest（这几个席位目前只有 prep）：需要 selected_tasks、dependency_closure、改动区域的机位或开孔探针、预期会变的步骤名（--expect-c |
| LY-098 | 历史表述与完成量终审 | 独立验收 | M | 是 | 新做 | LY-091/092/093/094 区域验收结论：终审要逐条对照章节和 progress 状态。不能从 GLB 重建 |
| LY-099 | 源包与可复现交付核验 | 独立验收 | M | 是 | 新做 | luoyang-yong-city-v1.1-private-source.zip（r2026.11.05-5）。用途：重建已入城的雍门地坪 yong-apron-LOD0/1/2 和它的装配。仓库里只有文件名、没有 SHA，待传文件夹里也 |