"""Reproduce 006's first short-oblique-triangle coplanar miss from source, no saved bad binary needed.
All generated baseline/probe/old-checker artifacts live under work/gate-coplanar-quantization.
Runs old threshold, current threshold and +1 micrometre control; each has a dedicated assertion.
"""
import argparse,json,subprocess,sys,hashlib,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE_CONFIG={'name':'quantization-base','seed':0,'recipe_version':'1.0.0','width':.25,'height':.19,'display_angle':65,'rear_angle':62,'tray_depth':.05,'foot_depth':.032,'lip_height':.026,'bend_radius':.008,'thickness':.003}
TARGET_TRIANGLE=298

def plane(q):
 u=[q[1][i]-q[0][i] for i in range(3)];v=[q[2][i]-q[0][i] for i in range(3)];n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];ln=math.sqrt(sum(x*x for x in n));n=[x/ln for x in n];return n,sum(n[i]*q[0][i] for i in range(3))
def maker(out):
 import bpy
 from mathutils import Vector
 bpy.ops.wm.open_mainfile(filepath=str(out/'base/model.blend'));ob=next(o for o in bpy.data.objects if o.type=='MESH');me=ob.data;me.calc_loop_triangles();tri=me.loop_triangles[TARGET_TRIANGLE];p=[me.vertices[i].co.copy() for i in tri.vertices];norm=(p[1]-p[0]).cross(p[2]-p[0]).normalized();short=min((p[(i+1)%3]-p[i]).length for i in range(3));width=max(q.x for q in p)-min(q.x for q in p)
 assert .1<abs(norm.z)<.9 and width>.2 and .0001<short<.0003,'Expected original narrow oblique triangle not present; do not silently choose a different case'
 center=sum(p,Vector())/3;inset=[center+(q-center)*.55 for q in p];v=[tuple(q.co) for q in me.vertices]+[tuple(q) for q in inset];faces=[tuple(f.vertices) for f in me.polygons]+[tuple(range(len(me.vertices),len(me.vertices)+3))];new=bpy.data.meshes.new('Short oblique quantization probe');new.from_pydata(v,[],faces);new.update();new.materials.append(me.materials[0]);ob.data=new;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'oblique-inset.blend'))
 original=[tuple(q) for q in p];stored=[tuple(new.vertices[i].co) for i in range(len(v)-3,len(v))];n,d=plane(original);nn,dd=plane(stored);cos=abs(sum(n[i]*nn[i] for i in range(3)));forward=max(abs(sum(n[i]*q[i] for i in range(3))-d) for q in stored);reverse=max(abs(sum(nn[i]*q[i] for i in range(3))-dd) for q in original)
 metrics={'target_loop_triangle':TARGET_TRIANGLE,'source_triangle_indices':list(tri.vertices),'source_points_m':original,'stored_inset_points_m':stored,'inset_fraction':.55,'shortest_source_edge_m':short,'source_width_m':width,'float64_unit_normal_dot':cos,'source_plane_to_inset_max_distance_m':forward,'inset_plane_to_source_max_distance_m':reverse,'quantization':'Coordinates stored as Blender float32; plane arithmetic subsequently uses Python float64.'};(out/'probe-metrics.json').write_text(json.dumps(metrics,indent=2))
 direct=Vector(nn)
 for i in range(len(v)-3,len(v)):new.vertices[i].co+=direct*1e-6
 new.update();bpy.ops.wm.save_as_mainfile(filepath=str(out/'offset-control.blend'))

def run(cmd,log):
 r=subprocess.run(list(map(str,cmd)),capture_output=True,text=True);log.write_text(r.stdout+r.stderr);return r

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',default=str(ROOT/'work/gate-coplanar-quantization'));p.add_argument('--make',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else None);out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=True)
 if a.make:maker(out);return
 config=out/'input.json';config.write_text(json.dumps(BASE_CONFIG,indent=2));blender=['blender','-b','-t','3','--python-exit-code','1','--python']
 run(blender+[ROOT/'source/generate.py','--','--config',config,'--output',out/'base','--revision','0','--geometry-only'],out/'generate.log').check_returncode()
 run(blender+[Path(__file__).resolve(),'--','--make','--output',out],out/'make.log').check_returncode()
 current=(ROOT/'source/check.py').read_text();old=current.replace('<1-1e-7:continue','<1-1e-10:continue').replace('plane_tol=5e-8','plane_tol=1e-8').replace("'coplanar_normal_cosine':1-1e-7","'coplanar_normal_cosine':1-1e-10").replace("'coplanar_plane_distance_m':5e-8","'coplanar_plane_distance_m':1e-8")
 old=old.replace("  if max(abs(sum(y[4][k]*q[k] for k in range(3))-y[5]) for q in x[3])>plane_tol:continue\n",'')
 # Working snapshot imports the real recipe without writing beside the public checker.
 old=old.replace("sys.path.insert(0,str(Path(__file__).resolve().parent));import recipe", "sys.path.insert(0,"+repr(str(ROOT/'source'))+");import recipe")
 assert old!=current and '<1-1e-10:continue' in old
 old_path=out/'old-threshold-check.py';old_path.write_text(old);rows=[]
 for label,checker,model,expect in [('old-threshold',old_path,out/'oblique-inset.blend',False),('current-threshold',ROOT/'source/check.py',out/'oblique-inset.blend',True),('one-micrometre-control',ROOT/'source/check.py',out/'offset-control.blend',False)]:
  report=out/(label+'-validation.json');r=run(blender+[checker,'--','--model',model,'--info',out/'base/model-info.json','--report',report],out/(label+'.log'));j=json.loads(report.read_text());hit=bool(j['coplanar_positive_area_overlaps']);rows.append({'case':label,'overall_rejected':r.returncode!=0 and j['passed'] is False,'coplanar_detection_expected':expect,'coplanar_detection_actual':hit,'coplanar_count':len(j['coplanar_positive_area_overlaps']),'nonadjacent_bvh_count':len(j['nonadjacent_self_intersection_candidates']),'matched':hit==expect,'thresholds':j['thresholds'],'model_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'checker_sha256':hashlib.sha256(checker.read_bytes()).hexdigest(),'report':str(report.relative_to(ROOT))})
 metrics=json.loads((out/'probe-metrics.json').read_text());summary={'passed':all(x['overall_rejected'] and x['matched'] for x in rows),'probe':metrics,'cases':rows,'generation':{'config':BASE_CONFIG,'revision':0,'source_triangle':TARGET_TRIANGLE,'inset':.55},'meaning':'Old checker still rejects overall through other defects, but misses the dedicated coplanar field. Current checker must detect that field; a +1 um control must not. No old saved binary is required.'};(ROOT/'review/gate-coplanar-quantization-reproduction.json').write_text(json.dumps(summary,indent=2));print('QUANTIZATION REPRODUCTION',summary['passed'],metrics['float64_unit_normal_dot']);raise SystemExit(0 if summary['passed'] else 1)
if __name__=='__main__':main()
