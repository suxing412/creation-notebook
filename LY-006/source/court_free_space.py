# LY-006: free-space occupancy of the candidate demonstration courtyard prototype (local frame),
# used only to derive non-overlapping C-partition write zones for LY-041..049. Read-only.
# Occupied = any triangle sample with y in (y0, y1). Grid 0.1 m over site_lot+lane.
import json, sys, os, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from glbio import read_glb, mesh_items, apply

glb, out = sys.argv[1], sys.argv[2]
y0, y1, cell = 0.25, 2.2, 0.1
g = read_glb(glb)
X0, X1, Z0, Z1 = -9.0, 9.0, -12.0, 16.0
nx, nz = int(round((X1 - X0) / cell)), int(round((Z1 - Z0) / cell))
occ = np.zeros((nz, nx), bool)
per = {}
for i, name, w, pos, tri, anc in mesh_items(g):
    V = apply(w, pos)
    m = np.zeros((nz, nx), bool)
    for t in tri:
        a, b, c = V[t]
        L = max(np.linalg.norm(b - a), np.linalg.norm(c - a), np.linalg.norm(c - b))
        n = max(2, int(L / 0.04) + 1)
        u, v = np.meshgrid(np.linspace(0, 1, n), np.linspace(0, 1, n))
        k = (u + v) <= 1
        P = a + np.outer(u[k], b - a) + np.outer(v[k], c - a)
        P = P[(P[:, 1] > y0) & (P[:, 1] < y1)]
        if not len(P): continue
        ix = np.floor((P[:, 0] - X0) / cell).astype(int); iz = np.floor((P[:, 2] - Z0) / cell).astype(int)
        ok = (ix >= 0) & (ix < nx) & (iz >= 0) & (iz < nz)
        m[iz[ok], ix[ok]] = True
    per[name] = int(m.sum()); occ |= m

def free_rect(x0, x1, z0, z1):
    i0, i1 = int(round((x0 - X0) / cell)), int(round((x1 - X0) / cell))
    j0, j1 = int(round((z0 - Z0) / cell)), int(round((z1 - Z0) / cell))
    sub = occ[j0:j1, i0:i1]
    return {'box_xz': [x0, x1, z0, z1], 'cells': int(sub.size), 'occupiedCells': int(sub.sum())}

rects = {k: free_rect(*v) for k, v in json.load(open(sys.argv[3], encoding='utf-8')).items()} if len(sys.argv) > 3 else {}
res = {'glb': glb, 'sha256': g['sha256'], 'band_y': [y0, y1], 'cell_m': cell, 'extent_xz': [X0, X1, Z0, Z1],
       'occupiedCellsByNode': per, 'occupiedCellsTotal': int(occ.sum()), 'rects': rects}
# coarse free map rows (1 m) for the record
coarse = []
for j in range(0, nz, 10):
    coarse.append(''.join('#' if occ[j:j + 10, i:i + 10].any() else '.' for i in range(0, nx, 10)))
res['coarseMap_1m_rows_fromZminus12'] = coarse
json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n'.join(f'{Z0 + r:6.1f} {row}' for r, row in enumerate(coarse)))
for k, v in rects.items(): print(k, v)
