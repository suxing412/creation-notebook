# 两院PBR材质尺度研究

状态：独立C设计材质研究，未发布、非历史色彩复原、未用户验收。仅C02-006(B2)、C02-010(A2)，不增加院数/作品计数，不移动院落，不修改任何原建筑顶点/三角。

## 材质与复现
使用作者程序自制随机噪声生成土墙、木材、灰瓦三类PBR贴图，seed18054；没有外部照片、模型贴图或AI图像。每类512×512的basecolor、normal、ORM各一张，共9张。basecolor以sRGB存储，normal/ORM按非颜色数据，G粗糙度/B金属度0，法线为切线空间。没有用Blender专属程序节点冒充GLB材质。
土墙纹理试验重复尺度2×2m，木纹2×0.5m，瓦面0.8×0.8m。UV按面主投影；木构先识别连通构件最长轴，使侧面纹理沿构件长向。端面没有专门年轮，投影转角有接缝，是明确失效边界。颜色、矿物颗粒、木纹强度、瓦粗糙度都是C美术假设，不是180年洛阳实物测色。

## 修订
首版纹理较弱，32samples近景噪声盖住细节，保留first-pass图和旧生成脚本。第二轮适度提高低频与微表面层次并靠近机位；尝试64samples降噪失败，当前Blender无OpenImageDenoise，未安装或绕过。最终采用CPU128samples、无降噪，前后均相同灯光、机位、曝光与采样，近中远三尺度。

## GLB与几何验收
原建筑几何哈希前后相同。最终GLB实际JSON与BIN中验证3材质各绑定baseColor/metallicRoughness/normal，9图内嵌512²，UV存在。实际导回GLB，逐有向三角距离匹配原生模型；另做导回GLB同近机位CPU渲染。具体数值见qa/glb-material-check.json、export-check.json。
这些证明可传递PBR数据与CPU导回结果，不等于Three.js GPU外观一致、手机或动态闪烁验收。没有实际WebGL帧率/显存测量。模型几何不变，沿用原几何范围，不能据材质研究宣称额外碰撞路径通过。

## 纹理预算
9张RGB8的基础解码预算6.75MiB，含完整mip理论9MiB；若引擎展开RGBA8则含mip约12MiB，另有引擎/绑定开销。两院共享同3材质9图，不按院子重复制作。GLB实际压缩体积另记录；未来实例化仍需验证真实引擎资源共享，不能将理论预算称实测。

## 首版后参考
2026-11-03读取Khronos glTF2.0原始规范 https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html ：采用核心metallic-roughness及normalTexture传递，按规范分开颜色与线性数据。规范支持数据格式，不保证不同光照/色彩管理的渲染像素相同。原作者Adam Sharp模块场景页 https://nads.artstation.com/projects/qJe9bL 的材质/光照分开对比方法沿用，但未复制其纹理、UE5能力或欧洲建筑细节。其艺术展示不是汉代证据。

## 文件与适用边界
native/two-yard-pbr.blend内嵌贴图，可编辑；assets/two-yard-pbr.glb仅两院建筑，不含整个城市/地表。source/build.py重跑依赖旁边luoyang-south14-composition完整原件（其独立源包已保留）；make-textures.py无需外部输入。统一地表作为渲染背景留在blend中，未混入GLB建筑。
仅验证两个原型、有限材质尺度/机位；未验证所有房型、任意旋转、细长构件端面、不同曝光环境、真实GPU色彩和纹理采样。下一步要看实际画面是否提升；若只是综合色变化，应继续改善材质分层而不是宣称细节完成。

## 最终CPU图评审
在实际近景，土墙不再纯色大平面，门楣木纹方向与土墙颗粒有区分，瓦面呈低频矿物色差；中景改善较弱，远景不应显著花斑。仍缺木端面年轮与真实接榫，瓦本体仍是原简化瓦条，不能靠贴图声称构造精度提高。墙面平铺重复与转角接缝需继续对不同原型检查；当前只证实两院有限迁移。

原生保存时发现Blender packed_files仍留绝对纹理路径，已逐项改成相对路径，打包图像SHA保持不变。清理报告见qa/native-image-path-cleanup.json；重新制作亦需运行sanitize-native.py后package.py。
