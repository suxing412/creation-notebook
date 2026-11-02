"""FOLIO continuous folded shell — deterministic geometric recipe, no fabrication claim."""
import math,re
VERSION='1.0.0'
BOUNDS={'width':(.18,.31),'height':(.13,.24),'display_angle':(55,75),'rear_angle':(53,72),'tray_depth':(.038,.060),'foot_depth':(.022,.045),'lip_height':(.020,.032),'bend_radius':(.006,.012),'thickness':(.0024,.0040)}
def validate(c,version=(4,3,2)):
 if tuple(version)!=(4,3,2):raise ValueError('Validated Blender version is 4.3.2 only')
 if set(c)!=set(BOUNDS)|{'name','seed','recipe_version'}:raise ValueError('Exact configuration keys required')
 if not isinstance(c['name'],str) or not re.fullmatch('[a-z][a-z0-9-]{0,30}',c['name']):raise ValueError('Invalid name')
 if type(c['seed']) is not int or c['seed']!=0:raise ValueError('Only deterministic seed 0 is supported')
 if c['recipe_version']!=VERSION:raise ValueError('Recipe version mismatch')
 for k,(lo,hi) in BOUNDS.items():
  if type(c[k]) not in (int,float) or not math.isfinite(c[k]) or not lo<=c[k]<=hi:raise ValueError(k+': finite number in '+str((lo,hi))+' required')
 if c['bend_radius']<=c['thickness']*1.6:raise ValueError('Inner bend radius margin failed')
 if c['lip_height']<c['bend_radius']+.008:raise ValueError('Lip must retain at least 8 mm straight segment')
 pts=control_points(c);trims=[]
 for i in range(1,len(pts)-1):
  u=unit(sub(pts[i],pts[i-1]));v=unit(sub(pts[i+1],pts[i]));turn=math.atan2(cross(u,v),dot(u,v));trims.append(c['bend_radius']*math.tan(abs(turn)/2))
 for i in range(len(pts)-1):
  available=norm(sub(pts[i+1],pts[i]))-(trims[i-1] if i else 0)-(trims[i] if i<len(trims) else 0)
  if available<.008:raise ValueError('Adjacent bend trims leave less than 8 mm straight segment')
 return c

def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def mul(a,s):return tuple(x*s for x in a)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def norm(a):return math.sqrt(dot(a,a))
def unit(a):return mul(a,1/norm(a))
def control_points(c):
 h=c['height'];t=c['thickness'];rear=c['tray_depth']+h/math.tan(math.radians(c['display_angle']))+h/math.tan(math.radians(c['rear_angle']))
 p=[(0,t/2+c['lip_height']),(0,t/2),(c['tray_depth'],t/2),(c['tray_depth']+h/math.tan(math.radians(c['display_angle'])),t/2+h),(rear,t/2),(rear+c['foot_depth'],t/2)]
 mid=(p[0][0]+p[-1][0])/2
 return [(y-mid,z) for y,z in p]

def profile(c):
 """Circular fillets, 2 degree maximum angular step; linear sections use <=8 mm step."""
 p=control_points(c);r=c['bend_radius'];samples=[];bends=[]
 def add_sample(q,tangent,label):
  if samples and norm(sub(samples[-1]['point'],q))<1e-10:return
  samples.append({'point':q,'tangent':tangent,'normal':(-tangent[1],tangent[0]),'segment':label})
 def line(a,b,label):
  v=unit(sub(b,a));n=max(1,math.ceil(norm(sub(b,a))/.008))
  for j in range(n+1):add_sample(add(a,mul(sub(b,a),j/n)),v,label)
 cursor=p[0]
 for i in range(1,len(p)-1):
  u=unit(sub(p[i],p[i-1]));v=unit(sub(p[i+1],p[i]));turn=math.atan2(cross(u,v),dot(u,v));sgn=1 if turn>0 else -1;trim=r*math.tan(abs(turn)/2);start=sub(p[i],mul(u,trim));end=add(p[i],mul(v,trim));center=add(start,mul((-u[1],u[0]),r*sgn));line(cursor,start,'line-'+str(i-1));n=max(4,math.ceil(abs(math.degrees(turn))/2));a0=math.atan2(start[1]-center[1],start[0]-center[0]);idx0=len(samples)-1
  for j in range(1,n+1):
   theta=a0+turn*j/n;q=add(center,(r*math.cos(theta),r*math.sin(theta)));tan=(-sgn*math.sin(theta),sgn*math.cos(theta));add_sample(q,tan,'bend-'+str(i))
  bends.append({'corner':i,'center_yz_m':center,'turn_deg':math.degrees(turn),'center_radius_mm':r*1000,'inside_radius_mm':(r-c['thickness']/2)*1000,'outside_radius_mm':(r+c['thickness']/2)*1000,'first_station':idx0,'last_station':len(samples)-1});cursor=end
 line(cursor,p[-1],'line-4')
 lengths=[0]
 for a,b in zip(samples,samples[1:]):lengths.append(lengths[-1]+norm(sub(b['point'],a['point'])))
 total=lengths[-1]
 for s,l in zip(samples,lengths):s['s']=l;s['u']=l/total
 return samples,bends

def width_ratio(u,revision=1):
 # Controlled lateral taper; one smooth function, no attached decorative parts.
 if revision==0:return 1.0
 knots=[(0,.86),(.10,.96),(.42,1),(.58,.90),(.84,.72),(1,.76)]
 for (x,a),(y,b) in zip(knots,knots[1:]):
  if x<=u<=y:
   q=(u-x)/(y-x);q=q*q*(3-2*q);return a+(b-a)*q
 return knots[-1][1]

def geometry(c,revision=1):
 samples,bends=profile(c);verts=[];faces=[];cs=[];edge=min(.00065,c['thickness']*.22);t=c['thickness'];corner_steps=5
 for q in samples:
  w=c['width']*width_ratio(q['u'],revision);yz=q['point'];normal=q['normal'];ring=[]
  # Counterclockwise rounded rectangle in local x/normal plane; exact paired normal offsets.
  for sx,sy,start in [(1,1,0),(-1,1,90),(-1,-1,180),(1,-1,270)]:
   for j in range(corner_steps+1):
    a=math.radians(start+90*j/corner_steps);x=sx*(w/2-edge)+edge*math.cos(a);d=sy*(t/2-edge)+edge*math.sin(a);ring.append(len(verts));verts.append((x,yz[0]+normal[0]*d,yz[1]+normal[1]*d))
  cs.append(ring)
 n=len(cs[0])
 for a,b in zip(cs,cs[1:]):
  for j in range(n):faces.append((a[j],a[(j+1)%n],b[(j+1)%n],b[j]))
 # Each end is one convex rounded-rectangle cap, with no coincident seam vertices.
 faces.append(tuple(reversed(cs[0])));faces.append(tuple(cs[-1]))
 return verts,faces,{'stations':samples,'bends':bends,'cross_section_vertices':n,'edge_radius_mm':edge*1000,'control_points_yz_m':control_points(c),'revision':revision}
