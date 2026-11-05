"""Region status map (top-down, CPU, Pillow).  Reads lab files read-only.
Footprints are real triangles of the GLBs the current city entry loads, transformed by
the manifest matrices, with the renderer's excludeNodes removed.  Hidden trials are drawn
from their package placement records (rotated local bounds).  Unplaced models are listed.

usage: python -I draw_map.py <lab_root> <ledger_json> <city_dump_json> <out_png>
"""
import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import glbinfo  # noqa: E402

LAB = Path(sys.argv[1]); DOCS = LAB / 'docs'; CITY = DOCS / 'cities/luoyang'
L = json.load(open(sys.argv[2], encoding='utf8'))
M = json.load(open(sys.argv[3], encoding='utf8'))
OUT = Path(sys.argv[4])
FONT = 'C:/Windows/Fonts/msyh.ttc'
f_s, f_m, f_l, f_xl = (ImageFont.truetype(FONT, s) for s in (15, 19, 24, 34))

COL = {
    'init': (46, 110, 74), 'chap': (52, 98, 170), 'ground': (150, 176, 205), 'trial': (222, 120, 20),
    'paper': (246, 241, 230), 'ink': (40, 40, 38), 'grid': (222, 214, 198), 'muted': (120, 116, 108),
}

assets = {a['id']: a for a in M['assets']}
state_of = {n['nodeId']: n['state'] for n in L['cityNodes']}


def node_matrix(n):
    if n.get('matrix'):
        return np.array(n['matrix'], float).reshape(4, 4).T
    T = np.eye(4)
    T[:3, 3] = n.get('position') or [0, 0, 0]
    return T


def url_rel(u):
    from urllib.parse import unquote, urlparse
    return Path(unquote(urlparse(u).path).lstrip('/'))


tri_cache = {}


def tris_for(asset_id):
    if asset_id not in tri_cache:
        a = assets[asset_id]
        p = url_rel(a['url'])
        _, boxes, tris = glbinfo.summarize(p, want_tris=True, exclude=a.get('excludeNodes') or [])
        tri_cache[asset_id] = (tris, boxes)
    return tri_cache[asset_id]


# gather world-space 2D triangles per node: diagram (x east, y north = -z)
layers = []  # (kind, nodeId, Nx3x2 array)
for n in M['nodes']:
    st = state_of[n['id']]
    kind = 'ground' if n['chapter'] == 'terrain' else ('init' if '首屏' in st else 'chap')
    tris, boxes = tris_for(n['asset'])
    W = node_matrix(n)
    if tris is None or len(tris) == 0:
        pts = np.concatenate([b[1] for b in boxes]) if boxes else np.zeros((0, 3))
        continue
    P = tris.reshape(-1, 3)
    P = (np.c_[P, np.ones(len(P))] @ W.T)[:, :3]
    D = np.stack([P[:, 0], -P[:, 2]], 1).reshape(-1, 3, 2)
    H = P[:, 1].reshape(-1, 3).max(1)
    o = np.argsort(H)
    layers.append((kind, n['id'], D[o], H[o]))

