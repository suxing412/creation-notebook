"""Controls for measured assembly and actual-mesh motion audit; corrupt files stay private work."""
import bpy,sys,json,math,hashlib,datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));import audit_assembly,audit_motion,audit_native
R=Path(__file__).resolve().parents[1];src=R/'assets/hinge';out=R/'work/qa-assembly-controls-final';out.mkdir(exist_ok=True);rows=[]
for name,target in [('valid',None),('oversize_shaft','shaft_radius'),('collapsed_bore','bore_radius'),('layer_collision','layer_gap')]:
 bpy.ops.wm.open_mainfile(filepath=str((src/'model.blend').resolve()));info=json.loads((src/'model-info.json').read_text())
 if name=='oversize_shaft':
  ob=bpy.data.objects['Shoulder axle'];P=info['pose']['shoulder']
  for v in ob.data.vertices:v.co.x=P[0]+(v.co.x-P[0])*1.4;v.co.z=P[2]+(v.co.z-P[2])*1.4
 if name=='collapsed_bore':
  ob=bpy.data.objects['Lower arm'];P=info['pose']['shoulder'];a=info['pose']['lower_angle'];cs,sn=math.cos(a),math.sin(a)
  for v in ob.data.vertices:
   dx=v.co.x-P[0];dz=v.co.z-P[2];x=cs*dx+sn*dz;z=-sn*dx+cs*dz
   if math.hypot(x,z)<.006:v.co.x=P[0]+dx*.6;v.co.z=P[2]+dz*.6
 if name=='layer_collision':
  for v in bpy.data.objects['Lower arm'].data.vertices:v.co.y+=.004
 case=out/name;case.mkdir(exist_ok=True);model=case/'model.blend';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(model.resolve()));r=audit_assembly.audit(model,src/'model-info.json');codes=[f['code']for f in r['failures']];rows.append({'case':name,'expected_code':target,'observed_codes':codes,'passed':r['passed'],'targeted_condition_observed':r['passed']if target is None else target in codes,'model_sha256':audit_native.sha(model)});(case/'report.json').write_text(json.dumps(r,indent=2))
# A translated actual head violates ground clearance despite unchanged nominal pose metadata.
bpy.ops.wm.open_mainfile(filepath=str((src/'model.blend').resolve()))
for name in['Head housing','Diffuser']:
 for v in bpy.data.objects[name].data.vertices:v.co.z-=.6
model=out/'wrong-head-height.blend';bpy.ops.wm.save_as_mainfile(filepath=str(model.resolve()));mr=audit_motion.sample(model,src/'model-info.json',2);caught=any(q['lowest_vertex_z_m']<-.01 for q in mr['records']);rows.append({'case':'actual_mesh_below_ground','expected_code':'negative_actual_ground_z','targeted_condition_observed':not mr['passed']and caught,'accepted_pose_count':mr['accepted_pose_count'],'failed_pose_count':mr['failed_pose_count'],'model_sha256':audit_native.sha(model)});(out/'motion-report.json').write_text(json.dumps(mr,indent=2))
r={'passed':all(x['targeted_condition_observed']for x in rows),'checker_sha256':audit_native.sha(audit_assembly.__file__),'motion_checker_sha256':audit_native.sha(audit_motion.__file__),'control_script_sha256':audit_native.sha(__file__),'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cases':rows};(R/'review/qa-assembly-controls-final.json').write_text(json.dumps(r,indent=2));print('ASSEMBLY CONTROLS',r['passed']);assert r['passed']
