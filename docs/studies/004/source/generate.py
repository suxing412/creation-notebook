"""LIMEN / 岬界 — original coastal observatory architectural study.
Run: blender -b -t 8 --python source/generate.py
STUDY_VIEWS=beauty or STUDY_MODEL_ONLY=1. Units are nominal metres, not building certification.
"""
import bpy, bmesh, math, os, json, random
from math import sin,cos,pi
from mathutils import Vector
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));A=R+'/dist/assets';E=R+'/evidence'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def mat(n,c,metal=0,rough=.65):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;return m
stone=mat('Limestone / warm chalk',(.62,.57,.46));trim=mat('Cut limestone / pale edge',(.76,.70,.57));floor=mat('Terrace / honed limestone',(.43,.43,.37));rock=mat('Basalt / weathered coastal rock',(.15,.20,.21));bronze=mat('Bronze / brushed warm alloy',(.35,.20,.075),.78,.31);dark=mat('Bronze / patinated structure',(.055,.105,.10),.68,.4);glass=mat('Objective / smoky optical surface',(.032,.09,.12),.65,.15)
def mesh(n,v,f,ma):
 me=bpy.data.meshes.new(n);me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new(n,me);bpy.context.collection.objects.link(o);o.data.materials.append(ma);bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free();return o
def bevel(o,w=.025):
 bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('Softened construction arris','BEVEL');mod.width=w;mod.segments=2;bpy.ops.object.modifier_apply(modifier=mod.name);return o
def box(n,lo,hi,ma,edge=.015):
 bpy.ops.mesh.primitive_cube_add(size=1,location=tuple((a+b)/2 for a,b in zip(lo,hi)));o=bpy.context.object;o.name=n;o.scale=tuple(b-a for a,b in zip(lo,hi));bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(ma);return bevel(o,edge) if edge else o
def boolop(o,c,op='DIFFERENCE'):
 bpy.context.view_layer.objects.active=o;m=o.modifiers.new('True carved void','BOOLEAN');m.operation=op;m.solver='EXACT';m.object=c;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(c,do_unlink=True)
def prism(n,profile,depth,ma,axis='Y'):
 # x,z profile extruded along y; normal orientation recalculated globally below.
 v=[(x,y,z) for y in depth for x,z in profile];N=len(profile);f=[tuple(reversed(range(N))),tuple(range(N,2*N))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)]
 o=mesh(n,v,f,ma)
 if axis=='X':o.rotation_euler.z=pi/2
 return o
def archcut(cx,y0,y1,zbase,spring,r,axis='Y'):
 p=[(cx-r,zbase),(cx+r,zbase),(cx+r,spring)]+[(cx+r*cos(pi*i/32),spring+r*sin(pi*i/32)) for i in range(1,33)]
 return prism('temporary arch cutter',p,(y0,y1),stone,axis)
def cylinder(n,r,depth,loc,ma,N=48):
 bpy.ops.mesh.primitive_cylinder_add(vertices=N,radius=r,depth=depth,location=loc);o=bpy.context.object;o.name=n;o.data.materials.append(ma);return bevel(o,min(.012,depth*.1))
def beam(n,a,b,r,ma):
 a,b=Vector(a),Vector(b);o=cylinder(n,r,(b-a).length,(a+b)/2,ma,20);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
# Asymmetric continuous rock outcrop. No stacked sphere pile.
random.seed(44);N=31;vs=[]
radii=[1+random.uniform(-.13,.13) for i in range(N)]
for j,(sx,sy,z) in enumerate([(3.65,4.25,-.15),(4.12,4.70,.48),(3.65,3.30,1.30),(3.25,2.85,1.76)]):
 for i in range(N):
  t=2*pi*i/N;rr=radii[i]*(1+random.uniform(-.045,.045));vs.append((sx*rr*cos(t)+.25,sy*rr*sin(t)-.2,z+random.uniform(-.13,.13)))
