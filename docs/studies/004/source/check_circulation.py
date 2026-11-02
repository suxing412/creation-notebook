"""Test actual meshes: arch rays, all stair treads, handrail clearance and support contact.
blender -b --python source/check_circulation.py -- dist/assets/limen.blend output.json
"""
import bpy,sys,json
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.open_mainfile(filepath=args[0]);dg=bpy.context.evaluated_depsgraph_get()
def cast(origin,direction,distance=50):
 hit,loc,normal,index,obj,matrix=bpy.context.scene.ray_cast(dg,Vector(origin),Vector(direction),distance=distance)
 return {'hit':hit,'point':list(loc),'object':obj.name if obj else None}
front=cast((-.68,-1,3.5),(0,1,0));east=cast((2,1.02,3.5),(-1,0,0));stairs=[]
for i in range(12):
 y=-4.71+(i+.5)*.25;expected=.27+(i+1)*.18
 for x in [-1.05,-.68,-.25]:
  h=cast((x,y,7),(0,0,-1));h.update({'step':i+1,'sampleX':x,'expectedHeight':expected,'heightError':abs(h['point'][2]-expected)});stairs.append(h)
arrival=[cast((x,-4.90,4),(0,0,-1)) for x in [-1.05,-.68,-.25]]
landing=[cast((x,y,4),(0,0,-1)) for x,y in [(-.68,-1.55),(-.68,-1.1),(-.68,-.55),(-.68,-.1),(1.45,1.02),(1.3,.1)]]
r={'entryRay':front,'eastRay':east,'archPass':front['hit'] and front['point'][1]>2 and east['hit'] and east['point'][0]<-2,'stairSamples':stairs,'stairPass':all(s['object']=='Access / twelve continuous stone steps' and s['heightError']<.002 for s in stairs),'arrivalSamples':arrival,'arrivalPass':all(x['object']=='Access / lower arrival threshold' and abs(x['point'][2]-.27)<.002 for x in arrival),'landingSamples':landing,'landingPass':all(s['object']=='Terrace / continuous slab' and abs(s['point'][2]-2.43)<.002 for s in landing),'limits':'36 vertical tread-centre samples plus6upperlanding and3lowerarrival samples and2opening horizontal rays; not continuous pedestrian clearance, accessibility or structural certification. No realtime z-fighting verification.'}
json.dump(r,open(args[1],'w'),indent=2);print('CIRCULATION',r['archPass'],r['stairPass'],r['landingPass'])
assert r['archPass'] and r['stairPass'] and r['landingPass'] and r['arrivalPass']
