import json,copy,sys,hashlib
from pathlib import Path
import recipe
root=Path(__file__).resolve().parents[1];base=json.loads((root/'configs/slot.json').read_text());rows=[]
for k,v in [('length',.249),('length',.481),('depth',.119),('depth',.231),('divider_height',.099),('divider_height',.191),('thickness',.0059),('thickness',.0121),('rail_height',.049),('rail_height',.081),('clearance',.00039),('clearance',.00121),('dividers',2),('dividers',7),('dividers',3.0),('dividers',True),('length',float('nan')),('depth',float('inf')),('thickness',True),('name','unknown')]:
 c=copy.deepcopy(base);c[k]=v
 try:recipe.validate(c);ok=False
 except ValueError:ok=True
 rows.append({'case':k+'='+str(v),'rejected':ok})
for label,fn in [('extra',lambda c:c.update(extra=1)),('missing',lambda c:c.pop('depth')),('shoulder',lambda c:c.update(divider_height=.1,rail_height=.08)),('ligament',lambda c:c.update(length=.25,dividers=6,thickness=.012))]:
 c=copy.deepcopy(base);fn(c)
 try:recipe.validate(c);ok=False
 except ValueError:ok=True
 rows.append({'case':label,'rejected':ok})
r={'passed':all(x['rejected']for x in rows),'checks':rows,'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'recipe_sha256':hashlib.sha256((root/'source/recipe.py').read_bytes()).hexdigest(),'scope':'Input rejection only, not geometric envelope proof'}
Path(sys.argv[1]).write_text(json.dumps(r,indent=2));assert r['passed']
