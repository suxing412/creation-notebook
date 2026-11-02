# 首版之后的官方研究 · 2026-11-01

时间顺序：先完成原创首版 `.blend/.glb` 与实际主图/接点图，再查下列官方来源。没有把参考模型或图片导入 Vesper。

## 实际查阅

1. [Louis Poulsen · PH 5 / Poul Henningsen](https://www.louispoulsen.com/en/c/indoor-lighting/pendants/90293?v=90293-5741113044-01)。已读官方产品页文字：多层罩引导下向/侧向光，下方使用磨砂扩散玻璃，材料分别承担遮光、反射和扩散角色。官方的防眩声明是其产品声明，不能移植为 Vesper 性能。
2. [Flos · Bellhop Glass Suspension / Edward Barber and Jay Osgerby](https://professional.flos.com/en-US/us/subfamily/decorative-suspension-bellhop-glass-suspension/)。已读官方文字，其三层乳白玻璃扩散罩把材料分工放在设计中心。

官方图片链接曾尝试获取：Flos 图片返回 cache miss，Louis Poulsen 图片链接未得到可供本轮可靠像素审阅的显示。**不声称实见其原图细节、装配或底层拓扑**；没有将外部图片收进资产。旧 PH5 产品路径 404 后使用官网当前 canonical 页面读取；官方 PDF 转向失败，没有冒称读过 PDF 全文。

## 从方法到自己的可验证决定（推断，不是厂家事实）

- 推断：视觉分层应来自真正的间距与材质分工，不应只靠颜色线画出“接缝”。因此 Vesper 的透光体径比从 .91 收至 .86，罩缘参考垂直偏置从 10 mm 加至 16 mm；重新检查罩/透光体不接触。
- 推断：轻量灯罩需要解释支撑路径。Vesper 保留自身偏心软罩 + 弯柱比例，用 3 根小定位销将环形透光体接到中央套筒；不是复制 PH 的多层罩或 Bellhop 的外轮廓。
- 推断：软罩与暴露套筒的语言应协调。套筒以真实圆角截面代替直筒硬口，不靠法线把几何边角掩盖。

## 可说与不可说

可说：本轮实际看了自己的 Blender 多视图，官方文字研究影响了对“间距/连接/材料分工”的评审问题。
不可说：Vesper 已达到这些品牌的光学、防眩、稳定性或制造质量；已检查官方模型拓扑；官方原图证实了我们的连接细节。
