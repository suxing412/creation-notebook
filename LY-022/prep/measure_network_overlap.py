# LY-022 prep (read-only): does in-city network ground reach into the market rectangle? rays at 1 m grid.
# usage: blender -b --factory-startup --python-exit-code 1 -P measure_network_overlap.py -- <network-ground.glb> <out.json>
import bpy,sys,json,bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=a[0])
hits={};n=0;names=[];pts=[]
for o in bpy.data.objects:
    if o.type!='MESH': continue
    bm=bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world); t=BVHTree.FromBMesh(bm); bm.free(); names.append(o.name)
    for i in range(0,61):
        for j in range(0,45):
            X=184.286+i; Z=-1981.184+j
            h=t.ray_cast(Vector((X,-Z,5)),Vector((0,0,-1)),10)
            if h[0] is not None:
                k=o.name+'@'+str(round(h[0].z,3)); hits[k]=hits.get(k,0)+1; pts.append((X,Z))
json.dump({"points":pts,"objects":names,'grid':'1m over market rect 61x45','hits':hits},open(a[1],'w'),indent=1); print('OK',hits)
