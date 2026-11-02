"""Sample exposed stair/arrival front faces, separate from horizontal walking surfaces."""
import bpy,sys,json
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.open_mainfile(filepath=args[0]);dg=bpy.context.evaluated_depsgraph_get();fail=[];groups=[]
faces=[('arrival',-5.11,-.10,.27,'Access / lower arrival threshold')]+[(f'riser{i+1}',-4.71+i*.25,.27+i*.18,.27+(i+1)*.18,'Access / twelve continuous stone steps') for i in range(12)]
for label,y,z0,z1,expected in faces:
 wrong=[]
 for i in range(81):
  x=-1.34+1.34*i/80
  for j in range(31):
   z=z0+.018+(z1-z0-.036)*j/30
   origin=Vector((x,y-.10,z));direction=Vector((0,1,0));hits=[]
   for ob in [bpy.data.objects[expected],bpy.data.objects['Rock / single faceted outcrop']]:
    inv=ob.matrix_world.inverted();h,loc,n,index=ob.ray_cast(inv@origin,inv.to_3x3()@direction,distance=.20)
    if h:
     world=ob.matrix_world@loc;hits.append(((world-origin).length,world,ob))
   hit=bool(hits);p=Vector((0,0,0));o=None
   if hits:distance,p,o=min(hits,key=lambda h:h[0])
   if not hit or o.name!=expected or abs(p.y-y)>.001:
    wrong.append({'x':x,'z':z,'object':o.name if o else None,'point':list(p)})
 groups.append({'face':label,'samples':81*31,'unexpectedHits':len(wrong)});fail += [{'face':label,**w} for w in wrong]
r={'method':'Horizontal rays from0.10 in front of each vertical face, distance0.20;81x31 samples per face excluding18mm top/bottom bevel and20mm side edges. Compares rock and tested stone object only; guardrail occlusion is excluded. Checks exposed faces, not all volume containment.','groups':groups,'totalSamples':len(faces)*81*31,'unexpectedHits':len(fail),'failures':fail};json.dump(r,open(args[1],'w'),indent=2);print('RISERS',r['totalSamples'],r['unexpectedHits']);assert not fail
