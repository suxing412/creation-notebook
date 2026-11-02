"""007 real fault injection. Run with system Python; every Blender call uses --python-exit-code 1.
General GLB mutation and raw-state proof pattern adapted from study-006/source/test_faults.py.
New closed-sweep seam/frame/island construction uses 007 stations, not 006 folded-sheet indices.
Bad binaries/logs remain under work; public reports record exact dedicated field hits and identities.
"""
import sys,json,math,struct,subprocess,hashlib,argparse,datetime,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NATIVE=[('seam-open','seam_topology_failures'),('frame-ring-twist','ring_frame_fit_failures'),('point-deformation','ring_frame_fit_failures'),('frame-metadata-mismatch','frame_metadata_failures'),('reversed-face','inconsistent_winding_edges'),('contained-island','invalid_connected_components'),('piercing-prism','nonadjacent_self_intersection_candidates'),('oblique-coplanar','coplanar_positive_area_overlaps'),('oblique-offset-control','coplanar_positive_area_overlaps'),('missing-face','nonmanifold_edges'),('degenerate-face','degenerate_triangles'),('duplicate-face','duplicate_triangles'),('crossing-triangles','nonadjacent_self_intersection_candidates'),('mirrored-transform-inverted-world','non_positive_world_volume'),('modifier-solidify','model_state_contract_failures'),('shape-key-deform','model_state_contract_failures'),('parent-state','model_state_contract_failures'),('animation-state','model_state_contract_failures')]
STATE_REASONS={'modifier-solidify':'modifiers_present','shape-key-deform':'shape_keys_present','parent-state':'parent_present','animation-state':'animation_data_present'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def maker(base,out):
 import bpy
 from mathutils import Vector,Quaternion
 bpy.ops.wm.open_mainfile(filepath=str(base/'model.blend'));ob=next(o for o in bpy.data.objects if o.type=='MESH');origv=[tuple(v.co) for v in ob.data.vertices];origf=[tuple(f.vertices) for f in ob.data.polygons];ob.data.calc_loop_triangles();tris=[tuple(t.vertices) for t in ob.data.loop_triangles];info=json.loads((base/'model-info.json').read_text());m=info['construction']['cross_section_vertices'];n=info['construction']['station_count'];s=info['construction']['stations'][n//4];center=Vector(s['center']);T=Vector(s['tangent']);N=Vector(s['normal']);B=Vector(s['binormal'])
 def cube(v,f,half):
  offset=len(v)
  for a,b,c in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]:v.append(tuple(center+T*(a*half[0])+N*(b*half[1])+B*(c*half[2])))
  for ff in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:f.append(tuple(offset+i for i in ff))
 eligible=[]
 for t in tris:
  p=[Vector(origv[i]) for i in t];cross=(p[1]-p[0]).cross(p[2]-p[0]);normal=cross.normalized()
  if min(abs(x) for x in normal)>.10 and max(abs(x) for x in normal)<.95:eligible.append((cross.length,t))
 if not eligible:raise RuntimeError('No suitably oblique real triangle')
 target=max(eligible)[1];targetp=[Vector(origv[i]) for i in target];targetcenter=sum(targetp,Vector())/3;targetnormal=(targetp[1]-targetp[0]).cross(targetp[2]-targetp[0]).normalized();state_evidence=[]
 for name,field in NATIVE:
  ob.modifiers.clear();ob.constraints.clear();ob.animation_data_clear();ob.parent=None;ob.scale=(1,1,1);v=list(origv);f=list(origf);caseinfo=json.loads(json.dumps(info));extra=None
  if name=='seam-open':f=f[:-m]
  elif name=='frame-ring-twist':
   ss=info['construction']['stations'][0];q=Quaternion(Vector(ss['tangent']),.11);cc=Vector(ss['center'])
   for i in range(m):v[i]=tuple(cc+q@(Vector(v[i])-cc))
  elif name=='point-deformation':idx=m*7+4;v[idx]=tuple(Vector(v[idx])+Vector((.003,.002,.001)))
  elif name=='frame-metadata-mismatch':caseinfo['construction']['stations'][0]['normal']=[-x for x in caseinfo['construction']['stations'][0]['normal']]
  elif name=='reversed-face':f[len(f)//3]=tuple(reversed(f[len(f)//3]))
  elif name=='contained-island':cube(v,f,(.0002,.0002,.0002))
  elif name=='piercing-prism':cube(v,f,(.003,.003,info['config']['section_depth']))
  elif name in ['oblique-coplanar','oblique-offset-control']:
   idx=len(v);offset=targetnormal*(1e-6 if name=='oblique-offset-control' else 0);v.extend(tuple(targetcenter+(q-targetcenter)*.55+offset) for q in targetp);f.append((idx,idx+1,idx+2))
  elif name=='missing-face':f.pop(len(f)//3)
  elif name=='degenerate-face':idx=len(v);v.extend([(.5,.7,.6),(.51,.7,.6),(.52,.7,.6)]);f.append((idx,idx+1,idx+2))
  elif name=='duplicate-face':f.append(tuple(tris[len(tris)//3]))
  elif name=='crossing-triangles':idx=len(v);v.extend([(.5,.68,.6),(.54,.68,.6),(.52,.72,.6),(.52,.69,.58),(.52,.71,.62),(.52,.72,.58)]);f.extend([(idx,idx+1,idx+2),(idx+3,idx+4,idx+5)])
  elif name=='mirrored-transform-inverted-world':v=[(-q[0],q[1],q[2]) for q in v];f=[tuple(reversed(q)) for q in f];ob.scale.x=-1
  me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update();me.materials.append(ob.data.materials[0]);old=ob.data;ob.data=me
  raw=lambda:hashlib.sha256(json.dumps({'vertices':[tuple(q.co) for q in me.vertices],'faces':[tuple(q.vertices) for q in me.polygons]},sort_keys=True).encode()).hexdigest()
  raw_before=raw()
  if name=='modifier-solidify':modifier=ob.modifiers.new('Injected solidify','SOLIDIFY');modifier.thickness=.004
  elif name=='shape-key-deform':ob.shape_key_add(name='Basis');key=ob.shape_key_add(name='Injected deformation');key.data[len(key.data)//3].co.z+=.01;key.value=1
  elif name=='parent-state':extra=bpy.data.objects.new('Injected parent',None);bpy.context.scene.collection.objects.link(extra);ob.parent=extra
  elif name=='animation-state':ob.keyframe_insert(data_path='location',frame=1)
  if name in STATE_REASONS:state_evidence.append({'case':name,'raw_ob_data_before_sha256':raw_before,'raw_ob_data_after_sha256':raw(),'raw_ob_data_unchanged':raw_before==raw()})
  bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/(name+'.blend')));(out/(name+'-info.json')).write_text(json.dumps(caseinfo,indent=2));ob.modifiers.clear();ob.animation_data_clear();ob.parent=None
  if extra:bpy.data.objects.remove(extra,do_unlink=True)
  ob.data=old;bpy.data.meshes.remove(me)
 evidence={'state_proofs':state_evidence,'oblique_triangle_indices':target,'oblique_normal':[float(x) for x in targetnormal],'inset_fraction':.55,'offset_control_m':1e-6,'contained_island_center':list(center),'contained_island_half_side_m':.0002,'piercing_prism_half_lengths_m':[.003,.003,info['config']['section_depth']]};(out/'mutation-evidence.json').write_text(json.dumps(evidence,indent=2));print('CREATED',len(NATIVE),'native faults/controls')
def glb_mutants(base,out):
 data=(base/'model.glb').read_bytes();n=struct.unpack_from('<I',data,12)[0];j=json.loads(data[20:20+n]);nb=struct.unpack_from('<I',data,20+n)[0];binary=data[28+n:28+n+nb];prim=j['meshes'][0]['primitives'][0]
 def offset(acc):a=j['accessors'][acc];v=j['bufferViews'][a['bufferView']];return v.get('byteOffset',0)+a.get('byteOffset',0)
 def save(name,jj,bb):
  jb=json.dumps(jj,separators=(',',':')).encode();jb+=b' '*((-len(jb))%4);bb=bytes(bb);bb+=b'\0'*((-len(bb))%4);(out/(name+'.glb')).write_bytes(struct.pack('<III',0x46546C67,2,28+len(jb)+len(bb))+struct.pack('<II',len(jb),0x4E4F534A)+jb+struct.pack('<II',len(bb),0x004E4942)+bb)
 bb=bytearray(binary);struct.pack_into('<f',bb,offset(prim['attributes']['POSITION']),float('nan'));save('nan-position',j,bb)
 bb=bytearray(binary);ac=j['accessors'][prim['indices']];fmt={5121:'B',5123:'H',5125:'I'}[ac['componentType']];struct.pack_into('<'+fmt,bb,offset(prim['indices']),{5121:255,5123:65535,5125:4294967295}[ac['componentType']]);jj=json.loads(json.dumps(j));jj['accessors'][prim['indices']].pop('min',None);jj['accessors'][prim['indices']].pop('max',None);save('out-of-range-index',jj,bb)
 bb=bytearray(binary);struct.pack_into('<fff',bb,offset(prim['attributes']['NORMAL']),0,0,0);save('zero-normal',j,bb)
 jj=json.loads(json.dumps(j));jj['bufferViews'][jj['accessors'][prim['attributes']['POSITION']]['bufferView']]['byteStride']=4;save('undersized-stride',jj,binary)
 jj=json.loads(json.dumps(j));jj['accessors'][prim['attributes']['POSITION']]['byteOffset']=len(binary)+64;save('accessor-overrun',jj,binary)
 jj=json.loads(json.dumps(j));jj['accessors'][prim['attributes']['POSITION']]['byteOffset']=-12;save('negative-offset',jj,binary)
 return [('nan-position','nonfinite_accessor'),('out-of-range-index','index_out_of_range'),('zero-normal','normal_length'),('undersized-stride','accessor_stride'),('accessor-overrun','accessor_overrun'),('negative-offset','accessor_offset')]
def invoke(model,info,report,log):
 if report.exists():raise RuntimeError('Refusing stale report target: '+report.name)
 cmd=['blender','-b','-t','4','--python-exit-code','1','--python',str(ROOT/'source/check.py'),'--','--model',str(model),'--info',str(info),'--report',str(report)];p=subprocess.run(cmd,capture_output=True,text=True);log.write_text(p.stdout+p.stderr);r=json.loads(report.read_text()) if report.exists() else {};fresh=bool(r.get('run_id')) and r.get('model_sha256')==sha(model) and r.get('checker_sha256')==sha(ROOT/'source/check.py');return p.returncode,r,fresh

def main():
 p=argparse.ArgumentParser();p.add_argument('--baseline',default=str(ROOT/'assets/orison'));p.add_argument('--output');p.add_argument('--report');p.add_argument('--make',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else None);base=Path(a.baseline).resolve();tag=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:6];out=Path(a.output).resolve() if a.output else ROOT/'work'/('gate-faults-'+tag);out.mkdir(parents=True,exist_ok=True)
 if not out.is_relative_to(ROOT/'work'):raise RuntimeError('Bad samples must be inside study-007/work')
 if a.make:maker(base,out);return
 final=Path(a.report).resolve() if a.report else ROOT/'review'/('gate-fault-tests-'+tag+'.json')
 if final.exists():raise RuntimeError('Refusing to overwrite previous fault report')
 code,baseline,fresh=invoke(base/'model.blend',base/'model-info.json',out/'baseline-validation.json',out/'baseline.log')
 if code!=0 or not baseline.get('passed') or not fresh:raise RuntimeError('Baseline must pass current checker before injecting defects')
 cmd=['blender','-b','-t','4','--python-exit-code','1','--python',str(Path(__file__).resolve()),'--','--make','--baseline',str(base),'--output',str(out)];p=subprocess.run(cmd,capture_output=True,text=True);(out/'make.log').write_text(p.stdout+p.stderr);p.check_returncode();rows=[]
 for name,field in NATIVE:
  report=out/(name+'-validation.json');code,r,fresh=invoke(out/(name+'.blend'),out/(name+'-info.json'),report,out/(name+'.log'));hit=bool(r.get(field));reason=STATE_REASONS.get(name)
  if reason:hit=any(q.get('reason')==reason for q in r.get(field,[]))
  control=name=='oblique-offset-control';control_pass=(not hit and not r.get('nonadjacent_self_intersection_candidates')) if control else None;dedicated=control_pass if control else hit
  if name=='contained-island':dedicated=dedicated and not r.get('nonadjacent_self_intersection_candidates')
  row={'kind':'native','case':name,'exit_code':code,'rejected':code!=0 and r.get('passed') is False,'fresh_identity_verified':fresh,'dedicated_detector':field,'dedicated_detector_triggered':hit,'dedicated_expectation_satisfied':dedicated,'required_state_reason':reason,'trigger_count':len(r.get(field,[])),'is_offset_control':control,'expected_no_surface_intersections':name=='contained-island' or control,'actual_surface_intersection_candidates':len(r.get('nonadjacent_self_intersection_candidates',[])),'model_sha256':sha(out/(name+'.blend')),'checker_sha256':r.get('checker_sha256'),'public_validation':None};public=ROOT/'review'/(final.stem+'-'+name+'.json');public.write_text(json.dumps(r,indent=2));row['public_validation']=public.name;rows.append(row);print(name,'rejected',row['rejected'],'dedicated',dedicated,flush=True)
 for name,expected in glb_mutants(base,out):
  report=out/(name+'-validation.json');p=subprocess.run([sys.executable,str(ROOT/'source/check_glb.py'),str(out/(name+'.glb')),str(report)],capture_output=True,text=True);(out/(name+'.log')).write_text(p.stdout+p.stderr);r=json.loads(report.read_text()) if report.exists() else {};hit=any(q.get('code')==expected for q in r.get('failures',[]));fresh=r.get('model_sha256')==sha(out/(name+'.glb')) and r.get('checker_sha256')==sha(ROOT/'source/check_glb.py') and bool(r.get('run_id'));public=ROOT/'review'/(final.stem+'-'+name+'.json');public.write_text(json.dumps(r,indent=2));rows.append({'kind':'glb','case':name,'exit_code':p.returncode,'rejected':p.returncode!=0 and r.get('passed') is False,'fresh_identity_verified':fresh,'dedicated_detector':expected,'dedicated_detector_triggered':hit,'dedicated_expectation_satisfied':hit,'model_sha256':sha(out/(name+'.glb')),'checker_sha256':r.get('checker_sha256'),'public_validation':public.name});print(name,'rejected',rows[-1]['rejected'],'dedicated',hit,flush=True)
 evidence=json.loads((out/'mutation-evidence.json').read_text());passed=all(q['rejected'] and q['fresh_identity_verified'] and q['dedicated_expectation_satisfied'] for q in rows) and len(evidence['state_proofs'])==len(STATE_REASONS) and all(q['raw_ob_data_unchanged'] for q in evidence['state_proofs']);result={'baseline':str(base.relative_to(ROOT)),'baseline_sha256':sha(base/'model.blend'),'checker_sha256':sha(ROOT/'source/check.py'),'glb_checker_sha256':sha(ROOT/'source/check_glb.py'),'test_script_sha256':sha(__file__),'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':passed,'tests':rows,'mutation_evidence':evidence,'scope':'Actual files and checker executions; dedicated field must match its expectation. Offset control is still rejected for extra mesh island but overlap/intersection fields must be empty. Contained island must trigger connectivity without surface intersection. Public reports do not include bad binaries or private paths.'};final.parent.mkdir(parents=True,exist_ok=True);final.write_text(json.dumps(result,indent=2));print('FAULTS PASSED',passed,'report',final.name);raise SystemExit(0 if passed else 1)
if __name__=='__main__':main()
