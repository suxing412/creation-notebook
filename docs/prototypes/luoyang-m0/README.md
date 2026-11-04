# 洛阳 M0 画风原型

独立入口为 `prototypes/luoyang-m0/`。这一阶段供制作人比较画风，画风选择和 Claude 的 tag 评审完成后进入后续阶段。

## 体验

桌面并排显示反向外壳和深度／法线边缘检测，共用一座住宅 A 方案和镜头。可切换墨线实色、铅笔淡彩，调整线宽与纸纹，并通过鼠标或键盘转动、缩放、复位。淡彩采用颜料对纸色的透明合成，建筑之间保持正常遮挡。

手机首次进入显示海报与四张图文样张，点击“打开 3D”后才请求渲染器、three.js 和模型。关闭、取消或渲染失败时回到海报。每次重新打开使用新画布，避免复用已释放的图形上下文。

## 本地验证

在仓库根目录运行以下命令，再打开 `http://127.0.0.1:8765/prototypes/luoyang-m0/`。

```sh
python modeling-lab/gallery/serve.py --port 8765
```

页面底部的展开区记录真实绘制调用、提交三角形和进入交互前发起的下载。当前统计范围是单院原型。全城的 300 draw call、150 万三角形、集显 30 fps 和 8 MB 交互前下载预算仍需在后续规模化场景中验证。

## 实现与素材

- `renderer.mjs` 管理场景、双栏同步镜头、渲染通道和资源释放。
- `shaders.mjs` 实现平涂、反向外壳、深度／法线折边及稳定纸纹。边缘检测会筛除亚像素尺度的细小折线，缩放时应结合样张观察这一取舍。
- `bootstrap.mjs` 管理手机按需加载、海报回落、控件与资源统计。
- `assets/samples.json` 记录模型身份、样张参数、原始截图和输出摘要。四张样张来自本页的真实渲染，海报使用墨线实色 A 样张。
- 字体为项目专用文楷子集，原字体来源和 OFL 许可见 [字体说明](../../fonts/README.md) 与 [许可全文](../../fonts/OFL-LXGW-WenKai.txt)。

专用字体可使用已有子集工具重建。

```sh
python modeling-lab/gallery/subset_notebook_font.py /path/to/LXGWWenKai-Regular.ttf --pages prototypes/luoyang-m0/index.html --output prototypes/luoyang-m0/assets/notebook-m0.woff2 --stylesheet prototypes/luoyang-m0/style.css
```

方案依据为 `origin/reviews:plans/luoyang-redesign.md` v1.1，执行范围按制作人指定的独立 M0。当前院落为研究推测模型，建筑的史料等级与依据由内容交付绑定。
