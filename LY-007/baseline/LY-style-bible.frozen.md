# 洛阳城建模风格规范（LY-style-bible）

适用：「造物之匣 · 洛阳城」东汉雒阳（约公元 180 年）低多边形研究性复原。凡新做模型（包括 Claude 子代理批量铺量）一律照此执行，目标是与伊苏里亚已交付的 49 张卡片、216 个可读 GLB 在网页上看不出是两个人做的。

配套工具库：`ly_style.py`（同目录）。规范里的每个默认值都已写进库里，照库函数做就自动合规。

路径约定（下文简写）：
- `docs/` = `D:/GitHub/creation-notebook-lab/docs/`（她的 GLB，只读）
- `mq/` = `C:/Users/suxin/AppData/Local/Temp/claude/bfd0867865ae17cc/14ddfcf2-ca06-49dc-95f8-4586da1502c1/scratchpad/mq/`
- 测量证据：`mq/style/bible_work/`（总编复核）、`mq/style/{gates,ritual,palace,housing,production,market}/`（六位分析员）、`mq/style/stats.json`（全量材质与导出器统计）

写法约定：每条结论后的「证据」给出文件、节点或网格、量到的数字。量不到的写「未量到」。坐标除特别注明外都用 **glTF 坐标（Y 向上，正面 +Z）**；涉及建模操作时写 Blender 坐标（Z 向上，正面 -Y），两者关系是 glTF (x, y, z) = Blender (x, z, -y)。

---

## 0. 三十秒速查

| 项 | 规定 |
|---|---|
| 单位 / 轴 | 米；glTF Y 向上；正面朝 +Z；地面 y = 0 |
| 着色 | 全部平直着色（角点法线 = 面法线），不倒角、不做布尔 |
| UV | 世界坐标盒式投影，1 UV 单位 = 1 m，不展 UV |
| 材质 | LOD0/1：`LY_P01_<材料>__PBR`（共享贴图 512² / 256²）；LOD2：`LY_P01_<材料>__FLAT` |
| 调色板 | earth #A58B65、timber #56483A、tile #575A54（FLAT 线性值见 §3.1） |
| 网格 | 每种材质合成一个网格、一个节点，节点无变换；命名跟随所在卡片家族（§7：城门/礼制/宫殿 `<slug>-<变体>-static_<材料>`，市肆 `S84-static-LY_P01_<mat>__PBR`，住屋房型 `layout__LY_P01_<mat>__PBR`）；节点/材质按 earth→timber→tile 排列 |
| LOD | 三档 LOD0 / LOD1 / LOD2。圆木 16→8→方盒；瓦垄 8 边→（住屋：逐板段重排一半；其余：抽稀）加 4 边菱形→删除；夯土不变 |
| 面数 | LOD1 约为 LOD0 的 0.2–0.6，LOD2 约为 0.05–0.16 |
| 导出 | Blender glTF 导出器，GLB，不压缩、无扩展；参数见 §8（`ly.EXPORT_SETTINGS`） |
| 自检 | `ly.report_checks` + `ly.check_clearance` + `ly.export_lods`（内含 `inspect_glb`） |

---

## 1. 总则

1. **时代与性质。** 东汉雒阳，约公元 180 年。所有模型都是研究性复原的「候选」，不是测绘。每个节点的 extras 里必须写证据句：以证据等级开头（她的全部卡片都是 C 级），接一句英文，说明这是什么、不是什么。
   - 证据：她的 216 个文件里，extras.evidence 以 `C ` 开头 399 处、`C` 开头 253 处、`C:` 开头 12 处。北郊方坛是唯一例外，写作 `Hou Hanshu: square altar, four approaches; dimensions and exact form C assumptions`。卡片摘要中「C级 / C 级」共出现 39 次（`lab/data/assets.json`）。
   - 范例：kaiyang-K 写 `C Kaiyang central-room-open-gallery trial, not a surveyed elevation`；G10 写 `C functional variation, not archaeological house`。
2. **低多边形，体块优先。** 构件全是闭合的简单体块：方盒（12 三角）、正 n 棱柱、轮廓挤出体、12 顶点屋面板。
   - 不倒角，不做布尔。门洞、墙洞用「画轮廓再挤出」或「墙垛 + 过梁墙」拼成。
   - 不做曲面屋顶，也不做起翘、举折。
   - 细节只靠三样东西：瓦垄细管、少量方木、低对比贴图。
3. **观感。** 观感按两种场景设计：网页实时浏览，以及 Workbench 棚拍光（cavity + 轮廓线，见 `mq/render.py`）。
   - 颜色基本由调色板决定。贴图对比度极低（底色 std 只有 1.2–2.4/255），只给近看一点颗粒感。
   - 剪影和明暗主要靠平直着色的棱面。
   - 证据：`mq/style/bible_work/texcensus.json`，earth-basecolor 512 std (1.98, 1.70, 1.32)，tile (1.21, 1.21, 1.18)。
4. **不臆造细部。** 证据之外不添加装饰：彩画、鸱尾、瓦当纹、斗栱出跳这类都不做。
   - 她的模型里没有完整斗栱，只有柱顶的栌斗方块（§5.12）。
   - 需要表达「不确定」时，写进 extras 和卡片说明，不在几何上做花样。
5. **一个资产一个 slug。** 同一资产的三档 LOD 共用 slug 与变体字母，各档的包围盒、原点、朝向必须一致。
   - 她的 LOD2 只比 LOD0 小约 1 cm（瓦垄伸出部分被删掉了），例：kaiyang 12.622→12.6，`mq/cards/m-luoyang-kaiyang-gate/audit.json`。

---

## 2. 单位、朝向、原点、落地

| 规则 | 规定 | 证据 |
|---|---|---|
| 单位 | 米。extras `metres_per_unit: 1.0` | 18 张卡用 metres、16 张用 meters（`bible_work` 统计，见 §7） |
| 上方向 | glTF +Y（导出 export_yup） | 全部文件 |
| 正面 | **+Z**（Blender -Y） | 石经院 extras `local_south='positive glTF Z / negative Blender Y'`；德阳、侧廊、玉堂的踏步都在 +Z（`palace/palace_constants.json`）；住屋前檐墙外皮在 z=0、屋身向 -Z（`housing/housing_style_constants.json`） |
| 左右 | 面阔沿 X，X 方向居中（cx = 0） | `mq/cards/*/audit.json`：全部单体建筑 cx=0.000（mao 1.033、灶台 -0.312 等因附属件偏心） |
| 进深原点 | 两种，按家族选（下行） | 同上 |
| ├ 单体建筑（门、殿、坛、阙、亭） | 建筑本体（台基 / 柱网）中心在 z=0；踏步、月台另外伸出，不重新居中 | deyang cz=2.04（踏步伸向 +Z）、yutang 0.68、sidehall 0.046；城门、礼制建筑都是 0.000 |
| └ 成排住屋 / 店铺 / 作坊棚 | 前檐墙外皮中点在 (0, 0, 0)，屋身向 -Z | G10 cz=-2.0（墙 z∈[-4,0]）、H64 -2.8、H72 -2.0、H96 -2.4、S84 -2.0、S86 -3.0、workshed -2.0 |
| 落地 | 自然地面 y = 0，建筑最低点 = 0 | 城门、殿堂、住屋 ymin=0.000 |
| 地面补丁 | 单独出 `<slug>-ground-LOD<n>.glb`，板厚 0.2，y -0.16→+0.04 | kaiyang/yong/pingcheng-ground：ymin -0.160、ymax 0.040–0.042 |
| 院落地坪 | 院落套件以 y = 0.2 为院内地面 | compact_work / opposed_rooms / wall-house / workyard：ymin 0.200 |
| 不要学 | 辟雍把 y=0 定在殿台顶，台基向下到 -1.2；xiaoyuan 偏心 cz=-3.6；城市拼块直接放在世界坐标（life-block cx=560） | audit.json |

裁决：新单体建筑一律「台基中心在原点、地面 y=0、正面 +Z」。新的城市住屋套件一律「前檐墙外皮在 z=0」，这样拼街时可以直接沿街排。辟雍的做法不推广，因为它的 y=0 不在地面，拼城时要单独调。

---

## 3. 材质体系

### 3.1 调色板（LY_P01）

| 材料 | FLAT baseColorFactor（线性，照抄 float32） | 对应 sRGB | FLAT 粗糙度 | PBR 贴图前缀 | ORM.G 均值→粗糙度 |
|---|---|---|---|---|---|
| earth 夯土 | (0.3762621283531189, 0.2581828534603119, 0.13013647496700287) | #A58B65 (165,139,101) | 0.88 | earth | 231.48/255 = 0.908 |
| timber 木 | (0.09305896610021591, 0.06480326503515244, 0.0423114113509655) | #56483A (86,72,58) | 0.88 | **wood** | 198.4/255 = 0.778 |
| tile 瓦 | (0.09530746936798096, 0.10224173218011856, 0.08865558356046677) | #575A54 (87,90,84) | 0.88 | tile | 214.22/255 = 0.840 |
| path 路面 | (0.4677838087081909, 0.35640013217926025, 0.21952620148658752) | #B6A181 (182,161,129) | 0.88 | earth（借用） | 0.908 |
| paper__stone 纸样石 | (0.8069522380828857, 0.7379103899002075, 0.5840784311294556) | #E8DFC9 (232,223,201) | 0.90 | stone（只用 normal、orm） | 218.77/255 = 0.858 |

证据：
- FLAT 值取自 kaiyang-K-LOD2.glb `materials[0..2]`、lingtai-A-LOD2 `LY_P01_path__FLAT`、foot-pestle-LOD2 `LY_P01_paper__stone__FLAT`。
- 线性→sRGB 由总编换算，结果都是整数，可见调色板是先定 sRGB 整数色值、再转线性的。
- 贴图均值见 `bible_work/texcensus.json`：earth-basecolor 512 均值 (164.51, 138.49, 100.52)，比调色板低约 0.5/255，肉眼无差。
- FLAT 粗糙度 float32 写出为 0.8799999952316284。

各家族里出现过的特例（不推广）：
- earth__FLAT 粗糙度 0.92：enclosure-L-LOD2、westwall10-LOD2。
- 地面补丁 FLAT 粗糙度 0.90：kaiyang-ground-LOD2。
- 内门 timber 粗糙度 0.82：`housing/housing_style_constants.json`。
- xiaoyuan 的 metal #4B4842 r0.80、stone #938F86 r0.90。
- 石经院 plaster #CDC3AA r0.92。

### 3.2 `__PBR` 材质结构（LOD0、LOD1）

