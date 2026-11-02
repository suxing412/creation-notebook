from pathlib import Path
import runpy,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent
runpy.run_path(str(R/'build_legacy.py'))
runpy.run_path(str(R/'build_overview.py'))
