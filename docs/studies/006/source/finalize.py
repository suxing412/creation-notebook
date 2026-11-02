"""Recheck final assets and current-source GLB reproducibility, then write the current manifest.
No upload, external publication, or browser settings changes. Run only after all renders finish.
"""
from pathlib import Path
import sys,subprocess,json,hashlib,time,tempfile
R=Path(__file__).resolve().parents[1];S=R/'source';NAMES=['atlas','folio','spire'];start=time.time()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def blend(script,*args):subprocess.run(['blender','-b','-t','6','--python-exit-code','1','--python',str(S/script),'--',*map(str,args)],check=True)
for n in NAMES:
 d=R/'assets'/n
 for f in ['model.blend','model.glb','scene.blend','model-info.json','beauty.png','front.png','side.png','top.png','rear.png','bend-detail.png','contact-detail.png']:assert (d/f).is_file(),str(d/f)
 blend('check.py','--model',d/'model.blend','--info',d/'model-info.json','--report',d/'validation.json')
 subprocess.run([sys.executable,str(S/'check_glb.py'),str(d/'model.glb'),str(d/'glb-validation.json')],check=True)
 blend('inspect_sections.py','--model',d/'model.blend','--info',d/'model-info.json','--report',d/'section-measurements.json')
blend('audit_scene.py')
blend('inspect_terminal_feature.py','--scene',R/'assets/folio/scene.blend','--info',R/'assets/folio/model-info.json','--report',R/'review/terminal-feature-evidence.json','--diagnostic',R/'review/terminal-cap-diagnostic.png','--no-render')
subprocess.run([sys.executable,str(S/'test_contract.py')],check=True)
subprocess.run(['node',str(S/'test_three_loader.mjs')],check=True)
subprocess.run(['node',str(S/'test_viewer_state.cjs')],check=True)
repro=[]
for n in NAMES+['folio']:
 with tempfile.TemporaryDirectory(prefix='repro-',dir=R/'work') as td:
  d=Path(td);blend('generate.py','--config',R/'configs'/(n+'.json'),'--output',d,'--geometry-only')
  actual=sha(d/'model.glb');expected=sha(R/'assets'/n/'model.glb');assert actual==expected,(n,actual,expected);repro.append({'variant':n,'generated_glb_sha256':actual,'final_glb_sha256':expected,'bytes':(d/'model.glb').stat().st_size,'byte_identical':True})
repro_report={'passed':True,'blender_version':'4.3.2','seed':0,'runs':repro,'source_sha256':{p.name:sha(p) for p in [S/'generate.py',S/'recipe.py']},'scope':'Current source regenerated all three final GLBs and Folio a second time in this environment. Not native .blend byte identity or cross-hardware/image/render-engine equality.'};(R/'review/reproducibility.json').write_text(json.dumps(repro_report,indent=2))
subprocess.run([sys.executable,str(S/'make_contact_sheet.py')],check=True)
subprocess.run([sys.executable,str(S/'clean_png.py')],check=True)
subprocess.run([sys.executable,str(S/'compare_sampling.py')],check=True)
rows=[]
for n in NAMES:
 d=R/'assets'/n;info=json.loads((d/'model-info.json').read_text());qa=json.loads((d/'validation.json').read_text());assert qa['passed'] and qa['checker_sha256']==sha(S/'check.py');rows.append({'id':n,'config':info['config'],'dimensions_mm':info['dimensions_mm'],'triangles':info['triangles'],'vertices':sum(qa['component_records'][0]['component_sizes']),'native_gate_passed':qa['passed'],'glb_payload_passed':json.loads((d/'glb-validation.json').read_text())['passed'],'realtime_verified':False,'physical_engineering_verified':False,'render_elapsed_seconds':info.get('elapsed_seconds'),'pipeline_elapsed_seconds':info.get('pipeline_elapsed_seconds'),'files':{f.name:{'bytes':f.stat().st_size,'sha256':sha(f)} for f in sorted(d.iterdir()) if f.is_file()}})
manifest={'title':'FOLIO / 折页','study':'006','recipe_version':'1.0.0','status':'candidate-awaiting-root-review','blender_version':'4.3.2','seed':0,'geometry_units':'metres','variant_count':3,'variants':rows,'invariants':['one closed connected shell','four circular centreline bends','two sampled planar ground spans','fixed material and studio','no assembly-pair exceptions'],'finite_mesh_test_points':['atlas','folio','spire','boundary-low','boundary-high','first-version'],'parameter_domain_note':'108 explicit input cases; 512 box corners validator-only (320 accepted/192 rejected); no continuous-domain proof.','rendering':{'renderer':'Cycles CPU','threads':6,'max_samples':256,'adaptive_threshold':.01,'resolution':[960,960],'views':['beauty','front','side','top','rear','bend-detail','contact-detail'],'denoising':False,'view_transform':'AgX','exposure':0,'seed':0,'monetary_cost':'not available; no invented monetary charge'},'source_sha256':{p.name:sha(p) for p in sorted(S.iterdir()) if p.is_file()},'checks':{'input':'review/gate-input-tests.json','native_and_payload':'assets/*/validation.json + glb-validation.json','faults':'review/gate-fault-tests.json','coplanar_quantization':'review/gate-coplanar-quantization-reproduction.json','world_inversion':'review/gate-world-inversion-before.json + gate-world-inversion-after.json','three_parse':'review/three-loader-tests.json','viewer_cpu_state':'review/viewer-state-tests.json','reproducibility':'review/reproducibility.json','studio':'review/scene-audit.json'},'unverified':['GPU/WebGL rendering','dynamic z-fighting','real iPhone','manufacturing/forming/springback/tolerances','loads/stability/slip','ergonomics/book fit'],'viewer':{'entry':'view.html','three_revision':'180','external_network_dependencies':False,'fallback':'same-variant actual CPU render; no GL-security override'},'finalization_elapsed_seconds':round(time.time()-start,3)};(R/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False));print('FINALIZED',time.time()-start)