# hidden trials: rotated local bounds at package placement
trials = []
north = json.load(open(CITY / 'progress-assets/north13-gates/source.json', encoding='utf8'))
for p in north['packages']:
    pl = p['placement']
    b = None
    for m in p['models']:
        b = m.get('primitiveLocalBounds') or b
    if pl.get('engineering_origin_from_existing_wall_caps'):
        ox, oy, _ = pl['engineering_origin_from_existing_wall_caps']
        r = pl['rotation_z_rad']
        mn, mx = b['min'], b['max']
        loc = [(mn[0], mn[2]), (mx[0], mn[2]), (mx[0], mx[2]), (mn[0], mx[2])]
        # city: X = ox + cos r*lx + sin r*lz ; Z = -oy - sin r*lx + cos r*lz ; diagram y = -Z
        poly = [(ox + math.cos(r) * lx + math.sin(r) * lz, oy + math.sin(r) * lx - math.cos(r) * lz) for lx, lz in loc]
        trials.append((p['package'], poly, 'gate'))
    for t in pl.get('targets', []):
        mtx = np.array(t['matrixGLTFColumnMajor'], float).reshape(4, 4).T
        lb = None
        for m in p['models']:
            if f"-{t['variant']}-LOD1" in m['file']:
                lb = m.get('primitiveLocalBounds')
        if lb is None:
            lb = {'min': [-9, 0, -12], 'max': [9, 5, 12.15]} if t['variant'] != 'TC03-2' else {'min': [0, 0, -36], 'max': [28, 5, 0.15]}
        mn, mx = lb['min'], lb['max']
        loc = [(mn[0], mn[2]), (mx[0], mn[2]), (mx[0], mx[2]), (mn[0], mx[2])]
        poly = []
        for lx, lz in loc:
            w = mtx @ np.array([lx, 0, lz, 1.0])
            poly.append((w[0], -w[2]))
        trials.append((f"{p['package']}:{t['id']}", poly, 'court'))


class View:
    def __init__(self, x0, y0, x1, y1, px, box):
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1
        self.box = box  # (left, top, right, bottom) on canvas
        self.s = min((box[2] - box[0]) / (x1 - x0), (box[3] - box[1]) / (y1 - y0))

    def P(self, x, y):
        return (self.box[0] + (x - self.x0) * self.s, self.box[3] - (y - self.y0) * self.s)


def draw_view(img, v, title, scale_m, grid=None):
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle(v.box, fill=(252, 249, 242), outline=COL['ink'], width=2)
    if grid:
        g = grid
        x = math.ceil(v.x0 / g) * g
        while x <= v.x1:
            a, _ = v.P(x, v.y0)
            d.line([(a, v.box[1]), (a, v.box[3])], fill=COL['grid'], width=1)
            x += g
        y = math.ceil(v.y0 / g) * g
        while y <= v.y1:
            _, b = v.P(v.x0, y)
            d.line([(v.box[0], b), (v.box[2], b)], fill=COL['grid'], width=1)
            y += g
    clip = Image.new('RGBA', img.size, (0, 0, 0, 0))
    cd = ImageDraw.Draw(clip, 'RGBA')
    order = {'ground': 0, 'chap': 1, 'init': 2}
    for kind, nid, D, H in sorted(layers, key=lambda t: order[t[0]]):
        xs, ys = D[..., 0], D[..., 1]
        keep = (xs.max(1) >= v.x0) & (xs.min(1) <= v.x1) & (ys.max(1) >= v.y0) & (ys.min(1) <= v.y1)
        if not keep.any():
            continue
        c = COL[kind]
        paper = (252, 249, 242)
        for t, h in zip(D[keep], H[keep]):
            pts = [v.P(x, y) for x, y in t]
            if kind == 'ground':
                cd.polygon(pts, fill=c + (90,))
            else:
                f = min(1.0, max(0.28, 0.28 + h / 6.0))  # higher parts darker: roofs read over floors
                cd.polygon(pts, fill=tuple(int(paper[i] + (c[i] - paper[i]) * f) for i in range(3)) + (255,))
    for name, poly, kind in trials:
        pts = [v.P(x, y) for x, y in poly]
        if max(p[0] for p in pts) < v.box[0] or min(p[0] for p in pts) > v.box[2]:
            continue
        if max(p[1] for p in pts) < v.box[1] or min(p[1] for p in pts) > v.box[3]:
            continue
        w = max(2, int(2 if v.s < 1 else 3))
        cd.polygon(pts, outline=COL['trial'] + (255,), width=w)
        if v.s < 1:  # make tiny trials visible at city scale
            cx = sum(p[0] for p in pts) / 4
            cy = sum(p[1] for p in pts) / 4
            cd.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], outline=COL['trial'] + (255,), width=3)
    mask = Image.new('L', img.size, 0)
    ImageDraw.Draw(mask).rectangle([v.box[0] + 1, v.box[1] + 1, v.box[2] - 1, v.box[3] - 1], fill=255)
    img.paste(clip, (0, 0), Image.composite(clip, Image.new('RGBA', img.size, (0, 0, 0, 0)), mask))
    d = ImageDraw.Draw(img, 'RGBA')
    d.text((v.box[0] + 8, v.box[1] + 6), title, fill=COL['ink'], font=f_m, stroke_width=3, stroke_fill=(252, 249, 242))
    # scale bar
    L_px = scale_m * v.s
    bx, by = v.box[0] + 10, v.box[3] - 16
    d.line([(bx, by), (bx + L_px, by)], fill=COL['ink'], width=3)
    d.text((bx + L_px + 6, by - 11), f'{scale_m} 示意米', fill=COL['ink'], font=f_s)


