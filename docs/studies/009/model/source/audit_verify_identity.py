"""Re-read all final 009 gate reports and bind their PASS to current bytes."""
import json,hashlib,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify():
 checks=[];failures=[]
 for variant in ['hinge','reach','poise']:
  for pose in [None,'folded','extended']:
   asset=ROOT/'assets'/variant
   if pose:asset=asset/'poses'/pose
   label=variant+('-'+pose if pose else '')
   for kind in(['native']if pose else['native','assembly','motion']):
    report=ROOT/'review'/('qa-final-'+label+'-'+kind+'.json');r=json.loads(report.read_text());identities={'model_sha256':asset/'model.blend','info_sha256':asset/'model-info.json','checker_sha256':ROOT/'source'/('audit_'+kind+'.py')}
    if kind=='native':identities.update({'glb_sha256':asset/'model.glb','payload_checker_sha256':ROOT/'source/audit_payload.py'})
    else:identities['recipe_sha256']=ROOT/'source/recipe.py'
    if kind=='motion':identities['native_checker_sha256']=ROOT/'source/audit_native.py'
    mismatches=[{'field':k,'path':str(p.relative_to(ROOT)),'reported':r.get(k),'current':sha(p)}for k,p in identities.items()if r.get(k)!=sha(p)]
    topology_ok=True
    if kind=='native':
     topology_ok=all(o['euler_characteristic']==(-2 if o['name']in ['Fixed upright','Lower arm','Upper arm','Head neck'] else 2)for o in r['objects'])
    ok=r.get('passed')is True and not mismatches and not r.get('identity_failures')and topology_ok;checks.append({'report':str(report.relative_to(ROOT)),'report_sha256':sha(report),'passed':ok,'bound_inputs':{str(p.relative_to(ROOT)):sha(p)for p in identities.values()},'mismatches':mismatches,'family_euler_characteristics_confirmed':topology_ok if kind=='native'else None})
    if not ok:failures.append({'report':str(report.relative_to(ROOT)),'mismatches':mismatches,'reported_passed':r.get('passed')})
 for file,script in [('qa-controls-final.json','audit_fault_controls.py'),('qa-payload-controls-final.json','audit_payload_controls.py'),('qa-assembly-controls-final.json','audit_assembly_controls.py'),('qa-contact-controls-final.json','audit_contact_controls.py')]:
  p=ROOT/'review'/file;r=json.loads(p.read_text());related={'checker_sha256':'audit_native.py','payload_checker_sha256':'audit_payload.py'}if file=='qa-controls-final.json'else{'checker_sha256':'audit_payload.py'}if file=='qa-payload-controls-final.json'else{'checker_sha256':'audit_assembly.py','motion_checker_sha256':'audit_motion.py'}if file=='qa-assembly-controls-final.json'else{'checker_sha256':'audit_native.py'}
  ok=r.get('passed')is True and r.get('control_script_sha256')==sha(ROOT/'source'/script)and all(r.get(k)==sha(ROOT/'source'/v)for k,v in related.items())and all(q.get('targeted_condition_observed',q.get('expected_condition_observed'))is True for q in r.get('cases',[]))
  checks.append({'report':str(p.relative_to(ROOT)),'report_sha256':sha(p),'passed':ok,'cases':len(r.get('cases',[]))})
  if not ok:failures.append({'report':file,'reason':'Control report/script mismatch'})
 return {'passed':not failures,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verifier_sha256':sha(__file__),'checks':checks,'failures':failures,'scope':'15 final actual-asset gate reports plus 31 targeted controls; historical reports are not reassigned to final bytes.'}
if __name__=='__main__':
 r=verify();(ROOT/'review/qa-final-identities.json').write_text(json.dumps(r,indent=2));print('FINAL IDENTITIES',r['passed']);assert r['passed']
