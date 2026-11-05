# LY-047 prep: CPU plan diagrams from the same grids as measure_ly047.py (Pillow raster, not a GPU/browser render).
# usage: python -I plot_ly047.py <lab_root> <measure.json> <out_dir>
# Legend: dark = obstacle in body band 0.45-2.10 m; grey = geometry at any height; light blue = reachable body centre r0.30;
#         blue = reachable r0.45 (laden); red = storage bins/bench AABB; orange = shed box; green = workshed eaves (A2 option);
#         magenta = LY-044 stove trial point; black = gate seed / door points. North (glTF -z) is up.
import sys, os, json
LAB, MJ, OUTD = sys.argv[1], sys.argv[2], sys.argv[3]
sys.argv = [sys.argv[0], LAB, os.devnull]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw
import measure_ly047 as m

M = json.load(open(MJ, encoding='utf-8'))
os.makedirs(OUTD, exist_ok=True)
grid = m.Grid()
S = 3  # pixels per cell


def px(x, z):
    return ((x - grid.x0) / m.CELL * S, (z - grid.z0) / m.CELL * S)


def rect(d, r, col, w=2):
    x0, x1, z0, z1 = r
    a, b = px(x0, z0), px(x1, z1)
    d.rectangle([a, b], outline=col, width=w)


def court_png(variant, path, fn, extra):
    keep, _ = m.load_proto(path, m.EXCLUDE[variant])
    allT = np.concatenate(list(keep.values()))
    band = grid.raster(allT, *m.BAND)
    anyh = grid.raster(allT, m.FLOOR + 0.05, None)
    rw, _, _ = m.reachable(grid, band, m.R_WALK, m.GATE[variant])
    rl, _, _ = m.reachable(grid, band, m.R_LADEN, m.GATE[variant])
    img = np.full((grid.nz, grid.nx, 3), 255, np.uint8)
    img[anyh.T] = (215, 215, 215)
    img[rw.T] = (205, 230, 255)
    img[rl.T] = (150, 200, 255)
    img[band.T] = (60, 60, 60)
    im = Image.fromarray(img).resize((grid.nx * S, grid.nz * S), Image.NEAREST)
    d = ImageDraw.Draw(im)
    extra(d)
    im.save(os.path.join(OUTD, fn))


def storage(key):
    def f(d):
        for e in M['inplace'][key]['storage_access']:
            mn, mx = e['min'], e['max']
            rect(d, (mn[0], mx[0], mn[2], mx[2]), (220, 0, 0))
        rect(d, M['inplace'][key]['shed_box'], (255, 140, 0), 1)
        g = m.GATE[M['inplace'][key]['variant']]
        a = px(*g); d.rectangle([a[0] - 4, a[1] - 4, a[0] + 4, a[1] + 4], fill=(0, 0, 0))
    return f


court_png('B', m.PROTO['B'][0], 'plan-B-LOD0.png', storage('B-LOD0'))
court_png('B2', m.PROTO['B2'][0], 'plan-B2-LOD0.png', storage('B2-LOD0'))
A = M['a2_install_option']


def a2(d):
    ref = (-4.5, 7.5)
    e = A['workshed_eaves_rect_local']
    rect(d, (e[0] + ref[0], e[1] + ref[0], e[2] + ref[1], e[3] + ref[1]), (0, 160, 0), 3)
    for b in A['workshed_post_boxes']:
        rect(d, (b[0] + ref[0], b[1] + ref[0], b[2] + ref[1], b[3] + ref[1]), (0, 100, 0), 2)
    sx, sz = m.LY044_STOVE_TRIAL_LOCAL
    a = px(sx, sz); d.ellipse([a[0] - 6, a[1] - 6, a[0] + 6, a[1] + 6], fill=(200, 0, 200))
    for xy in list(m.A2_DOORS.values()) + [m.GATE['A2']]:
        a = px(*xy); d.rectangle([a[0] - 4, a[1] - 4, a[0] + 4, a[1] + 4], fill=(0, 0, 0))


court_png('A2', m.PROTO['A2'][0], 'plan-A2-workshed-ref.png', a2)
print('ok')
