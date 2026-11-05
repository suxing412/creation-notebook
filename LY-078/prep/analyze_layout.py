# LY-078 prep: classify parts of stoneclassic near GLB by position. python -I analyze_layout.py qa/parts-near.json <glb>
import sys, json, collections
import numpy as np
sys.path.insert(0, __file__.rsplit('/',1)[0] if '/' in __file__ else '.')
d = json.load(open(sys.argv[1], encoding='utf-8'))
T = d['materials']['LY_P01_timber']['partList']
def sz(p): return [round(h-l,3) for l,h in zip(p['lo'],p['hi'])]
b = collections.Counter()
for p in T: b[tuple(sz(p))] += 1
print('timber part size buckets (dx,dy,dz):count')
for k,v in sorted(b.items(), key=lambda kv:-kv[1]): print('  ',k,v)
tall = [p for p in T if sz(p)[1] > 2.0]
print('timber parts taller than 2 m:')
for p in sorted(tall, key=lambda p:(p['lo'][2],p['lo'][0])): print('  ', p['lo'], p['hi'], p['tris'])
print('plaster parts:')
for p in d['materials']['LY_P01_plaster']['partList']: print('  ', p['lo'], p['hi'])
print('tile parts (bbox of all) n=', len(d['materials']['LY_P01_tile']['partList']))
