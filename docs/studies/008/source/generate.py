"""VEIL 008, Blender 4.3.2 CPU studio. Pure native mesh and actual GLB; no external assets."""
import bpy,sys,json,argparse,time,hashlib,math
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent));import recipe
p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True);p.add_argument('--geometry-only',action='store_true');p.add_argument('--views',default='beauty,front,side,top,rear,hole-detail');p.add_argument('--revision',type=int,default=1);p.add_argument('--samples',type=int,default=128);p.add_argument('--resolution',type=int,default=960);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);start=time.time();c=recipe.validate(json.loads(Path(a.config).read_text()),bpy.app.version,a.revision);out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for d in list(bpy.data.materials):bpy.data.materials.remove(d)
s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.scale_length=1

def mat(name,color,rough):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(*color,1);n.inputs['Metallic'].default_value=0;n.inputs['Roughness'].default_value=rough;return m
material=mat('VEIL | warm mineral ceramic',(.58,.49,.36),.38)
v,f,construction=recipe.geometry(c,a.revision);me=bpy.data.meshes.new('Shared-cell perforated cylindrical shell');me.from_pydata(v,[],f);me.update();ob=bpy.data.objects.new('VEIL | continuous perforated shell',me);bpy.context.collection.objects.link(ob);me.materials.append(material)
for face in me.polygons:face.use_smooth=True
# The revision-0 average-smooth shading is retained as the real before state.
# Revision 1 uses analytic corner normals on the actual curved/bore surfaces;
# the hole bevel remains real geometry, not a normal-map or bevel shader.
if a.revision:
 normal_by_vertex={}
 R=c['width']/math.radians(c['curve_angle_degrees'])
 for i,(u,z,t,role) in enumerate(construction['vertex_uvt']):
  normal_by_vertex[i]=Vector(recipe.normal(c,u))*(1 if t>0 else -1)
 for hole in construction['holes']:
  rx,ry=hole['radii_uv']
  for ri,ring in enumerate(hole['all_rings']):
   offset,t=hole['profile'][ri]
   if ri<=recipe.BEVEL_STEPS:
    psi=math.pi/2*ri/recipe.BEVEL_STEPS;do=-math.cos(psi);dt=-math.sin(psi)
   else:
    psi=math.pi/2*(2*recipe.BEVEL_STEPS+1-ri)/recipe.BEVEL_STEPS;do=math.cos(psi);dt=-math.sin(psi)
   for vid,(_,_,angle) in zip(ring,recipe.loop_angles()):
    u,z,_,_=construction['vertex_uvt'][vid];theta=u/R
    U=Vector((math.cos(theta),math.sin(theta),0))*((R+t)/R);N=Vector(recipe.normal(c,u));Z=Vector((0,0,1))
    tangent=U*(-(rx+offset)*math.sin(angle))+Z*((ry+offset)*math.cos(angle))
    profile_tangent=U*(do*math.cos(angle))+Z*(do*math.sin(angle))+N*dt
    normal_by_vertex[vid]=tangent.cross(profile_tangent).normalized()
 normals=[]
 outer_wall_count=len(construction['outer_front_edges'])
 for poly in me.polygons:
  is_outer_wall=poly.index>=len(me.polygons)-outer_wall_count
  for vid in poly.vertices:normals.append(tuple(poly.normal if is_outer_wall else normal_by_vertex[vid]))
 me.normals_split_custom_set(normals)
 me.update()

