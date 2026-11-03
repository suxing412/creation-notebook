import bpy,pathlib,json,math,hashlib,bmesh,itertools
from mathutils import Vector
P=pathlib.Path(__file__).parent;A=P.parent/'luoyang-passage-interface-modules';R=json.loads((P/'results.json').read_text());T=json.loads((P/'states.json').read_text());seeds=json.loads((P/'summary.json').read_text())['selected_topology_seeds'];C=json.loads((A/'contract.json').read_text());reports=[]
(P/'previews').mkdir(exist_ok=True);(P/'assets').mkdir(exist_ok=True)
for seed in seeds:
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);r=R[seed];poses=[]
 for i,state in enumerate(r['layout']):
  k=T[state]['kind'];a=next(a for a in C['assets'] if a['id']==k);path=A/a['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==a['sha256']
  before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(path));obs=set(bpy.data.objects)-before
  bpy.ops.object.empty_add(type='PLAIN_AXES',location=(i%3*4,i//3*4,0));root=bpy.context.object;root.name=f'tile_{i}_{state}';root.rotation_euler.z=math.radians(-T[state]['rotationCW'])
  for o in obs:o.parent=root
  poses.append({'tile':i,'asset_id':k,'asset_sha256':a['sha256'],'positionBlender':[i%3*4,i//3*4,0],'rotationZDegrees':-T[state]['rotationCW']})
 bpy.context.view_layer.update();bounds={};meshstats=[]
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data);bm.transform(o.matrix_world);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);v=[v.co for v in bm.verts];bounds[o.name]=([min(q[d] for q in v) for d in range(3)],[max(q[d] for q in v) for d in range(3)]);meshstats.append({'name':o.name,'volume':bm.calc_volume(signed=True),'nonmanifold':sum(not e.is_manifold for e in bm.edges)});bm.free()
 overlaps=[];contacts=0
 for a,b in itertools.combinations(bounds,2):
  la,ha=bounds[a];lb,hb=bounds[b];dep=[min(ha[d],hb[d])-max(la[d],lb[d]) for d in range(3)]
  if min(dep)>1e-5:overlaps.append([a,b,dep])
  elif min(dep)>=-1e-5:contacts+=1
 assert not overlaps
 bpy.ops.object.select_all(action='SELECT');f=P/'assets'/f'seed-{seed}.glb';bpy.ops.export_scene.gltf(filepath=str(f),export_format='GLB',use_selection=True)
 world=bpy.context.scene.world or bpy.data.worlds.new('World');bpy.context.scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.58,.6,1);world.node_tree.nodes['Background'].inputs[1].default_value=.6
 bpy.ops.object.light_add(type='AREA',location=(2,-4,15));bpy.context.object.data.energy=1800;bpy.context.object.data.size=10
 bpy.ops.object.camera_add(location=(17,-19,24));cam=bpy.context.object;cam.rotation_euler=(Vector((4,4,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=20;bpy.context.scene.camera=cam
 s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=24;s.cycles.use_denoising=False;s.render.resolution_x=900;s.render.resolution_y=850;s.render.resolution_percentage=100;s.render.filepath=str(P/'previews'/f'seed-{seed}-cpu.png');bpy.ops.render.render(write_still=True)
 reports.append({'seed':seed,'poses':poses,'positive_overlap_pairs':overlaps,'boundary_contact_pairs':contacts,'module_geometry_meshes':meshstats,'glb_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'scope':'actual imported prototype geometry under placement; axis-aligned AABB after orthogonal rotations; final combined export not independently reimported'})
(P/'geometry-checks.json').write_text(json.dumps({'checker_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'source_registry':'independent candidate group sixth; not public or city','reports':reports},indent=2))
