# 当前城市47块：小型JSON接入候选

本包只交数据，不修改网页，不创建公开URL，不自动加载。内容GLB来自已交city-visible-web-handoff-v1-public，仍依赖其47块文件。原城市母版SHA为1e8c4d2ce19827bb8ab5ff24a662fd4f3909aa5c6074fc9a90623a103b73b01b。

## 固定接口

按父任务指定aeeff013版本，实际只读city-renderer.mjs的SHA固定为de31a317bf8c687b6edeaf105f54fac7494babe89aa6f5eb1d242b2010b9b36c，city-data.mjs SHA在adapter.json。检查了loadAsset使用asset.url、transformFor使用node.matrix、initial=false不首屏载入、tier=C按推测显示等接口。版本变动后应重新适配。

adapter.json提供47个assets与47个nodes一对一记录，全部tier=C、initial=false。GLB本身已保留世界变换，因此外层16元素列主序matrix为identity。bounds为实际反读每块worldbbox，从原Zup转换成glTF Yup：[x,y,z]→[x,z,-y]；min/max的负y端点正确交换。不要重复套原源矩阵、旋转或居中。

assets只提供relativePath，例如chunks/某块.glb。它是内容包根目录内路径，不是公开URL。网页侧先选择并验证公开前缀，再构建runtime asset.url = new URL(relativePath, publicPrefixEndingSlash).href。当前renderer不能直接消费缺少url的候选assets，这一步尚未实施。没有虚构nearUrl或全城LOD。

## 分组与互斥

35个groups明确列nodeIds，分组是交付组织而非历史城区确认。layer替代清单从固定city-data.mjs实际读取64个旧城市nodeIDs；researchModels另列保留，不并入64旧城集合。

网页侧必须实现新旧整层互斥和旧异步请求取消，避免47新块与64旧城市节点叠载；完整基准GLB也不得同时加载。这里的layer/atomicGroups是声明，renderer没有原生整组取消接口，本包没有假称已实现。原renderer的逐节点replaces机制不等于事务式整层切换。

两瓦原子组分别3片、4片，node记录sourceNodeId、fragmentIndex/count及primitive triangleRange。网页侧应全部片到齐后整组激活；失败时不保留残片，取消/卸载同组处理。单片不保证闭合，不得作为不同建筑。也不要因所有节点initial=false而误认为替代已完成。

qa/validation.json核47资源和节点双射、35组、64旧节点、两原子组、全C/关闭/identity与实际坐标换算。所有资源SHA/大小按已交内容实际文件复核。本包无部署、GPU、历史完成度或全城统一质量结论。
