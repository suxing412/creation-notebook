"""Adversarial meshes for the QA regression suite; never publish these as assets."""
import bpy,bmesh,sys,json
from pathlib import Path
src,out=sys.argv[sys.argv.index('--')+1:];out=Path(out);out.mkdir(parents=True,exist_ok=True);info=json.loads(Path(src).with_name('model-info.json').read_text());C=info['config'];cx=C['stem_lean']/2;ax=C['shade_width']/2
# These retained-contact probes were identified by the independent QA worker.
def add_box_preserve_endpoint_rings(ob,center,half):
 me=ob.data;v=[tuple(q.co) for q in me.vertices];f=[tuple(p.vertices) for p in me.polygons];cut=20
 cube=[(center[0]+x*half[0],center[1]+y*half[1],center[2]+z*half[2]) for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
 cf=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)];remap=lambda i:i+8 if i>=cut else i
 faces=[tuple(remap(i) for i in q) for q in f]+[tuple(i+cut for i in q) for q in cf];me.clear_geometry();me.from_pydata(v[:cut]+cube+v[cut:],[],faces);me.update()
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
for case in ['duplicate-face','degenerate-face','open-boundary','unexpected-penetration','fully-contained-pin','missing-pin','self-intersection','coplanar-partial-overlap','hub-overreach','same-pair-extra-prism','allowed-hub-contained-island','reversed-base-face','oblique-coplanar-overlap']:
 bpy.ops.wm.open_mainfile(filepath=src);objects=sorted([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:o.name)
 if case=='oblique-coplanar-overlap':
  ob=objects[0];me=ob.data;me.calc_loop_triangles()
  for tri in me.loop_triangles:
   points=[me.vertices[i].co.copy() for i in tri.vertices];normal=(points[1]-points[0]).cross(points[2]-points[0]);normal.normalize()
   if normal.dot(normal)<1-1e-8:break
  center=sum(points,points[0]*0)/3;vertices=[tuple(v.co) for v in me.vertices];faces=[tuple(f.vertices) for f in me.polygons];start=len(vertices);vertices.extend(tuple(center+(q-center)*.75) for q in points);faces.append((start,start+1,start+2));me.clear_geometry();me.from_pydata(vertices,[],faces);me.update()
 elif case=='same-pair-extra-prism':
  r=.155;z=C['rim_height']-.016-.017*(1-(r/.86)**2);add_box_preserve_endpoint_rings(objects[5],(cx+ax*r,0,z),(.0007,.0007,.006))
 elif case=='allowed-hub-contained-island':
  r=.5;z=C['rim_height']+C['shade_rise']*(1-r*r)**1.55;add_box_preserve_endpoint_rings(objects[4],(cx+ax*r+C['crown_shift']*(1-r*r),0,z),(.0002,.0002,.0002))
 elif case=='reversed-base-face':objects[2].data.polygons[0].flip()
 elif case=='duplicate-face':
  ob=objects[0];me=ob.data;verts=[tuple(v.co) for v in me.vertices];faces=[tuple(f.vertices) for f in me.polygons];faces.append(faces[0]);me.clear_geometry();me.from_pydata(verts,[],faces);me.update()
 elif case=='degenerate-face':
  ob=objects[0];me=ob.data;verts=[tuple(v.co) for v in me.vertices];faces=[tuple(f.vertices) for f in me.polygons];faces.append((0,0,1));me.clear_geometry();me.from_pydata(verts,[],faces);me.update()
 elif case=='hub-overreach':objects[4].location.z+=.010
 elif case=='open-boundary':
  bm=bmesh.new();bm.from_mesh(objects[0].data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[0]],context='FACES');bm.to_mesh(objects[0].data);bm.free()
 elif case=='unexpected-penetration':objects[1].location.z-=.09;objects[1].location.x+=.06
 elif case=='fully-contained-pin':
  pin=objects[5];pts=[v.co for v in pin.data.vertices];center=sum(pts,pts[0]*0)/len(pts);pin.location=(-center.x,-center.y,.013-center.z)
 elif case=='missing-pin':objects[5].location.y+=.09
 elif case=='self-intersection':
  shade=objects[0];top=max(v.co.z for v in shade.data.vertices);peak=max(shade.data.vertices,key=lambda v:v.co.z).co
  bpy.ops.mesh.primitive_cube_add(size=.018,location=(peak.x,peak.y,top-.003));cube=bpy.context.object;bpy.ops.object.select_all(action='DESELECT');cube.select_set(True);shade.select_set(True);bpy.context.view_layer.objects.active=shade;bpy.ops.object.join()
 elif case=='coplanar-partial-overlap':
  ob=objects[2];me=ob.data;me.calc_loop_triangles();tri=max(me.loop_triangles,key=lambda t:t.center.z);q=[me.vertices[i].co.copy() for i in tri.vertices];center=sum(q,q[0]*0)/3;new=[center+(p-center)*.75 for p in q];verts=[tuple(v.co) for v in me.vertices];faces=[tuple(f.vertices) for f in me.polygons];start=len(verts);verts.extend(new);faces.append((start,start+1,start+2));me.clear_geometry();me.from_pydata(verts,[],faces);me.update()
 bpy.ops.wm.save_as_mainfile(filepath=str((out/(case+'.blend')).resolve()))
