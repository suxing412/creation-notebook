"""LY-009 pause register (暂停区) specification.

An entry parks a matter that a seat cannot settle by itself. Rules:
  * a parked matter is not worked around: affected seats keep their own packages
    in their own LY-### directory, mark the parked part '未做', and do not
    substitute a guess;
  * every entry cites a source file and an exact quote that the builder re-finds
    (so the entry can be traced and re-checked); 'lab-git' sources are re-read
    with read-only git;
  * effect: 'blocks-merge' (seat may build, LY-100 may not merge the affected
    part), 'blocks-city' (local package only, no city placement),
    'blocks-start' (seat cannot start that part), 'advisory' (no blocking);
  * an entry is cleared only by the named decider; clearing is a new
    pause-zone version, the old entry is kept with clearedBy/clearedAt.
"""

PAUSES = [
    {
        'id': 'PZ-01', 'title': '基线漂移：lab origin/main 已越过 bce3211',
        'effect': 'blocks-merge',
        'seats': ['LY-010', 'LY-041', 'LY-042', 'LY-043', 'LY-044', 'LY-045', 'LY-046', 'LY-047', 'LY-048',
                  'LY-049', 'LY-050', 'LY-092', 'LY-100'],
        'detail': ('lab origin/main 在 bce3211 之后有 f28d650、b70c495（雍门接街，持锁方）与 cad338b（北缘三院，'
                   '住宅区由 44 院变为 47 院）。041–050、092 的「原44院计数」以 bce3211 为准；合并时 G 是否改基线须协调者定。'),
        'decider': '主协调者',
        'unblock': '协调者宣布 G 基线（保留 bce3211 或改到新 HEAD）；改基线则 LY-001/005/006 按各自 source/ 重跑。',
        'sources': [
            {'file': 'LY-005/status.json', 'quote': 'origin/main 在开工时已前进到 f28d650'},
            {'file': 'LY-007/status.json', 'quote': '收尾时 origin/main 已前进到 cad338b'},
            {'lab-git': 'cad338b:docs/cities/luoyang/progress-assets/north-three-v1/README.md', 'quote': '总数为47院'},
        ],
    },
    {
        'id': 'PZ-02', 'title': '南北宫与东北约束未能配准',
        'effect': 'blocks-city',
        'seats': ['LY-039', 'LY-061', 'LY-062', 'LY-063', 'LY-064', 'LY-065', 'LY-066', 'LY-067', 'LY-068',
                  'LY-069', 'LY-070', 'LY-084', 'LY-086', 'LY-088', 'LY-094'],
        'detail': '宫区没有任何双方都有数值坐标的共同控制点；宫院、复道、东北对外路与宫墙水道只能交局部包，不得落实名宫区。',
        'decider': 'LY-003（资料到位后重跑）→ LY-010 / LY-094',
        'unblock': 'LY-003 status 中列明的解除条件（≥2 个共同控制点及 2023 北宫墙段发掘平面）。',
        'sources': [{'file': 'LY-003/status.json', 'quote': '本轮一份也没拿到'}],
    },
    {
        'id': 'PZ-03', 'title': '城南礼制四所与南北郊位置未放行',
        'effect': 'blocks-city',
        'seats': ['LY-071', 'LY-072', 'LY-073', 'LY-074', 'LY-075', 'LY-076', 'LY-077', 'LY-078', 'LY-079',
                  'LY-080', 'LY-085', 'LY-094'],
        'detail': '四所只能停在 B 示意点；南郊坛与北郊方坛无位置放行，北郊三说未裁定。所有礼制包只交局部包。',
        'decider': 'LY-004 → LY-010 / LY-094',
        'unblock': '取得《汉魏洛阳故城南郊礼制建筑遗址》等原报告控制点并核清分期。',
        'sources': [{'file': 'LY-004/status.json', 'quote': 'LY-079、LY-080不能取得位置放行'}],
    },
    {
        'id': 'PZ-04', 'title': '平城「旧斜路」端口只有 ID 没有数值',
        'effect': 'blocks-start',
        'seats': ['LY-016', 'LY-017'],
        'detail': 'pingcheng-P-v1:old-ramp:ground 冻结了 ID 与版本，几何未找到；LY-017 的旧路联合装配须等 LY-016 交出实测文件与 SHA。',
        'decider': 'LY-016（交值）/ LY-006（registry v2）',
        'unblock': 'LY-016 交出旧斜路实测文件与 SHA，LY-006 回填端口。',
        'sources': [{'file': 'LY-006/status.json', 'quote': '只冻结了 ID 和版本，数值待补'}],
    },
    {
        'id': 'PZ-05', 'title': '示范院帧候选 C02-010 待 LY-010 冻结',
        'effect': 'blocks-start',
        'seats': ['LY-041', 'LY-042', 'LY-043', 'LY-044', 'LY-045', 'LY-046', 'LY-047', 'LY-048', 'LY-049', 'LY-050'],
        'detail': 'LY-006 以 C02-010（A2）为候选划区；LY-010 若另选，041–050 的帧与写入区整体重发 registry v2。',
        'decider': 'LY-010',
        'unblock': 'LY-010 决策表写明示范院。',
        'sources': [{'file': 'LY-006/status.json', 'quote': '示范院帧以 C02-010（A2，calt）为候选，由 LY-010 冻结'}],
    },
    {
        'id': 'PZ-06', 'title': 'LY-087 是否应依赖 LY-086（依赖图变更提案）',
        'effect': 'advisory',
        'seats': ['LY-086', 'LY-087'],
        'detail': 'LY-087 不依赖 LY-086，宫墙水道三段的 drain 端口没有接入排水一致性包。LY-009 不改原文依赖，只登记。',
        'decider': '主协调者',
        'unblock': '协调者决定是否给 LY-087 增加依赖 LY-086；若增加，taskboard 出 v3 并重算层级。',
        'sources': [{'file': 'LY-006/status.json', 'quote': 'LY-087 不依赖 LY-086'}],
    },
    {
        'id': 'PZ-07', 'title': '材质与导出的待制作人拍板项',
        'effect': 'advisory',
        'seats': ['LY-011', 'LY-012', 'LY-013', 'LY-014', 'LY-016', 'LY-018', 'LY-019', 'LY-020', 'LY-021',
                  'LY-024', 'LY-031', 'LY-032', 'LY-057', 'LY-096'],
        'detail': 'P-GENERATOR、P-NEWMAT、P-LEGACY、P-DOUGONG、P-TYPEGATE、P-STONE-COLOR 未拍板；暂行做法见 LY-007，新件照暂行做法交付并注明。（席位列表为示例：凡交新几何的补件席位都受影响。）',
        'decider': '制作人',
        'unblock': '制作人逐项拍板，LY-007 出新版。',
        'sources': [{'file': 'LY-007/status.json', 'quote': '待制作人拍板 P-GENERATOR'}],
    },
    {
        'id': 'PZ-08', 'title': '「31组重复宫殿」来源清单缺失',
        'effect': 'advisory',
        'seats': ['LY-061', 'LY-066', 'LY-070', 'LY-094'],
        'detail': '锁 LOCK-31PALACES 目前只能按名称禁用，无法逐件挂 SHA。',
        'decider': '主协调者',
        'unblock': '协调者提供 31 组清单（路径或 SHA）。',
        'sources': [{'file': 'LY-001/status.json', 'quote': '「被停用的 31 组重复宫殿」在 bce3211 的 docs、lab/data 与 git 历史中未找到'}],
    },
    {
        'id': 'PZ-09', 'title': 'LY-100 合并前须处理的既有仓库更正',
        'effect': 'blocks-merge',
        'seats': ['LY-098', 'LY-100'],
        'detail': ('sourceContracts 13 条中 12 条 SHA 只匹配 CRLF 检出字节（LY-001 C8）；雍门研究候选仍重复展示（LY-001）；'
                   '「旋门」应为「秏门」（LY-002 D-01）；R-01…R-05 礼制/北郊命名与归章（LY-004）。均归 LY-100 统一处理。'),
        'decider': 'LY-100 / 主协调者',
        'unblock': 'LY-100 在对应批次 manifest 中逐条写明处理结果。',
        'sources': [
            {'file': 'LY-001/status.json', 'quote': 'C8 未通过'},
            {'file': 'LY-002/status.json', 'quote': '应改为“秏门（旄、耗异写）”'},
            {'file': 'LY-004/status.json', 'quote': 'R-01 research-unplaced'},
        ],
    },
    {
        'id': 'PZ-10', 'title': 'taskboard.json 9 处 text 字段串入下一节导语',
        'effect': 'advisory',
        'seats': ['LY-010', 'LY-020', 'LY-030', 'LY-040', 'LY-050', 'LY-060', 'LY-070', 'LY-080', 'LY-090'],
        'detail': ('根 taskboard.json 里每节最后一个席位的 text 带上了下一节标题与导语（例如 LY-040 的 text 含「不触另行处理的13院片区」，'
                   '这条约束实际属于 041–050）。v2 把导语挂到所在节的每个席位（sectionIntro），text 与原文逐字一致。'),
        'decider': '主协调者',
        'unblock': '协调者用 LY-009/board/taskboard.v2.json 替换或修补根文件。',
        'sources': [{'file': 'LY-009/qa/parse-compare.json', 'quote': 'text-bleeds-next-section'}],
    },
    {
        'id': 'PZ-11', 'title': '地域准入不在依赖图里',
        'effect': 'advisory',
        'seats': ['LY-039', 'LY-061', 'LY-070', 'LY-071', 'LY-079', 'LY-080', 'LY-084', 'LY-086'],
        'detail': ('G 不含 LY-003/004（原文：它不自动替代LY-003/004的地域准入）。上述席位的原文依赖里没有 003/004，'
                   '可开工只表示能做局部包；是否能落城看 LY-010 决策表与 LY-094，不看本板的「可开工」。'),
        'decider': 'LY-010 / LY-094',
        'unblock': '不需要解除；是长期规则。',
        'sources': [{'file': 'TASKPOOL.md', 'quote': '它不自动替代LY-003/004的地域准入'}],
    },
    {
        'id': 'PZ-12', 'title': '持锁人身份没有登记',
        'effect': 'advisory',
        'seats': [],
        'detail': '「雍门接街」「13院压缩」的原负责人在 LY-009 可读的文件里没有写明姓名或会话；锁的 holder 只能写角色。',
        'decider': '主协调者',
        'unblock': '协调者在 locks.json v2 写入持锁人。',
        'sources': [{'file': 'TASKPOOL.md', 'quote': '由原负责人继续'}],
    },
    {
        'id': 'PZ-13', 'title': '13院锁的边界待持锁人确认',
        'effect': 'advisory',
        'seats': ['LY-041', 'LY-050', 'LY-092'],
        'detail': 'LOCK-13COURT 的路径集合由卡片文本与 LY-006 的冻结判断推出，未经持锁人确认；北缘三院（cad338b）明说与13院分离，未纳入本锁。',
        'decider': '13院原负责人 / 主协调者',
        'unblock': '持锁人确认或修订 LOCK-13COURT 路径集合。',
        'sources': [{'file': 'LY-006/brief.md', 'quote': '雍门和 13 院按保护清单冻结'},
                    {'lab-git': 'cad338b:docs/cities/luoyang/progress-assets/north-three-v1/README.md', 'quote': '与另待部署的13院区域分离'}],
    },
    {
        'id': 'PZ-14', 'title': '工作包里混入源工程、临时件与超限 GLB（workpacks 分支提交前须处理）',
        'effect': 'blocks-merge',
        'seats': ['LY-007', 'LY-008', 'LY-011', 'LY-016', 'LY-017', 'LY-076', 'LY-077'],
        'detail': ('LY-009 第一次扫描（约 23:00）有 22 个文件违反白名单 R3/R4：解出的源包 .blend/.zip 放在 prep/ 下，'
                   'LY-076、LY-077 的 prep 工作目录里有超过 15,000,000 字节的 GLB，LY-007/native/ 有 1 个 .blend。'
                   '23:17 起根目录出现未跟踪的 .gitignore（*.blend、*.zip、native/、_src/、tmp/ 等；作者未核实，按规则应为协调者），'
                   '被它挡住的文件不会进 git。最新扫描中仍未被挡住的违规见 qa/whitelist-scan.json 的 violationsNotIgnored'
                   '（本次为 LY-076 prep 里一个 25,848,260 字节的 GLB）。.gitignore 忽略 native/ 等于按 README 裁定「源工程不进分支」，'
                   '与任务池「native/ 与公共模型文件分开交付」的写法仍须协调者确认。LY-009 不动别席位的文件。'),
        'decider': '主协调者（native/ 规则、.gitignore 入库）；各席位（移出超限件）',
        'unblock': '.gitignore 由协调者提交；violationsNotIgnored 为空（check_whitelist --scan 为 PASS）。',
        'sources': [{'file': 'LY-009/qa/whitelist-scan.json', 'quote': 'source project / archive not allowed in workpacks branch'},
                    {'file': 'README.md', 'quote': '源工程（.blend、源 ZIP）不进这个分支'},
                    {'file': 'TASKPOOL.md', 'quote': '`source/`、`native/`：生成器、参数、可编辑源；与公共模型文件分开交付。'}],
    },
]
