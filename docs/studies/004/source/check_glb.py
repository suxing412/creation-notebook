"""Structural glTF validation (not a realtime rendering test)."""
import json,struct,pathlib
p=pathlib.Path(__file__).resolve().parents[1]/'dist/assets/limen.glb'
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
print(json.dumps({'glbBytes':size,'triangles':tri,'exportVertices':vertices,'meshes':len(g['meshes']),'primitives':sum(len(m['primitives']) for m in g['meshes']),'materials':len(g['materials']),'externalFiles':False},indent=2))
