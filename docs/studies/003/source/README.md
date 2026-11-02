# UMBRA / 玄瞳 — Study 003

原创八叶概念光阑：Blender 可编辑模型、独立叶片 GLB、Three.js 原型，以及离线三状态与结构图。设计单位不是毫米；刻度只是视觉方向标，不是 f 值或光学标定。

## 复现

使用 Blender 4.3.2、Python 3（Pillow、NumPy 用于投影检测和图版）：

```sh
blender -b -t 8 --python source/generate.py
blender -b -t 2 --python source/check_geometry.py
blender -b -t 2 --python source/check_coplanar.py -- dist/assets/iris.blend evidence/coplanar-after.json
blender -b -t 2 --python source/check_projection.py
python source/analyze_projection.py
python source/make_contact_sheet.py
python -m http.server 8080 --directory dist
```

所有脚本从自身位置计算工程根目录；应保留 `source/`、`dist/`、`evidence/` 结构。`IRIS_MODEL_ONLY=1` 只生成模型，不渲染。CPU Cycles 128 samples，无降噪；图片仍有细微噪声。Three.js r180 与 addons 已本地保存，无 CDN、远程贴图、字体或外部模型依赖。

`Pivot_00`…`Pivot_07` 是固定位置的旋转父节点，`Blade_00`…`Blade_07` 是其子网格。网页转角 `u` 对应 Blender 角度 `i×45° + 55° − u`。导出后的本地转轴为 `[0,-1,0]`，默认 `u=27.5°`；网页保存默认 quaternion 后右乘增量，不能直接覆盖各片方位。

## 交付边界

这不是完整机械设计：8 片叶片独立转动，没有驱动环、滑槽与联动杆；不是快门，不完全闭孔，没有 f-stop 校准、衍射、光线传输或制造验证。分层通过设计间隙解决实体相交，但不等同于薄片交错机构的真实装配。

当前实际验证了 Blender 几何、离线渲染、GLB 结构和前端语法/静态图切换。当前验证环境无法创建 WebGL 上下文，因此未完成真实实时闪烁、移动设备帧率或 GPU 渲染验收；页面必须显示明确的离线预渲染降级。

第三方参考只作研究，不复制网格、不把其产品图放入网站。Three.js 的许可证保留在 `dist/vendor/THREE-LICENSE`。


## 本站源码下载布局

源码位于本页同目录；展示用最终文件位于上级 `assets/`。复现时将脚本放入独立工程的 `source/`，运行生成脚本会新建 `dist/assets/` 与 `evidence/`；不要把生成输出误认为本站已经发布的文件。先生成模型，再运行检查脚本。公开检查记录见[几何检查](../assets/QA.md)，失败版本与对标见[制作复盘](../assets/REVIEW.md)。
