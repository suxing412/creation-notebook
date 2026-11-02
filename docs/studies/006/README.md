# FOLIO / 折页 — Study 006

**原创参数化数字资产。** 一片连续厚壳，由前唇、接地前托、阅读斜面、顶部回折、后腿和后足组成。它不是005灯具换皮，不含外来模型、图片或纹理，也不是现实品牌复刻。未来可与005暮灯构成桌面空间F03；本包尚不包含融合场景。

- `view.html`：独立真实GLB观察器，Three.js r180本地依赖；默认离线真渲染，手动尝试实时。浏览器禁GL时保留同变体图片与下载。
- `assets/{atlas,folio,spire}/`：纯模型 `.blend`、`.glb`、可复开摄影 `scene.blend`、7幅CPU真渲染、参数与测量/门禁报告。
- `configs/`、`source/`：可复现配方与检查器；`manifest.json`：最终身份与有限测试记录。
- `review/before-after.png`：相同48采样上限、560²、材质、相机、曝光的真实几何前后对照。
- `review/contact-sheet.png`：三变体七视图；`review/reference-notes.md`：首版后真实原作者/官方方法检索。
- 独立网页制作图解由另一worker设计，不用这个小观察器冒充整份网页设计。

## 三种几何，不换色

| 变体 | 名义宽 × 控制折点高 mm | 阅读斜面角 / 后腿角 | 实际包围宽 × 深 × 高 mm | 三角数 |
|---|---:|---:|---:|---:|
| Atlas · 低宽 | 305 × 135 | 56° / 58° | 304.986 × 271.916 × 131.312 | 10,988 |
| Folio · 折页 | 250 × 190 | 65° / 62° | 249.968 × 273.123 × 183.077 | 12,044 |
| Spire · 高窄 | 185 × 235 | 74° / 69° | 184.979 × 229.093 × 220.811 | 13,004 |

“控制折点高”是未圆角化折线交点的名义参数，不等于实际顶面高度。顶弯去尖后高度降低，顶点采样也可能使实际最大宽略小于名义宽；实际值来自生成网格。

## 生成与复现

在包目录执行，需要 **Blender 4.3.2** 命令 `blender`、Python 3（Pillow用于PNG无损元数据清理；numpy仅用于图像统计辅助），Node.js用于Three解析/状态逻辑测试。联系表辅助脚本使用系统DejaVu Sans字体（Linux路径在脚本内）；核心模型生成不依赖该字体。几何源码只依赖Python标准库、Blender的bpy/bmesh/mathutils。没有远程API、AI账号、CDN或外部贴图。GLB为普通未压缩导出，不需要Draco；安装包导出时可能打印缺少Draco库的探测消息，但没有请求该压缩扩展，实际未压缩payload需通过检查。

```sh
python source/run.py --config configs/folio.json --output work/my-folio --threads 6 --samples 256 --resolution 960
# 新目录事务式生成：先网格门禁，再渲染，渲染后再检查；不会覆盖已有目标。
python source/test_contract.py
blender -b --python-exit-code 1 --python source/check.py -- --model assets/folio/model.blend --info assets/folio/model-info.json --report work/folio-validation.json
python source/check_glb.py assets/folio/model.glb work/folio-glb.json
python source/test_faults.py --baseline assets/folio --output work/faults-new
node source/test_three_loader.mjs
node source/test_viewer_state.cjs
python -m http.server 8000
# 打开 http://localhost:8000/view.html；file://的模块限制不是模型错误。
```

`seed=0`是唯一允许种子；几何没有随机项。同环境同参数两次GLB的字节同一性以 `review/reproducibility.json` 为证，**不承诺不同Blender/硬件或跨渲染器逐像素一致**。脚本退出码非0即未通过；不得将失败目录当正式资产。`work/`为本地临时/复现实验区，不在公开源包白名单中；报告可引用其中历史证据，但公开复现应使用提供的源码与正式基线。

## 参数、合法输入与失败边界

单位为米；两个角用度。`config.schema.json`仅做前置类型/范围说明；`recipe.validate`是权威，还拒绝NaN、Inf、布尔伪数值、多/缺键、非法名字、非0 seed、recipe版本或Blender版本不符。

| 参数 | 接受范围 |
|---|---|
| width / height | 0.18–0.31 / 0.13–0.24 m |
| display_angle / rear_angle | 55–75 / 53–72° |
| tray_depth / foot_depth | 0.038–0.060 / 0.022–0.045 m |
| lip_height | 0.020–0.032 m |
| bend_radius / thickness | 0.006–0.012 / 0.0024–0.0040 m |

