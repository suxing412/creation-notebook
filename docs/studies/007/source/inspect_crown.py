"""Read the candidate's true side-view silhouette ROI; render crop, no geometry edits."""
import bpy,sys,json,argparse,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=argparse.ArgumentParser();p.add_argument('--scene',required=True);p.add_argument('--output',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(a.output);out.mkdir(parents=True,exist_ok=True);bpy.ops.wm.open_mainfile(filepath=a.scene);s=bpy.context.scene;ob=next(o for o in s.objects if o.type=='MESH' and o.name.startswith('ORISON'));me=ob.data;me.calc_loop_triangles();tris=[tuple(t.vertices) for t in me.loop_triangles];world=[ob.matrix_world@v.co for v in me.vertices];tree=BVHTree.FromPolygons(world,tris,all_triangles=True);cam=s.camera;cam.location=(1,0,.205);cam.rotation_euler=(Vector((0,0,.205))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.50;R=cam.rotation_euler.to_matrix();hits=[]
for py in range(130,166,2):
 for px in range(284,313):
  origin=cam.location+R@Vector(((px+.5-320)/640*.5,(320-py-.5)/640*.5,0));direction=R@Vector((0,0,-1));loc,n,idx,dist=tree.ray_cast(origin,direction)
  if loc is not None:
   hits.append({'pixel':[px,py],'world':list(loc),'triangle':idx,'vertex_indices':list(tris[idx]),'stations':sorted(set(i//36 for i in tris[idx]))});break
report={'source_scene':Path(a.scene).parent.name,'original_side_camera':{'location':[1,0,.205],'target':[0,0,.205],'ortho_scale':.5,'resolution':[640,640]},'roi_pixels':{'x':[284,312],'y':[130,164]},'first_surface_hits_by_row':hits,'seam_station':0,'interpretation':'Actual geometry ray hits; station indices refer to modulo sweep, seam at 319/0. Silhouette cusp is not by itself a topology defect.'};(out/'crown-ray-report.json').write_text(json.dumps(report,indent=2));target=(0,.012,.335);cam.location=(1,target[1],target[2]);cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.13;s.render.resolution_x=800;s.render.resolution_y=800;s.cycles.samples=128;s.render.filepath=str((out/'crown-detail.png').resolve());bpy.ops.render.render(write_still=True)
