"""ORISON 007 — periodic analytic-frame sweep, metres; numerical finite family, not manufacture."""
import math,re
VERSION='1.0.0'
STATIONS=320
CORNER_STEPS=8
BOUNDS={'radius_x':(.085,.18),'radius_z':(.10,.22),'asymmetry':(-.16,.25),'depth_wave':(0,.042),'lean':(-.03,.03),'section_width':(.035,.072),'section_depth':(.026,.060),'corner_radius':(.006,.014),'roll_degrees':(0,30),'width_modulation':(0,.27)}
TAU=2*math.pi

def add(a,b):return tuple(x+y for x,y in zip(a,b))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def mul(a,s):return tuple(x*s for x in a)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def norm(a):return math.sqrt(dot(a,a))
def unit(a):return mul(a,1/norm(a))
def point(c,t):
 a,b=c['radius_x'],c['radius_z'];q=c['asymmetry']
 return (a*math.cos(t)*(1+q*math.sin(t)),c['depth_wave']*(.65*math.sin(2*t+.35)+.35*math.cos(3*t-.4))+c['lean']*math.sin(t),b*(math.sin(t)+.065*math.cos(2*t+.4)))
def derivatives(c,t):
 a,b=c['radius_x'],c['radius_z'];q=c['asymmetry'];d=c['depth_wave'];l=c['lean']
 v=(-a*math.sin(t)+a*q*math.cos(2*t),d*(1.3*math.cos(2*t+.35)-1.05*math.sin(3*t-.4))+l*math.cos(t),b*(math.cos(t)-.13*math.sin(2*t+.4)))
 acc=(-a*math.cos(t)-2*a*q*math.sin(2*t),d*(-2.6*math.sin(2*t+.35)-3.15*math.cos(3*t-.4))-l*math.sin(t),b*(-math.sin(t)-.26*math.cos(2*t+.4)))
 return v,acc

def frame(c,t,revision=1):
 v,_=derivatives(c,t);T=unit(v);N0=unit(cross((0,1,0),T));B0=cross(T,N0)
 angle=math.radians(c['roll_degrees'])*(math.sin(t+.45) if revision else 0)
 N=add(mul(N0,math.cos(angle)),mul(B0,math.sin(angle)));B=add(mul(N0,-math.sin(angle)),mul(B0,math.cos(angle)))
 return T,N,B

def section(c,t,revision=1):
 # Four genuine circular arcs joined by straight portions; no bevel shader and no caps.
 w=c['section_width']*(1+c['width_modulation']*math.sin(t-.25) if revision else 1);d=c['section_depth'];r=c['corner_radius'];out=[]
 for sx,sy,start in [(1,1,0),(-1,1,90),(-1,-1,180),(1,-1,270)]:
  for j in range(CORNER_STEPS+1):
   a=math.radians(start+90*j/CORNER_STEPS);out.append((sx*(w/2-r)+r*math.cos(a),sy*(d/2-r)+r*math.sin(a)))
 return out

def diagnostics(c,revision=1,samples=640):
 pts=[];curv=[];align=[];rr=[]
 for i in range(samples):
  t=-math.pi/2+TAU*i/samples;v,a=derivatives(c,t);pts.append(point(c,t));curv.append(norm(cross(v,a))/norm(v)**3);align.append(norm(cross((0,1,0),unit(v))));rr.append(max(math.hypot(x,y) for x,y in section(c,t,revision)))
 maxprod=max(k*r for k,r in zip(curv,rr));maxradius=max(rr)
 # Exclude only local arc neighborhoods under 2.8*maximum section radius. This is sampled clearance, not a theorem.
 lengths=[norm(sub(pts[(i+1)%samples],pts[i])) for i in range(samples)];total=sum(lengths);s=[0]
 for l in lengths[:-1]:s.append(s[-1]+l)
 closest=(float('inf'),None)
 for i in range(samples):
  for j in range(i+1,samples):
   ds=min(s[j]-s[i],total-(s[j]-s[i]))
   if ds<=2.8*maxradius:continue
   gap=norm(sub(pts[i],pts[j]))-rr[i]-rr[j]
   if gap<closest[0]:closest=(gap,(i,j))
 return {'samples':samples,'max_curvature_per_m':max(curv),'max_section_circumradius_m':maxradius,'max_curvature_radius_product':maxprod,'minimum_frame_reference_sine':min(align),'sampled_nonlocal_clearance_m':closest[0],'closest_station_pair':closest[1],'nonlocal_arc_exclusion_m':2.8*maxradius,'centerline_length_m':total}

