# First version — retained, not the delivered final geometry

Actual initial CPU preview: 48 maximum adaptive samples, 560 x 560, no denoising. Constant width; no 4 mm terminal plan-corner rounding. Config and exact original recipe/generator snapshots are retained. These images were inspected before research/refinement. Its original native binaries remain in the local work environment, but are intentionally excluded from the public source package to avoid treating a superseded variant as final.

To reconstruct the original source in a new folder, copy `recipe-before.py` to `recipe.py` and `generate-before.py` to `generate.py`, copy the config, then run Blender 4.3.2 with `--revision 0 --samples 48 --resolution 560`. The original generator accepts `--views beauty,side,bend-detail`.

The final recipe also retains `--revision 0` for controlled shape comparisons. The old images are not silently replaced by later high-sample renders.
