# 太学 A v3.2：原生净化生成补充

## 核包结论

先前公开投影ZIP已经包含 qa/native-projection-equivalence.json、材质/活动场景核对、旧QA以及 source-to-projection.json，但没有包含生成原生UI历史投影的脚本。此小包补上该脚本与实际重现结果；原公开ZIP及其SHA保持不变。

本包不含模型副本，不重新修模，不导出GLB、不重编码PNG、不改变城市落位或网页。它只在新目录中从原v3.2 .blend生成省略UI历史的场景数据文件，再同原件和已公开原生文件逐项比较。

## 输入和环境

使用 Blender 4.3.2，后台CPU模式，2线程；不需要额外Python包或网络。脚本会拒绝其他版本与不匹配的ZIP。

输入1：luoyang-taixue-entry-repair-v3.2-source.zip
SHA256：0f4fdd0ceada1793da6c81d400a9f940a69ce42202bd4725c9cd7d92f1d88815

输入2：luoyang-taixue-A-v3.2-public-projection-v1.zip
SHA256：83556f30e8e88c56f8578b84afba00fe81d4c611cadb23acd30d7e3cbf4e671d

不把原件目录用作输出目录。输出目录须不存在或为空。脚本只从这两个固定ZIP读取三档模型，临时解包，生成到新输出目录；输入ZIP前后SHA必须保持一致。

## 运行

将下列路径占位符替换为你保存文件的位置，在本补充包根目录执行：

    blender -b -t 2 -P source/reproduce-native-projection.py -- --source-zip ORIGINAL_ZIP --projection-zip PUBLIC_ZIP --output-dir NEW_EMPTY_OUTPUT_DIRECTORY

成功后会生成：
- models/taixue-A-LOD0.blend
- models/taixue-A-LOD1.blend
- models/taixue-A-LOD2.blend
- reproduction-result.json

成功标记为 TAIXUE_NATIVE_REPRODUCTION_PASS 3。不能仅看进程退出码：Blender遇到Python异常有时仍返回0，应检查结果文件status=pass、三档记录齐全且输入SHA不变。遇到不同输入、意外外链或无打包贴图会停止，不会宽泛删除数据求通过。

## 具体操作和验证

1. 打开原始场景，不改顶点、拓扑、UV、矩阵、材质或图像像素。
2. 仅将打包图片的路径规范为内部相对路径，将渲染输出设为相对文件名。
3. 使用 bpy.data.libraries.write，仅写场景及其数据依赖，不写屏幕、工作区、窗口管理器或文件浏览器历史。原文件不另存覆盖。
4. 重新打开生成文件，逐项比较几何/拓扑/UV/矩阵、材质槽、材质节点和连线输入值、打包图像字节，同时对比原件和先前已公开的原生文件。
5. 验证当前活动场景实际包含4/4/3个可见网格，扫描输出文件是否残留环境绝对路径。

场景数据型 .blend 打开时可能出现通用的“Library file, loading empty scene”提示；打包贴图的外部路径不存在也可能提示保留packed image。本检查不凭这些提示判断成功，而是实际验证活动场景网格可见、材质连接及打包图像字节一致。检查结果中任一项失败都不能称完成。

## 实测结果与字节边界

已用本包脚本从两个固定ZIP完整重跑，三档生成及重开对比均通过，见 qa/reproduction-result.json。原件与先前公开ZIP未改。

**这不是逐字节重现Blender文件的承诺。** Blender原生文件在不同保存进程中可能有不同二进制SHA；报告同时列原件SHA、已公开SHA和本次生成SHA。声明的可重现对象是经过逐项核对的几何、UV、矩阵、材质图和打包图像内容。不能把新的blend SHA写成旧的已公开SHA。

旧QA到公开SHA的关系由 qa/source-qa-public-sha-ledger.json 明示：GLB没有改字节，旧入口报告的GLB SHA仍对应公开模型；旧非踏步报告只是历史修复证据，不能单独证明UI投影。原生等价桥接及本次实际重现另行证明原件与公开原生内容一致。

本补充不替代入口有限体积检查，不覆盖B方案、历史考据真实性、结构承载、全城或动态门扇。
