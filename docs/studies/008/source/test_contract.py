"""VEIL finite input-domain tests. Input acceptance, sampled constraints and actual meshes stay distinct."""
import json,math,itertools,hashlib,datetime,argparse
from pathlib import Path
import recipe
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def independent(c,revision=1):
 b=c['edge_radius'] if revision else 0;dx=c['width']/c['columns'];dy=c['height']/c['rows'];margin=1e9
 for row in range(c['rows']):
  for col in range(c['columns']):
   u=-c['width']/2+(col+.5)*dx;v=(row+.5)*dy;field=.62*math.sin(math.pi*v/c['height'])+.38*math.sin(2*math.pi*(u/c['width']+.5)+.4);scale=1+c['gradient']*field if revision else 1
   margin=min(margin,dx/2-dx*c['aperture_ratio']*.5*scale-b,dy/2-dy*c['aperture_ratio']*.5*scale-b)
 return margin>=.005 and c['thickness']*math.radians(c['curve_angle_degrees'])/(2*c['width'])<.05

def run(report):
 base=json.loads((ROOT/'configs/veil.json').read_text());rows=[]
 def check(name,c,expected,fragment=None,**kwargs):
  try:recipe.validate(c,**kwargs);accepted=True;error=None
  except Exception as e:accepted=False;error=type(e).__name__+': '+str(e)
  rows.append({'case':name,'expected_acceptance':expected,'actual_acceptance':accepted,'expected_error_fragment':fragment,'error':error,'passed':accepted==expected and (fragment is None or fragment in (error or '')),'geometry_constraints_enabled':kwargs.get('check_geometry',True)})
 for key,(lo,hi) in recipe.BOUNDS.items():
  mid=(lo+hi)//2 if key in recipe.INTEGER_KEYS else (lo+hi)/2
  for label,value in [('lower',lo),('upper',hi),('midpoint',mid)]:check(key+'-'+label,dict(base,**{key:value}),True,check_geometry=False)
  for label,value in [('below-lower',lo-1),('above-upper',hi+1),('nan',float('nan')),('positive-inf',float('inf')),('negative-inf',-float('inf')),('bool-true',True),('bool-false',False),('string',str(lo)),('null',None),('list',[lo]),('dict',{'value':lo})]:check(key+'-'+label,dict(base,**{key:value}),False,key+': finite numeric value',check_geometry=False)
  if key in recipe.INTEGER_KEYS:
   for value in [float(lo),lo+.5]:check(key+'-noninteger-type-'+str(value),dict(base,**{key:value}),False,key+': integer required',check_geometry=False)
 for key in base:
  c=base.copy();del c[key];check('missing-'+key,c,False,'Exact configuration key set',check_geometry=False)
 check('extra-key',dict(base,unexpected=1),False,'Exact configuration key set',check_geometry=False)
 for name in ['', '../outside','x/y','X','中文','a'*32,'bad_name','a b']:check('invalid-name-'+repr(name),dict(base,name=name),False,'Invalid name',check_geometry=False)
 for name in ['a','valid-name-008','a'*31]:check('valid-name-'+name,dict(base,name=name),True,check_geometry=False)
 for seed in [False,True,1,-1,0.,'0',None]:check('invalid-seed-'+repr(seed),dict(base,seed=seed),False,'Only integer seed 0',check_geometry=False)
 for version in ['0.0.0','1.0',None,1]:check('invalid-recipe-version-'+repr(version),dict(base,recipe_version=version),False,'Recipe version mismatch',check_geometry=False)
 for version in [(4,3,1),(4,4,0),(5,0,0)]:check('invalid-blender-version-'+repr(version),base,False,'Only Blender 4.3.2',version=version,check_geometry=False)
 for revision in [False,True,-1,2,1.,'1',None]:check('invalid-revision-'+repr(revision),base,False,'Revision must be integer 0 or 1',revision=revision,check_geometry=False)
 for revision in [0,1]:check('valid-revision-'+str(revision),base,True,revision=revision)
 bad=dict(base,width=.24,height=.28,columns=10,rows=10,aperture_ratio=.74,gradient=.22,edge_radius=.0018)
 check('full-validator-insufficient-developed-margin',bad,False,'Developed cell aperture margin')
 named=[]
 for path in sorted((ROOT/'configs').glob('*.json')):
  c=json.loads(path.read_text());check('full-validator-'+path.stem,c,True);named.append({'config':path.name,'sha256':sha(path),'diagnostics':recipe.diagnostics(c),'independent_geometry_acceptance':independent(c)})
 corners=[];keys=list(recipe.BOUNDS)
 for index,values in enumerate(itertools.product(*[recipe.BOUNDS[k] for k in keys])):
  c=dict(base,**dict(zip(keys,values)));input_expected=2*c['edge_radius']<=c['thickness']-.002;expected=input_expected and independent(c)
  try:recipe.validate(c,check_geometry=False);input_accept=True
  except Exception:input_accept=False
  try:recipe.validate(c);accepted=True;error=None
  except Exception as e:accepted=False;error=str(e)
  corners.append({'index':index,'input_layer_accepted':input_accept,'full_validator_accepted':accepted,'independent_geometric_rule_accepted':expected,'passed':input_accept==input_expected and accepted==expected,'rejection':error})
 r={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':all(q['passed'] for q in rows+corners),'test_script_sha256':sha(__file__),'recipe_sha256':sha(recipe.__file__),'base_config_sha256':sha(ROOT/'configs/veil.json'),'explicit_tests':len(rows),'tests':rows,'named_configs':named,'parameter_box_corners':{'count':len(corners),'input_accepted':sum(q['input_layer_accepted'] for q in corners),'full_validator_accepted':sum(q['full_validator_accepted'] for q in corners),'actual_meshes_generated':0,'rows':corners},'limits':['Finite endpoint/corner/config tests do not prove a continuous parameter domain.','Corner acceptance is validation of finite formulas only, not actual mesh QA or visual acceptance. Actual boundary-low/high native+GLB gates are separate.','Within this bounded parameter box the curvature-half-thickness <0.05 and straight-bore >=2mm clauses are implied by stricter bounds; no independent rejection trigger inside the box is claimed.','Actual minimal internal wall thickness, manufacture, load/stability and GPU are not tested.']};report.parent.mkdir(parents=True,exist_ok=True);report.write_text(json.dumps(r,indent=2,ensure_ascii=False));print('008 INPUT',r['passed'],'explicit',len(rows),'corner accepted',r['parameter_box_corners']['full_validator_accepted'],'/',len(corners));raise SystemExit(0 if r['passed'] else 1)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--report',required=True);a=p.parse_args();report=Path(a.report)
 if report.exists():raise RuntimeError('Fresh report required')
 run(report)
