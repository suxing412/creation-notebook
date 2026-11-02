from pathlib import Path
import runpy
R=Path(__file__).resolve().parent
runpy.run_path(str(R/'build_legacy.py'))
runpy.run_path(str(R/'build_overview.py'))
