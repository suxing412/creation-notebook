"""010 independent audit controls; generated corrupt binaries stay work/, public gets data only."""
import bpy,sys,json,math,hashlib,argparse,datetime
from pathlib import Path
from mathutils import Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent));import audit_native

def clear():bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def cube(name,location=(0,0,0),scale=(.01,.01,.01),rotation=0):
 bpy.ops.mesh.primitive_cube_add(size=2,location=location);o=bpy.context.object;o.name=name;o.scale=scale;o.rotation_euler.z=rotation;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);m=bpy.data.materials.new(name);m.diffuse_color=(.3,.4,.5,1);m.use_nodes=True;o.data.materials.append(m);return o

def run(out):
 out.mkdir(parents=True,exist_ok=True);cases=[]
 for name,expected in [('valid',None),('missing_face','nonmanifold'),('self_crossing','self_intersection_candidates'),('reverse_one','winding'),('reverse_all','world_volume'),('duplicate_face','duplicate_triangle'),('degenerate','degenerate'),('two_components','components'),('coplanar_duplicate','coplanar_positive_area'),('crossing','unclassified_interobject_intersections'),('contained','unclassified_containment'),('local_region_valid','contact_region_contract'),('local_region_partial','unclassified_interobject_intersections'),('export_wrong','export_geometry_mismatch')]:
  clear();ob=cube('Box');regions=[]
  if name in('missing_face','reverse_one','reverse_all','duplicate_face','degenerate'):
   verts=[tuple(v.co)for v in ob.data.vertices];faces=[tuple(p.vertices)for p in ob.data.polygons]
   if name=='missing_face':faces.pop()
   if name=='reverse_one':faces[0]=tuple(reversed(faces[0]))
   if name=='reverse_all':faces=[tuple(reversed(f))for f in faces]
   if name=='duplicate_face':faces.append(faces[0])
   if name=='degenerate':faces.append((0,0,1))
   me=bpy.data.meshes.new('Fault');me.from_pydata(verts,[],faces);me.materials.append(ob.data.materials[0]);ob.data=me
  if name in ('two_components','self_crossing'):
   other=cube('Other',(.03,0,0) if name=='two_components' else (.012,.003,.004),rotation=0 if name=='two_components' else .28);ob.select_set(True);other.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.join()
  if name=='coplanar_duplicate':cube('Other')
  if name in('crossing','local_region_valid','local_region_partial'):
   cube('Other',(.012,.003,.004),(.01,.010,.008),.28)
   if name.startswith('local_region'):
    regions=[{'id':'known-local-fixture','objects':['Box','Other'],'kind':'box','min':[-.03,-.03,-.03],'max':[.03,.03,.03]if name=='local_region_valid'else[.01,.002,.03]}]
  if name=='contained':cube('Other',(0,0,0),(.004,.004,.004),.19)
  case=out/name;case.mkdir(exist_ok=True);native=case/'model.blend';glb=case/'model.glb';info=case/'model-info.json';info.write_text(json.dumps({'contact_regions':regions}));bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(native.resolve()))
  if name=='export_wrong':
   ob.data.vertices[0].co.x-=.001
  bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.gltf(filepath=str(glb.resolve()),export_format='GLB',use_selection=True,export_apply=True,export_extras=False)
  try:r=audit_native.run(native,glb,info)
  except Exception as e:r={'passed':False,'failures':[{'code':getattr(e,'code',type(e).__name__),'message':str(e)}]}
  codes=[f['code']for f in r.get('failures',[])];matched=(r['passed'] if expected is None else expected in codes);cases.append({'case':name,'expected_failure':expected,'checker_passed':r['passed'],'observed_codes':codes,'expected_condition_observed':matched,'model_sha256':audit_native.sha(native),'glb_sha256':audit_native.sha(glb)});(case/'result.json').write_text(json.dumps(r,indent=2))
 report={'checker_sha256':audit_native.sha(audit_native.__file__),'payload_checker_sha256':audit_native.sha(audit_native.audit_payload.__file__),'control_script_sha256':audit_native.sha(__file__),'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':all(c['expected_condition_observed']for c in cases),'cases':cases}
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--report',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);r=run(Path(a.output));Path(a.report).write_text(json.dumps(r,indent=2));print('CONTROLS',r['passed']);
 if not r['passed']:raise RuntimeError('Control missed its targeted failure')
