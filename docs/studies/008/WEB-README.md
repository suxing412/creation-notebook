# 008 / 透幕 VEIL · 独立观察网页

主入口为 `index.html`。这是静态观察图版，不是Three模型观察页换皮；原模型的独立观察页仍为 `viewer/index.html`。

## 内容与边界

- 孔洞、遮挡、孔间实体三种读法；三个真实几何预设。
- 主图和孔缘裁片随预设一起更新，保留完整原图入口。宽幅主图为独立wide摄影；方图与宽图相机不同，不互相用作投影热点。
- 主图名义输入来自原 `model-info.json`；报告给出的孔口折线净空下界另列。解析孔口面积比不是投影可见率、透光率或孔隙率。
- 原模型全部公开清单字节保真接入。网页报告在 `web-review/`，源码在 `web-source/`，展示摘要在 `web-assets/`，不改写原模型报告。

## 渐进增强

无JavaScript时，正文、三组模型、静态图版、章节锚点与真实下载可阅读；脚本只增强图版选择。图片/元数据失败时保持旧图旧标签并给出重试；没有成功图片时显示诚实的不可用提示。GPU不属于主页面依赖。

## 本地阅读与复查

解压完整包后可直接打开正文及下载原文件。交互fetch建议使用标准静态HTTP服务；开发环境预览仅使用宿主允许的单一预览工具。本包不附发布身份、登录状态、服务命令或自动发布配置。

已有环境中可运行：

```sh
node web-source/test_state.cjs web-review/state-unit-checks.json
node web-source/test_app.cjs web-review/app-unit-checks.json
python -B web-source/test_import.py --output web-review/import-unit-checks.json
python -B web-source/verify.py --directory .
python -B web-source/verify_delivery.py --directory .
```

这些分别是模拟状态、实际app模拟、隔离ZIP故障、静态来源和交付身份检查，不替代浏览器或模型质量门禁。最终浏览器检查绑定的输入见 `web-review/browser-checks.json`。

## 托管压缩与下载路径

`web-delivery.json` 只存下载URL与标签。父级图库若采用同SHA共享vendor或将单个BLEND无损压缩，应另做托管投影清单并逐字节回验；不得全局替换JS或原几何元数据。本独立完整包仍保留原模型文件，不嵌套另一份整体ZIP。

## 未验

GPU材质与实时操作、实体iPhone/Android、200%浏览器缩放、完整读屏流程以及物理/制造性能未由本网页验收。320 CSS宽度只代表云Chromium中的窄布局。最终ZIP另在托管目录外交付，用于离线保存或Space附件。
