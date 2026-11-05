# -*- coding: utf-8 -*-
"""LY-004 唯一数据源：城南礼制四所、南郊、北郊（单列）的证据、分期、位置约束。

所有引文都必须在对应快照（或外部来源文字层）里逐字找到，由 build.py 核对。
引文不超过一句。四栏：sameLuoyang（同期洛阳原文/考古）、otherHan（异地汉代）、
later（魏晋北魏及后世）、unknown（未知）。
"""

SNAPSHOT_YEAR = 180

# ---------------------------------------------------------------- 来源
# kind: classical(公有领域古籍快照) / research(版权材料，只记SHA) / repo(仓库沿用)
SOURCES = {
    "S01": {"title": "《后汉书·光武帝纪上》及李贤注（卷一上）", "url": "https://www.njmuseum.org.cn/files/wshl/rbbook/gb/25/houhanshu/hhs01.html",
            "file": "LY002:source/snapshots/hhs01.html", "enc": "gbk", "textDate": "范晔（南朝宋）；注引陆机《洛阳记》（西晋）", "kind": "classical"},
    "S02": {"title": "《后汉书·光武帝纪下》及李贤注（卷一下）", "url": "https://www.njmuseum.org.cn/files/wshl/rbbook/gb/25/houhanshu/hhs02.html",
            "file": "LY002:source/snapshots/hhs02.html", "enc": "gbk", "textDate": "注引应劭《汉官仪》（东汉末，约与180年同时）、《汉宫阁疏》（成书年代未核）", "kind": "classical"},
    "S07": {"title": "《后汉书·孝顺孝冲孝质帝纪》（卷六）", "url": "https://www.njmuseum.org.cn/files/wshl/rbbook/gb/25/houhanshu/hhs07.html",
            "file": "LY004:source/snapshots/hhs07.html", "enc": "gbk", "textDate": "范晔（南朝宋）", "kind": "classical"},
    "S09": {"title": "《后汉书·灵帝纪》及李贤注（卷八）", "url": "https://www.njmuseum.org.cn/files/wshl/rbbook/gb/25/houhanshu/hhs09.html",
            "file": "LY002:source/snapshots/hhs09.html", "enc": "gbk", "textDate": "范晔；注引《续汉志》", "kind": "classical"},
    "S65": {"title": "《后汉书·蔡邕列传》（卷六十下）", "url": "https://www.njmuseum.org.cn/files/wshl/rbbook/gb/25/houhanshu/hhs65.html",
            "file": "LY002:source/snapshots/hhs65.html", "enc": "gbk", "textDate": "范晔", "kind": "classical"},
    "S85": {"title": "《后汉书·儒林列传上》序及注（卷七十九上）", "url": "https://www.njmuseum.org.cn/files/wshl/rbbook/gb/25/houhanshu/hhs85.html",
            "file": "LY002:source/snapshots/hhs85.html", "enc": "gbk", "textDate": "范晔；注引谢承《后汉书》（孙吴）", "kind": "classical"},
    "S103": {"title": "《续汉书·礼仪志上》（志第四）", "url": "https://www.njmuseum.org.cn/files/wshl/rbbook/gb/25/houhanshu/hhs103.html",
             "file": "LY004:source/snapshots/hhs103.html", "enc": "gbk", "textDate": "司马彪（西晋）撰，记东汉制度", "kind": "classical"},
    "S106": {"title": "《续汉书·祭祀志上》（志第七）", "url": "https://www.njmuseum.org.cn/files/wshl/rbbook/gb/25/houhanshu/hhs106.html",
             "file": "LY002:source/snapshots/hhs106.html", "enc": "gbk", "textDate": "司马彪（西晋）撰，记建武二年制度", "kind": "classical"},
    "S107": {"title": "《续汉书·祭祀志中》（志第八）", "url": "https://www.njmuseum.org.cn/files/wshl/rbbook/gb/25/houhanshu/hhs107.html",
             "file": "LY002:source/snapshots/hhs107.html", "enc": "gbk", "textDate": "司马彪；注引张璠记（晋）、蔡邕《月令章句》（东汉末）", "kind": "classical"},
    "S118": {"title": "《续汉书·郡国志一》河南尹雒阳条注（志第十九）", "url": "https://www.njmuseum.org.cn/files/wshl/rbbook/gb/25/houhanshu/hhs118.html",
             "file": "LY002:source/snapshots/hhs118.html", "enc": "gbk", "textDate": "刘昭注引《魏氏春秋》", "kind": "classical"},
    "SQ3": {"title": "杨衒之《洛阳伽蓝记》卷三城南（维基文库原始wikitext）",
            "url": "https://zh.wikisource.org/w/index.php?title=%E6%B4%9B%E9%99%BD%E4%BC%BD%E8%97%8D%E8%A8%98/%E5%8D%B7%E4%B8%89&action=raw",
            "file": "LY004:source/snapshots/qielan3.wikitext", "enc": "utf-8", "textDate": "东魏武定五年（547）追记北魏洛阳", "kind": "classical"},
    "G23": {"title": "高崇文《东汉都城洛阳礼制文化研究》，《中原文化研究》2023年第2期，页48–56",
            "url": "https://www.zywhyj.cn/Uploads/PdfFile/2023-04-11/6434e64ce0ef9.pdf",
            "file": "EXT:gao2023_raw.txt", "enc": "utf-8", "externalOriginal": "gao2023.pdf",
            "externalSha256": "c10cd82d71a864f4441f539f178432d09a354dbe02f28bdcf97df301885d5b51",
            "textDate": "2023；考古数字转引段鹏琦2010，原发掘报告本轮未读", "kind": "research"},
    "G23F1": {"title": "高崇文2023 图1《东汉洛阳城平面布局示意图》（引徐龙国制图），PDF第49页内嵌图",
              "url": "https://www.zywhyj.cn/Uploads/PdfFile/2023-04-11/6434e64ce0ef9.pdf",
              "file": "EXT:gao2023.pdf#page-index-48/Im3", "imageSha256": "da21a2c0bd0ad0d97c695b59325ec21bfd3a115890007b170b914a24999e04bc",
              "imagePx": [373, 594], "textDate": "现代研究示意图，非测绘", "kind": "research"},
}

