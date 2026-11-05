# LY-008 建立可重跑交付检查器

- 类型：考据/契约。依赖 LY-001、LY-005、LY-007（都已交付）。
- 基线：`D:/GitHub/creation-notebook-lab` @ `bce3211f818ee5a8bef1773539da70695ba37b17`，只读。
- 产物：单文件检查器 `source/ly_check.py`（Python 3.11 + numpy，可选 Pillow），有命令行入口，加上负例生成、自检、官方 checker 调用、普查标定和汇总脚本。
- 本席位不产模型，不写公共文件。检查器要不要进仓库（比如放进 `lab/tools/`）由 LY-100 走合并队列决定。

## 检查器管什么

| 子命令 | 查什么 |
|---|---|
| `glb <file…> [--profile base\|ly-p01] [--lod N] [--tex-manifest …] [--upload-limit B --upload-encoding raw\|base64]` | 容器层：魔数、版本、头部长度与实际长度、块长度、4 字节对齐、JSON 块。数据层：buffer、bufferView、accessor 越界，索引越界，NaN/Inf（顶点数据和 JSON 字面量都查），POSITION 的 min/max 是否存在、是否与数据相符，法线是否单位长，退化三角。贴图：材质→texture→image 的引用链；外部 uri 判为未内嵌，文件不存在判为缺失；魔数与 mimeType 是否一致；PNG 结构与 CRC；Pillow 解码复核。私密路径：JSON 的全部字符串、PNG 文字块、BIN 块。路径越界：image/buffer 的 uri。体积：正式上限 15,000,000 字节。面数：上限 500,000（官方口径）。`ly-p01` 档再按 LY-007 冻结基线加查：材质名、PBR/FLAT 与档位是否对应、禁用项、doubleSided、贴图分辨率（LOD0 512²、LOD1 256²、LOD2 无图）、贴图字节是否是她的原字节、旧灰调色板、静态节点有没有 TRS、Blender `.001` 后缀、顶点属性集、世界盒式 UV（从 `ly_style.inspect_glb` 移植的同一判据）、平直法线、是否落地 |
| `lodset <LOD0> <LOD1> <LOD2> [--family house\|default]` | 三档字节相同或几何哈希 + 贴图分辨率 + 材质名都相同，判为 LOD0 复制改名；几何相同，判为没降档；三角数必须逐档减少；三角比超出 [0.17, 0.62] / [0.05, 0.20] 记警告；LOD1 包围盒必须与 LOD0 逐值相同；LOD2 ≤ 0.02 m，house 族顶部允许下降 ≤ 0.10 m（LY-007 D-LOD-BBOX） |
| `package <LY-###>` | 席位交付包：清单（`files` 或 `whitelist`）里每个文件是否存在，大小和 SHA256 是否一致；路径必须是包内相对路径（不能有 `..`、绝对路径、反斜杠，也不能经链接跑出包外）；包内 GLB 逐个过 `glb`，登记 `expectFail: true` 的负例夹具必须判出错误；文本文件扫私密路径：public 文件命中强判据记错误，内部文件只记警告 |
| `privacy <docs>` | 把要公开的整棵目录当公共内容扫：文本文件私密路径（强判据记错误，`/home/` 式弱判据记警告）、源工程扩展名（与官方 SOURCE 正则相同，已登记归档的除外）、链接越界 |
| `official <导出副本>` | 在副本里跑官方 `python -I lab/tools/build_assets.py --check`，记录规范版本、四个规范文件的 SHA、命令、退出码和 report.json 计数。目录里有 `.git`（也就是原仓库）就拒绝运行 |

退出码：有错误为 1，只有警告为 0。每条问题都有稳定的代码，自检按代码断言。

## 结论（全部可重算，SHA 见 qa/checks.json）

1. **负例都能被判出，好样本都能通过。** 77 个用例，其中负例 46 个，46 个都判出了期望的错误代码，退出码都是 1；正例 31 个都通过，退出码都是 0。覆盖范围：
   - 坏长度：头部长度 +8、截断 1000 字节、BIN 块长度越界、坏魔数；
   - NaN/Inf：顶点、UV、JSON 字面量；
   - 缺纹理：texture 索引不存在、image 来源不存在、外部图片文件不存在、PNG 头被毁、贴图材质缺 UV；
   - 体积：15,000,004 字节判错；恰好 15,000,000 字节通过（边界）；面数超过 500,000 判错；
   - 私密路径：`C:/Users/…` 写进 extras、`D:/GitHub/…` 当节点名、用户名混进 generator、PNG tEXt 块里藏 `C:\Users\…\AppData`；
   - 越界相对路径：image uri `../../…`、buffer uri `../outside/…`、清单路径 `../`、清单写盘符绝对路径、清单用反斜杠夹 `..`；
   - 其他：accessor/bufferView/索引越界、min/max 错，LY_P01 材质名、档位、贴图分辨率、静态节点 TRS、UV 平移、非她的贴图字节，三档复制改名、对调、按错家族判，清单大小/SHA 错、文件缺失、包含坏 GLB、负例夹具失效。

   自检逻辑本身也做了反证：把好样件当成"应失败"、把 NaN 件当成"应通过"，两次都被判为自检不通过（`qa/selftest.json` harnessSanity）。好样本就是 LY-007 交付的 9 个 GLB 原字节，SHA 与它的清单逐个一致（C3）。负例由 `make_negatives.py` 生成，重跑后 cases.json 里记录的 SHA 全部不变，56 个有记录的输入文件当场重算 SHA 也都一致（C2）。