她的 glTF 写法（kaiyang-K-LOD0.glb、G10-LOD1.glb 完全一致）：

```json
{"doubleSided": true, "name": "LY_P01_earth__PBR",
 "normalTexture": {"index": 0},
 "pbrMetallicRoughness": {"baseColorTexture": {"index": 1}, "metallicRoughnessTexture": {"index": 2}}}
```

- **不写** metallicFactor / roughnessFactor（即默认 1）。金属度靠 ORM 贴图的 B=0 压成 0，粗糙度来自 ORM 的 G。
- 不引用 occlusionTexture（ORM 的 R 恒为 255）。normalTexture 不写 scale（= 1）。
- 无 emissive，无 alphaMode，无任何 KHR_materials_* 扩展。
- 采样器只有一个：`{"magFilter": 9729, "minFilter": 9987}`（LINEAR / LINEAR_MIPMAP_LINEAR），wrap 不写（即 REPEAT）。
- Blender 节点写法（`ly.pbr_material`）：
  - 底色图（sRGB）→ Base Color；
  - ORM 图（Non-Color）→ Separate Color，G → Roughness，B → Metallic；
  - 法线图（Non-Color）→ Normal Map（强度 1）→ Normal；
  - 图像插值 Linear，扩展 Repeat；IOR 1.5，Specular IOR Level 0.5（避免导出 KHR_materials_ior / specular）；
  - 关闭背面剔除，导出为 doubleSided。
- paper__stone__PBR 例外：不挂底色图，只写 baseColorFactor，加 stone-orm、stone-normal（foot-pestle-LOD0.glb）。

### 3.3 `__FLAT` 材质（LOD2）

`{"doubleSided": true, "name": "LY_P01_<m>__FLAT", "pbrMetallicRoughness": {"baseColorFactor": [...,1], "metallicFactor": 0, "roughnessFactor": 0.88}}`。不带贴图。

- 证据：kaiyang-K-LOD2.glb。
- 同一个文件里不会同时出现 PBR 和 FLAT（ritual 分析员 38 个文件，`ritual/glbjson.txt`）。

### 3.4 共享贴图库（必须原字节复用）

她所有 LY_P01 卡片嵌入同一套 PNG（8-bit RGB，无 alpha），字节完全相同。本库把它们原样导出到 `textures/`，导出时 Blender 走 happy path，原字节嵌入新 GLB。

总编实测，demo 导出的 9 张图 sha 全部与她的相同（§附录 B）。

| 图名（= glTF image.name） | 512²（LOD0）sha256 前 12 位 / 使用文件数 | 256²（LOD1）sha256 前 12 位 / 使用文件数 |
|---|---|---|
| earth-basecolor | 522d6b1f68a5 / 47 个文件 27 张卡 | 9ea2f6f2c011 / 50 个文件 30 张卡 |
| earth-normal | d0e0d7965902 / 64 | a2c6ca111356 / 54 |
| earth-orm | 6c3992a3c6a4 / 64 | 16ebdabda5fa / 55 |
| wood-basecolor | 3383d4f1f353 / 45 | cf45b370bb41 / 48 |
| wood-normal | a76185638832 / 63 | 0d97751590c1 / 52 |
| wood-orm | 66dea3367e89 / 63 | aa0fa3c978e4 / 52 |
| tile-basecolor | 47ea3f24cb54 / 41 | 977b131f7332 / 44 |
| tile-normal | ac5451bc8808 / 47 | 02d338882700 / 47 |
| tile-orm | c0fe9035bf86 / 47 | 5299af3e2a26 / 47 |
| stone-normal | d5e3b8583952 / 6 | 872a3902f959 / 2 |
| stone-orm | 8712b08b4357 / 6 | 26d990aa1783 / 2 |

- 证据：`bible_work/texcensus.py` → `texcensus.json`（216 个文件逐图 sha256；A1-v3-LOD1 是 meshopt 压缩，跳过）。导出脚本 `extract_textures.py`，清单 `textures/manifest.json`。
- 图案（分析员实测，`gates/textures.json`、`ritual/tex/textures.json`）：
  - earth、tile：低频 fBm 云状噪声，无砖纹、无瓦纹。
  - wood：平行木纹条带，条纹沿 U 方向延伸、沿 V 方向排列（grad_y/grad_x ≈ 6），周期 12.2 px/512，每米约 42 条，约 2.4 cm 一条。
  - normal 起伏极弱，wood 的 G 通道 std 约 10。
- 贴图密度：LOD0 每米 512 px，LOD1 每米 256 px。
- 旧灰调色板（`textures/legacy_grey/`）：earth (195,188,171)，sha 6250b50f5541 / 946d534bff86；tile (137,146,146)；wood (141,123,100)；另有 stone-basecolor。
  - 只出现在 REUSED_C_*（hand-mill、house-roof、southern-altar、stable、tile-kiln）、northern-altar 的 earth_C_reused，以及 gu-G、shangdong-S、zhongdong-Z 的 LOD1。
  - **新模型禁用**。它们的 LOD2 FLAT 是棕色，切换 LOD 时颜色会跳。

### 3.5 UV：世界坐标盒式投影

规则：每个面按面法线的主轴取世界坐标，1 UV 单位 = 1 m，不按正负翻转，不展 UV。主轴按 float32 面法线分量的绝对值**严格比较**（round2 修订，原写「Y 优先于 X」有误）。在 Blender 坐标里写作：

| 面法线主轴（Blender） | (u, v) |
|---|---|
| \|nz\| 最大（地面、屋面、坡面） | (x, y) |
| \|ny\| 最大（前后立面） | (x, z) |
| \|nx\| 最大（侧立面） | (y, z) |

glTF 存储时 v 翻转（v_gltf = 1 − v_blender）。

**45° 并列面（round2 实测）。** 12 边柱有 4 个面、LOD2 菱形柱 4 个面都是 |nx| = |ny| 的 45° 面。她的取向由坐标末位的浮点噪声决定：GLB 里按 float32 位置重算，|nx|−|ny| 为 +3e-7 的面取 (y, z)，为 −4.8e-7 的面取 (x, z)，无一例外。S84-LOD0、G10-LOD0 的 16 个并列面全是 (y, z)；S84-LOD2 菱形柱外侧 4 面取 (x, z)、内侧 4 面取 (y, z)；G10-LOD2 8 面全 (y, z)。全部 LOD0 统计 1471 : 228 偏 (y, z)（round1 review_color/ties.py）。
- 库的做法：坐标全程双精度计算，cos/sin 的 0、±1 取精确值（`geo_prism`），使顶点与她的 float32 逐位相同（S84 菱形柱 x 为 float32(−3.7) = −3.70000005，而不是单精度 Vector 算出的 −3.6999998）；取轴用 `_box_uv`，`UV_TIE = 0` 严格比较，完全相等才取 (y, z)。结果：S84、G10 三档 6 个文件的全部并列面与她一致（`validate/round2/measure/compare.txt`）。
- 自检 `inspect_glb` 不把并列面计入吻合率，单独计数并报告实际用的投影（`uv_ties`，如 S84-LOD2 `timber:xy->yz 8, xy->xz 8`）。GLB 里只有三角形，重算的法线与 Blender 四边形面法线的噪声方向不一定相同，所以并列面只能拿她的原件逐顶点比，不能靠自检。

- 证据：总编在 G10 LOD0/1/2、H64、H72、H96、S84、workshed、kaiyang-K-LOD0、gate-A-LOD1 上逐三角形比对，earth、timber、tile 各主轴吻合率都是 1.0（`bible_work/glbparts.py`，输出 g10.json、h64.json、small.json、kai0.json、gateA.json）。
- 唯一不到 1.0 的是 H64/H72/H96 的逐片瓦（0.95–0.997），那是另一套近景件。
- 后果（照抄即可，不要「修正」）：
  - 竖柱侧面的木纹是水平环纹，横梁上才顺纹。
  - 斜坡面的 UV 有投影拉伸，每单位约 1.04–1.19 m（gates 分析员）。
- 例外：REUSED_C_earth 与 earth_C_reused 是 2 m/单位；xiaoyuan 是 2 m/单位；TC03-roof-medium 的 REUSED_C_tile 是 0.8 m/单位。新模型不采用。

### 3.6 例外材质一览（只读，不推广）

| 名称 | 出现处 | 特点 |
|---|---|---|
| `LY_P01_earth` / `timber` / `tile`（无后缀） | guangyang gate-A、stoneclassic、earthwall | gate-A 的 LOD1 带贴图、LOD2 是 FLAT 值，名字却一样 |
| `LY_P01_earth__VC` / 无后缀 earth | earthwall、enclosure-L | 颜色只来自 COLOR_0（FLOAT VEC3），材质不写底色，粗糙度 0.92；Workbench 下显示为灰色 |
| `__TEX256` / `__TEX128` | xiaoyuan | 只有底色图，颜色偏暗 earth (96,66,33)，UV 2 m |
| `REUSED_C_*`、`earth_C_reused_LOD*` | 7 张旧卡 | 旧灰调色板；北坛 normal scale 0.35 |
| `LY_P01_fiber__PBR` | 太学 | 席纹 mat-* 贴图 |
| `LY_P01_brick` | 宫墙水道 | 取 tile 色，extras 说明是派生角色 |
| `LY_P01_plaster` | 石经院 | 自写 build.py 导出，doubleSided=false |
| `.001` / `.007` 后缀 | a1-neighborhood、palace-admission-court | Blender 副本后缀漏进导出 |

### 3.7 裁决

- 新模型只用 §3.1 五种材料，名称必须带 `__PBR` 或 `__FLAT`，禁止 `.001` 之类后缀。
  - `ly.inspect_glb` 按正则 `LY_P01_[a-z_]+__(PBR|FLAT)` 检查。
- 需要新材料（例如真正的石材）时，先找制作人定调色板与贴图，不要自己起名。brick、plaster 这类派生角色也要先问。
- 顶点色夯土（城垣做法）只在续做城垣家族时用，因为 Workbench 下会显示成灰色。

---

## 4. 几何总规则

1. **平直着色。** 角点法线 = 面法线，比例 100%，16 棱柱也是棱面。
   - 证据：gates 45 个文件、ritual 38 个文件全部如此；总编复核 G10/H64/H72/H96/kaiyang 的 `flat` 字段均为 1.0。
   - Blender 里把所有面设为 Shade Flat，导出器会按面拆分顶点，顶点数约为三角数的 1.8–2.2 倍。
