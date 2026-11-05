# LY-033 prep: measure the door opening, stair and floor of one granary split GLB (read-only).
# python -I opening_probe.py <granary-X-LOD0.glb> [json-out]
# Finds: floor-slab top, front wall plane, opening jambs/lintel (from wall-shell vertices near the
# front plane), stair width/depth/rise/step count, and clear-width rays through the opening.
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbread as R

path = sys.argv[1]
js, ps = R.prims(path)
timber = [p for p in ps if 'timber' in (p['material'] or '')][0]
tile = [p for p in ps if 'tile' in (p['material'] or '')][0]
cargo = [p for p in ps if 'cargo' in (p['material'] or '')]
cs = R.components(timber)
size = lambda c: c['hi'] - c['lo']
# floor slab: widest thin component
floor = max([c for c in cs if size(c)[1] < 0.3], key=lambda c: size(c)[0] * size(c)[2])
shell = max(cs, key=lambda c: size(c)[1] * size(c)[0])
stair = [c for c in cs if c['lo'][2] >= floor['hi'][2] - 1e-6]
stair = stair[0] if stair else None
out = dict(file=os.path.basename(path), sha256=R.sha256(path))
out['floor'] = dict(top=float(floor['hi'][1]), bottom=float(floor['lo'][1]),
                    x=[float(floor['lo'][0]), float(floor['hi'][0])], z=[float(floor['lo'][2]), float(floor['hi'][2])])
out['shell'] = dict(lo=shell['lo'].round(4).tolist(), hi=shell['hi'].round(4).tolist(), tris=int(len(shell['tris'])))
zf = float(shell['hi'][2])
V = timber['pos'][timber['tris'][shell['tris']].reshape(-1)]
U = np.unique(V.round(4), axis=0)
front = U[np.abs(U[:, 2] - zf) < 1e-3]
inner = U[(np.abs(U[:, 2] - zf) < 0.5) & (np.abs(U[:, 2] - zf) >= 1e-3)]
out['frontPlaneZ'] = zf
out['frontVertsXY'] = sorted({(float(x), float(y)) for x, y in front[:, :2]})
out['wallThicknessCandidatesZ'] = sorted({float(z) for z in inner[:, 2]})
# opening: interior x-coordinates on the front plane that are not the outer corners
xs = sorted({float(x) for x in front[:, 0]})
ys = sorted({float(y) for y in front[:, 1]})
out['frontXs'], out['frontYs'] = xs, ys
# ray test: horizontal rays along -Z from outside (z=zf+1) at grid of x,y, hit any timber/tile triangle?
T = np.concatenate([timber['pos'][timber['tris']], tile['pos'][tile['tris']]] +
                   [c['pos'][c['tris']] for c in cargo])


def ray_hits(o, d, tris):
    e1 = tris[:, 1] - tris[:, 0]; e2 = tris[:, 2] - tris[:, 0]
    h = np.cross(d, e2); a = (e1 * h).sum(1)
    ok = np.abs(a) > 1e-12
    f = np.where(ok, 1.0 / np.where(ok, a, 1), 0)
    s = o - tris[:, 0]
    u = f * (s * h).sum(1)
    q = np.cross(s, e1)
    v = f * (q * d).sum(-1) if q.ndim == 1 else f * (q * d).sum(1)
    t = f * (e2 * q).sum(1)
    m = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-6)
    return t[m]


ftop = out['floor']['top']
grid = []
for y in np.round(np.arange(ftop + 0.05, ftop + 3.0, 0.05), 3):
    row = []
    for x in np.round(np.arange(-2.0, 2.0001, 0.025), 3):
        t = ray_hits(np.array([x, y, zf + 1.0]), np.array([0, 0, -1.0]), T)
        row.append(float(t.min()) if len(t) else None)
    grid.append((float(y), row))
# a cell is "open" if the first hit lies >= 0.5 m behind the front plane (i.e. ray passes wall thickness)
xsg = np.round(np.arange(-2.0, 2.0001, 0.025), 3)
open_rows = []
for y, row in grid:
    op = [bool(r is None or r > 1.0 + 0.5) for r in row]
    xo = xsg[np.array(op)]
    open_rows.append((y, (float(xo.min()), float(xo.max())) if len(xo) else None, int(sum(op))))
out['openingRaysPerHeight'] = [dict(y=y, openX=o, openCount=n) for y, o, n in open_rows]
oy = [y for y, o, n in open_rows if o]
out['opening'] = dict(sill=ftop, headApprox=(max(oy) if oy else None),
                      widthAtMid=(lambda r: (r[1][1] - r[1][0]) if r and r[1] else None)(
                          next((r for r in open_rows if abs(r[0] - (ftop + 1.0)) < 0.026), None)))
if stair is not None:
    sp = timber['pos'][timber['tris'][stair['tris']].reshape(-1)]
    tops = sorted({round(float(y), 4) for y in sp[:, 1]})
    zs = sorted({round(float(z), 4) for z in sp[:, 2]})
    out['stair'] = dict(lo=stair['lo'].round(4).tolist(), hi=stair['hi'].round(4).tolist(),
                        width=float(stair['hi'][0] - stair['lo'][0]), depth=float(stair['hi'][2] - stair['lo'][2]),
                        totalRise=float(stair['hi'][1] - stair['lo'][1]), levelsY=tops, levelsZ=zs,
                        boxes=int(len(stair['tris']) // 12))
print(json.dumps({k: v for k, v in out.items() if k not in ('openingRaysPerHeight', 'frontVertsXY')}, indent=1))
for r in out['openingRaysPerHeight'][::4]:
    print(r)
if len(sys.argv) > 2:
    json.dump(out, open(sys.argv[2], 'w'), indent=1)
