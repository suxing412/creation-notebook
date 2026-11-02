from pathlib import Path
import json,sys,subprocess
R=Path(__file__).resolve().parents[1];D=R/'dist';out=R/'review/model-final-binding.json'
subprocess.run([sys.executable,str(D/'model/source/audit_verify_identity.py'),'--root',str(D/'model'),'--report',str(out)],check=True)
r=json.loads(out.read_text());assert r['passed'];print('Imported model final gate bindings',len(r['records']),r['passed'])
