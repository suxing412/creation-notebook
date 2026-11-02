# F04：真正换几何的有限迁移样本

这个样本不是新一轮作品，也不以换颜色充数。它将 F04 中的 ORISON / VEIL 换为 **LATITUDE / HORIZON**：回环由竖向变为横向，幕由窄高变为宽低，孔阵列从 6×8 变为 9×5。两件源 GLB 都保留原始字节与材质。

## 固定与可变

固定：生成器与主 F04 同字节；两模型实例 scale=1、摆放平移、旋转；全部相机与目标、40°垂直 FOV、1.6 画幅；原光照、原台座、径向摄影背景；Blender 4.3.2 / Cycles CPU / 128 samples / 1280×800 / seed 0 / AgX / 不降噪。没有为新构图默默挪物、缩放、换材质。

可变：两个经过已有门禁的模型文件，以及从新模型实际三角面重新取得的语义锚点、重新计算的可见掩码。它们不是可以无条件继承的屏幕坐标。

本次只测试两组配对：原 ORISON + VEIL，以及这个 LATITUDE + HORIZON 样本。其尺寸跨度只是实际测试点的外包范围，不是连续参数范围证明，不保证任意厚度、曲率、形体或任意模型保持同样效果。

## 一次真实失败及修复

直接继承旧环定位点会失败：它不在 Latitude 的可见表面上，且 overview 的首命中从幕变成了环。aperture 与 around 的旧可见掩码也与实际三角面不符。旧幕定位点的高度 430 mm 超过新幕 320 mm 的顶缘，因此语义上也不再是幕面点。

原配置与失败检查保存在 `dist/assets/scene-inherited.json`、`reports/inherited-anchor-failure.json`。没有把此失败版本作为最终导航配置。

重新取 Latitude 第1836面中心，得到世界点约 `[0.08980851, 0.06572940, -0.22961976]`。同一相机组中，它在 overview 先被 Horizon 挡住，在 aperture 经过 Horizon 圆柱中面的有效内部区域而不碰实体并首达该点，在 around 绕开幕的有效区域而首达该点。容差 0.1 mm，使用实际双面 GLB 光线计算。它只证明这一指定视线，不代表整件可见率、透光率或孔口通行能力。

幕的锚点也重取为实际可见三角面中心。最终 `scene.json` 与 `scene-reanchored.json` 相同；旧失败配置单独保留。锚点只影响网页语义及检查，不影响三张离线图的几何、相机和照明，因此没有为改锚点重渲染或修图。

## 复现

在包含主 F04 的完整来源包中：

```sh
SAMPLES=128 WIDTH=1280 blender -b -t 8 --python-exit-code 1 --python reuse/source/build.py
python reuse/source/sanitize_public.py
blender -b -t 4 --python-exit-code 1 --python reuse/source/audit_blender.py
node --loader ./reuse/source/local-loader.mjs reuse/source/audit-rays.mjs scene-inherited.json inherited-anchor-failure.json
node --loader ./reuse/source/local-loader.mjs reuse/source/audit-rays.mjs scene.json rays-transfer.json
python reuse/source/check_contract.py
```

Three r180 从主 F04 的 `dist/vendor` 读取。源输入身份在 `source/source-inputs.json`，源脚本与配置均在包内。检查失败必须非零退出；不要把旧 JSON 文件当成本次成功。

## 验收与局限

同一视觉语言指原材质、光照、背景、固定镜头系统与相同离线采样质量，并非逐像素相同或每个新模型有相同构图占比。具体几何、首命中、接触、相机净空、失败控制与可见性结果见报告。新的横向组合占据画面的高度较小，必须保持真实尺度，不为了填满画面伪造尺寸。

CPU渲染、数学证书和离散射线不代替GPU、实时闪烁、手机或工程性能测试。原模型完整自交门禁未在此重复宣称；本轮只复核引用身份、导出关系和装配条件。
