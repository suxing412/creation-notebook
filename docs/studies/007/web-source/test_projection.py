"""Independent isolated projection reader/regression tests; no sculpture generation.
Usage: python web-source/test_projection.py --asset-root assets --output web-review/projection-unit-checks.json
Bad GLB fixtures are generated only in a TemporaryDirectory and never published.
"""
from pathlib import Path
import argparse,copy,hashlib,json,struct,subprocess,sys,tempfile
import numpy as np
import sys
sys.dont_write_bytecode=True
import project
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(ok,detail):
 if not ok:raise RuntimeError(detail)
def run(asset_root,output):
 results=[];failures=[];identities={}
 def case(name,fn):
  try:detail=fn();results.append({'name':name,'passed':True,'detail':detail})
  except Exception as e:failures.append({'name':name,'error':f'{type(e).__name__}: {e}'});results.append({'name':name,'passed':False})
 source=asset_root/'orison'/'model.glb';raw=source.read_bytes();n,typ=struct.unpack_from('<II',raw,12);original=json.loads(raw[20:20+n]);binchunk=raw[20+n:]
 with tempfile.TemporaryDirectory(prefix='web007-projection-tests-') as temp:
  temp=Path(temp)
  def encoded(name,data):
   body=json.dumps(data,separators=(',',':')).encode();body+=b' '*((-len(body))%4)
   out=struct.pack('<III',0x46546c67,2,12+8+len(body)+len(binchunk))+struct.pack('<II',len(body),0x4e4f534a)+body+binchunk
   path=temp/(name+'.glb');path.write_bytes(out);return path
  def reject(name,mutate,code):
   data=copy.deepcopy(original);mutate(data);path=encoded(name,data)
   try:project.glb_geometry(path)
   except project.ProjectionError as e:
    require(e.code==code,f'expected {code}, got {e.code}');return {'rejected':True,'code':e.code}
   raise RuntimeError('invalid fixture accepted')
  def real_control(key):
   glb=asset_root/key/'model.glb';info_path=asset_root/key/'model-info.json';info=json.loads(info_path.read_text());v,t,_=project.glb_geometry(glb)
   err=float(abs(np.stack((v.min(0),v.max(0)),axis=1)-np.array(info['bounds_m'])).max());require(err<2e-6,'native bounds mismatch')
   identities[key]={'glb_sha256':sha(glb),'info_sha256':sha(info_path)}
   return {'native_bounds_max_abs_error_m':err,'vertices':len(v),'triangles':len(t)}
  for key in ('orison','latitude','ascend'):case('valid actual '+key,lambda key=key:real_control(key))
  cases=[
   ('negative scene index',lambda d:d.update(scene=-1),'scene_index'),
   ('out-of-range scene index',lambda d:d.update(scene=len(d['scenes'])),'scene_index'),
   ('boolean scene index',lambda d:d.update(scene=False),'scene_index'),
   ('negative root node index',lambda d:d['scenes'][0].update(nodes=[-1]),'node_index'),
   ('out-of-range root node',lambda d:d['scenes'][0].update(nodes=[len(d['nodes'])]),'node_index'),
   ('float root node index',lambda d:d['scenes'][0].update(nodes=[0.0]),'node_index'),
   ('negative child index',lambda d:d['nodes'][0].update(children=[-1]),'node_index'),
   ('negative mesh index',lambda d:d['nodes'][0].update(mesh=-1),'mesh_index'),
   ('negative POSITION accessor',lambda d:d['meshes'][0]['primitives'][0]['attributes'].update(POSITION=-1),'accessor_index'),
   ('negative index accessor',lambda d:d['meshes'][0]['primitives'][0].update(indices=-1),'accessor_index'),
   ('negative bufferView index',lambda d:d['accessors'][0].update(bufferView=-1),'buffer_view_index'),
   ('negative buffer index',lambda d:d['bufferViews'][0].update(buffer=-1),'buffer_index'),
   ('negative material index',lambda d:d['meshes'][0]['primitives'][0].update(material=-1),'material_index'),
   ('float index accessor schema',lambda d:d['accessors'][2].update(componentType=5126),'index_schema'),
   ('integer position accessor schema',lambda d:d['accessors'][0].update(componentType=5125),'position_schema'),
   ('zero skin index is still unsupported',lambda d:d['nodes'][0].update(skin=0),'model_state'),
   ('negative accessor offset',lambda d:d['accessors'][0].update(byteOffset=-4),'accessor_offset'),
   ('sparse POSITION unsupported',lambda d:d['accessors'][0].update(sparse={}),'accessor_schema'),
   ('undersized vertex stride',lambda d:d['bufferViews'][0].update(byteStride=4),'accessor_stride'),
   ('projective node matrix',lambda d:d['nodes'][0].update(matrix=[1,0,0,.1,0,1,0,0,0,0,1,0,0,0,0,1]),'node_transform'),
   ('nonfinite translation',lambda d:d['nodes'][0].update(translation=[float('nan'),0,0]),'node_transform'),
   ('transparent material is not silhouette contract',lambda d:d['materials'][0].update(alphaMode='BLEND'),'material_contract'),
  ]
  for name,mutate,code in cases:case(name,lambda name=name,mutate=mutate,code=code:reject(name.replace(' ','-'),mutate,code))
  v,t,_=project.glb_geometry(source)
  def matrix_control():
   d=copy.deepcopy(original);d['nodes'][0]['matrix']=[1,0,0,0,0,1,0,0,0,0,1,0,0,.007,0,1]
   q,_,_=project.glb_geometry(encoded('valid-matrix',d));require(np.max(abs(q-v-[0,0,.007]))<1e-10,'matrix translation mismatch');return 'glTF +Y maps to Blender +Z'
  case('valid matrix translation',matrix_control)
  def trs_control():
   d=copy.deepcopy(original);d['nodes'].append({'translation':[.01,.02,.03],'children':[0]});d['scenes'][0]['nodes']=[1]
   q,_,_=project.glb_geometry(encoded('valid-parent',d));require(np.max(abs(q-v-[.01,-.03,.02]))<1e-10,'parent TRS mismatch');return 'parent composed before Y-up to Z-up'
  case('valid parent TRS',trs_control)
  vs=np.array([[-.1,0,.105],[.1,0,.105],[.1,0,.305],[-.1,0,.305],[-.05,0,.155],[.05,0,.155],[.05,0,.255],[-.05,0,.255]])
  tris=np.array([[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]])
  def known_area():
   _,_,s=project.project(vs,tris,'front',2048);require(abs(s['interior_blank_area_cm2']-100)<1,'raster area differs by >= 1 cm²')
   return {'exact_fixture_cm2':100,'raster_cm2':s['interior_blank_area_cm2'],'scope':'2D planar fixture, not sculpture manufacturing measurement'}
  case('known rectangular projected hole',known_area)
  def open_control():
   _,_,s=project.project(vs,tris[2:],'front',2048);require(s['interior_blank_area_cm2']==0,'open side falsely enclosed');return 'open complement connects to image boundary'
  case('open gap is not enclosed interior',open_control)
  def clipped():
   try:project.project(vs+[.5,0,0],tris,'front',2048)
   except project.ProjectionError as e:require(e.code=='view_clipping','unexpected rejection');return {'rejected':True,'code':e.code}
   raise RuntimeError('clipped view accepted')
  case('clipped view rejected',clipped)
  def optimized():
   d=copy.deepcopy(original);d['scenes'][0]['nodes']=[-1];p=encoded('optimized-negative-index',d)
   code="import sys;sys.path.insert(0,sys.argv[1]);import project\ntry:project.glb_geometry(sys.argv[2])\nexcept project.ProjectionError as e:print(e.code);sys.exit(0 if e.code=='node_index' else 2)\nelse:sys.exit(3)"
   proc=subprocess.run([sys.executable,'-B','-O','-c',code,str(Path(project.__file__).parent),str(p)],text=True,capture_output=True)
   require(proc.returncode==0 and proc.stdout.strip()=='node_index','Python -O bypassed rejection');return 'explicit node_index rejection retained with -O'
  case('optimization cannot remove rejection',optimized)
 report={'passed':not failures,'checker_version':'007-projection-tests-1.0','checker_sha256':sha(__file__),'projection_version':project.VERSION,'projection_sha256':sha(project.__file__),'dependencies':{'numpy':np.__version__,'Pillow':project.PIL.__version__,'scipy':project.scipy.__version__},'scope':'Isolated malformed-GLB and synthetic 2D projection fixtures plus three actual-file controls. Not a complete model, native-browser, GPU or manufacturing test.','historical_regression':{'version':'007-projection-1.0','negative_scene_root_index_accepted':True,'observation':'Independently executed against a real candidate GLB copy before the fix on 2026-11-01 UTC. Valid current assets were not affected.','current_expectation':'dedicated node_index rejection'},'input_identities':identities,'count':len(results),'results':results,'failures':failures}
 if output:output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'passed':report['passed'],'count':len(results),'failures':failures},indent=2));return report['passed']
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--asset-root',type=Path,default=ROOT/'assets');p.add_argument('--output',type=Path);a=p.parse_args();raise SystemExit(0 if run(a.asset_root,a.output) else 1)
