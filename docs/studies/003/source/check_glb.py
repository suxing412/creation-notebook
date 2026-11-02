"""Structural glTF validation (not a realtime rendering test)."""
import json,struct,pathlib
p=pathlib.Path(__file__).resolve().parents[1]/'dist/assets/iris.glb'
b=p.read_bytes();magic,version,size=struct.unpack_from('<4sII',b)
assert magic==b'glTF' and version==2 and size==len(b)
n,kind=struct.unpack_from('<II',b,12);assert kind==0x4E4F534A
g=json.loads(b[20:20+n]);tri=0;vertices=0
for m in g['meshes']:
 for prim in m['primitives']:
  assert prim.get('mode',4)==4
  a=g['accessors'][prim['indices']];assert a['count']%3==0;tri+=a['count']//3
  vertices+=g['accessors'][prim['attributes']['POSITION']]['count']
assert not g.get('images') and not g.get('animations')
info=json.loads((p.parent/'model-info.json').read_text());assert tri==info['triangles']
pivots={x['name']:x for x in g['nodes'] if x.get('name','').startswith('Pivot_')}
assert set(pivots)==set(info['motion']['pivotNames'])
import math
for i in range(8):
 node=pivots['Pivot_%02d'%i]
 assert len(node['children'])==1
 assert g['nodes'][node['children'][0]]['name']=='Blade_%02d'%i
 q=node['rotation'];expected=math.radians(i*45+27.5)/2
 assert abs(abs(q[1]*math.sin(expected)+q[3]*math.cos(expected))-1)<1e-6
 assert abs(q[0])+abs(q[2])<1e-6
assert info['motion']['axis']==[0,-1,0]
report={'glbBytes':size,'triangles':tri,'exportVertices':vertices,'meshes':len(g['meshes']),'primitives':sum(len(m['primitives']) for m in g['meshes']),'materials':len(g['materials']),'externalFiles':False,'namedPivots':8,'pivotLocalAxis':[0,-1,0],'referenceDegrees':27.5,'motionQuaternionChecked':True,'runtimeRenderingVerified':False}
(p.parent.parent.parent/'evidence/glb-check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
