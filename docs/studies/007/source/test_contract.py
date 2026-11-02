"""007 finite input-domain regression. No mesh generation or continuous parameter-box proof.
Tests type/bounds independently of sampled geometry; separately exercises full-validator named
configs and known geometric rejections. Source boundary grid is input acceptance only.
"""
import json,math,itertools,copy,hashlib,datetime,argparse
from pathlib import Path
import recipe
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(report):
 base=json.loads((ROOT/'configs/orison.json').read_text());rows=[];input_fixture=dict(base,section_width=.072,section_depth=.060,corner_radius=.006,width_modulation=0)
 def check(name,c,expected,fragment=None,**kwargs):
  try:recipe.validate(c,**kwargs);accepted=True;error=None
  except Exception as e:accepted=False;error=type(e).__name__+': '+str(e)
  passed=accepted==expected and (fragment is None or fragment in (error or ''));rows.append({'case':name,'expected_acceptance':expected,'actual_acceptance':accepted,'expected_error_fragment':fragment,'error':error,'passed':passed,'sampled_geometry_enabled':kwargs.get('check_geometry',True)})
 for key,(lo,hi) in recipe.BOUNDS.items():
  for label,value in [('lower',lo),('upper',hi),('midpoint',(lo+hi)/2)]:check(key+'-'+label,dict(input_fixture,**{key:value}),True,check_geometry=False)
  for label,value in [('below-lower',lo-1e-6),('above-upper',hi+1e-6),('nan',float('nan')),('positive-inf',float('inf')),('negative-inf',-float('inf')),('bool-true',True),('bool-false',False),('string',str(lo)),('null',None),('list',[lo]),('dict',{'value':lo})]:check(key+'-'+label,dict(input_fixture,**{key:value}),False,key+': finite numeric value',check_geometry=False)
 for key in base:
  c=base.copy();del c[key];check('missing-'+key,c,False,'Exact configuration key set',check_geometry=False)
 check('extra-key',dict(base,unexpected=1),False,'Exact configuration key set',check_geometry=False)
 for name in ['', '../outside','x/y','X','中文','a'*32,'bad_name','a b'] :check('invalid-name-'+repr(name),dict(base,name=name),False,'Invalid name',check_geometry=False)
 for name in ['a','valid-name-007','a'*31]:check('valid-name-'+name,dict(base,name=name),True,check_geometry=False)
 for seed in [False,True,1,-1,0.,'0',None]:check('invalid-seed-'+repr(seed),dict(base,seed=seed),False,'Only integer seed 0',check_geometry=False)
 for version in ['0.0.0','1.0',None,1]:check('invalid-recipe-version-'+repr(version),dict(base,recipe_version=version),False,'Recipe version mismatch',check_geometry=False)
 for version in [(4,3,1),(4,4,0),(5,0,0)]:check('invalid-blender-version-'+repr(version),base,False,'Only Blender 4.3.2',version=version,check_geometry=False)
 for revision in [False,True,-1,2,1.,'1',None]:check('invalid-revision-'+repr(revision),base,False,'Revision must be integer 0 or 1',revision=revision,check_geometry=False)
 for revision in [0,1]:check('valid-revision-'+str(revision),base,True,revision=revision,check_geometry=False)
 check('rounded-section-straight-span-consumed',dict(base,corner_radius=.014,section_depth=.026),False,'corner radius consumes straight span',check_geometry=False)
 check('full-validator-curvature-rejection',dict(base,radius_x=.085,radius_z=.22,section_width=.072,section_depth=.060,asymmetry=.25,depth_wave=0,lean=0,width_modulation=.27),False,'Curvature times section circumradius')
 check('full-validator-reference-rejection',dict(base,radius_x=.085,radius_z=.10,depth_wave=.042,lean=.03),False,'Analytic frame reference near singularity')
 named=[]
 for path in sorted((ROOT/'configs').glob('*.json')):
  c=json.loads(path.read_text());check('full-validator-'+path.stem,c,True);named.append({'config':path.name,'sha256':sha(path),'diagnostics':recipe.diagnostics(c)})
 corner_rows=[];keys=list(recipe.BOUNDS)
 for index,values in enumerate(itertools.product(*[recipe.BOUNDS[k] for k in keys])):
  c=dict(base,**dict(zip(keys,values)));minimum_width=c['section_width']*(1-c['width_modulation']);expected=2*c['corner_radius']<min(minimum_width,c['section_depth'])-.004
  try:recipe.validate(c,check_geometry=False);accepted=True;error=None
  except Exception as e:accepted=False;error=str(e)
  corner_rows.append({'index':index,'accepted_by_input_layer':accepted,'expected_by_independent_straight_span_rule':expected,'passed':accepted==expected,'rejection':error})
 r={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':all(q['passed'] for q in rows+corner_rows),'test_script_sha256':sha(__file__),'recipe_sha256':sha(recipe.__file__),'base_config_sha256':sha(ROOT/'configs/orison.json'),'independent_endpoint_input_fixture':input_fixture,'explicit_tests':len(rows),'tests':rows,'named_full_validator_configs':named,'parameter_box_corners':{'count':len(corner_rows),'accepted_input_layer':sum(q['accepted_by_input_layer'] for q in corner_rows),'rejected_input_layer':sum(not q['accepted_by_input_layer'] for q in corner_rows),'geometry_generated':0,'full_geometry_validator_run':False,'rows':corner_rows},'limits':['Ten-parameter finite input cases and 1024 binary corners are not a continuous-domain proof.','Box corners invoke check_geometry=False; acceptance is only type/bounds/cross-field straight-span acceptance, not sampled curvature/clearance acceptance or valid mesh acceptance.','Only named configs and explicit geometric rejection examples use the full sampled validator; separate native/GLB reports are required for actual files.']};report.parent.mkdir(parents=True,exist_ok=True);report.write_text(json.dumps(r,indent=2,ensure_ascii=False));print('007 INPUT',r['passed'],'explicit',len(rows),'corner input accepted',r['parameter_box_corners']['accepted_input_layer'],'/',len(corner_rows));raise SystemExit(0 if r['passed'] else 1)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--report',default=str(ROOT/'review/gate-input-tests-v1.json'));a=p.parse_args();report=Path(a.report)
 if report.exists():raise RuntimeError('Refusing to overwrite existing report; choose a new --report')
 run(report)
