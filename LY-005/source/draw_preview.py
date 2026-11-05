# LY-005 preview: (A) Yong gate ports in local frame with world axes, (B) measured elevation ladder.
# PIL vector drawing of measured numbers; not a render. python -I draw_preview.py <ports.json> <frames.json> <elev.json> <out.png>
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbio

ports = json.load(open(sys.argv[1], encoding='utf-8'))['ports']
frames = json.load(open(sys.argv[2], encoding='utf-8'))
elev = json.load(open(sys.argv[3], encoding='utf-8'))
out = sys.argv[4]
F = 'C:/Windows/Fonts/msyh.ttc'
f14 = ImageFont.truetype(F, 14); f12 = ImageFont.truetype(F, 12); f18 = ImageFont.truetype(F, 18)
W, H = 1600, 820
im = Image.new('RGB', (W, H), '#f7f4ec'); dr = ImageDraw.Draw(im)
INK, MUTE, ACC, ACC2 = '#2b2a27', '#7a756b', '#b5462f', '#2f6db5'

# ---- panel A
dr.text((30, 18), 'A  雍门端口：本地坐标（GLB 场景帧，单位米）→ 世界坐标（luoyang-local-schematic-v01）', font=f18, fill=INK)
ox, oy, s = 360, 360, 17.0  # local x -> right, local z -> down (plan, looking from +Y)
P = lambda x, z: (ox + x * s, oy + z * s)


def footprint(path, ex=()):
    g = glbio.read_glb(path)
    pts = np.concatenate([glbio.apply(w, pos) for ni, n, w, pos, tri, anc in glbio.mesh_items(g) if not any(a in ex for a in anc)])
    return pts


LAB = 'D:/GitHub/creation-notebook-lab/'
body = footprint(LAB + frames['assets']['yong-gate-near']['files']['far']['path'])
apron = footprint(LAB + frames['assets']['yong-gate-apron']['files']['far']['path'])
amn, amx = apron.min(0), apron.max(0)
dr.rectangle([P(amn[0], amn[2]), P(amx[0], amx[2])], outline=MUTE, width=1, fill='#ece4d2')
# piers from y≈0 body vertices
low = body[np.abs(body[:, 1]) < 1e-6]
for x0, x1 in ((-11.3, -8.6), (-5.2, -2.4), (2.4, 5.2), (8.6, 11.3)):
    sel = low[(low[:, 0] >= x0 - .2) & (low[:, 0] <= x1 + .2)]
    if len(sel):
        dr.rectangle([P(sel[:, 0].min(), sel[:, 2].min()), P(sel[:, 0].max(), sel[:, 2].max())], fill='#cbb48a', outline=INK)
dr.text(P(amn[0] + .3, amn[2] + .2), '接口地坪 apron（本地 y=0 → 世界 0.17）', font=f12, fill=MUTE)
short = {}
rows = []
for p in ports:
    if not p['portId'].startswith('yong-gate:'):
        continue
    x, y, z = p['local']['position']
    cx, cy = P(x, z)
    col = ACC if p['kind'] == 'threshold' else (ACC2 if p['kind'] == 'ground' else '#5a8a3a')
    dr.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=col)
    lab = p['portId'].replace('yong-gate:', '')
    code = str(len(rows) + 1)
    dr.text((cx + 7, cy - 18 if z < 0 else cy + 4), code, font=f14, fill=col)
    w = p['world']['position']
    rows.append((code, lab, p['kind'], (x, y, z), w, col))
ty = 572
dr.text((30, ty), '编号  端口ID                              类型        本地 (x, y, z)              世界 (x, y, z)', font=f12, fill=MUTE)
for i, (code, lab, kind, l, w, col) in enumerate(rows):
    yy = ty + 16 + i * 15
    dr.text((30, yy), code, font=f12, fill=col)
    dr.text((62, yy), lab, font=f12, fill=INK)
    dr.text((300, yy), kind, font=f12, fill=INK)
    dr.text((380, yy), f'({l[0]:7.3f}, {l[1]:.3f}, {l[2]:7.3f})', font=f12, fill=INK)
    dr.text((580, yy), f'({w[0]:9.4f}, {w[1]:.4f}, {w[2]:11.4f})', font=f12, fill=INK)
