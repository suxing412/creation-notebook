"""NACRE / 潮翼 — Study 002. Original closed parametric ceramic glider.
Recommended: python source/run.py --config configs/baseline.json --output my-wing
No downloaded mesh, texture or AI generation dependency.
"""
import bpy, math, os, json, shutil
from math import sin,cos,pi,sqrt,exp
from mathutils import Vector
import sys, argparse, re
from pathlib import Path
parser=argparse.ArgumentParser(description='Bounded ceramic wing recipe v1')
parser.add_argument('--config',required=True)
parser.add_argument('--output',required=True)
parser.add_argument('--geometry-only',action='store_true')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
C=json.loads(Path(args.config).read_text())
BOUNDS={'span':(8.5,11.5),'chord_factor':(.9,1.08),'leading_exponent':(1.5,1.9),'tail_factor':(.85,1.15)}
if set(C)!=set(BOUNDS)|{'name','seed'}: raise ValueError('Config keys must exactly match schema')
if not isinstance(C['name'],str) or not re.fullmatch('[A-Za-z0-9-]+',C['name']): raise ValueError('Invalid preset name')
if type(C['seed']) is not int or C['seed']!=0: raise ValueError('Only deterministic seed 0 supported; no random geometry')
for key,(lo,hi) in BOUNDS.items():
 if type(C[key]) not in (int,float) or not math.isfinite(C[key]) or not lo<=C[key]<=hi: raise ValueError(f'{key}: expected finite number in [{lo}, {hi}]')
def require_supported_version(version):
 if tuple(version)!=(4,3,2):
  raise RuntimeError('Unvalidated Blender version: this recipe requires exactly 4.3.2; port and revalidate before use')
require_supported_version(bpy.app.version)
A=str(Path(args.output).resolve()); E=A
os.makedirs(A,exist_ok=True)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def mat(n,c,metal=0,rough=.3):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;return m
IVORY=mat('01 | warm porcelain',(.78,.72,.59),.12,.29)
TEAL=mat('02 | deep petrol underside',(.023,.075,.077),.32,.3)
COPPER=mat('03 | satin copper seam',(.56,.245,.105),.8,.25)
DARK=mat('04 | recessed graphite',(.014,.022,.024),.15,.35)
def mesh(n,v,f,materials,ids=None):
 me=bpy.data.meshes.new(n);me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new(n,me);bpy.context.collection.objects.link(o)
 for m in materials:me.materials.append(m)
 for i,p in enumerate(me.polygons):p.use_smooth=True;p.material_index=ids[i] if ids else 0
 # Consistent outward normals are ensured explicitly by signed volume below.
 if sum(Vector(me.vertices[p.vertices[0]].co).dot(Vector(me.vertices[p.vertices[1]].co).cross(Vector(me.vertices[p.vertices[2]].co))) for p in me.polygons)<0:
  for p in me.polygons:p.flip()
 return o
def section(u,t):
 # Leading and trailing boundaries converge at tips; right wing lifts more.
 a=abs(u);lead=-2.6+3.8*a**C['leading_exponent'];trail=2.05-.85*a-1.2*sin(pi*a)**1.2
 mid=(lead+trail)/2;chord=(trail-lead)/2
 y=(mid+chord*cos(t))*C['chord_factor']
 camber=.16*(1-cos(t)**2)*(1-a)
 thickness=(.085+.50*exp(-(u/.25)**2))*(1-a*a)**.48
 z=1.55+.75*a**3+.24*u**3+camber+thickness*sin(t)
 return (C['span']/2*u,y,z)
N=100;M=48;verts=[section(-1,0)];faces=[];ids=[]
for i in range(1,N):
 u=-cos(pi*i/N)
 for j in range(M):verts.append(section(u,2*pi*j/M))