2. **只有三角形。** 面数预算按三角数计：方盒 12，n 边柱 4n−4，屋面板 20。
   - n 边形封口不加中心点，导出时扇形三角化为 n−2 个三角（kaiyang 16 边柱 32 个焊接顶点、60 三角）。
3. **顶点属性只有三项：** POSITION、NORMAL、TEXCOORD_0（只有一套 UV，名叫 UVMap）。没有 TANGENT，没有 COLOR_0（城垣除外）。
4. **索引：** 单个图元顶点数小于 65535 时用 uint16（5123）。目前最大的是 zhongdong tile，25648 顶点（gates 分析员）。
5. **节点无变换：** 几何烘焙在世界坐标，节点不带 translation/rotation/scale。只有可开合门扇是例外（§5.6）。
6. **闭合体块，不倒角，不做布尔。** 墙洞用「墙垛 + 窗下墙 + 过梁墙」相接的盒，门框用 10 点 Π 形轮廓挤出，城台立面用整块轮廓挤出。
   - 证据：H72 earth 152 三角里墙段相接，边使用次数为 2（184 条）和 4（22 条），`bible_work` 复核；kaiyang 门框 20U/36T；jin 城台 32U/60T。
7. **棱柱首顶点在轴线方向上。**
   - 竖柱、沿坡的瓦垄：首顶点朝 X（H72 柱顶点 (-3.3, *, 0.18)，柱心 -3.2；G10 瓦垄截面顶点在 x = 中心 ±0.055）。
   - 沿 X 的正脊：首顶点朝竖直方向（kaiyang 正脊顶点 y = 10.05 / 10.23，中心 10.14）。
   - 库函数 `_perp_basis` 依次试 X、Z、Y。
8. **埋入原则（她的一贯做法）。** 构件之间宁可埋入，不留缝。
   - 瓦垄管心比板顶高 0.02，管底埋进板里；正脊管心比板脊顶高 0.04。
   - 檐枋、檩条的顶抵到板底，低的一侧埋进板内。
   - 埋入深度必须小于板厚，否则会从板顶穿出。`ly.beam_under_roof` 超过板厚 90% 时报错。
   - 实例：H72 檐枋深 0.30 埋入 0.135，靠上面另一层瓦面才盖住；单层 0.13 板的屋面就得改用 0.24 深的枋。
9. **檐墙顶留缝（照她，不改）。** 住屋、店铺的檐墙（前后墙）顶 **平** 在檐口线标高，与屋面板底之间留一条 0.20–0.33 m 的暗缝；街面视角（眼高 1.6 m）看得到墙顶与檐口之间一道深色带，这是她的观感，不要封死。
   - 证据：S84 后墙顶平 y=3.000（顶点 (±3.72, 3.000, −4.000)、(±3.72, 3.000, −3.720)），板底在墙外皮 3.202、内皮 3.328；G10 前后墙顶平 3.200（x ±4.72），板底 3.402 / 3.528；H72 后檐墙顶 2.8、板底 3.002。round1 按旧 §4.9 做斜顶贴板底，评审在街面视图（`validate/round1/review_geo/cmp_o84_street.png`）里看出缺了这道暗带，round2 改回。
   - 库：`a.eave_wall(roof, axis, u0, u1, face, t, z0, openings=...)`，墙顶 = `roof.z_eave`。`a.wall(..., z1=(外, 内))` 的斜顶只留给作者明确要封死的场合（不是她的住屋做法）。
   - 对照视图必须包括 `street`、`backlow`（`validate/round2/render_street.py`）：iso、close、front、wire 看不到檐下。
10. **不留缝（比她更严一点）。** 两处改进，外观不变：
   - H72 檩条端头与屋面板端面齐平，同向共面会闪烁。新模型端头缩进 0.04（`ly.purlins` 自动处理）。
   - shangdong 在 LOD2 删了望柱，扶手悬空；辟雍在 LOD2 删了栌斗，柱顶与圈梁之间露 0.24 缝。新模型望柱按圆木规则降档，栌斗各档保留。

---

## 5. 构件做法与典型尺寸

下表的 Blender 函数都在 `ly_style.py`，默认参数即本表推荐值。

### 5.1 柱、柱础、栌斗

| 项 | 做法 | 尺寸 | 面数 | 证据 |
|---|---|---|---|---|
| 殿堂 / 城门柱 | 正 16 棱柱，不收分、不卷杀、不倒角 | Ø0.24–0.48：deyang 0.46、biyong 0.48、mingtang 0.44、yutang 0.36、sidehall/taixue 0.32、guard 0.28、kaiyang 0.34（r0.17）、que 0.38 | 60 | palace_constants.json、ritual analysis.json、gates loddiff.txt |
| 复道 / 廊 / 登临柱 | 12 棱柱 | gallery Ø0.32/0.28、yutang 廊 0.24、access 0.36 | 44 | palace_constants.json |
| 住屋檐柱 | 12 棱柱，无础，柱心在前檐墙外 0.18，立在地面；G10、S84 柱顶斜切到屋面板底（`frontpost_sloped_cap`，`a.post(..., cap_roof=roof)`） | Ø0.20，高 2.7（H72）、2.8（H64）、3.1（H96）、3.276–3.366（G10 斜切柱顶）；S84 柱心在地坪内 0.16（敞口铺面无前墙），**柱从 y=0 起穿过 0.22 地坪**（不是从地坪顶起；S84 timber 最低点 0.000），柱顶 3.229–3.319 | 44 | `bible_work/h72.json`：dims [0.2, 2.7, 0.2]，min z 0.08；G10/S84 见 `validate/round1/measure/orig_parts.txt` |
| 柱础 | 方盒，**earth 材质**（并进夯土网格），柱身从础顶起 | 边长约为柱径的 1.5–2.0 倍，高 0.2（deyang 0.76×0.28、biyong 0.72×0.2、sidehall 0.65×0.2、gallery 0.5×0.2） | 12 | palace_constants.json；biyong 柱 zmin 0.2 = 础高 |
| jin/mao 门道柱础 | 多环圆盘（32 边 × 4 环） | Ø0.48×0.16 | 256/128/64 | gates measure.json（新模型不推荐） |
| 栌斗 | 柱顶方盒，timber | biyong 0.78×0.78×0.24；jin 柱头块 0.48×0.48×0.22 | 12 | ritual partGroups、gates |

库函数：`a.column(x, y, z0, z1, d=0.32, sides=16, base=True)`（础 1.6d × 0.2，earth）、`a.post(...)`（12 边 Ø0.20、无础）、`a.ludou(...)`。

### 5.2 梁、枋、檩、楼面板

| 项 | 做法 | 尺寸 | 证据 |
|---|---|---|---|
| 梁枋（方木） | 轴对齐方盒，各 LOD 不减、不倒角 | kaiyang 进深梁 0.22×0.22×7.8、纵枋 0.24×0.25×23.4；类型门阑额 0.32×0.96、檩 0.24×0.32；石经院檩 0.15×0.16、梁 0.28×0.27 | gates measure.json、ritual |
| 住屋檐枋 | 方盒，搁在檐柱顶，顶抵屋面板底 | H72：6.76×0.289×0.30，y 2.7→2.989，z 0.03→0.33（柱外 0.18） | `bible_work/h72.json` |
| 住屋檩条 | 每坡 2 根细方木，沿 X 通长，穿过山墙出头 | H72：0.054×0.08（墙内皮线）、0.072×0.08（再进 0.45） | h72.json：x2 [8.1, 0.054, 0.08]、x2 [8.1, 0.072, 0.08] |
| 圆檩 / 圆梁 | 与柱同法，横放 8/12 边棱柱 | 灵台檩 Ø0.32；太学横梁 Ø0.36–0.38 | ritual partGroups |
| 圈梁（殿堂） | 一整圈方框体 | 明堂 24.44×24.44×0.44 | ritual |
| 城楼楼面板 | 整块大板盒 | kaiyang 0.34×10×24.8，y 5.0→5.34 | gates |
| 叉手 / 人字斜梁 | 沿「檐-脊-檐」折线扫掠的圆木，每段一根带封口棱柱，折点不斜切，只在折轴上共点 | kaiyang r0.11，跨 7.67、高 1.39 | gates axisvals：120/56/24 三角 |

库函数：`a.beam(p0, p1, w, h)`、`a.beam_under_roof(roof, p0, p1, w)`（顶自动抵板底）、`a.round_beam(...)`、`a.sweep(points, d)`、`a.purlins(roof, ys, x0, x1)`。

### 5.3 墙与门窗洞

| 项 | 做法 | 尺寸 | 证据 |
|---|---|---|---|
| 住屋夯土墙 | earth 盒拼接：地坪板上立四面墙，前檐墙按门窗切成墙垛、窗下墙、过梁墙 | 厚 0.28；地坪 0.22；檐墙顶 2.8；山尖到板底（H72 3.9） | `bible_work` 转储 H72 earth 68 顶点 |
| 山墙 | 住屋/店铺：**墙身盒（地坪顶 → 檐口线）+ 山尖五边形（檐口线 → 板底 → 脊）两块**，在檐口线有一圈顶点和一对重合的内部面；每面墙 12 + 16 = 28 三角 | 山尖斜边 = 屋面板底；S84 檐口线 3.000、山尖起点 3.202、脊 4.1；G10 3.2 / 3.402 / 4.3 | S84 earth 80 三角 = 地坪 12 + 后墙 12 + 山墙 2×28；G10 140 = 12 + 2×28 + 前后墙 2×36（round1 review_lod/earth.py；round2 逐三角吻合）。库 `a.gable_wall(..., z_shoulder=roof.z_eave)` |
| 带门洞的檐墙 | 洞口两侧墙垛只到洞顶，洞顶以上一条 **通长墙带**（沿墙全长，洞顶 → 墙顶） | G10：墙垛 0.22 → 2.30，墙带 x ±4.72、2.30 → 3.20 | round1/measure/g10_earth_verts.txt；库 `eave_wall(..., band=True)`（缺省）。H72 等多洞口墙未核 |
| 殿墙 | earth 竖直厚板，不收分 | mingtang 0.24×3.1；deyang 0.3×5.0；sidehall 0.18–0.22×3.0；yutang 0.24 | ritual、palace_constants.json |
| 城门上层墙 | 带门洞缺口的 10 点轮廓挤出，一块成形 | 厚 0.24（试做门）；门洞 2.2×2.0 | gates axisvals：20U/36T |
| 院墙 | 夯土墙 + 压顶 | 0.35 厚 × 2.2 高，压顶 0.12 | housing_style_constants.json（压顶细部未细量） |
| 坛墙（圆） | 沿 128 段/周圆弧挤出矩形截面 | 南坛 0.45×1.4 | ritual |
| 门洞（住屋） | 外沿 1.56–1.76 × 2.16（门槛即地坪顶 0.22，洞顶 2.38） | H64 1.56、H72/H96 1.76 | h64.json、h72.json |
| 门洞（殿堂） | mingtang 2.2×2.35；kaiyang 中门道 5.6、侧门 4.0 | | ritual、gates |
| 窗洞（住屋） | 0.8×0.8，窗台 1.2（H96 有 1.0×0.8） | | h72.json、housing_style_constants.json |