# 同一文章在同站点还有另一上传件（9页），字节不同；本席位以 G23（与LY-002同SHA）为准。
ALT_UPLOAD = {"url": "https://www.zywhyj.cn/Uploads/PdfFile/2023-04-11/643503e53f1c0.pdf",
              "sha256": "516b163774b02ed7ca6fc33706cc98a14a51a3b6708047b35513682043dd1dcd",
              "note": "同文单篇抽印件；图1内嵌图字节SHA与G23相同(da21a2c0…)，本席位用它做了文字核对的交叉阅读，引文以G23文字层为准"}

# 本轮查过但没有拿到可用于配准的资料（不冒称已读）
NOT_OBTAINED = [
    {"what": "中国社会科学院考古研究所《汉魏洛阳故城南郊礼制建筑遗址（1962–1992年考古发掘报告）》，文物出版社2010",
     "status": "未能访问：网上只检索到书目条目，正文、遗址总平面和测绘控制点均未取得", "searched": "WebSearch 2026-11-05"},
    {"what": "南郊圆坛、北郊方坛的考古遗址资料",
     "status": "未找到：检索只得到邙山东汉帝陵材料；高2023称南郊坛遗址未发现、'大郊村'只是可能位置", "searched": "WebSearch 2026-11-05"},
    {"what": "大郊村、太学村、岗上村等现代村落的坐标",
     "status": "没有取得：即使取得，也只能给现代地名点，不能当东汉遗址控制点；本席位没有使用任何现代地理坐标", "searched": "未取"},
    {"what": "东汉尺的量器实测出处",
     "status": "未取得：检索只得到科普转述（约23.1厘米）；换算沿用LY-002的C假设0.230–0.240米/尺", "searched": "WebSearch 2026-11-05"},
]

# ---------------------------------------------------------------- 单位（全部C）
UNITS = {
    "chi_m": [0.230, 0.240],
    "bu_chi": 6,
    "li_bu": 300,
    "note": "C假设（LY-002 X22）：汉尺0.230–0.240米；1步=6尺；1里=300步=1800尺，故1里=414–432米、1步=1.38–1.44米。",
    "rounding": {"li": 0.5, "bu_hundreds": 50,
                 "note": "C假设：'二里所''一里所'等取±0.5里；'三百步'取±50步。这是读法宽度，不是历史误差。"},
}

