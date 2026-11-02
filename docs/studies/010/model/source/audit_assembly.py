"""010 independent finite ray/coordinate fit probes; not engineering certification."""
import bpy,json,sys,argparse,hashlib,datetime
from pathlib import Path
from mathutils import Vector
VERSION='010-assembly-1.0'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def measure(model,info_path):
 bpy.ops.wm.open_mainfile(filepath=str(Path(model).resolve()));info=json.loads(Path(info_path).read_text());c=info['config'];H=c['rail_height'];T=c['thickness'];C=c['clearance'];D=c['depth'];L=c['length'];N=c['dividers'];rows=[];fails=[];bottoms=[];shifts={p['name']:p.get('floor_alignment_m',0) for p in info.get('parts',[])};aligned=all('floor_alignment_m'in p for p in info.get('parts',[]))
 def fail(code,**detail):fails.append({'code':code,**detail})
 def ray(ob,o,d):
  ok,p,n,i=ob.ray_cast(Vector(o),Vector(d),distance=2)
  if not ok:raise ValueError('missing probe surface '+ob.name)
  return p
 def width(ob,o,axis):
  a=[0,0,0];a[axis]=1;b=[-v for v in a];return ray(ob,o,a)[axis]-ray(ob,o,b)[axis]
 for ob in bpy.data.objects:
  if ob.type!='MESH':continue
  zmin=min(v.co.z for v in ob.data.vertices)
  bottoms.append({'object':ob.name,'actual_zmin_m':zmin,'nominal_profile_bottom_z_m':0,'deviation_m':zmin,'studio_ground_z_m':-.0002,'ground_clearance_m':zmin+.0002})
  if aligned and abs(zmin)>2e-7:fail('ground_alignment',object=ob.name,zmin_m=zmin,tolerance_m=2e-7)
  if zmin<=-.0002:fail('studio_ground_intersection',object=ob.name,zmin_m=zmin,ground_z_m=-.0002)
 for i in range(N):
  x=-L/2+L*(i+1)/(N+1);div=bpy.data.objects['Divider '+str(i+1)]
  for j,y in enumerate([-D/2,D/2]):
   rail=bpy.data.objects['Rail '+str(j+1)];r={'rail':rail.name,'divider':div.name}
   try:
    r['rail_slot_width_m']=width(rail,(x,y,H*.78),0)
    r['divider_slot_width_m']=width(div,(x,y,H*.25),1)
    # Rays start inside actual solid at a safe mid-thickness section.
    r['divider_thickness_m']=width(div,(x,y,H*.80),0)
    r['rail_thickness_m']=width(rail,(x,y,H*.25),1)
    r['rail_floor_z_m']=ray(rail,(x,y,H*.78),(0,0,-1))[2]
    r['divider_roof_z_m']=ray(div,(x,y,H*.25),(0,0,1))[2]
    r['midlap_gap_m']=r['divider_roof_z_m']-r['rail_floor_z_m']
    if r['midlap_gap_m']<C-1e-6:fail('midlap_clearance_minimum',joint=[rail.name,div.name],measured=r['midlap_gap_m'],minimum=C-1e-6)
    r['lateral_clearance_x_m']=r['rail_slot_width_m']-r['divider_thickness_m'];r['lateral_clearance_y_m']=r['divider_slot_width_m']-r['rail_thickness_m']
    for axis,outer,inner,outer_z,inner_z,label in [(0,rail,div,H*.78,H*.80,'x'),(1,div,rail,H*.25,H*.25,'y')]:
     for sign in [-1,1]:
      direction=[0,0,0];direction[axis]=sign
      gap=sign*(ray(outer,(x,y,outer_z),direction)[axis]-ray(inner,(x,y,inner_z),direction)[axis]);key='one_side_clearance_'+label+str(sign)+'_m';r[key]=gap
      if abs(gap-C/2)>2e-7:fail('assembly_alignment',joint=[rail.name,div.name],metric=key,measured=gap,nominal=C/2,tolerance_m=2e-7)
    for key,target in [('rail_slot_width_m',T+C),('divider_slot_width_m',T+C),('rail_thickness_m',T),('divider_thickness_m',T),('midlap_gap_m',C+shifts.get(div.name,0)-shifts.get(rail.name,0)),('lateral_clearance_x_m',C),('lateral_clearance_y_m',C)]:
     if abs(r[key]-target)>2e-7:fail('assembly_dimension',joint=[rail.name,div.name],metric=key,measured=r[key],nominal=target,tolerance_m=2e-7)
   except Exception as e:fail('assembly_probe',joint=[rail.name,div.name],message=str(e))
   rows.append(r)
 return {'passed':not fails,'joints':rows,'bottom_measurements':bottoms,'warnings':['Bevelled final bottom is not necessarily exactly at nominal profile z=0; reported, not manufacturing tolerance.'],'failures':fails,'scope':'Finite section ray probes of actual Blender surfaces; complements full pair intersection checker, not continuous distance proof, manufacturing tolerance, load or stability validation.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--info',required=True);p.add_argument('--report',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);r=measure(a.model,a.info);r.update(checker_version=VERSION,checker_sha256=sha(__file__),model_sha256=sha(a.model),info_sha256=sha(a.info),created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());Path(a.report).write_text(json.dumps(r,indent=2));print('ASSEMBLY',r['passed']);
 if not r['passed']:raise RuntimeError('assembly rejected')