vs.append((.2,0,1.72));top=len(vs)-1;vs.append((.1,0,-.35));bottom=len(vs)-1;fs=[]
for j in range(3):
 for i in range(N):
  a=j*N+i;b=j*N+(i+1)%N;c=(j+1)*N+(i+1)%N;d=(j+1)*N+i
  fs.extend([(a,b,d),(b,c,d)])
for i in range(N):fs += [(3*N+i,3*N+(i+1)%N,top),((i+1)%N,i,bottom)]
outcrop=mesh('Rock / single faceted outcrop',vs,fs,rock)
# Embedded rubble plinth reads as building support. Top promenade clear of rock peaks.
foundation=box('Foundation / embedded load bearing plinth',(-2.7,-1.6,1.35),(3.25,2.8,2.27),stone,.035)
# Stepped corner footings descend into the lower rock, so the plinth does not hover at its outer corners.
for x,y in [(-2.4,-1.3),(-2.4,2.5),(2.95,-1.3),(2.95,2.5)]:
 box('Foundation footing / '+str(x)+' '+str(y),(x-.22,y-.22,.32),(x+.22,y+.22,1.55),stone,.025)
box('Terrace / continuous slab',(-2.84,-1.74,2.24),(3.39,2.94,2.43),floor,.035)
# One hollow masonry room, genuine front and east arches. Body dimensions do not claim building regulation compliance.
hall=box('Hall / carved monolithic masonry',(-2.50,-.38,2.42),(.90,2.64,5.48),stone,0)
inner=box('temporary interior',(-2.14,-.02,2.25),(.54,2.28,5.70),stone,0);boolop(hall,inner)
boolop(hall,archcut(-.68,-.8,.2,2.20,4.02,.69))
# Rotated cut profile x becomes y; extrusion y becomes negative x.
c=archcut(1.02,-1.20,-.3,2.20,4.02,.69,'X');boolop(hall,c)
# Small real rear slit, not a dark decal.
c=box('temporary rear slit',(-1.69,2.1,3.18),(-1.37,2.9,4.37),stone,0);boolop(hall,c);bevel(hall,.022)
box('Roof / deep floating shadow eave',(-2.63,-.51,5.44),(1.03,2.77,5.65),floor,.035)
box('Roof / inset mineral cap',(-2.52,-.40,5.635),(.92,2.66,5.76),trim,.022)
# Voussoirs genuinely follow arch opening; narrow mortar gaps, no overlaid wall faces.
def archstones(prefix,cx,depth,spring,ri,ro,axis='Y'):
 for i in range(13):
  a=i*pi/13+.008;b=(i+1)*pi/13-.008
  p=[(cx+ri*cos(a),spring+ri*sin(a)),(cx+ro*cos(a),spring+ro*sin(a)),(cx+ro*cos(b),spring+ro*sin(b)),(cx+ri*cos(b),spring+ri*sin(b))]
  bevel(prism(prefix+' / voussoir %02d'%i,p,depth,trim,axis),.009)
archstones('Entry arch',-.68,(-.445,-.354),4.02,.715,.93)
archstones('East arch',1.02,(-.97,-.875),4.02,.715,.93,'X')
for x in [-1.50,.14]:box('Entry / cut jamb '+str(x),(x-.105,-.444,2.42),(x+.105,-.353,4.015),trim,.012)
for y in [.20,1.84]:box('East / cut jamb '+str(y),(.875,y-.105,2.42),(.97,y+.105,4.015),trim,.012)
# A single closed stair solid, twelve risers of 0.18m and treads0.25m, full width1.38.
# Stair climb points toward terrace and terminates flush in height, embedded0.03 in slab.
steps=12;start=-4.71;tread=.25;base=.27;rise=.18
profile=[(start,.05),(start,base+rise)]
for i in range(steps):
 end=start+(i+1)*tread;z=base+(i+1)*rise;profile.append((end,z))
 if i<steps-1:profile.append((end,z+rise))
