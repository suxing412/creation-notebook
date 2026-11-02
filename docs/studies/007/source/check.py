"""007 ORISON: native closed analytic-frame sweep contract and numerical geometry gate.
Reusable numerical substrate: study-006 check.py component traversal, float64 world-volume,
BVH nonadjacent candidates and bidirectional near-coplanar SAT. Family-specific constraints
here are toroidal modulo sweep, periodic analytic frame, rounded-rectangle profile, sampled
curvature/clearance and complete vertex/topology identity; no 006 folded-sheet constraints.
Raw mesh only. Not arbitrary evaluated-scene, manufacture, GPU or continuous-domain proof.
"""
import bpy,bmesh,sys,json,math,argparse,itertools,hashlib,time,uuid,datetime
from pathlib import Path
from collections import defaultdict,Counter
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
import recipe
VERSION='007-native-1.0'
FAIL_FIELDS=['degenerate_triangles','duplicate_triangles','nonmanifold_edges','non_positive_world_volume','inconsistent_winding_edges','invalid_connected_components','nonfinite_coordinates','recipe_vertex_envelope_failures','recipe_topology_failures','object_contract_failures','material_contract_failures','object_transform_failures','model_state_contract_failures','nonadjacent_self_intersection_candidates','coplanar_positive_area_overlaps','seam_topology_failures','frame_periodicity_failures','frame_metadata_failures','ring_frame_fit_failures','genus_contract_failures','curvature_radius_failures','nonlocal_centerline_clearance_failures','frame_reference_failures','input_contract_failures']
def canonical(face):
 x=tuple(face);return min(tuple(x[i:]+x[:i]) for i in range(len(x))) if x else ()
def facekey(face):return min(canonical(tuple(face)),canonical(tuple(reversed(face))))
def vec(q):return Vector(q)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sat(a,b):
 for poly in [a,b]:
  for i in range(3):
   u,w=poly[i],poly[(i+1)%3];x,y=-(w[1]-u[1]),w[0]-u[0];ln=math.hypot(x,y)
   if ln<1e-13:continue
   x/=ln;y/=ln;pa=[q[0]*x+q[1]*y for q in a];pb=[q[0]*x+q[1]*y for q in b]
   if min(max(pa),max(pb))-max(min(pa),min(pb))<=1e-8:return False
 return True

def sweep_contract(C,revision,construction,expected_v,expected_f,r):
 n=construction['station_count'];m=construction['cross_section_vertices'];stations=construction['stations'];t0=-math.pi/2
 if n!=320 or m!=36 or len(stations)!=n:r['seam_topology_failures'].append({'reason':'station_layout','station_count':n,'section_vertices':m})
 ends=[]
 for t in [t0,t0+2*math.pi]:
  T,N,B=recipe.frame(C,t,revision);ends.append({'point':recipe.point(C,t),'tangent':T,'normal':N,'binormal':B,'section':recipe.section(C,t,revision)})
 residuals={k:max(abs(x-y) for x,y in zip(ends[0][k],ends[1][k])) for k in ['point','tangent','normal','binormal']};residuals['section']=max(abs(x-y) for a,b in zip(ends[0]['section'],ends[1]['section']) for x,y in zip(a,b))
 for k,v in residuals.items():
  if v>1e-10:r['frame_periodicity_failures'].append({'quantity':k,'endpoint_residual':v})
 r['periodicity_records']={'endpoint_parameters':[t0,t0+2*math.pi],'maximum_absolute_residuals':residuals,'unique_station_count':n,'duplicated_endpoint_ring_allowed':False}
 # Independent float64 arithmetic and denser 960-point sampling, not recipe.diagnostics output.
 samples=960;pts=[];radii=[];curv=[];references=[];orthogonal=[]
 for i in range(samples):
  t=t0+2*math.pi*i/samples;p=tuple(recipe.point(C,t));v,acc=recipe.derivatives(C,t);speed=math.sqrt(math.fsum(x*x for x in v));cross=(v[1]*acc[2]-v[2]*acc[1],v[2]*acc[0]-v[0]*acc[2],v[0]*acc[1]-v[1]*acc[0]);k=math.sqrt(math.fsum(x*x for x in cross))/speed**3;radius=max(math.hypot(x,y) for x,y in recipe.section(C,t,revision));T,N,B=recipe.frame(C,t,revision);vectors=[T,N,B];err=max([abs(math.fsum(x*x for x in q)-1) for q in vectors]+[abs(math.fsum(x*y for x,y in zip(vectors[a],vectors[b]))) for a,b in [(0,1),(0,2),(1,2)]]);hand=(vec(T).cross(vec(N))-vec(B)).length
  if err>1e-10 or hand>2e-7:orthogonal.append({'sample':i,'orthonormal_residual':err,'handedness_residual':hand})
  pts.append(p);radii.append(radius);curv.append(k);references.append(math.hypot(T[0],T[2]))
 if orthogonal:r['frame_periodicity_failures'].append({'reason':'frame_orthonormality_or_handedness','samples':orthogonal[:20],'count':len(orthogonal)})
 products=[k*q for k,q in zip(curv,radii)];maximum=max(products)
 if maximum>=.72:r['curvature_radius_failures'].append({'maximum':maximum,'required_less_than':.72})
 if min(references)<.65:r['frame_reference_failures'].append({'minimum_reference_sine':min(references),'required_at_least':.65})
 dist=lambda a,b:math.sqrt(math.fsum((x-y)**2 for x,y in zip(a,b)))
 lengths=[dist(pts[i],pts[(i+1)%samples]) for i in range(samples)];total=math.fsum(lengths);arc=[0.]
 for length in lengths[:-1]:arc.append(arc[-1]+length)
 excluded=2.8*max(radii);minimum=float('inf');pair=None;tested=0
 for i in range(samples):
  for j in range(i+1,samples):
   ds=min(arc[j]-arc[i],total-(arc[j]-arc[i]))
   if ds<=excluded:continue
   tested+=1;gap=dist(pts[i],pts[j])-radii[i]-radii[j]
   if gap<minimum:minimum=gap;pair=[i,j]
 if minimum<.006:r['nonlocal_centerline_clearance_failures'].append({'sampled_gap_m':minimum,'required_at_least_m':.006,'pair':pair})
 r['independent_sampling']={'samples':samples,'max_curvature_radius_product':maximum,'max_curvature_per_m':max(curv),'max_section_circumradius_m':max(radii),'minimum_reference_sine':min(references),'sampled_nonlocal_clearance_m':minimum,'closest_pair':pair,'tested_nonlocal_pairs':tested,'local_arc_exclusion_m':excluded,'centerline_length_m':total,'method':'Independent float64 arithmetic; analytic recipe point/derivatives/profile evaluated on 960 periodic parameters. Not a continuous proof.'}
 return n,m

