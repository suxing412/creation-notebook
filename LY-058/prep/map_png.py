# LY-058 prep: render the measure_yard.py grid to a top-down PNG (x right, glTF +z down the image).
# colours: black=blocked, dark grey=eroded (too close to obstacle), red=walkable but NOT reachable from outside,
# light green=reachable open sky, teal=reachable roofed, blue tint=floor geometry present (raised floor), white=outside pad.
# usage: python map_png.py <out.npz> <out.png> [scale]
import sys, numpy as np
from PIL import Image, ImageDraw
d = np.load(sys.argv[1]); S = int(sys.argv[3]) if len(sys.argv) > 3 else 4
xs, zs = d['xs'], d['zs']; NX, NZ = len(xs), len(zs)
img = np.full((NZ, NX, 3), 255, np.uint8)
for i in range(NX):
    for j in range(NZ):
        if d['blocked'][i, j]: c = (0, 0, 0)
        elif not d['walk'][i, j]: c = (110, 110, 110)
        elif not d['reach'][i, j]: c = (220, 40, 40)
        elif d['sky'][i, j]: c = (170, 230, 150) if d['inside_fp'][i, j] else (245, 245, 245)
        else: c = (60, 170, 170)
        if d['has_floor'][i, j] and not d['blocked'][i, j] and d['walk'][i, j]:
            c = (int(c[0] * 0.6), int(c[1] * 0.6), min(255, int(c[2] * 0.6) + 90))
        img[j, i] = c
im = Image.fromarray(img).resize((NX * S, NZ * S), Image.NEAREST)
dr = ImageDraw.Draw(im)
step = xs[1] - xs[0]
for m in range(int(np.floor(xs[0])), int(np.ceil(xs[-1])) + 1):
    if m % 2 == 0:
        px = (m - xs[0]) / step * S; dr.line([(px, 0), (px, 6)], fill=(0, 0, 255)); dr.text((px + 1, 6), str(m), fill=(0, 0, 255))
for m in range(int(np.floor(zs[0])), int(np.ceil(zs[-1])) + 1):
    if m % 2 == 0:
        pz = (m - zs[0]) / step * S; dr.line([(0, pz), (6, pz)], fill=(0, 0, 255)); dr.text((8, pz - 5), str(m), fill=(0, 0, 255))
im.save(sys.argv[2])
print('saved', sys.argv[2], im.size)
