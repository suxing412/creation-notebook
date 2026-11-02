"""Independent static mesh/assembly gate. All 28 object pairs are classified explicitly.
No assertion about GPU depth buffering, photometry, manufacturing, or load stability.
"""
import bpy,bmesh,sys,json,math,argparse
from pathlib import Path
from collections import defaultdict
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--report',required=True);p.add_argument('--info',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);info=json.loads(Path(a.info).read_text());C=info['config'];bpy.ops.wm.open_mainfile(filepath=a.model)
obs=sorted([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:o.name)
D={};planes=defaultdict(list);facekeys={};duplicate=[];degenerate=[];nonmanifold=[];selfhits=[];negative=[]
for ob in obs:
 me=ob.data;me.calc_loop_triangles();v=[ob.matrix_world@x.co for x in me.vertices];t=[tuple(x.vertices) for x in me.loop_triangles]
 bm=bmesh.new();bm.from_mesh(me);bad=sum(not e.is_manifold for e in bm.edges)
 if bad:nonmanifold.append({'object':ob.name,'count':bad})
 volume=bm.calc_volume(signed=True)
 if volume<=0:negative.append({'object':ob.name,'signed_volume':volume})
 bm.free()
 tree=BVHTree.FromPolygons(v,t,all_triangles=True,epsilon=0);D[ob.name]=(v,t,tree)
 for k,tt in enumerate(t):
  pts=[v[i] for i in tt];normal=(pts[1]-pts[0]).cross(pts[2]-pts[0]);area=normal.length/2
  if area<1e-12:degenerate.append([ob.name,k,area]);continue
  key=tuple(sorted(tuple(round(c,8) for c in pt) for pt in pts))
  if key in facekeys:duplicate.append([facekeys[key],[ob.name,k]])
  facekeys[key]=[ob.name,k]
  normal.normalize()
  if next((n for n in normal if abs(n)>1e-8),1)<0:normal=-normal
  d=normal.dot(pts[0]);axis=max(range(3),key=lambda j:abs(normal[j]));axes=[j for j in range(3) if j!=axis];flat=[tuple(pt[j] for j in axes) for pt in pts]
  planes[tuple(round(n,6) for n in normal)+(round(d,7),)].append((ob.name,k,flat,tt,pts,normal,d))
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
for group in planes.values():
 for i,x in enumerate(group):
  for y in group[i+1:]:
   # Two triangulated sides of the same shared edge are only exempt if separated.
   if x[0]==y[0] and len(set(x[3])&set(y[3]))==2:
    common=set(x[3])&set(y[3]);pts=dict(zip(x[3],x[2]));pts.update(zip(y[3],y[2]));u,w=[pts[c] for c in common];xa=pts[next(c for c in x[3] if c not in common)];ya=pts[next(c for c in y[3] if c not in common)];cross=lambda q:(w[0]-u[0])*(q[1]-u[1])-(w[1]-u[1])*(q[0]-u[0])
    if cross(xa)*cross(ya)<=0:continue
   if abs(x[5].dot(y[5]))<1-1e-8 or max(abs(x[5].dot(q)-x[6]) for q in y[4])>1e-8:continue
   if any(min(max(p[k] for p in x[2]),max(p[k] for p in y[2]))-max(min(p[k] for p in x[2]),min(p[k] for p in y[2]))<=1e-8 for k in range(2)):continue
   if sat(x[2],y[2]):coplanar.append([[x[0],x[1]],[y[0],y[1]]])

def inside(pt,tree):
 # Odd/even parity with irrational-ish oblique direction; tested sample, not exact solid proof.
 direct=Vector((1,.3713907,.193723)).normalized();pos=pt+direct*3e-8;count=0
 for _ in range(80):
  hit,n,idx,d=tree.ray_cast(pos,direct,5)
  if hit is None:return bool(count%2)
  count+=1;pos=hit+direct*3e-7
 return None

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
 if kind=='pin-hub':return all(math.hypot(q.x-cx,q.y)<=.013 for q in pts)
 if kind=='pin-diffuser':
  ax=C['shade_width']/2;by=C['shade_depth']/2
  return all(.128<=math.hypot((q.x-cx)/ax,q.y/by)<=.165 for q in pts)
 return False
rows=[];unexpected=[];missing=[];badregion=[];containment=[]
for i,oa in enumerate(obs):
 va,ta,ba=D[oa.name]
 for ob in obs[i+1:]:
  vb,tb,bb=D[ob.name];hits=ba.overlap(bb);key=tuple(sorted((oa.name,ob.name)));kind=allowed.get(key)
  samplesA=va[::max(1,len(va)//96)];samplesB=vb[::max(1,len(vb)//96)]
  nearest=min([bb.find_nearest(q)[3] for q in samplesA]+[ba.find_nearest(q)[3] for q in samplesB])
  insA=sum(inside(q,bb) is True for q in samplesA);insB=sum(inside(q,ba) is True for q in samplesB)
  row={'a':oa.name,'b':ob.name,'policy':kind or 'must-be-disjoint','triangle_intersection_candidates':len(hits),'sampled_vertex_surface_min_mm':round(nearest*1000,4),'sampled_inside_vertices':[insA,insB]}
  if kind:
   if not hits:missing.append(row)
   # Use intersection segment midpoint estimates, not remote vertices of long cylinder faces.
   contact_points=[]
   for ia,ib in hits:
    for idx in ta[ia]:
     q=va[idx];near=bb.find_nearest(q)
     if near[3]<.0025:contact_points.append((q+near[0])/2)
    for idx in tb[ib]:
     q=vb[idx];near=ba.find_nearest(q)
     if near[3]<.0025:contact_points.append((q+near[0])/2)
   row['bounded_contact_samples']=len(contact_points);row['region_passed']=bool(contact_points) and region_ok(kind,contact_points)
   if not row['region_passed']:badregion.append(row)
  else:
   if hits:unexpected.append(row)
   if insA or insB:containment.append(row)
  rows.append(row)
# Shell/diffuser minimum distance is sampled in both directions and independently forbidden to intersect/contain.
clearance=next(r for r in rows if r['a'].startswith('01') and r['b'].startswith('02'))
report={'blender_version':bpy.app.version_string,'variant':C['name'],'recipe_version':info['recipe_version'],'mesh_objects':len(obs),'triangles':sum(len(x[1]) for x in D.values()),'degenerate_triangles':degenerate,'duplicate_triangles':duplicate,'nonmanifold_edges':nonmanifold,'non_positive_volume':negative,'nonadjacent_self_intersection_candidates':selfhits,'coplanar_positive_area_overlaps':coplanar,'all_28_pair_classifications':rows,'unexpected_intersection_pairs':unexpected,'missing_expected_contact_pairs':missing,'contact_region_failures':badregion,'unexpected_containment_samples':containment,'shell_diffuser_clearance':clearance,'thresholds':{'degenerate_area_m2':1e-12,'duplicate_vertex_round_m':1e-8,'coplanar_plane_distance_m':1e-8,'positive_overlap_axis_m':1e-8},'limits':['BVH nonadjacent triangles excludes shared vertices; coplanar SAT adds adjacent overlap checks, not complete interval proof.','Containment checks use sampled vertices and oblique ray parity; unsampled tiny islands can be missed.','Nearest-surface sampling is not exact all-edge global minimum.','Socket bounds certify this static model contact region, not manufacturing tolerances or electrical safety.','WebGL/GPU/iPhone/dynamic z-fighting not tested; no browser GL security override.']}
report['passed']=not any([degenerate,duplicate,nonmanifold,negative,selfhits,coplanar,unexpected,missing,badregion,containment])
Path(a.report).write_text(json.dumps(report,indent=2,ensure_ascii=False));print('QA',C['name'],report['passed'], 'defects',len(degenerate),len(duplicate),len(nonmanifold),len(selfhits),len(coplanar),'assembly',len(unexpected),len(missing),len(badregion),len(containment))
if not report['passed']:raise RuntimeError('Vesper static gate rejected; see report')
