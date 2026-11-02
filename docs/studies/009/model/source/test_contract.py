import json,math,itertools,hashlib
from pathlib import Path
import recipe
root=Path(__file__).resolve().parents[1];rows=[]
def check(label,func,want):
 try:func();ok=True;why='accepted'
 except Exception as e:ok=False;why=str(e)
 rows.append({'label':label,'accepted':ok,'expected':want,'passed':ok==want,'detail':why})
base=json.loads((root/'configs/hinge.json').read_text())
for p in (root/'configs').glob('*.json'):check('preset:'+p.stem,lambda p=p:recipe.pose(json.loads(p.read_text())),True)
for key,(lo,hi) in recipe.RANGES.items():
 for val,tag in [(float('nan'),'nan'),(float('inf'),'inf'),(True,'bool'),('3','string'),(lo-.001,'under'),(hi+.001,'over')]:
  c=base|{key:val};check(key+':'+tag,lambda c=c:recipe.pose(c),False)
for key,val in [('seed',1),('seed',True),('version','bad'),('name','../bad')]:check(str((key,val)),lambda key=key,val=val:recipe.validate(base|{key:val}),False)
check('extra-key',lambda:recipe.validate(base|{'surprise':1}),False)
check('missing-key',lambda:recipe.validate({k:v for k,v in base.items() if k!='name'}),False)
check('coupled-table-collision',lambda:recipe.pose(base|{'lower_length':.20,'upper_length':.29},[55,-125,-25]),False)
for val in [[],[1,2],[55,-70,True],[55,-70,float('nan')],[54,-70,0]]:check('bad-angle:'+repr(val),lambda val=val:recipe.pose(base,val),False)
# Finite geometry/angle corner acceptance census; rejection is expected for some combinations.
census=[]
for L,U,R,H in itertools.product(*[recipe.RANGES[k] for k in ['lower_length','upper_length','base_radius','head_radius']]):
 c=base|{'lower_length':L,'upper_length':U,'base_radius':R,'head_radius':H}
 for q in itertools.product(*[recipe.RANGES[k] for k in ['shoulder_deg','elbow_deg','head_deg']]):
  try:p=recipe.pose(c,q);valid=True;why='accepted';z=p['head_floor_conservative_bound_m']
  except Exception as e:valid=False;why=str(e);z=None
  census.append({'geometry':[L,U,R,H],'angles':q,'accepted':valid,'reason':why,'head_floor_bound_m':z})
r={'passed':all(x['passed'] for x in rows),'tests':rows,'finite_corner_count':len(census),'corner_accepted':sum(x['accepted'] for x in census),'corners':census,'scope':'Configuration validation and conservative head/table envelope only. Not mesh collision testing or full domain proof.','recipe_sha256':hashlib.sha256(Path(recipe.__file__).read_bytes()).hexdigest(),'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};(root/'review/input-contract-tests.json').write_text(json.dumps(r,indent=2));print(r['passed'],len(rows),'corner',len(census));assert r['passed']