# axes
ax0 = (720, 120)
dr.line([ax0, (ax0[0] + 60, ax0[1])], fill=INK, width=2); dr.multiline_text((ax0[0] + 64, ax0[1] - 8), '本地 +X\n= 世界北（-Z）', font=f12, fill=INK)
dr.line([ax0, (ax0[0], ax0[1] + 60)], fill=INK, width=2); dr.multiline_text((ax0[0] + 6, ax0[1] + 64), '本地 +Z = 世界东（+X）\n城内方向', font=f12, fill=INK)
dr.text((30, 770), '节点矩阵：yaw = 90.666°（绕 +Y），平移 (-16.016, 0.170, -1397.773)，缩放 1（偏差 ≤2.6e-9）。门体在门道内无地面几何，门道行走面取接口地坪顶面。', font=f12, fill=MUTE)
dr.text((30, 790), '外侧 outer = 本地 -Z = 世界西（城外）。图为平面示意，按实测顶点与端口数值绘制，不是渲染图。', font=f12, fill=MUTE)

# ---- panel B: elevation ladder
bx0, by0, bh = 1030, 80, 640
dr.text((1000, 18), 'B  实测高程（世界 Y，米；全部是 C 工程零点，不是考古高程）', font=f18, fill=INK)
ymin, ymax = -0.5, 10.6
Y = lambda v: by0 + bh - (v - ymin) / (ymax - ymin) * bh
dr.line([(bx0, Y(ymin)), (bx0, Y(ymax))], fill=INK, width=1)
for t in range(0, 11, 2):
    dr.line([(bx0 - 5, Y(t)), (bx0, Y(t))], fill=INK); dr.text((bx0 - 30, Y(t) - 8), str(t), font=f12, fill=INK)
cy = elev['courtyards']
items = [
    (10.40, '雍门门体顶 10.40 / 广阳门 direct 门体顶 10.30'),
    (6.20, '城垣顶 6.20 = 广阳门体底 6.20 = 雍门接墙顶 6.20'),
    (0.21, '道路/缝合地面顶 0.21'),
    (0.20, f'地块/院落地面 0.20；44 院基底 0.20（基底-地面 {min(c["gapMin_m"] for c in cy)*1000:.3f} ~ {max(c["gapMax_m"] for c in cy)*1000:.3f} mm）'),
    (0.17, '城垣底 0.17 = 雍门门体底/门道 0.17'),
    (0.00, '工程零点 Y=0；市肆/仓储最低 0.00'),
    (-0.03, '雍门接口地坪底 -0.03'),
]
zoom_y = lambda v: by0 + bh - 40 - (v + 0.05) / 0.3 * 200  # inset for 0..0.25
for v, t in items:
    if v > 1:
        yy = Y(v)
        dr.line([(bx0, yy), (bx0 + 40, yy)], fill=ACC, width=2); dr.text((bx0 + 46, yy - 9), t, font=f14, fill=INK)
# inset for near-zero band
ix0, iy_top, iy_bot = bx0 + 60, by0 + bh - 260, by0 + bh - 20
dr.rectangle([ix0 - 10, iy_top - 10, ix0 + 520, iy_bot + 10], outline=MUTE)
dr.text((ix0, iy_top - 30), '近地面放大（-0.05 ~ 0.25 m）', font=f12, fill=MUTE)
Z = lambda v: iy_bot - (v + 0.05) / 0.30 * (iy_bot - iy_top)
for v, t in items:
    if v <= 1:
        yy = Z(v)
        off = {0.21: -16, 0.20: 2}.get(v, -8)
        dr.line([(ix0, yy), (ix0 + 40, yy)], fill=ACC2, width=2); dr.text((ix0 + 46, yy + off), f'{t}', font=f12, fill=INK)
im.save(out)
print('saved', out)