库函数：
- `a.floor_slab(...)`；
- `a.eave_wall(roof, axis, u0, u1, face, t, z0, openings=[...], band=True)`：住屋/店铺檐墙，平顶在檐口线（§4.9）；
- `a.wall(axis, u0, u1, face, t, z0, z1, openings=[(ua, ub, za, zb), ...], band=False)`，z1 可写成 (外皮高, 内皮高)，做成贴合屋面的斜墙顶（不是她的住屋做法）；
- `a.gable_wall(...)`、`a.court_wall(...)`。

### 5.4 台基、夯土台、收分

| 项 | 做法 | 尺寸 | 证据 |
|---|---|---|---|
| 殿台 / 台基 | 直角盒，12 三角，台面无细节 | deyang 35×1.8×25；sidehall 38×0.45×10；yutang 35/31×0.6×19；biyong 36×36×1.2；mingtang 28×28×1.2；taixue 37.6×7.6×0.6 | palace_constants.json、ritual |
| 城门墩台 | 直角盒，不收分，没有券顶，门道顶由梁和楼面板封住 | 宽 2.0–3.0、高 5.0–5.6、深 6.8–10 | gates measure.json |
| 阙台 | 8 顶点四棱台，收分 1:6 | 底 9.0×9.0、顶 6.6×6.6、高 7.2 | gates hexa.py |
| 城台前脸 | 整块轮廓挤出，前脸内收约 1:11 | jin 4.9 高内收 0.4455 | gates axisvals |
| 城垣 | 收分梯形截面，按 0.25 m 夯层分带，颜色用顶点色 | A/B 底 14.05、顶 10.05、高 8（1:4）；C 底 8、顶 5.6、高 6.03（约 1:5） | ritual parts/earthwall-* |

库函数：`a.platform(x0, y0, x1, y1, z0, z1, taper=0)`，taper>0 时为收分台，taper 为单侧内收与高度之比（阙台 1/6）。

### 5.5 踏步

做法：实心叠级。每级一块盒，第 i 层从该级前沿一直伸到台基立面，层层相叠，没有垂带和栏杆，与台基同为 earth。

| 来源 | 踢面 / 踏面 | 级数 | 证据 |
|---|---|---|---|
| deyang（宫） | 0.15 / 0.30–0.34 | 12 | palace_constants.json |
| sidehall / yutang | 0.15 / 0.30–0.34 | 3 / 4 | 同上 |
| mingtang | 0.15 / 0.33 | 8 | ritual |
| biyong、lingtai、taixue、北坛 | 0.20 / 0.34–0.50 | 6 / 30 / 3 / 6 | ritual |
| 南坛 | 0.16 / 0.45；上台 0.10 / 0.2875 | 10 / 8 | ritual |
| 木登临梯 | 0.20 / 0.32，宽 2.0，板厚 0.12；LOD2 合成 10 级 0.4 / 0.64 | 20 | palace_constants.json |

裁决：默认踢面上限 0.15、踏面 0.32，取宫殿家族和明堂。礼制坛台可传 `riser_max=0.20`。`a.steps(u0, u1, face, z0, z1)` 按总高自动分级：n = ceil(H / riser_max)，踢面 = H/n。

### 5.6 门框、门叶

| 项 | 做法 | 尺寸 | 证据 |
|---|---|---|---|
| 门框 | 两框柱 + 门额连成 10 点 Π 形轮廓，沿墙厚挤出，一整块 | H72：外沿 1.76×2.16，框料 0.08，额 0.08，深 0.28（= 墙厚），净 1.60×2.08。kaiyang：框 0.2、额 0.3、深 0.32；类型门深 0.36 | `bible_work` 转储 H72 x ±0.88/±0.80、y 0.22/2.30/2.38 |
| 门叶（静态） | 方盒板，并入 static_timber | 城门板厚 0.14、宽 1.36–2.56、高 4.26–4.6，地面留 0.05 缝；内门 0.055 厚 | gates measure.json；single-door-LOD0 [0.055, 2.035, 1.44] |
| 门叶横带 | 0.05×0.12 盒，每扇 3 道，约在 0.16/0.51/0.86 高处；LOD2 删除 | kaiyang y 0.7/2.2/3.7 | gates loddiff：LOD1→2 REMOVED x12 |
| 门叶（可开合，jin） | 每扇单独节点 `<slug>-<V>-leaf_<道>_<L/R>`，原点在铰点（节点 translation = 铰点），绕 Y 旋转；extras 写 hinge_axis_native [0,0,1]、pivot_native、angle_range_deg [0,90]、swing_sign；门钉只在 LOD0 | 门轴 r0.09，铰点 z=+1.35 | gates glbjson：jin-C-leaf_0_L translation [-9.85, 0, 1.35] |
| 住屋 | H64/H72/H96/G10 **没有门叶**，门洞直接空着；内门另成卡片 | | h72.json timber 部件清单 |

裁决：城门、宫门默认静态门叶并网（试做门做法）。需要开合动画时才用 jin 的单独节点，库里是 `separate_node='leaf_0_L'`（已测通，§附录 B）。住屋可以不放门叶；放的话用 0.06 厚、开 90°，免得挡住通道。

### 5.7 窗

| 项 | 做法 | 尺寸 | 证据 |
|---|---|---|---|
| 住屋直棂窗 | 窗框 = 两框 + 上下槛 4 根方木并成一件（48 三角），深 = 墙厚；棂条为方棂，居中立在下槛上 | H72：0.8×0.8，料 0.05，深 0.28；棂 3 根 0.035×0.7×0.035 | `bible_work` 转储 H72 窗框 24 顶点 / 48 三角 |
| 太学直棂窗 | 六棱细杆（20 三角） | Ø0.07，高 1.05，40 根 | ritual |
| 降档 | H72：棂 3→1（留中间一根）→0；框各档保留 | | h72.json LOD1 x1 bar、LOD2 无 |

库函数：`a.window(axis, ua, ub, face, depth, za, zb, member=0.05, bars=3, bar=0.035)`。

### 5.8 屋面板

| 项 | 做法 | 证据 |
|---|---|---|
| 悬山板 | 倒 V 形 6 点截面（前檐、脊、后檐各上下两点，上下之差是竖直厚度 t）沿 X 挤出，两端平切，每段 12 顶点 / 20 三角，tile 材质，三档 LOD 同一块。**住屋/店铺分 3 段，断在檐柱外皮**（柱心 ± r），3 × 20 = 60 三角；两端面各是两块四边形（前坡、后坡），不是一个六边形 | kaiyang slab 12U/20T（1 段）；S84 断在 x = ±3.70（柱心 ±3.6 + 0.1）、G10 ±4.70，60 三角 / 108 导出顶点，S84-LOD2、G10-LOD2 也是 60（round2 逐三角吻合）。库 `roof_gable(..., splits=(−px−r, px+r), slab_name='roof_left')` |
| 庑殿（四阿）板 | 同样 12 顶点（檐口矩形 4 点 + 脊端 2 点，上下两层），正脊两端缩短，20 三角 | pingcheng X[-14,-8.8,8.8,14]；deyang 32×22、脊长 10（等坡） |
| 厚度（竖直） | 住屋 0.13；类型门 0.08；gallery 0.12；试做门、yutang、sidehall 0.16；deyang、jin、que 0.18；xiaoyuan 0.20；taixue、lingtai 0.10 | G10 3.2→3.33；roofslab.py；palace_constants.json |
| 坡度 | 住屋 24.2°（1.1/2.45）；城门 15.9–24.4°；殿堂 12.8–26°（deyang 17.25°、gallery 17.7°） | H72 earth 山尖；gates roofslab；palace ribs.txt |
| 出檐（板边到墙外皮 / 柱中线） | 住屋 0.45；试做门山面约 1.2、檐面约 1.3（shangxi 1.45）；类型门 1.0；辟雍、石经院 2.0；明堂 1.4；太学 0.65 | housing constants、gates、ritual |
| 曲面 | 无起翘，无举折，无曲线，全是直坡 | 全部 |

库函数：`roof = a.roof_gable(x0, x1, y_front, y_back, z_eave, rise, t, ribs=..., ridge=...)`、`a.roof_hip(...)`。

**住屋 / 店铺瓦垄端点（round1 实测修订）。** G10、S84 的瓦垄不在脊线相会：管心起点在檐口内收 0.06、高 = 檐口板顶 + 0.05；终点在脊线前 0.07、高 = 脊线板顶 + 0.05。管身因此比板面略陡（S84 1.1/2.32 对板 1.1/2.45），下端埋入板 0.03，上端离板约 0.02，两坡管头在脊上并成一道鼓起的「假脊」。库写法 `ribs=dict(d=0.11, pitch=0.28, inset=0.06, lift=0.05, lift_ridge=0.05, lift_ref='edge', ridge_gap=0.07)`，复刻件瓦垄包围盒与她逐值相同（0.11×1.199×2.367，y 3.1303–4.3297，z -4.4136–-2.0464）。证据：S84-LOD0 tile 第 1 根管 16 顶点，管心 (z 0.39, y 3.18) → (z -1.93, y 4.28)；`validate/round1/measure/`。返回的 Roof 对象可以查 `top_z(x, y)` 和 `bottom_z(x, y)`，墙顶、梁顶、檩条都据此贴合。

**住屋 / 店铺瓦垄的横向排布（round2 实测修订）。** 按板段逐段排、段内均分居中：每段宽 w 排 n = floor(w / 0.28) 根，第 i 根心 = 段起点 + (i + 0.5)·w / n。
- S84：出际段 0.75 m 各 2 根（心距 0.375，最外一根心 ±4.2625，离板端 0.1875），中段 7.4 m 26 根（心距 0.2846），每坡 30；G10 中段 9.4 m 33 根（0.2848），每坡 37。
- pitch 取 0.28 是推断：(0.2765, 0.2846] 内任何值都能复现这 6 段根数，精确值未量到。
- 板段的断缝（x = ±3.70）在线框图上可见；瓦垄心距在山面出际处由 0.375 跳到 0.285，近看可见。
- 库：`LOD_PROFILES['house']['rib_layout'] = 'segments'`，`Assembly.rib_xs_segments(roof.segments, 0.28)`；殿堂、城门仍按全长等距（`'even'`，未按段复核）。

