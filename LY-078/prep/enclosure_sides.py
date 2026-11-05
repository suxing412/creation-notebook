# LY-078 prep: per-side fence coverage (gaps) and support (lowest y) of enclosure + gate parts.
# python -I enclosure_sides.py qa/parts-near.json
import sys, json
d = json.load(open(sys.argv[1], encoding='utf-8'))
T = d['materials']['LY_P01_timber']['partList']
def inside(p, lo, hi, e=1e-3): return all(p['lo'][i] >= lo[i]-e and p['hi'][i] <= hi[i]+e for i in range(3))
cover = ([-12.2,0,-7.1],[12.2,6.6,7.1]); gate = ([-2.4,0,9.7],[2.4,3.6,10.4])
enc = [p for p in T if not inside(p,*cover) and not inside(p,*gate)]
g = [p for p in T if inside(p,*gate)]
print('gate parts:'); [print('  ', p['lo'], p['hi'], p['tris']) for p in g]
def cov(parts, axis):
    iv = sorted((p['lo'][axis], p['hi'][axis]) for p in parts); m = []
    for a,b in iv:
        if m and a <= m[-1][1] + 1e-3: m[-1][1] = max(m[-1][1], b)
        else: m.append([a,b])
    return m
sides = {'north z=-10': [p for p in enc if p['hi'][2] < -9.6], 'south z=+10': [p for p in enc if p['lo'][2] > 9.6],
         'west x=-14': [p for p in enc if p['hi'][0] < -13.6], 'east x=+14': [p for p in enc if p['lo'][0] > 13.6]}
for k, ps in sides.items():
    ax = 0 if k.startswith(('north','south')) else 2
    print(k, 'parts', len(ps), 'covered', cov(ps, ax), 'minY', min(p['lo'][1] for p in ps), 'maxY', max(p['hi'][1] for p in ps))
posts = [p for p in enc if p['hi'][1]-p['lo'][1] > 1.4]
print('enclosure posts', len(posts), 'lowest lo.y', min(p['lo'][1] for p in posts), 'highest lo.y', max(p['lo'][1] for p in posts))
float_parts = [p for p in enc if p['lo'][1] > 1e-3]
print('enclosure parts not touching y=0:', len(float_parts), '(rails/pickets; need post contact check)')
pick = [p for p in enc if abs((p['hi'][0]-p['lo'][0]) - 0.07) < 0.01 and abs((p['hi'][1]-p['lo'][1]) - 1.11) < 0.01]
print('pickets', len(pick), 'pickets lo.y set', sorted(set(p['lo'][1] for p in pick)))
other = [p for p in T if not inside(p,*cover) and not inside(p,*gate) and not inside(p,[-14.2,0,-10.2],[14.2,1.8,10.4])]
print('timber outside all rule boxes:', len(other))
