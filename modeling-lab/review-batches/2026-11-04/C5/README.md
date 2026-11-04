# C5 cover refresh, 2026-11-04

Content-only candidate. No GitHub write or frontend change. Three self-made model families; not a new artwork count.

- Market: exact C2+C4 semantic batch candidate. Buildings and stalls remain in their original relative positions; no new geometry. Presentation hides sample ground, route and boundary batches only.
- Storage: exact C2 organized local group. Two warehouses, canopy and small items remain in original positions. Presentation hides sample ground only.
- Que 014: exact publicly fetched que-A.glb. Presentation hides the continuous terrain/tread only, keeping original chamfered plinth and main/sub shafts. No recovered .blend claimed; source of these covers is the actual GLB, preserved in inputs.

All recommended covers are 1200×900 (4:3), contain no text, and use true Blender Cycles CPU rendering, not generated illustration. Neutral warm paper background is for card presentation; materials are not repainted. Original camera trials and previous public cover images retained for comparison. No GPU/device/engine or archaeological acceptance claimed.

C5 status: market and storage framing candidates meet 60–70% using the alpha-threshold silhouette bounding-box area (not filled pixels). Que is deliberately kept at a readable three-quarter angle: narrow tall subject cannot fill 60–70% bbox area in 4:3 without a near-top-down angle or clipping. A higher-angle alternative achieves about61%, but was rejected as recommended cover because it flattens the tower. Que framing therefore remains PARTIAL for Claude review, not all-C5-closed.

Before-after sheet rows: market, storage, que. Left: previous public cover. Right: recommended candidate. The six images are correspondence evidence, not production cards.

No original GLB bytes are overwritten. After images omit optional display terrain only; models downloadable by users still contain all source geometry. Rendering is not proof of mesh, UV, history or collision correctness; those reports remain separate.

Source identity and camera: qa/render-final.json. Pixel framing: qa/occupancy.json. PNG compressed text removal preserves IDAT/RGBA: qa/png-sanitization.json. Original image SHA records retained; sanitized before images have identical pixels. Source and outputs checksummed in SHA256SUMS.json.


## 公开投影状态
014/que 推荐封面占框面积43.86%，状态 notaccepted；高角度备选不代表已接受。市肆/仓储61.92%仅满足该包定义的bbox构图指标，不代表整体C5完成。未达标014封面、高角度备选、旧首轮相机图及含014的比较图不公开；仅保留SHA与不通过原因。

解压 evidence-and-source.zip 到本目录保留目录结构。inputs内GLB逐字节不变；渲染脚本仅改为包内inputs相对路径，新旧SHA见projection-manifest.json，未用修订脚本重跑旧报告。qa保留历史源SHA，不能把它说成新的检查器结果。原PNG元数据已净化，像素保持；旧PNG SHA只指原件。本批未修改网页、主城或其他作品。
