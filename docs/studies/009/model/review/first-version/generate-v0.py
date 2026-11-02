import bpy,bmesh,sys,json,math,argparse,time
from pathlib import Path
from mathutils import Vector,Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent));import recipe
p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True);p.add_argument('--geometry-only',action='store_true');p.add_argument('--angles');p.add_argument('--samples',type=int,default=128);p.add_argument('--resolution',type=int,default=960);p.add_argument('--views',default='beauty,front,side,top,rear,joint');p.add_argument('--revision',type=int,default=0);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);start=time.time();c=recipe.validate(json.loads(Path(a.config).read_text()));kin=recipe.pose(c,json.loads(a.angles) if a.angles else None);out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
materials={}
def mat(name,color,rough,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(*color,1);n.inputs['Roughness'].default_value=rough;n.inputs['Metallic'].default_value=metal;materials[name]=m;return m
paint=mat('Midnight enamel',(.025,.075,.083),.29,.18);brass=mat('Satin warm metal',(.42,.24,.10),.3,.78);opal=mat('Opal diffuser',(.72,.69,.58),.36);black=mat('Rubber feet',(.025,.029,.028),.7)
objects=[];parts=[]
def mesh(name,v,f,material,transform=None,bevel=0):
 me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);me.materials.append(material);bpy.context.view_layer.objects.active=ob;ob.select_set(True)
 if bevel:
  mod=ob.modifiers.new('Manufactured edge radius','BEVEL');mod.width=bevel;mod.segments=3;mod.limit_method='ANGLE';mod.angle_limit=.4;bpy.ops.object.modifier_apply(modifier=mod.name)
 # Flat caps retain their planes; curved small faces smoothly interpolate.
 for face in me.polygons:face.use_smooth=face.area<.00015
 if transform:me.transform(transform);me.update()
 ob.select_set(False);objects.append(ob);parts.append({'name':name,'vertices':len(me.vertices),'polygons':len(me.polygons),'material':material.name});return ob

def trans(loc):return Matrix.Translation(Vector(loc))
def Ry(theta):return Matrix.Rotation(-theta,4,'Y')
def axisY():return Matrix.Rotation(math.pi/2,4,'X')
def lat(name,profile,material,loc=(0,0,0),rotation=None):
 v,f=recipe.lathe(profile);return mesh(name,v,f,material,trans(loc)@(rotation or Matrix.Identity(4)))
def cyl(name,r,z0,z1,material,loc=(0,0,0),rotation=None,edge=.0004):
 e=min(edge,(z1-z0)/4,r/4);return lat(name,[(0,z0),(r-e,z0),(r,z0+e),(r,z1-e),(r-e,z1),(0,z1)],material,loc,rotation)
def plate(name,length,loc,angle,material=paint):
 return mesh(name,*recipe.plate(length),material,trans(loc)@Ry(angle),bevel=.00065)
R=c['base_radius'];lat('Base body',[(0,.005),(R-.005,.005),(R,.009),(R,.022),(R-.005,.026),(0,.026)],paint)
# Small feet are intentional support; their top plane stops below the base to avoid coincident surfaces.
for i in range(3):
 q=2*math.pi*i/3;loc=(R*.65*math.cos(q),R*.65*math.sin(q),0);cyl('Foot '+str(i+1),.012,0,.0048,black,loc)
# Fixed upright has a second real bore buried inside the base mounting region.
plate('Fixed upright',.08,(0,.009,.03),math.pi/2)
A=kin['shoulder'];B=kin['elbow'];C=kin['head_pivot'];D=kin['head_center'];plate('Lower arm',c['lower_length'],(A[0],-.009,A[2]),kin['lower_angle']);plate('Upper arm',c['upper_length'],(B[0],.009,B[2]),kin['upper_angle']);plate('Head neck',.095,(C[0],-.009,C[2]),kin['head_angle'])
for name,P in [('Shoulder',A),('Elbow',B),('Head',C)]:
 # Native lathe Z becomes negative Y; symmetric shaft and separated outer cap plates.
 cyl(name+' axle',recipe.PIN_R,-.0165,.0165,brass,P,axisY(),.00015)
 for side in [-1,1]:
  cyl(name+' cap '+str(side),.010,-.002,.002,brass,(P[0],side*.019,P[2]),axisY(),.0004)
