"""Correct fixed front camera across all specimens; native geometry/GLB remain unchanged."""
import bpy,sys,json,argparse,hashlib
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--asset',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);d=Path(a.asset);info=json.loads((d/'model-info.json').read_text());spec={'location':[.20,-1.4,.26],'target':[.20,0,.26],'ortho_scale':.82};old=info['studio']['views']['front']
if old==spec:print('already current');sys.exit(0)
geo={f:hashlib.sha256((d/f).read_bytes()).hexdigest() for f in ['model.blend','model.glb']};bpy.ops.wm.open_mainfile(filepath=str((d/'scene.blend').resolve()));s=bpy.context.scene;cam=s.camera;cam.location=spec['location'];cam.rotation_euler=(Vector(spec['target'])-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=spec['ortho_scale'];s.render.filepath=str((d/'front.png').resolve());bpy.ops.render.render(write_still=True);info['studio']['views']['front']=spec;info['front_camera_revision']={'reason':'Fixed frame widened for all finite extended samples; same camera retained across variants and poses','old':old,'new':spec};(d/'model-info.json').write_text(json.dumps(info,indent=2,ensure_ascii=False));assert all(hashlib.sha256((d/f).read_bytes()).hexdigest()==h for f,h in geo.items())
