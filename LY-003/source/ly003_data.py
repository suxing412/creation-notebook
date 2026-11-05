# -*- coding: utf-8 -*-
"""LY-003 唯一数据源：外部来源登记、引文、控制点候选、准入判定文字。
几何数字一律由 build.py 从仓库提交字节现算，不在这里手填。"""

BASE_COMMIT = 'bce3211f818ee5a8bef1773539da70695ba37b17'
FROZEN_EVIDENCE_SHA = 'fa8b7002869e01e981d2b2679c327a2f1db957119e55537e06289ca59e5ba7c7'

# 仓库只读输入（git show <commit>:<path> 的提交字节）
REPO_INPUTS = [
    'docs/cities/luoyang/data/evidence/evidence-geometry.json',
    'docs/cities/luoyang/data/west/north-palace-conflict-layer.json',
    'docs/cities/luoyang/data/west/road-preconstraints.json',
    'docs/cities/luoyang/data/west/storage-interface.json',
    'docs/cities/luoyang/data/c02v/research-mask.json',
    'docs/cities/luoyang/progress-assets/granary-city-v1/source.json',
    'docs/cities/luoyang/progress-assets/granary-city-v1/granary-city-LOD0.glb',
    'docs/cities/luoyang/city-data.mjs',
]

# 前置席位文件（只读）
PRIOR_INPUTS = [
    'LY-001/status.json',
    'LY-001/qa/city-nodes.csv',
    'LY-001/qa/glb-files.csv',
    'LY-001/source/glbinfo.py',
    'LY-002/status.json',
    'LY-002/tables/evidence-ledger.json',
    'LY-002/qa/palace-spacing-check.json',
]

# 外部来源。kind: 期刊二手综述 / 官方评选巡礼(转载) / 新闻 / 政府科普 / 百科(三手)
# 本包不分发任何外部字节，只记 SHA256；重算时用 --external 指向重新下载的同名文件。
SOURCES = {
    'X-GAO': {
        'title': '高崇文《东汉都城洛阳礼制文化研究》，《中原文化研究》2023年第2期', 'date': '2023',
        'url': 'https://www.zywhyj.cn/Uploads/PdfFile/2023-04-11/6434e64ce0ef9.pdf',
        'file': 'gao2023_raw.txt', 'pdf': 'gao2023.pdf', 'kind': '期刊二手综述（城垣数字转引1973初步勘查）',
        'read': '已读PDF文字层（LY-002同一份下载，PDF SHA一致）'},
    'X-SINA': {
        'title': '2023年度河南省十大考古新发现巡礼（下），手机新浪网转载', 'date': '2024-03-04',
        'url': 'http://henan.sina.cn/city/csgz/2024-03-04/detail-inamckxt1025059.d.html',
        'file': 'sina2024b.html', 'kind': '评选巡礼文字（发掘领队刘涛项目条目）的网站转载；非发掘报告、无图',
        'read': '已读全文中汉魏洛阳故城宫城条'},
    'X-QQ': {
        'title': '洛阳三个项目入选2023年度河南省十大考古新发现（洛报融媒）', 'date': '2024-03-03',
        'url': 'https://news.qq.com/rain/a/20240303A07OU500',
        'file': 'qq2024.html', 'kind': '新闻', 'read': '已读全文'},
    'X-CTDSB': {
        'title': '考古2023｜三国两晋南北朝考古（极目新闻／楚天都市报，社科院考古所学者年度综述）', 'date': '2024-06-22',
        'url': 'https://www.ctdsb.net/c1664_202406/2173744.html',
        'file': 'ctdsb2024.html', 'kind': '学者年度综述的新闻转载；无图', 'read': '已读汉魏洛阳城段'},
    'X-HUANQIU': {
        'title': '汉魏洛阳城遗址考古重大发现（环球网，千秋门水道）', 'date': '2022',
        'url': 'https://china.huanqiu.com/article/48Nj5E1mwn0',
        'file': 'huanqiu2022.html', 'kind': '新闻（考古队副队长郭晓涛介绍）；无图坐标', 'read': '已读全文'},
    'X-QIAN': {
        'title': '钱国祥《汉魏洛阳故城居中宫城制度考》（中国社会科学报，全国哲学社会科学工作办公室网转载）', 'date': '2018-07-04',
        'url': 'https://www.nopss.gov.cn/n1/2018/0704/c373410-30125781.html',
        'file': 'nopss2018.html', 'kind': '发掘主持者的成果短文；无图坐标', 'read': '已读全文'},
    'X-CHINANEWS': {
        'title': '汉魏洛阳城遗址发现大型仓窖遗迹（光明日报，中新网转载）', 'date': '2023-01-16',
        'url': 'https://www.chinanews.com.cn/cul/2023/01-16/9936171.shtml',
        'file': 'chinanews2023.html', 'kind': '新闻；北魏遗迹', 'read': '已读全文'},
    'X-CHANHE': {
        'title': '《文化瀍河》第二章第五节 汉魏洛阳故城（下）（政务号，澎湃转载）', 'date': '2023-08-30',
        'url': 'https://m.thepaper.cn/baijiahao_24443356',
        'file': 'chanhe2023.html', 'kind': '地方政务科普；分期混写', 'read': '已读内城遗址段'},
    'X-MAIGOO': {
        'title': '汉魏洛阳城遗址（买购网百科词条）', 'date': '未注',
        'url': 'https://www.maigoo.com/citiao/140672.html',
        'file': 'maigoo.html', 'kind': '百科（三手，无出处）', 'read': '已读城垣与宫城段'},
}