### 5.9 瓦垄（三种做法，先选一种）

| 做法 | 几何 | 尺寸 | 面数 | 用在 | 证据 |
|---|---|---|---|---|---|
| A 细管瓦垄（推荐） | 每坡一根带封口的 8 边细管，从檐口直到脊线；管心在板顶上方 0.02，管底埋入板内；前后坡在脊线上共点（她的「连续瓦垄」就是两根这样的管在折轴上共 2 点，30U/56T） | 住屋 Ø0.11，逐板段排 @≈0.28（G10/S84，檐口内收 0.06；workshed 未按段复核）；殿堂 Ø0.07–0.09 @0.40–0.46（deyang 0.09@0.451、gallery 0.07@0.427、biyong 0.07@0.40、mingtang 0.09@0.44）；试做门 Ø0.066–0.07 @0.21–0.24 | 每坡 28 | 住屋、殿堂、试做门、礼制 | g10.json：x74 [0.11, 1.199, 2.367] t28 wv16；kai0.json：x111 t56 wv30；palace ribs.txt |
| B 檐口逐片瓦 | 只沿前后檐铺一排：板瓦为 7 点抛物线弧（下凹 0.025、厚 0.008、宽 0.36、沿坡 0.42），筒瓦宽 0.13、拱高 0.06，压在板瓦缝上；其余坡面只有屋面板 | 列距 0.36 | 每片 52 | 类型门（gu、广阳、夏门、上东、中东） | gateA.json：x122 [0.359, 0.191, 0.42] t52 wv28、x120 [0.13, 0.221, 0.42] |
| C 整坡逐片瓦 | 板瓦、筒瓦逐片满铺，另有檐口条带 | 筒瓦距 0.292 | 2–3 万三角 / 栋 | H64/H72/H96 近景套件、石经院 near | h64.json：tile 19992 三角 |

庑殿两端：
- 前后坡靠角的垄在戗脊线前截短（截短量约 1.5 倍管径）；端坡的垄沿 X 走，同样截在戗脊线上（biyong、deyang 的做法）。
- pingcheng、shangxi 是另一种：先上到戗脊高度再水平折过去（44U/84T），不推广。

裁决：
- 新模型一律用 A。
- 不用 B：类型门 95% 的三角都压在这一排瓦上（gu-G LOD1 tile 13728 三角），而它的「LOD1」比试做门的 LOD0 还重，铺量会吃光面数预算。
- C 只在指定的近景主角件上用。
- 库里 B 也已实现（`a.eave_tiles(roof)`），续做类型门时用；A 由 `ribs=dict(...)` 生成。

### 5.10 檐口

- 檐口就是屋面板边：竖直立边，即「板厚」那一圈。不另做连檐、瓦当。
- 住屋檐下是檩条（§5.2），城门、殿堂檐下是梁枋。
- 类型门另有倾斜檐板 0.172×0.479（长 19.4–22.9）。gates 分析员量到了尺寸，但没有量到具体位置和倾角，库未实现，标「未量到」。

### 5.11 脊

| 项 | 做法 | 尺寸 | 面数 / LOD | 证据 |
|---|---|---|---|---|
| 正脊（城门、殿堂） | 圆管沿 X，管心比板脊顶高 0.04，部分埋入；悬山全长同板，庑殿只在正脊段 | 试做门 r0.09–0.10，jin 0.11，mao 0.13，deyang Ø0.20（12 边），sidehall 0.18（16 边），gallery 0.15（10 边），guard 0.13 | 16 边 60 → 8 边 28 → 2r 方盒 12 | kai0.json：正脊 16 边 r0.09、y 10.14 对比板顶 10.10；palace ridge_rolls |
| 正脊（类型门） | 0.12×0.2 方盒，各 LOD 相同 | | 12 | gates |
| 戗脊 / 垂脊 | 16 边 r0.08 斜管 → 8 边 → LOD2 删除 | 长 7.1–8.5 | 60/28/0 | gates loddiff（pingcheng 戗脊） |
| 住屋 | **不设正脊**：两坡瓦垄各停在脊线前 0.07，管头高出脊板 0.05，形成假脊（见 §5.8 末） | | | G10/S84/workshed 的 tile 只有板和瓦垄（g10.json）；端点见 `validate/round1/measure/` |

库函数：`ridge=dict(d=0.18, sides=16, lift=0.04)`、`hip_ridges=dict(d=0.16, sides=16, lift=0.04)`。

### 5.12 斗栱

她的 216 个文件里只有柱顶栌斗方块（biyong 0.78×0.78×0.24，24 个）和 jin/mao 的柱头块（0.48×0.48×0.22），没有栱、昂、出跳。新模型不要自己加斗栱。确有证据需要时，先报制作人。

- 证据：ritual partGroups；gates measure.json；palace 家族各 objects_summary 中无此类部件。
- 未量到：她是否有意回避斗栱，判断依据不在 GLB 里。

### 5.13 栏杆

| 项 | 做法 | 尺寸 | LOD | 证据 |
|---|---|---|---|---|
| 望柱 | 细棱柱 | shangdong 12 边 r0.05×1.0；mao 16/8 边 r0.075×1.0–1.2；kaiyang 矮柱 0.16 方盒×1.12 | 她：LOD2 删除；本库：降为方盒 | gates loddiff |
| 扶手 | 方盒或细管 | kaiyang 0.18×0.18 | 各档保留 | gates |
| 竖棂（石经院） | 0.07 方棂 | 0.07×0.07×1.11；横杆 0.12×0.13；栏柱 0.22×0.22×1.5 | near 234 → middle 113 → far 0 | ritual |

### 5.14 院墙

做法：夯土墙 0.35 厚 × 2.2 高，加 0.12 压顶（court-layout-kit 实测，`housing/housing_style_constants.json`）。compact_work 的压顶由 66 片 16 三角的小瓦件组成（`housing/rep2_small.txt`：x66 [0.11, 0.29, 0.45] t16），细部未逐片量，本库先用一块 tile 方板代替（`a.court_wall`）。住屋低墙：0.24 厚 × 1.15 高。

### 5.15 地坪、地面补丁、路面

- 住屋室内地坪：earth 实心板，厚 0.22，墙立在板顶（H72、G10）。
- 地面补丁：单独 GLB，earth，例如 3 条 14×1.8×0.2 的板。
  - LOD0 顶面细分（每条 672 三角），LOD1 192，LOD2 退成盒（kaiyang-ground 2016/576/36）。
  - 节点名 `<slug>_ground_C`，extras 写 'temporary local support; not excavated pavement'。
  - 库里 `a.ground_patch` 只做一块盒，没做顶面细分。
- 路面：LY_P01_path（灵台 static_path），PBR 借用 earth 贴图，FLAT 更浅（#B6A181），LOD2 切换时会变亮。

### 5.16 器物（简述）

器物家族（灶、碓、磨、内门）做法更自由：
- foot-pestle 用到 24 边棱柱；石臼 480 面。
- 内门组件 LOD0 就用 FLAT，网格名是 Cube.004。

这些是例外，不作为建筑铺量依据（`production/summ_small.txt`、`bible_work/h72.json` 中 single-door 部分）。

---

## 6. LOD 规则

### 6.1 三档定义与命名

| 档 | 用途 | 材质 | 贴图 | 文件名 |
|---|---|---|---|---|
| LOD0 | 近景 | `__PBR` | 512² | `<slug>-<V>-LOD0.glb` |
| LOD1 | 中景 | `__PBR` | 256²（同图案，均值相同） | `<slug>-<V>-LOD1.glb` |
| LOD2 | 远景 | `__FLAT` | 无 | `<slug>-<V>-LOD2.glb` |

节点 extras 的 LOD 字段与文件名一致（default 写法）。市肆、住屋房型卡片的文件名是 `<原型>-LOD<n>.glb`（S84-LOD0.glb、G10-LOD0.glb），extras 不写 LOD（§7）；库按 `Assembly(naming=)` 选。

不推广的命名：
- 类型门只有 LOD1/LOD2，且 LOD1 实际是最高档；
- 南坛用主文件加 -LOD1，没有 LOD2；
- 石经院用 near/middle/far；
- 宫墙水道用 near/mid/far；
- mao 有 display-LOD1。

### 6.2 逐类降档规则（`component_geometry` 的 lod 规则）

| 构件 | LOD0 → LOD1 | LOD1 → LOD2 | 证据 |
|---|---|---|---|
| 夯土（台、墙、墩、础、踏步） | 不变 | 不变 | biyong earth 588/588/588；mingtang-A 956×3；H64 116×3；G10 140×3 |
| 圆木（柱、圆檩、望柱） | 16/12 边 → 8 边，r 不变 | → 边长 2r 的轴对齐方盒（外接）；**住屋檐柱例外**：4 边菱形（顶点在轴向上，`lod2_shape='diamond'`） | kaiyang prism16 → prism8 → box[0.34,0.34,3.33]；G10-LOD2、S84-LOD2 檐柱是 8 顶点 12 三角的菱形，顶点 (x±0.1, z) 与 (x, z±0.1)（round1 实测，原写 box 有误）；H72-LOD2 未量到 |
| 扫掠件（叉手） | 16 → 8 边 | → 4 边菱形 | kaiyang 120/56/24 |
| 瓦垄 | 住屋/店铺：**逐板段重排 n0 // 2 根**（不是 LOD0 的子集），截面 8 → 4 边；其余家族：每 k 根留 1 | 删除 | S84-LOD1 出际段 2→1（心 ±4.075）、中段 26→13（心距 0.5692），每坡 15；G10 2→1、33→16，每坡 18（心距 0.5875）；见 6.4 |
| 正脊 | 16 → 8 边 | → 2r 方盒 | kaiyang；deyang LOD2 10×0.2×0.2 |
| 戗脊 | 16 → 8 边 | 删除 | pingcheng |
| 梁、枋、门框、窗框、板 | 不变 | 不变 | H72 门框 36、窗框 48 各档相同 |
| 窗棂、檩条（thin） | 留中间一根，或隔根留 | 删除 | H72：棂 3→1→0、檩 4→2→0 |
| 门叶横带、小矮柱（lod01） | 不变 | 删除 | kaiyang LOD1→2 REMOVED x12 横带 |
| 门钉、纴木头、柱头小块（lod0） | 删除 | — | jin 门钉、que 60 块纴木头、mao 36 块柱头 |
| 檐口逐片瓦 | 不变 | 删除 | 类型门 LOD2 |
| 屋面板 | 不变 | 不变 | 全部 |
| 材质 | PBR 512 → PBR 256 | → FLAT | 全部 |