ob['recipe_version']=recipe.VERSION;ob['construction']=construction['construction_method'];ob['seed']=0
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='FILE_BROWSER' and area.spaces.active.params:area.spaces.active.params.directory=b''
s.render.filepath='//beauty.png';bpy.ops.wm.save_as_mainfile(filepath=str((out/'model.blend').resolve()));bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.export_scene.gltf(filepath=str((out/'model.glb').resolve()),export_format='GLB',use_selection=True,export_apply=True,export_extras=False)
bounds=[[min(q[k] for q in v),max(q[k] for q in v)] for k in range(3)]
views={'beauty':{'location':[.80,-1.25,.72],'target':[0,.03,.28],'ortho_scale':.76},'front':{'location':[0,-1.4,.28],'target':[0,.03,.28],'ortho_scale':.68},'side':{'location':[1.4,.03,.28],'target':[0,.03,.28],'ortho_scale':.68},'top':{'location':[0,.03,1.4],'target':[0,.03,.28],'ortho_scale':.68},'rear':{'location':[-.80,1.25,.72],'target':[0,.03,.28],'ortho_scale':.76},'hole-detail':{'location':[.20,-.34,.34],'target':[0,.008,.28],'ortho_scale':.155}}
info={'title':'VEIL / 透幕','study':'008','variant':c['name'],'recipe_version':recipe.VERSION,'seed':0,'config':c,'blender_version':bpy.app.version_string,'units':'metres','mesh_objects':1,'vertices':len(v),'triangles':2*len(f),'dimensions_mm':{k:round((bounds[i][1]-bounds[i][0])*1000,3) for i,k in enumerate(['width','depth','height'])},'bounds_m':bounds,'construction':construction,'validation_status':'external_report_required','realtime_verified':False,'physical_engineering_verified':False,'material':{'name':material.name,'base_color_linear':[.58,.49,.36],'metallic':0,'roughness':.38},'studio':{'renderer':'Cycles CPU','samples':a.samples,'adaptive_sampling':False,'denoiser':'none','view_transform':'AgX','exposure':0,'seed':0,'fixed_camera':True,'resolution':[a.resolution,a.resolution],'views':views,'background_linear':[.22,.24,.24],'world_color':[.22,.22,.22]},'phase':'first-version' if a.revision==0 else 'refined'}
(out/'model-info.json').write_text(json.dumps(info,ensure_ascii=False,separators=(',',':')));(out/'config.json').write_text(json.dumps(c,indent=2))
if a.geometry_only:print('VEIL geometry',c['name'],len(v),info['triangles']);sys.exit(0)
groundmat=mat('Studio | cool mineral grey',(.22,.24,.24),.84);bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.0002));ground=bpy.context.object;ground.name='Studio ground';ground.data.materials.append(groundmat)
def light(name,loc,energy,size,target=(0,0,.25)):
 bpy.ops.object.light_add(type='AREA',location=loc);q=bpy.context.object;q.name=name;q.data.energy=energy;q.data.shape='DISK';q.data.size=size;q.rotation_euler=(Vector(target)-q.location).to_track_quat('-Z','Y').to_euler()
light('Key | high left',(-.85,-.85,1.1),72,.75);light('Fill | right',(.85,-.25,.65),20,.68);light('Edge | rear',(.15,.65,.95),42,.55)
s.world.color=(.22,.22,.22);bpy.ops.object.camera_add();cam=bpy.context.object;cam.name='Fixed orthographic study camera';cam.data.type='ORTHO';s.camera=cam;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.seed=0;s.cycles.use_animated_seed=False;s.cycles.use_denoising=False;s.cycles.use_adaptive_sampling=False;s.cycles.samples=a.samples;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX';s.view_settings.exposure=0;s.view_settings.gamma=1;s.display_settings.display_device='sRGB'
for name in a.views.split(','):
 d=views[name];cam.location=d['location'];cam.rotation_euler=(Vector(d['target'])-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=d['ortho_scale'];s.render.resolution_x=a.resolution;s.render.resolution_y=a.resolution;s.render.filepath=str((out/(name+'.png')).resolve());bpy.ops.render.render(write_still=True)
d=views['beauty'];cam.location=d['location'];cam.rotation_euler=(Vector(d['target'])-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=d['ortho_scale'];s.render.filepath='//beauty.png';bpy.ops.wm.save_as_mainfile(filepath=str((out/'scene.blend').resolve()));info['elapsed_seconds']=round(time.time()-start,3);(out/'model-info.json').write_text(json.dumps(info,ensure_ascii=False,separators=(',',':')));print('VEIL',c['name'],'complete',info['elapsed_seconds'])
