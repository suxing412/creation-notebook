from pathlib import Path
import importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];D=R/'dist'if(R/'dist/index.html').exists()else R
p=D/'model/source/audit_verify_identity.py';spec=importlib.util.spec_from_file_location('model_identity_verifier',p);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
r=module.verify();assert r['passed'],r['failures'];review=R/'review'if(R/'review').exists()else R/'web-review';(review/'model-final-binding.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print('actual imported model gate bindings',len(r['checks']),r['passed'])