### 6.3 面数比例（实测）

| 资产 | LOD0 / LOD1 / LOD2 三角 | LOD1/0 | LOD2/0 |
|---|---|---|---|
| kaiyang-K | 8204 / 1964 / 740 | 0.24 | 0.09 |
| pingcheng-P | 10100 / 1708 / 548 | 0.17 | 0.05 |
| palaceque-Q | 7888 / 1600 / 656 | 0.20 | 0.08 |
| jin-C | 13244 / 4964 / 2692 | 0.37 | 0.20 |
| biyong-A | 9724 / 2844 / 1052 | 0.29 | 0.11 |
| mingtang-A | 12464 / 7424 / 1264 | 0.60 | 0.10 |
| deyang-A | 8660 / 5356 / 924 | 0.62 | 0.11 |
| sidehall-A | 8456 / 2760 / 1280 | 0.33 | 0.15 |
| G10 | 2360 / 688 / 224 | 0.29 | 0.09 |
| S84 | 1956 / 604 / 176 | 0.31 | 0.09 |
| H72 | 22068 / 11388 / 320 | 0.52 | 0.015 |
| demohut-A（本库） | 1740 / 636 / 280 | 0.37 | 0.16 |
| demoting-A（本库） | 2396 / 1300 / 356 | 0.54 | 0.15 |

证据：`lab/data/assets.json` 的 files[].triangles；demo 见 `demo/demo_report.json`。

验收区间：LOD1/LOD0 在 0.17–0.62 之间，LOD2/LOD0 在 0.05–0.20 之间。超出时先查是不是夯土太重：夯土不降档，太重会拉高 LOD2。

### 6.4 各家族差异与裁决

瓦垄 LOD1 的抽稀率与截面边数：

| 家族 | 抽稀 | 截面 | 证据 |
|---|---|---|---|
| 住屋（G10、S84） | 逐板段重排一半（n0 // 2，段内居中） | 8 → 4 | g10.json：74→36 根，t28→t12；S84 60→30。round1 隔根抽取在根数为偶时排不对称（S84 右端空 0.535、左端 0.245），round2 改为重排后逐三角吻合 |
| 殿堂（deyang、yutang、gallery、mingtang） | 1/2 | 保持 8 | palace ribs.txt：deyang 234→116、gallery 62→32 |
| sidehall、guard、biyong | 约 1/3 | 8 → 4 | palace lodiff.txt、ritual |
| 试做门 | 约 1/4 | 8 → 4 | gates loddiff：kaiyang 111→27、pingcheng 81→15 |

裁决：按家族选规则档 `profile='house' | 'hall' | 'gate'`（`ly.LOD_PROFILES`）。新铺量的住屋、店铺用 house，殿堂、廊庑用 hall，续做城门用 gate。

LOD1 圆木：
- deyang、yutang、mingtang 的 LOD1 保持 16 边；
- sidehall、guard、access、biyong、试做门、住屋降到 8 边，是多数。
- 裁决：降到 8 边（`round_lod1=8`）。

LOD2 柱：
- 辟雍用菱形（4 边柱，顶点在轴上）；
- 明堂、灵台、太学、城门、住屋用轴对齐方盒。
- 裁决：方盒，因为多数这样做，而且包围盒与柱径一致。

城垣 LOD2：A/B/C 带单色 COLOR_0，westwall10 和 enclosure 改用 earth__FLAT。裁决：续做城垣时 LOD2 用 earth__FLAT，不带 COLOR_0，与建筑一致。

---

## 7. 命名与层级

| 对象 | 规定 | 证据 / 说明 |
|---|---|---|
| 文件 | `<slug>-<变体>-LOD<n>.glb`；slug 小写连字符，变体一个大写字母。市肆、住屋房型：`<原型>-LOD<n>.glb` | kaiyang-K、pingcheng-P、biyong-A、deyang-A/B、mingtang-A/B、sidehall-A；S84-LOD0.glb、G10-LOD0.glb |
| 地面补丁 | `<slug>-ground-LOD<n>.glb` | kaiyang-ground |
| 静态节点 | **跟随所在卡片家族**（`Assembly(naming=...)`，`ly.NAMING`）：default `<slug>-<变体>-static_<材料>`（23 张卡片 272 个节点）；market `<原型>-static-LY_P01_<mat>__PBR`（LOD2 为 __FLAT，S84/S86）；house_types `layout__LY_P01_<mat>__PBR`（G10）。每种材料一个 | `bible_work` 统计；`validate/round2/measure/orig_gltfjson.txt` |
| 网格名 | default = 节点名；market / house_types = `<原型>_<该材料组第一个构件名>`，三档同名：S84_floor、S84_frontpost_sloped_cap、S84_roof_left（G10 同） | orig_gltfjson.txt |
| 顺序 | 节点、网格、材质、贴图、图片按 earth → path → paper__stone → timber → tile（`MAT_ORDER`）；二进制块按「网格 k 的 4 个 bufferView → 该材质 3 张图」交错 | 她 34/45 个含三种材料的 LOD0 文件是 earth、timber、tile（4 个是 earth、tile、timber）；S84/G10 的 bufferView 长度与偏移和复刻件逐项相同（round2 compare） |
| 门扇节点 | `<slug>-<变体>-leaf_<序>_<L/R>` | jin-C-leaf_0_L |
| 层级 | 场景名 'Scene'；所有节点平铺在根下，无父子，无空物体、相机、灯 | 全部（石经院场景无名） |
| 材质 | `LY_P01_<材料>__PBR` / `__FLAT`；禁止副本后缀 | §3 |
| 图片 | `<earth\|wood\|tile\|stone>-<basecolor\|normal\|orm>`，木材叫 wood | 全部 LY_P01 卡片；yong-apron 用 sha 作图名，不推广 |
| 节点 extras | 跟随家族，键序固定：default `{evidence, metres_per_unit: 1.0, LOD}`（试做门与辟雍）；market `{prototype, module, unit: 'metres', evidence, version, meters_per_unit: 1}`（整数 1）；house_types `{prototype, module, unit: 'metres', evidence}`。module 按材料组：S84 body / frontframe_counter / roof_left，G10 body / front_supports / roof_left | S84、G10 六个文件（orig_gltfjson.txt）。meters_per_unit（美式）有 16 张卡在用，读取时两种都认；新开的家族用 default 写法 |
| 网格 extras | 不写 | 她的网格无 extras |
| 材质 extras | 不写（brick 例外） | — |

注意：Blender 物体、网格的自定义属性会随 export_extras 导出成 extras。组件记录 `obj['ly']` 只留在 LOD0 预览物体上，导出用的合并物体只带上表的键（库已处理）。

---

## 8. 导出设置（在 Blender 5.2.1 上复刻她 4.3.2 的输出）

她的导出器：216 个可读文件中 211 个是 `Khronos glTF Blender I/O v4.3.47`（Blender 4.3.2）。另外 3 个是宫墙水道的 `LY private deterministic lossless static batch v1`，3 个是石经院的 `private deterministic source/build.py, Blender 4.3.2`，都是自写的写出器。还有 A1-v3-LOD1 用了 EXT_meshopt_compression。新模型只用 Blender 官方导出器。

`ly.EXPORT_SETTINGS`（全部显式写死；4.3 没有的参数自动跳过）：

```python
export_format='GLB', export_yup=True, export_apply=True, export_extras=True,
export_normals=True, export_tangents=False, export_texcoords=True,
export_vertex_color='MATERIAL', export_attributes=False,
export_materials='EXPORT', export_image_format='AUTO', export_keep_originals=False,
export_unused_images=False, export_unused_textures=False,
export_cameras=False, export_lights=False, export_animations=False, export_skins=False, export_morph=False,
export_draco_mesh_compression_enable=False, export_meshopt_compression_enable=False, export_use_gltfpack=False,
export_shared_accessors=False, export_gpu_instances=False, export_gn_mesh=False,
use_mesh_edges=False, use_mesh_vertices=False, export_original_specular=False, use_selection=True
```

5.2 里与她必须对齐、默认值不对的项（`ritual/exporter_probe.json` 与 5.2 源码 `io_scene_gltf2/__init__.py` 实测）：
- export_apply 默认 False，必须改 True；
- export_extras 默认 False，必须改 True；
- 5.2 新增 export_meshopt_compression_enable（默认 False），保持 False。

导出前的准备（库的 `build_lod_objects` 已做）：
1. 按材质合并成一个物体，节点名、网格名按 §7，变换为单位矩阵；
2. 全部面 Shade Flat；
3. 生成 UVMap 盒式 UV；
4. 材质关闭背面剔除；
5. 贴图从 `textures/<res>/` 加载，不修改，保证原字节嵌入；
6. 面的起点决定导出对角线（导出器按首点切四边形、按环的起点耳切多边形），库的构件按她的起点写面：方盒 `geo_box`；屋面板端面两块四边形 (0,5,4,1)(1,4,3,2)，板底三面从 i 起、板顶三面从 j 起；竖柱封口 (n−1..0)/(0..n−1)；斜管（瓦垄）封口 (0,n−1..1)/(1..n−1,0)。round2 用这些规则后 S84、G10 三档 18 个网格的三角形与她逐个相同（`validate/round2/tess/`）。bmesh 预三角化（BEAUTY 等）反而更不像（`tess/tri_methods.json`），`TRIANGULATE` 保持 None。

实测结果：demohut-A 与 kaiyang-K（LOD0、LOD2）、G10（LOD1）的 GLB JSON 逐键比对，贴图引用先换成「图名@sha」再比（`bible_work/json_compare.txt`）。以下各项全部一致：asset.version、scenes（'Scene'）、extensionsUsed（无）、材质 JSON（含贴图字节 sha）、samplers、贴图数、图元属性与 mode、uint16 索引、节点键、单 buffer。extras 只多了 demo 自己传的可选键 version。

无法消除的差异：
- generator 写成 `Khronos glTF Blender I/O v5.2.40`。不手改这个字符串（会谎报文件来源）；要与她一致只能在 Blender 4.3.2 上最终导出，本机没有 4.3.2，round2 未做。
- 5.2 按物体名字母序输出节点和材质（earth、tile、timber），她的 4.3 文件是 earth、timber、tile。**已消除**：`export_glb` 导出后调用 `reorder_glb`，只改排列与索引、不改数据字节；改排后 S84/G10 的 nodes、meshes、materials、textures、images、bufferViews（长度与偏移）与她逐项相同。
- 导出日志有 `More than one shader node tex image used for a texture` 警告：ORM 一张图供粗糙度和金属度两个插口所致，结果正确，可忽略。

