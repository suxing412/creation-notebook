# LY-043 prep: per-node world triangles plus stored per-corner normals (read-only GLB reader).
import numpy as np
from glbio import load, acc, trs


def node_geometry(path):
    js, binc = load(path)
    out = {}
    scene = js['scenes'][js.get('scene', 0)]
    stack = [(i, np.eye(4)) for i in scene['nodes']]
    while stack:
        i, P = stack.pop()
        n = js['nodes'][i]; M = P @ trs(n)
        if 'mesh' in n:
            T, N = [], []
            for prim in js['meshes'][n['mesh']]['primitives']:
                if prim.get('mode', 4) != 4:
                    continue
                pos = acc(js, binc, prim['attributes']['POSITION'])
                idx = acc(js, binc, prim['indices']).reshape(-1) if 'indices' in prim else np.arange(len(pos))
                p = (np.c_[pos, np.ones(len(pos))] @ M.T)[:, :3]
                T.append(p[idx.reshape(-1, 3)])
                if 'NORMAL' in prim['attributes']:
                    nr = acc(js, binc, prim['attributes']['NORMAL']) @ np.linalg.inv(M[:3, :3]).T
                    N.append(nr[idx.reshape(-1, 3)])
                else:
                    N.append(np.zeros_like(T[-1]))
            out[n.get('name', 'node%d' % i)] = (np.concatenate(T), np.concatenate(N))
        for c in n.get('children', []):
            stack.append((c, M))
    return out
