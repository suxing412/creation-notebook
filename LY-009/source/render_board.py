"""Draw board/taskboard.v2.json as a level-by-level DAG picture (PIL; schematic, not a render).

python -I render_board.py <LY-009 dir>   ->  preview/dag-status.png
Columns = DAG level (1..15). Boxes = seats, fill = status, border = lane. Edges drawn only
between consecutive levels' explicit deps (G edges are summarised by the 'G' marker) to stay legible.
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

me = sys.argv[1]
b = json.load(open(os.path.join(me, 'board', 'taskboard.v2.json'), encoding='utf-8'))
seats = b['seats']
FILL = {'待输入': (225, 225, 225), '可开工': (190, 225, 255), '制作中': (255, 235, 160), '待验收': (255, 205, 150),
        '阻断': (240, 150, 150), '复用完成': (175, 230, 190), '交付完成': (120, 200, 140)}
LANE = {'资料契约': (60, 60, 160), '模型补件': (170, 90, 30), '复用装配': (30, 130, 120), '独立验收': (130, 40, 130),
        '唯一整合': (0, 0, 0)}


def font(sz):
    for p in [r'C:\Windows\Fonts\msyh.ttc', r'C:\Windows\Fonts\simhei.ttf', r'C:\Windows\Fonts\simsun.ttc']:
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


F, FS, FT = font(13), font(11), font(20)
levels = {}
for s in seats:
    levels.setdefault(s['level'], []).append(s)
BW, BH, GX, GY, X0, Y0 = 92, 34, 40, 8, 30, 110
maxn = max(len(v) for v in levels.values())
W = X0 * 2 + len(levels) * (BW + GX)
Hh = Y0 + maxn * (BH + GY) + 140
img = Image.new('RGB', (W, Hh), 'white')
d = ImageDraw.Draw(img)
pos = {}
for lv in sorted(levels):
    for i, s in enumerate(sorted(levels[lv], key=lambda x: x['id'])):
        x = X0 + (lv - 1) * (BW + GX)
        y = Y0 + i * (BH + GY)
        pos[s['id']] = (x, y)
for s in seats:
    x, y = pos[s['id']]
    for dep in s['depsExplicit']:
        px, py = pos[dep]
        d.line([(px + BW, py + BH // 2), (x, y + BH // 2)], fill=(185, 185, 200), width=1)
for s in seats:
    x, y = pos[s['id']]
    d.rectangle([x, y, x + BW, y + BH], fill=FILL[s['status']], outline=LANE[s['lane']], width=2)
    d.text((x + 4, y + 2), s['id'] + (' G' if s['usesG'] else ''), fill='black', font=F)
    d.text((x + 4, y + 18), s['status'] + (' *暂停区' if s['pauses'] else ''), fill=(40, 40, 40), font=FS)
for lv in sorted(levels):
    d.text((X0 + (lv - 1) * (BW + GX) + 30, Y0 - 22), f'L{lv}', fill='black', font=F)
d.text((X0, 14), f"LY-009 任务板 v2 · 依赖层级图（{b['generatedAt']}）  示意图，非渲染", fill='black', font=FT)
d.text((X0, 44), f"计数：" + '  '.join(f"{k} {v}" for k, v in b['counts'].items()) +
       f"   G 冻结：{'是' if b['G']['frozen'] else '否，缺 ' + '、'.join(b['G']['missing'])}", fill='black', font=F)
d.text((X0, 64), '线只画原文显式依赖；标 G 的席位另依赖 G 八席。*暂停区 = 有暂停区条目（不一定阻断）。', fill=(60, 60, 60), font=FS)
ly = Hh - 110
x = X0
for k, c in FILL.items():
    d.rectangle([x, ly, x + 22, ly + 16], fill=c, outline='black')
    d.text((x + 28, ly), k, fill='black', font=F)
    x += 110
x = X0
for k, c in LANE.items():
    d.rectangle([x, ly + 30, x + 22, ly + 46], fill='white', outline=c, width=3)
    d.text((x + 28, ly + 30), k, fill='black', font=F)
    x += 110
os.makedirs(os.path.join(me, 'preview'), exist_ok=True)
img.save(os.path.join(me, 'preview', 'dag-status.png'), optimize=True)
print('preview', img.size)
