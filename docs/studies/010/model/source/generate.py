import bpy,bmesh,sys,json,math,argparse,time,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
sys.path.insert(0,str(Path(__file__).resolve().parent));import recipe
if bpy.app.version!=(4,3,2):raise RuntimeError('Pinned Blender 4.3.2')
p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True);p.add_argument('--geometry-only',action='store_true');p.add_argument('--revision',type=int,default=2);p.add_argument('--samples',type=int,default=128);p.add_argument('--resolution',type=int,default=960);p.add_argument('--views',default='beauty,front,side,top,joint,joint-exploded,exploded');a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);start=time.time();c=recipe.validate(json.loads(Path(a.config).read_text()));out=Path(a.output)
if (out/'model.blend').exists():raise FileExistsError('New output required')
out.mkdir(parents=True,exist_ok=True);bpy.context.preferences.filepaths.save_version=0;bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.scale_length=1

def mat(name,col,rough):
 m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);m.use_nodes=True;q=m.node_tree.nodes.get('Principled BSDF');q.inputs['Base Color'].default_value=(*col,1);q.inputs['Roughness'].default_value=rough;return m
railmat=mat('Oxide satin rails',(.22,.058,.028),.39);boardmat=mat('Warm mineral panels',(.52,.46,.34),.43);objects=[];parts=[]
def panel(name,profile,axis,center,material):
 n=len(profile);T=c['thickness'];v=[]
 for offset in [-T/2,T/2]:
  for u,z in profile:v.append((u,center+offset,z) if axis=='x' else (center+offset,u,z))
 f=[tuple(reversed(range(n))),tuple(i+n for i in range(n))]
 for i in range(n):j=(i+1)%n;f.append((i,j,j+n,i+n))
 me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);me.materials.append(material)
 bpy.context.view_layer.objects.active=ob;ob.select_set(True)
 mod=ob.modifiers.new('Small readable edge','BEVEL');mod.width=.00055;mod.segments=3;mod.limit_method='ANGLE';mod.angle_limit=.3;bpy.ops.object.modifier_apply(modifier=mod.name);ob.select_set(False)
 floor_shift=-min(v.co.z for v in me.vertices)
 for v in me.vertices:v.co.z+=floor_shift
 me.update()
 for face in me.polygons:face.use_smooth=True
 adjacency={}
 for face in me.polygons:
  for vi in face.vertices:adjacency.setdefault(vi,[]).append(face)
 normals=[]
 for face in me.polygons:
  for vi in face.vertices:
   normal=Vector((0,0,0))
   for other in adjacency[vi]:
    if face.normal.dot(other.normal)>.8:normal+=other.normal*other.area
   normals.append(tuple(normal.normalized()))
 me.normals_split_custom_set(normals);objects.append(ob);parts.append({'name':name,'axis':axis,'center_m':center,'vertices':len(me.vertices),'polygons':len(me.polygons),'floor_alignment_m':floor_shift});return ob
