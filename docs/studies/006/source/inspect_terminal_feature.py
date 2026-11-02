"""Same-camera ray evidence for the small bright terminal corner; no inference from image alone."""
import bpy,sys,json,math,argparse,hashlib
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--scene',required=True);p.add_argument('--info',required=True);p.add_argument('--report',required=True);p.add_argument('--diagnostic',required=True);p.add_argument('--no-render',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);bpy.ops.wm.open_mainfile(filepath=a.scene);info=json.loads(Path(a.info).read_text());s=bpy.context.scene;cam=s.camera;front=info['construction']['bends'][1]['center_yz_m'];cam.location=(.36,front[0]-.32,.15);target=Vector((.06,front[0],.024));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.17;s.render.resolution_x=s.render.resolution_y=560;s.render.resolution_percentage=100;bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();basis=cam.matrix_world.to_3x3();right=basis@Vector((1,0,0));up=basis@Vector((0,1,0));direction=basis@Vector((0,0,-1));hits=[];counts={}
# Pixel ROI selected from the actually viewed 560px contact-detail image.
for y in range(319,342):
 for x in range(279,304):
  origin=cam.location+right*((x+.5)/560-.5)*.17+up*(.5-(y+.5)/560)*.17;hit,point,normal,index,ob,matrix=s.ray_cast(deps,origin,direction,distance=10)
  if hit and ob.name.startswith('FOLIO'):
   n=info['construction']['cross_section_vertices'];station=index//n;role='terminal end cap' if index==len(ob.data.polygons)-2 else ('rear end cap' if index==len(ob.data.polygons)-1 else 'swept face, station '+str(station));counts[role]=counts.get(role,0)+1;hits.append({'pixel':[x,y],'polygon':index,'role':role,'point_m':list(point),'geometric_normal':list(normal)})
body=next(o for o in bpy.data.objects if o.name.startswith('FOLIO') and o.type=='MESH');bm=body.data;n=info['construction']['cross_section_vertices'];caps=[]
for idx in [len(bm.polygons)-2,len(bm.polygons)-1]:caps.append({'polygon':idx,'vertex_count':len(bm.polygons[idx].vertices),'normal':list(bm.polygons[idx].normal)})
report={'variant':info['variant'],'image_basis':'review/after-contact.png at 560 x 560; same recipe camera reconstructed from the final scene','scene_sha256':hashlib.sha256(Path(a.scene).read_bytes()).hexdigest(),'selected_roi_xyxy':[279,319,304,342],'hit_count':len(hits),'selected_bright_pixel':next((q for q in hits if q['pixel']==[290,332]),None),'polygon_roles':counts,'end_caps':caps,'interpretation':'The ROI contains the foreground rounded terminal corner (stations 0-8 and end cap), plus the tray-to-back bend behind it (stations 80-94). The selected bright pixel [290,332] hits the real terminal corner at station 4, not an extra component. A same-geometry diffuse/cap-colour diagnostic removes the concentrated silver highlight while preserving the rounded silhouette. This supports a specular/corner-normal explanation, not a claim of dynamic z-fighting verification. Whole-mesh topology/envelope/coplanar gates are separate evidence.','geometry_limits':'4 mm in-plane terminal corner and 0.65 mm section micro-round are real mesh. Terminal end-cap edge in thickness direction is not an all-direction fillet.','hits':hits}
Path(a.report).write_text(json.dumps(report,indent=2));
if a.no_render:print('TERMINAL_ROI',counts);sys.exit(0)
# Geometry diagnostic: original shape, diffuse body; two terminal cap polygons in orange.
def mat(name,color):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=0;p.inputs['Roughness'].default_value=.8;return m
body.data.materials.clear();body.data.materials.append(mat('Diagnostic body',(.17,.30,.39)));body.data.materials.append(mat('Diagnostic cap',(.8,.19,.045)))
for f in bm.polygons:f.material_index=1 if len(f.vertices)>4 else 0
s.cycles.samples=96;s.render.filepath=str(Path(a.diagnostic).resolve());bpy.ops.render.render(write_still=True);print('TERMINAL_ROI',counts)