未量到：Blender 5.2 其余几十个动画、骨骼类参数与 4.3 的默认值差异没有逐项实测。静态建筑用不到这些参数。

---

## 9. 交付检查清单

### 9.1 自动（库函数；任何一项不过都不交付）

| 检查 | 函数 | 判据 | demo 结果 |
|---|---|---|---|
| 悬空 | `ly.check_floating(a)` | ① 朝下的面按 0.12 m 取样向下打射线，离支承 ≤ 5 mm，或样点埋在别的实体里，或在地面；② 不满足时把构件外扩 5 mm，与邻件相交即算接触支承（两端搭在梁上的梁、立在细望柱上的扶手）。门扇、地面补丁豁免 | 小屋 0、小亭 0；反例「离地 0.3 的方盒」被测出，gap 0.3 |
| 穿插 | `ly.check_intersections(a)` | 两两 BVH 三角相交（先各自收缩 2 mm，剔除贴面）。允许：瓦垄、正脊、戗脊入板；梁顶、墙顶、檩条入板底；檩条穿山墙；檐枋入柱；檐柱、柜台腿入地坪（round2）；相交区整个落在屋面板实体内 | 小屋 0、小亭 0 个意外；反例「墙穿柱」被测出 |
| 共面 | `ly.check_coplanar(a)` | 不同构件之间法线同向、平面距 < 0.1 mm、重叠面积 > 1 cm² 即报（会闪烁）；法线相反的贴面不报；z=0 上朝下的贴地底面不报（穿地坪的柱底与地坪底同在 y=0，从下面看不到） | 0；改正前测出 4 处檩条端面与板端面共面；反例被测出 |
| 落地 | `ly.check_grounded(a)` | 建筑最低点 = 0（±2 mm）；低于地面的构件须带 ground / below_grade 标签 | 通过；反例「整体抬高 0.1」被测出 |
| 入口净空 | `ly.check_clearance(a, center, direction, min_width, min_height)` | 在门洞中线 1.0 m 高处左右打射线量净宽，从门槛向上量净高；再在通行矩形内按 0.1 m 取样沿通行方向打射线，碰到任何构件即阻挡 | 小屋净宽 1.40、净高 2.08、无阻挡；小亭 4.08 / 3.00；反例「关着的门扇加窄洞」被测出（宽 0.64、高 1.70、阻挡 171 点） |
| 梁顶埋入 | `a.beam_under_roof` | 梁顶埋入板内 > 0.9 × 板厚即报错 | 小屋第一次按 H72 用 0.30 深的枋时被拦下 |
| GLB 自检 | `ly.inspect_glb`（`export_lods` 自动跑） | 无扩展；材质名合规且与 LOD 对应；PBR 不写因子；无 occlusion、emissive；doubleSided；贴图字节属于共享库且分辨率对应 LOD；LOD2 无贴图；属性仅三项；uint16；无退化三角；节点都有名、无副本后缀；静态节点（非门扇）无 TRS；节点名、网格名等于命名规则给出的期望值；材质顺序按 MAT_ORDER；平直法线 100%；世界盒式 UV 严格吻合 ≥ 99.9%（45° 并列面不计入，单独报 `uv_ties`）；最低点 y = 0 | 6 个 demo 文件全部通过；反例文件报 6 项问题 |

反例测试脚本：`test_checks.py`，9/9 通过，报告在 `demo/test/test_report.json`。

### 9.2 人工

1. 用 `mq/render.py` 出 iso、back、close、front、side、wire，再用 `validate/round2/render_street.py` 出 street、backlow（眼高 1.6 m 仰看檐下），与同家族她的卡片并排看（参考 `validate/round2/renders/compare-*.png`）。看颜色是否同档，瓦垄粗细与间距是否同家族，有没有发白或发灰的贴图。
2. 三档 LOD 的包围盒一致（差 ≤ 2 cm），原点一致，LOD2 远看剪影不变。
3. 面数比例落在 §6.3 的验收区间内。
4. 接口：
   - 住屋套件前檐墙外皮在 z=0，单体建筑台基中心在原点，正面 +Z；
   - 与地面补丁、相邻院墙的接缝落在整 0.01 m 上；
   - 门道、通道方向与城市路网一致（门道沿 Z 贯通，与城门家族相同）。
5. extras 的 evidence 句写清「是什么、不是什么」，卡片说明写明证据等级。
6. 文件名、节点名、材质名逐一核对 §7。
7. 不得出现她体系外的元素：斗栱出跳、曲面屋顶、倒角、彩色，以及新材料。

---

## 10. 工具库 `ly_style.py` 速查

```python
import sys; sys.path.insert(0, r'C:/Users/suxin/AppData/Local/Temp/claude/bfd0867865ae17cc/14ddfcf2-ca06-49dc-95f8-4586da1502c1/scratchpad/mq/style')
import ly_style as ly
a = ly.Assembly('slug', 'A', evidence='C … not a surveyed building', profile='house')   # house | hall | gate
# 续做市肆 / 住屋房型卡片：ly.Assembly('s90', 'A', profile='house', naming='market', prototype='S90',
#     modules={'earth': 'body', 'timber': 'frontframe_counter', 'tile': 'roof_left'}, extras={'version': ...})
```

| 类别 | 函数 | 说明 |
|---|---|---|
| 材质 | `pbr_material(mat, res)`、`flat_material(mat)`、`material_for(mat, lod)` | 五种材料；贴图从 textures/512、/256 加载 |
| 体块 | `box`、`platform(taper=)`、`floor_slab`、`ground_patch`、`add_geo` | |
| 木构 | `column`、`post`、`beam`、`beam_under_roof`、`round_beam`、`sweep`、`ludou`、`purlins`、`railing` | |
| 墙门窗 | `eave_wall(roof, ..., band=True)`、`wall(openings=, z1=(外,内), band=)`、`gable_wall(z_shoulder=)`、`court_wall`、`door_frame`、`door_leaf(angle_deg=, separate_node=)`、`window` | |
| 踏步 | `steps(u0, u1, face, z0, z1, riser_max=0.15, going=0.32)` | 自动分级 |
| 屋面 | `roof_gable(..., ribs=, ridge=, splits=, slab_name=)`、`Assembly.rib_xs_segments(segments, pitch, divisor)`、`roof_hip(..., ridge_half=, ribs=, ridge=, hip_ridges=)`、`eave_tiles(roof)` | 返回 Roof 对象（top_z / bottom_z） |
| LOD | `component_geometry(comp, lod, profile)`、`build_lod_objects(a, lod)`、`assembly_from_objects(objs, …)` | 后者从 LOD0 物体（含手工件）还原，再派生 LOD1/2 |
| 导出 | `export_lods(a, outdir)`、`export_glb(objs, path)`、`reorder_glb(path)`、`EXPORT_SETTINGS`、`NAMING`、`node_name / mesh_name / file_name / node_extras` | 一次三档、改排顺序并自检 |
| 检查 | `report_checks(a)`、`check_floating`、`check_intersections`、`check_coplanar`、`check_grounded`、`check_clearance`、`inspect_glb(path, expect_lod)` | |

最小示例：`demo_build.py`（小屋 demohut-A 与庑殿小亭 demoting-A）。运行方法：

```
D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P demo_build.py -- <outdir>
```

---

## 11. 分歧与裁决汇总

| 分歧 | 以哪个为准 | 理由 |
|---|---|---|
| 调色板：棕（LY_P01）还是灰（REUSED_C 与旧 LOD1） | 棕 | 27–35 张卡用棕；灰只在 7 张旧卡里；灰 LOD1 加棕 LOD2 会跳色 |
| 材质名：有后缀还是无后缀（gate-A、石经院、城垣） | 有后缀 | 按材质名判断 LOD 的工具在无后缀处会误判 |
| UV 密度：1 m 还是 2 m | 1 m | LY_P01 全部为 1 m；2 m 只在 REUSED 与 xiaoyuan |
| 节点名 | 跟随所在卡片家族（default / market / house_types） | round2：同一张卡片里的新文件必须与该卡已有文件同式；新家族用 default（23 张卡） |
| metres 还是 meters | metres（读取时两种都认） | 18 比 16 张卡，试做门与辟雍为模板 |
| 原点 | 单体：台基中心；住屋：前檐墙外皮 z=0 | 两种都是多数家族的一致做法；辟雍 y=0 在台顶，不推广 |
| 瓦垄做法 | 细管（A） | 面数省；三大家族通用；类型门的逐片瓦面数失控 |
| 瓦垄排布 | house 逐板段排（pitch 0.28，段内居中）；hall、gate 全长等距 | S84/G10 实测；殿堂、城门未按段复核 |
| 瓦垄 LOD1 | house 逐段重排一半加 4 边；hall 1/2 加 8 边；gate 1/4 加 4 边 | 各家族内部一致，跨家族不一致，跟随所在家族 |
| LOD1 圆木 | 8 边 | 多数家族如此 |
| LOD2 圆木 | 2r 方盒 | 多数如此（辟雍菱形为少数） |
| 住屋正脊 | 不设 | G10、S84、workshed 都没有 |
| 柱础材质 | earth | 辟雍、太学的础都在 static_earth 节点里 |
| 檐墙顶缝 | 照她留缝（§4.9） | round1 改成斜顶封缝，街面视图里少了檐下暗带，评审判为不一致；round2 改回 |
| 檩条端面、LOD2 栌斗与望柱 | 按本规范改进（§4.10） | 外观不变，消除闪烁和悬空 |
| 檐柱柱脚 | 从 0 起穿过地坪 | S84 实测；穿插检查放行 post/floor |
| 门叶 | 静态并网；需要动画时用 jin 的单独节点 | 试做门、类型门都是静态；jin 是唯一带动画的 |
| 踢面 | 0.15（坛台可 0.20） | 宫殿家族与明堂 |
| 导出器 | 官方 glTF 导出器 | 211/216 个文件如此；自写写出器有 doubleSided=false、uint32 等差异 |

---

## 12. 未量到 / 待确认

