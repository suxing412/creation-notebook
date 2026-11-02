# VEIL 008 — native / payload QA

This is a **restricted VEIL recipe gate**, not a general-purpose mesh validator, manufacturing certificate or GPU acceptance report. It reuses numerical ideas from 006/007, not their geometric families or allowed-contact whitelists. Units are metres; Blender is exactly 4.3.2.

## Commands

Run from the parent directory of `study-008`:

```sh
python study-008/source/run_gates.py --asset study-008/assets/veil --label unique-final-label
python study-008/source/test_contract.py --report study-008/review/unique-input-report.json
python study-008/source/test_faults.py --baseline study-008/assets/veil --output study-008/work/qa/unique-faults --report study-008/review/unique-fault-report.json
python study-008/source/test_export_comparison.py --baseline study-008/assets/veil --label unique-export-faults
```

Every Blender invocation includes `--python-exit-code 1`. The wrapper refuses an existing report label, captures exit codes, requires explicit PASS and fresh run IDs, and verifies exact input/checker/recipe hashes before and after the run. The native file is **reopened from disk**; a prior in-memory scene is not the tested asset. A generated model or a process exit alone does not count as acceptance.

## Native contract

- Exactly one raw mesh, identity transform, no modifiers, parents, constraints, shape keys, object/mesh animation or drivers.
- Whole-mesh deterministic vertex positions within 0.2 µm; **oriented** polygon index cycles, not point sets or an object-name whitelist.
- Finite coordinates; triangle area, duplicate triangles, nonmanifold edges, local winding, float64 world signed volume, components, Euler characteristic and genus.
- `columns × rows` actual holes. Every actual aperture ring edge has incidence two; every pair of neighboring rings has the prescribed oriented wall face; inverse-cylinder positions fit the rounded profile. A centre normal ray through every aperture must be clear. Capping, opening a wall, moving a ring and filling a handle have separate fault probes.
- Front/back mouth separation, straight bore depth and outer-surface same-UV normal pairs are measured from actual stored vertices, not merely the nominal thickness parameter.
- Construction metadata is regenerated and compared; units, counts, dimensions, bounds and locked material metadata are also checked. Actual shader graph is one Principled BSDF connected to one material output, with the locked base colour/roughness/metallic and no transparent/transmissive/coated/subsurface/emissive change covered by those fields.
- Native corner normals must be finite and unit length within `2e-5`, and must not oppose the geometric face hemisphere (`dot < -1e-5` is rejected). This does **not** independently prove equality to the author's analytic normal field.

### Meaning of the ligament number

`ligament_sampling.records` measures the **3D Euclidean separation of actual front/back mouth boundary polylines**, each compared with every other same-side mouth and the same-side external rim. Every actual line segment is divided into four equal intervals; each production 64-edge mouth supplies 256 samples. The checker derives this count from the locked recipe resolution rather than accepting arbitrary user-controlled tessellation.

The sampled minimum is an **upper estimate** of the continuous polyline minimum. For each compared pair the checker subtracts half of each boundary's largest sample spacing, plus 0.2 µm, to obtain a conservative polyline lower bound. The gate requires this lower bound ≥ 4 mm. The input validator separately requires a developed cell margin ≥ 5 mm.

This is **not** the minimum thickness over all rounded rim/bore surfaces, a developed geodesic ligament, projected visibility, manufacturing wall thickness, strength or stability. The report's `definition` and `excludes` fields must accompany any public number.

## GLB and correspondence

`check_glb.py` decodes the real GLB bytes: magic/chunks/length, buffer views, accessor schema/offset/stride/alignment/bounds, finite payloads, actual POSITION min/max, index ranges, unit normals, positive triangle areas, one scene/mesh/material and locked PBR factors. It rejects unsupported external resources, skins, animation and required extensions. It is not a complete glTF conformance suite.

`compare_exports.py` first invokes that payload checker, then compares exact **oriented triangle coordinate multisets** after native `(x,y,z) → GLB (x,z,-y)`. Exporter vertex splitting is allowed; neither equal point sets nor equal vertex counts are treated as topology equivalence.

For each matching oriented triangle, all three corner normals are compared after the same axis mapping. The declared vector tolerance is `2e-4` (approximately 0.0115° for unit vectors). This explicitly accommodates the observed save/reopen/export normal difference. Quantization is a plausible explanation, not an independently isolated cause; this is **not exact normal equality**. Reports expose maximum error and matched corner count. A legal unit-length reversed-normal payload must pass structural payload validation yet fail this correspondence field.

No indexed-topology isomorphism, shader equivalence, runtime lighting, GPU rendering or dynamic flicker is claimed.

## Real fault probes and limits

`test_faults.py` saves real damaged `.blend` files and real malformed `.glb` files under `work/qa`; these must never be shipped as formal assets. Each case requires its **specified dedicated field** to hit; rejection by some other field is insufficient. Contained-island and +1 µm near-plane controls also require no surface-intersection hits. State probes prove the raw vertex/face arrays did not change.

`test_export_comparison.py` includes legal translated-position, reversed-triangle and reversed-unit-normal payloads. The latter two preserve the coordinate point set; structural payload PASS is required before dedicated correspondence rejection.

Coverage is deliberately finite. Not every fail field, every branch, every animation/driver kind, every malformed glTF possibility or the continuous parameter box has a dedicated counterexample. BVH candidates exclude triangles sharing any vertex; noncoplanar adjacent foldovers are not independently certified. Coplanarity uses bidirectional float64 plane distances and projected SAT with numeric tolerances, not exact predicates. Exact recipe shape/topology agreement constrains those gaps but is not an independent arbitrary-geometry proof.

## Historical failure preservation

The original revision-0 mesh had the wrong orientation on its hole wall quads. Its observed local winding failure is retained; it is not accepted as the before baseline. A separately regenerated `baseline-corrected` is the accepted revision-0 comparison.

The earliest gate run also recorded two QA caveats: recipe bytes changed while it ran, so the fresh-identity wrapper failed; and the initial emission check incorrectly treated the default white emission colour as emitting while strength was zero. The shader check was corrected to test colour × strength. That older report is not rewritten or promoted to a valid final gate. A later current-checker replay of the old bad mesh separately establishes the geometric rejection with stable identities.

A second QA regression was found by the real narrowing fault after normal checks were added: a broad edit accidentally formed a tuple report key, so overall rejection occurred via an internal exception without the dedicated ligament field. The exact faulty checker snapshot and failed report were retained, the key was repaired, and the same mesh hit its dedicated field on retest. `gate-qa-regression-history-v3.json` records both outcomes. An additional AST key guard supplements the actual mesh faults.

The production recipe is fixed at 64 aperture points. Earlier 32-point geometry/source/report identity is kept separately as history; it is not retroactively certified by a 64-point recipe hash.
