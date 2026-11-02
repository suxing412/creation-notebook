# 造物手记 · Creation Notebook

把想象做成有形之物，把经验留下来。

总览与作品同步迭代。manifest.json是作品目录；publication-ledger.json记录独立公开核验，不自动猜测上线。每次修改后运行python3 build.py，按网站overview-acceptance.md复检。生成器支持同级dist、上级dist以及仓库modeling-lab/gallery对应docs布局。保留所有静态资产，不只复制生成器。

列表与Three.js空间目录由同一清单生成。3D须用户明确开启，不自动加载原模型；展台是目录符号，非原件。有限CPU数学、无GL降级和CSS窄屏已查，GPU动态/深度闪烁/iPhone未验。

本候选15项归档中12项此前公开核验，008、009、F04尚待部署核验。状态详情和范围见网站publication-ledger.json。无损分卷交付版本使用downloads/delivery-map.json映射与原字节校验；并非删减模型或伪标ZIP。

## 总览自动检查

在本目录运行 `python3 check_overview.py`，检查链接、清单/卡片/目录按钮一致及重建零差异。脚本支持仓库 `modeling-lab/gallery/` 到 `docs/` 的布局，不依赖其他工作目录。

如需原资产保真检查，显式提供独立保存的旧静态快照：`python3 check_overview.py --baseline /path/to/prior-static-snapshot`。未提供时报告 `assetPreservation: not_checked`，不能当作资产保真通过；路径不存在则失败。允许变化只有根首页及根manifest，其余原文件缺失/改字节会失败。可用 `--report /path/to/report.json` 指定报告位置；报告只供本地验证，不自动发布。
