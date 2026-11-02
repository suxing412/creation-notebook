"""Vesper / 暮灯 — original constrained lamp family, recipe 1.0.0.
Blender 4.3.2 only. No external textures, meshes, accounts, or image services.
"""
import bpy,bmesh,math,json,sys,argparse,re
from pathlib import Path
from mathutils import Vector
from math import sin,cos,pi
VERSION='1.1.0'
BOUNDS={'shade_width':(.33,.49),'shade_depth':(.27,.35),'shade_rise':(.05,.12),'rim_height':(.28,.53),'stem_lean':(.025,.065),'base_width':(.16,.21),'base_depth':(.13,.16),'crown_shift':(.008,.022)}
def validate(c,version=(4,3,2)):
 if tuple(version)!=(4,3,2):raise ValueError('Only Blender 4.3.2 is validated')
 if set(c)!=set(BOUNDS)|{'name','seed','recipe_version'}:raise ValueError('Config keys must match the exact contract')
 if not isinstance(c['name'],str) or not re.fullmatch('[a-z][a-z0-9-]{0,30}',c['name']):raise ValueError('Invalid name')
 if type(c['seed']) is not int or c['seed']!=0:raise ValueError('Only seed=0; deterministic geometry')
 if c['recipe_version']!=VERSION:raise ValueError('Recipe version mismatch')
 for k,(lo,hi) in BOUNDS.items():
  if type(c[k]) not in (int,float) or not math.isfinite(c[k]) or not lo<=c[k]<=hi:raise ValueError(f'{k}: finite number in [{lo},{hi}] required')
 if c['shade_width']/c['shade_depth']>1.7:raise ValueError('Shade aspect ratio exceeds 1.7')
 if c['shade_rise']/c['shade_width']>.36:raise ValueError('Dome slope boundary exceeded')
 if c['rim_height']/c['base_width']>3.3:raise ValueError('Visual support slenderness exceeds recipe limit; not a physical stability certificate')
 return c
p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True);p.add_argument('--geometry-only',action='store_true');p.add_argument('--views',default='beauty,front,side,top,junction,base-junction');p.add_argument('--draft',action='store_true')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);C=validate(json.loads(Path(a.config).read_text()),bpy.app.version)
out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for data in list(bpy.data.materials):bpy.data.materials.remove(data)
S=bpy.context.scene;S.unit_settings.system='METRIC';S.unit_settings.scale_length=1
N=128;NR=28
th=.006;gap=.010 if a.draft else .016;inset=.91 if a.draft else .86
lens_th=.004;lens_sag=.017;inner=.145;hub_r=.011;stem_r=.0105
ax=C['shade_width']/2;by=C['shade_depth']/2;rim=C['rim_height'];cx=C['stem_lean']/2

def material(name,color,metal,rough,emission=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;q=m.node_tree.nodes.get('Principled BSDF');q.inputs['Base Color'].default_value=(*color,1);q.inputs['Metallic'].default_value=metal;q.inputs['Roughness'].default_value=rough
 if emission:q.inputs['Emission Color'].default_value=(1,.59,.27,1);q.inputs['Emission Strength'].default_value=emission
 return m
shellmat=material('Vesper | mineral warm ivory',(.60,.53,.42),0,.31)
metal=material('Vesper | dark patinated bronze',(.071,.045,.026),.77,.29)
lensmat=material('Vesper | warm opal luminous ceramic',(.83,.72,.53),0,.28,1.2)

def mesh(name,verts,faces,mat):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
 ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);me.materials.append(mat)
 for f in me.polygons:f.use_smooth=True
 return ob

def lathe(name,profile,xscale,yscale,mat,center=(0,0),skew=0):
 # A profile contains single poles, not coincident full zero-radius rings.
 v=[];rings=[];f=[]
 for r,z in profile:
  if abs(r)<1e-12:
   rings.append([len(v)]);v.append((center[0]+skew,center[1],z))
  else:
   ids=[]
   for j in range(N):
    t=2*pi*j/N;ids.append(len(v));v.append((center[0]+xscale*r*cos(t)+skew*(1-r*r),center[1]+yscale*r*sin(t),z))
   rings.append(ids)
 def bridge(u,w):
  if len(u)==1:
   for j in range(N):f.append((u[0],w[j],w[(j+1)%N]))
  elif len(w)==1:
   for j in range(N):f.append((u[j],w[0],u[(j+1)%N]))
  else:
   for j in range(N):f.append((u[j],w[j],w[(j+1)%N],u[(j+1)%N]))
 for u,w in zip(rings,rings[1:]):bridge(u,w)
 # Closed annular profiles must be explicitly closed; pole-ended profiles need no extra caps.
 if len(rings[0])!=1:bridge(rings[-1],rings[0])
 return mesh(name,v,f,mat)

