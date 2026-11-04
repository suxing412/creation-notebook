# 手账标题字体

`notebook-hand.woff2` 来自霞鹜文楷 Regular v1.530。站点以 `Notebook WenKai` 为字体族名称，自托管四个作品库入口使用的字形，使用 `font-display: swap` 加载。子集保留上游版权与许可元数据。

- [上游项目](https://github.com/lxgw/LxgwWenKai)
- [固定版本 v1.530](https://github.com/lxgw/LxgwWenKai/releases/tag/v1.530)
- [原始 TTF](https://github.com/lxgw/LxgwWenKai/releases/download/v1.530/LXGWWenKai-Regular.ttf)
- [同版本 OFL 许可原文](https://github.com/lxgw/LxgwWenKai/blob/v1.530/OFL.txt)
- 本地许可全文保存在 `OFL-LXGW-WenKai.txt`。

原始 TTF 的 SHA-256 为 `2d73eea94ad808999d90c0000c239a84a33b09d4bc6ab6c5b8bbf1eda8a7fc8b`。

## 内容更新后的再生成

下载以上固定版本 TTF 到站点目录之外。生成环境使用 Python 3、FontTools 4.68.0 与 Brotli 1.2.1。

```sh
python -m pip install "fonttools[woff]==4.68.0" "brotli==1.2.1"
python modeling-lab/gallery/subset_notebook_font.py /path/to/LXGWWenKai-Regular.ttf
```

脚本读取首页与三个作品库入口的正文，提取所需字符并生成 WOFF2 和 `subset-manifest.json`，同时把主题样式中的字体 URL 查询版本更新为字体 SHA-256 的前八位。清单记录字符覆盖、输出大小及输入输出摘要，可用于复查。上游未提供的装饰符号 `↝` 和 `✳` 使用 CSS 字体栈中的后备字体。标题和便签的中文字符包含在子集中。