2. **正式上限和上传承载分开判。** 14,000,000 字节的文件在正式上限之内（B12 通过，上传一栏记 not-judged）；给出 `--upload-limit 15000000 --upload-encoding base64` 后，按 base64 承载 18,666,668 字节，判 `UPLOAD_OVER_CHANNEL_LIMIT`（N12）。这条判据只在给出具体通道上限时启用。本席位没有拿到任何真实上传通道的上限，所以没有替任何通道下结论。
3. **官方 checker 只在导出副本里跑。** 每次都重新执行 `git -C <lab> -c core.autocrlf=false archive bce3211 | tar -x -C tmp/repo`，再逐文件核 git blob id，4411 个 blob 全部相同。运行命令是 `python -I lab/tools/build_assets.py --check`，cwd 设为副本，`GIT_CEILING_DIRECTORIES` 设为副本的上一级。规范版本 spec = 1，限值 glbMaxMB 15、glbWarnMB 5、trianglesMax 500,000、trianglesWarn 150,000。四个规范文件的提交字节 SHA 见 inputs.json。结果：
   - 基线：退出码 0，89 张卡，0 张有错误，50 张有警告；
   - 注入 12 张负例/正例卡和 1 个 `.blend` 后：退出码 1，超体积、超面数、越界路径、坏索引、`.blend` 都被判出；
   - 撤回后：退出码 0，计数与基线相同；
   - 对原仓库调用会被拒绝，build_assets 没有运行；
   - 原仓库前后的 HEAD 和 `git status --porcelain` 完全一致。
4. **官方 checker 有覆盖缺口，所以合并队列两者都要跑。** 截断文件、头部长度错、NaN 顶点、texture 索引缺失、外部贴图缺失、extras 里写私密路径，这 6 种情况官方都判为通过，ly_check 都判出（C5）。反过来，卡片字段（title、summary、cover 等）只有官方查。
5. **用 bce3211 的真实文件做了标定。** docs 下 442 个 GLB 全部重跑：
   - 字节、三角、顶点、图元、材质、贴图六项统计与官方 `glb_audit.audit` 442/442 一致；
   - 与 LY-001 账本重叠的 373 个文件，提交字节 SHA 也全部一致；
   - 0 个错误。警告有：GLB_LARGE 9 个，HIGH_DRAWCALLS 6 个，GEOM_TRI_HIGH 3 个，GEOM_DEGENERATE 3 个（武库 B 三档，与 LY-001 的记录相符），NODE_NONUNIT_SCALE 1 个（fusions/F02），GEOM_DRAWN_TRI_OVER_LIMIT 1 个，GLTF_UNUSED_MESH 1 个。

   第一轮普查暴露了检查器自己的三处毛病，已修正并加了回归正例 R01–R03：
   - UNC 判据在贴图二进制里误报 39 个文件；
   - meshopt 回退缓冲被误判为没有数据来源；
   - 三角数按实例计数，与官方按 mesh 计数的口径不同。

   第一轮的原始结果保存在 `qa/census-round1-falsepositives.json`。
6. **前置席位交付包都通过。** LY-001（25 项）、LY-005（82 项）、LY-007（95 项）的清单大小和 SHA 全部一致，没有路径越界，包内 GLB 没有错误。三个包的内部文件里都有本机路径，只记警告：这些包不公开，但内容不能原样搬进 docs。
7. **公共 docs 有一处真实发现。** bce3211 的 `docs/asset-spec/README.md` 里有 2 处 `D:/` 盘本机路径（源包落盘目录和待删目录的说明），判为 `PRIVATE_PATH_PUBLIC_FILE`。本席位不改公共文件，交给 LY-100/协调者决定是否改写。另有 8 个 study 脚本带 `/home/agent/` 清洗正则，按弱判据只记警告。

## 没做到 / 局限

- 只做了文件层和数据层的静态检查，没有做浏览器、GPU、手机实测，也没有判渲染是否正确。"模型能读取"在这里只表示数据结构合法、数值有限、引用完整，不等于"已入城"、"局部通行通过"、"真实结构安全"或"历史复原成立"。
- ly-p01 档的判据来自 LY-007 冻结基线。LY-007 自己说明宫院和生产两族的数字来自分析员的部分输出、待复核；它们只影响这两族的三角比和包围盒判据（警告级或 house/default 家族选择）。
- 接触、穿插、浮空、通行不在本检查器范围（ly_style 的 check_* 需要 Blender 与构件参数）。
- 私密路径是正则判据：强判据可能漏掉换了写法的路径（如 URL 编码、拆开拼接）；BIN 块只查成词的严格模式，以免像素数据误报。
- 三角上限采用官方口径（每个 mesh 定义计一次）。按场景实例绘制的三角数超限只记警告（life-block-LOD0 实例绘制 506,828，官方口径 116,108），哪种口径算准由 LY-100/制作人定。
- 压缩几何（meshopt）不解压，只统计 accessor 计数，几何数值检查跳过，报告里 `geometryRead: false`。
- 运行环境：Windows 11，Python 3.11.9，numpy 2.4.6，Pillow 12.3.0。注意 Windows 上 `git archive` 在 `core.autocrlf=true` 时会把文本文件转成 CRLF，所以导出命令必须带 `-c core.autocrlf=false`，否则副本字节与提交不一致（本席位第一次导出时就是这样，已改正）。
