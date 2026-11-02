"""007 native numerical-limit dedicated probes, not production generation.
Constructs TWO known in-box invalid configs using recipe.geometry directly under work/ only.
The normal generator calls recipe.validate first and rejects both. This deliberate test-only
bypass proves native curvature/reference fields really trigger on actual saved .blend meshes.
No nonlocal-clearance counterexample search is performed or claimed.
"""
import sys,json,subprocess,argparse,hashlib,datetime,uuid,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import recipe
ROOT=Path(__file__).resolve().parents[1]
CASES=[('curvature-limit','curvature_radius_failures','Curvature times section circumradius',{'radius_x':.085,'radius_z':.22,'section_width':.072,'section_depth':.060,'asymmetry':.25,'depth_wave':0,'lean':0,'width_modulation':.27}),('frame-reference-limit','frame_reference_failures','Analytic frame reference near singularity',{'radius_x':.085,'radius_z':.10,'depth_wave':.042,'lean':.03})]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def make(base,out):
 import bpy
 info=json.loads((base/'model-info.json').read_text());proof=[]
 for name,field,expected,changes in CASES:
  c=dict(info['config'],**changes);recipe.validate(c,revision=1,check_geometry=False);error=None
  try:recipe.validate(c,revision=1)
  except ValueError as e:error=str(e)
  if error is None or expected not in error:raise RuntimeError('Normal generator must first reject known invalid config: '+name)
  # Explicit test-only bypass: NEVER invoke generate.py on these configurations.
  verts,faces,construction=recipe.geometry(c,revision=1);bpy.ops.wm.read_factory_settings(use_empty=True);me=bpy.data.meshes.new('Numerical gate fault mesh');me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new('ORISON | numerical fault '+name,me);bpy.context.scene.collection.objects.link(ob);material=bpy.data.materials.new('Numerical probe only');me.materials.append(material);bpy.context.preferences.filepaths.save_version=0;model=out/(name+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(model));case=json.loads(json.dumps(info));case['config']=c;case['construction']=construction;case['bounds_m']=[[min(v[i] for v in verts),max(v[i] for v in verts)] for i in range(3)];case['dimensions_mm']={k:round((case['bounds_m'][i][1]-case['bounds_m'][i][0])*1000,3) for i,k in enumerate(['width','depth','height'])};case['validation_status']='Intentionally invalid isolated numerical-limit test; not production asset';(out/(name+'-info.json')).write_text(json.dumps(case,indent=2));proof.append({'case':name,'dedicated_field':field,'normal_generator_validation_rejected':True,'normal_generator_rejection':error,'raw_input_box_and_cross_field_validation_passed':True,'bypass_used':'recipe.geometry(c, revision=1) called directly only in isolated work fault generator','config':c,'recipe_diagnostics_640_samples':construction['diagnostics'],'vertices':len(verts),'quad_faces':len(faces),'model_sha256':sha(model)})
 (out/'construction-proof.json').write_text(json.dumps(proof,indent=2))
def main():
 p=argparse.ArgumentParser();p.add_argument('--baseline',default=str(ROOT/'assets/orison'));p.add_argument('--label');p.add_argument('--make',action='store_true');p.add_argument('--output');a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else None);base=Path(a.baseline).resolve();label=a.label or datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:6];out=Path(a.output).resolve() if a.output else ROOT/'work'/('numeric-geometry-faults-'+label)
 if not re.fullmatch('[A-Za-z0-9-]+',label):raise RuntimeError('Simple alphanumeric/hyphen label required')
 out=out.resolve()
 if not out.is_relative_to(ROOT/'work'):raise RuntimeError('Invalid mesh files must remain inside work')
 if a.make:make(base,out);return
 out.mkdir(parents=True,exist_ok=False);report=ROOT/'review'/('gate-numeric-geometry-faults-'+label+'.json')
 if report.exists():raise RuntimeError('Refusing existing report')
 before={n:sha(base/n) for n in ['model.blend','model.glb','model-info.json','config.json']};checker=sha(ROOT/'source/check.py');recipe_sha=sha(recipe.__file__);result=subprocess.run(['blender','-b','-t','4','--python-exit-code','1','--python',str(Path(__file__).resolve()),'--','--make','--baseline',str(base),'--output',str(out)],capture_output=True,text=True);(out/'make.log').write_text(result.stdout+result.stderr);result.check_returncode();proof=json.loads((out/'construction-proof.json').read_text());rows=[]
 for entry in proof:
  name=entry['case'];target=ROOT/'review'/('gate-numeric-'+label+'-'+name+'.json')
  if target.exists():raise RuntimeError('Refusing existing validation report')
  result=subprocess.run(['blender','-b','-t','4','--python-exit-code','1','--python',str(ROOT/'source/check.py'),'--','--model',str(out/(name+'.blend')),'--info',str(out/(name+'-info.json')),'--report',str(target)],capture_output=True,text=True);(out/(name+'.log')).write_text(result.stdout+result.stderr);r=json.loads(target.read_text()) if target.exists() else {};hit=bool(r.get(entry['dedicated_field']));fresh=r.get('model_sha256')==sha(out/(name+'.blend')) and r.get('info_sha256')==sha(out/(name+'-info.json')) and r.get('checker_sha256')==checker and r.get('recipe_sha256')==recipe_sha and bool(r.get('run_id'));valid_contract=not r.get('input_contract_failures') and not r.get('recipe_vertex_envelope_failures') and not r.get('recipe_topology_failures');passed=result.returncode!=0 and r.get('passed') is False and hit and fresh and valid_contract;rows.append(dict(entry,exit_code=result.returncode,native_rejected=r.get('passed') is False,dedicated_field_triggered=hit,dedicated_trigger_values=r.get(entry['dedicated_field']),fresh_identity_verified=fresh,input_vertex_topology_contracts_passed=valid_contract,passed=passed,validation_report=target.name,other_nonempty_fields=[k for k,v in r.items() if (k.endswith('_failures') or k in ['nonadjacent_self_intersection_candidates','coplanar_positive_area_overlaps']) and v and k!=entry['dedicated_field']]));print(name,'dedicated',hit,'passed',passed,flush=True)
 after={n:sha(base/n) for n in before};stable=before==after;summary={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':all(q['passed'] for q in rows) and stable,'baseline':str(base.relative_to(ROOT)),'formal_assets_untouched':stable,'formal_file_sha256':after,'checker_sha256':checker,'recipe_sha256':recipe_sha,'test_script_sha256':sha(__file__),'tests':rows,'coverage':{'curvature_radius_failures':'Dedicated actual saved native mesh rejection triggered.','frame_reference_failures':'Dedicated actual saved native mesh rejection triggered.','nonlocal_centerline_clearance_failures':'NOT independently fault-trigger covered. Valid finite samples exercise the passing path; no known counterexample search was performed.'},'limits':['Input-validator rejection alone is not counted as native field coverage. Both normal generation calls reject before geometry creation; direct geometry construction is an intentional isolated test bypass.','Other defect fields may trigger too; each selected dedicated field must independently be nonempty.','This supplement does not claim all checker fields or all parameter-domain failure modes have dedicated faults.','Bad native binaries and logs remain under work; public reports contain only configuration, identities and numerical results.']};report.write_text(json.dumps(summary,indent=2));print('NUMERIC NATIVE FAULTS',summary['passed']);raise SystemExit(0 if summary['passed'] else 1)
if __name__=='__main__':main()