# ---------------------------------------------------------------- 图1 人工读数（图像像素，373×594，原点左上，y向下）
# 每条读数都由 build.py 检查该像素行/列确为暗线（灰度<128 的比例），不通过即报错。
FIG1 = {
    "scaleBar": {"tick0_x": 29.0, "tick500_x": 77.5, "rows": [564, 569], "bar_rows": [568, 569], "label_m": 500},
    "southWall_y": 456.0, "southWall_rows": [455, 457],
    "gates": {"pingcheng": {"x": 221.5, "gapCols": [219, 221, 224]}, "kaiyang": {"x": 259.5, "gapCols": [257, 258, 261, 262]}},
    "roads": {"pingcheng_south": {"cols": [216, 217, 219], "rows": [500, 570], "x": 217.75},
              "kaiyang_south": {"cols": [258, 259], "rows": [545, 570], "x": 258.5}},
    # 符号外框（图上所绘矩形），只作读数，不是院界
    "boxes": {
        "lingtai": {"x": [194.5, 213.5], "y": [546.0, 564.0], "edges": {"top": [546, 195, 213], "bottom": [564, 195, 213], "left": [195, 547, 563], "right": [213, 551, 563]}},
        "mingtang": {"x": [223.5, 253.5], "y": [541.5, 571.0], "edges": {"top": [542, 224, 253], "bottom": [571, 224, 253], "left": [223, 543, 570], "right": [253, 543, 570]}},
        "biyong": {"x": [264.5, 286.0], "y": [533.5, 556.0], "edges": {"top": [534, 265, 285], "bottom": [556, 265, 285], "left": [265, 535, 555], "right": [286, 535, 555]}},
        "taixue": {"x": [289.5, 297.5], "y": [504.5, 520.5], "edges": {"top": [504, 290, 297], "bottom": [520, 290, 297], "left": [289, 506, 519], "right": [297, 506, 519]}},
    },
    "frame": {"top_y": 11, "bottom_y": 578},
    "unlabeled": [{"what": "开阳门南大道与太学之间的一个斜置小矩形（约x266–284, y518–528）",
                   "treatment": "图上无标注，不认定为任何礼制建筑，不进入本表"}],
}

# 仓库冻结证据层（evidence-geometry.json）的相关要素 id
REPO_IDS = {"lingtai": "ritual_lingtai_B", "mingtang": "ritual_mingtang_B", "biyong": "ritual_biyong_B", "taixue": "ritual_taixue_B",
            "pingcheng": "gate_pingcheng_B", "kaiyang": "gate_kaiyang_B", "xiaoyuan": "gate_xiaoyuan_B",
            "wall": "city_wall_schematic_B", "southWall": "south_wall_inferred_B",
            "pcRoad": "road_pingcheng_south_link_B", "eastSpine": "road_east_spine_B",
            "southPalace": "south_palace_candidate_gao2023_B", "northPalace": "north_palace_extent_gao2023_B"}

# ---------------------------------------------------------------- 引文
# col: same=同期洛阳(原文/考古)  other=异地汉代  later=魏晋北魏及后世  (未知另列)
Q = lambda qid, src, loc, quote, col, supports, textDate=None: dict(id=qid, src=src, locator=loc, quote=quote, col=col, supports=supports, textDate=textDate)

