# LY-060 prep: derive body extents from measure-out.json, excluding presentation/display ground nodes,
# and check that the pestle embedded in workyard-LOD0 is foot-pestle-LOD0 under a pure translation.
# python -I body_extents.py measure-out.json body-extents.json
import json, sys
d = json.load(open(sys.argv[1], encoding='utf-8'))
EXCL = ('presentation_ground',)
out = {}
for k, v in d.items():
    ns = [n for n in v['nodes'] if not any(e in n['name'] for e in EXCL)]
    ex = [n['name'] for n in v['nodes'] if any(e in n['name'] for e in EXCL)]
    lo = [min(n['min'][i] for n in ns) for i in range(3)]
    hi = [max(n['max'][i] for n in ns) for i in range(3)]
    out[k] = {'excludedNodes': ex, 'bodyMin': lo, 'bodyMax': hi,
              'bodyFootprintXY': [round(hi[0]-lo[0], 3), round(hi[1]-lo[1], 3)],
              'bodyFootprintArea': round((hi[0]-lo[0])*(hi[1]-lo[1]), 2),
              'fullFootprintArea': v['footprintArea'], 'bboxMinZ': v['bboxMin'][2]}
# pestle translation check
fp = {n['name']: n for n in d['m-luoyang-foot-pestle/foot-pestle-LOD0.glb']['nodes']}
wy = {n['name']: n for n in d['m-luoyang-workyard-shed/workyard-LOD0.glb']['nodes']}
pairs = [('pestle_stone_static', 'workyard_stone'), ('pestle_timber_moving', 'pestle__pestle_timber_moving')]
chk = []
for a, b in pairs:
    A, B = fp[a], wy[b]
    off = [round(B['min'][i]-A['min'][i], 4) for i in range(3)]
    off2 = [round(B['max'][i]-A['max'][i], 4) for i in range(3)]
    chk.append({'pestleNode': a, 'workyardNode': b, 'offsetMin': off, 'offsetMax': off2,
                'sameSize': off == off2, 'trisPestle': A['tris'], 'trisWorkyard': B['tris']})
out['_pestleEmbeddedInWorkyard'] = chk
json.dump(out, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for k, v in out.items():
    print(k, v if k.startswith('_') else (v['bodyFootprintXY'], v['bodyFootprintArea'], v['fullFootprintArea'], v['excludedNodes'], v['bodyMin'][2]))
