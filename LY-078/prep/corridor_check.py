# LY-078 prep: discrete AABB corridor check from street edge (z=18) through south gate to reserve edge (z=3).
# Body envelope: 0.60 m wide x 1.80 m tall pedestrian (C test, not code compliance); also a 2.0 m x 2.6 m handcart box.
# python -I corridor_check.py qa/parts-near.json qa/corridor-near.json
import sys, json
d = json.load(open(sys.argv[1], encoding='utf-8'))
parts = [(m, p) for m, M in d['materials'].items() if m != 'LY_P01_earth' for p in M['partList']]
def hits(lo, hi): return [(m, p['lo'], p['hi']) for m, p in parts if all(p['lo'][i] < hi[i]-1e-6 and p['hi'][i] > lo[i]+1e-6 for i in range(3))]
cases = {}
for name, (hw, h) in {'pedestrian_0.60x1.80': (0.30, 1.80), 'handcart_2.00x2.60': (1.00, 2.60), 'max_box_3.60x3.10': (1.80, 3.10), 'neg_box_3.80x3.10': (1.90, 3.10), 'neg_box_3.60x3.20': (1.80, 3.20)}.items():
    lo = [-hw, 0.001, 3.0]; hi = [hw, h, 18.0]
    hl = hits(lo, hi); cases[name] = {'box': [lo, hi], 'hits': len(hl), 'hitList': hl[:6]}
# lateral sweep: which x-centres admit the pedestrian through the gate line (z 9.7..10.4)
ok = []
x = -3.0
while x <= 3.0001:
    if not hits([x-0.30, 0.001, 9.6], [x+0.30, 1.80, 10.5]): ok.append(round(x, 2))
    x += 0.05
cases['pedestrian_gate_x_centres_ok'] = [min(ok), max(ok)] if ok else None
# ground support under corridor: earth top y=0 spans x[-20,20] z[-16,18]
cases['ground_top_y'] = d['materials']['LY_P01_earth']['hi'][1]
json.dump(cases, open(sys.argv[2], 'w', encoding='utf-8'), indent=1)
for k, v in cases.items(): print(k, v if not isinstance(v, dict) else (v['hits'], v['hitList'][:2]))
