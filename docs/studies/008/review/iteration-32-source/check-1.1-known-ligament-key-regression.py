"""008 VEIL native closed perforated shell QA.
Numeric substrate only is adapted from 006/007 (world volume, BVH and float64 near-plane SAT).
No inherited object-pair whitelist, closed-sweep seam or frame predicates.
The recipe-specific contract and actual aperture/wall tests are defined below.
"""
import bpy,bmesh,sys,json,math,argparse,itertools,hashlib,time,uuid,datetime
from pathlib import Path
from collections import defaultdict,Counter
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
import recipe
VERSION='008-native-1.1'
FAIL_FIELDS=['degenerate_triangles','duplicate_triangles','nonmanifold_edges','non_positive_world_volume','inconsistent_winding_edges','invalid_connected_components','nonfinite_coordinates','recipe_vertex_envelope_failures','recipe_topology_failures','object_contract_failures','material_contract_failures','object_transform_failures','model_state_contract_failures','nonadjacent_self_intersection_candidates','coplanar_positive_area_overlaps','genus_contract_failures','input_contract_failures','construction_metadata_failures','aperture_loop_failures','aperture_wall_failures','aperture_clearance_failures','thickness_failures','minimum_ligament_failures','corner_normal_failures']
def canonical(face):
 x=tuple(face);return min(x[i:]+x[:i] for i in range(len(x))) if x else ()
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

