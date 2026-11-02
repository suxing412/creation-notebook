"""Finite +Z extraction probes, actual mesh BVH. Not continuous collision proof."""
import bpy,json,sys,argparse,datetime,itertools
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent));from audit_native import sha,point_inside
OFFSETS=[0,.0003,.0006,.0012,.003,.006,.012,.024,.048,.055,.08,.12]
def measure(model):
 bpy.ops.wm.open_mainfile(filepath=str(Path(model).resolve()));data={};rows=[]
 for ob in bpy.data.objects:
  if ob.type!='MESH':continue
  ob.data.calc_loop_triangles();data[ob.name]=([ob.matrix_world@v.co for v in ob.data.vertices],[tuple(t.vertices)for t in ob.data.loop_triangles])
 for moving in sorted(n for n in data if n.startswith('Divider ')):
  for z in OFFSETS:
   av,at=data[moving];av=[v+Vector((0,0,z))for v in av];ab=BVHTree.FromPolygons(av,at,all_triangles=True,epsilon=0);fail=[]
   for name,(bv,bt)in data.items():
    if name==moving:continue
    bb=BVHTree.FromPolygons(bv,bt,all_triangles=True,epsilon=0);hits=ab.overlap(bb)
    if hits:fail.append({'object':name,'surface_candidate_count':len(hits)})
    else:
     statuses=[point_inside(tuple(av[0]),bb,bv),point_inside(tuple(bv[0]),ab,av)]
     if statuses!=[False,False]:fail.append({'object':name,'containment_or_uncertain':statuses})
   rows.append({'moving':moving,'z_offset_m':z,'passed':not fail,'failures':fail})
 return {'passed':all(r['passed']for r in rows),'sample_offsets_m':OFFSETS,'samples':rows,'scope':'Each divider moves alone along +Z, other parts fixed. Finite mesh BVH and ray-parity containment at listed offsets, not continuous swept volume proof, motion mechanics or stability validation. Static independent positive-coplanar scan is in audit_native, not repeated here.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--report',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);r=measure(a.model);r.update(checker_sha256=sha(__file__),native_helper_sha256=sha(Path(__file__).with_name('audit_native.py')),model_sha256=sha(a.model),created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());Path(a.report).write_text(json.dumps(r,indent=2));print('MOTION',r['passed']);
 if not r['passed']:raise RuntimeError('motion sample rejected')
