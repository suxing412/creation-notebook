"""Topology + discrete motion sweep. Surface BVH is not solid containment proof."""
import bpy,os,json,math,collections
from mathutils.bvhtree import BVHTree
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));bpy.ops.wm.open_mainfile(filepath=R+'/dist/assets/iris.blend')
objs=[o for o in bpy.data.objects if o.type=='MESH'];static=[o for o in objs if not o.name.startswith('Blade_')];moving=[o for o in objs if o.name.startswith('Blade_')]
def data(o):
 me=o.data;me.calc_loop_triangles();v=[o.matrix_world@p.co for p in me.vertices];t=[tuple(p.vertices) for p in me.loop_triangles];box=[(min(p[k] for p in v),max(p[k] for p in v)) for k in range(3)]
 return (v,t,BVHTree.FromPolygons(v,t,all_triangles=True),box)
def overlaps(a,b):return all(a[k][1]>=b[k][0]-1e-7 and b[k][1]>=a[k][0]-1e-7 for k in range(3))
def coplanar(a,b,ids):
 va,ta,_,_=a;vb,tb,_,_=b;count=0
 for i,j in ids:
  pa=[va[k] for k in ta[i]];pb=[vb[k] for k in tb[j]];na=(pa[1]-pa[0]).cross(pa[2]-pa[0]).normalized();nb=(pb[1]-pb[0]).cross(pb[2]-pb[0]).normalized()
  if abs(na.dot(nb))>1-1e-7 and max(abs(na.dot(p-pa[0])) for p in pb)<1e-6:count+=1
 return count
allData={o.name:data(o) for o in objs};seen={};duplicate=[];degenerate=[];manifold={};selfhits={}
for o in objs:
 d=allData[o.name];v,t,tree,_=d;edges=collections.Counter()
 for p in o.data.polygons:
  vv=list(p.vertices)
  for a,b in zip(vv,vv[1:]+vv[:1]):edges[tuple(sorted((a,b)))]+=1
 bad=sum(c!=2 for c in edges.values())
 if bad:manifold[o.name]=bad
 for i,tri in enumerate(t):
  p=[v[k] for k in tri]
  if (p[1]-p[0]).cross(p[2]-p[0]).length/2<1e-10:degenerate.append([o.name,i])
  key=tuple(sorted(tuple(round(float(x),7) for x in p1) for p1 in p))
  if key in seen:duplicate.append([seen[key],[o.name,i]])
  seen[key]=[o.name,i]
 hits=[(a,b) for a,b in tree.overlap(tree) if a<b and not set(t[a]).intersection(t[b])]
 if hits:selfhits[o.name]=len(hits)
staticContacts=[];coplanarStatic=[]
for i,a in enumerate(static):
 for b in static[i+1:]:
  da=allData[a.name];db=allData[b.name]
  if not overlaps(da[3],db[3]):continue
  ids=da[2].overlap(db[2])
  if ids:
   cp=coplanar(da,db,ids);staticContacts.append({'a':a.name,'b':b.name,'trianglePairs':len(ids),'coplanar':cp})
   if cp:coplanarStatic.append([a.name,b.name,cp])
sweep=[];worst=0
for step in sorted([float(i) for i in range(56)]+[27.5]):
 for i in range(8):bpy.data.objects['Pivot_%02d'%i].rotation_euler.z=i*math.pi/4+math.radians(55-step)
 bpy.context.view_layer.update();dynamic={o.name:data(o) for o in moving};collisions=[]
 for i,a in enumerate(moving):
  for b in static+moving[i+1:]:
   da=dynamic[a.name];db=dynamic[b.name] if b.name in dynamic else allData[b.name]
   if not overlaps(da[3],db[3]):continue
   ids=da[2].overlap(db[2])
   if ids:collisions.append({'a':a.name,'b':b.name,'trianglePairs':len(ids),'coplanar':coplanar(da,db,ids)})
 sweep.append({'degrees':step,'collisions':collisions});worst=max(worst,len(collisions))
