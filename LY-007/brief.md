# LY-007｜冻结材质与三档质量基线

席位类型：考据/契约。前置：LY-001（交付完成）。唯一写入区：`workpacks/LY-007/`。lab 仓库只读：没有改、建、删文件，没有执行 git 写操作，也没有运行 `build_assets.py`。字节一律取提交 `bce3211f818ee5a8bef1773539da70695ba37b17` 的 blob。

## 1 这一席交了什么

这一席不做新建筑。工作是把风格提取工作流已有的成果（`LY-style-bible.md`、`ly_style.py`、S84/G10 顶点级复刻）整理成任务池要的冻结基线。基线里的数字都能用本目录的脚本对提交字节重算。

| 产物 | 文件 | 内容 |
|---|---|---|
| LY_P01 材质语义 | `baseline/LY_P01-material-semantics.json` | 五种材料（earth、timber、tile、path、paper__stone）的用途、三档材质名、FLAT 线性因子（从她的 GLB 读出的 float32 原值）、sRGB 整数色、PBR 贴图槽与字节 SHA、ORM 通道含义、颜色空间、禁用项 |
| 纹理 / UV 规则 | `baseline/texture-uv-rules.json` | 贴图库、颜色空间、世界盒式 UV（1 UV = 1 m，并列面规则）、像素密度、采样器、显存（只有理论估算，没有实测）、预览陷阱 |
| LOD 命名与近景保留 | `baseline/lod-rules.json` | 三档定义、命名（default / market / house_types）、逐类降档表、验收区间、LOD0 复制判据、近景保留规则、动件规则、样件逐档差异 |
| 冻结裁决与待拍板 | `baseline/decisions.json` | 规范 §11 的 19 行分歧（合并成 17 条记录）和 §12 的 13 条「未量到」逐条给出状态（冻结 / 冻结·暂行 / 待量 / 待制作人拍板），另有本席位复核中新发现的 5 条，以及 6 个需要制作人拍板的问题 |
| 规范冻结副本 | `baseline/LY-style-bible.frozen.md` | 与 `mq/style/LY-style-bible.md` 字节相同 |
| 贴图 | `textures/` | 她的原字节 PNG：512 和 256 各 11 张，另有旧灰 7 张（只用来识别旧卡）；附 manifest |
| 工具库 | `source/lib/ly_style.py` | 冻结副本，字节未改。用的时候设 `ly.TEX_DIR = <LY-007>/textures` |
| 基准球 | `models/refsphere/lyref-A-LOD{0,1,2}.glb` | 五种材料，每种一个基准球加一个 1.000 m 标定块，三档都有 |
| 样件 | `models/samples/{S84,G10}-LOD{0,1,2}.glb` | round2 复刻件，从 GLB 量尺寸后用库函数重建 |

## 2 验收项逐条

席位原文的四条验收要求，加上实测结果。可重算的检查列表见 `qa/checks.json`。

1. **基准物和纹理可重新读取。** 用 Blender 官方 glTF 导入器重读了 3 个基准球文件和 6 个样件，问题数都是 0（`qa/readback.json`）。逐项结果：
   - 材质 JSON 与语义表一致。
   - LOD2 的 FLAT 因子与语义表逐位相同。
   - 贴图字节都属于共享库，分辨率与档位对应。
   - 导入后底色图的颜色空间是 sRGB，ORM 和法线图是 Non-Color。

   贴图来源：22 张 LY_P01 贴图与她 GLB 里嵌入的 PNG 逐字节相同，29 张全部与 manifest 一致（`qa/texture-provenance.json`）。
2. **每档轮廓和细节的差异有说明。** 说明在 `baseline/lod-rules.json` 的 samples 段，量化数据在 `qa/lod-diff.json`。量化内容包括：三角数比例、每种材料的连通块数、包围盒差，以及正、侧、顶三个方向 2 cm 栅格的轮廓 IoU。

   | 样件 | LOD1/LOD0 | LOD2/LOD0 | 侧向轮廓 IoU（LOD1 / LOD2） |
   |---|---|---|---|
   | S84 | 0.309 | 0.09 | 1.0 / 0.968 |
   | G10 | 0.292 | 0.095 | 1.0 / 0.970 |

   LOD2 高度降了 0.0997 m，原因是瓦垄删掉了。她的原件也是这样。负例：把 LOD0 复制成 LOD1，被判成了「LOD0 复制」。
3. **原近景仍可恢复。** 证据见 `qa/near-retention.json`：
   - city-data 里 46 条 path/sha256 引用，按提交字节核对全部一致。
   - 6 条院落 nearPath 与对应的远档字节都不同。
   - 87 组同名三档里，没有一组的 LOD1 或 LOD2 与 LOD0 字节相同。
   - 每条都附了 `git show <commit>:<path>` 恢复命令。

   复刻件可以逐字节重出：用本目录的库和贴图重跑 round2，6 个文件全部字节相同（`qa/round2-rebuild.json`）。与她提交字节的原件比，6 个文件的顶点（位置、法线、UV）和三角形吻合率都是 1.0000（`qa/sample-vs-original.json`）。
4. **材质颜色空间、UV 尺度和贴图来源明确。**
   - 颜色空间见语义表的 color_space 段。
   - UV 尺度：五个 1.000 m 标定块，每个三角面的 UV 跨度都是 (1.0, 1.0)；世界盒式吻合率是 1.0。
   - 贴图来源：每张图都标了来源 GLB 和提交 SHA。

库自带的 9 项反例测试在冻结副本上全部通过（`qa/lib-negative-tests.json`）。其中一项确认：门扇单独节点在三档里都导出了，没有被焊进静态网格。

