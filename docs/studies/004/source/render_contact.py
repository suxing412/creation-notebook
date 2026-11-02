"""Actual Blender closeup of the arrival block / rock interface."""
import bpy,sys
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.open_mainfile(filepath=args[0])
def light(loc,power,size):
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(Vector((-.65,-4.7,.4))-o.location).to_track_quat('-Z','Y').to_euler()
light((-4,-8,6),900,5);light((4,-2,5),600,5)
bpy.ops.object.camera_add(location=(2,-8,2));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=2.6;cam.rotation_euler=(Vector((-.67,-4.8,.4))-cam.location).to_track_quat('-Z','Y').to_euler();s=bpy.context.scene;s.camera=cam;s.render.engine='CYCLES';s.cycles.samples=80;s.cycles.use_denoising=False;s.render.resolution_x=1000;s.render.resolution_y=800;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX';s.render.filepath=args[1];bpy.ops.render.render(write_still=True)