QUOTES = [
    # 灵台
    Q("LT1", "S02", "光武纪下中元元年注引汉宫阁疏", "灵台高三丈，十二门", "same", "高度与门数（《汉宫阁疏》成书年代未核）", "未核"),
    Q("LT2", "S107", "祭祀志中中元元年", "是年初营北郊，明堂﹑[一]辟雍﹑[二]灵台未用事", "same", "56年三雍尚未用事（分期起点）"),
    Q("LT3", "S07", "顺帝纪永和元年", "宗祀明堂，登灵台，改元永和", "same", "136年明堂、灵台在用"),
    Q("LT4", "G23", "页55", "灵台位于平城门外大道西侧，与明堂一西一东夹道相对", "same", "与明堂夹平城门外大道（二手综述）"),
    Q("LT5", "G23", "页55", "每边长200米左右", "same", "围墙边长（转引段鹏琦2010，分期未核）"),
    Q("LT6", "G23", "页55", "残高约8米", "same", "台基现存残高（不是原高）"),
    Q("LT7", "SQ3", "卷三城南·秦太上公二寺条", "寺東有靈臺一所，基址雖頹，猶高五丈餘，即是漢光武所立者", "later", "北魏人认定此台为汉光武所立（6世纪追记）", "东魏547"),
    Q("LT8", "S09", "灵帝纪中平二年注引续汉志", "时烧灵台殿、乐成殿", "same", "185年南宫火烧的'灵台殿'是宫中殿名，不是城南灵台"),
    # 明堂
    Q("MT1", "S02", "光武纪下中元元年", "初起明堂﹑灵台﹑辟雍，及北郊兆域", "same", "56年起三雍及北郊兆域"),
    Q("MT2", "S02", "注引汉官仪", "明堂去平城门二里所", "same", "距平城门约二里（应劭，东汉末）"),
    Q("MT3", "S02", "注引汉官仪", "天子出，从平城门，先历明堂，乃至郊祀", "same", "出平城门先经明堂后至郊：郊坛在明堂之外"),
    Q("MT4", "S02", "注引汉官仪", "明堂四面起土作爎，上作桥，爎中无水", "same", "四面干壍与桥"),
    Q("MT5", "S07", "顺帝纪汉安元年", "汉安元年春正月癸巳，宗祀明堂", "same", "142年明堂在用"),
    Q("MT6", "G23", "页54", "每面墙约长400米", "same", "明堂围墙（转引，分期未核）"),
    Q("MT7", "G23", "页54", "直径61至62米", "same", "中心圆形夯土基址（转引，分期未核）"),
    Q("MT8", "SQ3", "卷三城南·秦太上公二寺条", "至我正光中，造明堂於辟雍之西南，上圓下方，八窗四闥", "later", "北魏正光（520–525）在辟雍西南另造明堂，上圆下方", "东魏547"),
    # 辟雍
    Q("BY1", "S02", "注引汉官仪", "辟雍去明堂三百步", "same", "与明堂相距三百步"),
    Q("BY2", "S02", "注引汉官仪", "车驾临辟雍，从北门入", "same", "北门入"),
    Q("BY3", "S02", "注引汉官仪", "东西南有水，北无", "same", "水在东西南三面"),
    Q("BY4", "S07", "顺帝纪阳嘉元年", "帝临辟雍飨射，大赦天下，改元阳嘉", "same", "132年辟雍在用"),
    Q("BY5", "S09", "灵帝纪熹平六年", "帝临辟雍", "same", "177年冬十月灵帝临辟雍（离快照最近的在用记录）"),
    Q("BY6", "G23", "页53", "可证辟雍遗址位于城南大郊村一带", "same", "遗址认定依据是晋碑（见BY9）"),
    Q("BY7", "G23", "页53", "各流出180余米后折而向南", "same", "环水东西分流（分期未核）"),
    Q("BY8", "G23", "页53", "尚未显出转折闭合的迹象", "same", "环水未见闭合"),
    Q("BY9", "G23", "页53", "发现晋武帝三临辟雍的纪念碑", "later", "西晋碑：证遗址延用到晋", "西晋"),
    Q("BY10", "SQ3", "卷三城南·秦太上公二寺条", "靈臺東辟雍，是魏武帝所立者", "later", "北魏人称灵台东的辟雍为魏武帝所立", "东魏547"),
    # 太学
    Q("TX0", "S01", "光武纪上建武五年", "初起太学", "same", "29年起太学"),
    Q("TX1", "S01", "光武纪上建武五年注引陆机洛阳记", "太学在洛阳城故开阳门外，去宫八里", "later", "开阳门外；'去宫八里'是西晋人以西晋宫城计", "西晋"),
    Q("TX2", "S07", "顺帝纪永建六年", "秋九月辛巳，缮起太学", "same", "131年重修太学"),
    Q("TX3", "S07", "顺帝纪阳嘉元年", "以太学新成", "same", "132年太学新成"),
    Q("TX4", "S85", "儒林传序", "凡所造构二百四十房，千八百五十室", "same", "顺帝重修规模（快照年的太学是重修后的状态）"),
    Q("TX5", "S09", "灵帝纪熹平四年", "刻石立于太学门外", "same", "175年起刻石经立太学门外"),
    Q("TX6", "S09", "灵帝纪熹平五年", "试太学生年六十以上百余人", "same", "176年太学在用"),
    Q("TX7", "S09", "灵帝纪光和五年", "还，幸太学", "same", "182年十二月幸太学"),
    Q("TX8", "S85", "儒林传注引谢承书", "碑立太学门外，瓦屋覆之，四面栏障，开门于南", "same", "石经覆屋与围护（谢承，孙吴人）", "孙吴"),
    Q("TX9", "G23", "页52", "太学遗址应在洛阳故城南郊今太学村一带", "same", "遗址推定位置（二手）"),
    Q("TX10", "G23", "页52", "东西150余米，南北约220米", "later", "魏晋以降太学遗址范围（LY-002 X09 禁作东汉）", "魏晋以降"),
    Q("TX11", "G23", "页52", "说明东汉太学遗址正在此处", "same", "东汉太学同址是作者推论"),
    Q("TX12", "SQ3", "卷三城南·报德寺条", "開陽門御道東有漢國子學堂", "later", "北魏人所见：开阳门御道东有'汉国子学堂'", "东魏547"),
    # 南郊
    Q("NJ1", "S106", "祭祀志上建武二年", "初制郊兆于雒阳城南七里", "same", "南郊兆在城南七里（26年）"),
    Q("NJ2", "S106", "祭祀志上建武二年", "为圆坛八陛，中又为重坛", "same", "圆坛八陛"),
    Q("NJ3", "S107", "祭祀志中五郊迎气注引月令章句", "南郊七里，因火数也", "same", "蔡邕以'七'为火数：七里可能是配数而非测距（LY-002 X17）"),
    Q("NJ4", "S103", "礼仪志上", "正月上丁，祠南郊", "same", "南郊在东汉礼仪中按年使用"),
    Q("NJ5", "S09", "灵帝纪中平元年注", "悬其首于南郊以谢天下", "same", "184年上书仍以南郊为京师地标"),
    Q("NJ6", "G23", "二（七）南北郊坛段", "有可能是南郊坛的位置所在", "same", "大郊村只是'可能'位置（遗址未发现）"),
    Q("NJ7", "S118", "郡国志一雒阳注引魏氏春秋", "魏时营为圆丘", "later", "曹魏另营圆丘，不是东汉南郊", "曹魏"),
    Q("NJ8", "SQ3", "卷三城南·永桥条", "永橋以南，圜丘以北，伊洛之間", "later", "北魏圜丘在洛水以南、伊洛之间，不是东汉南郊", "东魏547"),
    Q("NJ9", "SQ3", "卷三城南·永桥条", "宣陽門外四里，至洛水上，作浮橋，所謂永橋也", "later", "北魏洛水距宣阳门（汉小苑门）约四里", "东魏547"),
    # 北郊
    Q("BJ1", "S107", "祭祀志中", "北郊在雒阳城北四里，为方坛四陛", "same", "读法A：城北四里（志文正文）"),
    Q("BJ2", "S107", "祭祀志中注引张璠记", "城北六里", "later", "读法B：城北六里（晋人记）", "晋"),
    Q("BJ3", "S02", "光武纪下注引汉官仪", "北郊□在城西北角，去城一里所", "same", "读法C：城西北角外一里所（应劭，东汉末）"),
    Q("BJ4", "S02", "光武纪下注引汉官仪", "但有□祠舍而已", "same", "北郊只有祠舍类建筑（缺字）"),
    Q("BJ5", "S107", "祭祀志中", "四陛醊及中外营门封神如南郊", "same", "北郊也有中营、外营及营门"),
    Q("BJ6", "S107", "祭祀志中五郊迎气注引月令章句", "北郊六里，因水数也", "same", "这是'迎冬于北郊'的五郊迎气兆，以六为水数；与方坛不是同一设施"),
    Q("BJ7", "S103", "礼仪志上", "礼毕，次北郊，明堂，高庙，世祖庙，谓之五供", "same", "北郊在东汉礼仪中按年使用"),
    Q("BJ8", "G23", "二（七）南北郊坛段", "刘秀于建武中元元年立北郊坛于洛阳城北", "same", "二手综述：北郊坛在城北"),
]

