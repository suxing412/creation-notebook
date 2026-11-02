# 造物手记 · Creation Notebook

把想象做成有形之物，把经验留下来。

总览与作品同步迭代。manifest.json是作品目录；publication-ledger.json记录独立公开核验，不自动猜测上线。每次修改后运行python3 build.py，按网站overview-acceptance.md复检。生成器支持同级dist、上级dist以及仓库modeling-lab/gallery对应docs布局。保留所有静态资产，不只复制生成器。

列表与Three.js空间目录由同一清单生成。3D须用户明确开启，不自动加载原模型；展台是目录符号，非原件。有限CPU数学、无GL降级和CSS窄屏已查，GPU动态/深度闪烁/iPhone未验。

截至2026-11-02T05:47:40Z，16项归档的公开入口与内容访问已有核验记录；010介绍页与181文件源索引已实际访问；此状态不等于GPU动态、实时闪烁、全部交互或真机验收。状态详情和范围见网站publication-ledger.json。无损分卷交付版本使用downloads/delivery-map.json映射与原字节校验；并非删减模型或伪标ZIP。

## 总览自动检查

在本目录运行 `python3 check_overview.py`，检查链接、清单/卡片/目录按钮一致及重建零差异。脚本支持仓库 `modeling-lab/gallery/` 到 `docs/` 的布局，不依赖其他工作目录。

如需原资产保真检查，显式提供独立保存的旧静态快照：`python3 check_overview.py --baseline /path/to/prior-static-snapshot`。未提供时报告 `assetPreservation: not_checked`，不能当作资产保真通过；路径不存在则失败。允许变化只有根首页及根manifest，其余原文件缺失/改字节会失败。可用 `--report /path/to/report.json` 指定报告位置；报告只供本地验证，不自动发布。

## 类别与验收

“模型与介绍页”指模型设计及介绍其本身的网页。新的“3D空间设计”要求整个页面是可探索三维空间，空间承担布局、导航和内容；不是嵌入3D窗口。当前此类验收成品为0。F01–F04保留为4项已公开历史实验，设计状态为待重做，公开状态不撤销。总览的3D目录索引不是此新类别范例。

## SD01 原型接入

目录新增独立spaceDesigns数据，不将新空间原型混入旧fusion历史实验。当前10项模型与介绍页、0项已验收新空间设计、1项SD01原型、4项历史待重做、2项方法；截至2026-11-02T06:20:05Z公开入口访问已核验17/17；SD01因GL禁用进入文字备用，源分卷入口已打开，在线三卷浏览器内重组及完整SHA已通过22346955字节，未点保存，不声称磁盘下载完成。原型方向与实时验收尚未完成，19对实体包容未验，不能宣称全部穿插归零。原型完整源包采用字节分卷与SHA还原，不删减证据。构建禁止生成Python字节缓存，发布清单仍应排除__pycache__、pyc及内部QA。
