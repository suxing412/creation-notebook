"""LY-009 exclusion-lock specification (hand-written; resolved and verified by build_board.py).

Every lock names:
  poolQuote  - an exact substring of TASKPOOL.md that creates the lock (verified by the builder);
  holder     - who keeps write authority ('原负责人' means the pre-existing owner named in the pool,
               whose identity is NOT recorded in any file LY-009 can read);
  paths      - lab-repo globs; resolved against the baseline commit and origin/main, every
               matched blob is hashed (SHA256 of the committed bytes);
  cityNodes  - city-data node ids (cross-checked against LY-001 city-nodes.csv / LY-006 ownership);
  extRefs    - things outside the lab tree (other branches, workpack files, local dirs);
  keywords   - substrings used to list seats whose original text mentions the locked item
               (a text match, not a proof that the seat touches it);
  forbidden / allowed - what seats LY-011..099 and LY-100 may and may not do.
"""

COMMON_FORBIDDEN = [
    '交付替换、重做、改版或删除被锁文件/节点的成果包',
    '把被锁对象登记为本席位新建或新家族',
    'LY-100 合并时把非持锁人的改动写进被锁路径',
]
COMMON_ALLOWED = [
    '只读被锁文件与其冻结接口（LY-005/LY-006 端口）',
    '在自己工作包内做比对、测试和消费端口的子件',
]

