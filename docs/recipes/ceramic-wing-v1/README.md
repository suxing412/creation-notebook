# Ceramic Wing v1 · 可复用造型配方

不是保证“任何模型都一样好看”，而是把一个已定义的造型族、构造法和摄影棚固化：**换轮廓参数，保持瓷白 / 铜线 / 深青背面、闭合翼壳、柔和大面高光和可读剪影。**

## 可复现条件

- Blender **4.3.2**（生成器在创建输出目录前严格检查版本；其他版本直接拒绝，不静默标记已验证），CPU Cycles，Python 随 Blender；包装 CLI 用 Python 3 + Pillow。没有外部模型、贴图或生成式 API。
- 同一版本生成器、JSON、seed=0、网格分辨率 N=100 / M=48、固定材质和灯光。
- 只用于本配方的薄翼 / 鳐鱼式有机壳体。不是角色、建筑、任意导入网格、生产制造连续曲面的通用保证。
- 单件初始展幅 8.5–11.5 抽象单位；生成后统一展宽 10，y 包围盒居中、最低点 z=0.85。无物理单位承诺；真实尺寸改变需重新评估材料、光源与制造条件。
- 固定厚度函数、上拱 .75|u|³、左右不对称 .24u³、弧顶 .16(1−cos²t)(1−|u|)。这些是**锁定的构造约束**，不是开放滑块。
- 前缘指数 1.5–1.9、弦长系数 .90–1.08、尾长系数 .85–1.15、展幅 8.5–11.5 只是**输入接受范围**。验证过的是下表三个离散组合，不是整个四维连续域。新组合必须重新经过全部检查与人工多视角评审。

| 配置 | 展幅 | 弦长 | 前缘指数 | 尾长 | 意图 |
|---|---:|---:|---:|---:|---|
| baseline | 10 | 1 | 1.7 | 1 | 原比例控制组 |
| broad | 11.5 | .9 | 1.5 | .85 | 宽展、短尾、低弦长 |
| swept | 8.5 | 1.08 | 1.9 | 1.15 | 深弦、长尾、更收束的剪影 |

## 生成 API / CLI

```sh
python source/run.py --config configs/broad.json --output my-broad --threads 4
```

JSON 参数契约见 `config.schema.json`。这是推荐入口：暂存生成 → QA → 渲染 → 通过才复制到目标目录；拒绝覆盖已有目录。`source/generate.py` 是底层 Blender 构造 API，支持 `--geometry-only`，其临时输出不代表已验收。执行异常用 `--python-exit-code 1` 显式返回失败，不能只看 Blender 的默认退出码。

原 Study 002 完整保留，此处是它的受限参数化分支。每件输出 `model.blend`（纯模型）、`model.glb`、`scene.blend`（实际摄影棚）、四视图、`model-info.json`、`validation.json`。

## 几何与装配不变量

8 个闭合对象，18,668 三角面。翼尖使用单极点三角扇，无零半径重复圈；每条拓扑边恰好连接两面。铜周边半径固定 **.016**、中脊半宽 .035 / 扁平比 .35，保留原修正版的细铜脊而非裂缝感石墨槽。尾根是独立嵌入件，不假装焊接为制造用连续曲面。

检查拒绝：退化三角面面积 <1e−10；世界坐标四舍五入 1e−7 后重复三角面；非二流形边；BVH 非相邻自交；跨对象平面法线阈值 1−1e−7 与平面距离 1e−6 的共面接触；未经允许或缺失的装配接触组。允许列表仅包含翼壳与嵌线/尾根、首尾缘尖端接触、尾身与铜脊等原构造关系。**接触并不归零**，每组实际数值保存在报告中。

局限：BVH 排除共享顶点三角面，不能证明所有相邻折叠不存在；也不能识别完全包容、接触穿透深度或所有接近而未相交的共面面片。曲率没有得到解析上界证明；本次以局部铜管减径 + 离散 BVH 回归验证控制风险，不把它叫全参数无自交定理。