1. Blender 5.2 与 4.3 导出器的全部默认值差异未逐项实测（静态建筑用到的项已对齐并经 JSON 比对确认）。
2. 类型门倾斜檐板（0.172×0.479）的位置与倾角未量到，库未实现。
3. compact_work 院墙压顶逐片小瓦（66 片、每片 16 三角）的截面未量，库用方板代替。
4. 「正面」在城门 GLB 里没有标记（前后对称），只能按城市路网判断。
5. jin 门扇的 UV 是按世界坐标（关闭姿态）还是局部坐标投影，未量到。本库按导出姿态的世界坐标计算。
6. 地面补丁 LOD0 顶面细分的用途（是否留给起伏）未量到。本库的 ground_patch 不细分。
7. H72 后檐 0.2 m 缝：S84、G10 同类暗缝在街面视图可见（round2 `renders/*-street.png`）；H72 本身未出街面图。
8. 她是否有意回避斗栱，GLB 里没有依据。
10. 瓦垄 pitch 的精确值未量到（0.28 是能复现 6 段根数的推断值）。
11. 「墙垛 + 通长墙带」只在 G10 核过；H72 等门窗顶标高不同的多洞口墙怎么拼未量到。
12. 斜管封口起点规则只在住屋瓦垄（8 边、4 边）上核过；正脊、戗脊、叉手未核。
13. Blender 4.3.2 最终导出未做（本机只有 5.2.1），generator 仍是 v5.2.40。
9. 宫殿、住屋、市肆、器物四个家族的分析员事实没有随任务下发。本规范对这四家的引用来自它们留在 `mq/style/{palace,housing,market,production}/` 的输出文件，关键数字经总编复核：G10、H64、H72、H96、S84、workshed、gate-A、kaiyang 用 `bible_work/glbparts.py` 重量。

---

## 附录 A 证据文件索引

| 文件 | 内容 |
|---|---|
| `mq/style/stats.json`、`stats.py` | 全部洛阳 GLB 的材质表、导出器、节点模式 |
| `mq/style/bible_work/texcensus.py` → `texcensus.json`、`allimg/` | 216 个文件逐图 sha256、均值、用途 |
| `mq/style/bible_work/glbparts.py` | 原始 GLB 连通块分析（平直率、UV 吻合率、部件签名）；输出 g10.json、h64.json、h72.json、small.json、kai0.json、gateA.json |
| `mq/style/bible_work/dumppart.py` | 单个部件顶点转储（G10 板与瓦垄、H72 墙体与门窗、kaiyang 瓦垄与正脊、gate-A 檐口瓦） |
| `mq/style/bible_work/ref/` | 她的 G10、gallery-A 用同一 render.py 出的对照图 |
| `mq/style/gates/` | 城门与阙分析员：measure.json、glbjson.json、loddiff.txt、textures.json、tex/ |
| `mq/style/ritual/` | 礼制与城垣分析员：analysis.json、glbjson.txt、parts/、exporter_probe.json、tex/ |
| `mq/style/palace/palace_constants.json`、`ribs.txt`、`lodiff.txt` | 宫殿家族 |
| `mq/style/housing/housing_style_constants.json`、`rep2_small.txt` | 住屋家族 |
| `mq/style/production/`、`mq/style/market/` | 器物、市肆 |
| `mq/cards/<id>/audit.json` | 每个文件的包围盒、中心、面数 |

## 附录 B demo 结果（`demo/`）

| 文件 | 三角 | 材质 | 贴图 | 自检 |
|---|---|---|---|---|
| demohut-A-LOD0.glb | 1740（round2 起 1796：住屋瓦垄改为按段排、pitch 0.28） | earth/timber/tile __PBR | 9 张 512，sha 与共享库一致 | 通过 |
| demohut-A-LOD1.glb | 636（round2 起 660） | __PBR | 9 张 256，一致 | 通过 |
| demohut-A-LOD2.glb | 280 | __FLAT | 无 | 通过 |
| demoting-A-LOD0.glb | 2396 | __PBR | 9 张 512 | 通过 |
| demoting-A-LOD1.glb | 1300 | __PBR | 9 张 256 | 通过 |
| demoting-A-LOD2.glb | 356 | __FLAT | 无 | 通过 |

- 渲染：`demo/r/*.png`（iso、back、front、side、close、wire、wireclose）。
- 对照：`demo/compare_sheet.png`，她的 G10、gallery-A 与本库 demo 并排。
- 完整报告：`demo/demo_report.json`、`demo/test/test_report.json`。

## 附录 C round1 验证（S84 与 G10 复刻）

做法：先读她的 S84-LOD0/1/2、G10-LOD0 量尺寸（`validate/round1/measure/measure_orig.py`、`dumpverts.py`，输出 `orig_parts.txt`），再只用库函数重搭（`validate/round1/build_round1.py`），不读入、不拷贝她的几何。

库的补充（全部是可选参数，缺省行为不变；demo 三角数 1740/636/280、2396/1300/356 不变，`test_checks.py` 9/9 通过）：
- `a.post / a.column(..., cap_roof=roof)`：柱顶斜切贴屋面板底（G10、S84）。
- `a.post / a.column(..., lod2_shape='diamond')`：LOD2 用 4 边菱形（G10、S84）。
- `roof_gable(ribs=dict(lift_ref='edge', lift_ridge=, ridge_gap=, xs=))`：住屋瓦垄端点（§5.8 末）。
- `ALLOWED_INTERSECT` 加 (beam, post)：S84 檐枋 x±3.65 伸进柱心 x±3.6 的 Ø0.20 柱 0.15。

仍与她不同、本轮未改的地方：
- 屋面板：她分 3 段（在 x=±3.7 / ±4.7 断开，60 三角），库 1 段（20 三角），外观相同。
- 瓦垄横向排布：她按板段分格，每格居中（S84：两端出际段各 2 根、间距 0.375，中段 26 根、间距 0.2846；G10 中段 33 根、间距 0.2848）；库在全长上按 0.29 等距排，根数相同（S84 每坡 30、G10 37），最外一根差 0.06 m。
- LOD1 瓦垄：她按板段重新排一半根数（S84 出际段 1 根、中段 13 根，间距 0.569），不是 LOD0 的子集；库是隔根抽取。根数相同（每坡 15）。
- 墙顶：她的后墙（S84）、前后墙（G10）墙顶是平的（3.0 / 3.2），与板底之间留 0.2 缝；库按 §4.9 做成斜顶贴板底。
- 檐枋（S84）：她的枋顶 3.2 不抵板底（离板 0.03–0.11），复刻件照她原样用 `a.beam`，没用 `beam_under_roof`。
- 柱脚、柜台腿：她的 S84 柱从 y=0 起穿过 0.22 地坪，柜台腿底埋入地坪 0.06；复刻件都从地坪顶 0.22 起（外观相同，免得报穿插）。
- 节点名：她的是 `S84-static-LY_P01_<mat>__PBR`、G10 是 `layout__LY_P01_<mat>__PBR`；库按 §7 写 `<slug>-<V>-static_<mat>`。

三角数：S84 她 1956 / 604 / 176，复刻 1892 / 540 / 112（差额全在屋面板 3 段与 1 段、夯土 80 与 56）；G10-LOD0 她 2360，复刻 2296。

## 附录 D round2 验证（S84 三档 + G10 三档）

做法：读她的 S84-LOD0/1/2、G10-LOD0/1/2 量尺寸与写法（`validate/round2/measure/orig_parts.txt`、`orig_gltfjson.txt`，复用 round1 的 measure_orig.py / dumpverts.py），只用库函数重搭（`validate/round2/build_round2.py`），不读入、不拷贝她的几何。面的起点规则用 `validate/round2/tess/` 的探针从她的三角形反推，探针只读位置。

按 round1 评审改的库（都已写进本规范对应条目）：
- §3.5 UV：严格比较 float32 法线（`UV_TIE = 0`），坐标双精度、cos/sin 取精确 0/±1；自检把 45° 并列面单列。
- §4.9 檐墙平顶留缝（`eave_wall`）；§5.3 山墙在檐口线分墙身盒 + 山尖（`gable_wall(z_shoulder=)`）；带门洞檐墙用通长墙带（`band=True`）。
- §5.1 檐柱从 0 起穿地坪，柜台腿底 0.16；`ALLOWED_INTERSECT` 加 (post, floor)、(counter, floor)；`check_coplanar` 豁免贴地底面。
- §5.8 屋面板按柱外皮分 3 段（`splits=`），端面两块四边形；§5.9 瓦垄逐段排（pitch 0.28）；§6.2 LOD1 逐段重排一半（`lod_set` 组件，只在 LOD1 出现；LOD0 预览集合里是隐藏物体，`assembly_from_objects` 能还原）。
- §7 命名、网格名、extras、文件名按家族（`NAMING`）；§8 导出后 `reorder_glb` 改排为 earth→timber→tile；面的起点规则。

结果（`validate/round2/measure/compare.txt`、`compare.json`，她的对复刻件）：

| 文件 | 三角（她 / 复刻） | 顶点（位置 + 法线 + UV）吻合 | 三角形吻合 | 节点 / 网格 / 材质 / 图片顺序、材质 JSON、图片字节、bufferView 长度与偏移、extras 键序 |
|---|---|---|---|---|
| S84-LOD0 | 1956 / 1956 | 3 个网格都 1.0000 | 1.0000 | 全部相同 |
| S84-LOD1 | 604 / 604 | 1.0000 | 1.0000 | 全部相同 |
| S84-LOD2 | 176 / 176 | 1.0000 | 1.0000 | 全部相同 |
| G10-LOD0 | 2360 / 2360 | 1.0000 | 1.0000 | 全部相同 |
| G10-LOD1 | 688 / 688 | 1.0000 | 1.0000 | 全部相同 |
| G10-LOD2 | 224 / 224 | 1.0000 | 1.0000 | 全部相同 |

吻合按位置 1 mm、法线 0.01、UV 0.001 分箱计。仍不同的有三处：generator（v5.2.40 对 v4.3.47）；extras 的 evidence 与 version 值（复刻件写明是 Claude round2 复刻，故意不同）；部分顶点的 float32 末位：timber、板（LOD2 tile）三档全部逐位相同，earth S84 全同、G10 64 个里 56 个同，瓦垄只有 15–67% 逐位相同（S84-LOD0 tile 984 个里 176 个），其余差 1 ulp，来自瓦垄端点先取 6 位小数、坡面公式写法不同，外观无差别（`measure/bitpos.txt`）。

渲染（`validate/round2/renders/`、`pixel_diff.json`）：orig-* 与 mine-* 用同一台机器、同一脚本出图。iso、close、front、back、side、street、backlow 各视图色差 > 30 的像素都是 0.000%，线框图 ≤ 0.026%。round1 的 close 视图是 18.98%（S84）和 20.67%（G10）。
