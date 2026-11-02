"""Public entry point. Stage -> validate -> render -> atomic publish. Never overwrite."""
import argparse, pathlib, tempfile, subprocess, shutil, json, sys
p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True);p.add_argument('--threads',type=int,default=4);a=p.parse_args()
root=pathlib.Path(__file__).resolve().parent;out=pathlib.Path(a.output).resolve()
if out.exists(): raise SystemExit('Refusing to overwrite existing output; choose a new directory')
if not 1<=a.threads<=32: raise SystemExit('threads must be 1..32')
# Blender Python exceptions need explicit nonzero exit semantics.
with tempfile.TemporaryDirectory(prefix='wing-stage-') as tmp:
 stage=pathlib.Path(tmp)/'asset'
 command=['blender','-b','-t',str(a.threads),'--python-exit-code','1','--python',str(root/'generate.py'),'--','--config',str(pathlib.Path(a.config).resolve()),'--output',str(stage)]
 subprocess.run(command+['--geometry-only'],check=True)
 subprocess.run(['blender','-b','-t','2','--python-exit-code','1','--python',str(root/'check.py'),'--','--model',str(stage/'model.blend'),'--report',str(stage/'validation.json')],check=True)
 subprocess.run(command,check=True)
 # Validate the final files again; do not promote an unchecked re-generation.
 subprocess.run(['blender','-b','-t','2','--python-exit-code','1','--python',str(root/'check.py'),'--','--model',str(stage/'model.blend'),'--report',str(stage/'validation.json')],check=True)
 report=json.loads((stage/'validation.json').read_text())
 if not report['passed']:raise RuntimeError('Final artifact QA rejected')
 info=json.loads((stage/'model-info.json').read_text())
 info.update(nonManifoldEdges=sum(report['nonManifoldEdges'].values()),validationStatus='static-QA-passed',validationReport='validation.json')
 (stage/'model-info.json').write_text(json.dumps(info,indent=2))
 # Strip render metadata before publication. Pixel data are unchanged.
 from PIL import Image
 for f in stage.glob('*.png'):
  im=Image.open(f);clean=Image.new(im.mode,im.size);clean.paste(im);clean.save(f)
 out.parent.mkdir(parents=True,exist_ok=True)
 pending=pathlib.Path(tempfile.mkdtemp(prefix='.wing-ready-',dir=out.parent))
 try:
  shutil.copytree(stage,pending,dirs_exist_ok=True);pending.rename(out)
 finally:
  if pending.exists():shutil.rmtree(pending)
 print(json.dumps({'publishedDirectory':out.name,'qualityGate':True}))
