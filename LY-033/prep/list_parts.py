# LY-033 prep: list connected components (bbox, tri count) of a GLB, read-only.
# python -I list_parts.py <glb> [material-substring]
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbread as R

path = sys.argv[1]
flt = sys.argv[2] if len(sys.argv) > 2 else ''
js, ps = R.prims(path)
print('sha256', R.sha256(path))
for p in ps:
    if flt and flt not in (p['material'] or ''):
        continue
    cs = R.components(p)
    print('== node=%s mat=%s tris=%d comps=%d' % (p['node'], p['material'], len(p['tris']), len(cs)))
    cs.sort(key=lambda c: (round(c['lo'][2], 3), round(c['lo'][0], 3), round(c['lo'][1], 3)))
    for c in cs:
        print('   n=%4d lo=(%7.3f %6.3f %7.3f) hi=(%7.3f %6.3f %7.3f) size=(%6.3f %6.3f %6.3f)' % (
            len(c['tris']), *c['lo'], *c['hi'], *(c['hi'] - c['lo'])))
