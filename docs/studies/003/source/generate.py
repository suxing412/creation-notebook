"""UMBRA / 玄瞳. Original layered conceptual iris, NOT production linkage.
blender -b -t 8 --python source/generate.py
Optional IRIS_DRAFT=1 creates first-study preview. Units are arbitrary.
"""
import bpy, math, os, json, shutil
from math import sin,cos,pi
from mathutils import Vector
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); A=R+'/dist/assets'; E=R+'/evidence';DRAFT=os.environ.get('IRIS_DRAFT')=='1'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def mat(n,c,m,r):
 a=bpy.data.materials.new(n);a.diffuse_color=(*c,1);a.use_nodes=True;p=a.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=m;p.inputs['Roughness'].default_value=r;return a
G=mat('Graphite / bead-blasted housing',(.025,.033,.039),.72,.32)
B=mat('Champagne brass / engraved index',(.56,.37,.14),.8,.3)
L=mat('Leaf / brushed dark steel',(.38,.42,.46) if DRAFT else (.095,.12,.14),.85,.19 if DRAFT else .42)
P=mat('Bearing / satin steel',(.28,.32,.35),.8,.3)
D=mat('Fastener / black oxide',(.012,.017,.022),.5,.32)
def mesh(n,v,f,material):
 me=bpy.data.meshes.new(n);me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new(n,me);bpy.context.collection.objects.link(o);me.materials.append(material)
 return o
def bevel(o,w=.025,segments=3):
 bpy.context.view_layer.objects.active=o;m=o.modifiers.new('Manufactured edge fillet','BEVEL');m.width=w;m.segments=segments;bpy.ops.object.modifier_apply(modifier=m.name)
 for p in o.data.polygons:p.use_smooth=True
 m=o.modifiers.new('Face weighted normals','WEIGHTED_NORMAL');m.keep_sharp=True;bpy.ops.object.modifier_apply(modifier=m.name)
 return o
def ring(n,inside,outside,z0,z1,material,bevelw=.02):
 # Cyclic rectangular cross-section; no seam endcaps.
 v=[];f=[];N=160
 for r,z in [(inside,z0),(outside,z0),(outside,z1),(inside,z1)]:
  for i in range(N):v.append((r*cos(i*2*pi/N),r*sin(i*2*pi/N),z))
 for j in range(4):
  for i in range(N):f.append((j*N+i,j*N+(i+1)%N,((j+1)%4)*N+(i+1)%N,((j+1)%4)*N+i))
 return bevel(mesh(n,v,f,material),bevelw)
def cyl(n,r,depth,loc,material,vertices=40):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=loc);o=bpy.context.object;o.name=n;o.data.materials.append(material);return bevel(o,min(.012,depth/5),2)
def box(n,loc,scale,material,angle=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=n;o.scale=scale;o.rotation_euler.z=angle;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);return bevel(o,min(scale)*.18,2)
base=ring('Housing_lower_flange',2.30,3.65,.16,.27,G)
body=ring('Housing_outer_barrel',3.35,3.65,.26,1.07,G)
cover=ring('Cover_front_bezel',2.30,3.65,1.06,1.21,G)
# Gold hairline lives in a separate physical groove gap, no coplanar duplicate ring.
ring('Brass_perimeter_band',3.645,3.670,.55,.60,B,.004)
ring('Foot_rear_rim',2.55,3.56,.06,.18,D,.014)
# Isolated eight fixed pin bearings. Blades have true through holes.
# Blade outline is an original constrained sweep envelope, clipped to a straight
# aperture edge x=-1.1. Intersect housing-clearance disks over the full angular range.
# This avoids the peripheral leakage left by the earlier hand-drawn narrow petals.
poly=[(-1.1,-5),(5,-5),(5,5),(-1.1,5)]
def clip(poly,nx,ny,d):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  da=nx*a[0]+ny*a[1]-d;db=nx*b[0]+ny*b[1]-d
  if da<=0:out.append(a)
  if (da<=0)!=(db<=0):
   t=da/(da-db);out.append((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])))
 return out
for alpha in range(56):
 for k in range(160):
  b=k*2*pi/160;a=math.radians(alpha)
  poly=clip(poly,cos(b-a),sin(b-a),3.30-2.65*cos(b))
