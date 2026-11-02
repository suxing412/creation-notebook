"""Independent measurements of actual 009 bores, shafts and fixed-Y layer gaps."""
import bpy,sys,json,math,argparse,datetime,hashlib,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import recipe
VERSION='009-assembly-1.0'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def radial_segment(a,b):
 dx=b[0]-a[0];dy=b[1]-a[1];d=dx*dx+dy*dy;t=max(0,min(1,-(a[0]*dx+a[1]*dy)/d))if d else 0
 return math.hypot(a[0]+t*dx,a[1]+t*dy)
def audit(model,info_path):
 info=json.loads(Path(info_path).read_text());c=info['config'];p=info['pose'];bpy.ops.wm.open_mainfile(filepath=str(Path(model).resolve()));objects={o.name:o for o in bpy.data.objects if o.type=='MESH'};fails=[];bores=[];shafts=[]
 layouts=[('Fixed upright',.08,(0,.009,.03),math.pi/2),('Lower arm',c['lower_length'],(p['shoulder'][0],-.009,p['shoulder'][2]),p['lower_angle']),('Upper arm',c['upper_length'],(p['elbow'][0],.009,p['elbow'][2]),p['upper_angle']),('Head neck',.095,(p['head_pivot'][0],-.009,p['head_pivot'][2]),p['head_angle'])]
 for name,L,origin,angle in layouts:
  ob=objects[name];points=[];cs=math.cos(angle);sn=math.sin(angle)
  for v in ob.data.vertices:
   q=ob.matrix_world@v.co;dx=q.x-origin[0];dz=q.z-origin[2];points.append((cs*dx+sn*dz,q.y-origin[1],-sn*dx+cs*dz))
  for end in[0,L]:
   near={i:(q[0]-end,q[2])for i,q in enumerate(points)if math.hypot(q[0]-end,q[2])<.006}
   eligible=[(near[e.vertices[0]],near[e.vertices[1]])for e in ob.data.edges if all(i in near for i in e.vertices)]
   if not eligible:fails.append({'code':'missing_bore_edges','object':name,'end_m':end});continue
   minimum=min(radial_segment(a,b)for a,b in eligible);maximum=max(math.hypot(*q)for q in near.values());record={'object':name,'end_m':end,'actual_near_bore_vertices':len(near),'actual_edge_count':len(eligible),'minimum_edge_radial_distance_m':minimum,'maximum_near_bore_vertex_radius_m':maximum};bores.append(record)
   if minimum<.0044 or minimum>.0046:fails.append({'code':'bore_radius','record':record})
 for name,pivot in [('Shoulder',p['shoulder']),('Elbow',p['elbow']),('Head',p['head_pivot'])]:
  ob=objects[name+' axle'];points=[ob.matrix_world@v.co for v in ob.data.vertices];maximum=max(math.hypot(q.x-pivot[0],q.z-pivot[2])for q in points);record={'object':name+' axle','maximum_actual_radial_distance_m':maximum,'actual_axial_y_bounds_m':[min(q.y for q in points),max(q.y for q in points)]};shafts.append(record)
  if not .0039<maximum<.0041:fails.append({'code':'shaft_radius','record':record})
 minimum_bore=min(q['minimum_edge_radial_distance_m']for q in bores);maximum_shaft=max(q['maximum_actual_radial_distance_m']for q in shafts);clearance=minimum_bore-maximum_shaft
 if clearance<.0004:fails.append({'code':'radial_clearance','actual_m':clearance})
 gaps=[]
 for an,bn in [('Lower arm','Upper arm'),('Lower arm','Fixed upright'),('Head neck','Upper arm')]:
  ay=[(objects[an].matrix_world@v.co).y for v in objects[an].data.vertices];by=[(objects[bn].matrix_world@v.co).y for v in objects[bn].data.vertices];gap=max(min(by)-max(ay),min(ay)-max(by));gaps.append({'objects':[an,bn],'measured_y_interval_gap_m':gap})
  if gap<.0059:fails.append({'code':'layer_gap','objects':[an,bn],'actual_m':gap})
 return {'passed':not fails,'failures':fails,'bores':bores,'shafts':shafts,'minimum_measured_edge_bore_to_maximum_shaft_clearance_m':clearance,'layer_gaps':gaps,'limits':['Bore radius is the minimum radial distance on actual near-bore mesh edges, not a full solid distance oracle; all 8 bore boundaries are sampled by complete mesh edge enumeration.','Fixed-Y interval separation remains invariant under this declared planar Y-axis rotation, but does not establish separation from other components.','Positive radial/axial clearance is a digital fit metric, not tolerance, bearing, friction, strength, wiring or manufacturing validation.']}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--model',required=True);ap.add_argument('--info',required=True);ap.add_argument('--report',required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);r={'checker_version':VERSION,'checker_sha256':sha(__file__),'recipe_sha256':sha(recipe.__file__),'model_sha256':sha(a.model),'info_sha256':sha(a.info),'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'run_id':str(uuid.uuid4()),'passed':False}
 try:r.update(audit(a.model,a.info))
 except Exception as e:r['exception']={'type':type(e).__name__,'message':str(e)}
 for key,path in [('model_sha256',a.model),('info_sha256',a.info),('recipe_sha256',recipe.__file__),('checker_sha256',__file__)]:
  if r[key]!=sha(path):r['passed']=False;r.setdefault('identity_failures',[]).append({'file':Path(path).name,'reason':'changed_during_check'})
 Path(a.report).write_text(json.dumps(r,indent=2));print('009 ASSEMBLY',r['passed'])
 if not r['passed']:raise RuntimeError('Assembly gate failed')
