"""Read saved scenes, not the generator's intended settings."""
import bpy,json,sys
from pathlib import Path
root=Path(sys.argv[sys.argv.index('--')+1]);output=Path(sys.argv[sys.argv.index('--')+2]);rows=[]
for name in ['hush','poise','reach']:
 bpy.ops.wm.open_mainfile(filepath=str((root/name/'scene.blend').resolve()));s=bpy.context.scene
 materials=[]
 for m in bpy.data.materials:
  if not m.name.startswith('Vesper'):continue
  p=m.node_tree.nodes.get('Principled BSDF');materials.append({'name':m.name,'base_color_linear':list(p.inputs['Base Color'].default_value),'metallic':p.inputs['Metallic'].default_value,'roughness':p.inputs['Roughness'].default_value,'emission_strength':p.inputs['Emission Strength'].default_value})
 lights=[{'name':o.name,'location':list(o.location),'energy':o.data.energy,'color':list(o.data.color),'size':o.data.size} for o in bpy.data.objects if o.type=='LIGHT']
 row={'variant':name,'engine':s.render.engine,'device':s.cycles.device,'samples':s.cycles.samples,'seed':s.cycles.seed,'denoise':s.cycles.use_denoising,'view_transform':s.view_settings.view_transform,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'resolution':[s.render.resolution_x,s.render.resolution_y],'camera_position':list(s.camera.location),'camera_rotation':list(s.camera.rotation_euler),'ortho_scale':s.camera.data.ortho_scale,'materials':sorted(materials,key=lambda x:x['name']),'lights':sorted(lights,key=lambda x:x['name']),'external_images':[i.filepath for i in bpy.data.images if i.source=='FILE' and i.filepath]};rows.append(row)
canonical=lambda r:{k:v for k,v in r.items() if k!='variant'}
passed=all(canonical(r)==canonical(rows[0]) for r in rows) and all(not r['external_images'] for r in rows)
output.write_text(json.dumps({'passed':passed,'same_saved_studio_and_materials':passed,'scenes':rows},indent=2));assert passed