verts.append(section(1,0));end=len(verts)-1
for j in range(M):faces.append((0,1+(j+1)%M,1+j));ids.append(0 if j<M//2 else 1)
for i in range(N-2):
 for j in range(M):
  q=1+i*M;faces.append((q+j,q+(j+1)%M,q+M+(j+1)%M,q+M+j));ids.append(0 if j<M//2 else 1)
for j in range(M):q=1+(N-2)*M;faces.append((q+j,q+(j+1)%M,end));ids.append(0 if j<M//2 else 1)
body=mesh('A | continuous porcelain wing',verts,faces,[IVORY,TEAL],ids)
def tube(n,coords,r,material,sides=8,radii=None,flatten=1):
 v=[];f=[]
 for i,c in enumerate(coords):
  c=Vector(c);t=(Vector(coords[min(i+1,len(coords)-1)])-Vector(coords[max(0,i-1)])).normalized();ref=Vector((0,0,1));u=t.cross(ref).normalized();w=t.cross(u).normalized();rr=r*(radii[i] if radii else 1)
  for j in range(sides):v.append(c+rr*(cos(2*pi*j/sides)*u+flatten*sin(2*pi*j/sides)*w))
 for i in range(len(coords)-1):
  for j in range(sides):f.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
 f += [tuple(reversed(range(sides))),tuple((len(coords)-1)*sides+j for j in range(sides))]
 return mesh(n,v,f,[material])
# Copper structural seam is embedded in the actual boundary, not detached ornament.
for edge,t in [('leading',pi),('trailing',0)]:
 coords=[section(-cos(pi*i/120),t) for i in range(121)]
 tube('B | '+edge+' copper seam',coords,.016,COPPER,8)
# Two quiet inset sweep lines follow the upper shell and reinforce span direction.
for side in [-1,1]:
 coords=[]
 for i in range(65):
  u=side*(.12+.79*i/64);t=2.18-.47*i/64;p=list(section(u,t));p[2]+=.006;coords.append(p)
 tube('C | swept copper inlay '+str(side),coords,.017,COPPER,6,flatten=.55)
# Long ceramic tail: shaped elliptical section and a single copper continuation.
coords=[];radii=[]
for i in range(65):
 t=i/64;coords.append((.36*sin(pi*t)*t,1.72*C['chord_factor']+3.55*C['tail_factor']*t,1.54+.26*sin(pi*t)-.25*t));radii.append(.01+(1-t)**1.2)
tube('E | tapered ceramic tail',coords,.29,IVORY,16,radii,.38)
tube('F | tail copper spine',[(x,y,z+.108*r) for (x,y,z),r in zip(coords,radii)],.018,COPPER,6,[max(.12,r) for r in radii])
# Small dark dorsal insert, flush enough to read as a seam rather than an eye.
coords=[]
for i in range(45):
 t=.35+2.42*i/44;p=list(section(0,t));p[2]+=.001;coords.append(p)
tube('G | copper dorsal midrib',coords,.035,COPPER,10,[.15+.85*sin(pi*i/44)**.7 for i in range(45)],.35)
parts=[o for o in bpy.data.objects if o.type=='MESH']
# Canonical framing / lighting scale: all model x spans become 10 units.
allpoints=[v.co.copy() for o in parts for v in o.data.vertices]
xlo=min(p.x for p in allpoints); xhi=max(p.x for p in allpoints)
ylo=min(p.y for p in allpoints); yhi=max(p.y for p in allpoints)
zlo=min(p.z for p in allpoints)
normalization=10/(xhi-xlo)
for o in parts:
 for v in o.data.vertices:
  v.co.x=(v.co.x-(xlo+xhi)/2)*normalization
  v.co.y=(v.co.y-(ylo+yhi)/2)*normalization
  v.co.z=(v.co.z-zlo)*normalization+.85
tri=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in parts)
# Test closed topology before publication: each mesh edge should meet two faces.
nonmanifold={}
for o in parts:
 edges={}
 for p in o.data.polygons:
  vv=list(p.vertices)
  for a,b in zip(vv,vv[1:]+vv[:1]):key=tuple(sorted((a,b)));edges[key]=edges.get(key,0)+1
 bad=sum(n!=2 for n in edges.values())
 if bad:nonmanifold[o.name]=bad
assert not nonmanifold,nonmanifold
for screen in bpy.data.screens:
 for ar in screen.areas:
  if ar.type=='FILE_BROWSER' and ar.spaces.active.params: ar.spaces.active.params.directory=b''
bpy.context.scene.render.filepath='//beauty.png'
# Save fully editable construction; export artifact only, retaining semantic part names.
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(A,'model.blend'))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=os.path.join(A,'model.glb'),export_format='GLB',use_selection=True,export_apply=True)
info={'title':'NACRE / 潮翼','study':2,'sourceMeshObjects':len(parts),'renderMeshes':len(parts),'triangles':tri,'materials':3,'topologyAssertionNonManifoldEdges':sum(nonmanifold.values()),'validationStatus':'pending-full-QA','span':10,'config':C,'normalizationScale':normalization,'blenderVersion':bpy.app.version_string,'generator':'Blender 4.3.2 / closed parametric mesh','realtimeVerified':False}
json.dump(info,open(os.path.join(A,'model-info.json'),'w'),indent=2)
if args.geometry_only: sys.exit(0)
# Offline physical studio rendering, not a WebGL screenshot.
FLOOR=mat('Studio | warm chalk',(.34,.31,.265),0,.68)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,.03));ground=bpy.context.object;ground.name='Studio floor';ground.data.materials.append(FLOOR)
def area(n,loc,power,color,size):
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=n;o.data.energy=power;o.data.color=color;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,1.5))-o.location).to_track_quat('-Z','Y').to_euler()
area('Large silk key',(-3,-4,10),1800,(1,.88,.72),7)
area('Cool softbox',(5,2,7),1300,(.72,.85,1),6)
area('Tail strip',(-1,7,5),1100,(1,.64,.37),5)
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';bpy.context.scene.camera=cam
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=96;s.cycles.seed=0;s.cycles.use_animated_seed=False;s.cycles.use_denoising=False;s.world.color=(.25,.25,.25);s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX';s.view_settings.exposure=0;s.view_settings.gamma=1;s.display_settings.display_device='sRGB';s.render.resolution_percentage=100
views=[('beauty',(9,-12,12),(0,0,1.5),14.6,800,680),('top',(0,0,18),(0,0,1.5),14.6,800,680),('front',(0,-18,1.8),(0,0,1.8),12,800,400),('side',(18,0,1.8),(0,0,1.8),14,800,400)]
for name,loc,target,scale,w,h in views:
 s.cycles.samples=128 if name=='beauty' else 48
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;s.render.resolution_x=w;s.render.resolution_y=h;s.render.filepath=os.path.join(A,name+'.png');bpy.ops.render.render(write_still=True)
# Save the actual render scene too, with no saved private file-browser directories.
for screen in bpy.data.screens:
 for ar in screen.areas:
  if ar.type=='FILE_BROWSER' and ar.spaces.active.params: ar.spaces.active.params.directory=b''
s.render.filepath='//beauty.png'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(A,'scene.blend'))
print('MODEL_STATS',json.dumps(info))
