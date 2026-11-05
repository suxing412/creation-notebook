"""LY-024 prep: host-only see-through probe of the S84 front facade (where can a ray from the street reach the interior?).
Ray from z=+1.0 toward -z; 'leak' = ray reaches z<-1.5 (past counter zone) without hitting host. Grid 0.01 m in x, 0.05 m in y.
blender -b --factory-startup --python-exit-code 1 -P probe_facade_leaks.py -- host.glb out.json"""
import bpy, bmesh, sys, json, hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a=sys.argv[sys.argv.index('--')+1:]; host,out=a[0],a[1]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=host)
bm=bmesh.new()
for o in [o for o in bpy.data.objects if o.type=='MESH']:
    t=bmesh.new(); t.from_mesh(o.data); t.transform(o.matrix_world); me=bpy.data.meshes.new('t'); t.to_mesh(me); bm.from_mesh(me); t.free()
H=BVHTree.FromBMesh(bm); G=lambda x,y,z: Vector((x,-z,y)); d=G(0,0,-1)-G(0,0,0)
bands={}
def leak(x,y):
    r=H.ray_cast(G(x,y,1.0),d,2.5); return r[0] is None
res={'host':host,'sha256':hashlib.sha256(open(host,'rb').read()).hexdigest(),'rows':{}}
for yi in range(0,82):
    y=0.25+yi*0.05
    xs=[round(-3.95+0.01*i,3) for i in range(791)]
    L=[x for x in xs if leak(x,y)]
    # compress to intervals
    iv=[]; 
    for x in L:
        if iv and abs(x-iv[-1][1]-0.01)<1e-6: iv[-1][1]=x
        else: iv.append([x,x])
    res['rows'][round(y,3)]=iv
json.dump(res,open(out,'w'),indent=0); print('OK')
