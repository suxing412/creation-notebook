"""Pure validation boundary/invalid input regression without rendering."""
import ast,json,math,re,copy,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];tree=ast.parse((root/'source/generate.py').read_text());scope={'math':math,'re':re}
for node in tree.body:
 if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ['VERSION','BOUNDS']:exec(compile(ast.Module(body=[node],type_ignores=[]),'contract','exec'),scope)
 if isinstance(node,ast.FunctionDef) and node.name=='validate':exec(compile(ast.Module(body=[node],type_ignores=[]),'contract','exec'),scope)
base=json.loads((root/'configs/poise.json').read_text());cases=[]
def case(name,changes,expected,version=(4,3,2),remove=None):
 c=copy.deepcopy(base);c.update(changes)
 if remove:c.pop(remove)
 try:scope['validate'](c,version);accepted=True;reason=None
 except (ValueError,TypeError) as e:accepted=False;reason=str(e)
 cases.append({'name':name,'expected_accept':expected,'accepted':accepted,'passed':accepted==expected,'reason':reason})
for k,(lo,hi) in scope['BOUNDS'].items():
 case(k+'-lower-bound',{k:lo},True);case(k+'-upper-bound',{k:hi},True);case(k+'-below',{k:lo-1e-6},False);case(k+'-above',{k:hi+1e-6},False)
for name,changes in [('NaN',{'shade_width':float('nan')}),('infinity',{'rim_height':float('inf')}),('bool-number',{'shade_width':True}),('string-number',{'shade_rise':'0.08'}),('unknown-key',{'private_path':'x'}),('path-name',{'name':'../escape'}),('seed-other',{'seed':1}),('seed-float',{'seed':0.0}),('recipe-version',{'recipe_version':'2.0.0'}),('aspect-coupled',{'shade_width':.49,'shade_depth':.27}),('slope-coupled',{'shade_width':.33,'shade_rise':.12}),('support-coupled',{'rim_height':.53,'base_width':.16})]:case(name,changes,False)
case('missing-required',{},False,remove='stem_lean');case('blender-version-4.3.1',{},False,version=(4,3,1));case('blender-version-4.4.0',{},False,version=(4,4,0))
report={'tests':len(cases),'passed':all(c['passed'] for c in cases),'cases':cases,'scope':'Pure contract tests; separate boundary geometry tests exercise actual Blender meshes.'};(Path(sys.argv[1]) if len(sys.argv)>1 else root/'review/invalid-input-tests.json').write_text(json.dumps(report,indent=2));print(report['tests'],report['passed']);assert report['passed']
