"""Make an internal visual-QA contact sheet from the six actual views; does not alter originals."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16);views=['beauty','front','side','top','rear','hole-detail'];out=Image.new('RGB',(960,2070),'#e8e7df');draw=ImageDraw.Draw(out)
for col,variant in enumerate(['veil','horizon','fold']):
 for row,view in enumerate(views):
  im=Image.open(ROOT/'assets'/variant/(view+'.png')).convert('RGB').resize((320,320),Image.Resampling.LANCZOS);y=row*345;out.paste(im,(col*320,y));draw.text((col*320+10,y+323),variant+' / '+view,font=font,fill='#263837')
(ROOT/'work').mkdir(exist_ok=True);out.save(ROOT/'work/visual-check-sheet.png',compress_level=9)