UNREACHABLE = [
    {'url': 'https://www.hnswwkgyjy.cn/NewsView.php?News_ID=2283', 'what': '河南省文物考古研究院 2023年度十大考古新发现原页',
     'result': '未能访问：WebFetch 报 getaddrinfo ENOTFOUND；curl 返回 000（2026-11-05）'},
    {'url': 'https://www.hnswwkgyjy.cn/NewsView.php?News_ID=2810', 'what': '同站 2025年度考古工作汇报（仓库记录称或有东汉砖砌水道）',
     'result': '未能访问：curl 返回 000（2026-11-05）'},
    {'url': 'https://m.thepaper.cn/detail/30267154', 'what': '澎湃新闻 汉魏洛阳城相关报道（搜索结果）',
     'result': '未能访问：HTTP 403'},
    {'url': 'https://zhuanlan.zhihu.com/p/2069518466340632201', 'what': '知乎 汉魏洛阳城宫城遗址考古最新成果',
     'result': '未能访问：HTTP 403'},
    {'url': 'https://www.163.com/dy/article/L3LC7HE00556124F.html', 'what': '网易号 城垣实测数字转载',
     'result': '未能访问：HTTP 404'},
]

# 引文：每条不超过一句；校核时去掉空白与 HTML 标签后逐字匹配来源字节。
QUOTES = [
    {'id': 'Q01', 'src': 'X-GAO', 'loc': '印刷页50 宫殿建制段', 'text': '由于目前对南宫的具体位置还没勘查清',
     'use': '南宫位置未勘查：南宫不可落位'},
    {'id': 'Q02', 'src': 'X-GAO', 'loc': '印刷页49 城垣形制段', 'text': '北城垣全长约2523米，西城垣残长约3500米，东城垣残长约3895米',
     'use': '城垣实测长度（数值版本A，转引1973）'},
    {'id': 'Q03', 'src': 'X-SINA', 'loc': '汉魏洛阳故城宫城遗址条', 'text': '新发现了或与东汉北宫宫墙有关的遗迹',
     'use': '条目开头本身用了“或与……有关”的保留语'},
    {'id': 'Q04', 'src': 'X-SINA', 'loc': '同条', 'text': '新发现的东汉北宫东墙、南墙均巧妙地利用了台地的地形地貌特征，在台地边缘冲沟内侧修筑而成',
     'use': '东汉北宫东/南墙的地形判据（无坐标）'},
    {'id': 'Q05', 'src': 'X-SINA', 'loc': '同条', 'text': '东汉北宫的范围，与魏晋、北魏时期的宫城范围大致相同，只是不同区域的垣墙位置略有摆动',
     'use': '定性范围约束；“摆动”量未给'},
    {'id': 'Q06', 'src': 'X-CTDSB', 'loc': '汉魏洛阳城段', 'text': '最下层的不晚于东汉时期道路位于冲沟内，东西宽约23米',
     'use': '宫城东墙外最下层道路宽度（无坐标）'},
    {'id': 'Q07', 'src': 'X-CTDSB', 'loc': '同段', 'text': '在北魏宫城东墙外侧最下层道路西侧还发现不晚于东汉时期的夯土墙',
     'use': '东墙相关夯土墙的相对位置：只相对北魏宫城东墙'},
    {'id': 'Q08', 'src': 'X-CTDSB', 'loc': '同段', 'text': '宫城南墙经发掘确认仅有一道，系不同时代宫墙在原位不断修筑改建而成，其始建年代亦晚于东汉时期',
     'use': '后期宫城南墙始建晚于东汉：东汉北宫南墙不在该处或另有位置，与Q04“南墙”需对读'},
    {'id': 'Q09', 'src': 'X-QQ', 'loc': '汉魏洛阳城宫城遗址段', 'text': '还新发现了与东汉北宫宫墙有关的遗迹',
     'use': '新闻转述去掉了Q03的保留语'},
    {'id': 'Q10', 'src': 'X-HUANQIU', 'loc': '千秋门段', 'text': '千秋门遗址系汉魏洛阳城北魏宫城西墙从南至北的第三座门址',
     'use': '水道位置只相对北魏宫城西墙门址'},
    {'id': 'Q11', 'src': 'X-HUANQIU', 'loc': '同文', 'text': '其中发现的不晚于汉代的大型砖砌拱券式水道，由内外两重砌砖构成，内宽1.2米',
     'use': '宫墙水道的唯一尺寸线索（无坐标、无走向数据）'},
    {'id': 'Q12', 'src': 'X-QIAN', 'loc': '2011年宫城西南角段', 'text': '分别发现了不晚于曹魏的宫城西墙和汉晋时期的大型河渠',
     'use': '宫城西南角下的汉晋河渠（分期跨汉晋，无坐标）'},
    {'id': 'Q13', 'src': 'X-CHINANEWS', 'loc': '仓窖区段', 'text': '东西宽约150米，南北长约600米，较为独立的仓窖区，应属北魏时期的皇家府库遗迹',
     'use': '宫城东侧仓窖区属北魏：不得当东汉太仓'},
    {'id': 'Q14', 'src': 'X-CHANHE', 'loc': '内城遗址段', 'text': '西垣残长3510米，宽约20米 ；北垣全长2820米',
     'use': '城垣实测长度（数值版本B）'},
    {'id': 'Q15', 'src': 'X-MAIGOO', 'loc': '遗址现状段', 'text': '北魏宫城为长方形，南北长约1400米，东西宽约660米',
     'use': '北魏宫城尺寸（三手、后期）：只作异期对照'},
    {'id': 'Q16', 'src': 'X-MAIGOO', 'loc': '同词条', 'text': '内城东垣残长3895米，西垣残长4290米，北垣长3700米',
     'use': '城垣实测长度（数值版本C，含金墉城的可能）'},
    {'id': 'Q17', 'src': 'X-MAIGOO', 'loc': '宫城遗址段', 'text': '北魏的宫城位于城内北中部，南北长1398米，东西宽660米',
     'use': '北魏宫城南北长1398米与旧B北宫南北边长（≈1398米）相同：旧B南北长疑取自后期宫城实测（未证，交复核）'},
]