## 固定材质 / 摄影条件

以下 RGB 是节点内的线性值，不是可直接复制成 CSS 的 sRGB：

| 材质 | linear RGB | metallic | roughness |
|---|---|---:|---:|
| 瓷白 | .78, .72, .59 | .12 | .29 |
| 深青背面 | .023, .075, .077 | .32 | .30 |
| 铜 | .56, .245, .105 | .80 | .25 |

3 盏圆盘区域灯：key 1800 / cool fill 1300 / tail 1100，功率比 18:13:11；尺寸 7/6/5，位置、颜色与固定瞄准点见生成器。World 灰 .25；地面 .34/.31/.265、roughness .68。归一化后摄影棚不随造型参数变化。

AgX、sRGB 显示、曝光 0、gamma 1；CPU Cycles seed 0、beauty 128 samples，其余 48，禁用降噪。Beauty 800×680，正交尺度 14.6，位置 (9,−12,12)，瞄准 (0,0,1.5)。顶、前、侧相机完全固定。不同 CPU / Blender / 色彩配置可能导致像素差异；种子不是跨硬件逐像素一致的承诺。

## “同样效果”的验收

1. 三个不同轮廓均通过同一几何门槛，不通过不能发布。
2. 四视角不裁切；前缘、尾根与中脊可辨，铜线不过度抢占白瓷大面。
3. 固定材质/摄影数据可机器比对；高光阅读与剪影还需要人眼评审，不能靠一个主观评分冒充保证。
4. 可复现的是这套流程与视觉语言，不是每个角度同亮度或相同像素。

## Blender / Three.js 的边界

glTF 保留 PBR 参数与几何；Three.js 使用 GLTFLoader / linear 工作空间 / sRGB 输出，不应再次对已解码的线性颜色做 sRGB 解码。离线路径追踪区域灯、间接光、AgX 与浏览器实时阴影不是相同算法；即便同名色调映射也不保证完全匹配。当前 demo 展示**真实 Blender 离线图**，不是伪装的实时截图；实时 GL、z-fighting 动态检查和实体手机尚未验收。

技术依据：
- [Three.js 官方 Color Management](https://threejs.org/manual/pages/color-management.html)：工作 / 输出色彩空间与 glTF 推荐工作流；本轮已读取。
- [Blender 官方 Color Management](https://docs.blender.org/manual/en/4.0/render/color_management.html)：AgX 背景；本轮仅检索摘要可读取，全文抓取返回错误，未声称逐项全文核对。
- [Khronos glTF 2.0](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.pdf)：PBR 互换规范参考，不等于跨渲染器图像一致。

评审与修复见 `review/reflection.md`，失败与最终数据均保留以避免只展示成功样本。

## 本次交付证据
- `review/reproducibility.json`：同环境两次 baseline GLB 字节一致。
- `review/scene-audit.json`：实际 .blend 读取的材料 / 灯光 / 色彩配置与各变体 bounds。
- `review/html-tests.json`：12 个变体 / 视角组合的脚本逻辑与图片存在性检查；不是浏览器布局或手机验收。
- `contact-sheet.png`：真实最终四视图并排图；主图 128 samples，其余视图 48 samples。

形态对标原作者：[Igor Puškarić · Orchid Manta](https://igorpuskaric.artstation.com/projects/1nqBNK)、[Johnson Martin · Skye](https://johnson-martin.artstation.com/projects/QnNGzE)。仅作为原 002 已有设计研究背景，不包含其任何模型 / 图片资源。

底层生成器的 `model-info.json` 只记录已实际计算的拓扑断言，完整 QA 状态为 pending。包装入口渲染后再次检查最终模型，才从 validation.json 写入最终非二流形数与 static-QA-passed 状态。新参数组合仍必须通过完整 QA，不因版本匹配而豁免。
