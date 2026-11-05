# LY-046 prep: probe for a supportable outlet. (1) wall column between TC03-2 drain end and lot front;
# (2) city ground-south height levels around C02-010 / C02-012 and profiles from door / drain end outward.
# Read-only. usage: python probe_outlet.py <lab_root> <out_json>
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbio import nodes_tris, raster, sha256, col_major
LAB, OUT = sys.argv[1], sys.argv[2]
C = os.path.join(LAB, 'docs/cities/luoyang')
rep = {'tool': 'probe_outlet.py', 'inputs': {}}
# (1) TC03-2 local: wall/roof/timber/plinth surfaces in strip x 26.5..27.1, z -3.5..0.5
p = os.path.join(C, 'assets/c02v/TC03-2-LOD0-prototype.glb'); rep['inputs']['assets/c02v/TC03-2-LOD0-prototype.glb'] = sha256(p)
nt = nodes_tris(p)
strip = {}
for k, t in nt.items():
    P = t.reshape(-1, 3)
    c = t.mean(1)
    m = (t[:, :, 0].max(1) >= 26.5) & (t[:, :, 0].min(1) <= 27.1) & (t[:, :, 2].max(1) >= -3.5) & (t[:, :, 2].min(1) <= 0.5)
    if m.any():
        q = t[m].reshape(-1, 3)
        strip[k] = {'tris': int(m.sum()), 'bboxInStripTris': [q.min(0).round(3).tolist(), q.max(0).round(3).tolist()]}
rep['TC03-2_drainEndStrip'] = strip
# (2) city ground levels
gp = os.path.join(C, 'assets/ground-atomic/south.glb'); rep['inputs']['assets/ground-atomic/south.glb'] = sha256(gp)
gt = np.concatenate(list(nodes_tris(gp).values()))
gn = nodes_tris(gp)
rep['groundSouthNodes'] = {k: {'tris': int(len(t)), 'yMin': round(float(t[:, :, 1].min()), 4), 'yMax': round(float(t[:, :, 1].max()), 4)} for k, t in gn.items()}
H = 0.1
def window(x0, z0, x1, z1):
    nx, nz = int(round((x1 - x0) / H)), int(round((z1 - z0) / H))
    top = raster(gt, x0, z0, H, nx, nz)[0]
    return top, x0, z0, nx, nz
out = {}
for cid, (x0, z0, x1, z1) in {'C02-010': (514, -838.45, 548, -796.45), 'C02-012': (562, -849.45, 606, -797.45)}.items():
    top, gx0, gz0, nx, nz = window(x0, z0, x1, z1)
    vals, cnt = np.unique(np.round(top[np.isfinite(top)], 4), return_counts=True)
    levels = []
    for v, n in zip(vals, cnt):
        jj, ii = np.nonzero(np.isclose(top, v, atol=5e-5))
        if n * H * H < 0.5: continue
        levels.append({'y': float(v), 'areaM2': round(float(n) * H * H, 2), 'xRange': [round(gx0 + ii.min() * H, 2), round(gx0 + (ii.max() + 1) * H, 2)], 'zRange': [round(gz0 + jj.min() * H, 2), round(gz0 + (jj.max() + 1) * H, 2)]})
    # non-planar cells: slope magnitude
    gy, gxx = np.gradient(np.where(np.isfinite(top), top, np.nan), H)
    s = np.hypot(gy, gxx); s = s[np.isfinite(s)]
    out[cid] = {'window': [x0, z0, x1, z1], 'levels': levels, 'slopePercent_p50_p99_max': [round(float(np.percentile(s, 50) * 100), 3), round(float(np.percentile(s, 99) * 100), 3), round(float(s.max() * 100), 3)]}
    def prof(xa, za, xb, zb, n=120):
        pts = []
        for f in np.linspace(0, 1, n):
            x, z = xa + (xb - xa) * f, za + (zb - za) * f
            i, j = int((x - gx0) / H), int((z - gz0) / H)
            y = top[j, i] if 0 <= i < nx and 0 <= j < nz else None
            pts.append([round(x, 2), round(z, 2), None if y is None or not np.isfinite(y) else round(float(y), 4)])
        return pts
    if cid == 'C02-010':
        out[cid]['profileFromDoorNorth'] = prof(527.5, -806.5, 527.5, -797.0, 96)   # door centre x local -3.5, out through lane
        out[cid]['profileAlongLaneEW'] = prof(515, -804.45, 547, -804.45, 160)
    else:
        out[cid]['profileFromDrainEndNorth'] = prof(596.8, -808.45, 596.8, -798.0, 105)
        out[cid]['profileFromDoorNorth'] = prof(579.0, -805.5, 579.0, -798.0, 76)
rep['cityGround'] = out
json.dump(rep, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(strip, indent=0))
print(json.dumps(rep['groundSouthNodes']))
for cid, o in out.items():
    print(cid, o['slopePercent_p50_p99_max'])
    for l in o['levels']: print('  ', l)
