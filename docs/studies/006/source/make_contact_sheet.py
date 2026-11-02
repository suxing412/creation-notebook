from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import shutil,json,math
R=Path(__file__).resolve().parents[1];font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
def sheet(paths,labels,out,columns=3,size=360):
 rows=math.ceil(len(paths)/columns);im=Image.new('RGB',(columns*size,rows*(size+40)),(239,243,245));d=ImageDraw.Draw(im)
 for i,(p,label) in enumerate(zip(paths,labels)):
  tile=Image.open(p).convert('RGB');tile.thumbnail((size,size));x=(i%columns)*size;y=(i//columns)*(size+40);im.paste(tile,(x+(size-tile.width)//2,y+(size-tile.height)//2));d.text((x+14,y+size+9),label,font=small,fill=(24,46,61))
 im.save(out)
for a,b in [('work/before-comparison/beauty.png','review/before.png'),('work/refined-draft/beauty.png','review/after.png'),('work/before-comparison/top.png','review/before-top.png'),('work/refined-draft/top.png','review/after-top.png'),('work/before-comparison/contact-detail.png','review/before-contact.png'),('work/refined-draft/contact-detail.png','review/after-contact.png')]:
 if (R/a).exists():shutil.copyfile(R/a,R/b)
sheet([R/'review/before.png',R/'review/after.png',R/'review/before-top.png',R/'review/after-top.png',R/'review/before-contact.png',R/'review/after-contact.png'],['Before / 48 max samples','After / 48 max samples','Before / actual top view','After / actual top view','Before / terminal corner','After / 4 mm in-plane rounding'],R/'review/before-after.png',2,560)
variants=['atlas','folio','spire'];views=['beauty','front','side','top','rear','bend-detail','contact-detail']
if all((R/'assets'/n/'beauty.png').exists() for n in variants):sheet([R/'assets'/n/(v+'.png') for v in views for n in variants],[n.upper()+' / '+v for v in views for n in variants],R/'review/contact-sheet.png',3,440)
