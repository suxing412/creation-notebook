"""Build a labelled contact sheet of preview images. Usage: contact.py root out.png cols thumbw label=path ..."""
import sys, os
from PIL import Image, ImageDraw, ImageFont

root, out, cols, tw = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
items = [a.split('=', 1) for a in sys.argv[5:]]
th = int(tw * 0.75)
try:
    font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 18)
except Exception:
    font = ImageFont.load_default()
rows = (len(items) + cols - 1) // cols
sheet = Image.new('RGB', (cols * tw, rows * (th + 28)), (255, 255, 255))
d = ImageDraw.Draw(sheet)
for k, (label, rel) in enumerate(items):
    x, y = (k % cols) * tw, (k // cols) * (th + 28)
    p = os.path.join(root, rel)
    try:
        im = Image.open(p).convert('RGB')
        info = f'{im.width}x{im.height}'
        im.thumbnail((tw - 6, th - 6))
        sheet.paste(im, (x + (tw - im.width) // 2, y + 28 + (th - im.height) // 2))
    except Exception as e:
        info = 'MISSING'
    d.text((x + 4, y + 4), f'{label}  {info}', fill=(200, 0, 0) if info == 'MISSING' else (0, 0, 0), font=font)
sheet.save(out)
print(out, sheet.size)
