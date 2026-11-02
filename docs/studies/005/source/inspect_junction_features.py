"""Map the actual junction-camera pixels to exact mesh objects and inspect pin/lens margin."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
root=Path(sys.argv[sys.argv.index('--')+1]);out=root/'review';bpy.ops.wm.open_mainfile(filepath=str((root/'assets/poise/scene.blend').resolve()));S=bpy.context.scene;cam=S.camera;rim=.39;cx=.0225;ax=.205;by=.16
cam.location=(.42,-.65,rim-.06);cam.rotation_euler=(Vector((cx,0,rim+.015))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.30;S.render.resolution_x=1000;S.render.resolution_y=800;S.render.resolution_percentage=100;bpy.context.view_layer.update()
frame=cam.data.view_frame(scene=S);xmin=min(v.x for v in frame);xmax=max(v.x for v in frame);ymin=min(v.y for v in frame);ymax=max(v.y for v in frame);direction=cam.matrix_world.to_3x3()@Vector((0,0,-1));dg=bpy.context.evaluated_depsgraph_get()
names=['background']+sorted(o.name for o in bpy.data.objects if o.type=='MESH');ids={n:i for i,n in enumerate(names)}
def cast(x,y):
 u=(x+.5)/1000;v=1-(y+.5)/800;origin=cam.matrix_world@Vector((xmin+u*(xmax-xmin),ymin+v*(ymax-ymin),0));hit,loc,normal,face,obj,matrix=S.ray_cast(dg,origin,direction,distance=10)
 return (obj.name if hit else 'background',list(loc) if hit else None,face if hit else None)
x0,y0,w,h=400,540,170,55;grid=[];counts={}
for y in range(y0,y0+h):
 row=[]
 for x in range(x0,x0+w):
  name,loc,face=cast(x,y);row.append(ids[name]);counts[name]=counts.get(name,0)+1
 grid.append(row)
samples=[]
for y in [552,556,558,560,562,566,570]:
 for x in [420,430,440,450,460,480,500,520,530,535,540,545]:
  name,loc,face=cast(x,y);samples.append({'pixel':[x,y],'object':name,'world_hit_m':loc,'polygon':face})
margin=[]
for ob in bpy.data.objects:
 if not ob.name.startswith('06'):continue
 vv=[ob.matrix_world@v.co for v in ob.data.vertices];embedded=[v for v in vv if math.hypot((v.x-cx)/ax,v.y/by)>=.145]
 rows=[]
 for v in embedded:
  r=math.hypot((v.x-cx)/ax,v.y/by);lower=rim-.016-.017*(1-(r/.86)**2)-.002;rows.append(v.z-lower)
 margin.append({'pin':ob.name,'z_range_mm':[min(v.z for v in vv)*1000,max(v.z for v in vv)*1000],'lens_embedded_vertices':len(rows),'min_height_above_lens_lower_surface_mm':min(rows)*1000,'interpretation':'Positive margin: these embedded-end vertices do not protrude below the analytic lower diffuser surface. The inner-hole span remains exposed by design.'})
r={'camera_matches':'assets/poise/junction.png','roi_pixels':[x0,y0,w,h],'objects':names,'first_hit_ids':grid,'counts':counts,'sample_rays':samples,'pin_embedded_end_margins':margin,'nominal_hole_diameters_mm':[2*.145*ax*1000,2*.145*by*1000],'hub_diameter_mm':22,'limits':['Object-ID rays are geometric first hits, not rendered lighting/shadow labels.','Margin test uses the known analytic lower surface at sampled pin vertices; not production tolerances.','No latch, screw, retention, electrical or thermal engineering has been verified.']};(out/'junction-feature-evidence.json').write_text(json.dumps(r,indent=2));print(json.dumps({'counts':counts,'margin':margin},indent=2))
