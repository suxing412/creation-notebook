"""Freeze only after fresh static/unit/delivery checks and native-browser input binding.
Not a browser runner or model gate; it never converts unverified GPU/phone/AT into a pass.
"""
from pathlib import Path
import argparse,subprocess,sys,json,hashlib
import sys
sys.dont_write_bytecode=True
from verify import verify as static_verify
from verify_delivery import verify as delivery_verify

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def freeze(root):
 marker=root/'WEB-FROZEN-SHA256.json'
 if marker.exists():marker.unlink() # A failed recheck must not leave a stale freeze marker.
 def run(cmd):subprocess.run(cmd,check=True,cwd=root)
 run(['node','web-source/test_gallery.cjs','web-review/unit-checks.json'])
 run(['node','web-source/test_app.cjs','web-review/app-unit-checks.json'])
 run([sys.executable,'-B','web-source/test_projection.py','--asset-root','assets','--output','web-review/projection-unit-checks.json'])
 run([sys.executable,'-B','web-source/test_import.py','--output','web-review/import-unit-checks.json'])
 if not static_verify(root)['passed']:raise ValueError('Fresh static/link/provenance checks failed')
 browser=json.loads((root/'web-review/browser-checks.json').read_text())
 if not browser.get('passed') or browser.get('scope')!='Final native Chromium limited page QA':raise ValueError('Final native browser report unavailable')
 required={'index.html','style.css','app.js','gallery-state.js','web-assets/projection-data.json'}|{f'assets/orison/{v}.png' for v in ('beauty','front','side','seam-detail')}|{f'web-assets/{k}-{v}-projection.png' for k in ('orison','latitude','ascend') for v in ('front','side')}
 identities=browser.get('input_sha256',{})
 if not required<=set(identities):raise ValueError('Browser input binding incomplete')
 for name,digest in identities.items():
  p=root/name
  if not p.is_file() or sha(p)!=digest:raise ValueError('Browser checked a different file: '+name)
 if not delivery_verify(root)['passed']:raise ValueError('Fresh delivery gate failed')
 files=[{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(root.rglob('*')) if p.is_file() and p!=marker]
 result={'status':'web-frozen-static-and-limited-native-browser-validated','study':'007','scope':'Main observation page + exact model import identity; GPU, true mobile devices, 200% zoom, full screen reader and manufacturing remain unverified.','manifest_sha256':sha(root/'manifest.json'),'files_count':len(files),'bytes':sum(x['bytes'] for x in files),'files':files}
 marker.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'frozen':True,'files':len(files),'bytes':result['bytes'],'freeze_sha256':sha(marker)},indent=2));return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();freeze(a.directory.resolve())
