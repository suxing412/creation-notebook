"""Rebuild only into a NEW directory: geometry gate -> render -> final-file gate.
Blender 4.3.2; CPU; every subprocess has an explicit exit contract."""
import argparse,subprocess,sys,uuid,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True);p.add_argument('--samples',type=int,default=128);p.add_argument('--resolution',type=int,default=960);p.add_argument('--revision',type=int,default=1);p.add_argument('--views',default='beauty,front,side,top,rear,hole-detail');a=p.parse_args();out=Path(a.output).resolve();config=Path(a.config).resolve()
if not out.is_relative_to(ROOT) or out.exists():raise RuntimeError('Output must be a new directory within this study; no frozen overwrite')
if a.samples<1 or not 128<=a.resolution<=2048:raise ValueError('Invalid render budget')
label='rebuild-'+uuid.uuid4().hex[:12];out.mkdir(parents=True);log=ROOT/'work'/label;log.mkdir(parents=True);start=time.time()
base=['blender','-b','-t','4','--python-exit-code','1','--python',str(ROOT/'source/generate.py'),'--','--config',str(config),'--output',str(out),'--samples',str(a.samples),'--resolution',str(a.resolution),'--revision',str(a.revision),'--views',a.views]
for phase,cmd in [('geometry',base+['--geometry-only']),('pre-gate',[sys.executable,str(ROOT/'source/run_gates.py'),'--asset',str(out),'--label',label+'-pre']),('render',base),('final-gate',[sys.executable,str(ROOT/'source/run_gates.py'),'--asset',str(out),'--label',label+'-final'])]:
 r=subprocess.run(cmd,capture_output=True,text=True);(log/(phase+'.log')).write_text(r.stdout+r.stderr)
 if r.returncode:raise RuntimeError(phase+' failed with '+str(r.returncode)+'; retained evidence under work/'+label)
print(json.dumps({'passed':True,'output':str(out.relative_to(ROOT)),'final_identity_report':'review/gate-'+label+'-final-identity.json','elapsed_seconds':time.time()-start},indent=2))
