"""Finite sample set, not maximum travel. Each sample retains actual native/GLB/CPU front."""
import subprocess,sys
from pathlib import Path
src=Path(__file__).resolve().parent;root=src.parent
for variant in ['hinge','reach','poise']:
 for name,angles in [('folded','[100,-125,20]'),('extended','[55,-70,-25]')]:
  subprocess.run(['blender','-b','-t','4','--python-exit-code','1','--python',str(src/'generate.py'),'--','--config',str(root/'configs'/f'{variant}.json'),'--output',str(root/'assets'/variant/'poses'/name),'--angles',angles,'--views','front'],check=True)
