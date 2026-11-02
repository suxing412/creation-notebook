"""Independent static mesh/assembly gate. All 28 object pairs are classified explicitly.
No assertion about GPU depth buffering, photometry, manufacturing, or load stability.
"""
import bpy,bmesh,sys,json,math,argparse,itertools
from pathlib import Path
from collections import defaultdict
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--report',required=True);p.add_argument('--info',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);info=json.loads(Path(a.info).read_text());C=info['config'];bpy.ops.wm.open_mainfile(filepath=a.model)
obs=sorted([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:o.name)
D={};planes=defaultdict(list);facekeys={};duplicate=[];degenerate=[];nonmanifold=[];selfhits=[];negative=[];components=[];winding=[]
for ob in obs:
 me=ob.data;me.calc_loop_triangles();v=[ob.matrix_world@x.co for x in me.vertices];t=[tuple(x.vertices) for x in me.loop_triangles]
 assert all(math.isfinite(c) for q in v for c in q),'Nonfinite native vertex coordinates'
 bm=bmesh.new();bm.from_mesh(me);bad=sum(not e.is_manifold for e in bm.edges)
 flipped=sum(e.is_manifold and not e.is_contiguous for e in bm.edges)
 if flipped:winding.append({'object':ob.name,'inconsistent_winding_edges':flipped})
 if bad:nonmanifold.append({'object':ob.name,'count':bad})
 volume=bm.calc_volume(signed=True)
 if volume<=0:negative.append({'object':ob.name,'signed_volume':volume})
 bm.verts.ensure_lookup_table();seen_vertices=set();component_count=0
 for start in bm.verts:
  if start.index in seen_vertices:continue
  component_count+=1;stack=[start];seen_vertices.add(start.index)
  while stack:
   current=stack.pop()
   for edge in current.link_edges:
    other=edge.other_vert(current)
    if other.index not in seen_vertices:seen_vertices.add(other.index);stack.append(other)
 if component_count!=1:components.append({'object':ob.name,'connected_components':component_count,'required':1})
 bm.free()
 tree=BVHTree.FromPolygons(v,t,all_triangles=True,epsilon=0);D[ob.name]=(v,t,tree)
 for k,tt in enumerate(t):
  pts=[v[i] for i in tt];normal=(pts[1]-pts[0]).cross(pts[2]-pts[0]);area=normal.length/2
  if area<1e-12:degenerate.append([ob.name,k,area]);continue
  key=tuple(sorted(tuple(round(c,8) for c in pt) for pt in pts))
  if key in facekeys:duplicate.append([facekeys[key],[ob.name,k]])
  facekeys[key]=[ob.name,k]
  # Plane arithmetic uses Python float64, not mathutils float32 unit-vector dot products.
  u=[float(pts[1][k])-float(pts[0][k]) for k in range(3)];w=[float(pts[2][k])-float(pts[0][k]) for k in range(3)]
  n=[u[1]*w[2]-u[2]*w[1],u[2]*w[0]-u[0]*w[2],u[0]*w[1]-u[1]*w[0]];ln=math.sqrt(sum(q*q for q in n));normal=tuple(q/ln for q in n)
  d=sum(normal[k]*float(pts[0][k]) for k in range(3));axis=max(range(3),key=lambda j:abs(normal[j]));axes=[j for j in range(3) if j!=axis];flat=[tuple(float(pt[j]) for j in axes) for pt in pts]
  planes[tuple(math.floor(q/1e-4) for q in normal)].append((ob.name,k,flat,tt,pts,normal,d))
 for i,j in tree.overlap(tree):
  if i<j and not set(t[i])&set(t[j]):selfhits.append([ob.name,i,j])

def sat(a,b):
 for poly in [a,b]:
  for i in range(3):
   u,w=poly[i],poly[(i+1)%3];x,y=-(w[1]-u[1]),w[0]-u[0];l=math.hypot(x,y)
   if l<1e-13:continue
   x/=l;y/=l;pa=[q[0]*x+q[1]*y for q in a];pb=[q[0]*x+q[1]*y for q in b]
   if min(max(pa),max(pb))-max(min(pa),min(pb))<=1e-8:return False
 return True
coplanar=[]
# Search adjacent orientation bins, including opposite orientation. Do not put d in a hard bucket.
# For the 1e-10 cosine tolerance, unit-normal component differences are < 1.5e-5,
# so +/-1 neighbours of 1e-4 bins cover the accepted angular neighbourhood.
for key,group in planes.items():
 opposite=tuple(-k-1 for k in key);neighbours={tuple(base[k]+off[k] for k in range(3)) for base in [key,opposite] for off in itertools.product([-1,0,1],repeat=3)}
 candidates=[y for neighbour in neighbours for y in planes.get(neighbour,[])]
 for x in group:
  for y in candidates:
   if x[:2]>=y[:2]:continue
   if abs(sum(x[5][k]*y[5][k] for k in range(3)))<1-1e-10:continue
   if max(abs(sum(x[5][k]*float(q[k]) for k in range(3))-x[6]) for q in y[4])>1e-8:continue
   axis=max(range(3),key=lambda k:abs(x[5][k]));axes=[k for k in range(3) if k!=axis];flatA=x[2];flatB=[tuple(float(pt[k]) for k in axes) for pt in y[4]]
   # Shared-edge triangles are excluded only if their third vertices lie on opposite sides.
   if x[0]==y[0] and len(set(x[3])&set(y[3]))==2:
    common=set(x[3])&set(y[3]);pts=dict(zip(x[3],flatA));pts.update(zip(y[3],flatB));u,w=[pts[c] for c in common];xa=pts[next(c for c in x[3] if c not in common)];ya=pts[next(c for c in y[3] if c not in common)];cross=lambda q:(w[0]-u[0])*(q[1]-u[1])-(w[1]-u[1])*(q[0]-u[0])
    if cross(xa)*cross(ya)<=0:continue
   if any(min(max(p[k] for p in flatA),max(p[k] for p in flatB))-max(min(p[k] for p in flatA),min(p[k] for p in flatB))<=1e-8 for k in range(2)):continue
   if sat(flatA,flatB):coplanar.append([[x[0],x[1]],[y[0],y[1]]])

BBOX={}
def inside(pt,tree,verts):
 if id(verts) not in BBOX:BBOX[id(verts)]=[(min(v[k] for v in verts),max(v[k] for v in verts)) for k in range(3)]
 if any(pt[k]<BBOX[id(verts)][k][0]-1e-8 or pt[k]>BBOX[id(verts)][k][1]+1e-8 for k in range(3)):return False
 votes=[]
 for direct in [Vector((1,.3713907,.193723)).normalized(),Vector((.21367,1,.41731)).normalized(),Vector((.32711,.23197,1)).normalized()]:
  pos=pt+direct*3e-8;count=0
  for _ in range(80):
   hit,n,idx,d=tree.ray_cast(pos,direct,5)
   if hit is None:break
   count+=1;pos=hit+direct*3e-7
  votes.append(bool(count%2))
 return sum(votes)>=2

def triangle_contact_points(pa,pb):
 result=[]
 def intersect(edges,tri):
  n=(tri[1]-tri[0]).cross(tri[2]-tri[0]);n.normalize()
  u=tri[1]-tri[0];v=tri[2]-tri[0];uu=u.dot(u);uv=u.dot(v);vv=v.dot(v);den=uu*vv-uv*uv
  if abs(den)<1e-24:return
  for i in range(3):
   a,b=edges[i],edges[(i+1)%3];da=n.dot(a-tri[0]);db=n.dot(b-tri[0])
   if abs(da-db)<1e-14:continue
   t=da/(da-db)
   if not -1e-6<=t<=1+1e-6:continue
   q=a+(b-a)*t;w=q-tri[0];wu=w.dot(u);wv=w.dot(v);s=(vv*wu-uv*wv)/den;r=(uu*wv-uv*wu)/den
   if s>=-1e-6 and r>=-1e-6 and s+r<=1+1e-6:result.append(q)
 intersect(pa,pb);intersect(pb,pa)
 return result

# Specific regions plus limited geometric depth, not name-pattern blanket approval.
allowed={tuple(sorted((obs[0].name,obs[4].name))):'hub-shell',tuple(sorted((obs[2].name,obs[3].name))):'base-stem',tuple(sorted((obs[3].name,obs[4].name))):'stem-hub'}
for pin in obs[5:]:
 allowed[tuple(sorted((obs[1].name,pin.name))) ]='pin-diffuser'
 allowed[tuple(sorted((obs[4].name,pin.name))) ]='pin-hub'
# Do not accept an unexpected object count/name silently.
assert len(obs)==8 and [o.name[:2] for o in obs]==['01','02','03','04','05','06','06','06']

def region_ok(kind,pts):
 rim=C['rim_height'];cx=C['stem_lean']/2;hb=rim-.050
 if kind=='hub-shell':return all(rim+C['shade_rise']-.008<=q.z<=rim+C['shade_rise']+.004 and math.hypot(q.x-cx,q.y)<=.012 for q in pts)
 if kind=='base-stem':return all(.021<=q.z<=.028 and abs(q.x+C['stem_lean']/2)<=.013 and abs(q.y)<=.012 for q in pts)
 if kind=='stem-hub':return all(hb-.001<=q.z<=hb+.006 and math.hypot(q.x-cx,q.y)<=.012 for q in pts)
 pinz=rim-info['construction']['shell_to_lens_rim_vertical_offset_mm']/1000-.017*(1-(.145/info['construction']['lens_inset_ratio'])**2)
 if kind=='pin-hub':return all(math.hypot(q.x-cx,q.y)<=.013 and abs(q.z-pinz)<=.00142 for q in pts)
 if kind=='pin-diffuser':
  ax=C['shade_width']/2;by=C['shade_depth']/2
  return all(.128<=math.hypot((q.x-cx)/ax,q.y/by)<=.165 and abs(q.z-pinz)<=.00142 for q in pts)
 return False
rows=[];unexpected=[];missing=[];badregion=[];containment=[]
for i,oa in enumerate(obs):
 va,ta,ba=D[oa.name]
 for ob in obs[i+1:]:
  vb,tb,bb=D[ob.name];hits=ba.overlap(bb);key=tuple(sorted((oa.name,ob.name)));kind=allowed.get(key)
  samplesA=va[::max(1,len(va)//96)];samplesB=vb[::max(1,len(vb)//96)]
  nearest=min([bb.find_nearest(q)[3] for q in samplesA]+[ba.find_nearest(q)[3] for q in samplesB])
  insA=sum(inside(q,bb,vb) is True for q in samplesA);insB=sum(inside(q,ba,va) is True for q in samplesB)
  row={'a':oa.name,'b':ob.name,'policy':kind or 'must-be-disjoint','triangle_intersection_candidates':len(hits),'sampled_vertex_surface_min_mm':round(nearest*1000,4),'sampled_inside_vertices':[insA,insB]}
  if kind:
   if not hits:missing.append(row)
   # Use intersection segment midpoint estimates, not remote vertices of long cylinder faces.
   contact_points=[]
   for ia,ib in hits:
    contact_points.extend(triangle_contact_points([va[idx] for idx in ta[ia]],[vb[idx] for idx in tb[ib]]))
   row['bounded_contact_samples']=len(contact_points);row['region_passed']=bool(contact_points) and region_ok(kind,contact_points)
   if not row['region_passed']:badregion.append(row)
  else:
   if hits:unexpected.append(row)
   if insA or insB:containment.append(row)
  rows.append(row)
# Full-vertex finite envelopes for hidden connector bodies. Endpoint-only tests can miss extensions.
connector_envelope_failures=[]
cx=C['stem_lean']/2;rim=C['rim_height'];ax=C['shade_width']/2;by=C['shade_depth']/2;inset=info['construction']['lens_inset_ratio'];gap=info['construction']['shell_to_lens_rim_vertical_offset_mm']/1000
pinz=rim-gap-.017*(1-(.145/inset)**2)
for i,pin in enumerate(obs[5:]):
 theta=math.pi/2+2*math.pi*i/3;R=math.hypot(ax*math.cos(theta),by*math.sin(theta));rr=.145+.0013/R
 end=Vector((cx+ax*rr*math.cos(theta),by*rr*math.sin(theta),pinz));direct=Vector((end.x-cx,end.y,0)).normalized();start=Vector((cx,0,pinz))+direct*.0095;length=(end-start).length
 bad=[]
 for j,q in enumerate(D[pin.name][0]):
  t=(q-start).dot(direct);radial=(q-start-direct*t).length
  if t< -2e-6 or t>length+2e-6 or radial>.001402:bad.append(j)
 if bad:connector_envelope_failures.append({'object':pin.name,'outside_finite_pin_envelope_vertices':len(bad)})
hub_lo=rim-.050;hub_hi=rim+C['shade_rise']-.003+.0015
bad=[j for j,q in enumerate(D[obs[4].name][0]) if q.z<hub_lo-2e-6 or q.z>hub_hi+2e-6 or math.hypot(q.x-cx,q.y)>.011002]
if bad:connector_envelope_failures.append({'object':obs[4].name,'outside_finite_hub_envelope_vertices':len(bad)})
# Verify endpoint engagement in actual mesh solids, not only triangle-crossing regions.
assembly_endpoints=[]
def endpoint(label,pt,target,min_mm,max_mm):
 vv,tt,tree=D[target];depth=tree.find_nearest(pt)[3]*1000;contained=inside(pt,tree,vv);ok=contained and min_mm<=depth<=max_mm
 assembly_endpoints.append({'endpoint':label,'target':target,'inside':contained,'nearest_surface_depth_mm':round(depth,5),'accepted_depth_mm':[min_mm,max_mm],'passed':ok})
for pin in obs[5:]:
 vv=D[pin.name][0];endpoint(pin.name+' start',sum(vv[:20],Vector())/20,obs[4].name,.5,2.5);endpoint(pin.name+' end',sum(vv[-20:],Vector())/20,obs[1].name,.5,2.5)
sv=D[obs[3].name][0];endpoint('stem bottom centre',sum(sv[:48],Vector())/48,obs[2].name,3,5);endpoint('stem top centre',sum(sv[-48:],Vector())/48,obs[4].name,3,5)
hv=D[obs[4].name][0];hz=max(v.z for v in hv);cap=[v for v in hv if v.z>hz-1e-7]
for j,q in enumerate(cap):endpoint('hub top cap '+str(j),q,obs[0].name,.2,4.5)
assembly_endpoint_failures=[e for e in assembly_endpoints if not e['passed']]
# Shell/diffuser minimum distance is sampled in both directions and independently forbidden to intersect/contain.
clearance=next(r for r in rows if r['a'].startswith('01') and r['b'].startswith('02'))
report={'blender_version':bpy.app.version_string,'variant':C['name'],'recipe_version':info['recipe_version'],'mesh_objects':len(obs),'triangles':sum(len(x[1]) for x in D.values()),'degenerate_triangles':degenerate,'duplicate_triangles':duplicate,'nonmanifold_edges':nonmanifold,'non_positive_volume':negative,'inconsistent_winding_edges':winding,'invalid_connected_components':components,'connector_envelope_failures':connector_envelope_failures,'nonadjacent_self_intersection_candidates':selfhits,'coplanar_positive_area_overlaps':coplanar,'all_28_pair_classifications':rows,'unexpected_intersection_pairs':unexpected,'missing_expected_contact_pairs':missing,'contact_region_failures':badregion,'unexpected_containment_samples':containment,'assembly_endpoint_engagement':assembly_endpoints,'assembly_endpoint_failures':assembly_endpoint_failures,'shell_diffuser_clearance':clearance,'thresholds':{'degenerate_area_m2':1e-12,'duplicate_vertex_round_m':1e-8,'coplanar_normal_cosine':1-1e-10,'orientation_bin_width':1e-4,'orientation_neighbour_bins':1,'coplanar_plane_distance_m':1e-8,'positive_overlap_axis_m':1e-8},'limits':['BVH nonadjacent triangles excludes shared vertices; double-precision plane and adjacent orientation-bin SAT add coplanar overlap checks, not exact interval geometry.','Containment checks use sampled vertices and oblique ray parity; unsampled tiny islands can be missed.','Nearest-surface sampling is not exact all-edge global minimum.','Socket bounds certify this static model contact region, not manufacturing tolerances or electrical safety.','WebGL/GPU/iPhone/dynamic z-fighting not tested; no browser GL security override.']}
report['passed']=not any([degenerate,duplicate,nonmanifold,negative,selfhits,coplanar,unexpected,missing,badregion,containment,assembly_endpoint_failures,components,connector_envelope_failures,winding])
Path(a.report).write_text(json.dumps(report,indent=2,ensure_ascii=False));print('QA',C['name'],report['passed'], 'defects',len(degenerate),len(duplicate),len(nonmanifold),len(selfhits),len(coplanar),'assembly',len(unexpected),len(missing),len(badregion),len(containment))
if not report['passed']:raise RuntimeError('Vesper static gate rejected; see report')
