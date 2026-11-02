"""Measured native matched-vertex normal offsets and actual ground spans, not all-point thickness proof."""
import bpy,sys,json,argparse,math
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--info',required=True);p.add_argument('--report',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);bpy.ops.wm.open_mainfile(filepath=a.model);info=json.loads(Path(a.info).read_text());ob=next(o for o in bpy.data.objects if o.type=='MESH');v=[ob.matrix_world@q.co for q in ob.data.vertices];cons=info['construction'];n=cons['cross_section_vertices'];stations=cons['stations'];target=info['config']['thickness'];rows=[];mid=[];ground=[]
for i,s in enumerate(stations):
 normal=Vector((0,*s['normal']));values=[]
 for top,bottom in [(5,18),(6,17)]:
  d=v[i*n+top]-v[i*n+bottom];values.append({'length_mm':d.length*1000,'normal_projection_mm':d.dot(normal)*1000,'tangential_residual_mm':(d-normal*d.dot(normal)).length*1000})
 rows.append({'station':i,'segment':s['segment'],'pairs':values})
 if abs(s['point'][1]-target/2)<1e-9 and s['tangent'][0]>.999999 and abs(s['tangent'][1])<1e-9:ground.append({'station':i,'y_m':v[i*n+18].y,'bottom_z_m':min(v[i*n+k].z for k in range(n)),'segment':s['segment']})
 if i+1<len(stations):
  top=(v[i*n+5]+v[(i+1)*n+5])/2;bottom=(v[i*n+18]+v[(i+1)*n+18])/2;mid.append((top-bottom).length*1000)
lengths=[p['length_mm'] for r in rows for p in r['pairs']];groups=[]
for row in ground:
 if not groups or row['station']>groups[-1][-1]['station']+1:groups.append([])
 groups[-1].append(row)
# The broad top/bottom strips are flat across X; these actual vertex YZ values define x=0 section edges.
section=[(v[i*n+5].y,v[i*n+5].z) for i in range(len(stations))]+[(v[i*n+18].y,v[i*n+18].z) for i in reversed(range(len(stations)))];cut_z=max(q[1] for q in section)*.4;crossings=[]
for aa,bb in zip(section,section[1:]+section[:1]):
 if (aa[1]<=cut_z<bb[1]) or (bb[1]<=cut_z<aa[1]):crossings.append(aa[0]+(bb[0]-aa[0])*(cut_z-aa[1])/(bb[1]-aa[1]))
crossings=sorted(crossings);opening={'plane':'x=0 central side section','z_m':cut_z,'surface_crossings_y_m':crossings,'open_gap_mm':(crossings[2]-crossings[1])*1000 if len(crossings)==4 else None,'scope':'One horizontal cut through actual piecewise-linear mesh section; open to the sides, not a sealed cavity or global minimum clearance.'}
report={'variant':info['variant'],'nominal_normal_offset_thickness_mm':target*1000,'matched_vertex_pair_count':len(lengths),'matched_vertex_thickness_mm':[min(lengths),max(lengths)],'longitudinal_edge_midpoint_pair_count':len(mid),'longitudinal_edge_midpoint_thickness_mm':[min(mid),max(mid)],'max_tangential_residual_mm':max(p['tangential_residual_mm'] for r in rows for p in r['pairs']),'negative_space_opening':opening,'ground_spans':[{'station_count':len(g),'y_m':[min(r['y_m'] for r in g),max(r['y_m'] for r in g)],'sampled_bottom_z_m':[min(r['bottom_z_m'] for r in g),max(r['bottom_z_m'] for r in g)]} for g in groups],'bend_arc_chord_max_angle_deg':2,'nominal_max_chord_midpoint_thickness_deficit_mm':target*1000*(1-math.cos(math.radians(1))),'terminal_plan_corner_radius_mm':cons['terminal_plan_corner_radius_mm'],'cap_edge_note':'Terminal outline has 4 mm in-plane rounded corners. Cap-to-face thickness edge remains a hard boundary; no claim of all-direction edge fillet.','limits':['Matched vertex pairs and longitudinal edge midpoints are finite discrete samples, not a global minimum wall-thickness certificate.','Dimensions and contacts are digital geometry; no forming allowance, tolerance, load, friction, or ergonomics validation.'],'passed':min(lengths)>target*1000-.0001 and max(lengths)<target*1000+.0001 and len(groups)==2,'stations':rows}
Path(a.report).write_text(json.dumps(report,indent=2));print('SECTIONS',report['passed'],report['matched_vertex_thickness_mm'],report['longitudinal_edge_midpoint_thickness_mm'])
if not report['passed']:raise RuntimeError('section samples failed')
