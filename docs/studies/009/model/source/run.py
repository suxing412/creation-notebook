"""Rebuild in a NEW directory, then inspect actual exported files. Never overwrites a model."""
import argparse,subprocess,sys,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True);p.add_argument('--angles');p.add_argument('--geometry-only',action='store_true');p.add_argument('--threads',type=int,default=4);a=p.parse_args();src=Path(__file__).resolve().parent;out=Path(a.output).resolve();out.parent.mkdir(parents=True,exist_ok=True)
def run(script,args):subprocess.run(['blender','-b','-t',str(a.threads),'--python-exit-code','1','--python',str(src/script),'--',*map(str,args)],check=True)
args=['--config',Path(a.config).resolve(),'--output',out]
if a.angles:args+=['--angles',a.angles]
if a.geometry_only:args+=['--geometry-only']
run('generate.py',args);common=['--model',out/'model.blend','--info',out/'model-info.json'];run('audit_native.py',common+['--glb',out/'model.glb','--report',out/'native-export-audit.json']);run('audit_assembly.py',common+['--report',out/'assembly-audit.json']);reports=[out/'native-export-audit.json',out/'assembly-audit.json'];assert all(json.loads(q.read_text())['passed'] for q in reports);print(json.dumps({'passed':True,'reports':[str(q) for q in reports]}))
