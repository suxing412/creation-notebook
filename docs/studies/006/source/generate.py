"""FOLIO / 折页. Blender 4.3.2 CPU product-study exporter; no external assets."""
import bpy,bmesh,sys,json,argparse,math,time
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent));import recipe
p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True);p.add_argument('--geometry-only',action='store_true');p.add_argument('--views',default='beauty,front,side,top,rear,bend-detail,contact-detail');p.add_argument('--revision',type=int,default=1);p.add_argument('--samples',type=int,default=256);p.add_argument('--resolution',type=int,default=960);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);start=time.time();c=recipe.validate(json.loads(Path(a.config).read_text()),bpy.app.version);out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for d in list(bpy.data.materials):bpy.data.materials.remove(d)
s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.scale_length=1

def mat(name,color,metal,rough):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(*color,1);n.inputs['Metallic'].default_value=metal;n.inputs['Roughness'].default_value=rough;return m
material=mat('FOLIO | satin mineral aluminium',(.43,.49,.50),.82,.285)
v,f,construction=recipe.geometry(c,a.revision);me=bpy.data.meshes.new('Continuous sheet • exact normal thickness');me.from_pydata(v,[],f);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free();ob=bpy.data.objects.new('FOLIO | single continuous folded shell',me);bpy.context.collection.objects.link(ob);me.materials.append(material)
for face in me.polygons:face.use_smooth=len(face.vertices)==4
ob['recipe_version']=recipe.VERSION;ob['construction']='One connected closed thick shell with circular centerline bends';ob['normal_thickness_mm']=c['thickness']*1000
# Only original model in native/GLB: no floor, no study camera, no renderer lights.
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='FILE_BROWSER' and area.spaces.active.params:area.spaces.active.params.directory=b''
s.render.filepath='//beauty.png';bpy.ops.wm.save_as_mainfile(filepath=str((out/'model.blend').resolve()));bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.export_scene.gltf(filepath=str((out/'model.glb').resolve()),export_format='GLB',use_selection=True,export_apply=True,export_extras=False)
bounds=[[min(q[k] for q in v),max(q[k] for q in v)] for k in range(3)];info={'title':'FOLIO / 折页','study':'006','variant':c['name'],'recipe_version':recipe.VERSION,'seed':0,'config':c,'blender_version':bpy.app.version_string,'units':'metres','mesh_objects':1,'triangles':sum(len(face)-2 for face in f),'dimensions_mm':{k:round((bounds[i][1]-bounds[i][0])*1000,3) for i,k in enumerate(['width','depth','height'])},'bounds_m':bounds,'construction':construction,'validation_status':'pending','realtime_verified':False,'physical_engineering_verified':False,'material':{'name':material.name,'base_color_linear':[.43,.49,.50],'metallic':.82,'roughness':.285},'studio':{'renderer':'Cycles CPU','samples':a.samples,'samples_semantics':'maximum per-pixel samples; adaptive sampling enabled at threshold 0.01','adaptive_sampling':True,'adaptive_threshold':.01,'denoiser':'none; unavailable in installed Blender build','view_transform':'AgX','exposure':0,'seed':0,'fixed_camera':True,'resolution':[a.resolution,a.resolution]},'phase':'first-version' if a.revision==0 else 'refined'}
(out/'model-info.json').write_text(json.dumps(info,indent=2,ensure_ascii=False));(out/'config.json').write_text(json.dumps(c,indent=2))
if a.geometry_only:print('FOLIO geometry',c['name'],len(v),info['triangles']);sys.exit(0)
groundmat=mat('Studio | chalk',(.37,.39,.39),0,.8);bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.0006));ground=bpy.context.object;ground.name='Studio ground';ground.data.materials.append(groundmat)
def light(name,loc,energy,size,target=(0,0,.10)):
 bpy.ops.object.light_add(type='AREA',location=loc);q=bpy.context.object;q.name=name;q.data.energy=energy;q.data.shape='RECTANGLE';q.data.size=size;q.data.size_y=size*.6;q.rotation_euler=(Vector(target)-q.location).to_track_quat('-Z','Y').to_euler()
light('Softbox left',(-.60,-.50,.85),45,.75);light('Softbox rear',(.28,.52,.68),55,.60);light('Long edge',(.60,-.15,.42),23,.40)
s.world.color=(.30,.30,.30);bpy.ops.object.camera_add();cam=bpy.context.object;cam.name='Fixed study camera';cam.data.type='ORTHO';s.camera=cam;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.seed=0;s.cycles.use_animated_seed=False;s.cycles.use_denoising=False;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX';s.view_settings.exposure=0;s.view_settings.gamma=1;s.display_settings.display_device='sRGB';s.cycles.samples=a.samples;s.cycles.use_adaptive_sampling=True;s.cycles.adaptive_threshold=.01;s.cycles.adaptive_min_samples=0
bend=construction['bends'][2]['center_yz_m'];front=construction['bends'][1]['center_yz_m']
views={'beauty':((.52,-.72,.39),(0,0,.102),.43),'front':((0,-1,.12),(0,0,.12),.39),'side':((1,0,.12),(0,0,.12),.39),'rear':((.48,.68,.35),(0,0,.10),.43),'top':((0,0,1),(0,0,0),.39),'bend-detail':((.34,bend[0]-.25,bend[1]+.1),(.08,bend[0],bend[1]),.14),'contact-detail':((.36,front[0]-.32,.15),(.06,front[0],.024),.17)}
for name in a.views.split(','):
 loc,target,scale=views[name];cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;s.render.resolution_x=a.resolution;s.render.resolution_y=a.resolution;s.render.filepath=str((out/(name+'.png')).resolve());bpy.ops.render.render(write_still=True)
loc,target,scale=views['beauty'];cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;s.render.filepath='//beauty.png';bpy.ops.wm.save_as_mainfile(filepath=str((out/'scene.blend').resolve()));info['elapsed_seconds']=round(time.time()-start,3);(out/'model-info.json').write_text(json.dumps(info,indent=2,ensure_ascii=False));print('FOLIO',c['name'],'complete',info['elapsed_seconds'])
