from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
r=Path(__file__).resolve().parents[1]/'dist/assets'
views=[('beauty','01 / DAYLIGHT'),('front','02 / FRONT ORTHOGRAPHIC'),('side','03 / SIDE ORTHOGRAPHIC'),('top','04 / PLAN'),('rear','05 / REAR'),('entry','06 / ARCH / THRESHOLD')]
out=Image.new('RGB',(1500,1110),'#e9ede6');d=ImageDraw.Draw(out)
for i,(name,label) in enumerate(views):
 im=Image.open(r/(name+'.png')).convert('RGB');im.thumbnail((480,470));x=(i%3)*500+(500-im.width)//2;y=(i//3)*550+45+(470-im.height)//2;out.paste(im,(x,y));d.text(((i%3)*500+20,(i//3)*550+15),label,fill='#263d3d')
out.save(r/'contact-sheet.png')
