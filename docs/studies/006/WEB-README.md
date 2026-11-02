# FOLIO 折页 · 独立网页 006

这是制作图解／技术编辑页，不是Three.js观察器换肤，更不是F03融合轮。

## 结构

- `index.html`：原生阅读流；路径→厚壳→同尺度变体→源档案。
- `style.css` / `app.js`：本地样式与可选真图切换，无远程依赖。
- `view.html`：模型负责人的独立Three.js观察入口，降级保留真实PNG。
- `assets/diagrams/`：由实际model-info坐标生成的原创SVG与出处哈希。
- `web-source/`：图解与页面生成源、报告渲染、11项图版状态单元测试、7张SVG反投影检查、静态身份检查。
- `recipe-source.zip` / `source/` / `configs/`：模型公开交付原样接入。
- `design-case.html` / `web-review/`：网页首版→原站检索→评审→修订→限定复检→复盘。

## 复现本页

在完整目录中用Python 3运行（不依赖第三方Python包）：

```sh
python web-source/render_reports.py
python web-source/compose.py
node web-source/test_app.cjs
python web-source/test_diagrams.py
python web-source/verify.py
```

`compose.py`非draft会要求模型/图版/测量/源/观察器齐备，核对模型报告SHA与配置；不能将缺资产页面称为完成。`--draft`仅用于本地明确标记的布局工作，不是可发布状态。

图解坐标严格来自model-info的YZ站点与局部法向；m→mm仅用于标注。三小侧图共用固定比例，不显示X向宽度。SVG来源含输出与输入哈希；B3局部记录站点范围与变换。

## 发布集成

本任务不发布。父级将完整目录放入`studies/006/`时，`../../index.html`应返回图库；独立预览无法证明该集成链接。最后构建后还会用“模型源包全部条目＋明确网页文件集合”检查实际目录，不只依赖扩展名黑名单。不拷`qa/`、`before/`、外部原站截图、原始日志、临时模型或非冻结资产。

## 验证边界

浏览器范围以web-review/browser-qa.html为准。CSS视口不是手机硬件；CPU渲染不等于GPU；有限站点与网格门禁不等于制造、承载或全域厚度证明。未开启或修改WebGL安全设置。

模型review文件在最终目录仍是`review/`，以保持模型manifest路径与哈希。网页独立报告放`web-review/`，避免同名reference-notes/reflection互相覆盖。本地编辑目录临时用review存网页稿、model-review存模型记录，build明确映射。

## 本地冻结

`python web-source/freeze.py --directory <完整交付目录>`会先在目标目录重跑图版单元测试、SVG反投影、静态/出处检查和严格文件集合门禁，全部通过才生成`WEB-FROZEN-SHA256.json`。清单列出除自身以外每个文件的SHA256与字节数，不代表上传或部署成功。不要在冻结后直接改文件；改动后应重跑同一流程。
