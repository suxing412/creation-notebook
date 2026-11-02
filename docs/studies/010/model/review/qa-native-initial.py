"""010 independent native/decoded-export numerical gate. Not GPU/engineering certification."""
import bpy,bmesh,math,json,argparse,sys,itertools,hashlib,datetime,uuid
from pathlib import Path
from collections import Counter,defaultdict
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
import audit_payload
VERSION='010-native-1.0'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def cycle(x):x=tuple(x);return min(x[i:]+x[:i]for i in range(len(x)))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def dot(a,b):return math.fsum(x*y for x,y in zip(a,b))
def cross(a,b):return(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def length(a):return math.sqrt(dot(a,a))
def area(t):return length(cross(sub(t[1],t[0]),sub(t[2],t[0])))/2

def inside_triangle(p,t,eps=2e-9):
 u=sub(t[1],t[0]);v=sub(t[2],t[0]);w=sub(p,t[0]);uu=dot(u,u);vv=dot(v,v);uv=dot(u,v);wu=dot(w,u);wv=dot(w,v);d=uu*vv-uv*uv
 if d<=1e-30:return False
 s=(wu*vv-wv*uv)/d;q=(wv*uu-wu*uv)/d
 return s>=-eps and q>=-eps and s+q<=1+eps

def intersection_points(a,b):
 """Noncoplanar triangle intersection segment endpoints, float64; tolerance not exact predicates."""
 pts=[]
 for source,target in [(a,b),(b,a)]:
  n=cross(sub(target[1],target[0]),sub(target[2],target[0]));ln=length(n)
  if ln<1e-16:continue
  n=tuple(x/ln for x in n)
  for p,q in zip(source,source[1:]+source[:1]):
   dp=dot(n,sub(p,target[0]));dq=dot(n,sub(q,target[0]));den=dp-dq
   if abs(dp)<=1e-8 and inside_triangle(p,target):pts.append(p)
   if abs(den)>1e-14:
    t=dp/den
    if -1e-10<=t<=1+1e-10:
     hit=tuple(p[k]+t*(q[k]-p[k])for k in range(3))
     if inside_triangle(hit,target):pts.append(hit)
 return pts

def clip_area(a,b):
 """Positive area of near-coplanar projected triangles; zero for shared edge/point."""
 na=cross(sub(a[1],a[0]),sub(a[2],a[0]));nb=cross(sub(b[1],b[0]),sub(b[2],b[0]));la=length(na);lb=length(nb)
 if min(la,lb)<1e-16:return 0
 na=tuple(x/la for x in na);nb=tuple(x/lb for x in nb)
 if abs(dot(na,nb))<1-1e-7:return 0
 if max(abs(dot(na,sub(q,a[0])))for q in b)>5e-8 or max(abs(dot(nb,sub(q,b[0])))for q in a)>5e-8:return 0
 axes=[k for k in range(3)if k!=max(range(3),key=lambda k:abs(na[k]))]
 A=[tuple(q[k]for k in axes)for q in a];B=[tuple(q[k]for k in axes)for q in b]
 def cp(u,v):return u[0]*v[1]-u[1]*v[0]
 orient=1 if cp(sub(B[1],B[0]),sub(B[2],B[0]))>0 else -1
 for p,q in zip(B,B[1:]+B[:1]):
  clipped=[];edge=sub(q,p)
  for s,e in zip(A,A[1:]+A[:1]):
   ds=orient*cp(edge,sub(s,p));de=orient*cp(edge,sub(e,p));si=ds>=0;ei=de>=0
   if si!=ei:
    t=ds/(ds-de);clipped.append(tuple(s[k]+t*(e[k]-s[k])for k in range(2)))
   if ei:clipped.append(e)
  A=clipped
  if not A:return 0
 return abs(math.fsum(p[0]*q[1]-p[1]*q[0]for p,q in zip(A,A[1:]+A[:1])))/2

def allowed(point,pair,regions):
 for r in regions:
  if set(r.get('objects',[]))!=set(pair):continue
  if r.get('kind')=='box':
   if all(r['min'][k]-2e-7<=point[k]<=r['max'][k]+2e-7 for k in range(3)):return r.get('id','local_box')
  elif r.get('kind')=='sphere':
   if length(sub(point,r['center']))<=r['radius']+2e-7:return r.get('id','local_sphere')
  elif r.get('kind')=='cylinder':
   axis=r['axis'];q=sub(point,r['center']);t=dot(q,axis);rad=length(tuple(q[k]-t*axis[k]for k in range(3)))
   if r['axial_min']-2e-7<=t<=r['axial_max']+2e-7 and rad<=r['radius']+2e-7:return r.get('id','local_cylinder')
 return None

def point_inside(point,tree):
 nearest=tree.find_nearest(Vector(point))
 if nearest[0] is not None and nearest[3]<2e-7:return False
 votes=[]
 for direction in [(0.7421,0.5113,0.4327),(-0.3121,0.8759,0.3683),(0.4153,-0.2271,0.8809)]:
  d=Vector(direction).normalized();origin=Vector(point);hits=0
  for _ in range(10000):
   hit,normal,index,distance=tree.ray_cast(origin,d,100)
   if hit is None:break
   hits+=1;origin=hit+d*1e-7
  else:return None
  votes.append(hits%2==1)
 return votes[0] if len(set(votes))==1 else None

def contact_contract(info):
 """010 slotted family accepts no region-based intersection waivers."""
 errors=[]
 if info.get('contact_regions',[]):errors.append({'code':'contact_region_contract','message':'010 forbids metadata intersection waivers; slots must be physically clear'})
 return errors

def run(model,glb,info_path):
 info=json.loads(Path(info_path).read_text());regions=[];bpy.ops.wm.open_mainfile(filepath=str(Path(model).resolve()));obs=sorted([o for o in bpy.data.objects if o.type=='MESH'],key=lambda q:q.name)
 failures=[];records=[];D={};native={};duplicate={};coplanar=[];selfhits=[];crosshits=[];accepted=[]
 def fail(code,detail):failures.append({'code':code,**detail})
 failures.extend(contact_contract(info))
 if info.get('study')=='010':
  declared={q['name']for q in info.get('parts',[])}
  if declared!={q.name for q in obs}:fail('parts_metadata',{'declared':sorted(declared),'actual':[q.name for q in obs]})
 if len(obs)!=len(bpy.data.objects):fail('non_mesh_objects',{'count':len(bpy.data.objects)-len(obs)})
 for ob in obs:
  me=ob.data
  if ob.modifiers or ob.constraints or ob.parent or me.shape_keys or ob.animation_data or me.animation_data:fail('model_state',{'object':ob.name})
  if any(abs(ob.matrix_world[i][j]-(i==j))>1e-8 for i in range(4)for j in range(4)):fail('unbaked_transform',{'object':ob.name})
  me.calc_loop_triangles();v=[tuple(float(x)for x in ob.matrix_world@q.co)for q in me.vertices];tris=[tuple(t.vertices)for t in me.loop_triangles];polys=[tuple(p.vertices)for p in me.polygons]
  if any(not math.isfinite(x)for q in v for x in q):fail('nonfinite',{'object':ob.name});continue
  bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bad=sum(not e.is_manifold for e in bm.edges);flip=sum(e.is_manifold and not e.is_contiguous for e in bm.edges);seen=set();components=[]
  for root in bm.verts:
   if root.index in seen:continue
   stack=[root];seen.add(root.index);component=[]
   while stack:
    p=stack.pop();component.append(p.index)
    for e in p.link_edges:
     q=e.other_vert(p)
     if q.index not in seen:seen.add(q.index);stack.append(q)
   components.append(component)
  volume=math.fsum(dot(v[a],cross(v[b],v[c]))for a,b,c in tris)/6
  if bad:fail('nonmanifold',{'object':ob.name,'count':bad})
  if flip:fail('winding',{'object':ob.name,'count':flip})
  if volume<=0:fail('world_volume',{'object':ob.name,'signed_m3':volume})
  if len(components)!=1:fail('components',{'object':ob.name,'count':len(components)})
  degenerate=[];minimum=float('inf')
  for ti,t in enumerate(tris):
   points=[v[i]for i in t];ar=area(points);minimum=min(minimum,ar)
   if ar<1e-12:degenerate.append(ti)
   key=tuple(sorted(points))
   if key in duplicate:fail('duplicate_triangle',{'first':duplicate[key],'second':[ob.name,ti]})
   duplicate[key]=[ob.name,ti]
  if degenerate:fail('degenerate',{'object':ob.name,'count':len(degenerate),'indices':degenerate[:12]})
  records.append({'name':ob.name,'vertices':len(v),'polygons':len(polys),'triangles':len(tris),'nonmanifold_edges':bad,'inconsistent_edges':flip,'signed_world_volume_m3':volume,'component_count':len(components),'euler_characteristic':len(bm.verts)-len(bm.edges)+len(bm.faces),'minimum_triangle_area_m2':minimum});bm.free()
  tree=BVHTree.FromPolygons([Vector(q)for q in v],tris,all_triangles=True,epsilon=0);D[ob.name]=(v,tris,tree,components)
  native[ob.name]=Counter(cycle([(v[i][0],v[i][2],-v[i][1])for i in t])for t in tris)
  for i,j in tree.overlap(tree):
   if i>=j:continue
   A=[v[k]for k in tris[i]];B=[v[k]for k in tris[j]];overlap=clip_area(A,B)
   # Positive coplanarity is independently checked below; BVH misses some exact cases.
   if not set(tris[i])&set(tris[j]):selfhits.append({'object':ob.name,'triangles':[i,j]})
 for an,bn in itertools.combinations(D,2):
  av,at,ab,ac=D[an];bv,bt,bb,bc=D[bn]
  overlaps=ab.overlap(bb)
  if not overlaps:
   for inside_name,points,components,outside_name,tree in [(an,av,ac,bn,bb),(bn,bv,bc,an,ab)]:
    for component in components:
     point=points[component[0]];result=point_inside(point,tree)
     if result is None:fail('containment_uncertain',{'objects':[inside_name,outside_name],'point':point})
     elif result and not all(allowed(points[i],(an,bn),regions)for i in component):fail('unclassified_containment',{'objects':[inside_name,outside_name],'component_vertices':len(component),'representative':point})
  for i,j in overlaps:
   A=[av[k]for k in at[i]];B=[bv[k]for k in bt[j]];overlap=clip_area(A,B)
   # Coplanarity checked by independent spatial scan below.
   pts=intersection_points(A,B);where=[allowed(p,(an,bn),regions)for p in pts]
   record={'objects':[an,bn],'triangles':[i,j],'intersection_points':pts,'local_region_ids':where}
   if pts and all(where) and overlap<=1e-12:accepted.append(record)
   else:crosshits.append(record)
 # Independent spatial coplanarity scan does not rely on BVH overlap semantics.
 spatial=defaultdict(list);flat=[];cell=.02;plane_tol=5e-8
 for name,(vertices,triangles,tree,components) in D.items():
  for ti,tri in enumerate(triangles):
   points=[vertices[i]for i in tri];normal=cross(sub(points[1],points[0]),sub(points[2],points[0]));ln=length(normal)
   if ln<2e-12:continue
   normal=tuple(x/ln for x in normal);bb=[(min(p[k]for p in points),max(p[k]for p in points))for k in range(3)];keys=list(itertools.product(*(range(math.floor((lo-plane_tol)/cell),math.floor((hi+plane_tol)/cell)+1)for lo,hi in bb)));candidates=set(j for key in keys for j in spatial[key])
   for j in candidates:
    other_name,other_ti,other_points,other_normal,other_bb=flat[j]
    if any(min(bb[k][1],other_bb[k][1])-max(bb[k][0],other_bb[k][0]) < -plane_tol for k in range(3)):continue
    if abs(dot(normal,other_normal))<1-1e-7:continue
    overlap=clip_area(points,other_points)
    if overlap>1e-12:coplanar.append({'objects':[other_name,name],'triangles':[other_ti,ti],'projected_overlap_m2':overlap})
   index=len(flat);flat.append((name,ti,points,normal,bb))
   for key in keys:spatial[key].append(index)
 if selfhits:fail('self_intersection_candidates',{'count':len(selfhits),'examples':selfhits[:12]})
 if crosshits:fail('unclassified_interobject_intersections',{'count':len(crosshits),'examples':crosshits[:16]})
 if coplanar:fail('coplanar_positive_area',{'count':len(coplanar),'examples':coplanar[:16]})
 # GLB validation plus named-object exact oriented coordinate multiset equality.
 payload={};comparison=[]
 try:
  j,meshes,payload=audit_payload.decode(glb);exported={};nodes=j['nodes'];roots=j['scenes'][0].get('nodes',[]);visited=set()
  def walk(ni):
   if type(ni)is not int or not 0<=ni<len(nodes)or ni in visited:raise audit_payload.Reject('node_tree','Invalid/repeated node')
   visited.add(ni);n=nodes[ni]
   for key,identity in [('translation',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1]),('matrix',[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1])]:
    if key in n and n[key]!=identity:raise audit_payload.Reject('node_transform','Baked identity transforms required')
   if 'mesh'in n:
    mi=n['mesh'];audit_payload.require(type(mi)is int and 0<=mi<len(meshes),'mesh_reference','Bad mesh reference');name=n.get('name');audit_payload.require(name not in exported,'duplicate_node_name',str(name));count=Counter()
    for p in meshes[mi]:
     for t in p['triangles']:
      points=[p['positions'][i]for i in t];audit_payload.require(area(points)>1e-12,'export_degenerate',str(name));count[cycle(points)]+=1
    exported[name]=count
   for ch in n.get('children',[]):walk(ch)
  for n in roots:walk(n)
  if visited!=set(range(len(nodes))):fail('unused_nodes',{'count':len(nodes)-len(visited)})
  if set(exported)!=set(native):fail('export_object_names',{'native':list(native),'exported':list(exported)})
  comparison=[]
  for name in native:
   other=exported.get(name,Counter());missing=native[name]-other;extra=other-native[name];comparison.append({'object':name,'native_triangles':sum(native[name].values()),'export_triangles':sum(other.values()),'missing':sum(missing.values()),'extra':sum(extra.values()),'exact_oriented_coordinate_multisets_equal':not missing and not extra})
   if missing or extra:fail('export_geometry_mismatch',{'object':name,'missing':sum(missing.values()),'extra':sum(extra.values())})
 except Exception as e:
  fail(getattr(e,'code','glb_exception'),{'type':type(e).__name__,'message':str(e)})
 return {'passed':not failures,'failures':failures,'objects':records,'decoded_glb':payload,'export_comparison':comparison,'bvh_self_candidates':selfhits,'unclassified_pair_candidates':crosshits,'coplanar_overlaps':coplanar,'locally_accepted_intersections':accepted,'contact_regions_used':regions,'limits':['Float64 numerical triangles and float32 Blender BVH; not exact computational predicates.','Vertex/edge topology is not compared across GLB split vertices; actual oriented coordinate triangle multiplicities are.','No-boundary components tested by three-ray parity; ambiguous parity rejects. Surface contact classification uses numerical tolerances.','No shader equivalence, GPU rendering, real phone, physical stability, load, electrical or manufacture verification.']}

def main():
 p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--glb',required=True);p.add_argument('--info',required=True);p.add_argument('--report',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);r={'checker_version':VERSION,'checker_sha256':sha(__file__),'payload_checker_sha256':sha(audit_payload.__file__),'run_id':str(uuid.uuid4()),'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'model_sha256':sha(a.model),'glb_sha256':sha(a.glb),'info_sha256':sha(a.info),'passed':False}
 try:r.update(run(a.model,a.glb,a.info))
 except Exception as e:r.update({'passed':False,'exception':{'type':type(e).__name__,'code':getattr(e,'code',None),'message':str(e)}})
 for k,path in [('model_sha256',a.model),('glb_sha256',a.glb),('info_sha256',a.info),('checker_sha256',__file__),('payload_checker_sha256',audit_payload.__file__)]:
  if r[k]!=sha(path):r['passed']=False;r.setdefault('failures',[]).append({'code':'input_changed_during_check','file':Path(path).name})
 Path(a.report).parent.mkdir(parents=True,exist_ok=True);Path(a.report).write_text(json.dumps(r,indent=2));print('010 independent audit',r['passed'],len(r.get('failures',[])))
 if not r['passed']:raise RuntimeError('010 audit rejected; see report')
if __name__=='__main__':main()
