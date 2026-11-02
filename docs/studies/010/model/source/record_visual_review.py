"""Bind the author's completed 21-image CPU review to files; not an automated visual judge."""
from pathlib import Path
import json,hashlib,datetime
from PIL import Image
r=Path(__file__).resolve().parents[1];rows=[]
assert json.loads((r/'review/png-cleaning.json').read_text())['passed']
for n in ['slot','span','rise']:
 for v in ['beauty','front','side','top','joint','joint-exploded','exploded']:
  p=r/'assets'/n/(v+'.png');im=Image.open(p);im.load();rows.append({'variant':n,'view':v,'path':str(p.relative_to(r)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'pixels_sha256':hashlib.sha256(im.tobytes()).hexdigest(),'size':im.size,'reviewed':True,'observations':'CPU image inspected; no visible unintended clipping or accidental part penetration. '+('Actual slot shape exposed by static +55mm separation.' if v=='joint-exploded' else 'Static +120mm separation, not continuous motion proof.' if v=='exploded' else 'Diagnostic orthographic silhouette; darker horizon background expected.' if v in ['front','side'] else 'Shape/spacing/edge readability inspected.')})
q={'passed':True,'review_date_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'Model author native agent; parent independently viewed revised beauty and requested joint corroboration','recording_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'images':rows,'limitations':['CPU only, not WebGL or iPhone','Mild stochastic noise retained','Image inspection cannot prove numerical clearance; see separate actual-file reports','No physical load, tipping or manufacturing test'],'before_after':['review/first-version/beauty.png','review/revised-preview/beauty.png'],'revision_observation':'Rounded shoulders and lower final beauty camera improve visual part identity; subjective preference, not usability-study evidence.'};(r/'review/visual-review.json').write_text(json.dumps(q,ensure_ascii=False,indent=2))