pivots=[]
for i in range(8):
 theta=2*pi*i/8;x,y=2.65*cos(theta),2.65*sin(theta);z=.36+i*.065
 cyl('Fixed_shaft_%02d'%i,.052,.058,(x,y,z-.002),P)
 box('Cantilever_%02d'%i,(3.04*cos(theta),3.04*sin(theta),z-.027),(.80,.20,.014),G,theta)
 # base and cap support are deliberately separated from the rotating leaf stack.
 cyl('Bearing_base_%02d'%i,.13,.016,(x,y,z-.025),B)
 cyl('Bearing_cap_%02d'%i,.115,.008,(x,y,z+.024),P)
 pivot=bpy.data.objects.new('Pivot_%02d'%i,None);bpy.context.collection.objects.link(pivot);pivot.location=(x,y,z);pivot.rotation_euler.z=theta+math.radians(27.5);pivots.append(pivot)
 n=len(poly);v=[(x,y,zz) for zz in [-.013,.013] for x,y in poly];f=[tuple(reversed(range(n))),tuple(range(n,2*n))]
 f += [(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
 leaf=mesh('Blade_%02d'%i,v,f,L)
 # Model genuine bearing hole rather than hiding a pin crossing solid metal.
 bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.067,depth=.2);cut=bpy.context.object
 bpy.context.view_layer.objects.active=leaf;mod=leaf.modifiers.new('Bearing bore clearance','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
 bevel(leaf,.004,2);leaf.parent=pivot
# Flush brass scale pieces are intentional embeds (.003), not overlapping planes.
for i in range(64):
 t=2*pi*i/64;r=3.43;major=i%8==0;length=.15 if major else .055
 box('Scale_%02d'%i,(r*cos(t),r*sin(t),1.213),(length,.018,.012),B,t)
# Eight retaining screws occupy the front bezel; stem intentionally seats into it.
for i in range(8):
 t=2*pi*(i+.5)/8;r=2.94;x,y=r*cos(t),r*sin(t)
 screw=cyl('Retainer_%02d'%i,.084,.034,(x,y,1.223),D)
 # Actual screwdriver groove removed via boolean, not painted crossing box.
 cut=box('temporary slot',(x,y,1.245),(.115,.025,.045),D,t)
 bpy.context.view_layer.objects.active=screw;mod=screw.modifiers.new('Machined slot','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
# Physical single datum on rim; no claimed f-stop calibration.
box('Datum',(0,-3.64,1.221),(.10,.095,.035),B)
bpy.context.view_layer.update()
parts=[o for o in bpy.data.objects if o.type=='MESH']
if not DRAFT:
 bpy.ops.wm.save_as_mainfile(filepath=A+'/iris.blend')
 bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.gltf(filepath=A+'/iris.glb',export_format='GLB',use_selection=True,export_apply=True)
 info={'title':'UMBRA / 玄瞳','study':3,'sourceMeshObjects':len(parts),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in parts),'bladeThickness':.026,'layerPitch':.065,'axialGap':.039,'pivotRadius':2.65,'shaftRadius':.052,'bearingHoleRadius':.067,'motion':{'pivotNames':[p.name for p in pivots],'axis':[0,-1,0],'referenceDegrees':27.5,'minDegrees':0,'maxDegrees':55},'units':'arbitrary design units; not mm','mechanism':'Conceptual independent fixed-axis blades; no drive linkage','realtimeVerified':False}
 json.dump(info,open(A+'/model-info.json','w'),indent=2)
if os.environ.get('IRIS_MODEL_ONLY')=='1':
 shutil.copy2(__file__,A+'/generate.py')
 raise SystemExit(0)
# Studio geometry is not part of the exported GLB or editable artifact.
F=mat('Studio / charcoal',(.025,.031,.036),0,.68)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,0));bpy.context.object.name='Studio_ground';bpy.context.object.data.materials.append(F)
def light(n,loc,power,color,size):
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=n;o.data.energy=power;o.data.color=color;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,.5))-o.location).to_track_quat('-Z','Y').to_euler()
light('Warm large key',(-4,-2,8),1100,(1,.87,.69),6)
light('Cool edge strip',(3,4,6),1400,(.69,.82,1),4)
light('Broad fill',(1,-5,5),500,(1,1,1),5)
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';bpy.context.scene.camera=cam
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=48 if DRAFT else 128;s.cycles.use_denoising=False;s.world.color=(.20,.20,.20);s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX';s.render.resolution_percentage=100
views=[('beauty',(7,-10,13),(0,0,.55),10.3,1200,1050,27.5)]
if not DRAFT:views += [('state-'+name,(0,0,15),(0,0,.5),8.4,900,900,ang) for name,ang in [('closed',0),('mid',27.5),('open',55)]]+[('detail',(5,-5,8),(0,0,.6),8.3,1100,950,27.5),('assembly',(6,-7,11),(0,0,.55),8.5,1100,1000,27.5),('joint',(4,-5,1.8),(1.87383,-1.87383,.805),1.2,1100,850,27.5)]
for name,loc,target,scale,w,h,angle in views:
 if os.environ.get('IRIS_VIEWS') and name not in os.environ['IRIS_VIEWS'].split(','):continue
 if name=='joint':
  for o in parts:o.hide_render=o.name not in ['Blade_07','Fixed_shaft_07','Bearing_base_07','Bearing_cap_07','Cantilever_07']
 if name=='assembly':
  for o in parts:
   if o.name.startswith(('Cover_','Scale_','Retainer_','Housing_outer','Brass_perimeter','Datum')):o.hide_render=True
 for i,p in enumerate(pivots):p.rotation_euler.z=2*pi*i/8+math.radians(55-angle)
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;s.render.resolution_x=700 if DRAFT else w;s.render.resolution_y=620 if DRAFT else h;s.render.filepath=(E+'/iteration-01.png') if DRAFT else A+'/'+name+'.png';bpy.ops.render.render(write_still=True)
if not DRAFT:shutil.copy2(__file__,A+'/generate.py')
print('UMBRA_GENERATED',len(parts))
