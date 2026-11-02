"""009 strict embedded GLB reader; decoded geometric validation, not runtime rendering."""
import json,struct,math,hashlib
from pathlib import Path
VERSION='009-payload-1.0'
class Reject(ValueError):
 def __init__(self,code,message): self.code=code;super().__init__(message)
def require(ok,code,message):
 if not ok:raise Reject(code,message)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def decode(path):
 b=Path(path).read_bytes(); require(len(b)>=28,'header','Truncated GLB')
 magic,version,length=struct.unpack_from('<III',b);require(magic==0x46546c67 and version==2 and length==len(b),'header','Wrong GLB header')
 chunks=[];off=12
 while off<len(b):
  require(off+8<=len(b),'chunk','Truncated chunk header');n,t=struct.unpack_from('<II',b,off);off+=8
  require(n%4==0 and off+n<=len(b),'chunk','Unaligned or overrun chunk');chunks.append((t,b[off:off+n]));off+=n
 require(len(chunks)==2 and [c[0] for c in chunks]==[0x4e4f534a,0x004e4942],'chunks','Requires JSON/BIN only')
 j=json.loads(chunks[0][1]);data=chunks[1][1];require(j.get('asset',{}).get('version')=='2.0','version','glTF2 required')
 require(len(j.get('buffers',[]))==1 and not j['buffers'][0].get('uri'),'buffer','Single embedded buffer required')
 bl=j['buffers'][0]['byteLength'];require(type(bl)is int and 0<bl<=len(data) and len(data)-bl<4,'buffer','Invalid byteLength')
 require(not j.get('images') and not j.get('textures') and not j.get('skins') and not j.get('animations') and not j.get('extensionsRequired'),'unsupported','Only static untextured geometry supported')
 views=j.get('bufferViews',[]);acs=j.get('accessors',[]);decoded=[]
 sizes={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4};formats={5120:'b',5121:'B',5122:'h',5123:'H',5125:'I',5126:'f'};widths={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}
 for vi,v in enumerate(views):
  vo=v.get('byteOffset',0);vl=v.get('byteLength');require(v.get('buffer',0)==0 and type(vo)is int and type(vl)is int and vo>=0 and vl>0 and vo+vl<=bl,'view_bounds',str(vi))
  if 'byteStride'in v:require(type(v['byteStride'])is int and 4<=v['byteStride']<=252 and v['byteStride']%4==0,'stride',str(vi))
 for ai,a in enumerate(acs):
  require(not a.get('sparse') and a.get('componentType')in sizes and a.get('type')in widths,'accessor_schema',str(ai));vi=a.get('bufferView');n=a.get('count');o=a.get('byteOffset',0)
  require(type(vi)is int and 0<=vi<len(views) and type(n)is int and n>0 and type(o)is int and o>=0,'accessor_schema',str(ai));v=views[vi];cs=sizes[a['componentType']];w=widths[a['type']];stride=v.get('byteStride',cs*w);start=v.get('byteOffset',0)+o
  require(stride>=cs*w and stride%cs==0 and start%cs==0 and o+(n-1)*stride+cs*w<=v['byteLength'],'accessor_bounds',str(ai));fmt='<'+formats[a['componentType']]*w;values=[struct.unpack_from(fmt,data,start+i*stride)for i in range(n)]
  require(all(math.isfinite(x)for row in values for x in row),'nonfinite',str(ai))
  for key,fun in [('min',min),('max',max)]:
   if key in a:
    bound=a[key];require(isinstance(bound,list)and len(bound)==w and all(type(x)in(int,float)and math.isfinite(x)for x in bound),'bounds',str(ai))
    require(all(abs(fun(row[k]for row in values)-bound[k])<=max(1e-7,abs(bound[k])*2e-7)for k in range(w)),'bounds',str(ai))
  decoded.append(values)
 def acc(i):require(type(i)is int and 0<=i<len(acs),'reference','Accessor');return acs[i],decoded[i]
 meshes=[]
 for mi,m in enumerate(j.get('meshes',[])):
  prims=[]
  for p in m.get('primitives',[]):
   require(p.get('mode',4)==4 and not p.get('targets')and not p.get('extensions'),'primitive','Plain triangles only');attrs=p.get('attributes',{});require('POSITION'in attrs and 'NORMAL'in attrs,'attributes','Position and normal required')
   pa,pos=acc(attrs['POSITION']);na,norm=acc(attrs['NORMAL']);ia,idx=acc(p.get('indices'))
   require(pa['componentType']==5126 and pa['type']=='VEC3'and not pa.get('normalized')and 'min'in pa and 'max'in pa,'position','float32VEC3 bounds required')
   require(na['componentType']==5126 and na['type']=='VEC3'and not na.get('normalized'),'normal','float32VEC3 required')
   require(ia['type']=='SCALAR'and ia['componentType']in(5121,5123,5125)and len(idx)%3==0 and not ia.get('normalized'),'indices','Unsigned triangle indices required');indices=[q[0]for q in idx]
   require(all(0<=q<len(pos)for q in indices),'index_range','Index out of bounds');require(len(pos)==len(norm)and all(len(acc(i)[1])==len(pos)for i in attrs.values()),'attribute_count','Mismatched attributes')
   require(all(.98<=sum(x*x for x in q)<=1.02 for q in norm),'normals','Nonunit normals')
   mat=p.get('material');require(type(mat)is int and 0<=mat<len(j.get('materials',[])),'material','Invalid material')
   triangles=[tuple(indices[i:i+3])for i in range(0,len(indices),3)];prims.append({'positions':pos,'normals':norm,'triangles':triangles,'material':mat})
  require(prims,'mesh','Empty mesh');meshes.append(prims)
 require(meshes,'mesh','No meshes');nodes=j.get('nodes',[]);require(len(j.get('scenes',[]))==1 and j.get('scene',0)==0,'scene','Single scene required')
 return j,meshes,{'sha256':sha(path),'bytes':len(b),'mesh_count':len(meshes),'node_count':len(nodes),'accessors_checked':len(acs),'triangles':sum(len(p['triangles'])for m in meshes for p in m),'runtime_render_verified':False}
