"""Validate the current buildless site; explicitly opt into legacy generation."""
from pathlib import Path
import argparse
import runpy
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
SITE = next((p for p in (ROOT / 'dist', ROOT.parent / 'dist') if p.is_dir()), ROOT.parents[1] / 'docs')

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--legacy', action='store_true', help='Run the original gallery generators in a legacy checkout or prepared dist snapshot.')
args = parser.parse_args()

if args.legacy:
    # Legacy generators write index.html and archival files. Protect the current
    # library site, including when an old maintenance command is copied.
    if any((SITE / library / 'index.html').exists() for library in ('model-library', 'web-library', 'space-library')):
        parser.error('Legacy generation refused: this target contains the current library site. Use a separate legacy checkout or prepared gallery/dist snapshot without the library entry pages.')
    runpy.run_path(str(ROOT / 'build_legacy.py'))
    runpy.run_path(str(ROOT / 'build_overview.py'))
else:
    print('Current site is buildless: checking existing HTML without regenerating files.', flush=True)
    subprocess.run([sys.executable, '-B', str(ROOT / 'check_overview.py')], check=True)
