# taixue-long-hall-v1

Research content archive only. Not integrated into the public website or city. Historical geometry remains speculative. GPU and phone unverified.

Reassemble source.zip.part001, part002, etc. in lexical order to source.zip, verify SHA256 in archive.json, then unzip. Each part is raw ZIP bytes, not a standalone ZIP. No model geometry or image pixels were reduced. Private transport IDs were removed from text metadata; source-to-projection hashes are recorded in manifest.json. Excluded historical/failed outputs remain in the privately retained original archive.

# 太学长堂类型 · C 独立研究

这是一座长堂与未指定制度用途的空前场，不是汉魏太学发掘平面的复原，也没有进入城市或修改网页。

## 来源与分期

参见 inputs/taixue-hall-precedents.json。钱国祥2022的长宽转述是文献比例启发，不是公元180年测量；异文/OCR线索未完成校勘。这里选6:1作C试验，不裁定原文。A36×6米/12开间，B42×7米/14开间全部是设计参数。屋顶、墙窗、三处台阶、门向与柱网均C。前场未放完整46碑，不等于断言180年完全没有石经。没有复制晚期校园、241年三体石经或现代课桌。

## 可复现

Blender4.3.2；无随机变量，seed0。先运行 source/validate.py，再用Blender运行source/build.py、source/revise.py、source/check.py、source/contacts.py。build生成首版，revise修后窗竖条顶部承接并增加室内视角。first-pass保留首版原生几何与图；最终native为修订版。自制土/木/瓦9张512²PBR复用自灵台质量源，不含外部图像。

两个几何样本不同长宽、高度及开间数，证明有限迁移；输入护栏只防明显非法参数，不代表护栏范围内全部建模/结构合格。

## 模型使用

局部原点在长堂中心地面，米制。Blender X东Y北Z上，glTF X东Y上Z南。A/B互斥，近LOD/LOD1互斥，不能叠加载。presentation_ground只是独立展示台面，未来试放需卸掉并核验实际地面；平台、柱础、阶梯不可随意删。未生成城市placement。

## 尚未通过的验收

不是承重/榫卯/消防/人流容量证明。有限柱础接点、后窗条承梁及站立净高仅检查代表构件；不能整对豁免所有木构和瓦间相交。分件闭合不等于整体布尔并集，板筒瓦组合包含搭接。近景仍缺已考据室内陈设、完整结构节点及精细屋脊，不标013品质全部完成。CPU渲染和GLB回读不等于GPU、移动端或完整游戏运行验收。
