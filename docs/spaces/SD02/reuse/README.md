# SD02 · 第二真实几何限定迁移实验

仅验证012 A保持不变、013 B替换013 A的一个实际组合；不是任意模型通用接口，不提供前端切换。

## 失败先于修订
B真实地台为X[2,18]、Z[-13,3]，旧A槽为X[3,17]、Z[-12,3.2]。直接把B放进A环境失败。实际导入旧环境三角并裁到三条B超界区域，得到46平方单位、11.5立方单位的正体积交叠。没有将失败二进制混入成品；失败条件与测量保存在`qa/reuse-failure-and-revision.json`。

## 同生成器修订
`../source/build-environment.py`现在读取JSON模型列表、平移与路径；并非复制一份B专用地景算法。`source/config.json`选择冻结B，按其真实地台重建浅槽，门轴世界X8.9；路线端为[8.9,3.0]。原件路线前端Z2.8与地台前缘3.0之间原有0.2留白保留，不能据此声称角色通行。

默认A在`a-regression/`用参数化后的同脚本重建。输出GLB SHA仍为`aed3d338b384dc91d52425d45660338e13b8b72673e9bbe051e51e25ed9d0039`，与A最终文件逐字节相同。A前端、最终模型与最终环境没有改写。

B环境1984三角，闭合/无退化/有向体积正，实际GLB重导入有向三角多集一致；浅槽内部域检查未见正体积交叠，界面接触按平面与范围记录。原件内部几何不在本实验重新认证范围。

## 镜头与图像
`qa/reuse-b-high.png`使用B真实包络做完整投影检查，最外包络NDC绝对值约0.9401；可见更宽院落、偏门和折回路线。
`qa/reuse-b-low.png`采用[8.9,1.45,5.8]→[8.9,1.1,-3]，近面四角最小距1.1577、Y12垂降107样本最小距1.2，大于0.15半径。仅有限样本与CPU静态证据，不是连续碰撞/GPU/移动端验收。
PNG无损移除文本metadata，IDAT不变；原生环境文件清理默认UI路径。

## 可复现命令
从`space-design-02/`运行，Blender 4.3.2：

```sh
blender -b --python reuse-test/source/inspect-b-input.py
blender -b --python source/build-environment.py -- --output-root reuse-test --config reuse-test/source/config.json
blender -b --python source/build-environment.py -- --output-root reuse-test/a-regression
blender -b --python source/check-reuse-b.py
blender -b --python source/render-environment-check.py -- --reuse-root reuse-test
python reuse-test/source/verify-clean-native.py
```

输入GLB均已附在各`dist/assets/`，不修改其字节；同生成器位于主包source目录。两套输出目录分离，不能拿B实验覆盖A前端。

## 原生输入与边界
`source/inputs-clean/courtyard-B.blend`是已清理013源包的精确原件，SHA `dda805c514d3baff87a0b149fa75f2dc0807be326d3ea83d092beacf81a14435`。来源成员/源包SHA/私有路径扫描见`qa/b-native-provenance.json`；B GLB SHA `696227e0223ac094135edeea839f4b6c9674f2bd0398f0a5a15f117e8d7692d5`。
只说明两个离散真实几何配置可以经重新计算迁移，不能证明连续参数全集、包含型任意复杂网格、引擎批量性能或历史实尺。
