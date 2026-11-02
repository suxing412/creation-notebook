"""Decoded GLB geometry/structure gate, not a GPU render validator.
This recipe exports ordinary non-sparse uncompressed VEC/SCALAR mesh accessors.
"""
import struct,json,sys,math
from pathlib import Path
p=Path(sys.argv[1]);data=p.read_bytes();magic,version,length=struct.unpack_from('<III',data);assert magic==0x46546C67 and version==2 and length==len(data)
n,typ=struct.unpack_from('<II',data,12);assert typ==0x4E4F534A;j=json.loads(data[20:20+n]);nb,tb=struct.unpack_from('<II',data,20+n);assert tb==0x004E4942;binary=data[28+n:28+n+nb]
assert not j.get('images') and not j.get('textures');assert len(j['meshes'])==8;assert len(j['materials'])==3;assert all('uri' not in b for b in j['buffers']);assert len(j['buffers'])==1 and j['buffers'][0]['byteLength']<=len(binary)
sizes={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4};formats={5120:'b',5121:'B',5122:'h',5123:'H',5125:'I',5126:'f'};widths={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4};decoded={}
for i,a in enumerate(j['accessors']):
 assert 'sparse' not in a and a['type'] in widths and a['count']>0
 v=j['bufferViews'][a['bufferView']];assert v.get('buffer',0)==0;size=sizes[a['componentType']]*widths[a['type']];stride=v.get('byteStride',size);assert stride>=size and stride%sizes[a['componentType']]==0
 offset=a.get('byteOffset',0);end=offset+(a['count']-1)*stride+size;assert end<=v['byteLength'];assert v.get('byteOffset',0)+v['byteLength']<=len(binary)
 start=v.get('byteOffset',0)+offset;fmt='<'+formats[a['componentType']]*widths[a['type']];values=[struct.unpack_from(fmt,binary,start+k*stride) for k in range(a['count'])];assert all(math.isfinite(x) for row in values for x in row),'Nonfinite accessor bytes'
 if 'min' in a:
  assert len(a['min'])==widths[a['type']] and all(abs(min(row[k] for row in values)-a['min'][k])<=1e-5 for k in range(widths[a['type']])), 'Declared accessor min does not match bytes'
 if 'max' in a:
  assert len(a['max'])==widths[a['type']] and all(abs(max(row[k] for row in values)-a['max'][k])<=1e-5 for k in range(widths[a['type']])), 'Declared accessor max does not match bytes'
 decoded[i]=values
tris=0;vertices=0
for m in j['meshes']:
 for prim in m['primitives']:
  assert prim.get('mode',4)==4;assert not prim.get('extensions');ac=j['accessors'][prim['indices']];assert ac['type']=='SCALAR' and ac['componentType'] in [5121,5123,5125] and ac['count']%3==0
  posid=prim['attributes']['POSITION'];pos=decoded[posid];assert j['accessors'][posid]['componentType']==5126 and j['accessors'][posid]['type']=='VEC3'
  idx=[q[0] for q in decoded[prim['indices']]];assert all(0<=i<len(pos) for i in idx),'Index exceeds POSITION count';vertices+=len(pos);tris+=len(idx)//3
  for semantic,acc in prim['attributes'].items():assert len(decoded[acc])==len(pos)
  for q in decoded[prim['attributes']['NORMAL']]:assert .98<=sum(x*x for x in q)<=1.02,'Invalid normal length'
  for k in range(0,len(idx),3):
   a,b,c=[pos[ii] for ii in idx[k:k+3]];u=[b[d]-a[d] for d in range(3)];v=[c[d]-a[d] for d in range(3)];cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];assert sum(x*x for x in cross)>4e-24,'Degenerate exported triangle'
for node in j['nodes']:
 for key in ['translation','rotation','scale','matrix']:assert all(math.isfinite(v) for v in node.get(key,[]))
r={'file':p.name,'passed':True,'format':'glTF 2.0 binary','bytes':len(data),'mesh_count':len(j['meshes']),'material_count':len(j['materials']),'triangles':tris,'decoded_export_vertices':vertices,'decoded_all_accessors_finite':True,'decoded_indices_in_range':True,'decoded_normals_unit_length':True,'external_resources':0,'runtime_render_verified':False};Path(sys.argv[2]).write_text(json.dumps(r,indent=2));print('GLB',tris)
