# 007 · 空处也是形体 / 网页交付说明

常规007，第四周期第一常规。独立雕塑观察笔记，不是F04。

## 阅读入口

- `index.html`：完整静态正文，正侧投影、三几何变体、闭合研究与原文件下载。
- `viewer/index.html`：建模作者提供的独立Three.js观察入口，保留原始路径。
- `design-case.html`：网页首版、真实候选、最终图与复盘。
- `web-review/`：网页专属报告。模型原有`review/`与`manifest.json`未被覆盖。
- `web-assets/`：仅由本次真实GLB产生的投影图与数据，不含外部艺术作品图片。

无JavaScript时，三张实际照片直接列出，正文、原生details、章节与下载保留。JavaScript只增强主图切换，不自动旋转或拦截滚轮。

## 可复跑

Python依赖NumPy、Pillow、SciPy，版本记录在投影数据中。Node用于纯状态与异步模拟测试。源码均在`web-source/`。

```sh
python web-source/project.py --asset-root assets --output web-assets
node web-source/test_gallery.cjs web-review/unit-checks.json
node web-source/test_app.cjs web-review/app-unit-checks.json
python -B web-source/test_projection.py --asset-root assets --output web-review/projection-unit-checks.json
python -B web-source/test_import.py --output web-review/import-unit-checks.json
python -B web-source/verify.py --directory .
python -B web-source/verify_delivery.py --directory .
```

重新生成、测试或改文件后必须重做受影响检查；不能继续使用旧冻结清单。

## 语义与验证边界

正交投影以500mm画幅、205mm垂直中心生成。内空面积为2048²像素上实体覆盖并集的内部连通空白，不是三维体积、最小开口、净空或可穿过物体尺寸。1024²对照只是离散收敛观察。真实材质、物理自立、烧制与制造性能不在本数字研究中。

浏览器通过项见`web-review/browser-qa.html`，单元与静态检查另列。GPU、真机、200%缩放、完整屏幕阅读器不借其它测试冒称通过。

最终包只包含明确模型原包条目与网页允许文件。首版占位HTML、QA副本、外部原图、坏二进制、原始工作日志、私有绝对路径不在交付。托管目录不嵌重复模型ZIP；原包字节身份由`web-review/asset-parity.json`记录。

返回图库与方法页链接需要图库的`studies/007/`目录布局；独立目录阅读正文无需这些返回链接。


## 冻结与完整离线包

`WEB-FROZEN-SHA256.json`逐项记录最终网页包文件（不哈希自身）；`manifest.json`仍是原模型清单。二者职责不同。网页冻结要求新鲜静态、单元、完整原模型身份与已采集的最终原生浏览器输入SHA一致。原模型生成入口、配置和依赖说明由`model-source.html`、`source/`、`configs/`与原README完整保留。

完整离线源码ZIP在网站目录之外单独交付，内含本目录全部原文件和网页生成源。本站没有假设某个外部完整ZIP已经上线，也不嵌重复模型ZIP。图库返回与工作法链接依赖部署上下文，离线独立包中可能无对应图库页面；正文、模型、图版、报告、源与配置均本地可读。
