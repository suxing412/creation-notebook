import collections,json,hashlib,math
from pathlib import Path
import recipe
root=Path(__file__).resolve().parents[1];rows=[]
for length in sorted(set([.08,.095,.20,.205,.21,.235,.245,.28,.285,.29]+[.20+.09*i/64 for i in range(65)])):
 for radius,thick in [(recipe.PLATE_R,recipe.THICK),(.008,.008)]:
  v,f=recipe.plate(length,r=radius,thickness=thick);edges=collections.Counter(tuple(sorted((a,b))) for face in f for a,b in zip(face,face[1:]+face[:1]));unique_faces=collections.Counter(tuple(sorted(face)) for face in f);good=all(n==2 for n in edges.values()) and all(n==1 for n in unique_faces.values()) and all(len(set(face))==len(face) for face in f);rows.append({'length_m':length,'radius_m':radius,'thickness_m':thick,'vertices':len(v),'quads':len(f),'nonmanifold_edges':sum(n!=2 for n in edges.values()),'duplicate_faces':sum(n-1 for n in unique_faces.values()),'passed':good})
r={'passed':all(q['passed'] for q in rows),'finite_sample_count':len(rows),'records':rows,'scope':'Recipe indexed topology on discrete lengths, before Blender bevel. Not continuous-domain or post-bevel geometry proof.','recipe_sha256':hashlib.sha256(Path(recipe.__file__).read_bytes()).hexdigest(),'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};(root/'review/plate-sampling-tests.json').write_text(json.dumps(r,indent=2));print(r['passed'],len(rows));assert r['passed']
