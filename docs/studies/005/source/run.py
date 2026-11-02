"""Recommended transactional generation CLI. New folders only; publish after all gates."""
import argparse,subprocess,json,tempfile,shutil,sys,struct,hashlib
from pathlib import Path
from PIL import Image
p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True);p.add_argument('--threads',type=int,default=6);a=p.parse_args();src=Path(__file__).resolve().parent;out=Path(a.output).resolve();config=Path(a.config).resolve()
if out.exists():raise SystemExit('Refusing to overwrite an existing output folder')
if not 1<=a.threads<=32:raise SystemExit('threads must be 1..32')
out.parent.mkdir(parents=True,exist_ok=True)
def blender(script,*args):subprocess.run(['blender','-b','-t',str(a.threads),'--python-exit-code','1','--python',str(src/script),'--',*map(str,args)],check=True)
with tempfile.TemporaryDirectory(prefix='.vesper-staging-',dir=out.parent) as td:
 d=Path(td)
 # Reject geometric boundary failures before spending CPU time on six renders.
 blender('generate.py','--config',config,'--output',d,'--geometry-only')
 blender('check.py','--model',d/'model.blend','--info',d/'model-info.json','--report',d/'validation.json')
 subprocess.run([sys.executable,str(src/'check_glb.py'),str(d/'model.glb'),str(d/'glb-validation.json')],check=True)
 blender('generate.py','--config',config,'--output',d)
 # Strip auxiliary PNG metadata, including text/EXIF. Decoded pixels are checked unchanged.
 for image in d.glob('*.png'):
  im=Image.open(image);before=hashlib.sha256(im.tobytes()).hexdigest();im.save(image);assert hashlib.sha256(Image.open(image).tobytes()).hexdigest()==before
 blender('check.py','--model',d/'model.blend','--info',d/'model-info.json','--report',d/'validation.json')
 subprocess.run([sys.executable,str(src/'check_glb.py'),str(d/'model.glb'),str(d/'glb-validation.json')],check=True)
 info=json.loads((d/'model-info.json').read_text());info['validation_status']='static-QA-passed';(d/'model-info.json').write_text(json.dumps(info,indent=2,ensure_ascii=False))
 for path in d.iterdir():
  if path.suffix in ['.blend','.glb','.png']:
   data=path.read_bytes()
   if any(x in data for x in [b'/workspace/',b'/home/agent/',b'/tmp/',b'file://']):raise RuntimeError('Private path marker in '+path.name)
 shutil.copytree(d,out)
print('PASSED',out.name)