def family_contract(C,revision,construction,v,polygons,info,r):
 from mathutils.kdtree import KDTree
 holes=construction['holes'];required=C['columns']*C['rows'];R=C['width']/math.radians(C['curve_angle_degrees']);h=C['thickness']/2;edge_r=C['edge_radius'] if revision else 0
 edge_faces=defaultdict(list);actual_faces=Counter(canonical(q) for q in polygons)
 for fi,f in enumerate(polygons):
  for a,b in zip(f,f[1:]+f[:1]):edge_faces[tuple(sorted((a,b)))].append(fi)
 def inverse(p):return (R*math.atan2(float(p.x),R-float(p.y)),float(p.z),math.hypot(float(p.x),R-float(p.y))-R)
 valid_loops=0;clear_holes=0;loop_records=[];thickness_records=[];hole_boundaries=[[],[]]
 tree=BVHTree.FromPolygons(v,polygons,all_triangles=False,epsilon=0)
 if len(holes)!=required:r['aperture_loop_failures'].append({'reason':'hole_count','actual':len(holes),'expected':required})
 for hole in holes:
  hid=hole['id'];rings=hole['all_rings'];cu,cv=hole['center_uv'];rx,ry=hole['radii_uv'];local_bad=[];maxfit=0
  for z,ring in enumerate(rings):
   if len(ring)!=32 or len(set(ring))!=32 or any(type(i) is not int or i<0 or i>=len(v) for i in ring):local_bad.append({'ring':z,'reason':'invalid_ring_indices'});continue
   off,t=hole['profile'][z]
   for j,vid in enumerate(ring):
    nxt=ring[(j+1)%len(ring)];incidence=len(edge_faces.get(tuple(sorted((vid,nxt))),[]))
    if incidence!=2:local_bad.append({'ring':z,'edge':[vid,nxt],'face_incidence':incidence})
    u,vv,tt=inverse(v[vid]);angle=recipe.loop_angles()[j][2];fit=max(abs(u-cu-(rx+off)*math.cos(angle)),abs(vv-cv-(ry+off)*math.sin(angle)),abs(tt-t));maxfit=max(maxfit,fit)
    if fit>3e-7:local_bad.append({'ring':z,'vertex':vid,'inverse_cylinder_fit_m':fit})
  if local_bad:r['aperture_loop_failures'].append({'hole':hid,'failures':local_bad[:16],'count':len(local_bad)})
  else:valid_loops+=len(rings)
  wall_bad=[]
  for z in range(len(rings)-1):
   for j in range(len(rings[z])):
    k=(j+1)%len(rings[z]);f=(rings[z][j],rings[z][k],rings[z+1][k],rings[z+1][j])
    if actual_faces[canonical(f)]!=1:wall_bad.append({'rings':[z,z+1],'edge_index':j,'oriented_wall_face_multiplicity':actual_faces[canonical(f)]})
  if wall_bad:r['aperture_wall_failures'].append({'hole':hid,'failures':wall_bad[:16],'count':len(wall_bad)})
  center=vec(recipe.surface(C,cu,cv));normal=vec(recipe.normal(C,cu));start=center+normal*(h+.02);hit,hn,face_index,distance=tree.ray_cast(start,-normal,2*(h+.02))
  if hit is not None:r['aperture_clearance_failures'].append({'hole':hid,'reason':'central_normal_ray_blocked','face_index':face_index,'hit_distance_m':distance})
  else:clear_holes+=1
  for label,front,back,expected in [('mouth',hole['front_ring'],hole['back_ring'],C['thickness']),('straight_bore',hole['bore_front_ring'],hole['bore_back_ring'],C['thickness']-2*edge_r)]:
   values=[];errors=[]
   for a,b in zip(front,back):
    if max(a,b)>=len(v):continue
    ua,va,ta=inverse(v[a]);ub,vb,tb=inverse(v[b]);delta=v[a]-v[b];n=vec(recipe.normal(C,(ua+ub)/2));actual=delta.dot(n);residual=(delta-n*expected).length;values.append(actual)
    if residual>3e-7:errors.append({'pair':[a,b],'actual_normal_separation_m':actual,'required_m':expected,'vector_residual_m':residual})
   if errors:r['thickness_failures'].append({'hole':hid,'section':label,'failures':errors[:12],'count':len(errors)})
   thickness_records.append({'hole':hid,'section':label,'minimum_normal_separation_m':min(values) if values else None,'maximum_normal_separation_m':max(values) if values else None,'required_m':expected})
  for side,key in enumerate(['front_ring','back_ring']):
   ring=hole[key]
   if all(0<=i<len(v) for i in ring):hole_boundaries[side].append((hid,[(v[a],v[b]) for a,b in zip(ring,ring[1:]+ring[:1])]))
  loop_records.append({'hole':hid,'ring_count':len(rings),'vertices_per_ring':32,'max_inverse_cylinder_fit_m':maxfit,'loop_edge_contract_passed':not local_bad,'wall_face_contract_passed':not wall_bad,'central_ray_clear':hit is None})
 # Same-u,v normal pairs on the actual outer shell, not nominal recipe-only thickness.
 pairs={}
 for i,(u,vv,t,role) in enumerate(construction['vertex_uvt']):
  if role=='surface' and i<len(v):pairs.setdefault((round(u,10),round(vv,10)),{})[1 if t>0 else -1]=i
 surface_values=[];surface_errors=[]
 for (u,vv),pair in pairs.items():
  if set(pair)!={1,-1}:surface_errors.append({'uv':[u,vv],'reason':'missing_normal_pair'});continue
  delta=v[pair[1]]-v[pair[-1]];n=vec(recipe.normal(C,u));actual=delta.dot(n);surface_values.append(actual)
  if (delta-n*C['thickness']).length>3e-7:surface_errors.append({'uv':[u,vv],'actual_m':actual})
 if surface_errors:r['thickness_failures'].append({'section':'outer_surface','failures':surface_errors[:24],'count':len(surface_errors)})
 # Four equal samples on every actual mouth/rim line segment. For sample spacing d,
 # the polyline is covered within d/2. Sample minimum minus both covering radii is
 # a conservative Euclidean separation bound (with 0.2 um arithmetic allowance).
 def sampled(edges):
  pts=[];cover=0
  for a,b in edges:
   cover=max(cover,(b-a).length/8)
   pts.extend(a+(b-a)*(j/4) for j in range(4))
  kd=KDTree(len(pts))
  for i,p in enumerate(pts):kd.insert(p,i)
  kd.balance();return pts,kd,cover
 uv_to_back={(round(u,10),round(vv,10)):i for i,(u,vv,t,role) in enumerate(construction['vertex_uvt']) if t<0 and abs(t+h)<1e-9 and i<len(v)}
 outer_front=[(v[a],v[b]) for a,b in construction['outer_front_edges'] if max(a,b)<len(v)];outer_back=[]
 for a,b in construction['outer_front_edges']:
  ua,va,_,_=construction['vertex_uvt'][a];ub,vb,_,_=construction['vertex_uvt'][b];aa=uv_to_back.get((round(ua,10),round(va,10)));bb=uv_to_back.get((round(ub,10),round(vb,10)))
  if aa is not None and bb is not None:outer_back.append((v[aa],v[bb]))
 ligament_rows=[]
 for side,boundaries in enumerate(hole_boundaries):
  data=[(hid,*sampled(edges)) for hid,edges in boundaries];outer=sampled([outer_front,outer_back][side]);minimum=float('inf');minimum_lower=float('inf');nearest=None
  for i,(hid,pts,kd,cover) in enumerate(data):
   comparisons=[('outer',*outer)]+[(other,*rest) for other,*rest in data[i+1:]]
   for other,qpts,qtree,qcover in comparisons:
    distance=min(qtree.find(p)[2] for p in pts);lower=distance-cover-qcover-2e-7
    if distance<minimum:minimum=distance;nearest=[hid,other]
    minimum_lower=min(minimum_lower,lower)
    if lower<.004:r['minimum_ligament_failures','corner_normal_failures'].append({'side':['front','back'][side],'pair':[hid,other],'sample_minimum_m':distance,'conservative_polyline_lower_bound_m':lower,'required_lower_bound_m':.004})
  ligament_rows.append({'side':['front','back'][side],'sampled_minimum_m':minimum,'conservative_polyline_lower_bound_m':minimum_lower,'nearest_sample_pair':nearest,'samples_per_mouth':128,'subdivisions_per_actual_mesh_edge':4,'required_lower_bound_m':.004})
 r['aperture_records']={'expected_holes':required,'holes_with_clear_central_ray':clear_holes,'valid_actual_ring_cycles':valid_loops,'rings':loop_records,'genus_target':required}
 r['thickness_records']={'nominal_shell_m':C['thickness'],'surface_pair_count':len(surface_values),'surface_minimum_m':min(surface_values) if surface_values else None,'surface_maximum_m':max(surface_values) if surface_values else None,'hole_sections':thickness_records}
 r['ligament_sampling']={'records':ligament_rows,'definition':'Euclidean 3D separation of actual front/back mouth polylines to every other mouth and the same-side exterior rim; not developed geodesic, projected gap, minimal internal web thickness or manufacturing strength. Finite polyline samples give an upper estimate; subtract both segment covering radii and 0.2 um to obtain conservative polyline lower bounds.','excludes':'Bore interior/rounded rim full surface minimum, unsampled smooth analytic continuation and arbitrary adjacent-face folding are not independently proven.'}
 return required

