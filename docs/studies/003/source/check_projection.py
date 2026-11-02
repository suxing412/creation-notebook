"""Run in Blender: exports triangle projections; Python script rasterizes outside Blender."""
import bpy,os,json,math
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));bpy.ops.wm.open_mainfile(filepath=R+'/dist/assets/iris.blend')
frames=[]
for step in sorted([float(i) for i in range(56)]+[27.5]):
 for i in range(8):bpy.data.objects['Pivot_%02d'%i].rotation_euler.z=i*math.pi/4+math.radians(55-step)
 bpy.context.view_layer.update();polys=[]
 for o in bpy.data.objects:
  if o.name.startswith('Blade_'):
   me=o.data;me.calc_loop_triangles();v=[o.matrix_world@p.co for p in me.vertices]
   polys += [[[v[i].x,v[i].y] for i in t.vertices] for t in me.loop_triangles]
 frames.append({'degrees':step,'triangles':polys})
json.dump(frames,open(R+'/evidence/projected-triangles.json','w'))
