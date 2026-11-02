"""Bind a completed limited-browser review to final files, rerun local gates, freeze.
Does not turn the unverified GPU/device/zoom/screen-reader/physical layers into PASS.
"""
from pathlib import Path
import json,hashlib,subprocess,sys,argparse
sys.dont_write_bytecode=True
from verify import verify as verify_static
from verify_delivery import verify as verify_delivery
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def freeze(root):
 marker=root/'WEB-FROZEN-SHA256.json'
 if marker.exists():marker.unlink()
 for cmd in [['node','web-source/test_state.cjs','web-review/state-unit-checks.json'],['node','web-source/test_app.cjs','web-review/app-unit-checks.json'],[sys.executable,'-B','web-source/test_import.py','--output','web-review/import-unit-checks.json']]:subprocess.run(cmd,cwd=root,check=True)
 if not verify_static(root)['passed']:raise ValueError('Static identity/link checks failed')
 b=json.loads((root/'web-review/browser-checks.json').read_text())
 if b.get('passed') is not True or b.get('scope')!='Final native Chromium limited page QA':raise ValueError('Required native-browser review missing')
 o=b.get('observations',{})
 if set(o)!={'desktop','nine','interaction','deep','mobile','nojs','failure','recovery','initialFailure','initialRecovery','viewer'}:raise ValueError('Native observation groups incomplete')
 expected={(k,v)for k in ('veil','horizon','fold')for v in ('beauty','hole-detail','top')}
 if len(o['nine'])!=9 or {(x['variant'],x['view'])for x in o['nine']}!=expected or not all(x['ready']for x in o['nine']):raise ValueError('Native nine-state coverage incomplete')
 if o['desktop']['controlsBottom']>o['desktop']['height'] or o['desktop']['scrollWidth']>o['desktop']['width']:raise ValueError('Desktop first-task bounds failed')
 if o['mobile']['mobile']['scrollWidth']>o['mobile']['mobile']['width'] or o['mobile']['frameCSS']['width']!=320:raise ValueError('Native narrow CSS bounds failed')
 if o['nojs']['nojs']['enhanced'] is not False or o['nojs']['presets']!=3 or o['nojs']['downloads']!=9:raise ValueError('No-script observations incomplete')
 if o['failure']['title']!='透幕 / VEIL' or o['failure']['width']!='360 mm' or o['recovery']['title']!='横幕 / HORIZON' or o['recovery']['width']!='540 mm' or o['recovery']['retryHidden'] is not True:raise ValueError('Failure/recovery identity observations differ')
 if o['initialFailure']['frameHidden'] is not True or o['initialRecovery']['frameHidden'] is not False or o['viewer']['staticVisible'] is not True or o['viewer']['liveHidden'] is not True:raise ValueError('Fallback observations incomplete')

 required={'index.html','style.css','app.js','plate-state.js','web-assets/plate-data.json','web-delivery.json'}|{f'assets/{k}/{v}.png' for k in ('veil','horizon','fold') for v in ('beauty','beauty-wide','hole-detail','top','front')}
 if not required<=set(b.get('input_sha256',{})):raise ValueError('Browser input identity binding incomplete')
 for f,digest in b['input_sha256'].items():
  if not (root/f).is_file() or sha(root/f)!=digest:raise ValueError('Browser input has changed: '+f)
 if not verify_delivery(root)['passed']:raise ValueError('Delivery identity/privacy gate failed')
 files=[{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(root.rglob('*')) if p.is_file() and p!=marker]
 r={'study':'008','status':'web-frozen-static-and-limited-native-browser-validated','scope':'Independent main page and faithful model import; GPU, physical phones, 200% zoom, full screen reader and physical/optical/structural performance unverified.','manifest_sha256':sha(root/'manifest.json'),'files_count':len(files),'bytes':sum(x['bytes']for x in files),'files':files};marker.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();r=freeze(a.directory.resolve());print(json.dumps({k:v for k,v in r.items() if k!='files'},ensure_ascii=False,indent=2))
