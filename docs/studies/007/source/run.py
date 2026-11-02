"""Reproducible 007 generator: fresh destination, pre-render gate, final identity gate.
Output must be a new directory inside this study. Failed stages remain quarantined in work.
"""
import argparse,json,hashlib,subprocess,sys,uuid,time,shutil
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'source'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True);p.add_argument('--threads',type=int,default=6);p.add_argument('--samples',type=int,default=128);p.add_argument('--resolution',type=int,default=960);a=p.parse_args();out=Path(a.output).resolve();config=Path(a.config).resolve()
 if not out.is_relative_to(ROOT) or out==ROOT or out.exists():raise ValueError('Output must be a NEW child directory inside this study')
 if not 1<=a.threads<=8 or not 16<=a.samples<=512 or not 256<=a.resolution<=1600:raise ValueError('Unsupported resource budget')
 token='recipe-'+uuid.uuid4().hex[:12];stage=ROOT/'work'/token;stage.mkdir(parents=True,exist_ok=False);start=time.time()
 def blender(*extra):
  cmd=['blender','-b','-t',str(a.threads),'--python-exit-code','1','--python',str(SRC/'generate.py'),'--','--config',str(config),'--output',str(stage),'--samples',str(a.samples),'--resolution',str(a.resolution),*extra]
  subprocess.run(cmd,check=True)
 def gate(folder,label):
  subprocess.run([sys.executable,str(SRC/'run_gates.py'),'--asset',str(folder),'--label',label],check=True)
  identity=json.loads((ROOT/'review'/('gate-'+label+'-identity.json')).read_text());assert identity['passed'] and identity['input_sha256']['native']==sha(folder/'model.blend') and identity['input_sha256']['glb']==sha(folder/'model.glb')
 blender('--geometry-only');gate(stage,token+'-pre');blender()
 for image in stage.glob('*.png'):
  im=Image.open(image);pixels=sha(image);pixel_hash=hashlib.sha256(im.tobytes()).hexdigest();im.save(image);assert hashlib.sha256(Image.open(image).tobytes()).hexdigest()==pixel_hash
 for path in stage.iterdir():
  if path.suffix in ['.blend','.glb','.png'] and any(q in path.read_bytes() for q in [b'/workspace/',b'/home/agent/',b'/tmp/',b'file://']):raise RuntimeError('Private marker in '+path.name)
 info=json.loads((stage/'model-info.json').read_text());info['validation_status']='External validation.json is authoritative; see gate-identity.json for final input hashes';info['validation_report']='validation.json';(stage/'model-info.json').write_text(json.dumps(info,indent=2,ensure_ascii=False))
 out.parent.mkdir(parents=True,exist_ok=True);shutil.move(stage,out)
 try:gate(out,token+'-final')
 except Exception:
  quarantine=ROOT/'work'/(token+'-failed-final');shutil.move(out,quarantine);raise
 for key,filename in [('native','validation.json'),('glb','glb-validation.json'),('comparison','export-comparison.json'),('identity','gate-identity.json')]:shutil.copy2(ROOT/'review'/('gate-'+token+'-final-'+key+'.json'),out/filename)
 print('ORISON passed:',out.relative_to(ROOT),'elapsed_seconds',round(time.time()-start,3))
if __name__=='__main__':main()
