"""Compare actual aperture-edge chord midpoint error to the same analytic smooth target.
A finite midpoint diagnostic, not a continuous maximum or surface-Hausdorff proof."""
import bpy,sys,json,argparse,hashlib,math
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--assets',nargs='+',required=True);p.add_argument('--report',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);rows=[]
if Path(a.report).exists():raise ValueError('Use fresh report')
for folder in a.assets:
 d=Path(folder);info=json.loads((d/'model-info.json').read_text());c=info['config'];bpy.ops.wm.open_mainfile(filepath=str((d/'model.blend').resolve()));ob=next(o for o in bpy.data.objects if o.type=='MESH');v=[ob.matrix_world@q.co for q in ob.data.vertices];R=c['width']/math.radians(c['curve_angle_degrees']);t=c['thickness']/2;radius=c['edge_radius'];errors=[]
 for hole in info['construction']['holes']:
  u,z=hole['center_uv'];rx,ry=hole['radii_uv'];ring=hole['front_ring']
  for j,ia in enumerate(ring):
   ib=ring[(j+1)%len(ring)];angles=[]
   for vid in [ia,ib]:
    uu,zz,_,_=info['construction']['vertex_uvt'][vid];angles.append(math.atan2((zz-z)/(ry+radius),(uu-u)/(rx+radius)))
   while angles[1]<=angles[0]:angles[1]+=math.tau
   phi=sum(angles)/2;uu=u+(rx+radius)*math.cos(phi);zz=z+(ry+radius)*math.sin(phi);exact=Vector(((R+t)*math.sin(uu/R),R-(R+t)*math.cos(uu/R),zz));edge=v[ib]-v[ia];fraction=max(0,min(1,(exact-v[ia]).dot(edge)/edge.length_squared));errors.append((exact-(v[ia]+edge*fraction)).length)
 scale=info['studio']['views']['hole-detail']['ortho_scale'];res=960
 rows.append({'asset_label':d.name,'model_sha256':hashlib.sha256((d/'model.blend').read_bytes()).hexdigest(),'info_sha256':hashlib.sha256((d/'model-info.json').read_bytes()).hexdigest(),'points_per_hole':len(info['construction']['holes'][0]['front_ring']),'edges_evaluated':len(errors),'maximum_sampled_chord_midpoint_error_m':max(errors),'mean_sampled_chord_midpoint_error_m':sum(errors)/len(errors),'screen_scale_upper_estimate_px_at_960_detail':max(errors)*res/scale,'pixel_estimate_note':'World error divided by orthographic pixel pitch; actual projected direction may be smaller.'})
r={'passed':True,'diagnostic_only':True,'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'rows':rows,'limits':['Only the midpoint of each actual front-mouth chord is tested against the analytic target.','Does not measure max over the entire chord, full surface, manufacturing tolerance, or image/GPU aliasing.','Both geometries are actual native files. Render samples do not change this geometric diagnostic.']};Path(a.report).write_text(json.dumps(r,indent=2));print(json.dumps(rows,indent=2))
