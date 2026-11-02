# 造物手记 · Creation Notebook · 构建与源码交付

本工具目录用于独立公开作品集；仓库根目录的 `docs/` 是完整静态发布源，而不是其他仓库的嵌套子站。独立仓库为 `suxing412/creation-notebook`，站内仍不硬编码主机或仓库 slug；项目路径为 `/creation-notebook/`。总览采用确认的标题“造物手记 · Creation Notebook”和副标题“把想象做成有形之物，把经验留下来。”，既有作品与历史报告保持原始身份。

## 当前收录

- 常规 001–007：7 轮；007 为第 4 组的第一常规轮，不含 008。
- 融合 F01–F03：3 轮；不含 F04。
- 陶瓷翼 v1：1 套独立几何配方。
- 造物手记工作法 v2：独立方法资产，不增加作品计数。
- 随上述作品保留已有的制作复盘、检查报告和带日期研究；不额外带入其他项目、内部笔记、参考宣传原图或故障模型二进制。

## 构建

从仓库根目录执行（Python 3，标准库；不需要 API key 或 npm）：

```sh
python modeling-lab/gallery/build.py
```

`build.py` 从同目录 `manifest.json` 与仓库内 `docs/` 读取，输出仍为 `docs/`。`.nojekyll` 位于发布源根。模板、静态资产、Three.js 与 addon 使用相对链接；原生成器和建模工具需在独立工作副本运行，不应在冻结发布目录生成或覆盖模型。

若需要验证项目子路径，必须把 `docs/` 挂载到 `/creation-notebook/`，而不是只在站点根 `/` 预览。检查首页、作品、返回总览、importmap、模型、分卷及下载脚本；没有实际浏览器/GPU/手机证据时，不宣称这些检查通过。

## 原字节 ZIP 分卷

005 与 006 的 `recipe-source.zip` 以每卷不超过 8 MiB 的连续原字节分卷交付，入口为各自 `source-download.html`。不是删减包，不重新压缩；007 的全部原始文件布局保留，不嵌入另行交付的 combined ZIP。

- 当前可下载路径与完整身份以 `docs/downloads/delivery-map.json` 及各 `source-parts/manifest.json` 为准。
- `docs/downloads/restore-source.py` 先校验每卷，再校验完整 SHA-256，默认拒绝覆盖既有输出。
- 浏览器下载依赖 HTTPS/WebCrypto；只在校验通过后提供 Blob 保存链接。生成 Blob 不等同于已保存到磁盘。
- 需要制作新的分卷投影时，输入只读，输出必须是尚不存在且不嵌套的新目录：

```sh
python modeling-lab/gallery/archive_delivery.py --source-dir FULL_STATIC_DIRECTORY --output-dir NEW_STATIC_PROJECTION
```

构建末尾会重新校验已有分卷和下载入口，不会恢复失效的直接 ZIP 链接。

## 冻结历史与边界

各作品的原 manifest、冻结 SHA 清单、配方及报告描述各自原始快照；它们并非当前分卷投影的直接路径表。`DELIVERY-QA.json` 与 `PROJECTION-CHANGES.json` 原字节保留，描述既有分卷制作和历史检查；其中旧发布路径只用于历史对照，不是本仓库部署设置。当前部署路径以本 README 及仓库根 README 为准。

新增或修订必须在新的独立候选中执行、审计、生成 SHA-256 白名单；不能覆盖已冻结源输入。网页报告区分静态/局部浏览器检查与尚未验证的 WebGL、动态闪烁、实体手机、完整辅助技术等项目，不把历史检查冒充本次新验证。

第三方许可证按文件保留；本说明不向原创模型、图片、设计或文字额外授予许可证。