# ---------------------------------------------------------------- 六类地点
# region: city-south（城南礼制） / south-suburb（南郊） / north-suburb（北郊）
SITES = [
    {"id": "lingtai", "name": "灵台", "region": "city-south", "group": "城南礼制四所",
     "assets": ["m-luoyang-lingtai (F-lingtai)"], "ly002": ["E-R04", "E-R08"],
     "phase": {"founded": "56（中元元年）", "foundedQuote": ["MT1"], "notYetInUse56": ["LT2"],
               "inUseBefore180": ["LT3"], "nearest180": "136年（LT3）；180年前后无专条，但礼制按年行用",
               "afterSnapshot": "185年南宫火烧的'灵台殿'是宫殿名，不涉此台（LT8）",
               "laterReuse": "北魏人仍见台基并归于汉光武（LT7）；遗址现存部分各期分属未核"},
     "positionText": ["LT4"], "otherHan": [],
     "unknown": ["台体原高、各层建筑东汉形态：未知（残高约8米≠原高；'高三丈'与米值换算为C）",
                 "围墙'每边长200米左右'属哪一期：未核原报告",
                 "高2023'50平方米左右的台基'量纲疑为边长（网上游记称约31×41米，来源不明，不采用）"]},
    {"id": "mingtang", "name": "明堂", "region": "city-south", "group": "城南礼制四所",
     "assets": ["m-luoyang-mingtang"], "ly002": ["E-R03", "E-R08"],
     "phase": {"founded": "56（中元元年）", "foundedQuote": ["MT1"], "notYetInUse56": ["LT2"],
               "inUseBefore180": ["LT3", "MT5"], "nearest180": "142年（MT5）",
               "afterSnapshot": "无",
               "laterReuse": "北魏正光年间在'辟雍之西南'另造明堂，上圆下方（MT8）。图1明堂正在辟雍西南，现遗址中心'圆形夯土基址'可能属北魏，分期未核"},
     "positionText": ["MT2", "MT3"], "otherHan": [],
     "unknown": ["东汉明堂与北魏正光明堂是否同址重建：未核（原报告未读）",
                 "'每面墙约长400米''直径61至62米'属哪一期：未核"]},
    {"id": "biyong", "name": "辟雍", "region": "city-south", "group": "城南礼制四所",
     "assets": ["m-luoyang-biyong"], "ly002": ["E-R05", "E-R08"],
     "phase": {"founded": "56（中元元年）", "foundedQuote": ["MT1"], "notYetInUse56": ["LT2"],
               "inUseBefore180": ["BY4", "BY5"], "nearest180": "177年冬十月（BY5）",
               "afterSnapshot": "无",
               "laterReuse": "北魏人称灵台东的辟雍为魏武帝所立（BY10）；遗址出西晋碑（BY9）。东汉辟雍是否即此遗址、哪些遗迹属东汉：未核"},
     "positionText": ["BY1", "BY2"], "otherHan": [],
     "unknown": ["东汉辟雍中心殿形制：未知", "环水分期、闭合与否：未核（BY7、BY8 为二手转引）",
                 "伽蓝记'魏武帝所立'与东汉中元元年始建如何并存：未定（可能是曹魏重建，也可能是追记有误）"]},
    {"id": "taixue", "name": "太学", "region": "city-south", "group": "城南礼制四所",
     "assets": ["m-luoyang-taixue-a (F-taixue-hall)", "m-luoyang-stoneclassic-access-court"], "ly002": ["E-R06", "E-R08"],
     "phase": {"founded": "29（建武五年）", "foundedQuote": ["TX0"], "notYetInUse56": [],
               "inUseBefore180": ["TX2", "TX3", "TX5", "TX6"], "nearest180": "176年（TX6）、182年（TX7）",
               "afterSnapshot": "182年仍幸太学（TX7）",
               "laterReuse": "131–132年顺帝重修，凡二百四十房、千八百五十室（TX2–TX4），180年的太学是这次重修后的状态；175年起石经立于门外（TX5），180年立碑数未知；魏晋以降遗址另有150×220米范围（TX10，禁作东汉）"},
     "positionText": ["TX1", "TX9", "TX11"], "otherHan": [],
     "unknown": ["东汉太学院落范围、讲堂确址：未知", "180年已立石经碑数：未知",
                 "'去宫八里'是西晋人以西晋宫城计（宫在北），不能用来定东汉太学与南宫的距离"]},
    {"id": "nanjiao", "name": "南郊（圆坛八陛）", "region": "south-suburb", "group": "南郊",
     "assets": ["m-luoyang-southern-altar"], "ly002": ["E-R01"],
     "phase": {"founded": "26（建武二年）", "foundedQuote": ["NJ1"], "notYetInUse56": [],
               "inUseBefore180": ["NJ4"], "nearest180": "礼仪志记每年正月上丁祠南郊（NJ4）；184年仍作京师地标（NJ5）",
               "afterSnapshot": "无",
               "laterReuse": "曹魏另营圆丘（NJ7）、北魏圜丘在洛水南伊洛之间（NJ8），均不是东汉南郊"},
     "positionText": ["NJ1", "MT3"], "otherHan": [],
     "unknown": ["遗址：未发现（NJ6 只说大郊村'有可能'）", "坛高、径、陛宽、营墙尺寸：未知",
                 "'七里'从城垣、城门还是宫门量起：未知；'七'与蔡邕'火数'相合（NJ3），可能是配数而非实测",
                 "东西方向：完全没有约束"]},
    {"id": "beijiao", "name": "北郊（方坛四陛）", "region": "north-suburb", "group": "北郊（单列）",
     "assets": ["m-luoyang-northern-altar"], "ly002": ["E-R02"],
     "phase": {"founded": "56营、57初祀（中元元年/二年）", "foundedQuote": ["MT1", "LT2"], "notYetInUse56": [],
               "inUseBefore180": ["BJ7"], "nearest180": "礼仪志记每年五供次北郊（BJ7）；180年前后无专条",
               "afterSnapshot": "无",
               "laterReuse": "未见后世沿用记录"},
     "positionText": ["BJ1", "BJ2", "BJ3"], "otherHan": [],
     "unknown": ["三说孰是：未定（四里/六里/西北角一里所，互相排斥）", "坛边长、高度、陛宽：未知",
                 "祠舍、中外营的数量与形态：未知", "地形（邙山坡麓）与古地面高程：未知",
                 "张璠'六里'与蔡邕'北郊六里，因水数也'（迎冬北郊兆）数字相同，可能混入五郊迎气兆"]},
]

