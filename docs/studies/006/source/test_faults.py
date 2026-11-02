"""Reproducible fault injection and dedicated-detector assertions. Bad binaries stay under work/.
Run with system Python: python source/test_faults.py --baseline assets/folio
"""
import sys,json,math,struct,subprocess,hashlib,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NATIVE=[('reversed-face','inconsistent_winding_edges'),('contained-island','invalid_connected_components'),('piercing-prism','nonadjacent_self_intersection_candidates'),('oblique-coplanar','coplanar_positive_area_overlaps'),('missing-face','nonmanifold_edges'),('degenerate-face','degenerate_triangles'),('duplicate-face','duplicate_triangles'),('crossing-triangles','nonadjacent_self_intersection_candidates'),('off-recipe-vertex','recipe_vertex_envelope_failures'),('mirrored-transform-inverted-world','non_positive_world_volume'),('modifier-solidify','model_state_contract_failures'),('shape-key-deform','model_state_contract_failures')]
STATE_REASONS={'modifier-solidify':'modifiers_present','shape-key-deform':'shape_keys_present'}
def maker(base,out):
 import bpy
 from mathutils import Vector
 bpy.ops.wm.open_mainfile(filepath=str(base/'model.blend'));ob=next(o for o in bpy.data.objects if o.type=='MESH');origv=[tuple(v.co) for v in ob.data.vertices];origf=[tuple(f.vertices) for f in ob.data.polygons];ob.data.calc_loop_triangles();tris=[tuple(t.vertices) for t in ob.data.loop_triangles];info=json.loads((base/'model-info.json').read_text());stations=info['construction']['stations'];station=next(q for q in stations if q['segment']=='line-2' and q['point'][1]>.065);yz=station['point'];tan=station['tangent'];normal=station['normal']
 def cube(v,f,half):
  offset=len(v)
  for x,t,n in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]:v.append((x*half[0],yz[0]+t*half[1]*tan[0]+n*half[2]*normal[0],yz[1]+t*half[1]*tan[1]+n*half[2]*normal[1]))
  for ff in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:f.append(tuple(offset+i for i in ff))
 # First oblique triangle with a long sheet-width edge. Its longitudinal edge may be short;
 # the exact original float32 quantization probe is separately fixed in test_coplanar_quantization.py.
 target=next(t for t in tris if abs((Vector(origv[t[1]])-Vector(origv[t[0]])).cross(Vector(origv[t[2]])-Vector(origv[t[0]])).normalized().z)>.1 and abs((Vector(origv[t[1]])-Vector(origv[t[0]])).cross(Vector(origv[t[2]])-Vector(origv[t[0]])).normalized().z)<.9 and (Vector(origv[t[1]])-Vector(origv[t[0]])).cross(Vector(origv[t[2]])-Vector(origv[t[0]])).length>.00005)
 state_evidence=[]
 for name,field in NATIVE:
  ob.modifiers.clear();ob.scale=(1,1,1);v=list(origv);f=list(origf)
  if name=='reversed-face':f[len(f)//3]=tuple(reversed(f[len(f)//3]))
  elif name=='contained-island':cube(v,f,(.0002,.0002,.0002))
  elif name=='piercing-prism':cube(v,f,(.002,.002,.010))
  elif name=='oblique-coplanar':
   p=[Vector(origv[i]) for i in target];center=sum(p,Vector())/3;idx=len(v);v.extend(tuple(center+(q-center)*.55) for q in p);f.append((idx,idx+1,idx+2))
  elif name=='missing-face':f.pop(len(f)//3)
  elif name=='degenerate-face':
   idx=len(v);v.extend([(.3,0,.1),(.31,0,.1),(.32,0,.1)]);f.append((idx,idx+1,idx+2))
  elif name=='duplicate-face':f.append(tuple(tris[len(tris)//3]))
  elif name=='crossing-triangles':
   idx=len(v);v.extend([(.3,-.02,.1),(.34,-.02,.1),(.32,.02,.1),(.32,-.01,.08),(.32,.01,.12),(.32,.02,.08)]);f.extend([(idx,idx+1,idx+2),(idx+3,idx+4,idx+5)])
  elif name=='off-recipe-vertex':v[len(v)//3]=(v[len(v)//3][0]+.01,*v[len(v)//3][1:])
  elif name=='mirrored-transform-inverted-world':v=[(-q[0],q[1],q[2]) for q in v];f=[tuple(reversed(q)) for q in f];ob.scale.x=-1
  me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update();me.materials.append(ob.data.materials[0]);old=ob.data;ob.data=me
  raw_before=hashlib.sha256(json.dumps({'vertices':[tuple(q.co) for q in me.vertices],'faces':[tuple(q.vertices) for q in me.polygons]},sort_keys=True).encode()).hexdigest()
  if name=='modifier-solidify':modifier=ob.modifiers.new('Injected solidify','SOLIDIFY');modifier.thickness=.004
  elif name=='shape-key-deform':
   ob.shape_key_add(name='Basis');key=ob.shape_key_add(name='Injected deformation');key.data[len(key.data)//3].co.z+=.01;key.value=1
  if name in STATE_REASONS:
   raw_after=hashlib.sha256(json.dumps({'vertices':[tuple(q.co) for q in me.vertices],'faces':[tuple(q.vertices) for q in me.polygons]},sort_keys=True).encode()).hexdigest();state_evidence.append({'case':name,'raw_ob_data_before_sha256':raw_before,'raw_ob_data_after_sha256':raw_after,'raw_ob_data_unchanged':raw_before==raw_after})
  bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/(name+'.blend')))
  ob.modifiers.clear();ob.data=old;bpy.data.meshes.remove(me)
 (out/'model-state-mutation-evidence.json').write_text(json.dumps(state_evidence,indent=2))
 (out/'model-info.json').write_text(json.dumps(info,indent=2));print('CREATED',len(NATIVE),'native counterexamples')
def glb_mutants(base,out):
 data=(base/'model.glb').read_bytes();n=struct.unpack_from('<I',data,12)[0];j=json.loads(data[20:20+n]);nb=struct.unpack_from('<I',data,20+n)[0];binary=data[28+n:28+n+nb];prim=j['meshes'][0]['primitives'][0]
 def offset(acc):
  a=j['accessors'][acc];view=j['bufferViews'][a['bufferView']];return view.get('byteOffset',0)+a.get('byteOffset',0)
 def save(name,jj,bb):
  jb=json.dumps(jj,separators=(',',':')).encode();jb+=b' '*((-len(jb))%4);bb=bytes(bb);bb+=b'\0'*((-len(bb))%4);content=struct.pack('<III',0x46546C67,2,28+len(jb)+len(bb))+struct.pack('<II',len(jb),0x4E4F534A)+jb+struct.pack('<II',len(bb),0x004E4942)+bb;(out/(name+'.glb')).write_bytes(content)
 bb=bytearray(binary);struct.pack_into('<f',bb,offset(prim['attributes']['POSITION']),float('nan'));save('nan-position',j,bb)
 bb=bytearray(binary);ac=j['accessors'][prim['indices']];fmt={5121:'B',5123:'H',5125:'I'}[ac['componentType']];struct.pack_into('<'+fmt,bb,offset(prim['indices']),{5121:255,5123:65535,5125:4294967295}[ac['componentType']]);save('out-of-range-index',j,bb)
 bb=bytearray(binary);struct.pack_into('<fff',bb,offset(prim['attributes']['NORMAL']),0,0,0);save('zero-normal',j,bb)
 jj=json.loads(json.dumps(j));jj['bufferViews'][jj['accessors'][prim['attributes']['POSITION']]['bufferView']]['byteStride']=4;save('undersized-stride',jj,binary)
 jj=json.loads(json.dumps(j));jj['accessors'][prim['attributes']['POSITION']]['byteOffset']=len(binary)+64;save('accessor-overrun',jj,binary)
 jj=json.loads(json.dumps(j));jj['accessors'][prim['attributes']['POSITION']]['byteOffset']=-12;save('negative-offset',jj,binary)
 return [('nan-position','Nonfinite accessor bytes'),('out-of-range-index','Index exceeds POSITION count'),('zero-normal','Invalid normal length'),('undersized-stride','Invalid accessor stride'),('accessor-overrun','Accessor exceeds bufferView'),('negative-offset','Invalid accessor offset')]
def main():
 p=argparse.ArgumentParser();p.add_argument('--baseline',default=str(ROOT/'assets/folio'));p.add_argument('--output',default=str(ROOT/'work/gate-faults'));p.add_argument('--make',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else None);base=Path(a.baseline).resolve();out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=True)
 if a.make:maker(base,out);return
 cmd=['blender','-b','-t','4','--python-exit-code','1','--python',str(Path(__file__).resolve()),'--','--make','--baseline',str(base),'--output',str(out)];r=subprocess.run(cmd,capture_output=True,text=True);(out/'make.log').write_text(r.stdout+r.stderr);r.check_returncode();rows=[]
 for name,field in NATIVE:
  report=out/(name+'-validation.json');cmd=['blender','-b','-t','4','--python-exit-code','1','--python',str(ROOT/'source/check.py'),'--','--model',str(out/(name+'.blend')),'--info',str(out/'model-info.json'),'--report',str(report)];r=subprocess.run(cmd,capture_output=True,text=True);(out/(name+'.log')).write_text(r.stdout+r.stderr);result=json.loads(report.read_text()) if report.exists() else {};hit=bool(result.get(field));state_reason=STATE_REASONS.get(name)
  if state_reason:hit=any(q.get('reason')==state_reason for q in result.get(field,[]))
  rows.append({'kind':'native','case':name,'exit_code':r.returncode,'rejected':r.returncode!=0 and result.get('passed') is False,'dedicated_detector':field,'dedicated_detector_triggered':hit,'required_state_reason':state_reason,'trigger_count':len(result.get(field,[])),'report':str(report.relative_to(ROOT)),'model_sha256':hashlib.sha256((out/(name+'.blend')).read_bytes()).hexdigest()});print(name,'rejected',rows[-1]['rejected'],'dedicated',hit,flush=True)
 for name,message in glb_mutants(base,out):
  r=subprocess.run([sys.executable,str(ROOT/'source/check_glb.py'),str(out/(name+'.glb')),str(out/(name+'-validation.json'))],capture_output=True,text=True);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log);rows.append({'kind':'glb','case':name,'exit_code':r.returncode,'rejected':r.returncode!=0,'dedicated_detector':message,'dedicated_detector_triggered':message in log,'model_sha256':hashlib.sha256((out/(name+'.glb')).read_bytes()).hexdigest()});print(name,'rejected',r.returncode!=0,'dedicated',message in log,flush=True)
 current=(ROOT/'source/check.py').read_text();legacy=current.replace('volume=world_volume\n','volume=local_volume\n').replace('topology,object_contract,material_contract,transform_contract,model_state]','topology,object_contract,material_contract,model_state]')
 legacy=legacy.replace("sys.path.insert(0,str(Path(__file__).resolve().parent));import recipe","sys.path.insert(0,"+repr(str(ROOT/'source'))+");import recipe")
 legacy_path=out/'legacy-local-volume-policy.py';legacy_path.write_text(legacy);legacy_report=out/'legacy-world-inversion-validation.json';r=subprocess.run(['blender','-b','-t','4','--python-exit-code','1','--python',str(legacy_path),'--','--model',str(out/'mirrored-transform-inverted-world.blend'),'--info',str(out/'model-info.json'),'--report',str(legacy_report)],capture_output=True,text=True);(out/'legacy-world-inversion.log').write_text(r.stdout+r.stderr);old=json.loads(legacy_report.read_text());historical={'case':'world inversion under old local-volume-only policy','historical_false_pass_reproduced':r.returncode==0 and old['passed'] is True,'world_volume_m3':old['component_records'][0]['signed_world_volume_m3'],'local_volume_m3':old['component_records'][0]['signed_local_volume_m3'],'note':'Derived working checker disables transform rejection and restores local-volume decision; current production checker is not modified.','report':str(legacy_report.relative_to(ROOT))}
 state_proofs=json.loads((out/'model-state-mutation-evidence.json').read_text())
 report={'baseline':str(base.relative_to(ROOT)),'baseline_sha256':hashlib.sha256((base/'model.blend').read_bytes()).hexdigest(),'checker_sha256':hashlib.sha256((ROOT/'source/check.py').read_bytes()).hexdigest(),'glb_checker_sha256':hashlib.sha256((ROOT/'source/check_glb.py').read_bytes()).hexdigest(),'passed':all(r['rejected'] and r['dedicated_detector_triggered'] for r in rows) and historical['historical_false_pass_reproduced'] and len(state_proofs)==2 and all(x['raw_ob_data_unchanged'] for x in state_proofs),'model_state_raw_data_proofs':state_proofs,'historical_policy_reproduction':historical,'tests':rows,'scope':'Actual fault files and actual checker executions. Dedicated detector must trigger; rejection by another defect is not credited.'};(ROOT/'review/gate-fault-tests.json').write_text(json.dumps(report,indent=2));print('FAULTS PASSED',report['passed']);raise SystemExit(0 if report['passed'] else 1)
if __name__=='__main__':main()
