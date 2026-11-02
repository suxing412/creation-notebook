"""Actual Blender world-space reference for renderer-free JS transform parity."""
import bpy, pathlib, json, math, array
R=pathlib.Path(__file__).resolve().parents[1];E=R/'evidence';E.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'dist/assets/iris.blend'))
blades=[bpy.data.objects['Blade_%02d'%i] for i in range(8)]
angles=sorted([float(i) for i in range(56)]+[27.5]);meta={'angles':angles,'coordinateConversion':'Blender(x,y,z) -> glTF(x,z,-y)','blades':[]};offset=0
for o in blades:
 local=[[v.co.x,v.co.z,-v.co.y] for v in o.data.vertices];meta['blades'].append({'name':o.name,'offsetVertices':offset,'localVertices':local});offset+=len(local)
meta['verticesPerState']=offset
with open(E/'transform-reference.bin','wb') as f:
 for angle in angles:
  for i in range(8):bpy.data.objects['Pivot_%02d'%i].rotation_euler.z=math.radians(i*45+55-angle)
  bpy.context.view_layer.update();values=array.array('f')
  for o in blades:
   for v in o.data.vertices:
    p=o.matrix_world@v.co;values.extend([p.x,p.z,-p.y])
  values.tofile(f)
(E/'transform-reference.json').write_text(json.dumps(meta))
print('REFERENCE',len(angles),'states',offset,'source vertices per state')