def material_contract(ob,info,r):
 if len(ob.data.materials)!=1 or ob.data.materials[0] is None:
  r['material_contract_failures'].append({'object':ob.name,'reason':'exactly_one_material_required'});return
 mat=ob.data.materials[0];decl=info.get('material',{});locked={'base_color_linear':[.58,.49,.36],'metallic':0,'roughness':.38}
 if any(decl.get(k)!=val for k,val in locked.items()):r['material_contract_failures'].append({'reason':'material_metadata_not_locked_VEIL_values'})
 if not mat.use_nodes or mat.node_tree is None:
  r['material_contract_failures'].append({'reason':'principled_nodes_required'});return
 nodes=mat.node_tree.nodes;principled=[q for q in nodes if q.type=='BSDF_PRINCIPLED'];outputs=[q for q in nodes if q.type=='OUTPUT_MATERIAL']
 if len(principled)!=1 or len(outputs)!=1 or len(nodes)!=2:
  r['material_contract_failures'].append({'reason':'single_principled_output_graph_required'});return
 p=principled[0];out=outputs[0]
 if len(mat.node_tree.links)!=1 or not any(l.from_node==p and l.to_node==out and l.from_socket.name=='BSDF' and l.to_socket.name=='Surface' for l in mat.node_tree.links):r['material_contract_failures'].append({'reason':'principled_output_link_required'})
 for key,socket in [('base_color_linear','Base Color'),('metallic','Metallic'),('roughness','Roughness')]:
  expected=locked.get(key);actual=p.inputs[socket].default_value
  if key=='base_color_linear':
   actual=list(actual)[:3];ok=isinstance(expected,list) and len(expected)==3 and all(type(q) in (int,float) and math.isfinite(q) for q in expected) and max(abs(x-y) for x,y in zip(actual,expected))<2e-7
  else:actual=float(actual);ok=type(expected) in (int,float) and math.isfinite(expected) and abs(actual-expected)<2e-7
  if not ok:r['material_contract_failures'].append({'reason':'material_metadata_mismatch','quantity':key,'actual':actual,'expected':expected})
 for socket,expected in [('Alpha',1),('Transmission Weight',0),('Coat Weight',0),('Subsurface Weight',0)]:
  if abs(float(p.inputs[socket].default_value)-expected)>2e-7:r['material_contract_failures'].append({'reason':'unsupported_shader_change','socket':socket})
 if any(abs(float(x)*float(p.inputs['Emission Strength'].default_value))>2e-7 for x in p.inputs['Emission Color'].default_value[:3]):r['material_contract_failures'].append({'reason':'emission_not_zero'})
 if any(q.material_index!=0 for q in ob.data.polygons):r['material_contract_failures'].append({'reason':'nonzero_polygon_material_index'})
 if mat.animation_data is not None or mat.node_tree.animation_data is not None:r['material_contract_failures'].append({'reason':'animated_material'})