## 3 适用范围（必须读）

- **只在城门、礼制、市肆、住屋四族上验证过。** S84、G10 三档做到了顶点级复刻，G10、H64、H72、H96、S84、workshed、kaiyang、gate-A 逐三角核过 UV。
- **宫院和生产两族的事实来自分析员的部分输出**（`mq/style/palace`、`production`），没有逐三角复核。宫院指宫殿、廊、阙、武库等，生产指窑、磨、碓、灶等器物。涉及这两族的冻结值都标了「宫院/生产待复核」（decisions D-U09）。这两族的新件交付前，应各取一张她的卡，做与 S84/G10 同级的复刻。
- 基准球、标定块和各条「暂行做法」都属于 C 工程设计，不是她的模型，也不是历史构件。本席位不涉及史实，没有引用北魏、西汉或四川的任何尺寸。
- 五件不同的事，本席位各做到哪一步：
  - 「模型能读取」：基准件和样件做到了。
  - 「局部通行通过」：没做。
  - 「已入城」：不适用。
  - 「真实结构安全」：没做。
  - 「历史复原成立」：没做。

## 4 复核中的新发现（写进 decisions）

- **N1 材质顺序。** 规范写的是 earth→path→paper__stone→timber→tile，但她的 lingtai 和 workyard 是 earth→timber→tile 在前，path 或 paper__stone 跟在后面。冻结时以她的文件为准。

  库的 `_mat_rank` 有缺陷：非贪婪正则把 `paper__stone` 截成了 `paper`，排到最后；`MAT_ORDER` 又把 path 排在 timber 前面。所以基准球导出的顺序是 earth、path、timber、tile、paper__stone。这只影响 JSON 里的排列，不影响外观，S84/G10 不受影响。本席位没有改冻结库，修正提案写在 decisions N1-MATORDER 里。
- **N2 FLAT 粗糙度特例。** foot-pestle 的 timber__FLAT 是 0.90，属于器物族特例，不推广。生成语义表时，第一次误把这个值取了进来，已改为只从 lingtai 取四种材料。
- **D-LOD-BBOX。** 规范要求「三档包围盒差 ≤ 2 cm」，与住屋族实测不符：住屋 LOD2 低了 0.0997 m。冻结为：house 族 LOD2 允许下降 ≤ 0.10 m。
- **N3 预览陷阱。** Workbench 的 TEXTURE 模式会把 paper__stone__PBR 显示成亮黄色，因为它取到的是 stone-orm 图。她的 foot-pestle 在同一脚本下也是黄色。判断这种材料的颜色只能看 LOD2，不能看 Workbench 预览。
- **N4 功能判定只在 LOD0 上做。** S84 的柜台在 LOD2 被删掉了，LOD2 上没有员工通道。

## 5 现状普查（只记录，不改）

`qa/census-bce3211.{json,csv}` 把提交中 311 个洛阳 GLB 逐个与冻结基线对照：
- 81 个全项符合。
- 103 个材质名不合规范。
- 31 个含旧灰贴图，其中包括城中按章加载的 granary-city-LOD0。
- 101 个 UV 不是 1 m 世界盒投影。另有 12 个是带整体平移的 1 m 盒投影，外观等价。
- 147 个最低点不在 y=0，多数是地面补丁、院落 y=0.2 套件和城市坐标件，属于合理例外。
- 没有超过 15,000,000 字节的文件。

这是新件判据下的现状，不是要改旧卡的依据。任务池的边界是不全库换色。普查用的 UV 判据是本席位按 `inspect_glb` 规则另写的复算，对旧卡的分类只供参考。

收尾时 origin/main 已经前进到 `cad338b`：新增 4 个 GLB（yong-road-link-v2），没有改动或删除已有 GLB（`qa/census-cad338b.json`）。本基线仍然钉在 bce3211。

## 6 待制作人拍板（decisions 的 P 系列）

拍板之前，各项按括号里的暂行做法执行。

1. P-GENERATOR：是否接受 Blender 5.2.1 导出（generator 写 v5.2.40），还是要求在 4.3.2 上做最终导出？本机没有 4.3.2，也不会下载安装。（暂行：用 5.2.1 导出，generator 如实写，不手改。）
2. P-NEWMAT：是否引入第六种及以上材料？现状里已经有 brick、plaster、fiber、metal、cargo_proxy 等没有定调的角色。（暂行：新件只用五种。）
3. P-LEGACY：31 个旧灰文件是否迁移？（暂行：不迁移。）
4. P-DOUGONG：有证据时是否允许做斗栱？（暂行：不做。）
5. P-TYPEGATE：类型门「LOD1 实为最高档」的命名是否补正？（暂行：不改。）
6. P-STONE-COLOR：paper__stone 的浅色是不是有意做成的石色占位？（暂行：照原值。）

## 7 局限与诚实声明

- 所有预览都是 CPU 图，由 Blender 5.2.1 Workbench 渲染（`mq/render.py`）。没有做浏览器、GPU 或手机测试，显存只有理论估算。
- 私密源包（.blend、源 ZIP）没有取得。样件是从 GLB 重建的，不是她的原工程。基准球的源工程在 `native/lyref-A.blend`，不进 git。
- 本席位不产生公共文件，所以没有跑官方 `build_assets.py --check`。checker 归 LY-008。
- 越界记录：渲染时传了相对输出路径，Blender 把 63 张预览图写到了 `C:\tmp\r\`。发现后已全部移回 `tmp/r/`，并删除了本席位自己建的空目录 `C:\tmp\r`。`C:\tmp` 下的其他文件没有动过。
- 重算顺序写在 `delivery-manifest.json` 的 recompute 段。
