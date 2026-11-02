"""Readable 2D observations of original 007 GLB triangles; never generates or edits geometry.
Dependencies: numpy, Pillow, scipy. Strict plain-mesh subset, fixed projection in metres.
Raster-union complement measures visible 2D enclosed blank regions, NOT 3D clearance.
"""
from pathlib import Path
import argparse, struct, json, hashlib
import numpy as np
import PIL, scipy
from PIL import Image, ImageDraw
from scipy.ndimage import binary_fill_holes, label
VERSION='007-projection-1.1'
BASE=Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
class ProjectionError(ValueError):
 def __init__(self,code,detail): self.code=code;super().__init__(f'{code}: {detail}')
def need(ok,code,detail):
 if not ok: raise ProjectionError(code,detail)
def integer(value): return type(value) is int
def index(value,items,kind):
 need(integer(value) and 0<=value<len(items),f'{kind}_index',f'invalid index {value!r} for {len(items)} entries')
 return value
def finite_vector(value,length,kind):
 need(isinstance(value,list) and len(value)==length and all(type(v) in (int,float) and np.isfinite(v) for v in value),'node_transform',kind)
 return np.array(value,dtype=float)
def glb_geometry(path,source_bytes=None):
 # Decode this supplied immutable byte snapshot; build() hashes the same consumed bytes.
 b=Path(path).read_bytes() if source_bytes is None else source_bytes
 need(len(b)>=28,'glb_header','truncated GLB')
 magic,v,n=struct.unpack_from('<III',b)
 need((magic,v,n)==(0x46546c67,2,len(b)),'glb_header','invalid magic/version/declared length')
 off=12; chunks=[]
 while off<len(b):
  need(off+8<=len(b),'chunk_bounds','truncated chunk header')
  ln,ty=struct.unpack_from('<II',b,off)
  need(ln%4==0 and off+8+ln<=len(b),'chunk_bounds','unaligned or truncated chunk')
  chunks.append((ty,b[off+8:off+8+ln]));off+=ln+8
 need([q[0] for q in chunks]==[0x4e4f534a,0x004e4942],'chunk_layout','expected JSON then BIN only')
 j=json.loads(chunks[0][1]); binary=chunks[1][1]
 need(isinstance(j,dict) and j.get('asset',{}).get('version')=='2.0','asset_version','expected glTF 2.0')
 need(not j.get('animations') and not j.get('skins') and not j.get('extensionsRequired'),'model_state','animated/skinned/required-extension geometry unsupported')
 for field in ('buffers','bufferViews','accessors','nodes','scenes','meshes','materials'):
  need(isinstance(j.get(field),list) and len(j[field])>0 and all(isinstance(q,dict) for q in j[field]),'document_schema',field)
 need(len(j['buffers'])==1 and not j['buffers'][0].get('uri'),'buffer_contract','expected one embedded buffer')
 declared=j['buffers'][0].get('byteLength')
 need(integer(declared) and 0<declared<=len(binary) and len(binary)-declared<=3,'buffer_bounds','invalid embedded buffer length')
 need(len(j['meshes'])==1 and len(j['materials'])==1,'object_contract','007 expects one mesh and one material')
 material=j['materials'][0]
 need(material.get('alphaMode','OPAQUE')=='OPAQUE','material_contract','triangle-union silhouette assumes opaque material')
 views=j['bufferViews'];accessors=j['accessors']
 for vi,view in enumerate(views):
  index(view.get('buffer'),j['buffers'],'buffer')
  vo=view.get('byteOffset',0);vl=view.get('byteLength')
  need(integer(vo) and vo>=0 and integer(vl) and vl>0 and vo+vl<=declared,'view_bounds',str(vi))
  if 'byteStride' in view:
   stride=view['byteStride'];need(integer(stride) and 4<=stride<=252 and stride%4==0,'accessor_stride',str(vi))
 def access(i,kind):
  a=accessors[index(i,accessors,'accessor')]
  need('sparse' not in a and not a.get('normalized',False),'accessor_schema',kind+' requires plain unnormalized data')
  need(integer(a.get('count')) and a['count']>0,'accessor_count',kind)
  if kind=='position':
   need(a.get('type')=='VEC3' and a.get('componentType')==5126,'position_schema','expected float32 VEC3')
   dtype='<f4';width=3
  else:
   need(a.get('type')=='SCALAR' and a.get('componentType') in (5121,5123,5125),'index_schema','expected unsigned integer SCALAR')
   dtype={5121:'u1',5123:'<u2',5125:'<u4'}[a['componentType']];width=1
  view=views[index(a.get('bufferView'),views,'buffer_view')];size=np.dtype(dtype).itemsize
  if kind=='indices':need('byteStride' not in view,'index_stride','indices must be tightly packed')
  stride=view.get('byteStride',size*width);offset=a.get('byteOffset',0)
  need(integer(offset) and offset>=0,'accessor_offset',kind)
  need(integer(stride) and stride>=size*width and stride%size==0,'accessor_stride',kind)
  start=view.get('byteOffset',0)+offset
  need(offset%size==0 and start%size==0,'accessor_alignment',kind)
  need(offset+(a['count']-1)*stride+size*width<=view['byteLength'],'accessor_overrun',kind)
  out=np.ndarray((a['count'],width),dtype=dtype,buffer=binary,offset=start,strides=(stride,size)).copy()
  need(np.isfinite(out).all(),'nonfinite_accessor',kind)
  return out
 def local(n):
  if 'matrix' in n:
   need(not any(k in n for k in ('translation','scale','rotation')),'node_transform','matrix cannot coexist with TRS')
   m=finite_vector(n['matrix'],16,'matrix').reshape(4,4).T
   need(np.allclose(m[3],[0,0,0,1],rtol=0,atol=1e-10),'node_transform','matrix must be affine')
   need(abs(np.linalg.det(m[:3,:3]))>1e-12,'node_transform','singular matrix unsupported')
   return m
  x,y,z,w=finite_vector(n.get('rotation',[0,0,0,1]),4,'rotation')
  need(abs(x*x+y*y+z*z+w*w-1)<1e-5,'node_transform','quaternion must be unit length')
  scale=finite_vector(n.get('scale',[1,1,1]),3,'scale')
  need(np.all(abs(scale)>1e-12),'node_transform','singular scale unsupported')
  translation=finite_vector(n.get('translation',[0,0,0]),3,'translation')
  r=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
  m=np.eye(4);m[:3,:3]=r@np.diag(scale);m[:3,3]=translation;return m
 meshes=[];seen=set();transforms=[];nodes=j['nodes']
 def visit(i,parent,trail):
  index(i,nodes,'node')
  need(i not in trail and i not in seen,'node_graph','cycle or repeated node instance')
  seen.add(i);node=nodes[i]
  need('skin' not in node and 'weights' not in node,'model_state','skin or morph node unsupported')
  need(not node.get('extensions'),'node_extension','node extensions unsupported')
  m=parent@local(node);need(np.isfinite(m).all(),'node_transform','nonfinite world matrix')
  if 'mesh' in node:
   mesh=j['meshes'][index(node['mesh'],j['meshes'],'mesh')]
   need(not mesh.get('weights'),'model_state','mesh morph weights unsupported')
   primitives=mesh.get('primitives');need(isinstance(primitives,list) and len(primitives)==1,'primitive_contract','007 expects one primitive')
   for p in primitives:
    need(isinstance(p,dict) and p.get('mode',4)==4 and not p.get('targets') and not p.get('extensions'),'primitive_contract','plain triangles only')
    index(p.get('material'),j['materials'],'material')
    attrs=p.get('attributes');need(isinstance(attrs,dict) and 'POSITION' in attrs,'position_schema','POSITION required')
    pos=access(attrs['POSITION'],'position').astype(float);ids=access(p.get('indices'),'indices').flatten().astype(np.int64)
    need(len(ids)%3==0 and ids.min()>=0 and ids.max()<len(pos),'index_bounds','invalid triangle index payload')
    world=np.c_[pos,np.ones(len(pos))]@m.T
    need(np.isfinite(world).all() and np.allclose(world[:,3],1,rtol=0,atol=1e-10),'node_transform','non-affine/nonfinite transformed coordinates')
    # glTF world Y-up → Blender world Z-up: x_b=x_g, y_b=-z_g, z_b=y_g.
    blender=world[:,[0,2,1]];blender[:,1]*=-1
    meshes.append((blender,ids.reshape(-1,3)));transforms.append({'node':i,'world_matrix':m.tolist()})
  children=node.get('children',[]);need(isinstance(children,list),'node_graph','children must be a list')
  for child in children:visit(child,m,trail+[i])
 scene=j['scenes'][index(j.get('scene',0),j['scenes'],'scene')]
 roots=scene.get('nodes');need(isinstance(roots,list) and len(roots)>0,'scene_schema','nonempty root node list required')
 for root in roots:visit(root,np.eye(4),[])
 need(len(meshes)==1,'object_contract','007 requires exactly one primitive instance')
 return meshes[0][0],meshes[0][1],transforms

