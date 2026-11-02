"""Read a saved studio scene; add an optional editorial wide image without altering native model or square views."""
import bpy,sys,json,argparse,time,hashlib
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--asset',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);d=Path(a.asset).resolve();info=json.loads((d/'model-info.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(d/'scene.blend'));s=bpy.context.scene;cam=s.camera;start=time.time()
# Blender's horizontal sensor fit defines ortho_scale as image width. At 1.65:1,
# 1.12m gives about 0.679m vertical framing. Same camera for all variants, no bbox fit.
view={'location':[.80,-1.25,.685],'target':[0,.03,.245],'ortho_scale':1.12,'resolution':[1584,960],'sensor_fit':'HORIZONTAL','purpose':'Editorial wide view only; not a replacement for the square comparison camera.'}
cam.location=view['location'];cam.rotation_euler=(Vector(view['target'])-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=view['ortho_scale'];cam.data.sensor_fit='HORIZONTAL';s.render.resolution_x=1584;s.render.resolution_y=960;s.render.resolution_percentage=100;s.render.filepath=str(d/'beauty-wide.png');bpy.ops.render.render(write_still=True)
info['studio']['editorial_wide']=view;info['editorial_wide_elapsed_seconds']=round(time.time()-start,3);(d/'model-info.json').write_text(json.dumps(info,ensure_ascii=False,separators=(',',':')))
print('WIDE',info['variant'],info['editorial_wide_elapsed_seconds'])
