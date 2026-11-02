# Vesper / 暮灯 — 网页作品 005

独立设计目标：一份可读、可比、可复现的产品规格图录，而非用模型查看器替代网页设计。主图录由本地 HTML/CSS/JS 组成，不调用外部字体、模型库、图像或 AI 服务；独立 `view.html` 使用模型负责人的本地 Three.js r180 和实际 GLB，失败保留真实离线图。

完成状态：首版之后已检索 Flos、Muuto、Wästberg+ 原站，完成评审、修订、实际模型 1.1.0 接入和限定范围浏览器复检。发布候选仅为清洁 `dist/`；原始布局占位和故障测试副本不进入该目录。没有执行 Sites 或 GitHub 发布。

## 文件与职责

- `index.html`：完整基础阅读层；即使不执行 JavaScript，三变体、参数表和下载仍应可达。
- `style.css`：独立视觉系统与响应式布局。
- `app.js`：可选离线图切换；新图预加载成功前保留上一张，失败保留选择和规格，不依赖 WebGL。
- `before/`：真实时间顺序中的首版快照，明确包含资产占位。它是设计过程证据，不是当前成品。
- `review/`：网页设计检索/评审/复盘与证据。
- `qa/`：受控 CSS 视口测试页、静态检查、非浏览器 JS 单元测试。
- `integrate.py`：只读取模型负责人的冻结产物，复制并验证校验和；不修改任何模型源或模型 QA。
- `dist/`：冻结静态交付目录，同时供支持的 `sites-preview` 本地预览；不是已发布的 Sites。

## 本地检查

```sh
python qa/check_static.py
node --check app.js
node qa/test_app.mjs
python qa/check_links.py
```

浏览器测试只能通过 `sites-preview` 的返回 URL 与原生 `cua_repl` 工具。不要启动其他服务器、安装独立浏览器或开启 WebGL。受控 iframe 的 CSS 视口检查不代表真实手机或物理 GPU 验收。

## 已知集成边界

页面返回图库链接采用 `../../index.html`，对应最终 `studies/005/` 集成位置。独立根目录预览无法证明该返回链接正确；必须由图库集成负责人在最终目录中复查。

首版对标记录中的厂商图片只作为内部观察证据；不进入最终网页的视觉资产，不复制其产品形态、品牌或页面源代码。

## 验证与边界

真实浏览器已检查 6 个受控 CSS 视口、键盘、无脚本、两类真实 404 故障及恢复；独立观察器验证 WebGL 失败保离线图，不声称 GPU 通过。详见 `review/browser-qa.html`。`README.md` 是模型负责人说明；网页设计复盘在 `design-case.html`。模型公开源 ZIP 的 103 个条目原样保留，冻结哈希列于外层 `FROZEN-SHA256.json`。
