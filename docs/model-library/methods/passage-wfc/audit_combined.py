import bpy,bmesh,pathlib,json,hashlib,itertools
from mathutils import Vector
P=pathlib.Path(__file__).resolve().parent;reports=[]
for path in sorted((P/'assets').glob('*.glb')):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(path))
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];stats=[];bounds={}
 for o in meshes:
  bm=bmesh.new();bm.from_mesh(o.data);bm.transform(o.matrix_world);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table();vs=[v.co for v in bm.verts]
  lo=[min(v[k] for v in vs) for k in range(3)];hi=[max(v[k] for v in vs) for k in range(3)];bounds[o.name]=(lo,hi)
  stats.append({'mesh':o.name,'triangles':len(bm.faces),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'degenerate':sum(f.calc_area()<1e-10 for f in bm.faces),'signed_volume':bm.calc_volume(signed=True),'bounds':[lo,hi]});bm.free()
 overlaps=[];touches=[]
 for a,b in itertools.combinations(bounds,2):
  la,ha=bounds[a];lb,hb=bounds[b];depth=[min(ha[i],hb[i])-max(la[i],lb[i]) for i in range(3)]
  if min(depth)>1e-6: overlaps.append({'pair':[a,b],'depth':depth})
  elif min(depth)>=-1e-6:touches.append({'pair':[a,b],'kind':'boundary_contact','depth':depth})
 print(path.name,overlaps,stats); assert not overlaps and all(s['nonmanifold_edges']==0 and s['degenerate']==0 and s['signed_volume']>0 for s in stats)
 reports.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'meshes':stats,'positive_aabb_overlaps':overlaps,'boundary_contacts':touches,'method':'AABB is exact for these axis-aligned solid box primitives; not a general mesh collision certificate'})
(P/'combined-export-checks.json').write_text(json.dumps({'checker_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'blender_version':bpy.app.version_string,'assets':reports},indent=2))
