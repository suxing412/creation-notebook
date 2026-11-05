# LY-033 prep: read-only measurement of both granary doorways / stairs / floors across all
# 12 v2 split/group GLBs + 3 city GLBs + legacy v1 organized GLBs.
# python -I measure_all.py <lab-docs-root> <out.json>
# Every measurement is bound to the file SHA256. No GLB is written.
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbread as R

DOCS = sys.argv[1]
OUT = sys.argv[2]
CITY = np.array([2285.714111328125, 0.0, -3673.468994140625])
# local centres inside the group (measured: A floor slab x -16.7..-7.3, B 5.8..18.2, both z centre -6)
A_IN_GROUP = np.array([-12.0, 0.0, -6.0])
B_IN_GROUP = np.array([12.0, 0.0, -6.0])
# per-warehouse nominal (measured from split LOD0): front wall plane z, floor top
SPEC = {'A': dict(front=3.0, floor=0.85, steps=4, stairZ=(3.2, 4.48)),
        'B': dict(front=2.5, floor=1.10, steps=6, stairZ=(2.7, 4.62))}
U = 'model-library/updates/m-storage-functional/files/'
C = 'cities/luoyang/progress-assets/granary-city-v1/'
FILES = []
for lod in (0, 1, 2):
    FILES.append((U + 'granary-A-LOD%d.glb' % lod, {'A': np.zeros(3)}))
    FILES.append((U + 'granary-B-LOD%d.glb' % lod, {'B': np.zeros(3)}))
    FILES.append((U + 'granary-group-LOD%d.glb' % lod, {'A': A_IN_GROUP, 'B': B_IN_GROUP}))
    FILES.append((C + 'granary-city-LOD%d.glb' % lod, {'A': CITY + A_IN_GROUP, 'B': CITY + B_IN_GROUP}))
FILES.append(('cities/luoyang/assets/storage/storage-group-organized.glb', {'A': CITY + A_IN_GROUP, 'B': CITY + B_IN_GROUP}))
FILES.append(('model-library/assets/storage-group-organized-local.glb', {'A': A_IN_GROUP, 'B': B_IN_GROUP}))


def ray_first(o, d, T):
    e1 = T[:, 1] - T[:, 0]; e2 = T[:, 2] - T[:, 0]
    h = np.cross(d, e2); a = (e1 * h).sum(1)
    ok = np.abs(a) > 1e-12
    f = np.where(ok, 1.0 / np.where(ok, a, 1), 0)
    s = o - T[:, 0]
    u = f * (s * h).sum(1)
    q = np.cross(s, e1)
    v = f * (q @ d)
    t = f * (e2 * q).sum(1)
    m = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9) & (t > 1e-6)
    return float(t[m].min()) if m.any() else None


def down_hit(T, x, z, ytop):
    t = ray_first(np.array([x, ytop, z]), np.array([0, -1.0, 0]), T)
    return None if t is None else ytop - t


res = []
for rel, centres in FILES:
    path = os.path.join(DOCS, rel)
    if not os.path.exists(path):
        res.append(dict(file=rel, missing=True)); continue
    js, ps = R.prims(path)
    T = np.concatenate([p['pos'][p['tris']] for p in ps])
    rec = dict(file=rel, sha256=R.sha256(path), bytes=os.path.getsize(path), triangles=int(len(T)),
               nodes=[n.get('name') for n in js['nodes']])
    for wh, c in centres.items():
        sp = SPEC[wh]
        loc = T - c  # warehouse-local coordinates
        # restrict to warehouse neighbourhood to avoid hitting the other warehouse / receiving shed
        sel = (loc[:, :, 0].min(1) < 8.5) & (loc[:, :, 0].max(1) > -8.5) & (loc[:, :, 2].max(1) > -5) & (loc[:, :, 2].min(1) < 6.5)  # bbox overlap, keeps city ground
        L = loc[sel]
        # horizontal clear-width scan through the doorway (ray from outside toward -Z)
        xs = np.round(np.arange(-1.2, 1.2001, 0.01), 3)
        rows = {}
        for dy in (0.10, 0.50, 1.00, 1.50, 1.80, 2.00, 2.05, 2.15):
            y = sp['floor'] + dy
            open_x = [x for x in xs if (lambda t: t is None or t > 1.0 + 0.45)(
                ray_first(np.array([x, y, sp['front'] + 1.0]), np.array([0, 0, -1.0]), L))]
            rows['%.2f' % dy] = [min(open_x), max(open_x), round(max(open_x) - min(open_x) + 0.01, 3)] if open_x else None
        # head: highest open height at x=0
        head = None
        for y in np.round(np.arange(sp['floor'] + 0.02, sp['floor'] + 3.0, 0.01), 3):
            t = ray_first(np.array([0.0, y, sp['front'] + 1.0]), np.array([0, 0, -1.0]), L)
            if t is None or t > 1.45:
                head = float(y)
            elif head is not None:
                break
        # stair profile along x=0 and at x=+-0.74/+-0.76/+-0.90 (edge of 1.5 / 1.8 strip)
        prof = {}
        for xx in (0.0, 0.44, 0.74, 0.76, 0.89):
            zs = np.round(np.arange(sp['front'] - 0.3, sp['stairZ'][1] + 0.6, 0.02), 3)
            prof['%.2f' % xx] = [[float(z), (lambda h: None if h is None else round(h, 4))(down_hit(L, xx, z, sp['floor'] + 1.9))] for z in zs]
        rec[wh] = dict(centre=c.tolist(), clearWidthByHeightAboveFloor=rows, headAtX0=head,
                       clearHeight=(None if head is None else round(head - sp['floor'], 3)), stairProfiles=prof)
    res.append(rec)
    print(rel, rec['sha256'][:12], {wh: (rec[wh]['clearWidthByHeightAboveFloor']['1.00'], rec[wh]['clearHeight']) for wh in centres})
json.dump(res, open(OUT, 'w'), indent=1)
