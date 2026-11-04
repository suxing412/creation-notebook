# 评审 · r2026.11.04-1（72ad723，2026-11-04 09:36）
本次合并：无　对比基准：59b5a65

## 结论（一句总评 + 最要紧的三条）

**网页这一批修得扎实：W1–W6 六条里五条已修，一条部分修；内容侧只修了 C1，其余模型问题（C2–C8）原样未动。** GLB 一个字节都没变（158 个，SHA-256 全同），所以模型层面的可复用性没有任何进展。

最要紧的三条：
1. **C2〔高〕仍未修**：158 个 GLB 中 139 个缺 UV，4631/7122 个图元无 UV，和基线完全一样。新进来的灵台/太学已经带 UV，说明管线做得到，建议回补存量建筑类资产。
2. **W7〔中，新〕院落实时 3D 地面出现斜向条纹**：W2 加了阴影后，院子地面和房屋背面有明显的条纹，疑似阴影痤疮（shadow acne）。手机上尤其明显。
3. **C9〔中，新〕灵台、太学两组新内容进库前要先解决 draw call 和外链**：灵台 737 个网格 / 4 个材质，太学 160–188 个网格 / 3 个材质；`docs/model-library/{lingtai,taixue}/metadata.json` 的模型地址全部写成 `raw.githubusercontent.com/.../main/...` 绝对地址。

## 本版改了什么

**资产（伊苏里亚）**
- `docs/model-library/assets/courtyard.png` 重渲（C1）：现在是开敞院子加两栋房和门亭，对得上 A 方案。
- 新增 `modeling-lab/content/luoyang/lingtai-quality-v1/` 和 `taixue-long-hall-v1/`：源码分卷 ZIP、`display/` 下的 .gltf + .bin（含 LOD1），以及 `docs/model-library/lingtai/`、`taixue/` 的封面和 metadata。状态写的是「content-branch research archive; not integrated into website or city」，**目前没有任何页面引用它们**。
- 新增 `docs/cities/luoyang/research/2026-11-04/` 四张研究图（C032 街区、四院封闭/街景），同样没有页面引用。

**网页（Codex）**
- 新增 `docs/thumbnails/`：每张卡片图出 300/600 宽 WebP 两档，加 `srcset`/`sizes`，`manifest.json` 记来源尺寸和哈希；生成脚本 `modeling-lab/gallery/build_thumbnails.py`（W1）。
- `inspect.mjs` 重写：`RoomEnvironment` + `PMREMGenerator`、ACES 色调映射、软阴影（W2）；详情页改成「3D浏览 / 作品介绍」两个页签，可换背景色。
- 19 个详情页的线上绝对地址全部改成相对路径（W3）。
- 新增霞鹜文楷子集 `docs/fonts/notebook-hand.woff2`（137 KB，679 字，附 OFL 许可），只用于四个入口页的标题（W4）。
- 网页库补了 002/003/004/012/014 五张网页截图（W5）。
- 卡片 alt 改用 catalog 里的描述性文字，去掉「静态 CPU」等内部标签，下拉框改成「悬浮圣器 · 主模型」这类名称；导航和筛选控件加高（W6）。
- 新增 `modeling-lab/gallery/qa/r2026.11.04-1/verification.json` 和两张查看器截图，自带验收记录，值得肯定。

## 旧问题复审

