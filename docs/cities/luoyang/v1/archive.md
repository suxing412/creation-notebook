# 洛阳旧版归档

原应用取自提交 `bd9ea87`，归档日期为 2026-11-04（Asia/Shanghai）。

入口为 `index.html`。保留旧版全部 21 个应用模块、3 个 HTML 页面与 `shell.css`，以及 `mode`、`c01stage`、`c02stage` 等查询参数导航。

模型、图片、数据与研究记录共用上级目录的 `assets/`、`data/` 和 `research/`。`resource-url.mjs` 将旧模块和原始 JSON 中的资源地址解析至该目录。共享 Three.js 导入增加一级相对路径，页面中的资源站内链接相应调整。

阶段合同与原投影映射仍位于 `../project-stage-contract.json` 和 `../projection-map.json`。这些文件记录原提交的路径与内容身份，归档过程保留其原始字节。