LOCKS = [
    {
        'id': 'LOCK-YONG-ROAD', 'kind': 'protected-work', 'name': '雍门接街与雍门本体',
        'poolQuote': '雍门接街、13院模型压缩：由原负责人继续，任务池只读取冻结接口。',
        'holder': '原负责人（雍门接街）', 'holderRecorded': False,
        'paths': [
            'docs/cities/luoyang/progress-assets/yong-city-v1/**',
            'docs/cities/luoyang/progress-assets/yong-road-link-v2/**',
            'docs/library/models/m-luoyang-yong-gate/**',
            'docs/library/models/m-luoyang-yong-link/**',
            'docs/cities/luoyang/progress-assets/north13-gates/luoyang-yong-gate-study-v1/**',
            'docs/cities/luoyang/progress-assets/flat/study-north13-yong-Y-*',
            'docs/cities/luoyang/assets/city-wall/direct/wall-09.glb',
        ],
        'afterBaselinePaths': ['docs/cities/luoyang/progress-assets/yong-road-link-v2/**',
                               'docs/library/models/m-luoyang-yong-link/**'],
        'cityNodes': ['yong-gate-body', 'yong-gate-interface', 'research-north13-yong-Y', 'wall-direct-wall-09'],
        'extRefs': ['lab origin/main f28d650 / b70c495（持锁方在基线后继续提交的雍门接街）'],
        'keywords': ['雍门'],
        'release': '持锁人交出冻结接口版本并由协调者宣布解锁；任务池内不解锁。',
    },
    {
        'id': 'LOCK-13COURT', 'kind': 'protected-work', 'name': '13院片区与13院模型压缩',
        'poolQuote': '雍门接街、13院模型压缩：由原负责人继续，任务池只读取冻结接口。',
        'holder': '原负责人（13院压缩）', 'holderRecorded': False,
        'paths': [
            'docs/library/models/m-luoyang-residential-life/**',
            'docs/cities/luoyang/progress-assets/flat/study-north13-court-*',
            'docs/cities/luoyang/progress-assets/north13-gates/luoyang-north-four-courts-v2/**',
            'docs/cities/luoyang/progress-assets/north13-gates/luoyang-north-second-row-v1/**',
            'docs/cities/luoyang/progress-assets/north13-gates/luoyang-north-perimeter-v1/**',
        ],
        'scopeNote': ('m-luoyang-residential-life 卡片自述为「13院、26屋」布局候选（文本命中）；'
                      'research-north13-court-* 与 north13-gates 下三组院落/周界研究件归入本锁，'
                      '沿用 LY-006 的冻结判断，LY-009 未能从持锁人处确认边界，见暂停区 PZ-13。'),
        'cityNodes': ['research-north13-court-A', 'research-north13-court-A2', 'research-north13-court-B',
                      'research-north13-court-B2', 'research-north13-court-TC03-2'],
        'extRefs': ['lab origin/main cad338b README：北缘三院「与另待部署的13院区域分离」'],
        'keywords': ['13院'],
        'release': '同上。',
    },
    {
        'id': 'LOCK-12GATES', 'kind': 'protected-work', 'name': '十二门本体',
        'poolQuote': '十二门本体；井、灶、圈厕、厩、窑、磨、足碓、住屋、宫殿/廊、两坛、明堂、辟雍等现有原型。',
        'holder': '既有成果（本轮只读；仅子件/接口席位可交独立子件）', 'holderRecorded': True,
        'paths': [
            'docs/library/models/m-luoyang-%s-gate/**' % g for g in
            ['guangyang', 'kaiyang', 'pingcheng', 'gu', 'xia', 'yong', 'jin', 'mao', 'shangdong',
             'shangxi', 'xiaoyuan', 'zhongdong']
        ] + [
            'docs/cities/luoyang/assets/city-wall/direct/gate-body-only.glb',
            'docs/cities/luoyang/progress-assets/mao-gate/**',
            'docs/cities/luoyang/progress-assets/north13-gates/luoyang-*-gate-study-*/**',
        ],
        'expectCount': {'gateCards': 12},
        'cityNodes': ['wall-direct-gate-body-only', 'research-north13-shangxi-X', 'research-north13-zhongdong-Z',
                      'research-mao-gate'],
        'extRefs': [],
        'keywords': ['十二门', '门家族总数'],
        'release': '本轮不解锁；门数恒为12（LY-091验收）。',
    },
    {
        'id': 'LOCK-PROTOTYPES', 'kind': 'protected-work', 'name': '现有原型（井、灶、圈厕、厩、窑、磨、足碓、住屋、宫殿/廊、两坛、明堂、辟雍）',
        'poolQuote': '十二门本体；井、灶、圈厕、厩、窑、磨、足碓、住屋、宫殿/廊、两坛、明堂、辟雍等现有原型。',
        'holder': '既有成果（本轮只读）', 'holderRecorded': True,
        'paths': [
            'docs/model-library/well-study/**',
            'docs/library/models/m-luoyang-cooking-stove/**',
            'docs/library/models/m-luoyang-service-court/**',
            'docs/library/models/m-luoyang-household-service/**',
            'docs/library/models/m-luoyang-stable/**',
            'docs/library/models/m-luoyang-tile-kiln/**',
            'docs/library/models/m-luoyang-hand-mill/**',
            'docs/library/models/m-luoyang-foot-pestle/**',
            'docs/library/models/m-luoyang-ordinary-house-types/**',
            'docs/library/models/m-luoyang-house-roof/**',
            'docs/model-library/m-courtyard-family.asset.json',
            'docs/model-library/updates/m-courtyard-family/**',
            'docs/library/models/m-luoyang-deyang-hall/**',
            'docs/library/models/m-luoyang-yutang-halls/**',
            'docs/library/models/m-luoyang-palace-gallery/**',
            'docs/library/models/m-luoyang-southern-altar/**',
            'docs/library/models/m-luoyang-northern-altar/**',
            'docs/library/models/m-luoyang-mingtang/**',
            'docs/library/models/m-luoyang-biyong/**',
        ],
        'cityNodes': [],
        'extRefs': [],
        'keywords': ['原型'],
        'release': '本轮不解锁；补件只交兼容子件/安装包，原件不改。',
    },
    {
        'id': 'LOCK-MARKET-V21', 'kind': 'protected-work', 'name': '市肆S84/S86柜台与店前线v2.1',
        'poolQuote': '市肆S84/S86柜台和店前线v2.1、武库B门框枢轴v2.2、灵台五处踏步、复道A服务登临节点：已有修订，不再派相同修复。',
        'holder': '既有修订（只读）', 'holderRecorded': True,
        'paths': ['docs/library/models/m-luoyang-market-modular-assembly/**',
                  'docs/library/models/m-luoyang-market-frontage/**'],
        'cityNodes': [], 'extRefs': [],
        'keywords': ['S84', 'S86', 'v2.1', '柜台'],
        'release': '不再派相同修复。',
    },
    {
        'id': 'LOCK-WUKU-B22', 'kind': 'protected-work', 'name': '武库B门框枢轴v2.2',
        'poolQuote': '武库B门框枢轴v2.2',
        'holder': '既有修订（只读）', 'holderRecorded': True,
        'paths': ['docs/library/models/m-luoyang-wuku/files/wuku-B-LOD*.glb'],
        'cityNodes': [], 'extRefs': [],
        'keywords': ['v2.2', '武库B'],
        'release': '不再派相同修复。',
    },
    {
        'id': 'LOCK-LINGTAI-STEPS', 'kind': 'protected-work', 'name': '灵台五处踏步',
        'poolQuote': '灵台五处踏步',
        'holder': '既有修订（只读）', 'holderRecorded': True,
        'paths': ['docs/library/models/m-luoyang-lingtai/**',
                  'docs/cities/luoyang/progress-assets/lingtai-quality-v1/**',
                  'docs/model-library/lingtai/**'],
        'cityNodes': [], 'extRefs': [],
        'keywords': ['灵台'],
        'release': '不再派相同修复；LY-076 只补未修台缘与绕行。',
    },
    {
        'id': 'LOCK-GALLERY-A', 'kind': 'protected-work', 'name': '复道A服务登临节点',
        'poolQuote': '复道A服务登临节点',
        'holder': '既有修订（只读）', 'holderRecorded': True,
        'paths': ['docs/library/models/m-luoyang-gallery-access/**'],
        'cityNodes': [], 'extRefs': [],
        'keywords': ['复道A'],
        'release': '不再派相同修复。',
    },
    {
        'id': 'LOCK-GRANARY-NEAR', 'kind': 'protected-work', 'name': '太仓原位近景',
        'poolQuote': '太仓原位近景已接入',
        'holder': '既有成果（只读）', 'holderRecorded': True,
        'paths': ['docs/cities/luoyang/progress-assets/granary-city-v1/**',
                  'docs/model-library/m-storage-functional.asset.json',
                  'docs/model-library/updates/m-storage-functional/**'],
        'cityNodes': [], 'extRefs': [],
        'keywords': ['太仓'],
        'release': '不重复制作；031–035 只交门扇枢接、启闭与前场子件。',
    },
    {
        'id': 'LOCK-NE-196C', 'kind': 'protected-work', 'name': '东北约196米C短路',
        'poolQuote': '东北约196米C短路也早已有候选，不重复制作。',
        'holder': '既有候选（只读）', 'holderRecorded': True,
        'paths': [],
        'cityNodes': [],
        'extRefs': ['lab origin/luoyang-content city-visible 分卷 ZIP 内 northeast_C_access.glb（不在 docs 树）',
                    'workpacks LY-006/qa/chunks/northeast_C_access.glb sha256 58f2f58a464183e20d5489b13902f62f2570573cb8bf96fb237df781027d076e'],
        'extFiles': [{'path': 'LY-006/qa/chunks/northeast_C_access.glb',
                      'sha256': '58f2f58a464183e20d5489b13902f62f2570573cb8bf96fb237df781027d076e'}],
        'keywords': ['196'],
        'release': '不可再造、不可延成东北主干路；LY-039 只重绑定。',
    },
    {
        'id': 'LOCK-SOURCE-RELEASE', 'kind': 'protected-work', 'name': '源包净化与Release归档',
        'poolQuote': '正在独立进行的源包净化/Release归档不由普通模型代理接管。',
        'holder': '主协调者', 'holderRecorded': True,
        'paths': [], 'cityNodes': [],
        'extRefs': ['D:/GitHub/creation-notebook-待传/**', 'GitHub Releases（suxing412/creation-notebook）',
                    'lab origin/luoyang-content 分支'],
        'keywords': ['Release'],
        'release': '不下放；LY-099 只核已授权目录，不上传、不覆盖旧源包。',
    },
    {
        'id': 'LOCK-31PALACES', 'kind': 'protected-work', 'name': '被停用的31组重复宫殿',
        'poolQuote': '被停用的31组重复宫殿不能用来填南北宫，也不能当考据布局输入。',
        'holder': '主协调者（清单未交）', 'holderRecorded': False,
        'paths': [], 'cityNodes': [],
        'extRefs': ['来源清单缺：LY-001 在 bce3211 docs、lab/data 与 git 历史中未找到（LY-001 status openItems）'],
        'keywords': ['31组'],
        'release': '协调者交出清单后，按清单逐件挂锁；之前只按名称禁用。',
    },
    # ---------- shared files (pool: 共享文件禁写) ----------
    {
        'id': 'LOCK-SHARED-CITY', 'kind': 'shared-file', 'name': '共享城市文件、项目卡、构建数据、全局UI',
        'poolQuote': 'LY-001—099不得直接修改main、共享 `city-data.mjs`、项目卡 `p-luoyang.asset.json`、全站分类/构建数据或全局UI；只交独立分支/overlay和语义合并提案。',
        'holder': 'LY-100（按主协调者授权）', 'holderRecorded': True,
        'paths': ['docs/cities/luoyang/city-data.mjs', 'docs/cities/luoyang/p-luoyang.asset.json',
                  'docs/cities/luoyang/app.mjs', 'docs/cities/luoyang/city-renderer.mjs',
                  'docs/cities/luoyang/index.html', 'docs/cities/luoyang/v1/**', 'docs/cities/luoyang/data/**',
                  'docs/asset-spec/**', 'lab/data/**', 'lab/tools/**', 'docs/*.html', 'docs/model-library/registry.json'],
        'cityNodes': [], 'extRefs': ['lab main 分支（任何提交）'],
        'keywords': [],
        'appliesTo': 'ALL',
        'release': '不下放。',
    },
    {
        'id': 'LOCK-PUBLIC-DOCS', 'kind': 'shared-file', 'name': '全部公共文件（lab 仓库 docs/ 与 lab/）',
        'poolQuote': '所有公共文件另走LY-100。',
        'holder': 'LY-100（按主协调者授权）', 'holderRecorded': True,
        'paths': ['docs/**', 'lab/**'], 'cityNodes': [], 'extRefs': [],
        'keywords': [], 'appliesTo': 'ALL',
        'release': '不下放。',
    },
    # ---------- rights ----------
    {
        'id': 'RIGHT-PUBLISH', 'kind': 'right', 'name': '发布账户（push、Release 上传、Pages 部署、对外通信）',
        'poolQuote': '本任务池本身不授权新账号、插件、付款、对外通信或任意发布。远端提交、Release上传、源包落盘和发布仍由主协调者按已有授权安排，不能借“代理有100个”扩展权限。',
        'holder': '主协调者', 'holderRecorded': True,
        'paths': [], 'cityNodes': [], 'extRefs': ['git push 任意远端', 'gh release', 'GitHub Pages'],
        'keywords': [], 'appliesTo': 'ALL',
        'release': '不下放；LY-100 也只在主协调者逐批授权后提交。',
    },
    {
        'id': 'RIGHT-CITY-WRITE', 'kind': 'right', 'name': '城市写入权',
        'poolQuote': '只有此席位可写共享城市/项目文件；仍按主协调者授权提交发布。',
        'holder': 'LY-100', 'holderRecorded': True,
        'paths': [], 'cityNodes': [], 'extRefs': [],
        'keywords': [], 'appliesTo': 'ALL',
        'release': '不下放；区域装配包不能自动激活城市。',
    },
    {
        'id': 'RIGHT-TASKBOARD', 'kind': 'right', 'name': '任务板根文件（TASKPOOL.md、taskboard.json、README.md）',
        'poolQuote': '每个代理只写 `workpacks/LY-###/` 下自己的工作包，原输入只读。',
        'holder': '主协调者', 'holderRecorded': True,
        'paths': [], 'cityNodes': [], 'extRefs': ['workpacks/TASKPOOL.md', 'workpacks/taskboard.json', 'workpacks/README.md'],
        'keywords': [], 'appliesTo': 'ALL',
        'release': 'LY-009 只在 LY-009/board/ 交 v2 提案，由协调者决定是否替换根文件。',
    },
]