profile += [(start+steps*tread,.05)]
# profile x temporarily encodes y. Rotate so width lies x.
stair=prism('Access / twelve continuous stone steps',profile,(-.02,1.36),stone,'X');stair.location.x=-.68;bevel(stair,.014)
# Stair x after rotation = [-1.36, .02]-.68 would not align. Explicit set width centered entry.
stair.location.x=.00 # x range -1.36.. .02, centered -.67 entry -.68
# Cut real stepped clearance in the rock, extending above walking surface.
clear=[(start-.70,-.14),(start+.05,-.14),(start+steps*tread,1.98),(start+steps*tread,8),(start-.70,8)]
c=prism('temporary stair excavation',clear,(-.12,1.48),rock,'X');boolop(outcrop,c)
box('Access / lower arrival threshold',(-1.36,start-.40,-.10),(.02,start+.01,.27),stone,.014)
# Guard rail follows gradient; footpoints on each tread, never through a higher tread.
for i in [0,3,6,9,11]:
 y=start+(i+.50)*tread;z=base+(i+1)*rise
 beam('Stair / guard post %02d'%i,(-1.24,y,z-.025),(-1.24,y,z+.90),.026,dark)
beam('Stair / rising handrail',(-1.24,start+.125,base+rise+.90),(-1.24,start+11.5*tread,base+12*rise+.90),.035,bronze)
# Purpose-built L/U plan polygons. No boolean union of coplanar touching boxes.
def plan_solid(n,p,z0,z1,ma,w):
 v=[(x,y,z) for z in [z0,z1] for x,y in p];N=len(p);f=[tuple(reversed(range(N))),tuple(range(N,2*N))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)]
 return bevel(mesh(n,v,f,ma),w)
west=[(-2.78,-1.67),(-1.48,-1.67),(-1.48,-1.41),(-2.52,-1.41),(-2.52,-.50),(-2.78,-.50)]
east=[(.12,-1.67),(3.36,-1.67),(3.36,2.88),(.98,2.88),(.98,2.62),(3.10,2.62),(3.10,-1.41),(.12,-1.41)]
wc=[(-2.815,-1.705),(-1.445,-1.705),(-1.445,-1.375),(-2.485,-1.375),(-2.485,-.465),(-2.815,-.465)]
ec=[(.085,-1.705),(3.395,-1.705),(3.395,2.915),(.945,2.915),(.945,2.585),(3.065,2.585),(3.065,-1.375),(.085,-1.375)]
for name,p,cap in [('west',west,wc),('east',east,ec)]:
 plan_solid('Parapet / '+name+' continuous corner',p,2.40,3.25,stone,.022)
 plan_solid('Coping / '+name+' continuous corner',cap,3.235,3.32,trim,.018)
# Observatory instrument: grounded pier, real fork and hollow bronze optical barrel.
tx,ty=2.03,.65
cylinder('Instrument / bolted base',.32,.09,(tx,ty,2.465),dark)
cylinder('Instrument / tapered pier',.13,.95,(tx,ty,2.96),dark)
cylinder('Instrument / azimuth bearing',.23,.12,(tx,ty,3.45),bronze)
for yy in [ty-.25,ty+.25]:
 box('Instrument / fork '+str(yy),(tx-.09,yy-.055,3.45),(tx+.09,yy+.055,3.91),dark,.025)
for side in [-1,1]:beam('Instrument / short altitude trunnion '+str(side),(tx,ty+side*.15,3.88),(tx,ty+side*.33,3.88),.075,bronze)
# Telescope points toward southeast and up25deg along localZ. Build complete closed tube cross section.
axis=Vector((.92,0,.39)).normalized();center=Vector((tx,ty,3.89));q=axis.to_track_quat('Z','Y')
def tube(n,rin,rout,z0,z1,ma):
 N=64;v=[];f=[]
 for r,z in [(rin,z0),(rout,z0),(rout,z1),(rin,z1)]:
  for i in range(N):v.append((r*cos(2*pi*i/N),r*sin(2*pi*i/N),z))
 for j in range(4):
  for i in range(N):f.append((j*N+i,j*N+(i+1)%N,((j+1)%4)*N+(i+1)%N,((j+1)%4)*N+i))
 o=bevel(mesh(n,v,f,ma),.008);o.rotation_euler=q.to_euler();o.location=center;return o
