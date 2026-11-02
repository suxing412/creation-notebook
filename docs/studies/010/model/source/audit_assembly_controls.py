"""Actual 010 mesh fault injections, stored only in excluded work directory."""
import bpy,json,sys,argparse,datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));import audit_assembly as assembly;import audit_motion as motion
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--info',required=True);p.add_argument('--output',required=True);p.add_argument('--report',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(a.output);out.mkdir(parents=True,exist_ok=True);rows=[]
for name,expected in [('valid',None),('divider_x_offset','assembly_alignment'),('lower_below_studio','studio_ground_intersection'),('filled_joint','assembly_dimension')]:
 bpy.ops.wm.open_mainfile(filepath=str(Path(a.model).resolve()));ob=bpy.data.objects['Divider 1']
 if name=='divider_x_offset':
  for v in ob.data.vertices:v.co.x+=.001
 if name=='lower_below_studio':
  for v in ob.data.vertices:v.co.z-=.001
 if name=='filled_joint':
  c=json.loads(Path(a.info).read_text())['config'];roof=c['rail_height']/2+c['clearance']
  for v in ob.data.vertices:
   if abs(v.co.z-roof)<.001:v.co.z-=.002
 model=out/(name+'.blend');bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(model.resolve()));r=assembly.measure(model,a.info);codes=[f['code']for f in r['failures']];matched=r['passed'] if expected is None else expected in codes
 row={'case':name,'expected_failure':expected,'observed_codes':codes,'expected_condition_observed':matched,'model_sha256':assembly.sha(model)}
 if name in ('valid','divider_x_offset'):
  m=motion.measure(model);row['motion_passed']=m['passed'];row['motion_expected_observed']=m['passed'] if name=='valid' else not m['passed'];matched=matched and row['motion_expected_observed']
 row['passed']=matched;rows.append(row)
r={'passed':all(x['passed']for x in rows),'cases':rows,'source_model_sha256':assembly.sha(a.model),'info_sha256':assembly.sha(a.info),'assembly_checker_sha256':assembly.sha(assembly.__file__),'motion_checker_sha256':assembly.sha(motion.__file__),'control_script_sha256':assembly.sha(__file__),'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};Path(a.report).write_text(json.dumps(r,indent=2));print('ASSEMBLY CONTROLS',r['passed']);
if not r['passed']:raise RuntimeError('assembly controls did not match')