def run(a,r):
 info=json.loads(Path(a.info).read_text());C=info['config'];revision=info['construction']['revision'];r['variant']=C['name'];r['recipe_version']=info['recipe_version'];r['info_sha256']=sha(a.info)
 try:recipe.validate(C,bpy.app.version,revision=revision,check_geometry=False)
 except Exception as e:r['input_contract_failures'].append({'reason':str(e)});return
 expected_v,expected_f,construction=recipe.geometry(C,revision);n,m=sweep_contract(C,revision,construction,expected_v,expected_f,r)
 metadata=info['construction']
 for key in ['station_count','cross_section_vertices','corner_steps','seam_station']:
  if metadata.get(key)!=construction.get(key):r['frame_metadata_failures'].append({'reason':'construction_mismatch','key':key})
 if len(metadata.get('stations',[]))!=n:r['frame_metadata_failures'].append({'reason':'station_count'})
 else:
  for i,(actual,expected) in enumerate(zip(metadata['stations'],construction['stations'])):
   for key in ['center','tangent','normal','binormal']:
    q=actual.get(key,[])
    if len(q)!=3 or any(not math.isfinite(x) for x in q) or max(abs(x-y) for x,y in zip(q,expected[key]))>1e-10:r['frame_metadata_failures'].append({'station':i,'quantity':key})
   if not math.isfinite(actual.get('t',float('nan'))) or abs(actual['t']-expected['t'])>1e-12:r['frame_metadata_failures'].append({'station':i,'quantity':'t'})
 bpy.ops.wm.open_mainfile(filepath=a.model);obs=sorted([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:o.name);r['mesh_objects']=len(obs);all_objects=list(bpy.data.objects)
 if len(all_objects)!=1:r['model_state_contract_failures'].append({'reason':'object_count_not_one','actual':len(all_objects)})
 for candidate in all_objects:
  if candidate.type!='MESH':r['model_state_contract_failures'].append({'object':candidate.name,'reason':'non_mesh_object','type':candidate.type})
 if len(obs)!=1:r['object_contract_failures'].append({'required':1,'actual':len(obs)})
 D={};triangles=[];facekeys={};expected_faces=Counter(facekey(q) for q in expected_f);ring_records=[];component_records=[]
 for ob in obs:
  for attr,reason in [('modifiers','modifiers_present'),('constraints','constraints_present')]:
   if len(getattr(ob,attr)):r['model_state_contract_failures'].append({'object':ob.name,'reason':reason,'types':[q.type for q in getattr(ob,attr)]})
  if ob.data.shape_keys is not None:r['model_state_contract_failures'].append({'object':ob.name,'reason':'shape_keys_present'})
  if ob.parent is not None:r['model_state_contract_failures'].append({'object':ob.name,'reason':'parent_present'})
  for owner,label in [(ob,'object'),(ob.data,'mesh')]:
   animation=getattr(owner,'animation_data',None)
   if animation is not None:r['model_state_contract_failures'].append({'object':ob.name,'reason':'animation_data_present','owner':label,'drivers':len(animation.drivers)})
  if any(not math.isfinite(float(ob.matrix_world[i][j])) or abs(float(ob.matrix_world[i][j])-(1 if i==j else 0))>1e-8 for i in range(4) for j in range(4)):r['object_transform_failures'].append({'object':ob.name,'required':'identity world matrix'})
  me=ob.data;me.calc_loop_triangles();v=[ob.matrix_world@x.co for x in me.vertices];t=[tuple(x.vertices) for x in me.loop_triangles];badcoords=[[i,k] for i,q in enumerate(v) for k,c in enumerate(q) if not math.isfinite(c)]
  if badcoords:r['nonfinite_coordinates'].append({'object':ob.name,'coordinates':badcoords});continue
  if len(me.materials)!=1:r['material_contract_failures'].append({'object':ob.name,'material_count':len(me.materials),'required':1})
  if len(v)!=len(expected_v):r['recipe_vertex_envelope_failures'].append({'object':ob.name,'vertex_count':len(v),'expected':len(expected_v)})
  badv=[{'index':i,'distance_m':(q-vec(expected_v[i])).length} for i,q in enumerate(v[:len(expected_v)]) if (q-vec(expected_v[i])).length>2e-7]
  if badv:r['recipe_vertex_envelope_failures'].append({'object':ob.name,'off_recipe_vertices':badv[:64],'count':len(badv),'tolerance_m':2e-7})
  actual_faces=Counter(facekey(tuple(q.vertices)) for q in me.polygons)
  if actual_faces!=expected_faces:r['recipe_topology_failures'].append({'object':ob.name,'actual_polygons':len(me.polygons),'expected_polygons':len(expected_f),'identical_unoriented_index_cycles':False})
  edge_faces=defaultdict(list)
  for fi,poly in enumerate(me.polygons):
   f=tuple(poly.vertices)
   for j in range(len(f)):edge_faces[tuple(sorted((f[j],f[(j+1)%len(f)])))].append(fi)
  seam_bad=[]
  for j in range(m):
   edge=tuple(sorted(((n-1)*m+j,j)))
   if len(edge_faces.get(edge,[]))!=2:seam_bad.append({'edge':edge,'face_incidence':len(edge_faces.get(edge,[]))})
   face=((n-1)*m+j,(n-1)*m+(j+1)%m,(j+1)%m,j)
   if actual_faces[facekey(face)]!=1:seam_bad.append({'face':face,'multiplicity':actual_faces[facekey(face)]})
  if seam_bad:r['seam_topology_failures'].append({'object':ob.name,'reason':'modulo_seam_adjacency','failures':seam_bad})
  if len(v)>=n*m:
   centers=[];maxfit=0.;maxcenter=0.;maxaxes=0.
   for i,s in enumerate(construction['stations']):
    ring=v[i*m:(i+1)*m];center=sum(ring,Vector())/m;centers.append(center);profile=recipe.section(C,s['t'],revision);xx=sum(x*x for x,y in profile);yy=sum(y*y for x,y in profile);xy=sum(x*y for x,y in profile);det=xx*yy-xy*xy;vx=sum(((q-center)*x for q,(x,y) in zip(ring,profile)),Vector());vy=sum(((q-center)*y for q,(x,y) in zip(ring,profile)),Vector());N=(vx*yy-vy*xy)/det;B=(vy*xx-vx*xy)/det;fit=max((q-(center+N*x+B*y)).length for q,(x,y) in zip(ring,profile));ce=(center-vec(s['center'])).length;axes=max((N-vec(s['normal'])).length,(B-vec(s['binormal'])).length);maxfit=max(maxfit,fit);maxcenter=max(maxcenter,ce);maxaxes=max(maxaxes,axes)
    if fit>2e-7 or ce>2e-7 or axes>2e-5:r['ring_frame_fit_failures'].append({'station':i,'fit_residual_m':fit,'center_residual_m':ce,'normal_binormal_residual':axes})
   duplicate_end=(centers[0]-centers[-1]).length<=2e-7
   if duplicate_end:r['seam_topology_failures'].append({'reason':'duplicated_endpoint_ring'})
   ring_records.append({'object':ob.name,'max_profile_fit_residual_m':maxfit,'max_center_residual_m':maxcenter,'max_normal_binormal_residual':maxaxes,'last_to_first_center_distance_m':(centers[0]-centers[-1]).length,'seam_connecting_edges':m,'duplicate_endpoint_ring':duplicate_end})
  bm=bmesh.new();bm.from_mesh(me);bad=sum(not e.is_manifold for e in bm.edges);flipped=sum(e.is_manifold and not e.is_contiguous for e in bm.edges)
  if flipped:r['inconsistent_winding_edges'].append({'object':ob.name,'count':flipped})
  if bad:r['nonmanifold_edges'].append({'object':ob.name,'count':bad})
  local_volume=bm.calc_volume(signed=True);world_volume=math.fsum(float(v[a].x)*(float(v[b].y)*float(v[c].z)-float(v[b].z)*float(v[c].y))+float(v[a].y)*(float(v[b].z)*float(v[c].x)-float(v[b].x)*float(v[c].z))+float(v[a].z)*(float(v[b].x)*float(v[c].y)-float(v[b].y)*float(v[c].x)) for a,b,c in t)/6
  if world_volume<=0:r['non_positive_world_volume'].append({'object':ob.name,'signed_world_volume_m3':world_volume,'signed_local_volume_m3':local_volume})
  bm.verts.ensure_lookup_table();seen=set();component_sizes=[]
  for root in bm.verts:
   if root.index in seen:continue
   stack=[root];seen.add(root.index);count=0
   while stack:
    q=stack.pop();count+=1
    for e in q.link_edges:
     other=e.other_vert(q)
     if other.index not in seen:seen.add(other.index);stack.append(other)
   component_sizes.append(count)
  chi=len(bm.verts)-len(bm.edges)+len(bm.faces)
  if chi!=0:r['genus_contract_failures'].append({'object':ob.name,'euler_characteristic':chi,'required':0})
  if len(component_sizes)!=1:r['invalid_connected_components'].append({'object':ob.name,'connected_components':len(component_sizes),'component_sizes':component_sizes,'required':1})
  component_records.append({'object':ob.name,'component_sizes':component_sizes,'signed_world_volume_m3':world_volume,'signed_local_volume_m3':local_volume,'vertices':len(bm.verts),'edges':len(bm.edges),'faces':len(bm.faces),'euler_characteristic':chi,'genus_if_closed_connected_orientable':(2-chi)/2 if not bad and not flipped and len(component_sizes)==1 else None});bm.free();tree=BVHTree.FromPolygons(v,t,all_triangles=True,epsilon=0);D[ob.name]=(v,t,tree)
  for k,tt in enumerate(t):
   pts=[tuple(float(c) for c in v[i]) for i in tt];u=[pts[1][j]-pts[0][j] for j in range(3)];w=[pts[2][j]-pts[0][j] for j in range(3)];normal=[u[1]*w[2]-u[2]*w[1],u[2]*w[0]-u[0]*w[2],u[0]*w[1]-u[1]*w[0]];ln=math.sqrt(sum(q*q for q in normal));area=ln/2
   if area<1e-12:r['degenerate_triangles'].append([ob.name,k,area]);continue
   key=tuple(sorted(tuple(round(c,8) for c in pt) for pt in pts))
   if key in facekeys:r['duplicate_triangles'].append([facekeys[key],[ob.name,k]])
   facekeys[key]=[ob.name,k];normal=tuple(q/ln for q in normal);d=sum(normal[j]*pts[0][j] for j in range(3));bbox=tuple((min(q[j] for q in pts),max(q[j] for q in pts)) for j in range(3));triangles.append((ob.name,k,tt,pts,normal,d,bbox,area))
  for i,j in tree.overlap(tree):
   if i<j and not set(t[i])&set(t[j]):r['nonadjacent_self_intersection_candidates'].append([ob.name,i,j])
 for oa,ob in itertools.combinations(D,2):
  for i,j in D[oa][2].overlap(D[ob][2]):r['nonadjacent_self_intersection_candidates'].append([oa,i,ob,j])
 spatial=defaultdict(list);cell=.012;plane_tol=5e-8;candidates_count=0
 for i,x in enumerate(triangles):
  keys=list(itertools.product(*(range(math.floor((lo-plane_tol)/cell),math.floor((hi+plane_tol)/cell)+1) for lo,hi in x[6])));candidates=set(j for key in keys for j in spatial[key])
  for j in candidates:
   y=triangles[j]
   if any(min(x[6][k][1],y[6][k][1])-max(x[6][k][0],y[6][k][0])< -plane_tol for k in range(3)):continue
   if abs(sum(x[4][k]*y[4][k] for k in range(3)))<1-1e-7:continue
   if max(abs(sum(x[4][k]*q[k] for k in range(3))-x[5]) for q in y[3])>plane_tol:continue
   if max(abs(sum(y[4][k]*q[k] for k in range(3))-y[5]) for q in x[3])>plane_tol:continue
   candidates_count+=1;axis=max(range(3),key=lambda k:abs(x[4][k]));axes=[k for k in range(3) if k!=axis];A=[tuple(q[k] for k in axes) for q in x[3]];B=[tuple(q[k] for k in axes) for q in y[3]]
   if x[0]==y[0] and len(set(x[2])&set(y[2]))==2:
    common=set(x[2])&set(y[2]);pts=dict(zip(x[2],A));pts.update(zip(y[2],B));u,w=[pts[c] for c in common];xa=pts[next(c for c in x[2] if c not in common)];ya=pts[next(c for c in y[2] if c not in common)];cross=lambda q:(w[0]-u[0])*(q[1]-u[1])-(w[1]-u[1])*(q[0]-u[0])
    if cross(xa)*cross(ya)<=0:continue
   if any(min(max(q[k] for q in A),max(q[k] for q in B))-max(min(q[k] for q in A),min(q[k] for q in B))<=1e-8 for k in range(2)):continue
   if sat(A,B):r['coplanar_positive_area_overlaps'].append([[x[0],x[1]],[y[0],y[1]]])
  for key in keys:spatial[key].append(i)
 r.update({'triangles':sum(len(x[1]) for x in D.values()),'minimum_triangle_area_m2':min((x[7] for x in triangles),default=None),'component_records':component_records,'ring_frame_records':ring_records,'coplanar_candidate_pairs':candidates_count})

def main():
 p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--report',required=True);p.add_argument('--info',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);start=time.time();r={k:[] for k in FAIL_FIELDS};r.update({'checker_version':VERSION,'checker_sha256':sha(__file__),'recipe_sha256':sha(recipe.__file__),'model_sha256':sha(a.model),'file':Path(a.model).name,'run_id':str(uuid.uuid4()),'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'blender_version':bpy.app.version_string,'passed':False,'limits':['Full-vertex/topology identity is a restricted recipe contract, not general geometry proof or reindexing equivalence.','BVH candidates exclude triangles sharing any vertex; noncoplanar adjacent foldover is not fully independently certified.','Frame is periodic analytic fixed-reference projection, not RMF. Station profile fits use raw float32 mesh vertices.','Curvature and nonlocal clearance are finite 960-sample numerical tests. Local arc neighborhoods <=2.8 max circumradius are excluded. No continuous curve, swept-volume or parameter-domain proof.','Near-coplanar overlaps use bidirectional float64 plane distances and projected SAT, not exact symbolic predicates or dynamic z-fighting validation.','Exactly one raw mesh object, no modifiers, shape keys, parents, constraints, object/mesh animation or drivers; photographic scene.blend is out of scope.','No GPU, WebGL, dynamic flicker, physical iPhone, manufacture, load, stability or ergonomics verification.'],'thresholds':{'vertex_distance_m':2e-7,'frame_fit_m':2e-7,'frame_axis_residual':2e-5,'frame_endpoint_residual':1e-10,'triangle_area_m2':1e-12,'duplicate_vertex_round_m':1e-8,'identity_matrix_entry':1e-8,'coplanar_normal_cosine':1-1e-7,'bidirectional_plane_distance_m':5e-8,'positive_projected_overlap_m':1e-8,'spatial_cell_m':.012,'curvature_radius_max_exclusive':.72,'sampled_nonlocal_clearance_m_min':.006}})
 try:run(a,r);r['passed']=not any(r[k] for k in FAIL_FIELDS)
 except Exception as e:r['internal_error']={'type':type(e).__name__,'message':str(e)};r['passed']=False
 r['elapsed_seconds']=round(time.time()-start,3);Path(a.report).parent.mkdir(parents=True,exist_ok=True);Path(a.report).write_text(json.dumps(r,indent=2,ensure_ascii=False));print('007 NATIVE',r['passed'],'failures',{k:len(r[k]) for k in FAIL_FIELDS if r[k]},'error',r.get('internal_error'),'seconds',r['elapsed_seconds'])
 if not r['passed']:raise RuntimeError('007 native gate rejected; see report')
if __name__=='__main__':main()