for i,y in enumerate([-c['depth']/2,c['depth']/2]):panel('Rail '+str(i+1),recipe.rail_profile(c,a.revision),'x',y,railmat)
for i,x in enumerate(recipe.stations(c)):panel('Divider '+str(i+1),recipe.divider_profile(c,a.revision),'y',x,boardmat)
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='FILE_BROWSER' and area.spaces.active.params:area.spaces.active.params.directory=b''
s.render.filepath='//beauty.png';bpy.ops.wm.save_as_mainfile(filepath=str((out/'model.blend').resolve()));bpy.ops.object.select_all(action='DESELECT')
for ob in objects:ob.select_set(True)
bpy.context.view_layer.objects.active=objects[0];bpy.ops.export_scene.gltf(filepath=str((out/'model.glb').resolve()),export_format='GLB',use_selection=True,export_apply=True,export_extras=False)
pts=[ob.matrix_world@v.co for ob in objects for v in ob.data.vertices];bounds=[[min(p[k]for p in pts),max(p[k]for p in pts)]for k in range(3)];joint=[recipe.stations(c)[0],-c['depth']/2,c['rail_height']/2]
views={'beauty':{'location':[.65,-.85,.40],'target':[0,0,.07],'ortho_scale':.62},'front':{'location':[0,-1.1,.12],'target':[0,0,.12],'ortho_scale':.54},'side':{'location':[1.1,0,.12],'target':[0,0,.12],'ortho_scale':.54},'top':{'location':[0,0,1.2],'target':[0,0,0],'ortho_scale':.54},'joint':{'location':[joint[0]-.08,joint[1]-.13,joint[2]+.12],'target':joint,'ortho_scale':.09},'joint-exploded':{'location':[joint[0]-.08,joint[1]-.13,joint[2]+.12],'target':[joint[0],joint[1],joint[2]+.025],'ortho_scale':.13},'exploded':{'location':[.65,-.85,.62],'target':[0,0,.12],'ortho_scale':.68}}
info={'study':'010','title':'SLOT / 栖格','variant':c['name'],'config':c,'recipe_version':recipe.VERSION,'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'recipe_sha256':hashlib.sha256(Path(recipe.__file__).read_bytes()).hexdigest(),'blender_version':bpy.app.version_string,'seed':0,'parts':parts,'bounds_m':bounds,'units':'metres','revision':a.revision,'contact_regions':[],'assembly_contract':{'slots':'top-open rail / bottom-open transverse panel','nominal_slot_width':c['thickness']+c['clearance'],'nominal_total_lateral_clearance':c['clearance'],'nominal_midplane_gap':c['clearance'],'nominal_profile_bottom_z':0,'actual_z_bounds_m':bounds[2],'engineering_validated':False},'studio':{'renderer':'Cycles CPU','samples':a.samples,'resolution':[a.resolution,a.resolution],'seed':0,'denoising':False,'view_transform':'AgX','views':views},'gpu_verified':False}
(out/'model-info.json').write_text(json.dumps(info,indent=2,ensure_ascii=False));(out/'config.json').write_text(json.dumps(c,indent=2))
if a.geometry_only:sys.exit(0)
ground=mat('Warm grey studio',(.3,.29,.27),.8);bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.0002));bpy.context.object.data.materials.append(ground)
def light(name,loc,energy,size):
 bpy.ops.object.light_add(type='AREA',location=loc);ob=bpy.context.object;ob.name=name;ob.data.energy=energy;ob.data.shape='DISK';ob.data.size=size;ob.rotation_euler=(Vector((0,0,.07))-ob.location).to_track_quat('-Z','Y').to_euler()
light('Key',(-.6,-.7,1.1),85,.8);light('Fill',(.7,-.2,.65),30,.7);light('Rim',(.2,.6,.9),50,.7);s.world.color=(.22,.22,.22);bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';s.camera=cam;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=a.samples;s.cycles.seed=0;s.cycles.use_animated_seed=False;s.cycles.use_denoising=False;s.cycles.use_adaptive_sampling=False;s.render.resolution_percentage=100;s.render.resolution_x=a.resolution;s.render.resolution_y=a.resolution;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX';s.view_settings.exposure=0;s.view_settings.gamma=1
for name in a.views.split(','):
 for ob in objects:ob.location.z=(.12 if name=='exploded' else .055 if name=='joint-exploded' else 0) if ob.name.startswith('Divider') else 0
 d=views[name];cam.location=d['location'];cam.rotation_euler=(Vector(d['target'])-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=d['ortho_scale'];s.render.filepath=str((out/(name+'.png')).resolve());bpy.ops.render.render(write_still=True)
for ob in objects:ob.location.z=0
d=views['beauty'];cam.location=d['location'];cam.rotation_euler=(Vector(d['target'])-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=d['ortho_scale'];s.render.filepath='//beauty.png';bpy.ops.wm.save_as_mainfile(filepath=str((out/'scene.blend').resolve()));info['elapsed_seconds']=round(time.time()-start,3);(out/'model-info.json').write_text(json.dumps(info,indent=2,ensure_ascii=False));print('SLOT COMPLETE')
