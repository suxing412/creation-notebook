# LY-011 开工准备 · 开阳中门道承托框架修订（草案）

状态：**待输入**（G 未冻结；另缺 bearing-section-v1 与「开阳适配失败/实际剖面记录」两份必需输入）。本目录没有任何交付几何，只有读入、实测和测试准备。

核对基线：creation-notebook-lab main `bce3211f818ee5a8bef1773539da70695ba37b17`（只读；该工作树另有 lab/data/*.json 三个未提交修改，与本项无关，未触碰）。

## 1. 本项目标（照任务池原文，不扩写）

替代失败承托样例的**柱列、地栿、横梁子件与三档**；解决实测门楣/横梁重叠，明确是替换而非双层叠加；不改左右门道，不宣称荷载安全。验收：用实际导出重测门楣/梁/柱交体和净空；旧 0.0936 m³ 问题有可定位的前后证据；柱梁底顶接触与地面端口明确。

## 2. 已核到的现有成果（文件 + SHA256）

| 输入 | 路径（lab 仓） | SHA256 |
|---|---|---|
| K-v1 LOD0（库卡） | docs/library/models/m-luoyang-kaiyang-gate/files/kaiyang-K-LOD0.glb | 88d9a3223ded3229f90fa1e6702c68771a675edcf15d6d09f3e0fe5f50aeefec |
| K-v1 LOD1 | docs/cities/luoyang/progress-assets/north13-gates/luoyang-kaiyang-gate-study-v1/models/kaiyang-K-LOD1.glb | d82f13fcbadaf5dd713bbbc2b8c826c87e1165c7dccf23e520379559bf521ee8 |
| K-v1 LOD2 | 同目录 kaiyang-K-LOD2.glb | 13ff78a7a1fe9159ed577d715ff30c75cf3d0e8f6d2d47311968f660986ed801 |
| 城景实际加载的平面投影 | docs/cities/luoyang/progress-assets/flat/study-north13-kaiyang-K-94693c58dd63.glb | 94693c58dd6308153c5900b0bb9698eff138811f39369f54f545b9034417e71e |
| 地面附件 LOD0/1/2 | docs/library/models/m-luoyang-kaiyang-gate/files/kaiyang-ground-LOD{0,1,2}.glb | 5754432a… / 50f85502… / e758e45f…（全值见 inputs.json） |
| 源包 ZIP（仓内分卷） | modeling-lab/review-batches/2026-11-04-north13-gates/luoyang-kaiyang-gate-study-v1/content.zip.part00{1,2} | 拼接后 bad99bb9f5b301b5b6a3450931511caec385df3da8b5ffc5b94b1664eb598c23（与 manifest 一致） |
| 源包内原生 .blend LOD0/1/2 | prep/_src/…/models/kaiyang-K-LOD{0,1,2}.blend | 95568b8b… / f283dbf9… / c8ef8d10… |
| 生成器 | prep/_src/…/source/build.py、geometry.py | df0be5ed… / 47ef2902… |
| 三角→源对象映射 | prep/_src/…/qa/source-object-ranges.json | a13c9f741347db813ff2deb3678b5ad6062fbc84584a3117df7a44939d42fdea |

源包内三档 GLB 与公开路径**逐字节相同**（SHA 一致）。源包里的 .blend 是净化后重开版本，原 QA（qa/dimensions.json）绑定的原生 SHA（88877470…、f876be9e…、7deda70c…）与现文件不同，按 NATIVE-EQUIVALENCE.json 视为几何等价、非同一字节；本项一律以 GLB 为量测对象。

城景加载：`city-data.mjs:708` 资产 `study-north13-kaiyang-K`（平面投影 GLB）→ `city-data.mjs:4178` researchModel `research-north13-kaiyang-K`（space `local-study`，`cityPlacement: null`，`initial: false`）→ `city-renderer.mjs:286-299 loadAsset` 仅在 `focusResearchModel`（`city-renderer.mjs:646`）打开独立研究视图时读取。K-v1 LOD0/LOD2 与三档地面附件**不被城景加载**，只在资产卡出现。即：模型能读取 = 是；已入城 = 否（source.json placement `activation: false`）。

## 3. 改 / 不改范围（草案，待 LY-006 冻结端口与所有权后改定）

改（仅以独立子件 + 替换清单交付，源 GLB 只读）：
- 中门道（x∈[-2.8, 2.8] 本地，y∈[-5, 5]，z∈[0, 5.0]）内的柱列、地栿、横梁三档子件；与 K-v1 的接口只在墩面 x=±2.8、楼板底 z=5.0、地面端口 z（待 LY-005 定）三处。
- 若新横梁需占用现 `C_door_head_1`（门楣）或 `C_jamb_(1,±1)`（门框）位置：在 assembly 里明确「隐藏/替换哪一个源对象」，不得两层叠放。

不改：
- 左右门道（opening 0/2、`C_jamb_(0|2,*)`、`C_door_head_0|2`、侧门叶）。
- 门叶 `C_open_leaf_(1,±1)` 与 `C_leaf_batten_(1,*)`：属 LY-012；本项只把其占位作为禁入体积。
- 楼板 `C_upper_deck` 本体：属 LY-013；本项只用其底面 z=5.0 作为梁顶端口。
- 上层守室、廊柱、屋盖（z≥5.34）：不改。实测的上层交体（见 §5.4）只记录、移交。
- 城市总表、项目卡、资产卡、main。

## 4. 证据与未知（四类分开）

- 原始考古/原文：门名与南垣东端相对方位（《后汉书·秦彭传》注引《汉官仪》，源包 docs/evidence.md 记录；本轮未重新访问原文，按源包记录转述）。不涉及承托构造。
- 异地异期类比：汉晋三门道研究仅作类型类比；源包明言不移植建春门 30×12.5 m，不用北魏两重百尺。本项不引入任何北魏/西汉/画像砖承托尺寸。
- C 工程设计：K-v1 的全部尺寸（中门道 5.6 m、墩宽 2.8 m、门道高 5.0 m、楼板厚 0.34 m）以及本项将做的柱列、地栿、横梁全部为 C。
- 未知：东汉开阳门门道是否有排叉柱/地栿、木构过梁还是其他承托方式、柱径与间距、古地面高程；「0.0936 m³」原始失败样例的几何。

五件事分开：模型能读取（是）/ 局部通行通过（未做本项检查）/ 已入城（否）/ 真实结构安全（不做、不宣称）/ 历史复原成立（否，C 候选）。

## 5. 实测缺口（全部来自实际导出 GLB，脚本 `prep/measure_k_central.py`，SHA256 c41d6401147b39847885a0edd2b7d610742e67a1c5a6a9a102b08caddff293d5）

运行：`D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P prep/measure_k_central.py -- <ranges> <out.json> <ground.glb|-> <label=lodN=glb>...`；结果 `prep/qa/k-central-measure.json`（SHA 61fac69e…）、`prep/qa/k-allpairs-lod0.json`（全对，ae1ec4a9…）、`prep/qa/ground-LOD{1,2}-measure.json`。

5.1 **中门道楼板底无承托**：楼板 `C_upper_deck` 底 z=5.000，跨中门道净跨 5.60 m、进深 10 m。在 x(-2.8,2.8)×y(-5,5) 上以 0.05 m 网格取 22,400 点，下方 0.01 m 内有构件顶面的只有 **3.0%**（672 点：`C_door_head_1` 624、两根 `C_jamb_(1,±1)` 各 24），全部集中在前檐 y∈[-4.96,-4.64] 一条 0.32 m 宽带；其余 97% 楼板底悬空（只靠两侧墩边）。LOD0/1/2 与城景投影四份结果相同。
5.2 **楼板跨中上方有立物**：坐在楼板顶 z=5.34 且落在中门道净跨内的源对象 7 个：`C_gallery_post_(0,±3.8)`（x∈[-0.17,0.17]，正跨中，LOD0 各 0.2946 m³）、`C_central_room_rear`（跨满 5.6 m，3.452 m³）、`C_central_room_front_±1`（各 1.071 m³）、`C_central_room_side_±1`（墙体仅 0.02 m 越出墩边）。新横梁位置应优先对准 y=±3.8 与 y=-1.3、y=3.8 这几条落点线——这是 C 设计建议，不是受力结论。
5.3 **门楣/门框/楼板之间没有正体积交体**：中门道下部框架（`C_door_head_1`、`C_jamb_(1,±1)`、墩、楼板）在 K-v1 三档中全部是面接触（AABB 重叠厚度 0）。全模型 LOD0 977 对中有 695 对正体积交体、合计 3.251 m³，**没有任何一对落在 0.0936±0.003 m³ 内**。结论：任务池所说「旧 0.0936 m³ 门楣/横梁重叠」不在 K-v1 本体里，只能来自缺失的 bearing-section-v1 / 适配失败样例；在拿到该样例前，「前」的证据无法定位，验收这一条处于**阻断**。
5.4 **中门道上层已有交体（继承，不归本项）**：`C_central_room_rear`∩`C_gallery_post_(0,3.8)` LOD0 0.1811 / LOD1 0.1728 / LOD2 0.1309 m³（廊柱穿过守室后墙）；守室前/后墙与侧墙角部各 0.0357 m³（4 处）；`C_cross_tie_0` 与廊柱、廊枋、椽、屋壳共约 0.0587 m³（LOD0）；门叶与压条 6×0.00148 m³。中门道相关正体积合计 LOD0 0.5675 / LOD1 0.5456 / LOD2 0.4448 m³。需 LY-006 指定归属（多半是 LY-013/屋盖原负责人），本项不得顺手改。
5.5 **净空**（x=0 起左右射线，z 0.05–4.95，y -5..5 每 0.05 m；离散采样，非连续人体扫掠）：门框间 5.20 m（y≈-4.96..-4.64）；门叶开启区 y∈[-4.55,-1.99] 最窄 **4.89 m**（LOD0/1，压条外缘）/ 4.98 m（LOD2 无压条）；其余 5.60 m。中线净高：门楣下 **4.70 m**（y -4.95..-4.65），其余 5.00 m（楼板底）。任何沿墩面的新柱列，在门叶区内会再吃掉宽度并与开启门叶冲突（LY-012 接口）；无冲突的墩面段为 y∈[-1.99, 5.0]，约 7.0 m。
5.6 **地面端口缺口**：三档地面附件在中门道只有一条 x∈[-0.90, 0.91] 的 1.8 m 测试带，覆盖净跨采样 **33.3%**；顶面 z 0.040–0.042（LOD2 0.040），底 -0.16，门体底 z=0。墩面附近（新柱脚、沿墩地栿所在处）**没有任何地面几何**；而横跨门道的地栿若坐 z=0，会被测试带 0.04 m 顶面侵入。城市试放的工程原点 z=0.17（source.json placement），古地面未知。地面端口高程必须由 LY-005 冻结后再定，本项不得自定。

## 6. 缺的输入（详见 prep-status.json）

1. **bearing-section-v1**：仓库三条分支（main、origin/luoyang-content、origin/workpacks、origin/reviews）、modeling-lab 全部 review-batches 与 D:/GitHub 文件名扫描均未找到。用途：「失败承托样例」本体，「替代」的对象和 0.0936 m³ 的「前」证据。不能从 GLB 重建（K-v1 GLB 里根本没有这套件，见 5.3）。
2. **开阳适配失败 / 实际剖面记录**：同样未找到。用途：失败位置、剖面高差、重叠量算法。不能从 GLB 重建；只能用本目录的 K-v1 实测剖面作替代性基线，但不能冒称是那份记录。
3. 三门地面附件的源工程/生成器：仓内只有公开 GLB，无 .blend 或脚本。用途：如需改动地面端口。可「从 GLB 重建」（几何简单：三条 1.8×14×≈0.2 m 带），但须标为重建。
4. G 冻结件：LY-005 坐标/地面端口、LY-006 端口与所有权、LY-007 材质与三档、LY-008 检查器、LY-010 开阳放行。

## 7. 复用判定

无可复用的合格成果：K-v1 中门道楼板 97% 悬空、无柱列/地栿/横梁，承托框架确实缺；失败样例又不在手。所以本项是**补件**，不是**复用**。
