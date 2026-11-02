# 造物手记 · Creation Notebook

**把想象做成有形之物，把经验留下来。**

三维造物、网页实验与可复用方法的独立静态作品集。

**当前收录：7 轮常规（001–007）、3 轮融合（F01–F03）、1 套陶瓷翼几何配方，以及造物手记工作法 v2。** 制作过程、检查证据与尚未验证的边界随作品保留。

## 目录

- `docs/`：完整静态网站；入口 `docs/index.html`。
- `docs/studies/`：常规作品、真实模型、渲染、源码和复盘。
- `docs/fusions/`：三维网页融合实验。
- `docs/recipes/`、`docs/methods/`：几何配方与工作法。
- `modeling-lab/gallery/`：Python 静态构建器、作品清单与原字节 ZIP 分卷工具。

005/006 源 ZIP 使用带 SHA-256 校验的原字节分卷；通过作品页的源码下载入口还原完整 ZIP。007 保留全部 354 个原始文件，不用精简版本替代。已有报告中的验收日期与限制仍有效，不表示本次重新验证了模型/GPU/手机。

## 构建与维护

```sh
python modeling-lab/gallery/build.py
```

只需 Python 3 标准库。构建不访问私有工作区，不需要账户密钥；详情见 [工具说明](modeling-lab/gallery/README.md)。站内使用相对 URL，允许部署到 GitHub Pages 的项目子路径。

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