耦合约束：中心弯曲半径 `R > 1.6t`；前唇保留至少8mm直段；每一对相邻圆角修剪后，原折线段仍保留至少8mm直线。输入范围接受不等于几何已验。108项显式输入测试全符合预期；512盒角点只跑validator，320接受、192拒绝；**真实生成并跑网格门禁的是三变体、两个全低/全高边界及保存的首版**。未声称整个连续9维域有效。合法参数内的新组合必须重新运行完整门禁。

## 不变量与构造

1. 恰好一个mesh、一个材质槽、一个闭合连通分量，不靠穿插零件拼出弯折。
2. YZ平面中心线由6控制点形成，4处为真正圆弧；修剪长度 `R tan(|转角|/2)`，每个弧段最多2°，直段步长最多8mm。
3. 沿中心线使用法向偏移 `±t/2` 构造厚壳；内/外名义半径分别为 `R−t/2` 与 `R+t/2`。三正式变体均 t=3mm、R=8mm，即6.5/9.5mm。离散弦面中点的厚度略小，不能称全表面绝对等厚。
4. 宽度按归一弧长u经过6个固定平滑控制比例：`.86 → .96 → 1 → .90 → .72 → .76`，不另加装饰。前后端4mm为**平面轮廓**圆角，截面边缘0.65mm；端盖厚度方向边仍是硬边，不是全方向圆角。
5. 两段前/后平面接地，侧面为开放负空间，无隐蔽实体填满内部。端盖采用凸圆角矩形ngon，无零半径重合整圈。
6. 同材质（线性RGB .43/.49/.50、metallic .82、roughness .285）、同主机位/光源/AgX/sRGB/曝光0/seed0。主机位(.52,−.72,.39)m，看向(0,0,.102)m，正交尺度.43m；不会为变体重新放大取景掩盖比例。

Folio原生502组顶底对应顶点间距实测2.9999855–3.0000103mm；250组纵边中点配对为2.99952884–3.00000612mm。弦离散理论亏差与实测量级吻合；这是有限离散测量，不是全表面最小壁厚证书。接地坐标、各弯采样半径见 `section-measurements.json` 与 `review/gate-station-measurements.json`。

## 检查、反例与继承005的改进

- 退化三角面积<1e−12m²；坐标8位小数重复三角；非二面边；局部绕序不一致；非正局部/世界体积；非有限坐标；多连通岛；全顶点及索引循环recipe约束；纯model文件必须identity transform、无modifier/shape key/constraint/parent/animation/driver等未评估状态。
- 非相邻BVH自交候选；双精度、双向平面距离≤50nm、法向cos≥1−1e−7、二维SAT正重叠>10nm的**近共面**检测。共享顶点的非共面相邻折叠仍未得到完整独立证明。
- 006无装配pair例外，因此005“同pair再穿出/完全包容岛”不能借名字绕过；全顶点契约与单连通分别兜住额外几何和无表面交线岛。
- 真实GLB字节解码：有限POSITION/NORMAL、索引范围、buffer/stride/offset边界、法线长度、三角面积和声明极值。不只读取accessor标题。
- 18个真实坏native/GLB必须拒绝且特定字段命中。初次窄斜三角共面专项漏报被保存，修复后重跑，并有移开1µm的非共面控制组；不是用别项拒绝冒充专项覆盖。见 `review/gate-review.md`。
- 前唇角点的尖亮点用同机位射线、实际polygon和端盖着色诊断核对，见 `terminal-feature-evidence.json` 与 `terminal-cap-diagnostic.png`。该诊断图改变材质，仅用于解释，不能当正常产品外观。

## 渲染与成本

先48采样上限/560²，造型评审后128比较，最终选择**256上限/960²**，Cycles CPU、adaptive threshold .01、6线程、无降噪。银灰表面的残余颗粒是采样噪声，不假称拉丝纹理；也不把加采样算几何成功。实际逐变体wall time、文件大小、源码/资产哈希见manifest。没有已知货币账单数据，不编造费用。主机/CPU并发会影响wall time；samples是上限不是每个像素都用足的计费量。

## 验证边界

本资产只完成受约束数字模型、静态检查、真实CPU多视图、GLB实际解析与禁GL保底。**没有GPU/WebGL实时画面、动态深度闪烁、真实iPhone、制造/折弯成形、回弹、公差、材料强度、承载、防倾覆、防滑、书本适配或人体工学验证。** 当前禁GL设置未更改。名为阅读/陈列支架表达设计意图，不是性能承诺。

原创源码与几何的使用范围由所有者决定；Three.js保留MIT许可证，未将依赖版权冒充原创。
