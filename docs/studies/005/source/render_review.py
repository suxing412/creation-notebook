"""Re-render an archived scene for fair before/after comparisons or socket inspection."""
import bpy,sys,argparse
from mathutils import Vector
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--scene',required=True);p.add_argument('--model');p.add_argument('--output',required=True);p.add_argument('--view',choices=['beauty','junction','socket'],required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);bpy.ops.wm.open_mainfile(filepath=a.scene)
if a.model:
 for ob in list(bpy.data.objects):
  if ob.type=='MESH' and ob.name[:2] in ['01','02','03','04','05','06']:bpy.data.objects.remove(ob,do_unlink=True)
 with bpy.data.libraries.load(str(Path(a.model).resolve()),link=False) as (available,loaded):loaded.objects=available.objects
 for ob in loaded.objects:
  if ob:bpy.context.scene.collection.objects.link(ob)
S=bpy.context.scene;cam=S.camera
rim=.39;cx=.0225
if a.view=='beauty':loc,target,scale,w,h,samples=(.9,-1.4,.83),(0,0,.29),.86,900,1000,1024
elif a.view=='junction':loc,target,scale,w,h,samples=(.42,-.65,rim-.06),(cx,0,rim+.015),.30,1000,800,256
else:
 loc,target,scale,w,h,samples=(.12,-.20,.60),(cx,0,.37),.13,1000,800,256
 bpy.data.objects['01 Shade - closed mineral shell'].hide_render=True
cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;S.cycles.samples=samples;S.cycles.use_denoising=False;S.cycles.device='CPU';S.view_settings.exposure=-.4;S.render.resolution_x=w;S.render.resolution_y=h;S.render.resolution_percentage=100;S.render.filepath=str(Path(a.output).resolve());bpy.ops.render.render(write_still=True)
