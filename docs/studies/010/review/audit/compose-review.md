# 010 composer / static verifier independent review

2026-11-02. Static code review only. Neither `compose.py` nor `verify.py` was executed; no model asset was imported. The unfrozen `study-010/review/revised-preview/model-info.json` was read only as a provisional schema, not accepted as delivery evidence.

## Correct interpretation observed

- `config.depth=0.15` is the rail centre separation, not total object width. Composer uses `bounds_m` instead. Preview bounds span approximately 320 × 186 × 125.013 mm, so it avoids incorrectly labelling width 150 mm.
- Nominal slot width 8.6 mm and total lateral clearance 0.6 mm are separately labelled. Clearance is not called single-side clearance or manufacturing tolerance.
- Exploded view is expressly a static illustration; it does not claim arbitrary insertion order, continuous-path safety, engineering stability, load bearing or manufacturing certification.
- Native `<details>/<summary>` atlas, matching static image captions/data, native anchors and model downloads remain available without JS. This is structural inspection only, not a real no-JS browser test.
- The overview link is deliberately left for root integration and explicitly excluded from local link verification; no false local pass is claimed for it.

## Findings

### BIND-01 — medium: verifier does not bind all presented facts

`verify.py` only compares `facts[0].value` (part count), image-path format and source part count. It does not independently check thickness, slot width, total side clearance or world bounds. It also iterates whatever variants/views exist rather than requiring exactly three variants and three views. A metadata file with a variant removed or numeric display facts changed could therefore escape this check. Suggested repair: independently derive every fact from frozen source; require exact variant/view sets; compare static HTML-visible facts against the same intended source identity too. Merely checking that metadata agrees with composer code is not a substitute for original-record binding.

### BUILD-01 — medium: residual files survive a rebuild

`compose.py` creates/reuses `dist`, then copies current sources on top. `verify.py` checks model-stage files exist identically in dist/model, but does not reject extra files in dist/model. An obsolete model file or old review item could survive a repeated build and enter a later archive. Suggested repair: compose into a fresh isolated staging directory and swap only after checks, plus exact imported-model file-set comparison. Review/source public projection should use an explicit allowed-file set, rather than accidentally carrying internal progress files.

### WORD-01 — low: native bounds incorrectly described as export-derived

The atlas text says world bounds are calculated from export records. Current generator line 46 calculates from `ob.matrix_world @ v.co` in Blender, and line 48 writes that to `model-info.json`. That is native world-space mesh data, not a GLB extraction. Suggested wording: “由原生模型世界坐标记录计算；导出一致性另见报告”. This keeps native identity and GLB evidence distinct.

## Pending actual evidence

No frozen model means actual complete file links and numerical fixtures cannot be accepted yet. Required next checks include 320/390 px rendering, keyboard/no-JS, top-of-page primary task visibility, all static figure and download links, exact frozen file parity, and real network failure/retry. Existing mock JS tests are not a replacement for these browser checks. GPU and iPhone remain unverified.

## Follow-up code review, 05:08 UTC

- BUILD-01 residual-file issue closed at source level: composer clears only its generated dist before writing; verifier requires exact model source/target file sets. This has not yet been exercised against final assets.
- WORD-01 closed: atlas now correctly names native model world-coordinate records. Bottom-bound text defers to final 1.1.0 data instead of repeating unfrozen negative-z values.
- BIND-01 JSON portion closed: exact three variants/views and all four source-derived facts required.
- BIND-01 static HTML portion remains incomplete: verifier searches each label/value anywhere in the whole page. Swapping two variants' static fact blocks would still satisfy those presence checks. Recommended per-variant atlas identity (`data-static-variant`) and per-block extracted dt/dd comparison, also checking the initial live reader block. No build/import was run during this review.

## Follow-up code review, 05:10 UTC

BIND-01 static HTML portion closed at source level: composer marks fact blocks by variant; `FactBlocks` extracts each block's dt/dd pairs, requires exact initial-slot + atlas-slot/span/rise sequence, and compares each block with that variant's independently source-derived facts. Final frozen-asset execution remains pending and is not implied by this code review.