def project(vertices,triangles,view,res=2048):
 need(integer(res) and 32<=res<=8192,'raster_resolution','expected integer resolution from 32 to 8192')
 need(isinstance(vertices,np.ndarray) and vertices.ndim==2 and vertices.shape[1]==3 and len(vertices)>0 and np.isfinite(vertices).all(),'projection_vertices','finite Nx3 array required')
 need(isinstance(triangles,np.ndarray) and triangles.ndim==2 and triangles.shape[1]==3 and len(triangles)>0 and np.issubdtype(triangles.dtype,np.integer) and triangles.min()>=0 and triangles.max()<len(vertices),'projection_indices','valid integer triangle array required')
 scale=.50; target_z=.205
 if view=='front':xy=vertices[:,[0,2]].copy();xy[:,1]-=target_z
 elif view=='side':xy=vertices[:,[1,2]].copy();xy[:,1]-=target_z
 else:raise ProjectionError('projection_view',str(view))
 need(np.max(np.abs(xy))<scale/2-.001,'view_clipping','fixed view clips model')
 p=np.c_[((xy[:,0]/scale)+.5)*res,(.5-xy[:,1]/scale)*res]
 mask=Image.new('1',(res,res),0);draw=ImageDraw.Draw(mask)
 for tri in triangles:draw.polygon([tuple(q) for q in p[tri]],fill=1)
 body=np.array(mask,dtype=bool);filled=binary_fill_holes(body);holes=filled & ~body
 labels,count=label(holes);areas=[int(np.count_nonzero(labels==i)) for i in range(1,count+1)]
 # Deliberately include all interior pixel components in area; do not hide small holes.
 stats={'resolution_px':res,'metres_per_pixel':scale/res,'projection':'orthographic raster union of all triangle projections','view':view,'world_window_m':{'horizontal':[-.25,.25],'vertical':[-.045,.455]},'body_pixels':int(body.sum()),'interior_blank_pixels':int(holes.sum()),'interior_blank_components_px':areas,'interior_blank_area_cm2':float(holes.sum()*(scale/res)**2*10000)}
 return body,holes,stats

