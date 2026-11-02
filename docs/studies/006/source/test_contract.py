"""Finite exact-schema/input tests. Only separately generated meshes receive geometry QA."""
import sys,json,math,itertools,hashlib
from pathlib import Path
import recipe
root=Path(__file__).resolve().parents[1];base=json.loads((root/'configs/folio.json').read_text());rows=[]
def test(label,c,expected,version=(4,3,2)):
 try:recipe.validate(c,version);actual=True;reason=None
 except Exception as e:actual=False;reason=str(e)
 rows.append({'case':label,'expected_accepted':expected,'accepted':actual,'matched':actual==expected,'reason':reason})
test('base',base,True)
for k,(lo,hi) in recipe.BOUNDS.items():
 for suffix,v,ok in [('lower',lo,True),('upper',hi,True),('below',lo-1e-6,False),('above',hi+1e-6,False),('nan',float('nan'),False),('inf',float('inf'),False),('negative-inf',float('-inf'),False),('bool',True,False),('string',str(lo),False),('null',None,False)]:test(k+'-'+suffix,{**base,k:v},ok)
for suffix,v in [('path','../escape'),('newline','folio\n'),('unicode','折页'),('empty',''),('too-long','a'*32),('upper','Folio')]:test('name-'+suffix,{**base,'name':v},False)
for v in [True,1,0.0,None,'0']:test('seed-'+str(v),{**base,'seed':v},False)
test('extra-key',{**base,'extra':0},False);x=dict(base);del x['width'];test('missing-key',x,False);test('recipe-version',{**base,'recipe_version':'x'},False);test('blender-version',base,False,(4,4,0));test('inner-radius-coupling',{**base,'bend_radius':.006,'thickness':.004},False);test('lip-straight-margin',{**base,'lip_height':.020,'bend_radius':.012},True)
# Full 512 box corners: schema/coupling only; do not mislabel them as Blender mesh checks.
corner_rows=[]
for idx,bits in enumerate(itertools.product([0,1],repeat=len(recipe.BOUNDS))):
 c={**base,**{k:recipe.BOUNDS[k][bit] for k,bit in zip(recipe.BOUNDS,bits)}}
 try:recipe.validate(c);accepted=True;reason=None
 except ValueError as e:accepted=False;reason=str(e)
 corner_rows.append({'corner':idx,'bits':''.join(map(str,bits)),'accepted':accepted,'reason':reason})
report={'passed':all(r['matched'] for r in rows),'test_count':len(rows),'matched':sum(r['matched'] for r in rows),'cases':rows,'parameter_box_corners':{'total':len(corner_rows),'accepted':sum(r['accepted'] for r in corner_rows),'rejected':sum(not r['accepted'] for r in corner_rows),'scope':'validator only, not generated meshes or continuous-domain proof','cases':corner_rows},'recipe_sha256':hashlib.sha256((root/'source/recipe.py').read_bytes()).hexdigest()};(root/'review/gate-input-tests.json').write_text(json.dumps(report,indent=2));print('INPUT',report['matched'],'/',len(rows),'corners accepted',report['parameter_box_corners']['accepted'])
if not report['passed']:raise SystemExit(1)
