"""Real saved-scene negative controls; all altered binaries excluded in work/."""
import bpy,json,sys,argparse,runpy,datetime,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--scene',required=True);p.add_argument('--output',required=True);p.add_argument('--report',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=Path(__file__).resolve().parent;out=Path(a.output);out.mkdir(parents=True,exist_ok=True);rows=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for name,expected in [('valid',None),('raised_ground','scene_ground_intersection'),('shifted_divider','scene_model_geometry')]:
 bpy.ops.wm.open_mainfile(filepath=str(Path(a.scene).resolve()))
 if name=='raised_ground':bpy.data.objects['Plane'].location.z=.001
 if name=='shifted_divider':bpy.data.objects['Divider 1'].location.x=.001
 scene=out/(name+'.blend');report=out/(name+'.json');bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(scene.resolve()));sys.argv=['blender','--','--model',a.model,'--scene',str(scene),'--report',str(report)]
 try:runpy.run_path(str(root/'audit_scene.py'),run_name='__main__')
 except RuntimeError:pass
 r=json.loads(report.read_text());codes=[q['code']for q in r['failures']];rows.append({'case':name,'expected_failure':expected,'observed_codes':codes,'passed':r['passed'] if expected is None else expected in codes,'scene_sha256':sha(scene)})
r={'passed':all(q['passed']for q in rows),'cases':rows,'checker_sha256':sha(root/'audit_scene.py'),'native_helper_sha256':sha(root/'audit_native.py'),'control_script_sha256':sha(__file__),'source_scene_sha256':sha(a.scene),'source_model_sha256':sha(a.model),'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};Path(a.report).write_text(json.dumps(r,indent=2));print('SCENE CONTROLS',r['passed']);
if not r['passed']:raise RuntimeError('scene control missed expected result')