# ---------------------------------------------------------------- 180安装层准入：候选数据项
# use: 'marker'=研究标记层  'install180'=约180年安装层（实体落位/尺寸）
GATE_ITEMS = [
    {"id": "P01", "site": "lingtai", "item": "图1灵台B描点", "phase": "EH-figure", "position": "B", "request": "install180"},
    {"id": "P02", "site": "lingtai", "item": "灵台围墙每边约200米、残高约8米（LT5、LT6）", "phase": "unverified", "position": None, "request": "install180"},
    {"id": "P03", "site": "mingtang", "item": "图1明堂B描点", "phase": "EH-figure", "position": "B", "request": "install180"},
    {"id": "P04", "site": "mingtang", "item": "明堂围墙每面约400米、中心圆基径61–62米（MT6、MT7）", "phase": "unverified+NW-overlap", "position": None, "request": "install180"},
    {"id": "P05", "site": "biyong", "item": "图1辟雍B描点", "phase": "EH-figure", "position": "B", "request": "install180"},
    {"id": "P06", "site": "biyong", "item": "辟雍环水东西各180余米、未闭合（BY7、BY8）", "phase": "unverified", "position": None, "request": "install180"},
    {"id": "P07", "site": "biyong", "item": "西晋三临辟雍碑及晋代遗迹（BY9）", "phase": "W-Jin", "position": None, "request": "install180"},
    {"id": "P08", "site": "taixue", "item": "图1太学B描点", "phase": "EH-figure", "position": "B", "request": "install180"},
    {"id": "P09", "site": "taixue", "item": "魏晋以降太学遗址150×220米（TX10）", "phase": "Wei-Jin+", "position": None, "request": "install180"},
    {"id": "P10", "site": "taixue", "item": "陆机讲堂长十丈、广三丈（TX1注）", "phase": "W-Jin", "position": None, "request": "install180"},
    {"id": "P11", "site": "nanjiao", "item": "南郊'城南七里'文本距离带", "phase": "EH", "position": "text-band", "request": "install180"},
    {"id": "P12", "site": "nanjiao", "item": "曹魏圆丘、北魏圜丘位置（NJ7、NJ8）", "phase": "Wei/NW", "position": None, "request": "install180"},
    {"id": "P13", "site": "beijiao", "item": "北郊三说候选包络", "phase": "EH+Jin", "position": "text-band-exclusive", "request": "install180"},
    {"id": "P14", "site": "beijiao", "item": "月令章句'北郊六里'（迎冬兆）当作方坛位置（BJ6）", "phase": "EH-other-facility", "position": None, "request": "install180"},
    {"id": "P15", "site": "lingtai", "item": "185年南宫'灵台殿'火灾当作城南灵台状态（LT8）", "phase": "after-180-other-facility", "position": None, "request": "install180"},
    {"id": "P16", "site": "lingtai", "item": "图1灵台B描点作研究标记", "phase": "EH-figure", "position": "B", "request": "marker"},
    {"id": "P17", "site": "mingtang", "item": "图1明堂B描点作研究标记", "phase": "EH-figure", "position": "B", "request": "marker"},
    {"id": "P18", "site": "biyong", "item": "图1辟雍B描点作研究标记", "phase": "EH-figure", "position": "B", "request": "marker"},
    {"id": "P19", "site": "taixue", "item": "图1太学B描点作研究标记", "phase": "EH-figure", "position": "B", "request": "marker"},
    {"id": "P20", "site": "nanjiao", "item": "南郊文本距离带作研究标记（不出点）", "phase": "EH", "position": "text-band", "request": "marker"},
    {"id": "P21", "site": "beijiao", "item": "北郊三说包络作研究标记（不出点）", "phase": "EH+Jin", "position": "text-band-exclusive", "request": "marker"},
]

