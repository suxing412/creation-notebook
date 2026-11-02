"""007 decoded GLB payload gate, not a GPU or full native/GLB isomorphism verifier.
General accessor decoding/triangle checks adapted from study-006/source/check_glb.py.
007 adds stable failure codes, failure reports, complete input/checker identities and fresh-run ID.
"""
import struct,json,sys,math,hashlib,uuid,datetime
from pathlib import Path
VERSION='007-glb-1.0'
class Rejected(Exception):
 def __init__(self,code,detail): self.code=code;self.detail=detail;super().__init__(code+': '+detail)
def need(ok,code,detail):
 if not ok:raise Rejected(code,detail)
def integer(x):return type(x) is int

def validate(path):
 data=Path(path).read_bytes();need(len(data)>=28,'glb_header','Truncated GLB');magic,version,length=struct.unpack_from('<III',data);need(magic==0x46546C67 and version==2 and length==len(data),'glb_header','Invalid magic/version/declared length')
 chunks=[];offset=12
 while offset<len(data):
  need(offset+8<=len(data),'chunk_bounds','Incomplete chunk header');n,typ=struct.unpack_from('<II',data,offset);need(n%4==0 and offset+8+n<=len(data),'chunk_bounds','Chunk outside file or not aligned');chunks.append((typ,data[offset+8:offset+8+n]));offset+=8+n
 need(len(chunks)==2 and chunks[0][0]==0x4E4F534A and chunks[1][0]==0x004E4942,'chunk_layout','Expected JSON then BIN only');j=json.loads(chunks[0][1]);binary=chunks[1][1]
 need(j.get('asset',{}).get('version')=='2.0','asset_version','Only glTF 2.0 supported');need(not j.get('images') and not j.get('textures'),'external_resources','Images/textures outside contract');need(len(j.get('meshes',[]))==1 and len(j.get('materials',[]))==1,'object_contract','Expected one mesh and material');need(len(j.get('buffers',[]))==1 and not any('uri' in b for b in j['buffers']),'external_resources','Expected one embedded buffer');bl=j['buffers'][0]['byteLength'];need(integer(bl) and 0<bl<=len(binary) and len(binary)-bl<=3,'buffer_bounds','Invalid embedded buffer length')
 need(not j.get('animations') and not j.get('skins'),'model_state','Animation/skin unsupported');need(not j.get('extensionsRequired'),'unsupported_extension','Required extensions unsupported')
 sizes={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4};formats={5120:'b',5121:'B',5122:'h',5123:'H',5125:'I',5126:'f'};widths={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4};decoded={};views=j.get('bufferViews',[]);accessors=j.get('accessors',[])
 for vi,v in enumerate(views):
  need(v.get('buffer',0)==0,'buffer_reference',str(vi));vo=v.get('byteOffset',0);vl=v.get('byteLength');need(integer(vo) and vo>=0,'view_offset',str(vi));need(integer(vl) and vl>0 and vo+vl<=bl,'view_bounds',str(vi))
  if 'byteStride' in v:need(integer(v['byteStride']) and 4<=v['byteStride']<=252 and v['byteStride']%4==0,'accessor_stride',str(vi))
 for i,a in enumerate(accessors):
  need('sparse' not in a and a.get('type') in widths and a.get('componentType') in sizes,'accessor_schema',str(i));need(integer(a.get('count')) and a['count']>0,'accessor_count',str(i));vi=a.get('bufferView');need(integer(vi) and 0<=vi<len(views),'view_reference',str(i));v=views[vi];component=sizes[a['componentType']];size=component*widths[a['type']];stride=v.get('byteStride',size);need(integer(stride) and stride>=size and stride%component==0,'accessor_stride',str(i));off=a.get('byteOffset',0);need(integer(off) and off>=0,'accessor_offset',str(i));need(off%component==0 and (v.get('byteOffset',0)+off)%component==0,'accessor_alignment',str(i));end=off+(a['count']-1)*stride+size;need(end<=v['byteLength'],'accessor_overrun',str(i));start=v.get('byteOffset',0)+off;fmt='<'+formats[a['componentType']]*widths[a['type']];values=[struct.unpack_from(fmt,binary,start+k*stride) for k in range(a['count'])];need(all(math.isfinite(x) for row in values for x in row),'nonfinite_accessor',str(i))
  for bound,fun in [('min',min),('max',max)]:
   if bound in a:
    declared=a[bound];need(isinstance(declared,list) and len(declared)==widths[a['type']] and all(type(x) in (int,float) and math.isfinite(x) for x in declared),'accessor_bounds',f'{i}: {bound} invalid');need(all(abs(fun(row[k] for row in values)-declared[k])<=max(1e-7,abs(declared[k])*2e-7) for k in range(len(declared))),'accessor_bounds',f'{i}: {bound} disagrees with bytes')
  decoded[i]=values
 triangles=0;vertices=0;minimum_area=None
 def accessor(i):need(integer(i) and 0<=i<len(accessors),'accessor_reference',str(i));return accessors[i],decoded[i]
 for prim in j['meshes'][0]['primitives']:
  need(prim.get('mode',4)==4 and not prim.get('extensions') and not prim.get('targets'),'primitive_contract','Only plain triangles');need(prim.get('material')==0,'material_reference','Expected material zero');attrs=prim.get('attributes',{});need('POSITION' in attrs and 'NORMAL' in attrs,'required_attributes','Missing POSITION or NORMAL');pa,pos=accessor(attrs['POSITION']);na,normals=accessor(attrs['NORMAL']);need(pa['type']=='VEC3' and pa['componentType']==5126 and not pa.get('normalized',False),'position_schema','Expected float32 VEC3');need('min' in pa and 'max' in pa,'position_bounds','POSITION requires min and max');need(na['type']=='VEC3' and na['componentType']==5126 and not na.get('normalized',False),'normal_schema','Expected float32 VEC3');ac,indices=accessor(prim.get('indices'));need(ac['type']=='SCALAR' and ac['componentType'] in [5121,5123,5125] and ac['count']%3==0 and not ac.get('normalized',False),'index_schema','Expected unsigned triangle indices');need('byteStride' not in views[ac['bufferView']],'index_stride','Indices must be tightly packed');idx=[q[0] for q in indices];need(all(0<=ii<len(pos) for ii in idx),'index_out_of_range','Index exceeds POSITION count')
  for semantic,acc in attrs.items():need(len(accessor(acc)[1])==len(pos),'attribute_count',semantic)
  need(all(.98<=sum(x*x for x in q)<=1.02 for q in normals),'normal_length','NORMAL not unit length');vertices+=len(pos);triangles+=len(idx)//3
  for k in range(0,len(idx),3):
   a,b,c=[pos[ii] for ii in idx[k:k+3]];u=[b[d]-a[d] for d in range(3)];v=[c[d]-a[d] for d in range(3)];cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];area=math.sqrt(sum(x*x for x in cross))/2;need(area>1e-12,'degenerate_triangle',str(k//3));minimum_area=area if minimum_area is None else min(minimum_area,area)
 nodes=j.get('nodes',[]);need(sum('mesh' in n for n in nodes)==1 and all(n.get('mesh',0)==0 for n in nodes),'node_mesh_contract','Exactly one mesh node required')
 for node in nodes:
  need('skin' not in node and not node.get('weights'),'model_state','Skin or morph weights unsupported')
  for key,size in [('translation',3),('rotation',4),('scale',3),('matrix',16)]:
   if key in node:need(len(node[key])==size and all(type(v) in (int,float) and math.isfinite(v) for v in node[key]),'node_transform',key)
 return {'format':'glTF 2.0 binary','bytes':len(data),'mesh_count':1,'material_count':1,'triangles':triangles,'decoded_export_vertices':vertices,'minimum_triangle_area_m2':minimum_area,'decoded_all_accessors_finite':True,'decoded_indices_in_range':True,'decoded_normals_unit_length':True,'external_resources':0,'runtime_render_verified':False}
def main():
 p=Path(sys.argv[1]);out=Path(sys.argv[2]);r={'file':p.name,'checker_version':VERSION,'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'model_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'run_id':str(uuid.uuid4()),'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':False,'failures':[]}
 try:r.update(validate(p));r['passed']=True
 except Rejected as e:r['failures'].append({'code':e.code,'detail':e.detail})
 except Exception as e:r['failures'].append({'code':'malformed_payload','detail':type(e).__name__+': '+str(e)})
 out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(r,indent=2));print('007 GLB',r['passed'],r['failures']);raise SystemExit(0 if r['passed'] else 1)
if __name__=='__main__':main()
