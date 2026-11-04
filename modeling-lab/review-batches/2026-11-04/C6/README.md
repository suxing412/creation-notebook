# C6 · 形体习作评审标签候选

基于main a63af753e2fa71793a5d4a4ac4ae4a2d99ce437e，2026-11-04 UTC。
按评审意见为002潮翼、006折页、007回环、008透幕、010栖格添加“形体习作”标签。此为审美/用途分类意见，不代表技术、历史真实性或功能验收结论。

## 最小改动
仅新增reviewClassification对象：label=形体习作、basis=review_opinion、reviewId=C6、notHistoricalOrTechnicalCertification=true。
不更改catalog.kind=regular；这是既有validator枚举，不能替换为“形体习作”。notebook-index.kind=器物与雕塑亦保留。
模型字节、名称、描述、链接、版本、验收和发布状态、数量均保持不变。不删除、不改模型风格、不制作网页。

## Codex接入
codex-label-patch.json分别提供catalog.json和notebook-index.json的RFC6902候选patch；每项先test原ID及准确标题，再add元数据。
接入前读取最新HEAD，按ID重新定位。若数组位置变化，不能盲目应用旧下标。附candidate JSON仅作审阅，不建议整文件覆盖最新前端提交。
由前端负责人决定是否用现有标签/描述位置展示reviewClassification.label；当前未知字段可能不显示。数据准备完成不等于网页已显示。
不把“形体习作”写进designStatus以覆盖验收含义。

## 验证
10个跨文件ID映射逐项核验，移除新增字段后的结构与原快照完全相同。原catalog和候选catalog均通过从该提交读取的真实catalog-contract.js验证器。notebook-index没有找到正式schema，本包仅声明结构/字段类型/引用不变检查，不假称正式schema验证。
qa保存映射和验证结果，source保存可复现脚本及原validator。


## 公开投影
候选patch尚未应用，不能整文件覆盖最新数据。evidence-and-source.zip包含快照、历史QA及生成脚本。验证器以catalog-contract.mjs.txt保存，仅作源契约档案，需自行恢复后缀方可调用。原校验结论未重新运行，checker身份不变；本包无前端文件。