| 编号 | 问题 | 上次 | 本次 | 判据 |
|---|---|---|---|---|
| C1 | 院落组封面画的是别的东西 | 未修 | **已修** | 新 `courtyard.png`（1200×900）是开敞院子、两栋房加门亭，和 A-LOD0 实时画面一致。见 `evidence/r2026.11.04-1/changed-covers.jpg` 左上、`courtyard-3d-desktop.jpg` |
| C2 | 绝大多数模型没有 UV | 未修 | 未修 | GLB 审计与基线完全相同：139 个文件、4631/7122 个图元缺 UV。158 个 GLB 的 SHA-256 没有一个变化 |
| C3 | LOD 只减面数，没减贴图和 draw call | 未修 | 未修 | 同上，GLB 未变 |
| C4 | 同材质图元没合并 | 未修 | 未修 | 图元最多的仍是 `market-A-N2-local.glb`（554 图元 / 10 材质）。新增的灵台、太学也有同样的问题，见 C9 |
| C5 | 封面质量参差 | 未修 | 部分修 | 院落封面已换（随 C1）。市肆、仓储仍是带文字横幅的俯视图板，600 宽缩略图里横幅字读不出；001 仍是竖图；014 主体仍小、背景仍深。见 `model-library-thumbs.jpg` |
| C6 | 形体习作细节层级偏低（设计意见） | 未修 | 未修 | 002/006/007/008/010 GLB 未变 |
| C7 | 尺度单位不统一 | 未修 | 未修 | 存量 GLB 未变。新的灵台/太学 metadata 已写 `"units": "metres"` 和轴向，做法正确，可推广到存量 |
| C8 | 重复文件没标明 | 未修 | 未修 | `gate-roof-study.html` 下载区仍分别列出 `gate-far-local.glb` / `gate-original.glb`、`gate-near-local.glb` / `gate-roof.glb`，没有「同一文件」说明 |
| W1 | 卡片图太重 | 未修 | **已修** | 模型库首屏 144 KB（其中字体 137 KB），20 张图全部加载后整页约 301 KB（基线 21.4 MB）。首页约 191 KB，网页库约 278 KB，空间库约 168 KB。600 宽 WebP 每张 3–34 KB，实测尺寸确为 600 宽 |
| W2 | 实时查看器光照太平 | 未修 | 部分修 | 001 金属有明确高光和投影，见 `archive-001-3d-desktop.jpg`，这一半已修。院落的墙体侧面和地面能分开了，但墙顶和院地仍几乎同一亮度，且新出现地面条纹，见 W7 |
| W3 | 详情页写死线上地址 | 未修 | **已修** | `grep -c suxing412.github.io docs/model-library/*.html */index.html` 全部为 0；001 详情页查看器加载的是 `/studies/001/assets/aether-reliquary.glb` |
| W4 | 手账主题依赖 Windows 楷体 | 未修 | **已修** | 入口页 h1 的计算字体为 `"Notebook WenKai", KaiTi, …`，`document.fonts` 显示已加载；子集清单写明 681 字请求、679 字收录，只有 `↝` `✳` 两个符号回落。没在真机上看 |
| W5 | 网页库缩略图不统一 | 未修 | **已修** | 13 张卡片全是网页截图，5 张新图的 alt 也写成「X网页首屏……」。小瑕疵见 W8 |
| W6 | 面向访客的文案和标签 | 未修 | **已修** | 首页与模型库正文里「静态CPU」出现 0 次；alt 改成描述性文字；375 宽下导航项和筛选控件都 ≥44 px；详情页按钮 44 px，页签 63 px。剩余的卡片标题链接为 34 px，属正文链接，可以接受 |

## 新问题 · 给伊苏里亚（内容与模型）

### C9 〔中〕灵台、太学进库前：网格过碎，metadata 用了线上绝对地址
- **现象**：两组都标「independent-display-study」，目前没有页面引用，所以还不影响线上。但在接进模型库之前有两处要先改。
- **证据**：
  - `docs/model-library/lingtai/metadata.json`：LOD0 有 738 个网格、4 个材质，38 万面；LOD1 仍有 737 个网格（2.1 万面）。LOD1 只减了面，draw call 一点没降，和 C3 是同一个问题。
  - `docs/model-library/taixue/metadata.json`：hall-A 161 个网格 / 3 个材质，hall-B 188 / 3；LOD1 分别 160、187。完整档 26–32 MB。
  - 两份 metadata 的 `models[].file` 全部是 `https://raw.githubusercontent.com/suxing412/creation-notebook/main/...`。这和 W3 刚清掉的问题同类：本地预览会去拉线上 main 的文件，而且指向的是会变的分支头。
  - 好的一面：所有图元都带 UV（`uvPrimitives` 等于网格数），写了 `units: metres` 和轴向。
- **改法**：导出前按材质合并网格，LOD1 至少合并到「每个材质 1–2 个图元」；metadata 里的模型地址改成相对于站点根的路径，或者只记仓库内相对路径，由网页侧拼地址。
- **验收**：灵台、太学 LOD1 的网格数 ≤ 材质数 × 2；`grep -c raw.githubusercontent docs/model-library/*/metadata.json` 为 0。

### C10 〔低〕太学 A、B 两张封面几乎看不出区别
- **现象**：`taixue/cover-A-whole.png` 和 `cover-B-whole.png` 机位、光照、构图都一样，像素平均差 3.2/255。缩到卡片尺寸后完全分不出哪张是 A、哪张是 B。
- **证据**：`evidence/r2026.11.04-1/changed-covers.jpg` 第一行右侧两张。
- **改法**：如果 A/B 的差别在开间、檐口或台基细节上，就加一张近景对照，或者在同一张图里并排放；否则合并成一张封面。
- **验收**：卡片尺寸下不看文字也能说出 A、B 哪里不同。

## 新问题 · 给 Codex（网页）

