# LY-078 prep: Taixue A LOD1 earth parts (platform/steps) for the A-side interface that LY-077 will freeze.
# python -I taixue_a_steps.py <taixue-A-LOD1.glb>
import sys, numpy as np, collections
src = open(__file__.replace('taixue_a_steps.py','measure_parts.py'), encoding='utf-8').read().replace('\nmain()\n','\n')
P = {}; exec(compile(src,'mp','exec'), P)
js, binc, sha, n = P['load'](sys.argv[1]); print(sha, n)
for ni,node in enumerate(js['nodes']):
    m = js['meshes'][node['mesh']]
    for p in m['primitives']:
        pos = P['acc'](js,binc,p['attributes']['POSITION']).astype(float)
        tris = P['acc'](js,binc,p['indices']).reshape(-1,3).astype(int)
        print(node['name'], 'tris', len(tris), 'lo', np.round(pos.min(0),3).tolist(), 'hi', np.round(pos.max(0),3).tolist())
        if 'earth' in node['name']:
            gs = P['parts'](pos, tris)
            for g in sorted(gs, key=lambda g: pos[tris[g].reshape(-1)].min(0)[2]):
                v = pos[tris[g].reshape(-1)]
                print('   part tris', len(g), 'lo', np.round(v.min(0),3).tolist(), 'hi', np.round(v.max(0),3).tolist())
