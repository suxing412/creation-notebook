# Reproduce independent 010 checks
Requires Blender 4.3.2, Python 3 and the exported assets. From the study root, for each of slot, span, rise:

```sh
blender -b -t 3 --python-exit-code 1 --python source/audit_native.py -- --model assets/slot/model.blend --glb assets/slot/model.glb --info assets/slot/model-info.json --report review/qa-slot-native.json
blender -b -t 3 --python-exit-code 1 --python source/audit_assembly.py -- --model assets/slot/model.blend --info assets/slot/model-info.json --report review/qa-slot-assembly.json
blender -b -t 3 --python-exit-code 1 --python source/audit_motion.py -- --model assets/slot/model.blend --report review/qa-slot-motion.json
```

Frozen identity only (not rerunning geometry):
```sh
python source/audit_verify_identity.py --root . --report review/qa-final-identities.json
```
Controls create intentionally bad binaries under excluded work/:
```sh
blender -b -t 3 --python-exit-code 1 --python source/audit_fault_controls.py -- --output work/qa-controls-final --report review/qa-controls-final.json
python source/audit_payload_controls.py
blender -b -t 3 --python-exit-code 1 --python source/audit_assembly_controls.py -- --model assets/slot/model.blend --info assets/slot/model-info.json --output work/qa-assembly-controls --report review/qa-assembly-controls-final.json
```
The payload-control runner resolves its fixture path relative to the study directory. See review/qa-method-and-limits.md for the exact scope and limitations. Do not ship work/ or infer GPU/phone acceptance from these checks.

## Coverage, numerical gates and blind spots
- Blender native: finite coordinates, applied/identity transforms (matrix tolerance 1e-8), no modifiers/constraints/parents/animation/shape keys, expected component names, one connected shell per part, manifold edges and locally consistent winding, positive world signed volume, triangle area ≥1e-12 m² and no identical coordinate triangle duplicates.
- Cross/self geometry: Blender BVH epsilon 0; no 010 metadata-based contact exemptions. Independent projected coplanar overlap >1e-12 m² rejects (spatial cells .02 m, plane grouping tolerance 5e-8 m). A strictly outside-AABB point is not contained; other component representatives use three-ray parity. Inconsistent parity rejects. Surface-near points <2e-7 m are treated as contact in the containment helper, with intersections separately checked.
- GLB: binary/container/accessor/view/index/finite-number/bounds checks, named node coverage, identity transforms and exact **oriented coordinate-triangle multisets** including multiplicity. This is not vertex-index topology isomorphism: the exporter may split vertices at normal/material seams. Declared accessor bound tolerance is max(1e-7, 2e-7×|bound|). Shader equivalence is untested.
- Joint probes: each side clearance, thickness and slot width uses a 2e-7 m comparison tolerance against the configured geometry. Actual mid-lap gap includes the recorded whole-part floor-alignment displacement, with a minimum nominal clearance minus 1e-6 m. Aligned bottom tolerance is 2e-7 m; the studio plane at −.0002 m must remain below every vertex. These are numerical checks, not manufacturing tolerances.
- Extraction: exactly **12 listed +Z offsets per divider**, including .055 m and .12 m. Other parts remain stationary. No continuous swept-volume or load/fit/stability proof. The independent spatial coplanar scan is a static gate, not repeated at every extraction sample.
- Self BVH checks skip pairs sharing native vertex indices; the separate coplanar scan addresses positive-area coplanarity but is not a universal exact solver for all pathological adjacent-face crossings. All geometry calculations are finite precision.
- Controls: 14 native/export fixtures (1 valid +13 targeted faults), 9 payload fixtures (1 valid +8 faults), 4 actual-assembly fixtures (1 valid +3 faults), 3 saved-scene fixtures (1 valid +2 faults); two of the latter additionally test the motion checker. Counts mean expected outcomes observed, not that deliberately invalid inputs passed.
- CPU image review, mesh audits and narrow browser frames do **not** verify GPU/WebGL temporal z-fighting, real iPhone input, continuous parameter ranges, physical manufacturing or structural performance.

## Historical evidence
`review/qa-native-before-aabb.py` has the exact checker SHA used by the first lower-boundary failure and upper-boundary parity-ambiguity reports. It is historical, not the current gate. `qa-preflight-*.json` binds temporary sample files; `qa-{slot,span,rise}-*.json` must bind final files. The identity verifier requires all three final variants, all four gate reports each, matching generator/recipe hashes, and all current checker hashes.

## Saved CPU scene check
```sh
blender -b -t 3 --python-exit-code 1 --python source/audit_scene.py -- --model assets/slot/model.blend --scene assets/slot/scene.blend --report review/qa-slot-scene.json
```
The saved scene must preserve actual oriented model triangles, have the studio ground at −0.2 mm below all model vertices, and use Cycles CPU. This checks saved scene data, not rendered pixels. Then run `python source/audit_summary.py` after the identity verifier to write the final aggregate.

Saved-scene targeted controls (raised ground must fail ground clearance; shifted divider must fail model correspondence):
```sh
blender -b -t 3 --python-exit-code 1 --python source/audit_scene_controls.py -- --model assets/slot/model.blend --scene assets/slot/scene.blend --output work/qa-scene-controls --report review/qa-scene-controls-final.json
```