def run(a,r):
 info=json.loads(Path(a.info).read_text());C=info['config'];revision=info['construction']['revision'];r['variant']=C['name'];r['recipe_version']=info['recipe_version'];r['info_sha256']=sha(a.info)
 try:recipe.validate(C,bpy.app.version,revision=revision)
 except Exception as e:r['input_contract_failures'].append({'reason':str(e)});return
 expected_v,expected_f,construction=recipe.geometry(C,revision)
 if info.get('construction')!=json.loads(json.dumps(construction)):r['construction_metadata_failures'].append({'reason':'construction_differs_from_deterministic_recipe'})
 if info.get('recipe_version')!=recipe.VERSION:r['construction_metadata_failures'].append({'reason':'recipe_version_mismatch'})
 expected_metadata={'recipe_version':recipe.VERSION,'study':'008','variant':C['name'],'seed':0,'blender_version':'4.3.2','units':'metres','mesh_objects':1,'vertices':len(expected_v),'triangles':sum(len(f)-2 for f in expected_f)}
 for key,val in expected_metadata.items():
  if info.get(key)!=val:r['construction_metadata_failures'].append({'reason':'model_metadata_mismatch','key':key,'expected':val,'actual':info.get(key)})
 bounds=[[min(q[k] for q in expected_v),max(q[k] for q in expected_v)] for k in range(3)]
 if info.get('bounds_m')!=bounds:r['construction_metadata_failures'].append({'reason':'bounds_metadata_mismatch'})
 dimensions={key:round((bounds[i][1]-bounds[i][0])*1000,3) for i,key in enumerate(['width','depth','height'])}
 if info.get('dimensions_mm')!=dimensions:r['construction_metadata_failures'].append({'reason':'dimensions_metadata_mismatch'})
 bpy.ops.wm.open_mainfile(filepath=a.model);obs=sorted([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:o.name);r['mesh_objects']=len(obs);all_objects=list(bpy.data.objects)
 if len(all_objects)!=1:r['model_state_contract_failures'].append({'reason':'object_count_not_one','actual':len(all_objects)})
 for candidate in all_objects:
  if candidate.type!='MESH':r['model_state_contract_failures'].append({'object':candidate.name,'reason':'non_mesh_object','type':candidate.type})
 if len(obs)!=1:r['object_contract_failures'].append({'required':1,'actual':len(obs)})
 D={};triangles=[];facekeys={};expected_faces=Counter(canonical(q) for q in expected_f);component_records=[]
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
  material_contract(ob,info,r)
  corners=[q.vector.copy() for q in me.corner_normals];normal_errors=[];lengths=[];hemispheres=[]
  if len(corners)!=len(me.loops):normal_errors.append({'reason':'corner_count_mismatch','actual':len(corners),'expected':len(me.loops)})
  for poly in me.polygons:
   for lid in poly.loop_indices:
    if lid>=len(corners):continue
    n=corners[lid];length=math.sqrt(math.fsum(float(x)*float(x) for x in n));lengths.append(length);hemi=n.dot(poly.normal);hemispheres.append(hemi)
    if any(not math.isfinite(float(x)) for x in n) or not math.isfinite(length) or abs(length-1)>2e-5:normal_errors.append({'reason':'nonfinite_or_nonunit_corner_normal','corner':lid,'length':length})
    elif hemi< -1e-5:normal_errors.append({'reason':'corner_normal_opposes_geometric_face','corner':lid,'dot':hemi})
  if normal_errors:r['corner_normal_failures'].append({'object':ob.name,'count':len(normal_errors),'failures':normal_errors[:32]})
  r.setdefault('corner_normal_records',[]).append({'object':ob.name,'corners':len(corners),'has_custom_normals':me.has_custom_normals,'minimum_length':min(lengths) if lengths else None,'maximum_length':max(lengths) if lengths else None,'minimum_dot_geometric_face_normal':min(hemispheres) if hemispheres else None,'length_tolerance':2e-5,'negative_hemisphere_tolerance':1e-5,'analytic_normal_field_equivalence_independently_verified':False})

  if len(v)!=len(expected_v):r['recipe_vertex_envelope_failures'].append({'object':ob.name,'vertex_count':len(v),'expected':len(expected_v)})
  badv=[{'index':i,'distance_m':(q-vec(expected_v[i])).length} for i,q in enumerate(v[:len(expected_v)]) if (q-vec(expected_v[i])).length>2e-7]
  if badv:r['recipe_vertex_envelope_failures'].append({'object':ob.name,'off_recipe_vertices':badv[:64],'count':len(badv),'tolerance_m':2e-7})
  actual_faces=Counter(canonical(tuple(q.vertices)) for q in me.polygons)
  if actual_faces!=expected_faces:r['recipe_topology_failures'].append({'object':ob.name,'actual_polygons':len(me.polygons),'expected_polygons':len(expected_f),'identical_oriented_index_cycles':False})
  hole_count=family_contract(C,revision,construction,v,[tuple(q.vertices) for q in me.polygons],info,r)
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
  required_chi=2-2*hole_count
  if chi!=required_chi:r['genus_contract_failures'].append({'object':ob.name,'euler_characteristic':chi,'required':required_chi,'required_true_holes':hole_count})
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
 r.update({'triangles':sum(len(x[1]) for x in D.values()),'minimum_triangle_area_m2':min((x[7] for x in triangles),default=None),'component_records':component_records,'coplanar_candidate_pairs':candidates_count})

def main():
 p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--report',required=True);p.add_argument('--info',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);start=time.time();r={k:[] for k in FAIL_FIELDS};r.update({'checker_version':VERSION,'checker_sha256':sha(__file__),'recipe_sha256':sha(recipe.__file__),'model_sha256':sha(a.model),'file':Path(a.model).name,'run_id':str(uuid.uuid4()),'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'blender_version':bpy.app.version_string,'passed':False,'limits':['Full-vertex/oriented-face identity is a restricted VEIL recipe contract, not arbitrary geometry or reindexing equivalence.','BVH candidates exclude triangles sharing any vertex; noncoplanar adjacent foldover is not fully independently certified.','Near-coplanar overlaps use bidirectional float64 plane distances and projected SAT, not exact symbolic predicates or dynamic z-fighting validation.','Exactly one raw mesh, no modifiers/shape keys/parents/constraints/object or mesh animation or drivers; photographic scene.blend is out of scope.','No GPU, WebGL, dynamic flicker, physical iPhone, manufacturing, load or stability verification.'],'thresholds':{'vertex_distance_m':2e-7,'triangle_area_m2':1e-12,'duplicate_vertex_round_m':1e-8,'identity_matrix_entry':1e-8,'coplanar_normal_cosine':1-1e-7,'bidirectional_plane_distance_m':5e-8,'positive_projected_overlap_m':1e-8,'spatial_cell_m':.012}})
 try:run(a,r);r['passed']=not any(r[k] for k in FAIL_FIELDS)
 except Exception as e:r['internal_error']={'type':type(e).__name__,'message':str(e)};r['passed']=False
 r['elapsed_seconds']=round(time.time()-start,3);Path(a.report).parent.mkdir(parents=True,exist_ok=True);Path(a.report).write_text(json.dumps(r,indent=2,ensure_ascii=False));print('008 NATIVE',r['passed'],'failures',{k:len(r[k]) for k in FAIL_FIELDS if r[k]},'error',r.get('internal_error'),'seconds',r['elapsed_seconds'])
 if not r['passed']:raise RuntimeError('008 native gate rejected; see report')
if __name__=='__main__':main()