tube('Instrument / hollow optical tube',.135,.17,-.62,.75,bronze)
tube('Instrument / front lens rim',.139,.205,.66,.80,dark)
tube('Instrument / rear focusing drawtube',.055,.08,-.83,-.59,dark)
lens=cylinder('Instrument / recessed objective',.134,.018,center+axis*.685,glass);lens.rotation_euler=q.to_euler()
# Repair winding uniformly, preserve closed geometry.
import bmesh
for o in [o for o in bpy.data.objects if o.type=='MESH']:
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(o.data);bm.free()
bpy.context.view_layer.update();parts=[o for o in bpy.data.objects if o.type=='MESH'];tri=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in parts)
bpy.ops.wm.save_as_mainfile(filepath=A+'/limen.blend');bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.gltf(filepath=A+'/limen.glb',export_format='GLB',use_selection=True,export_apply=True)
json.dump({'title':'LIMEN / 岬界','study':4,'meshObjects':len(parts),'triangles':tri,'units':'nominal metres / conceptual architectural study only','stairs':{'risers':12,'rise':.18,'tread':.25,'width':1.38},'hallExternal':[3.40,3.02,3.06],'entryClearWidth':1.38,'terraceTop':2.43,'realtimeVerified':False},open(A+'/model-info.json','w'),indent=2)
if os.environ.get('STUDY_MODEL_ONLY')=='1':raise SystemExit(0)
# Studio ground excluded from saved modeling artifacts.
studio=mat('Studio / neutral sea mist',(.47,.53,.52));ground=box('Studio ground',(-100,-100,-.5),(100,100,-.4),studio,.0)
def light(n,loc,power,color,size):
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=n;o.data.energy=power;o.data.color=color;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,2))-o.location).to_track_quat('-Z','Y').to_euler();return o
key=light('Editorial daylight',(-5,-7,12),1800,(1,.94,.83),5);fill=light('Cool sky',(6,3,9),1400,(.73,.85,1),7);front=light('Open bounce',(2,-5,7),500,(1,1,1),6)
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';bpy.context.scene.camera=cam
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=96;s.cycles.use_denoising=False;s.world.color=(.25,.25,.25);s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX';s.view_settings.exposure=-.35;s.render.resolution_percentage=100
views=[('beauty',(11,-15,11),(0,-.3,2.1),12.8,1300,1100),('front',(0,-18,2.5),(0,-.5,2.5),11.2,1000,1000),('side',(18,-.4,2.5),(0,-.4,2.5),11.2,1000,1000),('top',(0,-.4,18),(0,-.4,0),11.5,1000,1000),('entry',(5,-10,6),(-.6,-.6,3.4),5.5,1100,950),('rear',(-11,14,10),(0,-.2,2.1),12.8,1100,1000),('dusk',(11,-15,11),(0,-.3,2.1),12.8,1300,1100)]
for n,loc,target,scale,w,h in views:
 if os.environ.get('STUDY_VIEWS') and n not in os.environ['STUDY_VIEWS'].split(','):continue
 ground.hide_render=n in ['front','side']
 s.cycles.samples=160 if n in ['beauty','dusk','entry'] else 80
 if n=='dusk':key.data.color=(1,.57,.25);key.data.energy=1250;fill.data.color=(.38,.55,1);fill.data.energy=550;front.data.energy=200;s.world.color=(.09,.12,.18)
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;s.render.resolution_x=w;s.render.resolution_y=h;s.render.filepath=A+'/'+n+'.png';bpy.ops.render.render(write_still=True)
print('LIMEN_GENERATED',len(parts),tri)
