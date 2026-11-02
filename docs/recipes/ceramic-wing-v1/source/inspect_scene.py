import bpy,sys,json
from pathlib import Path
root=Path(sys.argv[sys.argv.index('--')+1]);results=[]
for name in ['baseline','broad','swept']:
 bpy.ops.wm.open_mainfile(filepath=str(root/'assets'/name/'scene.blend'))
 s=bpy.context.scene
 meshes=[o for o in bpy.data.objects if o.type=='MESH' and o.name!='Studio floor'];pts=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
 results.append({'name':name,'bounds':[[min(p[i] for p in pts),max(p[i] for p in pts)] for i in range(3)],'viewTransform':s.view_settings.view_transform,'display':s.display_settings.display_device,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'seed':s.cycles.seed,'denoise':s.cycles.use_denoising,'savedView':'side','materials':{m.name:{'baseColor':list(m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value),'metallic':m.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value,'roughness':m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value} for m in bpy.data.materials if m.use_nodes and m.node_tree.nodes.get('Principled BSDF')},'lights':{o.name:{'energy':o.data.energy,'size':o.data.size,'position':list(o.location)} for o in bpy.data.objects if o.type=='LIGHT'}})
(root/'review/scene-audit.json').write_text(json.dumps(results,indent=2))
