"""Verify frozen numerical inputs; this does not rerun geometry checks."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));p.add_argument('--report',required=True);a=p.parse_args();root=Path(a.root);rows=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for folder in sorted((root/'assets').iterdir()):
 if not folder.is_dir():continue
 for kind in ['native','assembly','motion','scene']:
  report=root/'review'/('qa-'+folder.name+'-'+kind+'.json')
  if not report.exists():rows.append({'variant':folder.name,'kind':kind,'passed':False,'reason':'missing_report'});continue
  r=json.loads(report.read_text());paths=[('model_sha256',folder/'model.blend'),('checker_sha256',root/'source'/('audit_'+kind+'.py'))]
  if kind in ['native','assembly']:paths.append(('info_sha256',folder/'model-info.json'))
  if kind=='native':paths.extend([('glb_sha256',folder/'model.glb'),('payload_checker_sha256',root/'source/audit_payload.py')])
  if kind=='scene':paths.append(('scene_sha256',folder/'scene.blend'))
  if kind in ['motion','scene']:paths.append(('native_helper_sha256',root/'source/audit_native.py'))
  checks={key:path.exists() and r.get(key)==sha(path) for key,path in paths}
  info=json.loads((folder/'model-info.json').read_text())
  for key,name in [('generator_sha256','generate.py'),('recipe_sha256','recipe.py')]:checks[key]=info.get(key)==sha(root/'source'/name)
  rows.append({'variant':folder.name,'kind':kind,'report_passed':r.get('passed',False),'identity_checks':checks,'passed':r.get('passed',False) and all(checks.values())})
out={'passed':{r['variant'] for r in rows}=={'slot','span','rise'} and len(rows)==12 and all(r['passed']for r in rows),'records':rows,'scope':'Identity verification only; does not rerun geometry, GPU or phone tests.'};Path(a.report).write_text(json.dumps(out,indent=2));print(json.dumps(out));raise SystemExit(0 if out['passed']else 1)
