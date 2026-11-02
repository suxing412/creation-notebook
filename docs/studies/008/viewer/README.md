# VEIL / 透幕 — 独立观察页

入口：`viewer/index.html`。从项目根目录的静态 HTTP 服务打开；无需后端、CDN、字体服务或其它 API。不要通过 `file://` 判断 ES modules / fetch 是否可用。无 JavaScript 时，HTML 中直接保留三组正文、真实图片链接与模型下载。两个“制作与复现”链接直接指向模型包中的 `../README.md`，不依赖另行交付的主网页。

## 数据边界

- `../assets/{veil,horizon,fold}/` 是唯一模型来源；从实际 `model.glb` 读取，不程序化绘制替代物。
- `model-info.json` 用于身份、米制尺寸、真实材质与摄影机记录，不作为下载 URL 或文件包装状态的来源。
- `delivery-links.js` 是下载 URL / 标签 / 文件名的独立配置。源码默认下载原始 `model.blend`。
- 若发布层改用 `.blend.gz` 等交付包装，**只编辑下载配置**，随后运行 `node viewer/sync-delivery.mjs`，同步 HTML 的 16 个无 JS 文件入口。不得全局替换模型记录、修改三角数据或用异步元数据更新下载身份。
- `routes.js` 统一 `?variant=veil|horizon|fold&view=beauty|front|side|top|rear|hole-detail` 深链接；`camera.js` 只做一次 `(x,y,z) → (x,z,-y)` 坐标转换。实时相机读各组实际 `studio.views`，不归一化模型尺寸。

## 生命周期与保底

`state.js` 将图片 route epoch 与 GLB session epoch 分离。图片成功 `decode()` 后，图片节点、正文、标题、视角、下载身份和 URL 在同一个同步提交内更新。失败图不覆盖当前图片，不贴新标签。实际 viewer 在图片等待期间继续允许取消；图片提交处再次失效化 3D，防止等待期间新启用的旧模型污染新路由。

取消、主动回静态、context loss、重复启用、旧 parse 晚到分别处理；旧结果只释放自己的资源。页面离开主动停止 GPU；Back/Forward 图片失败时，URL 回到保留的正确内容。晚到 metadata 更新有 route/variant 双重检查。

## 本地校验

从 `study-008/` 执行：

```sh
node source/test_viewer_state.mjs
node --experimental-vm-modules source/test_viewer_state_dom.mjs
node source/test_three_loader.mjs
```

报告分别写入 `review/viewer-state-tests.json`、`review/viewer-dom-state-tests.json`、`review/viewer-three-loader-tests.json`。报告运行前清除，结束时绑定相关源码 SHA。GLB loader 报告还绑定三组实际 GLB / model-info SHA；资产变化后必须重跑，不能沿用候选通过。

第一组：实际控制器与纯函数的延迟 Promise / 路由 / 下载 / 坐标测试。第二组：实际 viewer 模块在 Node VM 的小型 DOM 模拟中执行（不是原生浏览器）。第三组：实际本地 Three r180 GLTFLoader 读取最终资产，并检查包围尺寸、三角数、PBR 和 CPU 相机目标投影。

**上述通过均不代表 GPU、真实手机、触控、动态闪烁、制造或结构性能通过。** 原生浏览器版面 / no-JS / 深链接 / 无 GL 保底如执行，应另在 `review/viewer-*` 记录环境和范围。预览仅使用父任务提供的单一 sites-preview 窗口，不启动第二个服务或浏览器。