# The shade is a closed 6 mm vertical-thickness shell with rounded perimeter.
profile=[]
for i in range(NR+1):
 r=i/NR;profile.append((r,rim+C['shade_rise']*(1-r*r)**1.55+th/2))
for j in range(1,8):
 t=pi*j/8;profile.append((1+.003/((ax+by)/2)*sin(t),rim+th/2*cos(t)))
for i in range(NR,-1,-1):
 r=i/NR;profile.append((r,rim+C['shade_rise']*(1-r*r)**1.55-th/2))
shade=lathe('01 Shade - closed mineral shell',profile,ax,by,shellmat,(cx,0),C['crown_shift'])

def lens_z(r):return rim-gap-lens_sag*(1-(r/inset)**2)
p=[]
for i in range(25):
 r=inner+(inset-inner)*i/24;p.append((r,lens_z(r)+lens_th/2))
for j in range(1,8):
 t=pi*j/8;p.append((inset+.0015/((ax+by)/2)*sin(t),lens_z(inset)+lens_th/2*cos(t)))
for i in range(24,-1,-1):
 r=inner+(inset-inner)*i/24;p.append((r,lens_z(r)-lens_th/2))
for j in range(1,8):
 t=pi*j/8;p.append((inner-.001/((ax+by)/2)*sin(t),lens_z(inner)-lens_th/2*cos(t)))
diffuser=lathe('02 Diffuser - inset opal annulus',p,ax,by,lensmat,(cx,0))

# Compact weighted-looking oval base. Physical mass/stability are not simulated.
bh=.026
p=[(0,bh),(.84,bh),(.94,bh-.001),(.985,bh-.004),(1,bh-.008),(1,.007),(.985,.003),(.94,.001),(.84,0),(0,0)]
base=lathe('03 Base - rounded bronze plinth',p,C['base_width']/2,C['base_depth']/2,metal)

def tube(name,points,radii,mat,sides=48):
 v=[];f=[]
 for i,point in enumerate(points):
  tangent=(Vector(points[min(i+1,len(points)-1)])-Vector(points[max(i-1,0)])).normalized();ref=Vector((0,1,0)) if abs(tangent.y)<.9 else Vector((1,0,0));u=tangent.cross(ref).normalized();w=tangent.cross(u).normalized();r=radii[i]
  for j in range(sides):v.append(Vector(point)+r*(u*cos(2*pi*j/sides)+w*sin(2*pi*j/sides)))
 for i in range(len(points)-1):
  for j in range(sides):f.append((i*sides+j,(i+1)*sides+j,(i+1)*sides+(j+1)%sides,i*sides+(j+1)%sides))
 f.append(tuple(reversed(range(sides))));f.append(tuple((len(points)-1)*sides+j for j in range(sides)))
 return mesh(name,v,f,mat)

# Bent stem is straight at the top and bottom, and smooth through its restrained lean.
hub_bottom=rim-.050;stem_bottom=bh-.004;stem_top=hub_bottom+.004
points=[];radii=[]
for i in range(41):
 t=i/40;smooth=3*t*t-2*t*t*t
 points.append((-C['stem_lean']/2+C['stem_lean']*smooth,0,stem_bottom+(stem_top-stem_bottom)*t));radii.append(stem_r*(1-.15*t))
stem=tube('04 Stem - tapered S curve',points,radii,metal)
hub_top=rim+C['shade_rise']-th/2+.0015
hub_profile=[(0,hub_bottom),(.78,hub_bottom),(.94,hub_bottom+.0007),(1,hub_bottom+.002),(1,hub_top-.002),(.94,hub_top-.0007),(.78,hub_top),(0,hub_top)]
hub=lathe('05 Hub - concealed axial socket',hub_profile,hub_r,hub_r,metal,(cx,0))
# Three short radial pins are the only diffuser connections; named/pair-bounded in QA.
pinz=lens_z(inner)
for i in range(3):
 t=pi/2+2*pi*i/3
 # Continue 1.3 mm radially into the opal part, not through the surface in front of it.
 rr=inner+.0013/math.sqrt((ax*cos(t))**2+(by*sin(t))**2)
 end=(cx+ax*rr*cos(t),by*rr*sin(t),pinz)
 direction=Vector((end[0]-cx,end[1],0)).normalized();start=Vector((cx,0,pinz))+direction*(hub_r-.0015)
 tube(f'06 Pin {i+1} - diffuser locator',[start,end],[.0014,.0014],metal,20)
