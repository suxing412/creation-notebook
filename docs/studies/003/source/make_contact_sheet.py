from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
R=Path(__file__).resolve().parents[1];A=R/'dist/assets'
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
F=lambda n:ImageFont.truetype(font,n)
im=Image.new('RGB',(1800,780),'#11191d');d=ImageDraw.Draw(im)
d.text((60,37),'UMBRA / THREE APERTURE STATES',font=F(30),fill='#e1e1d7')
d.text((60,84),'BLENDER OFFLINE RENDERS  /  SAME CAMERA + LIGHTING',font=F(16),fill='#a4afb3')
for i,(name,title,angle) in enumerate([('closed','01  /  CONTRACTED','0.0'),('mid','02  /  INTERMEDIATE','27.5'),('open','03  /  EXPANDED','55.0')]):
 x=60+i*580;pic=Image.open(A/('state-'+name+'.png')).convert('RGB');pic=pic.resize((520,520),Image.Resampling.LANCZOS);im.paste(pic,(x,134));d.text((x,677),title,font=F(22),fill='#d8c5a3');d.text((x,714),'CONTROL ANGLE  '+angle+' deg',font=F(15),fill='#a4afb3')
d.text((60,754),'Conceptual independent blades. Not a calibrated optical or manufacturing model.',font=F(14),fill='#a4afb3')
im.save(A/'contact-sheet.png')
