"""HINGE 009: bounded kinematic desk-light family, metres, deterministic seed 0."""
import math
VERSION='009-hinge-1.0'
REQUIRED={'name','lower_length','upper_length','base_radius','head_radius','shoulder_deg','elbow_deg','head_deg','seed','version'}
RANGES={'lower_length':(.20,.28),'upper_length':(.20,.29),'base_radius':(.085,.12),'head_radius':(.052,.075),'shoulder_deg':(55,100),'elbow_deg':(-125,-70),'head_deg':(-25,20)}
PLATE_R=.015; HOLE_R=.0045; PIN_R=.004; THICK=.012; GAP=.006; A=(0,0,.11)
def validate(c):
 if not isinstance(c,dict) or set(c)!=REQUIRED:raise ValueError('exact_config_keys')
 if not isinstance(c['name'],str) or not c['name'].isascii() or not c['name'].replace('-','').isalnum():raise ValueError('name')
 if c['version']!=VERSION or type(c['seed']) is not int or c['seed']!=0:raise ValueError('version_seed')
 for k,(lo,hi) in RANGES.items():
  v=c[k]
  if type(v) not in (int,float) or not math.isfinite(v) or not lo<=v<=hi:raise ValueError('range:'+k)
 return dict(c)
def pose(c,angles=None):
 c=validate(c);q=[c['shoulder_deg'],c['elbow_deg'],c['head_deg']] if angles is None else angles
 if len(q)!=3:raise ValueError('pose_count')
 for v,k in zip(q,['shoulder_deg','elbow_deg','head_deg']):
  if type(v) not in (float,int) or not math.isfinite(v) or not RANGES[k][0]<=v<=RANGES[k][1]:raise ValueError('pose_range:'+k)
 t=math.radians(q[0]);u=t+math.radians(q[1]);h=math.radians(q[2]);B=(A[0]+c['lower_length']*math.cos(t),0,A[2]+c['lower_length']*math.sin(t));C=(B[0]+c['upper_length']*math.cos(u),0,B[2]+c['upper_length']*math.sin(u));D=(C[0]+.095*math.cos(h),-.009,C[2]+.095*math.sin(h));return {'angles_degrees':q,'shoulder':A,'elbow':B,'head_pivot':C,'head_center':D,'lower_angle':t,'upper_angle':u,'head_angle':h}
def plate(length,r=PLATE_R,hole=HOLE_R,thickness=THICK,segments=96):
 """Two stitched annular radial patches form one capsule plate with two genuine bores."""
 pts=[];lookup={};quads=[]
 def vid(p):
  key=tuple(round(x,12) for x in p)
  if key not in lookup:lookup[key]=len(pts);pts.append(key)
  return lookup[key]
 corner=math.atan2(r,length/2)
 angles=sorted(set([round(2*math.pi*i/segments,12) for i in range(segments)]+[round(x%(2*math.pi),12) for x in [corner,math.pi-corner,math.pi+corner,2*math.pi-corner]]))
 for center,sign in [(0,1),(length,-1)]:
  inner=[];outer=[]
  for a in angles:
   cs,sn=math.cos(a),math.sin(a)
   if cs*sign<=1e-12:rad=r
   else:rad=min((length/2)/abs(cs),r/max(abs(sn),1e-20))
   inner.append(vid((center+hole*cs,hole*sn)));outer.append(vid((center+rad*cs,rad*sn)))
  for i in range(len(angles)):j=(i+1)%len(angles);quads.append((inner[i],outer[i],outer[j],inner[j]))
 edges={}
 for f in quads:
  for i,j in zip(f,f[1:]+f[:1]):edges.setdefault(tuple(sorted((i,j))),[]).append((i,j))
 n=len(pts);v=[(x,-thickness/2,z) for x,z in pts]+[(x,thickness/2,z) for x,z in pts];faces=[]
 for f in quads:faces.append(tuple(reversed(f)));faces.append(tuple(i+n for i in f))
 for uses in edges.values():
  if len(uses)==1:i,j=uses[0];faces.append((i,j,j+n,i+n))
 return v,faces

def lathe(profile,segments=96):
 """Closed radial/z polygon swept about Z; axis vertices shared."""
 v=[];rings=[]
 for radius,z in profile:
  if radius==0:rings.append([len(v)]*segments);v.append((0,0,z))
  else:
   rings.append(list(range(len(v),len(v)+segments)));v.extend((radius*math.cos(2*math.pi*i/segments),radius*math.sin(2*math.pi*i/segments),z) for i in range(segments))
 f=[]
 for i in range(len(rings)):
  a,b=rings[i],rings[(i+1)%len(rings)]
  for j in range(segments):
   k=(j+1)%segments;face=[a[j],a[k],b[k],b[j]];face=list(dict.fromkeys(face))
   if len(face)>=3:f.append(tuple(face))
 return v,f
