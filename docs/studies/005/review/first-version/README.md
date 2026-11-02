# Rejected first-version archive

This is historical evidence, **not a usable final asset**. Full rejected binary models remain only in the local study archive and are excluded from delivery packages; archived code/configuration permit intentional reproduction. It retains the original 76 degenerate triangles in Pin 1 and an early incomplete checker. Final models are only in `assets/`.

The original generator and exact configuration are preserved as `generate-before.py` and `config.json`. To reproduce the rejected geometry from the study root:

```sh
blender -b --python-exit-code 1 --python review/first-version/generate-before.py -- --config review/first-version/config.json --output rejected-first-repro --draft --geometry-only
```

The adjacent original render used 96 hero samples. `review/before.png` re-renders this same archived scene at the final 1024-sample setting with unchanged camera, lights, exposure and geometry. The invalid original geometry is intentionally not repaired in this archive.