# Upper cup is closed, underside recess real. Lens is smaller than inner bore and sits below cavity ceiling.
r=c['head_radius'];profile=[(0,.012),(r-.003,.012),(r,.009),(r,-.008),(r-.003,-.011),(r-.005,-.011),(r-.005,.002),(0,.002)]
rot=Ry(kin['head_angle']);lat('Head housing',profile,paint,D,rot);cyl('Diffuser',r-.0065,-.008,-.005,opal,D,rot,.0006)
# The neck enters the closed upper body; the joint region is declared, not whole-pair ignored.
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='FILE_BROWSER' and area.spaces.active.params:area.spaces.active.params.directory=b''
s.render.filepath='//beauty.png';bpy.ops.wm.save_as_mainfile(filepath=str((out/'model.blend').resolve()));bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=objects[0];bpy.ops.export_scene.gltf(filepath=str((out/'model.glb').resolve()),export_format='GLB',use_selection=True,export_apply=True,export_extras=False)
pts=[o.matrix_world@v.co for o in objects for v in o.data.vertices];bounds=[[min(p[i] for p in pts),max(p[i] for p in pts)] for i in range(3)]
views={'beauty':{'location':[.85,-1.25,.82],'target':[.16,0,.25],'ortho_scale':.75},'front':{'location':[.17,-1.4,.26],'target':[.17,0,.26],'ortho_scale':.73},'side':{'location':[1.4,0,.27],'target':[.17,0,.27],'ortho_scale':.73},'top':{'location':[.17,0,1.5],'target':[.17,0,.27],'ortho_scale':.73},'rear':{'location':[-.65,1.2,.75],'target':[.16,0,.25],'ortho_scale':.75},'joint':{'location':[B[0]+.13,-.24,B[2]+.10],'target':list(B),'ortho_scale':.11}}
info={'study':'009','title':'HINGE / 折光','variant':c['name'],'config':c,'pose':kin,'recipe_version':recipe.VERSION,'blender_version':bpy.app.version_string,'seed':0,'parts':parts,'bounds_m':bounds,'units':'metres','assembly_contract':{'plate_thickness_m':.012,'moving_plate_y_centres_m':[-.009,.009],'nominal_y_clearance_m':.006,'bore_radius_m':recipe.HOLE_R,'axle_radius_m':recipe.PIN_R,'nominal_radial_clearance_m':recipe.HOLE_R-recipe.PIN_R,'fixed_base_embed_region':'Fixed upright / Base body, z <= 0.026 m; inspect local contacts','head_neck_contact_region':'Head neck / Head housing, local lamp radius <= R and local z within housing upper material; lens contact forbidden','feet_gap_m':.0002},'studio':{'renderer':'Cycles CPU','samples':a.samples,'resolution':[a.resolution,a.resolution],'seed':0,'denoising':False,'view_transform':'AgX','fixed_camera':True,'views':views},'revision':a.revision,'gpu_verified':False,'manufacturing_verified':False}
(out/'model-info.json').write_text(json.dumps(info,indent=2,ensure_ascii=False));(out/'config.json').write_text(json.dumps(c,indent=2))
if a.geometry_only:sys.exit(0)
groundmat=mat('Studio warm grey',(.28,.27,.245),.8);bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.0002));bpy.context.object.data.materials.append(groundmat)
def light(name,loc,energy,size):
 bpy.ops.object.light_add(type='AREA',location=loc);q=bpy.context.object;q.name=name;q.data.energy=energy;q.data.shape='DISK';q.data.size=size;q.rotation_euler=(Vector((.15,0,.25))-q.location).to_track_quat('-Z','Y').to_euler()
light('Key',(-.65,-.7,1.1),85,.75);light('Fill',(.9,-.15,.6),28,.7);light('Rim',(.1,.6,.95),55,.6);s.world.color=(.22,.22,.22)
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';s.camera=cam;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=a.samples;s.cycles.seed=0;s.cycles.use_animated_seed=False;s.cycles.use_denoising=False;s.cycles.use_adaptive_sampling=False;s.render.resolution_percentage=100;s.render.resolution_x=a.resolution;s.render.resolution_y=a.resolution;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX';s.view_settings.exposure=0;s.view_settings.gamma=1
for name in a.views.split(','):
 d=views[name];cam.location=d['location'];cam.rotation_euler=(Vector(d['target'])-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=d['ortho_scale'];s.render.filepath=str((out/(name+'.png')).resolve());bpy.ops.render.render(write_still=True)
d=views['beauty'];cam.location=d['location'];cam.rotation_euler=(Vector(d['target'])-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=d['ortho_scale'];s.render.filepath='//beauty.png';bpy.ops.wm.save_as_mainfile(filepath=str((out/'scene.blend').resolve()));info['elapsed_seconds']=round(time.time()-start,3);(out/'model-info.json').write_text(json.dumps(info,indent=2,ensure_ascii=False));print('HINGE COMPLETE',info['elapsed_seconds'])