def label(img, v, x, y, text, dx=8, dy=-10, color=None):
    d = ImageDraw.Draw(img)
    px, py = v.P(x, y)
    d.text((px + dx, py + dy), text, fill=color or COL['ink'], font=f_s, stroke_width=3, stroke_fill=(252, 249, 242))


W_, H_ = 2600, 1900
img = Image.new('RGB', (W_, H_), COL['paper'])
d = ImageDraw.Draw(img)
d.text((40, 24), '东汉洛阳 · 当前 main 城景区域现状图（LY-001 快照）', fill=COL['ink'], font=f_xl)
d.text((40, 70), f"提交 {L['git']['head'][:12]}（{L['git']['head_date']}） · 工程示意坐标：x 向东、y=−glTF Z 向“图上北”；真实北向与地理原点未知（清单 coordinateFrame）。CPU 栅格化真实三角面，非浏览器/GPU 截图。", fill=COL['muted'], font=f_s)

main = View(-120, -120, 2760, 4040, None, (40, 110, 1260, 1860))
draw_view(img, main, '全城（当前入口 docs/cities/luoyang/index.html）', 500, grid=500)
# insets
ins = [
    (View(440, 680, 790, 1260, None, (1290, 110, 1690, 770)), '西城住宅 44 院 · 道路地面', 50, 50),
    (View(-45, 1370, 25, 1426, None, (1720, 110, 2080, 400)), '雍门（已入城）', 10, 10),
    (View(-30, 470, 30, 510, None, (2110, 110, 2560, 400)), '广阳门 direct 门体（已入城）', 10, 10),
    (View(170, 1925, 260, 1992, None, (1720, 430, 2080, 770)), '市肆 五店三摊（按章加载）', 10, 10),
    (View(2235, 3635, 2335, 3712, None, (2110, 430, 2560, 770)), '仓储 太仓候选附近（按章加载）', 10, 10),
    (View(500, 1060, 740, 1225, None, (1290, 800, 1890, 1215)), '北侧院落：隐藏试放覆盖 13 院（activation 未开）', 20, 20),
]
for v, t, sb, g in ins:
    draw_view(img, v, t, sb, grid=g)
# inset frames on main map
for v, t, sb, g in ins:
    a = main.P(v.x0, v.y1); b = main.P(v.x1, v.y0)
    d.rectangle([a[0] - 3, a[1] - 3, b[0] + 3, b[1] + 3], outline=(160, 60, 60), width=2)

# labels on main map
for name, poly, kind in trials:
    if kind == 'gate':
        cx = sum(p[0] for p in poly) / 4; cy = sum(p[1] for p in poly) / 4
        nm = {'kaiyang': '开阳门', 'pingcheng': '平城门', 'shangxi': '上西门', 'yong': '雍门', 'zhongdong': '中东门'}
        key = next(k for k in nm if k in name)
        txt = nm[key] + '（隐藏试放）' if key != 'yong' else '雍门旧试放包（已被入城版取代）'
        label(img, main, cx, cy, txt, dx=12, dy=-26 if key != 'yong' else 6, color=COL['trial'])
