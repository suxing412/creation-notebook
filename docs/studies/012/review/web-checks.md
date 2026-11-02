# 012 网页检查（工作稿，未最终冻结）
- node --check app.js：通过。
- state-tests.cjs：加载、异步前不改图文、失败保留旧组、重试、乱序竞态、popstate、章节历史恢复均通过。
- 云浏览器：B俯视与参数同步；C背视深链后Enter选A，最终A背视+4.2×3.2×4.6一致。
- 图片404真实测试：临时移走页面自己的C-rear，C背视深链显示失败、保留A前视及A参数。恢复图片后preview自动reload恢复；手动重试流程由state-tests验证（自动reload使按钮消失，不能称浏览器手动重试通过）。
- 390px真实iframe viewport：首版图太靠后；改为标题→模型图→说明并目视复检，无首屏横向溢出。不是手机硬件测试。
- noJS：HTML静态内容保留A图、全三参数及三俯视；另建移除script的QA页进行浏览器检查。未改浏览器全局JS设置。
- 无WebGL路径，不需求改安全设置；实时3D、GPU、引擎/LOD未测。
- QA-only页面仅测试，不纳入最终dist；浏览器截图仅内部不纳Library。
- 未冻结的rear混入旧白盒已报告并阻止发布；最终必须验证模型owner export-contract九图与数据哈希，重新目视。

## 按需观察器追加
- viewer.html 独立入口；主图录不导入Three，不请求GLB。viewer开始前canvas=0，点击才导入r180本地模块。
- 3份GLB的SHA与012-model-v1-frozen合同逐项匹配。
- 实际Three r180 GLTFLoader CPU parse成功：A 200网格/9272三角；B 248/11768；C 201/9284，见three-parse.json。此项不是GPU渲染。
- 云浏览器实际启动返回GL_VENDOR/GL_RENDERER=Disabled；0残留canvas、静态图仍可见，明确显示无法创建WebGL上下文。没有改安全flags。
- viewer-state-tests.cjs以mock渲染setup验证按需启动、失败保旧、取消旧响应、切换dispose旧对象、关闭observer/controls/renderer；未以mock证明Orbit/GPU。
- 真实GPU场景切换、Orbit手势/距离限制、动态闪烁、手机均未验，页面保留边界。

## 最终资产复检
- 012-model-v1-frozen 与012-images-v1-frozen关联核验，17图+3GLB逐SHA一致；build.py中设断言，禁止悄悄复制未冻结图。
- 9主视图均同版几何，顶视留完整地台；C构图更宽，页面不声称统一缩放。
- 桌面1165px与390px iframe首屏实际截图复检；截图仅/tmp内部，不入交付包。
- 最终C/top深链对应C图与3.6×4×5墙高参数；浏览器键盘B切换复核。
