"""VEIL 008: a perforated cylindrical normal-offset shell. Metres; no structural guarantee."""
import math,re
VERSION='1.0.0'
EDGE_STEPS=8
BEVEL_STEPS=4
BOUNDS={'width':(.24,.58),'height':(.28,.60),'curve_angle_degrees':(12,90),'thickness':(.006,.014),'columns':(3,10),'rows':(4,10),'aperture_ratio':(.46,.74),'gradient':(0,.22),'edge_radius':(.0006,.0018)}
INTEGER_KEYS={'columns','rows'}
TAU=math.tau

def surface(c,u,v,t=0):
 R=c['width']/math.radians(c['curve_angle_degrees']);angle=u/R
 return ((R+t)*math.sin(angle),R-(R+t)*math.cos(angle),v)
def normal(c,u):
 theta=u/(c['width']/math.radians(c['curve_angle_degrees']))
 return (math.sin(theta),-math.cos(theta),0)
def cell_parameters(c,revision=1):
 dx=c['width']/c['columns'];dy=c['height']/c['rows'];out=[]
 for row in range(c['rows']):
  for col in range(c['columns']):
   u=-c['width']/2+(col+.5)*dx;v=(row+.5)*dy
   field=.62*math.sin(math.pi*v/c['height'])+.38*math.sin(TAU*(u/c['width']+.5)+.4)
   scale=1+c['gradient']*field if revision else 1
   rx=dx*c['aperture_ratio']*.5*scale;ry=dy*c['aperture_ratio']*.5*scale
   out.append({'id':row*c['columns']+col,'row':row,'column':col,'center_uv':[u,v],'radii_uv':[rx,ry]})
 return out

def loop_angles():
 # Counterclockwise cell perimeter, including each corner once. Shared cell edges
 # have the very same 8 segments; integer-grid coordinates are deduplicated.
 pts=[]
 for j in range(EDGE_STEPS):pts.append((1,-1+2*j/EDGE_STEPS))
 for j in range(EDGE_STEPS):pts.append((1-2*j/EDGE_STEPS,1))
 for j in range(EDGE_STEPS):pts.append((-1,1-2*j/EDGE_STEPS))
 for j in range(EDGE_STEPS):pts.append((-1+2*j/EDGE_STEPS,-1))
 return [(x,y,math.atan2(y,x)) for x,y in pts]

def boundary_samples(c,revision=1,samples=128):
 b=c['edge_radius'] if revision else 0;res=[]
 for cell in cell_parameters(c,revision):
  u,v=cell['center_uv'];rx,ry=cell['radii_uv']
  res.append([surface(c,u+(rx+b)*math.cos(TAU*i/samples),v+(ry+b)*math.sin(TAU*i/samples),c['thickness']/2) for i in range(samples)])
 return res

def diagnostics(c,revision=1,samples=128):
 cells=cell_parameters(c,revision);b=c['edge_radius'] if revision else 0;dx=c['width']/c['columns'];dy=c['height']/c['rows'];margin=min(min(dx/2-q['radii_uv'][0]-b,dy/2-q['radii_uv'][1]-b) for q in cells)
 # Analytic conservative parameter-domain bound between cells, not an actual
 # surface ligament measurement. The checker separately samples real boundaries.
 gap=min(2*margin,margin)
 area=math.fsum(math.pi*(q['radii_uv'][0]+b)*(q['radii_uv'][1]+b) for q in cells)
 R=c['width']/math.radians(c['curve_angle_degrees'])
 return {'hole_count':len(cells),'genus':len(cells),'minimum_cell_margin_uv_m':margin,'conservative_uv_ligament_lower_bound_m':gap,'surface_open_area_ratio':area/(c['width']*c['height']),'cylinder_mid_radius_m':R,'inner_radius_m':R-c['thickness']/2,'curvature_times_half_thickness':c['thickness']/(2*R),'sampling_note':'Area is analytic smooth aperture footprint / developed mid-surface rectangle; not triangulated mesh area, projected visibility, porosity, or structural strength.'}

