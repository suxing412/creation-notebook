"""Contact-sheet layout from real renders only; no visual content generated or retouched."""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import argparse,json
p=argparse.ArgumentParser();p.add_argument('--candidate',action='store_true');a=p.parse_args();root=Path(__file__).resolve().parents[1]
if a.candidate:
 folders={json.loads((p/'model-info.json').read_text())['variant']:p for p in (root/'assets').glob('.vesper-staging-*') if (p/'model-info.json').exists()};views=['beauty'];dest='candidate-contact-sheet.png'
else:folders={n:root/'assets'/n for n in ['hush','poise','reach']};views=['beauty','front','side','top','junction','base-junction'];dest='contact-sheet.png'
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',24);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17);w=450;h=500;head=75
canvas=Image.new('RGB',(w*3,head+(h+35)*len(views)),(239,235,227));draw=ImageDraw.Draw(canvas)
for i,name in enumerate(['hush','poise','reach']):
 draw.text((i*w+22,18),name.upper()+' / 005',fill=(50,42,34),font=font)
 for j,view in enumerate(views):
  im=Image.open(folders[name]/(view+'.png')).convert('RGB');im.thumbnail((w,h));x=i*w+(w-im.width)//2;y=head+j*(h+35);canvas.paste(im,(x,y));draw.text((i*w+18,y+h+5),view+' | actual CPU Cycles',fill=(68,58,47),font=small)
canvas.save(root/'review'/dest)
