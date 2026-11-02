# Independent pose workbench audit

Scope: read-only review of `app.js`, `pose-state.js`, and composition mapping. All checks run in Node, using the existing mocked DOM/network/image harness where relevant. No browser, server, GPU, user computer, Codex task, or authored source modifications. These results are not native-browser or rendering validation.

## Findings and resolutions

1. **Fixed — path canonicalization bypass.** Original `localPath` accepted whitespace-prefixed ` ../outside.png` and ` javascript:alert(1)`. URL parsing strips leading/trailing ASCII whitespace. The new validator rejects whitespace. `original_path_counterexample.cjs` preserves the original function and four concrete counterexamples.
2. **Fixed — Retry lost navigation intent.** Retrying failed initial deep links or Back navigation always pushed history. The fixed state keeps `errorContext`; retry preserves the original `history` intent.
3. **Fixed — history failure broke state consistency.** A simulated `history.pushState` exception after image/number updates left committed selection at the old pose and falsely claimed the old view was retained. The fixed app keeps the successful visual commit and gives a separate history warning.
4. **Fixed — repeated current selection added unnecessary history.** An already-committed selection now does not fetch or push another entry.

`counterexamples-before-history-fix.json` records the pre-fix history failures and source hashes. `counterexamples.cjs` is intentionally an original-failure reproduction, not a final passing regression suite.

## Final verified source identity

- app.js: `a9b10e397eb8287763abde65192867a0ff7cb2d7b80b0be0d64e6785433abab5`
- pose-state.js: `2f50cad4153ebad58397341e2cd8133a0bb05fbe220447c827f1603e402e983d`

The app caption was subsequently clarified to `front同机位等幅裁片` without changing the intended state logic. The author reran the 19 baseline cases and both independent suites after that edit; the updated `regressions.json` confirms the app hash above and all 10 app regressions passing. The prior failures and their original hashes remain unchanged.

## Passed checks

- Existing `web-source/test_state.cjs`: 10 cases.
- Existing `web-source/test_app.cjs`: 9 cases.
- Independent `regressions.cjs`: 10 final actual-app mock-DOM regressions covering the repaired defects, stale decoder success, stale image failure, late initial success, and popstate superseding pending selection.
- Independent `independent_checks.cjs`: 384 settlement permutations (three concurrent requests plus initial success/error), 16 malformed metadata rejections, 20 unsafe-path rejections, and 3 generated-path acceptances.

Run from the work directory:

```sh
node web-revisions/009/web-source/test_state.cjs
node web-revisions/009/web-source/test_app.cjs
node web-revisions/009/review/audit_pose_workbench/regressions.cjs
node web-revisions/009/review/audit_pose_workbench/independent_checks.cjs
```

The independent suites verify source hashes remain unchanged during their run and save JSON results beside themselves.

## Explicit limits

The official model snapshot was still being finalized at this audit stage. No absent `model-stage` or old draft files were characterized as a completed delivery failure. Composition reads variant dimensions from each variant's default model-info and angle/head-center arrays from each individual pose's model-info. Final imported JSON, static HTML, source-model numeric parity, and file-byte parity must be checked after the official snapshot is composed. Native Back/Forward behavior, image decoding, GPU appearance, and device layout remain outside this Node-only audit.

## Composition and fixed-crop source review

This is a source/math review only, not execution of final `verify.py` or acceptance of an unimported model snapshot.

- `compose.py` copies each pose's `pose.angles_degrees` array without reordering; the static card, initial panel, and app present indices 0/1/2 as shoulder-world / elbow-relative / head-world angles. `recipe.pose` independently establishes that contract: `t=q[0]`, `u=t+q[1]`, and `h=q[2]` after degree-to-radian conversion.
- `head_center` remains `[x,y,z]` in metres. Static and interactive panels use indices 0 and 2 multiplied by 1000, rounded to 0.1 mm. These mappings agree.
- With a 960×960 source, a 4:3 viewport under `object-fit:cover` shows 960×720 source pixels. `object-position:50% 75%` distributes the 240-pixel vertical overflow as 180 pixels above and 60 below, exactly the stated `x=0..960, y=180..900` crop. The final high-specificity rule and its mobile override retain this geometry.
- The generator uses an orthographic front camera with the same camera/target x and z, `to_track_quat('-Z','Y')`, and square output. Therefore world z is screen up, and `pixel_y=480-(z-target_z)/ortho_scale*960` is the correct projection. `verify.py` uses maximum z for top and minimum z for bottom, then checks `180 <= top <= bottom <= 900`; it also compares front-camera dictionaries across all nine poses.
- Limited coverage, not a found wrong value: the current verifier checks JSON angle/head-center parity, but does not independently assert variant `stats` against config or all rendered static-HTML numeric text. The crop boundaries are hardcoded in the verifier rather than derived from or checked against CSS. Future CSS/mapping edits need renewed source review or explicit drift assertions.
