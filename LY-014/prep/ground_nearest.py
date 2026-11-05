# LY-014 prep: nearest city stitched-ground surface to the Kaiyang engineering origin (read-only)
import bpy,sys,json,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a=sys.argv[sys.argv.index('--')+1:]; gp=a[0]; org=Vector((2010.3973388671875,-21.3011474609375,0.17))
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=gp)
V=[];F=[];off=0
for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  me=o.data; me.calc_loop_triangles(); mw=o.matrix_world
  V+= [tuple(mw@v.co) for v in me.vertices]; F+=[tuple(i+off for i in t.vertices) for t in me.loop_triangles]; off=len(V)
bv=BVHTree.FromPolygons(V,F); Va=np.array(V)
res={'triangles':len(F),'bbox_lo':Va.min(0).round(3).tolist(),'bbox_hi':Va.max(0).round(3).tolist()}
for name,p in [('origin',org),('north10',org+Vector((0,10,0))),('north30',org+Vector((0,30,0))),('south10',org+Vector((0,-10,0)))]:
  loc,n,i,d=bv.find_nearest(Vector((p.x,p.y,0.2)))
  res[name]={'nearest':[round(c,3) for c in loc],'dist_xy':round(((loc.x-p.x)**2+(loc.y-p.y)**2)**.5,3),'z':round(loc.z,4)}
print('NEAREST',json.dumps(res))
