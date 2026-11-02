"""009 finite actual-mesh kinematic sampling. No continuous-domain or engineering proof."""
import bpy,sys,json,math,argparse,hashlib,datetime,itertools,uuid,struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
import recipe,audit_native
VERSION='009-motion-0.1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rotate(v,a):c=math.cos(a);s=math.sin(a);return(c*v[0]-s*v[2],v[1],s*v[0]+c*v[2])
def map_point(p,old,new,angle):q=rotate(tuple(p[k]-old[k]for k in range(3)),angle);return tuple(q[k]+new[k]for k in range(3))
def transformed(name,pts,old,new):
 if name=='Lower arm':pivot='shoulder';angle=new['lower_angle']-old['lower_angle']
 elif name=='Upper arm':pivot='elbow';angle=new['upper_angle']-old['upper_angle']
 elif name in('Head neck','Head housing','Diffuser'):pivot='head_pivot';angle=new['head_angle']-old['head_angle']
 elif name.startswith('Elbow '):pivot='elbow';angle=0
 elif name.startswith('Head '):pivot='head_pivot';angle=0
 else:return pts
 return [map_point(p,old[pivot],new[pivot],angle)for p in pts]

def sample(model,info_path,grid):
 info=json.loads(Path(info_path).read_text());c=info['config'];old=info['pose'];bpy.ops.wm.open_mainfile(filepath=str(Path(model).resolve()));parts={}
 for ob in bpy.data.objects:
  if ob.type!='MESH':continue
  me=ob.data;me.calc_loop_triangles();parts[ob.name]=([tuple(float(x)for x in ob.matrix_world@v.co)for v in me.vertices],[tuple(t.vertices)for t in me.loop_triangles])
 required={'Base body','Fixed upright','Lower arm','Upper arm','Head neck','Head housing','Diffuser'}|{'Foot '+str(i)for i in range(1,4)}|{n+s for n in ['Shoulder','Elbow','Head']for s in [' axle',' cap -1',' cap 1']}
 if set(parts)!=required:raise ValueError('Unknown or missing rigid component name')
 rows=[];fails=[];accepted=[];rejects=[]
 axes={k:[recipe.RANGES[k][0]+i*(recipe.RANGES[k][1]-recipe.RANGES[k][0])/(grid-1)for i in range(grid)]for k in['shoulder_deg','elbow_deg','head_deg']}
 for angles in itertools.product(*axes.values()):
  try:new=recipe.pose(c,angles)
  except Exception as e:rejects.append({'angles':angles,'reason':str(e)});continue
  posed={};ground=float('inf');bounds={}
  for name,(points,tris)in parts.items():
   points=[tuple(struct.unpack('<f',struct.pack('<f',x))[0]for x in p)for p in transformed(name,points,old,new)];ground=min(ground,min(p[2]for p in points));tree=BVHTree.FromPolygons([Vector(p)for p in points],tris,all_triangles=True,epsilon=0);posed[name]=(points,tris,tree);bounds[name]=[[min(p[k]for p in points),max(p[k]for p in points)]for k in range(3)]
  collisions=[];contacts=0
  # Allowed regions are rebuilt by the geometry generator contract when available.
  regions=recipe.contact_regions(c,new) if hasattr(recipe,'contact_regions') else info.get('contact_regions',[])
  for an,bn in itertools.combinations(posed,2):
   if any(bounds[an][k][1]<bounds[bn][k][0]-1e-8 or bounds[bn][k][1]<bounds[an][k][0]-1e-8 for k in range(3)):continue
   av,at,ab=posed[an];bv,bt,bb=posed[bn]
   for i,j in ab.overlap(bb):
    A=[av[k]for k in at[i]];B=[bv[k]for k in bt[j]];pts=audit_native.intersection_points(A,B);overlap=audit_native.clip_area(A,B)
    if pts and all(audit_native.allowed(p,(an,bn),regions)for p in pts)and overlap<=1e-12:contacts+=1
    else:collisions.append({'objects':[an,bn],'triangles':[i,j],'points':pts,'coplanar_area_m2':overlap})
  row={'angles_degrees':angles,'lowest_vertex_z_m':ground,'unclassified_triangle_pairs':len(collisions),'locally_accepted_triangle_pairs':contacts,'unclassified_examples':collisions[:12]};rows.append(row)
  if ground< -2e-7 or collisions:fails.append(row)
 return{'passed':not fails,'variant':info['variant'],'grid_per_axis':grid,'requested_pose_count':grid**3,'accepted_pose_count':len(rows),'rejected_pose_count':len(rejects),'domain_rejections':rejects,'failed_pose_count':len(fails),'records':rows,'limits':['Finite tensor-product angle samples on this exact three-length geometry; no guarantee between samples or other parameter combinations.','Every pose is applied to the actual baked mesh with declared rigid naming groups; no physics or inverse kinematics.','Motion uses BVH boundary intersections plus minimum vertex ground height; full containment and independent all-pair coplanarity are checked only on static exported poses, not every tensor-grid pose. Force/stability/electrical constraints remain unverified.','Locally accepted triangle pairs are clipped by spatial contact region at each pose, not pair-wide exclusions.']}
def main():
 p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--info',required=True);p.add_argument('--report',required=True);p.add_argument('--grid',type=int,default=3);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);r={'checker_version':VERSION,'checker_sha256':sha(__file__),'native_checker_sha256':sha(audit_native.__file__),'recipe_sha256':sha(recipe.__file__),'model_sha256':sha(a.model),'info_sha256':sha(a.info),'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'run_id':str(uuid.uuid4()),'passed':False}
 try:r.update(sample(a.model,a.info,a.grid))
 except Exception as e:r['exception']={'type':type(e).__name__,'message':str(e)}
 for key,path in [('model_sha256',a.model),('info_sha256',a.info),('recipe_sha256',recipe.__file__),('checker_sha256',__file__),('native_checker_sha256',audit_native.__file__)]:
  if r[key]!=sha(path):r['passed']=False;r.setdefault('identity_failures',[]).append({'file':Path(path).name,'reason':'changed_during_check'})
 Path(a.report).write_text(json.dumps(r,indent=2));print('009 motion',r['passed'],r.get('failed_pose_count'))
 if not r['passed']:raise RuntimeError('Motion gate failed')
if __name__=='__main__':main()
