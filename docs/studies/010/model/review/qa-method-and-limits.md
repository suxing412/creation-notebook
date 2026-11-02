# 010 independent geometry QA — method and limits

## Inherited and changed
- Reused 009's native oriented-triangle and actual GLB payload validation, local winding, world signed volume, connected components, triangle area, duplicate coordinates, independent spatial positive-area coplanar scan, BVH intersection and containment checks.
- Removed 009 lamp-specific family and contact whitelist. 010 allows **no contact-region waiver**. Every rail/divider pair remains subject to local intersection tests, even where the assembly was intended to join.
- Added expected Rail 1–2 and Divider 1–N family names; metadata cannot simply omit or invent a panel.
- Actual GLB vertices/indices/nodes are decoded and compared as a name-indexed oriented world-coordinate triangle multiset against native geometry, rather than trusting exporter success.

## Independent assembly probes
`audit_assembly.py` casts rays against actual Blender meshes at each rail/divider joint, measuring rail slot width, divider slot width, both plate thicknesses, each of four individual side clearances and the vertical mid-lap gap. Width equality alone is insufficient: an off-centre panel can retain its thickness while intruding into one side wall.

Actual minimum Z and studio-ground separation are measured from every vertex. Before floor alignment, the curved-divider bevel produced a minimum around −0.013245 mm while nominal profile bottoms were zero. The initial diagnostic report preserves that discrepancy. Final floor-aligned parts must measure zero within the numerical gate; a minimum below the studio plane at −0.2 mm fails. These are digital geometric checks, not manufacturing tolerances, flatness or stability certification.

The final vertical gap is tested against the nominal clearance plus each part's recorded alignment displacement, and cannot fall below nominal clearance minus 1 μm. Lateral clearance remains independently measured. `parts[].floor_alignment_m` records the geometry change; declaring metadata is not sufficient for the native/GLB or actual surface tests to pass.

## Extraction samples
`audit_motion.py` moves each divider independently along +Z while all other parts remain fixed. Sample offsets (metres): 0, .0003, .0006, .0012, .003, .006, .012, .024, .048, .055, .08, .12. The 55 mm sample corresponds to the close exploded view. Surface BVH candidates and ray-parity containment are tested at each sample. This is **not** continuous swept-volume proof, dynamics, material deformation, structural load or manufacturing validation. The full independent positive-coplanar scan is a static native gate; it is not repeated at every motion sample.

## Negative controls
- `audit_fault_controls.py`: valid reference plus missing face, self-crossing joined solids, one/all reversed faces, duplicate face, degenerate face, disconnected components, coincident coplanar solids, intersecting solids, contained solids, forbidden local waiver metadata, partially-covered local intersection and a GLB exported after changing geometry.
- `audit_payload_controls.py`: valid reference and deliberately corrupt header length, buffer-view extent, stride, index, nonfinite positions/normals, bounds and external-buffer reference.
- `audit_assembly_controls.py`: actual SLOT baseline plus 1 mm lateral panel displacement, 1 mm lowering and slot-roof deformation. The displacement must also fail finite motion inspection. A failure is credited only when its designated failure field is observed.
- Rejected mesh/GLB binaries stay in excluded `work/`; only control code and nonbinary reports belong in the release.

## Numerical limits and evidence
Reports bind checker SHA-256, input SHA-256 and UTC. Native and payload helpers have separate identities. Frozen-identity verification does not rerun geometry. Intersection algorithms are finite-precision mesh tests, not exact-arithmetic mathematical proof. Small untested parameter changes and all continuous parameter combinations remain unverified. CPU renders do not validate WebGL, GPU z-fighting or iPhone presentation.

## Boundary discovery and checker correction
The first lower-boundary sample (.25 m length, .12 m depth, .10 m divider height, 3 dividers, .006 m thickness, .05 m rail height, .0004 m clearance) exposed a real generation defect: pre-triangulated cap tessellation produced collinear zero-area triangles at the slot roof; bevel processing then generated microscopic edges, duplicate/degenerate triangles and self-overlap. The failure report and numerical diagnostic examples are retained. Rejecting this sample is not counted as successful reusable geometry.

The first upper-boundary inspection separately produced a ray-parity containment ambiguity at a point demonstrably outside the other closed mesh's axis-aligned bounding box. The checker now first rejects containment when the point is strictly outside that AABB (with a conservative margin). This is a geometric exclusion, not a contact exemption. The before-checker-change report is retained, and all targeted controls are rerun against the changed checker.

Two opposite envelope corners and the three published presets are finite samples only. Their independent native, actual GLB, joint-ray and extraction reports are named `qa-preflight-{lower,upper,slot,span,rise}-*.json`. Boundary configurations are preserved in `qa-boundary-configs.json`; regenerate them with the final generator rather than distributing rejected or temporary binaries. Successful preflight is not the identity verification of the subsequently rendered/published files; the final three `qa-{slot,span,rise}-*.json` sets serve that role.

Self-intersection BVH checks exclude triangle pairs sharing native vertex indices and separately test positive-area coplanarity. This and ray sampling remain finite-precision diagnostics; they are not a general exact self-intersection solver for every possible pathological mesh.

## Saved rendering scene closure
`audit_scene.py` reopens the actual final `scene.blend` and checks each model object's oriented world triangle multiset against `model.blend`, actual studio-plane Z and positive model-to-ground separation, and Cycles CPU configuration. This catches a scene that differs from the export even when each file independently loads. Three saved-scene controls (valid, raised ground, shifted divider) test designated failures; bad scenes remain only under excluded work/. This is data consistency, not a claim that the render pixels or GPU presentation were independently validated by this script.
