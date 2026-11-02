"""FOLIO recipe-specific native mesh gate. Numerical tests, not exact geometry or fabrication certification.
Inherited 005 fixes: components, local winding, finite full-vertex envelope, float64 coplanar planes.
006 has ONE shell: there are no allowed assembly pairs and no blanket collision exceptions.
"""
import bpy,bmesh,sys,json,math,argparse,itertools,hashlib,time
from pathlib import Path
from collections import defaultdict
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent));import recipe
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--report',required=True);p.add_argument('--info',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);start=time.time();info=json.loads(Path(a.info).read_text());C=info['config'];recipe.validate(C,bpy.app.version);bpy.ops.wm.open_mainfile(filepath=a.model)
obs=sorted([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:o.name)
D={};facekeys={};triangles=[];duplicate=[];degenerate=[];nonmanifold=[];selfhits=[];negative=[];components=[];winding=[];nonfinite=[];envelope=[];topology=[];object_contract=[];material_contract=[];transform_contract=[];model_state=[];component_records=[]
all_objects=list(bpy.data.objects)
if len(all_objects)!=1:model_state.append({'reason':'object_count_not_one','actual':len(all_objects),'required':1})
for candidate in all_objects:
 if candidate.type!='MESH':model_state.append({'object':candidate.name,'reason':'non_mesh_object','type':candidate.type})
if len(obs)!=1:object_contract.append({'expected_mesh_count':1,'actual':len(obs)})
expected_v,expected_f,construction=recipe.geometry(C,info['construction']['revision'])
def canonical(face):
 # Cyclic starts/winding ignored here; winding is independently checked on every two-manifold edge.
 x=tuple(face);return min(tuple(x[i:]+x[:i]) for i in range(len(x))) if x else ()
def facekey(face):return min(canonical(tuple(face)),canonical(tuple(reversed(face))))
expected_faces=sorted(facekey(q) for q in expected_f)
all_finite=True
for ob in obs:
 if len(ob.modifiers):model_state.append({'object':ob.name,'reason':'modifiers_present','types':[m.type for m in ob.modifiers]})
 if ob.data.shape_keys is not None:model_state.append({'object':ob.name,'reason':'shape_keys_present','key_blocks':len(ob.data.shape_keys.key_blocks)})
 if len(ob.constraints):model_state.append({'object':ob.name,'reason':'constraints_present','types':[q.type for q in ob.constraints]})
 if ob.parent is not None:model_state.append({'object':ob.name,'reason':'parent_present'})
 for owner,label in [(ob,'object'),(ob.data,'mesh')]:
  animation=getattr(owner,'animation_data',None)
  if animation is not None:
   model_state.append({'object':ob.name,'reason':'animation_data_present','owner':label})
   if len(animation.drivers):model_state.append({'object':ob.name,'reason':'drivers_present','owner':label,'count':len(animation.drivers)})
 if any(abs(float(ob.matrix_world[i][j])-(1 if i==j else 0))>1e-8 for i in range(4) for j in range(4)):
  transform_contract.append({'object':ob.name,'required':'identity world matrix','actual_matrix':[list(row) for row in ob.matrix_world]})
 me=ob.data;me.calc_loop_triangles();v=[ob.matrix_world@x.co for x in me.vertices];t=[tuple(x.vertices) for x in me.loop_triangles]
 badcoords=[[i,k] for i,q in enumerate(v) for k,c in enumerate(q) if not math.isfinite(c)]
 if badcoords:nonfinite.append({'object':ob.name,'coordinates':badcoords});all_finite=False;continue
 if len(me.materials)!=1:material_contract.append({'object':ob.name,'material_count':len(me.materials),'required':1})
 if len(v)!=len(expected_v):envelope.append({'object':ob.name,'vertex_count':len(v),'expected':len(expected_v)})
 badv=[{'index':i,'distance_m':(q-Vector(expected_v[i])).length} for i,q in enumerate(v[:len(expected_v)]) if (q-Vector(expected_v[i])).length>2e-7]
 if badv:envelope.append({'object':ob.name,'off_recipe_vertices':badv,'tolerance_m':2e-7})
 actual_faces=sorted(facekey(tuple(q.vertices)) for q in me.polygons)
 if actual_faces!=expected_faces:topology.append({'object':ob.name,'actual_polygons':len(actual_faces),'expected_polygons':len(expected_faces),'identical_unoriented_index_cycles':False})
 bm=bmesh.new();bm.from_mesh(me);bad=sum(not e.is_manifold for e in bm.edges);flipped=sum(e.is_manifold and not e.is_contiguous for e in bm.edges)
 if flipped:winding.append({'object':ob.name,'inconsistent_winding_edges':flipped})
 if bad:nonmanifold.append({'object':ob.name,'count':bad})
 local_volume=bm.calc_volume(signed=True)
 # World-space float64 triangle determinant sum; local volume alone misses mirrored transforms.
 world_volume=math.fsum(float(v[a].x)*(float(v[b].y)*float(v[c].z)-float(v[b].z)*float(v[c].y))+float(v[a].y)*(float(v[b].z)*float(v[c].x)-float(v[b].x)*float(v[c].z))+float(v[a].z)*(float(v[b].x)*float(v[c].y)-float(v[b].y)*float(v[c].x)) for a,b,c in t)/6
 volume=world_volume
 if volume<=0:negative.append({'object':ob.name,'signed_world_volume_m3':world_volume,'signed_local_volume_m3':local_volume})
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
 component_records.append({'object':ob.name,'component_sizes':component_sizes,'signed_volume_m3':volume,'signed_world_volume_m3':world_volume,'signed_local_volume_m3':local_volume})
 if len(component_sizes)!=1:components.append({'object':ob.name,'connected_components':len(component_sizes),'component_sizes':component_sizes,'required':1})
 bm.free();tree=BVHTree.FromPolygons(v,t,all_triangles=True,epsilon=0);D[ob.name]=(v,t,tree)
 for k,tt in enumerate(t):
  pts=[tuple(float(c) for c in v[i]) for i in tt];u=[pts[1][j]-pts[0][j] for j in range(3)];w=[pts[2][j]-pts[0][j] for j in range(3)];n=[u[1]*w[2]-u[2]*w[1],u[2]*w[0]-u[0]*w[2],u[0]*w[1]-u[1]*w[0]];ln=math.sqrt(sum(q*q for q in n));area=ln/2
  if area<1e-12:degenerate.append([ob.name,k,area]);continue
  key=tuple(sorted(tuple(round(c,8) for c in pt) for pt in pts))
  if key in facekeys:duplicate.append([facekeys[key],[ob.name,k]])
  facekeys[key]=[ob.name,k];normal=tuple(q/ln for q in n);d=sum(normal[j]*pts[0][j] for j in range(3));bbox=tuple((min(q[j] for q in pts),max(q[j] for q in pts)) for j in range(3));triangles.append((ob.name,k,tt,pts,normal,d,bbox,area))
 for i,j in tree.overlap(tree):
  if i<j and not set(t[i])&set(t[j]):selfhits.append([ob.name,i,j])
# Cross-object surface intersections are forbidden too; model count remains a separate gate.
for oa,ob in itertools.combinations(D,2):
 for i,j in D[oa][2].overlap(D[ob][2]):selfhits.append([oa,i,ob,j])
def sat(a,b):
 for poly in [a,b]:
  for i in range(3):
   u,w=poly[i],poly[(i+1)%3];x,y=-(w[1]-u[1]),w[0]-u[0];ln=math.hypot(x,y)
   if ln<1e-13:continue
   x/=ln;y/=ln;pa=[q[0]*x+q[1]*y for q in a];pb=[q[0]*x+q[1]*y for q in b]
   if min(max(pa),max(pb))-max(min(pa),min(pb))<=1e-8:return False
 return True
# Broadphase: every triangle's expanded AABB occupies all touched 12 mm spatial cells.
# Float32 vertices on short triangles need scale-aware angular slack: cosine 1-1e-7,
# but BOTH point-to-plane residuals must remain <=5e-8 m. This is a near-coplanar gate.
# Unlike hard plane buckets this cannot exclude a pair merely because normal/plane round differently.
spatial=defaultdict(list);cell=.012;plane_tol=5e-8;coplanar=[];tested=set();coplanar_candidates=0
for i,x in enumerate(triangles):
 cells=itertools.product(*(range(math.floor((lo-plane_tol)/cell),math.floor((hi+plane_tol)/cell)+1) for lo,hi in x[6]));keys=list(cells)
 candidates=set(j for key in keys for j in spatial[key])
 for j in candidates:
  y=triangles[j]
  if any(min(x[6][k][1],y[6][k][1])-max(x[6][k][0],y[6][k][0])< -plane_tol for k in range(3)):continue
  if abs(sum(x[4][k]*y[4][k] for k in range(3)))<1-1e-7:continue
  if max(abs(sum(x[4][k]*q[k] for k in range(3))-x[5]) for q in y[3])>plane_tol:continue
  if max(abs(sum(y[4][k]*q[k] for k in range(3))-y[5]) for q in x[3])>plane_tol:continue
  coplanar_candidates+=1;axis=max(range(3),key=lambda k:abs(x[4][k]));axes=[k for k in range(3) if k!=axis];A=[tuple(q[k] for k in axes) for q in x[3]];B=[tuple(q[k] for k in axes) for q in y[3]]
  if x[0]==y[0] and len(set(x[2])&set(y[2]))==2:
   common=set(x[2])&set(y[2]);pts=dict(zip(x[2],A));pts.update(zip(y[2],B));u,w=[pts[c] for c in common];xa=pts[next(c for c in x[2] if c not in common)];ya=pts[next(c for c in y[2] if c not in common)];cross=lambda q:(w[0]-u[0])*(q[1]-u[1])-(w[1]-u[1])*(q[0]-u[0])
   if cross(xa)*cross(ya)<=0:continue
  if any(min(max(q[k] for q in A),max(q[k] for q in B))-max(min(q[k] for q in A),min(q[k] for q in B))<=1e-8 for k in range(2)):continue
  if sat(A,B):coplanar.append([[x[0],x[1]],[y[0],y[1]]])
 for key in keys:spatial[key].append(i)
report={'variant':C['name'],'recipe_version':info['recipe_version'],'blender_version':bpy.app.version_string,'model_sha256':hashlib.sha256(Path(a.model).read_bytes()).hexdigest(),'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'mesh_objects':len(obs),'triangles':sum(len(x[1]) for x in D.values()),'degenerate_triangles':degenerate,'duplicate_triangles':duplicate,'nonmanifold_edges':nonmanifold,'non_positive_volume':negative,'non_positive_world_volume':negative,'inconsistent_winding_edges':winding,'invalid_connected_components':components,'component_records':component_records,'nonfinite_coordinates':nonfinite,'recipe_vertex_envelope_failures':envelope,'recipe_topology_failures':topology,'object_contract_failures':object_contract,'material_contract_failures':material_contract,'object_transform_failures':transform_contract,'model_state_contract_failures':model_state,'nonadjacent_self_intersection_candidates':selfhits,'coplanar_positive_area_overlaps':coplanar,'coplanar_candidate_pairs':coplanar_candidates,'minimum_triangle_area_m2':min((x[7] for x in triangles),default=None),'thresholds':{'degenerate_area_m2':1e-12,'duplicate_vertex_round_m':1e-8,'recipe_vertex_distance_m':2e-7,'identity_matrix_entry_tolerance':1e-8,'coplanar_normal_cosine':1-1e-7,'coplanar_plane_distance_m':5e-8,'positive_overlap_axis_m':1e-8,'spatial_cell_m':cell},'limits':['Recipe identity is a constrained full-vertex/topology contract, not independent proof of arbitrary geometry.','Nonadjacent BVH intersections exclude triangles sharing any vertex; adjacent noncoplanar foldover is not fully certified.','Float64 plane/SAT is numerical tolerance testing, not exact symbolic or continuous parameter-domain proof.','Pure model contract: exactly one object, of type MESH; no modifier, shape key, constraint, parent, object/mesh animation_data or drivers. Photographic scene.blend is not accepted here.','World-space signed volume is checked separately from local volume; this recipe also requires identity object transforms.','One closed connected shell is required; no allowed-pair exception exists. Interior islands are rejected by connectivity/recipe identity even when no surface intersection exists.','No fabrication, load, stability, ergonomics, GPU, WebGL, iPhone, or dynamic z-fighting verification.']}
report['passed']=not any([degenerate,duplicate,nonmanifold,negative,selfhits,coplanar,components,winding,nonfinite,envelope,topology,object_contract,material_contract,transform_contract,model_state]);report['elapsed_seconds']=round(time.time()-start,3);Path(a.report).parent.mkdir(parents=True,exist_ok=True);Path(a.report).write_text(json.dumps(report,indent=2,ensure_ascii=False));print('FOLIO QA',C['name'],report['passed'],'triangles',report['triangles'],'selfhits',len(selfhits),'coplanar',len(coplanar),'seconds',report['elapsed_seconds'])
if not report['passed']:raise RuntimeError('FOLIO static gate rejected; see report')
