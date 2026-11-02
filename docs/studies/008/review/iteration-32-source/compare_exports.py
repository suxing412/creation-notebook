"""Read-only 008 native/GLB oriented-triangle geometry comparison.
Compares actual triangle coordinate multisets after Blender Z-up -> glTF Y-up rotation.
Also compares each triangle corner normal after the same axis mapping (2e-4 vector tolerance).
This is NOT indexed mesh-topology isomorphism, shader equivalence or runtime rendering.
"""
import bpy,sys,json,struct,argparse,hashlib,uuid,datetime,math
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent))
import check_glb
VERSION='008-export-comparison-1.1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def cycle(points):p=tuple(points);return min(p[i:]+p[:i] for i in range(3))
def paired_cycle(points,normals):
 p=tuple(points);n=tuple(normals);i=min(range(3),key=lambda i:p[i:]+p[:i]);return p[i:]+p[:i],n[i:]+n[:i]
def run(model,glb):
 payload=check_glb.validate(glb);b=Path(glb).read_bytes();n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);binary=b[28+n:];need=check_glb.need
 need(len(j['nodes'])==1 and j['nodes'][0].get('mesh')==0,'comparison_node_contract','One direct mesh node required');node=j['nodes'][0]
 for key,identity in [('translation',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1]),('matrix',[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1])]:need(key not in node or node[key]==identity,'comparison_node_transform','Only identity export node supported')
 def accessor(index):
  a=j['accessors'][index];v=j['bufferViews'][a['bufferView']];width={'SCALAR':1,'VEC3':3}[a['type']];fmt={5121:'B',5123:'H',5125:'I',5126:'f'}[a['componentType']];size=struct.calcsize('<'+fmt)*width;start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',size);return [struct.unpack_from('<'+fmt*width,binary,start+k*stride) for k in range(a['count'])]
 exported=Counter();exported_points=Counter();exported_vertex_count=0;exported_corner_normals={}
 for prim in j['meshes'][0]['primitives']:
  pos=accessor(prim['attributes']['POSITION']);normals=accessor(prim['attributes']['NORMAL']);indices=[q[0] for q in accessor(prim['indices'])];exported_vertex_count+=len(pos);exported_points.update(pos)
  for k in range(0,len(indices),3):
   key,ns=paired_cycle([pos[i] for i in indices[k:k+3]],[normals[i] for i in indices[k:k+3]]);exported[key]+=1;exported_corner_normals.setdefault(key,[]).append(ns)
 bpy.ops.wm.open_mainfile(filepath=str(model));obs=[o for o in bpy.data.objects if o.type=='MESH'];need(len(obs)==1,'comparison_native_objects','Expected one mesh');ob=obs[0];me=ob.data;me.calc_loop_triangles();world=[ob.matrix_world@v.co for v in me.vertices];pos=[(float(q.x),float(q.z),-float(q.y)) for q in world];native=Counter(cycle([pos[i] for i in t.vertices]) for t in me.loop_triangles);native_points=Counter(pos);native_corner_normals={};normal_matrix=ob.matrix_world.to_3x3().inverted().transposed();corner_normals=[normal_matrix@q.vector for q in me.corner_normals]
 for tri in me.loop_triangles:
  normals=[(float(corner_normals[l].x),float(corner_normals[l].z),-float(corner_normals[l].y)) for l in tri.loops];key,ns=paired_cycle([pos[i] for i in tri.vertices],normals);native_corner_normals.setdefault(key,[]).append(ns)
 missing=native-exported;extra=exported-native;equal=not missing and not extra;max_normal_error=0.;normal_tests=0;normal_failures=[]
 for key,nlist in native_corner_normals.items():
  other=exported_corner_normals.get(key,[])
  if len(nlist)!=1 or len(other)!=1:
   normal_failures.append({'reason':'missing_or_ambiguous_oriented_triangle','native_count':len(nlist),'export_count':len(other)});continue
  for a,b in zip(nlist[0],other[0]):
   error=math.sqrt(math.fsum((x-y)**2 for x,y in zip(a,b)));normal_tests+=1;max_normal_error=max(max_normal_error,error)
   if not math.isfinite(error) or error>2e-4:normal_failures.append({'reason':'corner_normal_vector_mismatch','error':error})
 normals_equal=not normal_failures and normal_tests==sum(native.values())*3
 return {'passed':equal and normals_equal,'native_vertices':len(pos),'exported_vertices':exported_vertex_count,'native_triangles':sum(native.values()),'exported_triangles':sum(exported.values()),'exact_oriented_triangle_coordinate_multisets_equal':equal,'exact_vertex_coordinate_multisets_equal':native_points==exported_points,'exact_vertex_coordinate_sets_equal':set(native_points)==set(exported_points),'missing_triangle_multiplicity':sum(missing.values()),'extra_triangle_multiplicity':sum(extra.values()),'coordinate_tolerance_m':0,'axis_mapping':'native (x,y,z) -> glTF (x,z,-y)','indexed_topology_isomorphism_verified':False,'normals_correspondence_verified':normals_equal,'matched_corner_normals':normal_tests,'maximum_corner_normal_vector_error':max_normal_error,'normal_vector_tolerance':2e-4,'corner_normal_failures_count':len(normal_failures),'corner_normal_failures':normal_failures[:16],'runtime_render_verified':False,'payload_validation_passed':True}
def main():
 p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--glb',required=True);p.add_argument('--report',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);r={'checker_version':VERSION,'checker_sha256':sha(__file__),'glb_checker_sha256':sha(check_glb.__file__),'model_sha256':sha(a.model),'glb_sha256':sha(a.glb),'run_id':str(uuid.uuid4()),'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':False,'failures':[]}
 try:r.update(run(a.model,a.glb))
 except Exception as e:r['failures'].append({'type':type(e).__name__,'message':str(e)})
 out=Path(a.report);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(r,indent=2));print('008 EXPORT COMPARISON',r['passed'])
 if not r['passed']:raise RuntimeError('Native/GLB comparison rejected')
if __name__=='__main__':main()