def validate(c,version=(4,3,2),revision=1,check_geometry=True):
 if tuple(version)!=(4,3,2):raise ValueError('Only Blender 4.3.2 is validated')
 if set(c)!=set(BOUNDS)|{'name','seed','recipe_version'}:raise ValueError('Exact configuration key set required')
 if not isinstance(c['name'],str) or not re.fullmatch('[a-z][a-z0-9-]{0,30}',c['name']):raise ValueError('Invalid name')
 if type(c['seed']) is not int or c['seed']!=0:raise ValueError('Only integer seed 0 is supported')
 if c['recipe_version']!=VERSION:raise ValueError('Recipe version mismatch')
 if type(revision) is not int or revision not in (0,1):raise ValueError('Revision must be integer 0 or 1')
 for k,(lo,hi) in BOUNDS.items():
  if type(c[k]) not in (int,float) or not math.isfinite(c[k]) or not lo<=c[k]<=hi:raise ValueError(k+': finite numeric value in '+str((lo,hi))+' required')
 minw=c['section_width']*(1-c['width_modulation'] if revision else 1)
 if 2*c['corner_radius']>=min(minw,c['section_depth'])-.004:raise ValueError('Section corner radius consumes straight span; >=4mm straight margin required')
 if check_geometry:
  d=diagnostics(c,revision)
  if d['minimum_frame_reference_sine']<.65:raise ValueError('Analytic frame reference near singularity')
  if d['max_curvature_radius_product']>=.72:raise ValueError('Curvature times section circumradius must be <0.72')
  if d['sampled_nonlocal_clearance_m']<.006:raise ValueError('Sampled nonlocal tube clearance must be >=6mm')
 return c

def geometry(c,revision=1):
 verts=[];faces=[];stations=[];n=STATIONS;m=4*(CORNER_STEPS+1)
 for i in range(n):
  t=-math.pi/2+TAU*i/n;p=point(c,t);T,N,B=frame(c,t,revision);ring=section(c,t,revision)
  for x,y in ring:verts.append(add(p,add(mul(N,x),mul(B,y))))
  stations.append({'index':i,'t':t,'center':p,'tangent':T,'normal':N,'binormal':B,'width_m':c['section_width']*(1+c['width_modulation']*math.sin(t-.25) if revision else 1)})
 # The single endpoint is shared by modulo indices. No duplicate endpoint ring, end caps or weld modifier.
 for i in range(n):
  ni=(i+1)%n
  for j in range(m):
   nj=(j+1)%m;faces.append((i*m+j,i*m+nj,ni*m+nj,ni*m+j))
 zmin=min(v[2] for v in verts);verts=[(x,y,z-zmin) for x,y,z in verts]
 for s in stations:s['center']=(s['center'][0],s['center'][1],s['center'][2]-zmin)
 return verts,faces,{'revision':revision,'stations':stations,'station_count':n,'cross_section_vertices':m,'corner_steps':CORNER_STEPS,'vertical_translation_m':-zmin,'seam_station':0,'seam_parameter':-math.pi/2,'frame_method':'analytic fixed-reference projection with periodic roll, not parallel transport / RMF','diagnostics':diagnostics(c,revision),'topology':'one connected watertight genus-1 sweep; modulo shared endpoint; no end caps'}