# ---------------------------------------------------------------- 仓库出入（只报告，修改交LY-100/LY-098）
REPO_ISSUES = [
    {"id": "R-01", "file": "docs/cities/luoyang/data/research-unplaced.json", "where": "features[id=ritual_south].name",
     "found": "灵台、明堂、辟雍、太学这一组被命名为'南郊礼制区'", "issue": "'南郊'在东汉文献里专指城南七里的圆坛郊兆；把四所叫南郊会与南郊坛混组",
     "suggest": "改名'城南礼制区'，南郊坛另立一条 unknown-unplaced 记录", "to": "LY-100"},
    {"id": "R-02", "file": "docs/cities/luoyang/data/research-unplaced.json", "where": "features",
     "found": "没有北郊条目", "issue": "北郊在研究层里缺位，容易被归进城南或干脆忽略",
     "suggest": "新增 north_suburb（spatialState: unknown-unplaced，renderable: false，注三说互斥）", "to": "LY-100"},
    {"id": "R-03", "file": "docs/cities/luoyang/data/evidence/evidence-geometry.json", "where": "features",
     "found": "南郊坛、北郊坛都没有 null-geometry 的 list-only 条目", "issue": "两处有文献、无坐标，和北宫新墙段一样应该列名不落位",
     "suggest": "各加一条 geometry:null、placement_mode:none 的条目，北郊注明三说", "to": "LY-100"},
    {"id": "R-04", "file": "docs/cities/luoyang/p-luoyang.asset.json", "where": "progress[title=北郊方坛四陛].chapter",
     "found": "北郊方坛四陛记在 chapter 'ritual'，与城南灵台、太学等同一章", "issue": "展示分组上把北郊和城南礼制放在一起",
     "suggest": "北郊方坛加 region:'north-suburb' 或单列，卡片文字注明在城北", "to": "LY-098 / LY-100"},
    {"id": "R-05", "file": "docs/cities/luoyang/data/evidence/evidence-geometry.json", "where": "frame.calibration.original_raster_dimensions_px",
     "found": "记作 1284×1800；PDF内嵌图1实际为 373×594 像素（SHA da21a2c0…）", "issue": "本席位独立描点与冻结描点只差一个常量平移（约195.5, 932像素）且比例尺相同，说明冻结像素坐标来自另一张底图；底图来源未登记",
     "suggest": "在 frame 里登记底图来源与平移量；不影响现有米制数值", "to": "LY-100"},
]