# 实测长度（来自上面引文，单位米）。'kind': full=全长, residual=残长
SURVEY_LENGTHS = [
    {'set': 'A', 'quote': 'Q02', 'side': 'north', 'm': 2523, 'kind': 'full'},
    {'set': 'A', 'quote': 'Q02', 'side': 'west', 'm': 3500, 'kind': 'residual'},
    {'set': 'A', 'quote': 'Q02', 'side': 'east', 'm': 3895, 'kind': 'residual'},
    {'set': 'B', 'quote': 'Q14', 'side': 'north', 'm': 2820, 'kind': 'full'},
    {'set': 'B', 'quote': 'Q14', 'side': 'west', 'm': 3510, 'kind': 'residual'},
    {'set': 'C', 'quote': 'Q16', 'side': 'north', 'm': 3700, 'kind': 'full'},
    {'set': 'C', 'quote': 'Q16', 'side': 'west', 'm': 4290, 'kind': 'residual'},
    {'set': 'C', 'quote': 'Q16', 'side': 'east', 'm': 3895, 'kind': 'residual'},
]

LATER_PALACE_DIMS = {'quote': 'Q15', 'ns_m': 1400, 'ew_m': 660, 'phase': '北魏', 'class': '异期类比（三手）'}

# 控制点候选。frames: schematic=项目示意坐标是否已有；survey=有无可核的测绘/发掘坐标
# 四类：原始考古/原文、异地异期类比、C工程设计、未知
CONTROL_POINTS = [
    {'id': 'CP-01', 'name': '城西北角（内城）', 'feature': 'city_wall_schematic_B', 'vertex': 0,
     'evidence': '原始考古（残垣存在，二手）', 'phase': '多期累积；东汉单期位置未分',
     'schematic': True, 'survey': False, 'missing': '1973初步勘查/1998城垣试掘的测绘平面或角点坐标；金墉城叠压关系'},
    {'id': 'CP-02', 'name': '城东北角（内城）', 'feature': 'city_wall_schematic_B', 'vertex': 4,
     'evidence': '原始考古（残垣存在，二手）', 'phase': '多期累积',
     'schematic': True, 'survey': False, 'missing': '同上；示意图东北角为抹角（两点），实测转角位置未知'},
    {'id': 'CP-03', 'name': '城西南角、城东南角', 'feature': 'south_wall_inferred_B', 'vertex': None,
     'evidence': '未知（南垣被洛河冲毁，推定）', 'phase': '—',
     'schematic': True, 'survey': False, 'missing': '不可作控制点：本身是推定闭合'},
    {'id': 'CP-04', 'name': '上东门（北魏建春门）门址', 'feature': 'gate_shangdong_B', 'vertex': None,
     'evidence': '原始考古（考古1988(9)建春门发掘，未读）', 'phase': '北魏门址；东汉门位同址与否未核',
     'schematic': True, 'survey': False, 'missing': '1988简报门址平面与城垣相对位置；未取得'},
    {'id': 'CP-05', 'name': '东汉北宫东墙段', 'feature': 'north_palace_excavated_walls_A_unplaced', 'vertex': None,
     'evidence': '原始考古（2023发掘，仅转载文字，Q04/Q07）', 'phase': '不晚于东汉；逐段使用年代未知',
     'schematic': False, 'survey': False, 'missing': '发掘平面、探方坐标、与北魏宫城东墙的偏移量；原机构页未能访问'},
    {'id': 'CP-06', 'name': '东汉北宫南墙段', 'feature': 'north_palace_excavated_walls_A_unplaced', 'vertex': None,
     'evidence': '原始考古（仅文字，Q04）；与Q08“后期南墙始建晚于东汉”需对读', 'phase': '东汉',
     'schematic': False, 'survey': False, 'missing': '南墙段实际位置；它与北魏宫城南墙的南北距离'},
    {'id': 'CP-07', 'name': '宫城东墙外最下层道路（冲沟内，宽约23米）', 'feature': None, 'vertex': None,
     'evidence': '原始考古（仅文字，Q06）', 'phase': '不晚于东汉',
     'schematic': False, 'survey': False, 'missing': '道路中心线坐标与走向'},
    {'id': 'CP-08', 'name': '千秋门下不晚于汉代砖券水道（内宽1.2米）', 'feature': None, 'vertex': None,
     'evidence': '原始考古（仅新闻文字，Q10/Q11）', 'phase': '不晚于汉代；180年在用与否未知',
     'schematic': False, 'survey': False, 'missing': '水道平面、底高程、走向；千秋门在项目坐标中的位置（北魏门，不得前推）'},
    {'id': 'CP-09', 'name': '宫城西南角下汉晋大型河渠', 'feature': None, 'vertex': None,
     'evidence': '原始考古（仅成果短文，Q12）', 'phase': '汉晋（未细分）',
     'schematic': False, 'survey': False, 'missing': '2011宫城西南角发掘简报平面；河渠宽深与走向'},
    {'id': 'CP-10', 'name': '北魏宫城轮廓（约1400×660米）', 'feature': None, 'vertex': None,
     'evidence': '异地异期类比（同地后期，三手Q15）', 'phase': '北魏',
     'schematic': False, 'survey': False, 'missing': '只有尺寸、无位置；即使取得也只能作“范围大致相同”的定性对照，不能替换东汉北宫'},
    {'id': 'CP-11', 'name': '阊阖门（44.5×24.4米台基）', 'feature': None, 'vertex': None,
     'evidence': '原始考古（曹魏始建，钱2018）', 'phase': '曹魏—北魏',
     'schematic': False, 'survey': False, 'missing': '禁用（LY-002 X04）：不作东汉控制点'},
    {'id': 'CP-12', 'name': '南宫任一墙段/门址', 'feature': 'south_palace_candidate_gao2023_B', 'vertex': None,
     'evidence': '未知（Q01：位置还没勘查清）', 'phase': '东汉',
     'schematic': True, 'survey': False, 'missing': '无考古定位；示意包络只是一说'},
    {'id': 'CP-13', 'name': '太仓、武库', 'feature': 'region_taicang_B', 'vertex': None,
     'evidence': '研究推定（“东北隅”，LY-002 E-S01/E-S02）', 'phase': '东汉',
     'schematic': True, 'survey': False, 'missing': '无东汉遗址定位；2023仓窖区为北魏（Q13），不得替代'},
    {'id': 'CP-14', 'name': '永安宫（北宫东北别小宫）', 'feature': 'region_yongan_B', 'vertex': None,
     'evidence': '原文相对方位（LY-002 E-P07）', 'phase': '东汉',
     'schematic': True, 'survey': False, 'missing': '无考古定位'},
    {'id': 'CP-15', 'name': '台地/冲沟地形（东墙、南墙依托）', 'feature': None, 'vertex': None,
     'evidence': '原始考古判据（Q04），地形本身是现代可测', 'phase': '现代地形≠东汉地表',
     'schematic': False, 'survey': False, 'missing': '本项目坐标无地理原点，现代DEM无法套入；且需先有CP-01/02这类共同点'},
]

