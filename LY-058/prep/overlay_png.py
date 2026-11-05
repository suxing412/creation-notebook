# LY-058 prep: overlay service band, C winnow/storage probe squares and probe points on the grid map.
# usage: python overlay_png.py <grid.npz> <route.json> <step_max> <out.png> [scale]
import sys, json, numpy as np
from PIL import Image, ImageDraw
d = np.load(sys.argv[1]); R = json.load(open(sys.argv[2], encoding='utf-8')); sm = sys.argv[3]; S = int(sys.argv[5]) if len(sys.argv) > 5 else 3
band = np.load(sys.argv[2].replace('.json', '-band-%s.npy' % sm))
xs, zs = d['xs'], d['zs']; NX, NZ = len(xs), len(zs); st = xs[1] - xs[0]
img = np.full((NZ, NX, 3), 250, np.uint8)
img[(d['blocked']).T] = (0, 0, 0)
img[((~d['blocked']) & (~d['walk'])).T] = (120, 120, 120)
img[(d['walk'] & d['inside_fp'] & ~d['sky']).T] = (150, 200, 200)
img[(d['walk'] & d['inside_fp'] & d['sky']).T] = (200, 235, 190)
img[(d['walk'] & d['has_floor']).T] = (180, 170, 230)
img[(band & d['walk']).T] = (250, 200, 120)
im = Image.fromarray(img).resize((NX * S, NZ * S), Image.NEAREST); dr = ImageDraw.Draw(im)
def P(x, z): return ((x - xs[0]) / st * S, (z - zs[0]) / st * S)
r = R['per_step_max'][sm]
for key, col in (('winnow_open_sky_square_outside_band', (0, 140, 0)), ('roofed_square_outside_band', (0, 0, 200))):
    q = r[key]; a = P(q['x'][0] - st / 2, q['z'][0] - st / 2); b = P(q['x'][1] + st / 2, q['z'][1] + st / 2)
    dr.rectangle([a, b], outline=col, width=3); dr.text((a[0] + 4, a[1] + 4), key.split('_')[0] + ' %.1fm' % q['side_m'], fill=col)
for k, (x, z) in R['probe_points_C'].items():
    c = P(x, z); ok = r['probe_reachable'][k]
    dr.ellipse([c[0] - 5, c[1] - 5, c[0] + 5, c[1] + 5], fill=(0, 160, 0) if ok else (220, 0, 0))
    dr.text((c[0] + 7, c[1] - 6), k, fill=(0, 0, 0))
for m in range(-10, 11, 2):
    px = P(m, zs[0])[0]; dr.line([(px, 0), (px, 8)], fill=(0, 0, 255)); dr.text((px + 2, 9), 'x%d' % m, fill=(0, 0, 255))
for m in range(-12, 14, 2):
    pz = P(xs[0], m)[1]; dr.line([(0, pz), (8, pz)], fill=(0, 0, 255)); dr.text((10, pz - 5), 'z%d' % m, fill=(0, 0, 255))
dr.text((10, im.size[1] - 14), 'LY-058 prep CPU grid map, step_max=%s m, body r=0.30 m, head 2.0 m; orange=1.2 m C service band' % sm, fill=(0, 0, 0))
im.save(sys.argv[4]); print('saved', sys.argv[4], im.size)
