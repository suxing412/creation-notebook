from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
r=Path(__file__).resolve().parents[1];im=Image.new('RGB',(1080,1155),'#e8e5dd');d=ImageDraw.Draw(im);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
for y,v in enumerate(['hinge','reach','poise']):
 for x,p in enumerate(['default','folded','extended']):
  f=r/'assets'/v/('front.png' if p=='default' else f'poses/{p}/front.png');img=Image.open(f);img.load();img.thumbnail((360,360));im.paste(img,(x*360,y*385));d.text((x*360+12,y*385+363),v.upper()+' / '+p,fill='#172b2e',font=font)
im.save(r/'review/final-pose-contact-sheet.png')
im=Image.new('RGB',(1440,510),'#e8e5dd');d=ImageDraw.Draw(im)
for x,v in enumerate(['hinge','reach','poise']):
 img=Image.open(r/'assets'/v/'beauty.png');img.load();img.thumbnail((480,480));im.paste(img,(x*480,0));d.text((x*480+12,486),v.upper(),fill='#172b2e',font=font)
im.save(r/'review/final-variant-contact-sheet.png')
