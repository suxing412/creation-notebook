# -*- coding: utf-8 -*-
# LY-006: human-readable views of the registry -> registry/ownership-by-seat.csv, registry/ports.csv,
# preview/partition-plans.png (PIL plan drawings of measured/C-partition zones; not a render).
# Usage (from LY-006/): python -I source/render_tables.py .
import json, os, sys, csv, math
W6 = sys.argv[1]; J = lambda *p: os.path.join(W6, *p)
load = lambda p: json.load(open(p, encoding='utf-8'))
S = load(J('registry/seats.json'))['seats']; P = load(J('registry/ports.json'))['ports']
Zd = load(J('registry/zones.json')); Z = Zd['zones']; O = load(J('registry/ownership.json'))['ownership']

with open(J('registry/ownership-by-seat.csv'), 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['seat', 'title', 'type', 'site', 'siteOwner', 'role', 'frames', 'writeZones', 'cutZones', 'cityNodes', 'sourceObjects modify/replace',
                'sourceObjects keep (count)', 'groundPieces', 'cuts', 'cards (proposal owner)', 'components fixed', 'components moving', 'components state/removable',
                'ports produced', 'ports consumed'])
    for sid, t in S.items():
        comps = t['components']
        w.writerow([sid, t['title'], t['type'], t['site'], t['siteOwner'], t['role'], ' | '.join(t['frames']),
                    len(t['writeZones']) if not t['claimProtocol'] else 'claim protocol (no frozen zone)', len(t['cutZones']), ' '.join(t['ownsCityNodes']),
                    ' '.join(x.split(':', 1)[1] if x.count(':') else x for x in t['ownsSourceObjects']['modify/replace']), t['ownsSourceObjects']['keep (assembly steward)'],
                    ' '.join(t['ownsGroundPieces']), ' '.join(t['ownsCuts']), ' '.join(t['ownsCards']),
                    ' '.join(c['id'] for c in comps if c['class'].startswith('fixed')), ' '.join(c['id'] for c in comps if c['class'] == 'moving'),
                    ' '.join(f"{c['id']}({c['class']})" for c in comps if c['class'] not in ('fixed', 'moving', 'fixed-closed', 'fixed-open')),
                    ' '.join(t['produces']), ' '.join(t['consumes'])])
with open(J('registry/ports.csv'), 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['portId', 'version', 'kind', 'producer', 'steward', 'status', 'frame', 'local xyz', 'world xyz', 'consumers'])
    for pid, p in sorted(P.items()):
        w.writerow([pid, p['version'], p['kind'], p['producer'], p.get('steward'), p['status'], p['frames']['local'] if isinstance(p.get('frames'), dict) else '',
                    '' if not p.get('local') else ' '.join(f'{v:.4f}' for v in p['local']['position']),
                    '' if not p.get('world') else ' '.join(f'{v:.4f}' for v in p['world']['position']), ' '.join(p['consumers'])])

from PIL import Image, ImageDraw, ImageFont
def font(sz):
    for f in ('C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/simhei.ttf', 'C:/Windows/Fonts/arial.ttf'):
        if os.path.exists(f): return ImageFont.truetype(f, sz)
    return ImageFont.load_default()
F14, F18, F24 = font(14), font(18), font(24)
PAL = ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f', '#edc948', '#b07aa1', '#ff9da7', '#9c755f', '#bab0ac']
def panel(title, frame, seats, xr, zr, size=(820, 620), side=False):
    img = Image.new('RGB', size, 'white'); d = ImageDraw.Draw(img)
    d.text((12, 8), title, fill='black', font=F18)
    m = 40; W, H = size[0] - 2 * m, size[1] - 2 * m - 60
    sc = min(W / (xr[1] - xr[0]), H / (zr[1] - zr[0]))
    def T(x, z): return (m + (x - xr[0]) * sc, 40 + (z - zr[0]) * sc)
    col = {s: PAL[i % len(PAL)] for i, s in enumerate(seats)}
    zs = sorted([q for q in Z if q['box']], key=lambda q: -((q['box'][1][0] - q['box'][0][0]) * ((q['box'][1][1] - q['box'][0][1]) if side else (q['box'][1][2] - q['box'][0][2]))))
    for z in zs:
        if z['frame'] != frame or z['seat'] not in seats or not z['box']: continue
        (x0, y0, z0), (x1, y1, z1) = z['box']
        if side: a, b = T(x0, -y1), T(x1, -y0)
        else: a, b = T(x0, z0), T(x1, z1)
        if z['class'] == 'cut': d.rectangle([a, b], outline='black', width=2)
        else: d.rectangle([a, b], fill=col[z['seat']], outline='white')
    y = size[1] - 52; x = 12
    for s in seats:
        d.rectangle([x, y, x + 14, y + 14], fill=col[s]); d.text((x + 18, y - 2), s, fill='black', font=F14); x += 92
        if x > size[0] - 90: x = 12; y += 20
    d.text((size[0] - 330, 10), 'plan: +X right, +Z down (south)' if not side else 'elevation: +X right, +Y up', fill='#555', font=F14)
    return img
pk = panel('开阳 K-v1 局部帧 · 平面（写入区，C 分区）', 'local:kaiyang-K-v1', ['LY-011', 'LY-012', 'LY-013', 'LY-014', 'LY-015', 'LY-085'], (-17, 17), (-12, 14))
pke = panel('开阳 K-v1 局部帧 · 立面 x-y（011 承托 / 012 门 / 013 楼板 / 014 端间）', 'local:kaiyang-K-v1', ['LY-011', 'LY-012', 'LY-013', 'LY-014', 'LY-015'], (-17, 17), (-10, 1), side=True)
pc = panel('示范院候选 C02-010（A2 局部帧）· 平面', 'court:C02-010', ['LY-041', 'LY-042', 'LY-043', 'LY-044', 'LY-045', 'LY-046', 'LY-047', 'LY-048', 'LY-049'], (-10, 10), (-13, 13))
pm = panel('市肆局部帧（世界 − (214.286, 0, −1959.184)）· 平面', 'local:market-site', ['LY-021', 'LY-022', 'LY-023', 'LY-024', 'LY-025', 'LY-026', 'LY-027', 'LY-028'], (-31, 31), (-23, 23))
out = Image.new('RGB', (1640, 1240), 'white')
out.paste(pk, (0, 0)); out.paste(pke, (820, 0)); out.paste(pc, (0, 620)); out.paste(pm, (820, 620))
ImageDraw.Draw(out).text((12, 1222), 'LY-006 · PIL drawing of registry/zones.json boxes (not a render); black outline = cut zone. Boxes are C-partition write ranges, not designs.', fill='#333', font=F14)
os.makedirs(J('preview'), exist_ok=True)
out.save(J('preview/partition-plans.png'))
print('ok')
