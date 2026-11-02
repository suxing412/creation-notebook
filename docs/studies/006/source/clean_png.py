"""Remove Blender PNG text/EXIF metadata without changing a single decoded pixel."""
from pathlib import Path
from PIL import Image
import hashlib,json
R=Path(__file__).resolve().parents[1];rows=[]
for folder in ['review','assets']:
 for p in sorted((R/folder).rglob('*.png')):
  if any(part.startswith('.') for part in p.relative_to(R).parts):continue
  im=Image.open(p);before=hashlib.sha256(im.tobytes()).hexdigest();keys=sorted(im.info);im.save(p);afterim=Image.open(p);after=hashlib.sha256(afterim.tobytes()).hexdigest();assert before==after;assert not afterim.info;rows.append({'file':str(p.relative_to(R)),'decoded_pixel_sha256':after,'removed_metadata_keys':keys,'pixels_unchanged':True})
(R/'review/png-metadata-audit.json').write_text(json.dumps({'passed':True,'files':rows,'note':'All decoded pixels unchanged. Removed only PNG textual/EXIF metadata; no image retouching or denoising.'},indent=2))
f=R/'review/render-comparison.json'
if f.exists():
 d=json.loads(f.read_text())
 for row in d['comparison']:row['sha256']=hashlib.sha256((R/row['image']).read_bytes()).hexdigest()
 f.write_text(json.dumps(d,indent=2))
print('CLEANED PNG',len(rows))