def validate(c,version=(4,3,2),revision=1,check_geometry=True):
 if tuple(version)!=(4,3,2):raise ValueError('Only Blender 4.3.2 is validated')
 if set(c)!=set(BOUNDS)|{'name','seed','recipe_version'}:raise ValueError('Exact configuration key set required')
 if not isinstance(c['name'],str) or not re.fullmatch('[a-z][a-z0-9-]{0,30}',c['name']):raise ValueError('Invalid name')
 if type(c['seed']) is not int or c['seed']!=0:raise ValueError('Only integer seed 0 is supported')
 if c['recipe_version']!=VERSION:raise ValueError('Recipe version mismatch')
 if type(revision) is not int or revision not in (0,1):raise ValueError('Revision must be integer 0 or 1')
 for k,(lo,hi) in BOUNDS.items():
  if type(c[k]) not in (int,float) or not math.isfinite(c[k]) or not lo<=c[k]<=hi:raise ValueError(k+': finite numeric value in '+str((lo,hi))+' required')
  if k in INTEGER_KEYS and type(c[k]) is not int:raise ValueError(k+': integer required')
 if 2*c['edge_radius']>c['thickness']-.002:raise ValueError('At least 2mm straight bore depth required')
 if check_geometry:
  d=diagnostics(c,revision)
  if d['minimum_cell_margin_uv_m']<.005:raise ValueError('Developed cell aperture margin must be >=5mm')
  if d['curvature_times_half_thickness']>=.05:raise ValueError('Thickness/curvature bound exceeded')
 return c

def geometry(c,revision=1):
 verts=[];faces=[];vertex_lookup={};roles=[];n=4*EDGE_STEPS;dx=c['width']/c['columns'];dy=c['height']/c['rows'];h=c['thickness']/2;b=c['edge_radius'] if revision else 0;holes=[]
 def vertex(u,v,t,role):
  key=tuple(round(x,12) for x in (u,v,t))
  if key not in vertex_lookup:vertex_lookup[key]=len(verts);verts.append(surface(c,u,v,t));roles.append([u,v,t,role])
  return vertex_lookup[key]
 def quad(a,b,c_,d,flip=False):faces.append((d,c_,b,a) if flip else (a,b,c_,d))
 for cell in cell_parameters(c,revision):
  u,v=cell['center_uv'];rx,ry=cell['radii_uv'];outer=[];profile=[]
  for sign in [1,-1]:
   outer.append([vertex(u+x*dx/2,v+y*dy/2,sign*h,'surface') for x,y,angle in loop_angles()])
  if revision:
   for j in range(BEVEL_STEPS+1):
    phi=math.pi/2*j/BEVEL_STEPS;profile.append((b*(1-math.sin(phi)),h-b*(1-math.cos(phi))))
   for j in range(BEVEL_STEPS,-1,-1):
    phi=math.pi/2*j/BEVEL_STEPS;profile.append((b*(1-math.sin(phi)),-h+b*(1-math.cos(phi))))
  else:profile=[(0,h),(0,-h)]
  rings=[]
  for offset,t in profile:
   rings.append([vertex(u+(rx+offset)*math.cos(angle),v+(ry+offset)*math.sin(angle),t,'hole') for x,y,angle in loop_angles()])
  for j in range(n):
   k=(j+1)%n
   # CCW in developed u,v points towards front (-Y).
   quad(outer[0][j],outer[0][k],rings[0][k],rings[0][j])
   quad(outer[1][j],outer[1][k],rings[-1][k],rings[-1][j],True)
   for z in range(len(rings)-1):quad(rings[z][j],rings[z][k],rings[z+1][k],rings[z+1][j],True)
  holes.append({**cell,'front_ring':rings[0],'back_ring':rings[-1],'bore_front_ring':rings[BEVEL_STEPS if revision else 0],'bore_back_ring':rings[BEVEL_STEPS+1 if revision else 1],'all_rings':rings,'profile':profile})
 # The only open edges after per-cell assembly are the exterior front/back rims.
 counts={}
 for f in faces:
  for a,bb in zip(f,f[1:]+f[:1]):
   key=tuple(sorted((a,bb)));counts.setdefault(key,[]).append((a,bb))
 front_edges=[]
 for key,edges in counts.items():
  if len(edges)==1 and abs(roles[key[0]][2]-h)<1e-10 and abs(roles[key[1]][2]-h)<1e-10:front_edges.append(edges[0])
 for a,bb in front_edges:
  ua,va,_,_=roles[a];ub,vb,_,_=roles[bb];aa=vertex(ua,va,-h,'surface');bbb=vertex(ub,vb,-h,'surface');quad(bb,a,aa,bbb)
 return verts,faces,{'revision':revision,'topology':'one connected watertight orientable shell; each through-hole adds one handle','construction_method':'shared 2D cell boundaries; analytic cylinder mapping; normal-offset shell and explicit rounded bore rings; no alpha texture or boolean','hole_count':len(holes),'genus':len(holes),'edge_steps':EDGE_STEPS,'hole_loop_vertices':n,'bevel_steps':BEVEL_STEPS if revision else 0,'holes':holes,'vertex_uvt':roles,'outer_front_edges':front_edges,**diagnostics(c,revision)}
