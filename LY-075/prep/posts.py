# LY-075 prep: list vertical timber members (posts) per GLB: connected components of the timber mesh
# with height >= 2.5 m and plan footprint <= 0.8 m. Usage: python posts.py <glb>...
import sys, numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from glbinfo import load, acc
for path in sys.argv[1:]:
    js, b = load(path)
    for n in js['nodes']:
        if 'timber' not in n['name'] and 'earth' not in n['name']: continue
        pr = js['meshes'][n['mesh']]['primitives'][0]
        P = acc(js, b, pr['attributes']['POSITION']).astype(np.float64)
        I = acc(js, b, pr['indices']).reshape(-1, 3).astype(np.int64)
        key = np.round(P / 1e-4).astype(np.int64); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.reshape(-1)
        Iw = inv[I]; nv = inv.max() + 1
        r = np.concatenate([Iw[:, 0], Iw[:, 1]]); c = np.concatenate([Iw[:, 1], Iw[:, 2]])
        _, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(nv, nv)), directed=False)
        Pw = np.zeros((nv, 3)); Pw[inv] = P
        posts = []
        for k in np.unique(lab):
            q = Pw[lab == k]; lo, hi = q.min(0), q.max(0); s = hi - lo
            if s[1] >= 2.5 and s[0] <= 0.8 and s[2] <= 0.8:
                posts.append((round((lo[0]+hi[0])/2, 3), round((lo[2]+hi[2])/2, 3), round(s[0], 3), round(lo[1], 3), round(hi[1], 3)))
        posts.sort(key=lambda p: (p[1], p[0]))
        print(path.split('/')[-1], n['name'], 'components', lab.max() + 1, 'posts', len(posts))
        for p in posts: print('   x %.3f z %.3f diam %.3f y %.3f..%.3f' % p)
