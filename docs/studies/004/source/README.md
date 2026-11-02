# LIMEN / 岬界 — Study 004

原创海岸观测所建筑习作。Blender 4.3.2 + Three.js r180。

## 生成与检查

```sh
blender -b -t 8 --python source/generate.py
blender -b --python source/check_geometry.py -- dist/assets/limen.blend geometry-check.json
blender -b --python source/check_circulation.py -- dist/assets/limen.blend circulation-check.json
blender -b --python source/check_risers.py -- dist/assets/limen.blend riser-check.json
python source/check_glb.py
```

`STUDY_MODEL_ONLY=1` 仅生成 Blender / GLB；`STUDY_VIEWS=beauty,front` 限定渲染视角。未使用 OpenImageDenoise，因为当前 Blender 构建不支持它。

`dist/` 可放静态网页主机；Three.js 及插件均本地随附。通过 HTTP(S) 打开，不要直接使用 `file://` 加载 GLB。网页静态回退展示真实离线图，明确禁用不可用的实时按钮。顶部总览链接假设作品位于 `studies/004/`，集成到其他位置时调整即可。

构件按功能命名，名义米制仅为比例一致，不是建筑合规或制造精度。详见上级 assets/ 中的 QA.md、REVIEW.md，以及本目录 REFERENCE-NOTES.md。发布副本不含第三方参考图片、临时日志、用户文件或私有路径。


## 下载与复现目录

本目录提供生成和检查脚本；已发布结果位于上级 assets/。复现时请在独立工程中保留 source/ 与 dist/assets/、evidence/ 的原始布局，先运行生成脚本，不要在发布文件夹原地覆盖。
