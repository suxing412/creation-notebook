"""Evidence layout only: labelled thumbnails of actual CPU renders; originals are retained."""
import argparse,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--assets-root',default='assets');p.add_argument('--output',required=True);a=p.parse_args();font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',13);sheet=Image.new('RGB',(1200,930),'#e8e7df');d=ImageDraw.Draw(sheet)
for col,name in enumerate(['veil','horizon','fold']):
 folder=ROOT/a.assets_root/name;info=json.loads((folder/'model-info.json').read_text());config=info['config'];d.text((col*400+20,16),name.upper()+' / '+str(info['construction']['hole_count'])+' through-holes',fill='#263837',font=font);d.text((col*400+20,45),f"developed {config['width']*1000:g} x {config['height']*1000:g} mm / {config['curve_angle_degrees']} deg",fill='#485b58',font=small)
 for row,view in enumerate(['beauty','hole-detail']):
  im=Image.open(folder/(view+'.png')).convert('RGB');im=im.resize((400,400),Image.Resampling.LANCZOS);sheet.paste(im,(col*400,80+row*420));d.text((col*400+12,482+row*420),view+' / actual CPU render',fill='#263837',font=small)
sheet.save(ROOT/a.output,compress_level=9)
