# C7/C8 · 单位、边界与门楼对账 v1

基线：main a63af753e2fa71793a5d4a4ac4ae4a2d99ce437e，2026-11-04 UTC。
此包是数据候选，未修改仓库、网页、模型、场景缩放或发布状态。

## C7
- notebook-index 当前20个模型家族、78个GLB下载项；registry是其中6家族37项子集。
- 78项逐一绑定最新tree中的Git blob；39项取得相同blob原字节，计算默认场景、完整节点变换后的实际有向三角顶点包围盒。另39项没有原字节，AABB未知，不用JSON accessor min/max猜。
- 001–004此次未取得精确源二进制，其边界未知；没有擅自缩小。
- `unit: meter`仅记录glTF坐标规范，不证明制作者意图、考古真实尺寸或与现实1:1。设计示意米不能当历史实测米。
- 20家族全部 `intendedRealSize: null`，状态“用户未指定”。既有18×24地块等源设计尺寸也不能自动填成用户指定真实尺寸。
- metadata-candidate.json是78份文件的审计记录；codex-metadata-json-patches.json提供两份现有数据文件的RFC6902候选操作，不含前端布局变更。接入前必须核新HEAD和原ID/文件，不可直接套过期快照。
- 静态三角AABB不包含未引用网格，不是门扇运动包络、碰撞/导航净空、骨骼/形变范围或历史测绘。

## C8
5个下载项都是不同SHA256、不同字节文件，不存在逐字节完全相同的一对。准确对应：
1. docs/model-library/assets/gate-roof.glb ↔ docs/model-library/assets/gate-near-local.glb
2. docs/model-library/assets/gate-original.glb ↔ docs/model-library/assets/gate-far-local.glb
两组local文件各增加64字节；二进制BIN区完全相同，场景变换后世界有向三角多重集完全相同。区别是局部原点契约的identity根包装；不应说它们完全同文件。middle是第三种不同几何。
最小对账见gate-five-download-reconciliation.json，包含5项SHA/字节/路径、10对全比较。建议可在UI区分“历史原件”和“契约包装版”，由前端负责人决定，源件全部保留，本次不删除任何文件。

## 重跑
source/audit.py 是本次生成脚本，需恢复相同SHA原资产后运行；不在此小审计包再次复制数十MB源资产。readglb.py为实际三角读取器；不支持稀疏accessor/压缩几何/动画蒙皮的通用验收，仅适用于本次成功读取的39份资产。每条来源与SHA都在审计JSON中，缺源明确unavailable。


## 公开投影
本包保留39份已核原二进制的历史测量记录及39份未知项，不重新测量或缩放。GLB原件不重复打包。取用确切源文件时，使用metadata-candidate.json中的baseCommit与repoPath构造https://raw.githubusercontent.com/suxing412/creation-notebook/{baseCommit}/{repoPath}，先核gitBlobSHA；已取得原字节的项另核sha256。无sha256的未知项不得填充AABB。

解压ZIP可查看快照和读取器及patch生成器；完整audit.py依赖未打包的取件清单，未随包发布，本投影不宣称能直接重跑完整旧审计。旧SHA及旧测量结论保持来源含义，没有改写成新检查器验收。所有真实尺寸仍未指定；meter和AABB不能推导物理真实尺寸或应缩放比例。
