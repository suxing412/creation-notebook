#!/usr/bin/env python3
"""把 qa/selftest.json 与 qa/official-runs.json 画成一张对照表 preview/selftest-matrix.png（PIL，CPU 绘制，非浏览器截图）。
用法：python -I source/draw_preview.py <LY-008 目录>"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(sys.argv[1])
st = json.load(open(os.path.join(ROOT, 'qa', 'selftest.json'), encoding='utf-8'))
off = json.load(open(os.path.join(ROOT, 'qa', 'official-runs.json'), encoding='utf-8'))
FONT = 'C:/Windows/Fonts/msyh.ttc'
f = ImageFont.truetype(FONT, 15); fb = ImageFont.truetype(FONT, 17); ft = ImageFont.truetype(FONT, 22)
case2off = {r['lyCheckCase']: r for r in off['injectedComparison'] if r['lyCheckCase']}
rows = st['rows']
W, RH, TOP = 1700, 22, 120
H = TOP + RH * (len(rows) + 2) + 40
im = Image.new('RGB', (W, H), (250, 248, 243))
d = ImageDraw.Draw(im)
s = st['summary']
d.text((20, 14), 'LY-008 检查器自检矩阵（bce3211 / ly_check sha256 ' + s['checkerSha256'][:12] + '…）', font=ft, fill=(30, 30, 30))
d.text((20, 48), f"{s['cases']} 个用例：负例 {s['negatives']} 个全部判出 {s['negativesCaught']}，正例 {s['positives']} 个通过 {s['positivesPassed']}，"
                 f"自检失败 {s['selftestFailures']}。官方 build_assets --check：基线退出码 {off['runs']['baseline']['exitCode']}、"
                 f"注入后 {off['runs']['injected']['exitCode']}、撤回后 {off['runs']['reverted']['exitCode']}。CPU 绘制。", font=f, fill=(60, 60, 60))
cols = [(20, '用例'), (330, '注入'), (900, '期望错误代码'), (1210, 'ly_check 结果'), (1380, '退出码'), (1450, '官方 checker（注入同一 GLB）')]
y = TOP - 30
for x, t in cols:
    d.text((x, y), t, font=fb, fill=(20, 20, 20))
d.line((20, TOP - 6, W - 20, TOP - 6), fill=(120, 120, 120))
for i, r in enumerate(rows):
    y = TOP + i * RH
    if i % 2:
        d.rectangle((16, y - 2, W - 16, y + RH - 3), fill=(240, 236, 226))
    ok = r['pass']
    d.text((20, y), r['id'][:34], font=f, fill=(20, 20, 20))
    d.text((330, y), r['inject'][:40], font=f, fill=(70, 70, 70))
    d.text((900, y), ','.join(r['expectCodes'])[:30] or '（应通过）', font=f, fill=(70, 70, 70))
    lab = ('判出' if r['expectFail'] else '通过') if ok else '自检失败'
    d.text((1210, y), lab, font=f, fill=(30, 120, 60) if ok else (190, 30, 30))
    d.text((1380, y), str(r['exitCode']), font=f, fill=(70, 70, 70))
    o = case2off.get(r['id'])
    if o:
        t = ('判出：' + o['officialErrors'][0][:18]) if o['officialCatches'] else ('未判出（官方不查这一项）' if r['expectFail'] else '通过（无错误）')
        d.text((1450, y), t, font=f, fill=(30, 120, 60) if o['officialCatches'] == r['expectFail'] else (190, 110, 20))
os.makedirs(os.path.join(ROOT, 'preview'), exist_ok=True)
im.save(os.path.join(ROOT, 'preview', 'selftest-matrix.png'))
print('preview/selftest-matrix.png', im.size)
