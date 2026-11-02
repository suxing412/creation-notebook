"""New-directory reproducible generation followed by actual-file geometry checks."""
import argparse,subprocess,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True);p.add_argument('--geometry-only',action='store_true');p.add_argument('--threads',type=int,default=4);a=p.parse_args();src=Path(__file__).resolve().parent;out=Path(a.output).resolve()
def run(script,args):subprocess.run(['blender','-b','-t',str(a.threads),'--python-exit-code','1','--python',str(src/script),'--',*map(str,args)],check=True)
args=['--config',Path(a.config).resolve(),'--output',out]
if a.geometry_only:args+=['--geometry-only']
run('generate.py',args);common=['--model',out/'model.blend','--info',out/'model-info.json'];run('audit_native.py',common+['--glb',out/'model.glb','--report',out/'native-export-audit.json']);run('audit_assembly.py',common+['--report',out/'assembly-audit.json']);assert all(json.loads((out/q).read_text())['passed']for q in ['native-export-audit.json','assembly-audit.json']);print('SLOT REPRODUCTION PASS')
