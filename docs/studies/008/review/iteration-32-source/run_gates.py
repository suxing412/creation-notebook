"""Fresh-report/exit-code/identity wrapper for 008 native + real GLB checks.
Run e.g. python source/run_gates.py --asset assets/orison --label locked-orison.
Reports remain immutable: choose a new label for each rerun. Logs only under work.
"""
import argparse,subprocess,sys,json,hashlib,datetime,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--asset',required=True);p.add_argument('--label',required=True);a=p.parse_args();asset=Path(a.asset).resolve()
 if not asset.is_relative_to(ROOT):raise ValueError('Asset must be inside this study')
 if not re.fullmatch('[a-zA-Z0-9-]+',a.label):raise ValueError('Simple alphanumeric/hyphen label required')
 outputs={k:ROOT/'review'/('gate-'+a.label+'-'+k+'.json') for k in ['native','glb','comparison','identity']}
 if any(q.exists() for q in outputs.values()):raise RuntimeError('Immutable report label already exists; use a new label')
 inputs={'native':asset/'model.blend','glb':asset/'model.glb','info':asset/'model-info.json','native_checker':ROOT/'source/check.py','glb_checker':ROOT/'source/check_glb.py','recipe':ROOT/'source/recipe.py','comparison_checker':ROOT/'source/compare_exports.py'};before={k:sha(v) for k,v in inputs.items()};logdir=ROOT/'work'/'qa'/('gate-run-'+a.label);logdir.mkdir(parents=True,exist_ok=False)
 commands={'native':['blender','-b','-t','4','--python-exit-code','1','--python',str(inputs['native_checker']),'--','--model',str(inputs['native']),'--info',str(inputs['info']),'--report',str(outputs['native'])],'glb':[sys.executable,str(inputs['glb_checker']),str(inputs['glb']),str(outputs['glb'])],'comparison':['blender','-b','-t','4','--python-exit-code','1','--python',str(inputs['comparison_checker']),'--','--model',str(inputs['native']),'--glb',str(inputs['glb']),'--report',str(outputs['comparison'])]};checks={}
 for kind,command in commands.items():
  result=subprocess.run(command,capture_output=True,text=True);(logdir/(kind+'.log')).write_text(result.stdout+result.stderr);r=json.loads(outputs[kind].read_text()) if outputs[kind].exists() else {};checks[kind]={'exit_code':result.returncode,'new_report_exists':outputs[kind].exists(),'explicit_pass':r.get('passed') is True,'run_id_present':bool(r.get('run_id')),'model_identity_matches':r.get('model_sha256')==before['native' if kind=='comparison' else kind],'checker_identity_matches':r.get('checker_sha256')==before[kind+'_checker'],'report':outputs[kind].name}
  if kind=='comparison':checks[kind]['glb_identity_matches']=r.get('glb_sha256')==before['glb'];checks[kind]['glb_checker_identity_matches']=r.get('glb_checker_sha256')==before['glb_checker']
  if kind=='native':checks[kind].update({'info_identity_matches':r.get('info_sha256')==before['info'],'recipe_identity_matches':r.get('recipe_sha256')==before['recipe']})
 after={k:sha(v) for k,v in inputs.items()};stable=before==after;passed=stable and all(q['exit_code']==0 and all(v is True for k,v in q.items() if k not in ['exit_code','report']) for q in checks.values());r={'asset':str(asset.relative_to(ROOT)),'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':passed,'inputs_stable_during_checks':stable,'input_sha256':after,'checks':checks,'wrapper_sha256':sha(Path(__file__))};outputs['identity'].write_text(json.dumps(r,indent=2));print('008 GATES',a.label,passed);raise SystemExit(0 if passed else 1)
if __name__=='__main__':main()
