# lingtai-quality-v1

Research content archive only. Not integrated into the public website or city. Historical geometry remains speculative. GPU and phone unverified.

Reassemble source.zip.part001, part002, etc. in lexical order to source.zip, verify SHA256 in archive.json, then unzip. Each part is raw ZIP bytes, not a standalone ZIP. No model geometry or image pixels were reduced. Private transport IDs were removed from text metadata; source-to-projection hashes are recorded in manifest.json. Excluded historical/failed outputs remain in the privately retained original archive.

# 灵台类型 C：北殿瓦作与到达空间修订

这是独立研究资产，不是约180年灵台精确复原；未入城，未公开，网页未改。旧A/B仍保存在前一完整源包，本包只修A并含原A GLB输入。固定同一全景镜头、光照和CPU设置对照before-whole与whole。

## 采用与不采用
钱国祥2022支持方形高台、周边殿廊及外围院墙的类型关系；并非本模型尺寸实测。外部优秀作品只用于主次体量、地面过渡、材质层级，拒绝照搬游戏砖城墙、豪华楼阁。013围院只作视觉组织参照，不能成为礼制建筑的历史样板。台顶没有足够证据，此版不加殿堂或仪器。

北殿由同质细廊改为较深、后侧围护且正面开放的C殿堂；这个具体用途/尺度/围护均为设计假设。仅北殿增加浅槽板瓦与弧背筒瓦、坡向搭接，其余廊保持旧样；南入口用真实分区地面呈现到达路径，不叠贴片。瓦形依据为关联区域汉魏材料，瓦距、曲率、厚度、搭接长度和屋脊均C试验值。

## 重现与预算
Blender 4.3.2；运行 source/build.py 后 source/verify.py 与 source/contacts.py。确定性生成，无随机采样/随机种子。素材均自制PBR，10张512²内嵌图；外部参考原图未收录。近层380236三角，LOD1仅移除北殿详细瓦壳后21332三角。两层互斥，不应同时加载。按RGBA8估算10MiB无mip、约13.33MiB含完整mip，这不是实际GPU显存。近瓦只有近镜头可读，公里尺度不应加载。

## 检验与不足
实际GLB与原生有向三角5位小数一致，详细结果见qa。原生瓦批是5278个各自闭合壳，接触组件并非单一水密屋顶；按世界位置焊接后出现3248非二邻边，不能声称整体流形或碰撞已验。坡向接触只作参数截面有限采样，非完整穿模零风险证明。新地面单元实际布尔交叠与两根椽的实际支承接触单列。云端只能CPU图，GPU实时、闪烁、手机未验。

当前不足：北殿整体仍过于整齐、木构节点与屋脊简化，局部详细瓦与其余廊细节落差明显；台顶与周边活动关系尚未知。新瓦大幅提高成本，不能无选择地全城应用。真实加载性能、参数范围全集、结构承载与雨水排放均未验证。下一阶段应在独立库登记并审查与既有城市尺度/关系的适用性，不能因美图即直接放城。
