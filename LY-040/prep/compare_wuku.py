# LY-040 prep: does the wuku-B placed in the 2026-11-04 city-visible mother equal library wuku-B-LOD0 (+ translation)?
# Usage: python -I compare_wuku.py <lib_wuku_B_LOD0.glb> <wuku_C_with_support-01.glb> <wuku_C_with_support-02.glb> tx ty
import sys, hashlib, numpy as np
sys.path.insert(0, __import__('os').path.dirname(__file__))
import glbinspect as g

def tris(path, skip=()):
    js, b = g.load(path); out = {}
    for i, n, W, pth in g.walk(js):
        if 'mesh' not in n or n.get('name') in skip: continue
        T = []
        for p in js['meshes'][n['mesh']]['primitives']:
            pos = g.acc(js, b, p['attributes']['POSITION']).astype(float)
            wp = (W[:3, :3] @ pos.T).T + W[:3, 3]
            nat = np.c_[wp[:, 0], -wp[:, 2], wp[:, 1]]
            idx = g.acc(js, b, p['indices']).reshape(-1).astype(np.int64) if 'indices' in p else np.arange(len(nat))
            T.append(nat[idx].reshape(-1, 3, 3))
        out[n.get('name')] = np.concatenate(T)
    return out

lib = tris(sys.argv[1]); a = tris(sys.argv[2], skip=('C_WUKU_ISOLATED_SUPPORT_PATCH',)); a.update(tris(sys.argv[3]))
tx, ty = float(sys.argv[4]), float(sys.argv[5])
key = lambda nm: nm.split('__wuku-B-')[-1].split('.')[0].replace('wuku-B-', '')
L = {key(k): v + np.array([tx, ty, 0.0]) for k, v in lib.items()}
M = {key(k): v for k, v in a.items()}
print('parts lib', {k: len(v) for k, v in L.items()}, 'mother', {k: len(v) for k, v in M.items()})
worst = 0.0
for k in L:
    l, m = L[k], M[k]
    if l.shape != m.shape: print(k, 'shape differs', l.shape, m.shape); continue
    d = np.abs(l - m).max(); worst = max(worst, d)
    print(k, 'ordered max vertex delta m', d)
print('WORST', worst, 'PASS(<=1e-4 m)' if worst <= 1e-4 else 'FAIL')
