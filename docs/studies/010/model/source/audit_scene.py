"""Verify final CPU-render scene model geometry and actual ground separation."""
import bpy,json,sys,argparse,datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));from audit_native import sha,cycle
from collections import Counter
def mesh(o):
 o.data.calc_loop_triangles();v=[o.matrix_world@q.co for q in o.data.vertices];return Counter(cycle([tuple(v[i])for i in t.vertices])for t in o.data.loop_triangles)
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--scene',required=True);p.add_argument('--report',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);bpy.ops.wm.open_mainfile(filepath=str(Path(a.model).resolve()));native={o.name:mesh(o)for o in bpy.data.objects if o.type=='MESH'};bpy.ops.wm.open_mainfile(filepath=str(Path(a.scene).resolve()));fail=[];rows=[]
for name,triangles in native.items():
 o=bpy.data.objects.get(name);same=o is not None and o.type=='MESH' and mesh(o)==triangles;rows.append({'name':name,'oriented_world_triangles_equal':same})
 if not same:fail.append({'code':'scene_model_geometry','object':name})
ground=bpy.data.objects.get('Plane');gz=None;clearance=None
if ground is None or ground.type!='MESH':fail.append({'code':'scene_ground_missing'})
else:
 points=[ground.matrix_world@v.co for v in ground.data.vertices];gz=[min(v.z for v in points),max(v.z for v in points)]
 if any(abs(z+.0002)>2e-7 for z in gz):fail.append({'code':'scene_ground_position','z_range_m':gz})
 bottom=min((o.matrix_world@v.co).z for o in bpy.data.objects if o.name in native for v in o.data.vertices);clearance=bottom-gz[1]
 if clearance<=0:fail.append({'code':'scene_ground_intersection','clearance_m':clearance})
s=bpy.context.scene
if s.render.engine!='CYCLES' or s.cycles.device!='CPU':fail.append({'code':'scene_renderer','engine':s.render.engine,'device':s.cycles.device})
r={'passed':not fail,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checker_sha256':sha(__file__),'native_helper_sha256':sha(Path(__file__).with_name('audit_native.py')),'model_sha256':sha(a.model),'scene_sha256':sha(a.scene),'objects':rows,'ground_z_range_m':gz,'minimum_ground_clearance_m':clearance,'failures':fail,'scope':'Saved scene correspondence and actual ground only; does not rerender pixels or verify GPU/phone.'};Path(a.report).write_text(json.dumps(r,indent=2));print('SCENE',r['passed']);
if not r['passed']:raise RuntimeError('scene rejected')
