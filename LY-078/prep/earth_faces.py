# LY-078 prep: list earth (ground) triangles grouped by plane; find top-surface footprint & street strip.
# python -I earth_faces.py <glb>
import sys, json, importlib.util, numpy as np, collections
spec = importlib.util.spec_from_file_location('mp', __file__.replace('earth_faces.py','measure_parts.py'))
src = open(spec.origin, encoding='utf-8').read().replace('\nmain()\n', '\n')
P = {}; exec(compile(src, 'mp', 'exec'), P)
js, binc, sha, n = P['load'](sys.argv[1])
for p in js['meshes'][0]['primitives']:
    name = js['materials'][p['material']]['name']
    pos = P['acc'](js, binc, p['attributes']['POSITION']).astype(float)
    tris = P['acc'](js, binc, p['indices']).reshape(-1,3).astype(int)
    if name != 'LY_P01_earth':
        # lowest vertex y per material, and count of verts below 0
        print(name, 'minY', round(pos[:,1].min(),4), 'verts y<-1e-4:', int((pos[:,1] < -1e-4).sum()))
        continue
    planes = collections.defaultdict(list)
    for t in tris:
        a,b,c = pos[t]; nrm = np.cross(b-a, c-a); ar = np.linalg.norm(nrm)/2; nrm = nrm/ (np.linalg.norm(nrm)+1e-12)
        key = tuple(np.round(nrm,3)) + (round(float(np.dot(nrm,a)),3),)
        planes[key].append((ar, pos[t]))
    for k,v in sorted(planes.items()):
        allv = np.vstack([x[1] for x in v]); print('plane n=',k[:3],'d=',k[3],'tris',len(v),'area',round(sum(x[0] for x in v),3),'lo',np.round(allv.min(0),3).tolist(),'hi',np.round(allv.max(0),3).tolist())