def colored(body,holes,out):
 rgb=np.zeros((*body.shape,3),dtype=np.uint8);rgb[:]=[236,237,229];rgb[body]=[55,61,49];rgb[holes]=[188,200,157]
 im=Image.fromarray(rgb).resize((1000,1000),Image.Resampling.LANCZOS);im.save(out,optimize=True)

def build(asset_root,outdir):
 outdir.mkdir(parents=True,exist_ok=True); records=[]
 for key in ['orison','latitude','ascend']:
  src=asset_root/key/'model.glb';info_path=asset_root/key/'model-info.json'
  source_bytes=src.read_bytes();info_bytes=info_path.read_bytes();info=json.loads(info_bytes);v,t,transforms=glb_geometry(src,source_bytes)
  actual=np.stack([v.min(0),v.max(0)],axis=1);expected=np.array(info['bounds_m'])
  need(expected.shape==(3,2) and np.isfinite(expected).all(),'native_bounds','finite 3x2 bounds required')
  max_error=float(abs(actual-expected).max());need(max_error<2e-6,'native_bounds','GLB world axes do not match native bounds')
  for view in ['front','side']:
   body,holes,stats=project(v,t,view,2048);_,_,low=project(v,t,view,1024)
   name=f'{key}-{view}-projection.png';colored(body,holes,outdir/name)
   stats.update({'file':name,'source_glb':f'assets/{key}/model.glb','source_glb_sha256':hashlib.sha256(source_bytes).hexdigest(),'source_info_sha256':hashlib.sha256(info_bytes).hexdigest(),'output_sha256':sha(outdir/name),'native_bounds_max_abs_error_m':max_error,'glb_world_transforms':transforms,'convergence_1024_area_cm2':low['interior_blank_area_cm2'],'convergence_absolute_difference_cm2':abs(stats['interior_blank_area_cm2']-low['interior_blank_area_cm2']),'interpretation':'2D unoccluded enclosed blank regions at this direction; not 3D passage, minimum aperture, physical stability, or manufacturing clearance.'})
   records.append(stats)
 report={'version':VERSION,'dependencies':{'numpy':np.__version__,'Pillow':PIL.__version__,'scipy':scipy.__version__},'generator_sha256':sha(__file__),'passed':True,'scope':'Six fixed-scale 2D raster projections from real GLB bytes; model quality is validated separately.','raster_limits':'Pillow polygon rasterization includes boundary pixels; resolution convergence is evidence, not exact continuous area proof.','records':records}
 (outdir/'projection-data.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--asset-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=build(a.asset_root,a.output);print(json.dumps([{'file':q['file'],'area_cm2':q['interior_blank_area_cm2'],'difference_cm2':q['convergence_absolute_difference_cm2']} for q in r['records']],indent=2))
