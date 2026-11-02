"""Assemble web overlays into a freshly imported model directory; no publish/server actions."""
from pathlib import Path
import argparse,shutil,subprocess,sys
import sys
sys.dont_write_bytecode=True
import project,compose
from verify_delivery import WEB_SOURCE,WEB_REPORTS
ROOT=Path(__file__).resolve().parents[1]
def build(dest,reports):
 if not (dest/'manifest.json').exists():raise ValueError('Import approved model first')
 (dest/'web-source').mkdir(exist_ok=True);(dest/'web-review').mkdir(exist_ok=True)
 for name in WEB_SOURCE:
  if name=='model_lock.py':continue
  src=ROOT/'web-source'/name
  if src.resolve()!=(dest/'web-source'/name).resolve():shutil.copy2(src,dest/'web-source'/name)
 for name in WEB_REPORTS:
  if name in {'asset-parity.json','delivery-files.json','static-checks.json','link-checks.json'}:continue
  src=reports/name;out=dest/'web-review'/name
  if src.exists() and src.resolve()!=out.resolve():shutil.copy2(src,out)
 if (ROOT/'WEB-README.md').resolve()!=(dest/'WEB-README.md').resolve():shutil.copy2(ROOT/'WEB-README.md',dest/'WEB-README.md')
 project.build(dest/'assets',dest/'web-assets');compose.compose(dest,False)
 subprocess.run([sys.executable,'-B',str(dest/'web-source/render_reports.py'),'--directory',str(dest)],check=True)
 print('Web overlay assembled; not frozen until final browser checks and freeze.py')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--dest',type=Path,default=ROOT/'dist');p.add_argument('--reports',type=Path,default=ROOT/'review');a=p.parse_args();build(a.dest.resolve(),a.reports.resolve())