# 准入判定（build.py 会把计算数字填进 'numbers'）
ADMISSION = [
    {'zone': '北宫（墙、门、内部院落）', 'ids': ['north_palace_extent_gao2023_B', 'north_palace_excavated_walls_A_unplaced', 'north_palace_interior_unknown'],
     'status': '不可落位', 'allowed': '仅独立研究视图或局部包（无城市矩阵）；LY-070只交局部组装',
     'reason': '新墙段无坐标（CP-05/06/07）；旧B宽度与“范围与后期宫城大致相同”的报道尺寸相差悬殊；无共同控制点'},
    {'zone': '南宫', 'ids': ['south_palace_candidate_gao2023_B'],
     'status': '不可落位', 'allowed': '仅独立研究；B包络只作对照',
     'reason': 'Q01：南宫具体位置未勘查清；正方形/长方形两说'},
    {'zone': '两宫复道', 'ids': ['palaces_connector_B'],
     'status': '不可落位', 'allowed': '仅关系示意；复道模块只作局部C',
     'reason': '两端宫墙都未定位；“七里”与示意距离不符（LY-002 E-P02）'},
    {'zone': '永安宫', 'ids': ['region_yongan_B'],
     'status': '不可落位', 'allowed': '仅区域标签', 'reason': '只有“北宫东北”相对方位'},
    {'zone': '宫墙水道（三段接口）', 'ids': ['ancient_water_corridors_B_unplaced'],
     'status': '不可落位', 'allowed': 'LY-086只做局部墙块上的可撤回安装，不写世界位置',
     'reason': 'CP-08/09只有文字；分期跨汉晋；180年在用未知'},
    {'zone': '东北仓储区（太仓候选，已按章入城）', 'ids': ['region_taicang_B', 'region_wuku_B'],
     'status': '维持现状，不由本席位升级或撤回', 'allowed': '现位置是B区域标签点上的C功能模型；本包只给它与宫区悬置带的距离',
     'reason': '“东北隅”为研究推定；本席位没有能把它“配准”的资料'},
    {'zone': '东北接路（既有约196示意米C短路，LY-039）', 'ids': [],
     'status': '宫墙条件未决（不是放行）', 'allowed': '在“东北C试放筛查区”内可作可回退C局部包；不得声称位于宫外或有历史通行依据',
     'reason': 'C_NE_APPROACH_LOCAL 在 bce3211 提交中未找到，几何未核；新东墙未配准'},
    {'zone': '东北长接路（约1.7公里，LY-084）', 'ids': ['road_northeast_gate_link_B'],
     'status': '不可落位（西段悬置）', 'allowed': '无',
     'reason': '该示意线西端触旧北宫东界（road-preconstraints: hold_palace_interface）；新东墙与冲沟道路无坐标'},
]
