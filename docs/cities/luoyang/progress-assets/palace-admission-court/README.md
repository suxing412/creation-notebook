# 无名宫院通行组合

约公元180年语境的未定位C级空间兼容试案。状态：已建模，未入城。历史宫名、门名、所属南宫/北宫及城市绝对坐标均为空。

本目录是公开模型交付目录，**不是完整原生与重建包**。

## 本目录实际提供的文件

- `palace-admission-court-open-LOD0.glb`、`palace-admission-court-open-LOD1.glb`、`palace-admission-court-open-LOD2.glb`：三档开放姿态，均为独立可打开的GLB。
- `palace-admission-court-closed-LOD0.glb`、`palace-admission-court-closed-LOD1.glb`、`palace-admission-court-closed-LOD2.glb`：三档闭门姿态。
- `source.json`：六份模型的来源标识、字节数与SHA、史料链接和未入城声明。
- `evidence.md`：文献支持、跨时代排除和推测边界。
- `qa/summary.json`、`qa/finite-routes.json`、`qa/route-interfaces.json`、`qa/independent-geometry-review.json`、`qa/independent-native-images.json`、`qa/clean-rebuild.json`：已完成检查的记录。

模型卡、封面和图集位于 `../../../../library/models/m-luoyang-palace-admission-court/`。详情页使用实际GLB，封面是模型渲染。

完整的三档Blender原生文件、源模块输入、配置、重建与检查脚本、纹理及渲染图另存于独立交付的 `luoyang-palace-admission-court-v1.zip`；**本目录不含该压缩包或上述原生/重建文件**。QA和source.json中的 `models/`、`native/`、`inputs/` 等路径记录原交付包内部的来源位置，不表示它们存在于此公开目录。这里不能直接执行完整重建。

## 新增范围

复用既有无名门卫切片、两侧廊庑和殿堂原型，新增实体庭地，将门内出口、侧向分流和殿前台阶接通。只计一组连接方案，不将复用的原件另计为新建筑。

新地面预留孔与原门卫地面对接，未叠铺重合顶面。殿堂来自既有德阳原型库，但来源名称不代表本组合的历史目的地。两侧廊入口保留各自真实台阶，不用视觉中心线代替阶口。

## 已完成的检查

- 六份实际GLB经独立解码，原件几何、UV、材质及嵌入纹理保持一致；未新增模块间穿插。
- 新地面闭合且绕序一致，门卫地面与庭地之间无顶面重叠或空缝。
- 每份模型检查99个有限通行区域、18,487个支承点、73条接口邻接；六份共110,922个支承点，没有支承失败。
- 闭门通路与真实殿柱的负对照检出预期阻挡，没有把闭门姿态报成可通行。
- 原交付包从独立目录重建六份GLB，字节哈希一致；原生文件打包纹理通过单独迁移后的重开检查。

## 限制与待解决

《后汉书·百官二》支持受控准入、夹道值守、宫中巡行和殿门宿卫，但不证明本组合连续路线、距离、门房数量或轴线。全部尺寸与布置为C级设计，没有借曹魏/北魏宫门中轴或魏晋东掖门形式为东汉定形。

本组合没有完整围墙，中央门扇只控制中央通口。检查只覆盖有限几何区域和分级台阶，不认证人体步态、无障碍、连续门扇扫掠、结构安全或GPU表现。尚未改动城景坐标；city-data.mjs不属于本批内容修改。
