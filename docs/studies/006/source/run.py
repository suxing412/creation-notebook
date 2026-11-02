"""Transactional recipe CLI; rejects invalid geometry before rendering; never overwrites a destination."""
import argparse,subprocess,json,tempfile,shutil,sys,hashlib,time
from pathlib import Path
from PIL import Image
p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True);p.add_argument('--threads',type=int,default=6);p.add_argument('--samples',type=int,default=256);p.add_argument('--resolution',type=int,default=960);a=p.parse_args();src=Path(__file__).resolve().parent;out=Path(a.output).resolve();config=Path(a.config).resolve();start=time.time()
if out.exists():raise SystemExit('Refusing to overwrite an existing output folder')
if not 1<=a.threads<=32 or not 16<=a.samples<=1024 or not 256<=a.resolution<=1600:raise SystemExit('Invalid render resource limits')
out.parent.mkdir(parents=True,exist_ok=True)
def blender(script,*args):subprocess.run(['blender','-b','-t',str(a.threads),'--python-exit-code','1','--python',str(src/script),'--',*map(str,args)],check=True)
def gates(d):
 blender('check.py','--model',d/'model.blend','--info',d/'model-info.json','--report',d/'validation.json')
 subprocess.run([sys.executable,str(src/'check_glb.py'),str(d/'model.glb'),str(d/'glb-validation.json')],check=True)
 blender('inspect_sections.py','--model',d/'model.blend','--info',d/'model-info.json','--report',d/'section-measurements.json')
with tempfile.TemporaryDirectory(prefix='.folio-staging-',dir=out.parent) as td:
 d=Path(td);common=['--config',config,'--output',d,'--samples',a.samples,'--resolution',a.resolution]
 blender('generate.py',*common,'--geometry-only');gates(d);blender('generate.py',*common)
 for image in d.glob('*.png'):
  im=Image.open(image);before=hashlib.sha256(im.tobytes()).hexdigest();im.save(image);assert hashlib.sha256(Image.open(image).tobytes()).hexdigest()==before
 gates(d);info=json.loads((d/'model-info.json').read_text());info['validation_status']='static-QA-passed';info['pipeline_elapsed_seconds']=round(time.time()-start,3);(d/'model-info.json').write_text(json.dumps(info,indent=2,ensure_ascii=False))
 for path in d.iterdir():
  if path.suffix in ['.blend','.glb','.png'] and any(x in path.read_bytes() for x in [b'/workspace/',b'/home/agent/',b'/tmp/',b'file://']):raise RuntimeError('Private path marker in '+path.name)
 shutil.copytree(d,out)
print('PASSED',out.name,round(time.time()-start,3))