# Analytical maximum radius of each blade vertex over continuous local angle[0,55].
# Norm is convex over each mesh face, so vertices bound the whole polygonal mesh.
maxradius=0
for vertex in moving[0].data.vertices:
 x,y,_=vertex.co
 angles=[0,math.radians(55)]
 critical=math.atan2(-y,x)
 for k in [-1,0,1]:
  q=critical+k*2*math.pi
  if 0<=q<=math.radians(55):angles.append(q)
 maxradius=max(maxradius,max(math.sqrt(2.65**2+x*x+y*y+2*2.65*(x*math.cos(a)-y*math.sin(a))) for a in angles))
report={'objects':len(objs),'triangles':sum(len(d[1]) for d in allData.values()),'degenerateTriangles':degenerate,'duplicateTriangles':duplicate,'nonManifoldEdges':manifold,'nonAdjacentSelfIntersectionCandidates':selfhits,'staticContacts':staticContacts,'staticCoplanarCandidates':coplanarStatic,'motionSweep':sweep,'motionSampleCount':57,'maxDynamicCollisionGroups':worst,'analyticClearances':{'leafThickness':.026,'layerPitch':.065,'leafAxialGap':.039,'shaftRadius':.052,'boreRadius':.067,'radialBearingGap':.015,'maxContinuousBladeRadius':maxradius,'housingBoreRadius':3.35,'continuousRadialHousingGap':3.35-maxradius,'minimumBaseToLeafAxialGap':.004},'method':'World-space rounded 1e-7 duplicate triangles; triangle area <1e-10; edge valence; non-adjacent BVH; AABB+BVH at each integer degree 0..55 inclusive plus27.5; plane tolerance1e-6. Static contact requires classification.','limits':['Sampled motion is not a proof of all continuous positions.','Surface BVH misses complete containment; construction dimensions additionally constrain layer/bearing gaps.','No actual WebGL or depth-buffer flicker test.','Independent conceptual leaf pivots; no mechanical drive linkage or fabrication verification.']}
json.dump(report,open(R+'/evidence/geometry-check.json','w'),indent=2)
print(json.dumps({k:v for k,v in report.items() if k not in ['motionSweep','staticContacts']},indent=2));print('STATIC_CONTACTS',json.dumps(staticContacts));print('SWEEP_BAD',[r for r in sweep if r['collisions']])
# Explicit structural intent, not an assertion that all object intersections are wrong.
def classify(a,b):
 pair={a.split('_')[0],b.split('_')[0]}
 if a.startswith('Bearing_base') and b.startswith('Cantilever'):return 'bearing plinth embedded into its own support'
 if a.startswith('Bearing_') and b.startswith('Fixed_shaft'):return 'shaft retained by fixed bearing base/cap'
 if a.startswith('Cantilever') and b.startswith('Fixed_shaft'):return 'fixed shaft anchored in support'
 if a.startswith('Cantilever') and b=='Housing_outer_barrel':return 'cantilever anchored in housing wall'
 if a=='Cover_front_bezel' and b.startswith('Retainer'):return 'retaining screw seated in cover'
 if a=='Cover_front_bezel' and b.startswith('Scale'):return 'brass scale insert embedded by0.003'
 if {a,b}=={'Cover_front_bezel','Datum'}:return 'datum insert embedded in rim'
 if {a,b}=={'Brass_perimeter_band','Housing_outer_barrel'}:return 'brass band seated into barrel'
 if {a,b} in [{'Cover_front_bezel','Housing_outer_barrel'},{'Foot_rear_rim','Housing_lower_flange'},{'Housing_lower_flange','Housing_outer_barrel'}]:return 'static casing overlap joint; not Boolean fused'
 return None
classified=[dict(p,intent=classify(p['a'],p['b'])) for p in staticContacts]
json.dump({'groups':classified,'unclassified':[p for p in classified if not p['intent']]},open(R+'/evidence/contact-classification.json','w'),indent=2)
assert not duplicate and not degenerate and not manifold and not selfhits
assert worst==0 and 3.35-maxradius>.04
assert all(p['intent'] for p in classified)
