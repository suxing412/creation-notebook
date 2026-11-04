# 造物手记 · Creation Notebook

**把想象做成有形之物，把经验留下来。**

三维造物、网页实验与可复用方法的独立静态作品集。

**当前入口：1 个大型项目、20 个模型家族、13 个模型介绍网页、2 个空间原型与 4 个历史空间实验。** 分类及数量见 `docs/notebook-index.json`；发布状态与设计验收分别记录。制作过程、检查证据与尚未验证的边界随作品保留。

## 目录

- `docs/`：完整静态网站；入口 `docs/index.html`。
- `docs/studies/`：常规作品、真实模型、渲染、源码和复盘。
- `docs/fusions/`：三维网页融合实验。
- `docs/recipes/`、`docs/methods/`：几何配方与工作法。
- `modeling-lab/gallery/`：Python 静态构建器、作品清单与原字节 ZIP 分卷工具。

005/006 源 ZIP 使用带 SHA-256 校验的原字节分卷；通过作品页的源码下载入口还原完整 ZIP。007 保留全部 354 个原始文件，不用精简版本替代。已有报告中的验收日期与限制仍有效，不表示本次重新验证了模型/GPU/手机。

## 本地预览与维护

当前站点为直接维护 HTML/CSS/JavaScript 的静态站，无需安装依赖或生成页面。四个入口分别为 `docs/index.html`、`docs/model-library/index.html`、`docs/web-library/index.html`、`docs/space-library/index.html`，共用基础样式 `docs/notebook.css`、手账主题 `docs/notebook-design.css` 与交互 `docs/notebook.js`。手账主题只作用于这四个入口，作品详情保留各自设计。库内容索引保存在 `docs/notebook-index.json`。

在仓库根目录启动本地预览：

```sh
python -m http.server 8000 --directory docs --bind 127.0.0.1
```

然后打开 `http://127.0.0.1:8000/`。维护后执行静态入口检查：

```sh
python modeling-lab/gallery/build.py
```

该命令现在只检查现有页面，不重建或覆写首页。也可直接运行 `python modeling-lab/gallery/check_overview.py`；检查范围为四个入口的本地引用、重复 ID、筛选节点及目录数量，不代表浏览器交互、GPU、真机或设计验收。只需 Python 3 标准库，不需要账户密钥。

旧目录生成器保留显式命令 `python modeling-lab/gallery/build.py --legacy`，仅用于独立的旧版检出或准备好的 `modeling-lab/gallery/dist/` 旧版快照；检测到现行库入口时会拒绝覆盖。不要直接执行 `build_legacy.py` 或 `build_overview.py` 维护新版首页。详情见 [工具说明](modeling-lab/gallery/README.md)。新增站内链接使用相对 URL，以兼容 GitHub Pages 项目子路径；部分历史页面仍保留已发布站点的绝对 URL。

## GitHub Pages 设置（由仓库所有者执行）

仓库为 `suxing412/creation-notebook`。以下是待执行配置说明，不表示网站已经上线。预期项目路径为 `/creation-notebook/`；预期 Pages 地址为 `https://suxing412.github.io/creation-notebook/`，须以 GitHub Pages 部署结果验证。

1. 将本项目文件提交到新公开仓库的 `main` 分支；须先存在 `docs/index.html` 和空的 `docs/.nojekyll`。
2. 打开新仓库 **Settings → Pages → Build and deployment**。
3. **Source** 选择 **Deploy from a branch**。
4. **Branch** 选择 **main**，文件夹选择 **/docs**，点击 **Save**。
5. 等待 GitHub Pages 部署成功后，从 Pages 设置中的 **Visit site** 打开并检查实际 URL。

不需要添加自定义 workflow、扩大 token 权限或改变其他仓库的可见性。GitHub 会使用其 Pages 部署流程；空 `.nojekyll` 用于关闭默认 Jekyll 构建。

依据：[GitHub 官方发布源说明](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)、[静态文件与 `.nojekyll`](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)（核对日期：2026-11-02）。

## 权利与公开范围

本仓库只归档本作品系列，不包含其他项目或其他仓库的历史。第三方代码及其 MIT 等许可文本按原文件保留；外部参考链接不代表引用对象授权再分发。本 README **不对原创模型、图像、设计、源码或文字额外授予许可证**；适用范围以相应文件已有的明确说明为准。
