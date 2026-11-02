# Historical 32-point recipe source — not the final production sampler

These recipe/generator snapshots preserve the accepted intermediate 32-point hole topology. Final production uses 64 points per hole; do not substitute historical gate reports for final identity mappings. The files retain their exact bytes for provenance. To regenerate an intermediate visual baseline with Blender 4.3.2, invoke this snapshot's `generate.py` with the regular explicit `--config`, `--output`, `--revision`, `--samples` and `--resolution` arguments. Use a new output folder; never overwrite the final assets. The final checker enforces the final fixed sampling and is not a retroactive pass for these different-index historical files.

The original winding-broken recipe is also retained as an explicitly invalid source snapshot. It is for reproducing the documented failure only, not a working model recommendation. No broken binary is delivered as a final asset.
