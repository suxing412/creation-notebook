# 回环 ORISON · 造物手记 007

第4个「2+1」周期的第一件常规作品。原创连续陶瓷视觉雕塑，不是灯具、折板或外部模型改色。

## 三组真实几何

- **Orison / 回环**：偏心直立，周期宽度节奏；真实圆角14mm、最大滚转16°为接受后的soft基线。
- **Latitude / 横境**：宽低轮廓、较扁截面。
- **Ascend / 上行**：窄高轮廓、深厚截面、更明显前后起伏。

三组统一材质、主机位、背景、灯光、曝光与seed=0；不按各自包围盒重新缩放摄影。`assets/<variant>/` 保存纯模型 `model.blend`、实际 `model.glb`、摄影 `scene.blend`、配置、6张CPU离线图和最终身份门禁。`.blend`/GLB不是示意图或外链占位。

入口 `index.html` 由独立网页设计作者制作；`viewer/index.html` 是本模型的独立 Three.js r180 观察室。无JS/无GL仍有正文、三组真实图片与下载。实时光照不是Cycles；GPU、动态闪烁与实体iPhone未验。

## 家族与保证边界

单位米，Blender Z向上；GLB导出Y向上，坐标映射 `(x,z,-y)`。中心线是本配方原创的周期三角函数组合。解析frame由固定Y参考轴和切线建立，再施加周期滚转；不是一般RMF/最小扭转传输。仅支持参考轴远离奇异的本家族。

固定320站点 × 36圆角矩形截面点：11520顶点、11520四边面、23040导出三角。4段真实圆弧、每段8份，加上截面直段；不靠shader伪圆角。末环通过取模连到首环，**无重复端环、无端盖、无weld modifier**。一件连通封闭genus1网格，Euler特征数0。

`schema.json` 仅表达输入盒。Python运行时另拒绝非有限数、布尔/字符串、版本/键集合/seed错误，以及圆角吞没直段、参考轴近奇异、采样曲率×截面外接半径≥0.72、采样非局部间隙<6mm。检查器用更密960点复核，并检查真实网格。

**输入接受≠网格通过≠视觉接受。** 三组和low/high两个有限几何边界样本，不证明十维连续参数盒。1024角点只做输入层检查，没有生成1024个网格。非相邻BVH跳过共享顶点三角；近共面使用数值容差，不是符号几何证明。超出已支持家族不能凭这一门禁放行。

## 复现

环境：Blender **4.3.2**，自带Python；外部Python 3.12 + Pillow用于包装与无损去除PNG元信息。Three.js固定r180本地文件，MIT许可见 `vendor/THREE-LICENSE`。渲染Cycles CPU、AgX、无降噪、无自适应、正式128 samples/960²，seed0。

在本目录执行：

```sh
python source/run.py --config configs/orison.json --output assets/orison-rebuilt
python source/run.py --config configs/latitude.json --output assets/latitude-rebuilt
python source/run.py --config configs/ascend.json --output assets/ascend-rebuilt
python source/test_contract.py --report review/input-rerun-unique.json
python source/test_faults.py --baseline assets/orison --report review/faults-rerun-unique.json
node source/test_viewer_state.mjs
node source/test_three_loader.mjs
```

输出目录必须新建；正式文件不就地覆盖。`run.py`先生成几何并门禁，再花渲染预算，再以最终文件自身SHA复检；调用带 `--python-exit-code 1`，同时确认新报告、显式PASS、输入/配方/检查器SHA与文件检查期间未变。失败模型留内部work，不伪装正式资产。模型复现承诺是同配置/版本的几何与材质/摄影约束；不保证跨CPU逐像素一致，也不把重保存native说成字节相同。

已有模型只读门禁：

```sh
python source/run_gates.py --asset assets/orison --label my-new-unique-label
```

每次标签必须新，防旧报告造成假PASS。检查纯 `model.blend`，不把包含摄影地面/灯光/相机的 `scene.blend`当模型；拒绝modifier、shape key、parent、constraint、animation、driver与非identity对象矩阵。

## 评审与证据

- `review/first-version/`：首版真实文件与低采样图。
- `review/research-and-iteration.md`、`research.json`：首版后官方原作者/方法研究；区分实际照片观察、索引正文、推断、采用与不采用。
- `review/crown-before/`、`crown-after/`：冠部侧轮廓疑点的真实射线定位和同机位近景。改进是真圆角/滚转，不是法线/纹理遮掩；仍保留投影前后轮廓交接。
- `review/gate-review.md`：独立数字几何门禁、专项反例、已验/未验与限制。
- `review/costs.json`：实际资产字节与可获得的计算耗时；无虚构美元/API计费。
- `manifest.json`：允许交付文件的SHA与字节；work、原始日志、坏二进制、私有路径与外部原图不公开。

## 不是制造认证

模型最低点平移到Z=0；摄影地面为避免数值重合位于Z=−0.2mm，不把这点间隔当成实体接触。接地区很窄，是数字陈列姿态；未证明可自立、载荷、陶瓷成型/烧制、石材加工、公差或长期耐久性。当前只对有证据的数字几何与离线外观负责。没有修改受限GL设置来换取所谓“实时通过”。
