# 透幕 VEIL · 造物手记 008

第4个「2+1」周期的第二件常规研究。原创穿孔圆柱厚壳视觉雕塑/小型屏风，孔是贯通几何，不是alpha纹理。F04未包含在此包。

## 三个形体，同一摄影

| 预设 | 展开宽×高 | 圆柱张角 | 孔格/孔数 | 名义法向厚度 |
|---|---:|---:|---:|---:|
| Veil / 透幕 | 360×500 mm | 45° | 6×8 / 48 | 8 mm |
| Horizon / 横幕 | 540×320 mm | 24° | 9×5 / 45 | 8 mm |
| Fold / 曲幕 | 280×560 mm | 80° | 4×9 / 36 | 10 mm |

展开宽度不是世界包围盒宽；准确世界尺寸在 `model-info.json.dimensions_mm`。三组固定米制、材质、灯光、主相机、曝光、seed=0；摄影不按各自包围盒重新缩放。Blender Z向上，GLB轴映射 `(x,y,z)→(x,z,−y)`。

每组 `assets/<variant>/` 含真实纯模型 `model.blend`、`model.glb`、摄影 `scene.blend`、配置/元数据与6张CPU图；观察页为 `viewer/index.html`，独立大主页面由网页作者另供。完整离线包保留原生BLEND，不把容量投影后的ZIP下载标签写进模型元数据。

## 参数家族，不是任意网格工具

每个2D矩形单元有一个椭圆孔，单元外边以同一顶点共享，构成单张带孔面；解析映射为圆柱曲面，再按法向向两侧偏移。孔壁以显式环带连接，前后各4段展开参数域四分之一圆弧轮廓，中间为直壁；边框连续。最终每孔环64顶点、四边16段；不依赖Boolean或Solidify modifier。孔缘径向圆弧映射到椭圆圆柱后不保证全位置等Euclidean倒圆半径。

一件连通、封闭、可定向网格，H个贯通孔对应 genus H，Euler χ=2−2H。全部顶点/有向索引面对照配方仅是此受限家族的身份约束；合法重索引网格也会被拒绝，不能冒充通用几何证明。输入范围见 `schema.json`；Python另拒绝非有限数、布尔/错误整数、额外键、错误版本/seed、孔口消耗单元余量与过度曲率/厚度组合。

**输入接受 ≠ 实网格通过 ≠ 人工外观接受。** 三组及两个有限边界样本不证明整个连续参数域。材质为统一暖矿物陶瓷视觉，没有外贴材质或品牌资产。

## 指标含义

- `surface_open_area_ratio`：光滑椭圆口在展开中面上的面积除以展开矩形面积。不是三角网格投影可见开孔率、透光率或制造孔隙率。
- 名义厚度：圆柱法向双层偏移值；门禁读取真实对应顶点实际量测。不等于整个圆弧孔缘/内壁的最小实体截面。
- `ligament_sampling.records`：真实前/后孔口折线到其它孔口及同侧外边框的3D欧氏距离，逐边四等分采样。采样最小值是折线最小间距的上估计；减两侧覆盖半径及0.2µm余量得到保守下界。不是测地距离、全内壁最薄处、连续解析曲面证明或材料强度。

## 复现（新目录，不能覆盖冻结资产）

Blender **4.3.2**，自带Python；外部Python3 + Pillow只用于无损PNG去元信息与打包。Three固定r180本地文件，许可在vendor。正式Cycles CPU、128samples/960²、无自适应、无降噪、AgX、seed0。

```sh
python source/run.py --config configs/veil.json --output assets/veil-rebuilt
python source/run.py --config configs/horizon.json --output assets/horizon-rebuilt
python source/run.py --config configs/fold.json --output assets/fold-rebuilt
python source/run_gates.py --asset assets/veil --label my-new-audit
# 可选宽图（会更新该输出metadata，所以随后必须以新label再审）
blender -b --python-exit-code 1 --python source/render_wide.py -- --asset assets/veil-rebuilt
python source/run_gates.py --asset assets/veil-rebuilt --label my-rebuilt-with-wide
```

`run.py`先几何生成与门禁，再渲染，再对该次最终文件门禁；输出JSON给出新报告位置。原发行manifest只绑定原发行文件，不授予你的重建文件自动通过。所有Blender检查带 `--python-exit-code 1`；新报告、显式PASS、输入/检查器/recipe SHA和检查期间稳定性都需成立。重保存BLEND不承诺字节相同；同版本/配置的几何与视觉规则可复现，不保证跨CPU逐像素相同。摄影scene不是纯模型门禁的输入。

## 诚实的失败与评审记录

`review/research-and-iteration.md`记录首版后联网原作者方法研究与改进。最初孔壁面多反转一次，真实native门禁拒绝；原失败报告不改写。`review/first-version/`只保留失败图像/配置等证据，错误模型二进制留内部work，不作正式模型；`review/baseline-corrected/`为先修正拓扑的32点rev0基线。32点历史源快照在 `review/iteration-32-source/`，不冒充最终64点配方。公平高采样前后对比见 `review/comparison-before/` 与正式Veil图，摄影参数完全一致。

最终有效门禁以 `manifest.json.final_identity_reports` 为准，历史报告不因文件名较新自动成为最终。专项反例必须命中指定字段，不接受被别的检查碰巧拦住冒充通过。详细已验/失败/未验/限制见 `review/gate-review.md`，实际成本见 `review/costs.json`。

## 非制造认证

数字陈列姿态不等于可自立；未验承载、抗弯、陶瓷成型/烧结、耐久、公差、人体接触或固定方式。地面置于Z=−0.2mm仅避免摄影数值重合，不当实体接触证明。GPU、动态闪烁和真实手机/触控未验，不修改受限GL设置。无JS/无GL保底与状态测试另列，不能替代GPU验收。
