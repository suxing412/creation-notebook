# F03 检查记录

检查日期：2026-11-01 UTC。版本 0.2.0 / seed 0。

## 已通过的实际资产检查

- 005 Poise 原始 GLB SHA256：`53aef1b5fc4ef9d70bef6dae9562d393c80c93016d46bba2b41b67f97cd1a078`
- 006 Folio 原始 GLB SHA256：`2f036da9f9170535d4bd07c0a7b964df22655991a7eb4b54e9c2b4d0f93c6d83`
- 与冻结来源逐字节相同。原件材质的完整 glTF PBR/发光 payload 在组合 GLB 中逐项保持。
- 真正以 Three.js r180 GLTFLoader 解析：Poise 8 mesh / 40,256 triangles；Folio 1 mesh / 12,044 triangles。不是占位物件。
- 两物件底部与桌面 y=0 接触，数值误差小于 1e-5 m；全部包围盒在圆角边缘之外的有效桌面内。两者 X 方向包围盒间距 0.3190708729 m，不相交。
- 真实组合 GLB 双向最近世界顶点误差：Poise 0，Folio 3.332000986e-8 m，小于 5e-6 m 容差。源与组合顶点数分别记录，不声称拓扑索引一致。
- 真实 `.blend` 经 Blender 4.3.2 重开；保存帧 1/31/61 三相机位置、朝向、纵向 FOV 39.6° 与共享配置相符。CPU 离线图来自这些相机，不是 SVG 示意或参考照片。
- 9 条有向相机路线各采样 101 点：坐标有限、相机不穿入两个原件包围盒、距离大于安全阈值。数值采样不等于连续 GPU 动画验收。
- 自写投影与 Three.Vector3.project 一致；Blender 世界点投影与同一配置吻合。三章各自热点可见；概览全部热点可见。
- 268 / 330 / 655 CSS px 场景宽度下全景热点中心间距大于 44 px；真实模型 CPU Raycaster 有命中；真实 GPU 点击行为仍未验。
- 五项故障配置被拒绝：重复章节 ID、改变源模型尺度、非法 FOV、非有限位置、负 near。

## 原生云浏览器已观察

- 初始静态全景、完整三章、目录与场景编号均可读。
- 首版→修订首屏：最终桌面与主要入口同屏；DOM 视口 1188×761，stage y257–694，目录 y168–237，3D 按钮 y648–682；无横向溢出。
- 直接 `#fold`：对应图、标题、唯一可见折页热点与正文焦点一致。
- 原生链接 Enter、跳过空间 `#reading`、Back 恢复已检查；`light → reading → fold → Back` 恢复 reading 对应的 light 场景。
- 实际点击启用 3D 后，WebGL 创建因环境 GL Disabled 失败。失败提示、重试入口、离线图与后续章节导航仍可用；未修改浏览器设置。
- 390 / 320 CSS px 原生 iframe：文档无横向溢出，场景比例约 1.5。仅为布局检查，不是 iPhone 真机、触控或性能测试。
- sandbox 禁止 JavaScript 的 390 px 原生 iframe：三章正文存在；3D 控件隐藏；点击折页原生目录后 hash=`#fold`、焦点为 fold、正文进入视区。

## 独立复检

- 真实 app.js 的 Node VM 状态机回归：乱序解码、坏图不改标签、GL故障不取消挂起章节、reading状态恢复、旧parse取消后重新启用、主动离线均通过。DOM/renderer为stub，不代表GPU或浏览器渲染验证。
- 独立跨引擎检查：三相机×三热点，Blender 与 Three 的最大 UV 误差约2.88e-7。2,775条CPU光线中，851条首先击中桌面的光线没有触发物件导航，原件命中未出现错误章节。
- 独立原生浏览器再测：light→reading→fold→Back→Forward 恢复图、标签与焦点；320/390布局无溢出，44×44热点不重叠。发现窄屏圆盘遮物后，最终将可见圆片缩为19×19并移除halo，透明44×44目标保留。

## 最终原生限定验收

再次独立核对桌面首屏、空间热点02的Enter、light→reading→fold→Back、真实禁GL失败保底、320/390布局与无JS原生fold定位，均在上述限定范围通过。原生noJS图宽1440、加载完整，fold正文顶部约56.05 CSS px。详细结果见 [最终原生验收](final-native-browser.json)。

## 不包含在通过结论内

真实 GPU 材质/阴影/色彩对照、动态闪烁/深度冲突、真实 WebGL 对象点击、触屏手势、真实 iPhone 性能、物理照度、承重或制造可行性均未验。CPU 反投影、离线图和模拟状态机不能替代这些项目。

## 机器可读证据

- [空间与源资产检查](spatial-tests.json)
- [真实场景重开检查](scene-tests.json)
- [元数据清理](../assets/metadata-cleanup.json)
- [来源登记](../assets/asset-registry.json)
- [打包检查](package-tests.json)
- [独立状态回归](independent-state-after.json)
- [独立跨引擎与光线检查](independent-geometry.json)
- [独立原生历史记录](independent-browser-history.json)

公开包不包含私有路径、外部参考截图、原始浏览器日志或故障二进制。正式打包前再次扫描。
