"""ORISON / 回环. Blender 4.3.2 CPU studio, no external assets. Native and GLB are pure geometry."""
import bpy,sys,json,argparse,math,time,hashlib
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent));import recipe
p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True);p.add_argument('--geometry-only',action='store_true');p.add_argument('--views',default='beauty,front,side,top,rear,seam-detail');p.add_argument('--revision',type=int,default=1);p.add_argument('--samples',type=int,default=128);p.add_argument('--resolution',type=int,default=960);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);start=time.time();c=recipe.validate(json.loads(Path(a.config).read_text()),bpy.app.version,a.revision);out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for d in list(bpy.data.materials):bpy.data.materials.remove(d)
s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.scale_length=1

def mat(name,color,rough):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(*color,1);n.inputs['Metallic'].default_value=0;n.inputs['Roughness'].default_value=rough;return m
material=mat('ORISON | warm ivory unglazed ceramic',(.62,.56,.45),.36)
v,f,construction=recipe.geometry(c,a.revision);me=bpy.data.meshes.new('Periodic rounded rectangle sweep');me.from_pydata(v,[],f);me.update();ob=bpy.data.objects.new('ORISON | continuous closed sweep',me);bpy.context.collection.objects.link(ob);me.materials.append(material)
for face in me.polygons:face.use_smooth=True
ob['recipe_version']=recipe.VERSION;ob['construction']='Periodic analytic curve + analytic periodic frame; circular-corner section; no endpoint caps';ob['seed']=0
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='FILE_BROWSER' and area.spaces.active.params:area.spaces.active.params.directory=b''
s.render.filepath='//beauty.png';bpy.ops.wm.save_as_mainfile(filepath=str((out/'model.blend').resolve()));bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.export_scene.gltf(filepath=str((out/'model.glb').resolve()),export_format='GLB',use_selection=True,export_apply=True,export_extras=False)
bounds=[[min(q[k] for q in v),max(q[k] for q in v)] for k in range(3)]
views={'beauty':{'location':[.58,-.95,.50],'target':[0,0,.205],'ortho_scale':.53},'front':{'location':[0,-1,.205],'target':[0,0,.205],'ortho_scale':.50},'side':{'location':[1,0,.205],'target':[0,0,.205],'ortho_scale':.50},'top':{'location':[0,0,1],'target':[0,0,.205],'ortho_scale':.50},'rear':{'location':[-.58,.95,.50],'target':[0,0,.205],'ortho_scale':.53},'seam-detail':{'location':[.19,-.36,.14],'target':[0,0,.028],'ortho_scale':.145}}
info={'title':'ORISON / 回环','study':'007','variant':c['name'],'recipe_version':recipe.VERSION,'seed':0,'config':c,'blender_version':bpy.app.version_string,'units':'metres','mesh_objects':1,'vertices':len(v),'triangles':2*len(f),'dimensions_mm':{k:round((bounds[i][1]-bounds[i][0])*1000,3) for i,k in enumerate(['width','depth','height'])},'bounds_m':bounds,'construction':construction,'validation_status':'pending','realtime_verified':False,'physical_engineering_verified':False,'material':{'name':material.name,'base_color_linear':[.62,.56,.45],'metallic':0,'roughness':.36},'studio':{'renderer':'Cycles CPU','samples':a.samples,'samples_semantics':'maximum per-pixel samples; adaptive sampling disabled for before/after equivalence','adaptive_sampling':False,'denoiser':'none; installed Blender build does not provide one','view_transform':'AgX','exposure':0,'seed':0,'fixed_camera':True,'resolution':[a.resolution,a.resolution],'views':views,'background_linear':[.24,.255,.26],'world_color':[.22,.22,.22]},'phase':'first-version' if a.revision==0 else 'refined'}
(out/'model-info.json').write_text(json.dumps(info,indent=2,ensure_ascii=False));(out/'config.json').write_text(json.dumps(c,indent=2))
if a.geometry_only:print('ORISON geometry',c['name'],len(v),info['triangles']);sys.exit(0)
groundmat=mat('Studio | cool mineral grey',(.24,.255,.26),.84);bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.0002));ground=bpy.context.object;ground.name='Studio ground';ground.data.materials.append(groundmat)
def light(name,loc,energy,size,target=(0,0,.18)):
 bpy.ops.object.light_add(type='AREA',location=loc);q=bpy.context.object;q.name=name;q.data.energy=energy;q.data.shape='DISK';q.data.size=size;q.rotation_euler=(Vector(target)-q.location).to_track_quat('-Z','Y').to_euler()
light('Key | high left',(-.65,-.65,.95),55,.68);light('Fill | right',(.75,-.25,.55),16,.65);light('Edge | rear',(.15,.55,.78),38,.48)
s.world.color=(.22,.22,.22);bpy.ops.object.camera_add();cam=bpy.context.object;cam.name='Fixed orthographic study camera';cam.data.type='ORTHO';s.camera=cam;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.seed=0;s.cycles.use_animated_seed=False;s.cycles.use_denoising=False;s.cycles.use_adaptive_sampling=False;s.cycles.samples=a.samples;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX';s.view_settings.exposure=0;s.view_settings.gamma=1;s.display_settings.display_device='sRGB'
for name in a.views.split(','):
 d=views[name];cam.location=d['location'];cam.rotation_euler=(Vector(d['target'])-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=d['ortho_scale'];s.render.resolution_x=a.resolution;s.render.resolution_y=a.resolution;s.render.filepath=str((out/(name+'.png')).resolve());bpy.ops.render.render(write_still=True)
d=views['beauty'];cam.location=d['location'];cam.rotation_euler=(Vector(d['target'])-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=d['ortho_scale'];s.render.filepath='//beauty.png';bpy.ops.wm.save_as_mainfile(filepath=str((out/'scene.blend').resolve()));info['elapsed_seconds']=round(time.time()-start,3);(out/'model-info.json').write_text(json.dumps(info,indent=2,ensure_ascii=False));print('ORISON',c['name'],'complete',info['elapsed_seconds'])
