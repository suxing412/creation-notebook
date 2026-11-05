# -*- coding: utf-8 -*-
"""LY-007 预览拼图 + 她的原件/复刻件同机位像素差。输入 tmp/r/*.png（mq/render.py，Blender Workbench，CPU 渲染）。
用法: python -I sheets.py <LY-007 目录>
输出: preview/*.png、qa/render-diff.json
"""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W = sys.argv[1]
R = os.path.join(W, 'tmp', 'r'); P = os.path.join(W, 'preview'); os.makedirs(P, exist_ok=True)
try:
    F = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 22); FS = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 16)
except OSError:
    F = FS = ImageFont.load_default()
TW, TH = 500, 375
NOTE = 'CPU 渲染：Blender 5.2.1 Workbench（mq/render.py），不是浏览器/GPU 结果'


def tile(name):
    p = os.path.join(R, name + '.png')
    return Image.open(p).convert('RGB').resize((TW, TH), Image.LANCZOS) if os.path.exists(p) else Image.new('RGB', (TW, TH), (200, 60, 60))


def sheet(out, title, rows, cols, cell):
    """rows: [(行标签, 行键)]；cols: [(列标签, 列键)]；cell(rk, ck) -> 图名。"""
    lw, th = 150, 70
    im = Image.new('RGB', (lw + TW * len(cols), th + 30 + TH * len(rows)), (250, 250, 248))
    d = ImageDraw.Draw(im)
    d.text((10, 8), title, fill=(20, 20, 20), font=F); d.text((10, 40), NOTE, fill=(90, 90, 90), font=FS)
    for ci, (cl, _) in enumerate(cols):
        d.text((lw + ci * TW + 10, th + 4), cl, fill=(30, 30, 30), font=FS)
    for ri, (rl, rk) in enumerate(rows):
        d.text((10, th + 30 + ri * TH + TH // 2 - 12), rl, fill=(30, 30, 30), font=F)
        for ci, (_, ck) in enumerate(cols):
            im.paste(tile(cell(rk, ck)), (lw + ci * TW, th + 30 + ri * TH))
    im.save(os.path.join(P, out), optimize=True)
    return out


made = []
made.append(sheet('refsphere-tiers.png', 'LY-007 基准球与 1 m 标定块：earth / path / paper__stone / timber / tile（左→右）',
                  [('LOD0', 0), ('LOD1', 1), ('LOD2', 2)], [('iso', 'iso'), ('front', 'front'), ('close', 'close'), ('wire', 'wire')],
                  lambda r, c: f'lyref-LOD{r}-{c}'))
for m in ('S84', 'G10'):
    made.append(sheet(f'sample-{m}-orig-vs-replica.png', f'{m} 样件：她的原件（bce3211 提交字节） vs round2 复刻件（本席位 models/samples）',
                      [('LOD0', 0), ('LOD1', 1), ('LOD2', 2)],
                      [('原件 iso', ('orig', 'iso')), ('复刻 iso', ('sample', 'iso')), ('原件 close', ('orig', 'close')), ('复刻 close', ('sample', 'close'))],
                      lambda r, c: f'{c[0]}-{m}-LOD{r}-{c[1]}'))
    made.append(sheet(f'sample-{m}-tiers-wire.png', f'{m} 复刻件三档：线框与侧立面（档间轮廓/细节差异）',
                      [('LOD0', 0), ('LOD1', 1), ('LOD2', 2)], [('wire', 'wire'), ('wireclose', 'wireclose'), ('side', 'side')],
                      lambda r, c: f'sample-{m}-LOD{r}-{c}'))

diff = {}
for m in ('S84', 'G10'):
    for lod in (0, 1, 2):
        for v in ('iso', 'side', 'close'):
            a = os.path.join(R, f'orig-{m}-LOD{lod}-{v}.png'); b = os.path.join(R, f'sample-{m}-LOD{lod}-{v}.png')
            A = np.asarray(Image.open(a).convert('RGB'), np.int16); B = np.asarray(Image.open(b).convert('RGB'), np.int16)
            dd = np.abs(A - B).max(2)
            diff[f'{m}-LOD{lod}-{v}'] = dict(pct_px_diff_gt30=round(float((dd > 30).mean() * 100), 4),
                                             pct_px_diff_gt0=round(float((dd > 0).mean() * 100), 4), max=int(dd.max()))
json.dump(dict(note=NOTE, renders_dir='tmp/r (不入交付白名单，可用 render.py 重出)', diff=diff), open(os.path.join(W, 'qa', 'render-diff.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(made); print(json.dumps(diff))
