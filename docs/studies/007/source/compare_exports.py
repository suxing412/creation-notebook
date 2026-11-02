"""Read-only 007 native/GLB oriented-triangle geometry comparison.
Compares actual triangle coordinate multisets after Blender Z-up -> glTF Y-up rotation.
This is NOT indexed mesh-topology isomorphism or normal/shader/render equivalence.
"""
import bpy,sys,json,struct,argparse,hashlib,uuid,datetime
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent))
import check_glb
VERSION='007-export-comparison-1.0'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def cycle(points):p=tuple(points);return min(p[i:]+p[:i] for i in range(3))
def run(model,glb):
 payload=check_glb.validate(glb);b=Path(glb).read_bytes();n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);binary=b[28+n:];need=check_glb.need
 need(len(j['nodes'])==1 and j['nodes'][0].get('mesh')==0,'comparison_node_contract','One direct mesh node required');node=j['nodes'][0]
 for key,identity in [('translation',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1]),('matrix',[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1])]:need(key not in node or node[key]==identity,'comparison_node_transform','Only identity export node supported')
 def accessor(index):
  a=j['accessors'][index];v=j['bufferViews'][a['bufferView']];width={'SCALAR':1,'VEC3':3}[a['type']];fmt={5121:'B',5123:'H',5125:'I',5126:'f'}[a['componentType']];size=struct.calcsize('<'+fmt)*width;start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',size);return [struct.unpack_from('<'+fmt*width,binary,start+k*stride) for k in range(a['count'])]
 exported=Counter();exported_points=Counter();exported_vertex_count=0
 for prim in j['meshes'][0]['primitives']:
  pos=accessor(prim['attributes']['POSITION']);indices=[q[0] for q in accessor(prim['indices'])];exported_vertex_count+=len(pos);exported_points.update(pos)
  for k in range(0,len(indices),3):exported[cycle([pos[i] for i in indices[k:k+3]])]+=1
 bpy.ops.wm.open_mainfile(filepath=str(model));obs=[o for o in bpy.data.objects if o.type=='MESH'];need(len(obs)==1,'comparison_native_objects','Expected one mesh');ob=obs[0];me=ob.data;me.calc_loop_triangles();world=[ob.matrix_world@v.co for v in me.vertices];pos=[(float(q.x),float(q.z),-float(q.y)) for q in world];native=Counter(cycle([pos[i] for i in t.vertices]) for t in me.loop_triangles);native_points=Counter(pos)
 missing=native-exported;extra=exported-native;equal=not missing and not extra
 return {'passed':equal,'native_vertices':len(pos),'exported_vertices':exported_vertex_count,'native_triangles':sum(native.values()),'exported_triangles':sum(exported.values()),'exact_oriented_triangle_coordinate_multisets_equal':equal,'exact_vertex_coordinate_multisets_equal':native_points==exported_points,'missing_triangle_multiplicity':sum(missing.values()),'extra_triangle_multiplicity':sum(extra.values()),'coordinate_tolerance_m':0,'axis_mapping':'native (x,y,z) -> glTF (x,z,-y)','indexed_topology_isomorphism_verified':False,'normals_correspondence_verified':False,'runtime_render_verified':False,'payload_validation_passed':True}
def main():
 p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--glb',required=True);p.add_argument('--report',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);r={'checker_version':VERSION,'checker_sha256':sha(__file__),'glb_checker_sha256':sha(check_glb.__file__),'model_sha256':sha(a.model),'glb_sha256':sha(a.glb),'run_id':str(uuid.uuid4()),'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':False,'failures':[]}
 try:r.update(run(a.model,a.glb))
 except Exception as e:r['failures'].append({'type':type(e).__name__,'message':str(e)})
 out=Path(a.report);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(r,indent=2));print('007 EXPORT COMPARISON',r['passed'])
 if not r['passed']:raise RuntimeError('Native/GLB comparison rejected')
if __name__=='__main__':main()
