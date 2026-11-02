"""Reproduce pure-contract, boundary, deterministic-export and injected-fault tests.
No renders. Separate output folder required; invalid models are explicitly test fixtures.
"""
import argparse,subprocess,json,ast,hashlib,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--threads',type=int,default=2);a=p.parse_args();out=Path(a.output).resolve();root=Path(__file__).resolve().parents[1];src=root/'source'
if out.exists():raise SystemExit('Refusing to overwrite existing test output')
out.mkdir(parents=True)
def run(script,*args,success=True):
 result=subprocess.run(['blender','-b','-t',str(a.threads),'--python-exit-code','1','--python',str(src/script),'--',*map(str,args)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 # Logs stay in test output only, never in asset manifests.
 (out/(script+'-last.log')).write_text(result.stdout)
 if success and result.returncode!=0:raise RuntimeError('Blender test failed: '+script)
 return result.returncode
subprocess.run([sys.executable,str(src/'test_contract.py'),str(out/'invalid-input-tests.json')],check=True)
for name in ['repro-a','repro-b']:run('generate.py','--config',root/'configs/poise.json','--output',out/name,'--geometry-only')
aa=(out/'repro-a/model.glb').read_bytes();bb=(out/'repro-b/model.glb').read_bytes();repro={'byte_identical':aa==bb,'sha256':hashlib.sha256(aa).hexdigest()};assert repro['byte_identical']
run('check.py','--model',out/'repro-a/model.blend','--info',out/'repro-a/model-info.json','--report',out/'baseline-validation.json')
ns={}
for node in ast.parse((src/'generate.py').read_text()).body:
 if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ['BOUNDS','VERSION']:exec(compile(ast.Module(body=[node],type_ignores=[]),'contract','exec'),ns)
boundary=[]
for name,idx in [('boundary-low',0),('boundary-high',1)]:
 c=dict(name=name,seed=0,recipe_version=ns['VERSION'],**{k:v[idx] for k,v in ns['BOUNDS'].items()});cfg=out/(name+'.json');cfg.write_text(json.dumps(c,indent=2))
 run('generate.py','--config',cfg,'--output',out/name,'--geometry-only');run('check.py','--model',out/name/'model.blend','--info',out/name/'model-info.json','--report',out/(name+'-validation.json'));boundary.append(name)
run('make_test_mutants.py',out/'repro-a/model.blend',out/'mutants');cases=[]
for model in sorted((out/'mutants').glob('*.blend')):
 report=out/'mutants'/(model.stem+'.json');code=run('check.py','--model',model,'--info',out/'repro-a/model-info.json','--report',report,success=False);q=json.loads(report.read_text());
 if model.stem=='oblique-coplanar-overlap':assert q['coplanar_positive_area_overlaps'],'Specific oblique coplanar detector must fire'
 if model.stem=='reversed-base-face':assert q['inconsistent_winding_edges'],'Specific winding detector must fire'
 cases.append({'case':model.stem,'rejected':not q['passed'] and code!=0})
assert len(cases)==13 and all(c['rejected'] for c in cases)
subprocess.run([sys.executable,str(src/'test_glb_payload.py'),str(out/'repro-a/model.glb'),str(out/'glb-mutants')],check=True)
r={'passed':True,'glb_payload_tests':4,'contract_tests':47,'boundary_tests':boundary,'reproducibility':repro,'adversarial_cases':cases,'limits':'Static discrete tests, not a continuous-parameter proof or runtime graphics certification.'};(out/'summary.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