label(img, main, 0, 490, '广阳门（direct，已入城）', dx=14, dy=-6, color=COL['init'])
label(img, main, -16, 1398, '雍门（已入城）', dx=14, dy=-12, color=COL['init'])
label(img, main, 600, 950, '住宅 44 院', dx=40, dy=-6, color=COL['init'])
label(img, main, 214, 1960, '市肆（按章）', dx=12, dy=-14, color=COL['chap'])
label(img, main, 2286, 3673, '仓储（按章）', dx=-120, dy=8, color=COL['chap'])
label(img, main, 1200, 1300, '城内大部空白：未建，不代表无遗存', dx=0, dy=0, color=COL['muted'])

# legend + unplaced list
lx, ly = 1920, 800
d.rectangle([lx, ly, 2560, 1860], fill=(252, 249, 242), outline=COL['ink'], width=2)
y = ly + 12
d.text((lx + 14, y), '图例（状态以代码与数据为准）', fill=COL['ink'], font=f_l); y += 40
for c, t in [(COL['init'], '已入城·首屏默认加载（59 节点）'), (COL['chap'], '已入城·按章加载 initial=false（市肆2·仓储1）'),
             (COL['ground'], '已入城·按章加载：道路与地面 4 件（半透明）')]:
    d.rectangle([lx + 16, y + 4, lx + 40, y + 22], fill=c); d.text((lx + 50, y), t, fill=COL['ink'], font=f_s); y += 28
d.rectangle([lx + 16, y + 4, lx + 40, y + 22], outline=COL['trial'], width=3)
d.text((lx + 50, y), '隐藏试放：north13 8 包，activation=false/未激活', fill=COL['ink'], font=f_s); y += 28
d.text((lx + 16, y), '实体色深浅＝高度（越高越深），只为分辨屋面与地坪', fill=COL['muted'], font=f_s); y += 26
d.text((lx + 16, y), '不在图上 = 仅模型（无城市坐标/未配准）：', fill=COL['ink'], font=f_m); y += 30
research = [n for n in L['cityNodes'] if n['state'].startswith('仅模型')]
d.text((lx + 16, y), f'· 城景内独立研究视图 {len(research)} 件（cityPlacement=null）：', fill=COL['ink'], font=f_s); y += 24
names = {'research-lingtai': '灵台', 'research-taixue-A': '太学长堂A', 'research-taixue-B': '太学长堂B', 'research-mao-gate': '旄门'}
short = []
for n in research:
    k = n['nodeId']
    short.append(names.get(k) or k.replace('research-north13-', 'N13·'))
for i in range(0, len(short), 4):
    d.text((lx + 30, y), '、'.join(short[i:i + 4]), fill=COL['muted'], font=f_s); y += 22
only = [c for c in L['cards'] if c['isLuoyang'] and c['id'] != 'p-luoyang' and not any(f['sameBytesAsCityLoaded'] for f in c['files'])]
d.text((lx + 16, y + 4), f'· 资产库洛阳卡中无任何文件被城景加载的 {len(only)} 张（按卡计）：', fill=COL['ink'], font=f_s); y += 30
titles = [c['title'] for c in only]
line = ''
for t in titles:
    t2 = t[:12]
    if len(line) + len(t2) > 30:
        d.text((lx + 30, y), line, fill=COL['muted'], font=f_s); y += 21; line = ''
    line += ('、' if line else '') + t2
if line:
    d.text((lx + 30, y), line, fill=COL['muted'], font=f_s); y += 21
y += 8
for t in ['注：“已入城”只指当前入口会加载并放到城市坐标；', '不等于局部通行通过、结构安全或历史复原成立。',
          '门位/院落落位为 C/推测级设计；北宫新墙与古水系未配准。']:
    d.text((lx + 16, y), t, fill=COL['muted'], font=f_s); y += 21

img.save(OUT, optimize=True)
print('saved', OUT, img.size, 'layers', len(layers), 'trials', len(trials))