parts=[o for o in bpy.data.objects if o.type=='MESH']
# Pure model and GLB are free from the photographic floor/lights.
for o in parts:o['part_role']=o.name.split(' - ')[1];o['recipe_version']=VERSION
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='FILE_BROWSER' and area.spaces.active.params:area.spaces.active.params.directory=b''
S.render.filepath='//beauty.png'
bpy.ops.wm.save_as_mainfile(filepath=str((out/'model.blend').resolve()))
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str((out/'model.glb').resolve()),export_format='GLB',use_selection=True,export_apply=True,export_extras=False)
verts=[v.co for o in parts for v in o.data.vertices]
bounds=[[min(v[k] for v in verts),max(v[k] for v in verts)] for k in range(3)]
info={'title':'Vesper / 暮灯','study':'005','variant':C['name'],'recipe_version':VERSION,'seed':0,'config':C,'blender_version':bpy.app.version_string,'units':'metres','mesh_objects':len(parts),'triangles':sum(len(p.vertices)-2 for o in parts for p in o.data.polygons),'dimensions_mm':{k:round((bounds[i][1]-bounds[i][0])*1000,2) for i,k in enumerate(['width','depth','height'])},'bounds_m':bounds,'construction':{'shell_vertical_thickness_mm':6,'lens_thickness_mm':4,'lens_inset_ratio':inset,'shell_to_lens_rim_vertical_offset_mm':gap*1000,'hub_radius_mm':11,'base_height_mm':26,'stem_to_base_embed_mm':4,'stem_to_hub_embed_mm':4,'pin_radial_embed_mm':1.3},'validation_status':'pending','realtime_verified':False,'physical_engineering_verified':False,'materials':[m.name for m in [shellmat,metal,lensmat]],'phase':'before' if a.draft else 'after','studio':{'renderer':'Cycles CPU','hero_samples':1024,'orthographic_samples':384,'junction_samples':256,'denoiser':'none; this Blender build has no available Cycles denoiser','view_transform':'AgX','exposure':-.4,'resolution_hero':[900,1000]}}
(out/'model-info.json').write_text(json.dumps(info,indent=2,ensure_ascii=False))
if a.geometry_only:sys.exit(0)
# Fixed metric studio. Fixed camera and exposure make shape changes comparable.
floor=material('Studio only | warm stone',(.28,.25,.21),0,.75)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.0008));ground=bpy.context.object;ground.name='Studio floor';ground.data.materials.append(floor)
def light(name,loc,energy,color,size,target=(0,0,.26)):
 bpy.ops.object.light_add(type='AREA',location=loc);ob=bpy.context.object;ob.name=name;ob.data.energy=energy;ob.data.color=color;ob.data.shape='DISK';ob.data.size=size;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
light('Silk key',(-.55,-.70,1.30),70,(1,.89,.77),.85)
light('Cool fill',(.75,.15,.85),45,(.78,.86,1),.70)
light('Warm edge',(-.15,.70,1),55,(1,.74,.49),.55)
S.world.color=(.17,.17,.17)
bpy.ops.object.camera_add();cam=bpy.context.object;cam.name='Studio camera';cam.data.type='ORTHO';S.camera=cam
S.render.engine='CYCLES';S.cycles.device='CPU';S.cycles.seed=0;S.cycles.use_animated_seed=False;S.cycles.use_denoising=False;S.render.resolution_percentage=100;S.render.image_settings.file_format='PNG';S.view_settings.view_transform='AgX';S.view_settings.exposure=-.4;S.view_settings.gamma=1;S.display_settings.display_device='sRGB'
views={'beauty':((.9,-1.4,.83),(0,0,.29),.86,900,1000,1024),'front':((0,-2,.31),(0,0,.31),.80,840,840,384),'side':((2,0,.31),(0,0,.31),.80,840,840,384),'top':((0,0,2),(0,0,0),.66,840,840,384),'junction':((.42,-.65,rim-.06),(cx,0,rim+.015),.30,1000,800,256),'base-junction':((.22,-.38,.13),(-C['stem_lean']/2,0,.046),.25,1000,800,256)}
for name in a.views.split(','):
 loc,target,scale,w,h,samples=views[name];cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;S.render.resolution_x=w;S.render.resolution_y=h;S.cycles.samples=samples;S.render.filepath=str((out/(name+'.png')).resolve());bpy.ops.render.render(write_still=True)
# Leave scene camera in hero position, not the last detail camera.
loc,target,scale,w,h,samples=views['beauty'];cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;S.render.resolution_x=w;S.render.resolution_y=h;S.cycles.samples=samples;S.render.filepath='//beauty.png'
bpy.ops.wm.save_as_mainfile(filepath=str((out/'scene.blend').resolve()))
print('VESPER',json.dumps(info,ensure_ascii=False))