### W7 〔中〕院落实时 3D 地面出现斜向条纹，疑似阴影痤疮
- **现象**：`courtyard-family.html` 打开 A 方案 LOD0，院子地面上有一组平行的斜向亮暗条纹，房屋背面也有。375 宽下最明显；桌面上也能看到，只是淡一些。001 圣器上没看到。
- **证据**：`evidence/r2026.11.04-1/courtyard-3d-375.jpg`（院地中央）、`courtyard-3d-desktop.jpg`。`inspect.mjs` 第 193–194 行：`normalBias = radius * 0.001`、`bias = -0.0001`。院落包围半径大、地面是大平面，阴影贴图 1024² 覆盖 ±0.65 半径，每个阴影像素对应的面积大，固定的小 bias 压不住自阴影。
- **改法**：按阴影贴图的像素尺寸来设 `normalBias`（例如 `2 * 阴影相机宽度 / mapSize`）；或者让大平面的地面网格只接收阴影（`castShadow = false`）；必要时把 `mapSize` 提到 2048。
- **验收**：院落 A/B/TC03 的 LOD0 在桌面和 375 宽下截图，地面没有条纹；001 的投影仍然清楚。
- **注**：这是从截图判断的，没有逐帧排查，「阴影痤疮」是最可能的原因，不是确证。

### W8 〔低〕五张新网页截图带上了浏览器滚动条
- **现象**：`web-library/assets/002/003/004/012/014-page.jpg` 右侧都有一条浏览器滚动条，其余 8 张没有。卡片尺寸下能看出右边多了一道灰条。
- **证据**：`evidence/r2026.11.04-1/changed-covers.jpg` 第二行和第三行左一。
- **改法**：截图时隐藏滚动条（无头模式下加 `--hide-scrollbars`，或者注入 `html{scrollbar-width:none}`），重出这 5 张和对应缩略图。
- **验收**：13 张网页截图右边缘都没有滚动条。

### W9 〔低〕仓库没有 `.gitattributes`，二进制 .bin 被 Git 当作文本
- **现象**：`git diff --stat` 把 `taixue-long-hall-v1/display/hall-B-geometry-01.bin` 显示成 129469 行文本改动。这个文件开头 8000 字节里没有零字节，所以 Git 的自动判断把它当成了文本。本机 `core.autocrlf=true`。
- **为什么暂时没坏**：文件里有 21780 个单独的 CR，Git 遇到这种情况不做换行转换，所以检出后 SHA-256 和仓库里一致（已核对 `a14264ab…`）。但这是碰巧没坏，下一个 .bin 不一定有单独的 CR。
- **改法**：加 `.gitattributes`，至少写 `*.bin binary`、`*.glb binary`、`*.gltf -text`、`*.part* binary`、`*.png binary`、`*.webp binary`、`*.woff2 binary`。
- **验收**：`git check-attr -a <任一 .bin>` 显示 `binary: set`；`git diff --stat` 里 .bin 显示为 `Bin`。

## 通过项

- `check_overview.py`：passed=true，209 个本地引用，0 个错误，0 个外部引用。
- 158 个 GLB 与基线逐字节一致，退化三角形仍为 0。
- 四个入口页在 1366 宽和 375 宽下都没有横向溢出、没有坏图、控制台没有报错。
- 实时 3D：001（1538 KB）和院落 A-LOD0（499 KB）在桌面和 375 宽下都能加载出画面，控制台没有报错。
- 缩略图的 `srcset` 宽度描述和实际文件一致（抽查 40 张，600 档都是真 600 宽）。缩略图清单记录了来源尺寸和字节数，可以复核。
- Codex 自带的 `qa/r2026.11.04-1/verification.json` 加查看器截图，让这一版的验收有据可查。
- 新内容（灵台、太学）带 UV、写了单位和轴向，并且诚实地标注了「未接入网页和城市」。

## 本次没有验证的

- 没有 GPU 真机、iOS 或 Android 实测；手机只是 375 宽的模拟，霞鹜文楷在真机上的效果没看。
- 字体子集只看了它自己的清单（679/681），没有用 fontTools 逐字核对入口页标题。本机没装 fontTools。
- 灵台、太学的 .gltf 没有跑 `glb_audit.py`（脚本只读 GLB），数字取自它们自带的 metadata，没有独立复算；源码分卷 ZIP 没有解开。
- `docs/cities/luoyang/research/2026-11-04/` 四张研究图只看了观感（`city-C032-whole-CPU.png` 大部分是空的深色底，主体很小），没有对应页面，所以没提问题。
- 传输量是按 `encodedBodySize` 统计的本地数字，没有模拟 4G 测加载时间。
- 只开了 001 和院落两个详情页的实时 3D，其余 18 个详情页没逐个打开。
- C6 和 W7 的成因判断属于我的判断，C6 是设计意见，由制作人拍板。

## 附件

- `evidence/r2026.11.04-1/glb-audit.json`：158 个 GLB 的逐个指标（与基线相同）
- `evidence/r2026.11.04-1/model-library-thumbs.jpg`：模型库 20 张 600 宽缩略图总览
- `evidence/r2026.11.04-1/changed-covers.jpg`：本版新增或改动的封面、网页截图和研究图
- `evidence/r2026.11.04-1/archive-001-3d-desktop.jpg`、`courtyard-3d-desktop.jpg`、`courtyard-3d-375.jpg`：实时 3D 截图
