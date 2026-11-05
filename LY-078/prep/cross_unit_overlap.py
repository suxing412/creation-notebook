# LY-078 prep: AABB positive-volume overlaps between parts of DIFFERENT candidate units (approximate, part-bbox level;
# not an exact solid test). python -I cross_unit_overlap.py qa/parts-near.json qa/cross-unit-near.json
import sys, json, itertools
d = json.load(open(sys.argv[1], encoding='utf-8'))
def inside(p, lo, hi, e=1e-3): return all(p['lo'][i] >= lo[i]-e and p['hi'][i] <= hi[i]+e for i in range(3))
def unit(m, p):
    if m == 'LY_P01_earth': return 'ground'
    if m in ('LY_P01_tile','LY_P01_plaster') or inside(p,[-12.2,0,-7.1],[12.2,6.6,7.1]): return 'cover'
    if inside(p,[-2.4,0,9.7],[2.4,3.6,10.4]) and p['hi'][1] > 1.8: return 'south_gate'
    return 'enclosure'
items = [(unit(m,p), m, p) for m, M in d['materials'].items() for p in M['partList']]
res = []; touch = {}
for (ua,ma,a),(ub,mb,b) in itertools.combinations(items, 2):
    if ua == ub: continue
    ov = [min(a['hi'][i], b['hi'][i]) - max(a['lo'][i], b['lo'][i]) for i in range(3)]
    if all(o > 1e-6 for o in ov):
        res.append({'units': [ua, ub], 'a': [a['lo'], a['hi']], 'b': [b['lo'], b['hi']], 'overlap_m': [round(o,4) for o in ov], 'vol_m3': round(ov[0]*ov[1]*ov[2], 6)})
    elif all(o >= -1e-6 for o in ov):
        k = '/'.join(sorted([ua, ub])); touch[k] = touch.get(k, 0) + 1
out = {'src': sys.argv[1], 'positiveVolumeAABBOverlaps': res, 'touchingPairsByUnits': touch,
       'note': 'part-level AABB; columns/posts are boxes or prisms so AABB overlap equals solid overlap for the box members listed; roof/tile parts not exact'}
json.dump(out, open(sys.argv[2], 'w', encoding='utf-8'), indent=1)
print(len(res), 'cross-unit positive-volume AABB overlaps'); [print(' ', r) for r in res[:12]]; print('touching', touch)
