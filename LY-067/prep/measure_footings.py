"""LY-067 prep: read-only measurement of gallery-A (and access-A) footing points.

Usage:
  python -I measure_footings.py <out.json> <glb> [<glb> ...]

Reads GLB bytes directly (no Blender needed, no writes to the repo).
For each mesh primitive: welds by position (1e-5 m), finds connected
components, and classifies the lowest components as "foot" candidates:
  - post   : vertical prism, height > 1.0 m, footprint < 0.8 m
  - plinth : low block (height <= 0.6 m) whose top touches a post bottom
Then for each post it reports: footprint centre (glTF X,Z), bottom Y,
what is directly beneath it inside the same GLB (plinth top Y / nothing),
and the gap from the post bottom to Y=0 (asset origin plane).

Coordinates are glTF (Y up, metres). No city transform is applied:
gallery-A has no cityPlacement in bce3211, so world support cannot be
sampled; the script states that explicitly in the output.
"""
import hashlib
import json
import struct
import sys

import numpy as np


def load(path):
    b = open(path, 'rb').read()
    assert b[:4] == b'glTF', path
    l = struct.unpack('<I', b[12:16])[0]
    js = json.loads(b[20:20 + l])
    off = 20 + l
    bl = struct.unpack('<I', b[off:off + 4])[0]
    binc = b[off + 8:off + 8 + bl]
    return js, binc, hashlib.sha256(b).hexdigest(), len(b)


def acc(js, binc, i):
    a = js['accessors'][i]
    v = js['bufferViews'][a['bufferView']]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[a['componentType']]
    o = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = v.get('byteStride')
    if stride and stride != n * np.dtype(dt).itemsize:
        raise SystemExit('strided accessor not supported')
    arr = np.frombuffer(binc, dt, a['count'] * n, o)
    return arr.reshape(-1, n) if n > 1 else arr


def node_matrices(js):
    """World matrix per mesh node (TRS / matrix), column-vector convention."""
    def trs(n):
        if 'matrix' in n:
            return np.array(n['matrix'], dtype=float).reshape(4, 4).T
        t = np.array(n.get('translation', [0, 0, 0]), float)
        q = np.array(n.get('rotation', [0, 0, 0, 1]), float)
        s = np.array(n.get('scale', [1, 1, 1]), float)
        x, y, z, w = q
        R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                      [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                      [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
        M = np.eye(4)
        M[:3, :3] = R * s
        M[:3, 3] = t
        return M
    out = {}
    def walk(i, P):
        n = js['nodes'][i]
        M = P @ trs(n)
        if 'mesh' in n:
            out[i] = M
        for c in n.get('children', []):
            walk(c, M)
    for s in js.get('scenes', []):
        for r in s['nodes']:
            walk(r, np.eye(4))
    return out


def components(pos, tri):
    key = np.round(pos, 5)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    t = inv[tri]
    parent = np.arange(inv.max() + 1)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for a, b, c in t:
        ra = find(a)
        parent[find(b)] = ra
        parent[find(c)] = ra
    roots = np.array([find(i) for i in range(len(parent))])
    comps = {}
    for i, r in enumerate(roots[t[:, 0]]):
        comps.setdefault(int(r), []).append(i)
    return comps


def analyse(path):
    js, binc, sha, size = load(path)
    mats = node_matrices(js)
    parts = []
    for ni, M in mats.items():
        node = js['nodes'][ni]
        mesh = js['meshes'][node['mesh']]
        for pi, p in enumerate(mesh['primitives']):
            pos = acc(js, binc, p['attributes']['POSITION']).astype(float)
            pos = (np.c_[pos, np.ones(len(pos))] @ M.T)[:, :3]
            idx = acc(js, binc, p['indices']).reshape(-1, 3).astype(np.int64)
            for r, tl in components(pos, idx).items():
                vs = pos[idx[np.array(tl)].reshape(-1)]
                mn, mx = vs.min(0), vs.max(0)
                parts.append({'node': node.get('name'), 'prim': pi, 'tris': len(tl),
                              'min': mn.round(4).tolist(), 'max': mx.round(4).tolist()})
    allmin = np.min([p['min'] for p in parts], 0)
    allmax = np.max([p['max'] for p in parts], 0)
    # posts: tall slender vertical components reaching low
    posts, plinths = [], []
    for p in parts:
        mn, mx = np.array(p['min']), np.array(p['max'])
        sz = mx - mn
        if sz[1] > 1.0 and max(sz[0], sz[2]) < 0.8 and mn[1] < 1.0:
            posts.append(p)
        elif sz[1] <= 0.6 and mn[1] <= 0.05 and max(sz[0], sz[2]) < 2.0:
            plinths.append(p)
    feet = []
    for k, p in enumerate(sorted(posts, key=lambda q: (round(q['min'][0], 2), round(q['min'][2], 2)))):
        mn, mx = np.array(p['min']), np.array(p['max'])
        cx, cz = (mn[0] + mx[0]) / 2, (mn[2] + mx[2]) / 2
        under = None
        for q in plinths:
            qm, qx = np.array(q['min']), np.array(q['max'])
            if qm[0] - 1e-3 <= cx <= qx[0] + 1e-3 and qm[2] - 1e-3 <= cz <= qx[2] + 1e-3:
                under = q
        foot_y = under['min'][1] if under else mn[1]
        feet.append({
            'foot_id': f'A-F{k + 1:02d}',
            'post_centre_xz': [round(cx, 4), round(cz, 4)],
            'post_section_xz_m': [round(mx[0] - mn[0], 4), round(mx[2] - mn[2], 4)],
            'post_bottom_y': round(mn[1], 4),
            'post_top_y': round(mx[1], 4),
            'plinth': None if under is None else {
                'min': under['min'], 'max': under['max'], 'node': under['node'],
                'top_minus_post_bottom_m': round(under['max'][1] - mn[1], 5)},
            'lowest_point_y': round(foot_y, 4),
            'gap_to_local_y0_m': round(foot_y - 0.0, 4),
            'in_glb_support_below_plinth': 'none (no ground/base plate in GLB)',
        })
    return {
        'path': path.replace('\\', '/'), 'sha256': sha, 'bytes': size,
        'nodes': [n.get('name') for n in js['nodes']],
        'node_extras': [n.get('extras') for n in js['nodes']],
        'bbox_min': allmin.round(4).tolist(), 'bbox_max': allmax.round(4).tolist(),
        'components': len(parts),
        'components_touching_min_y': sum(1 for p in parts if abs(p['min'][1] - allmin[1]) < 1e-3),
        'post_count': len(posts), 'plinth_count': len(plinths),
        'feet': feet,
        'world_support': 'NOT SAMPLED: asset has no city node / cityPlacement in bce3211; '
                         'old candidate city transform and terrain are not in the repo',
    }


if __name__ == '__main__':
    out = sys.argv[1]
    res = [analyse(p) for p in sys.argv[2:]]
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for r in res:
        print(r['path'].split('/')[-1], r['sha256'][:12], 'bbox', r['bbox_min'], r['bbox_max'],
              'comps', r['components'], 'posts', r['post_count'], 'plinths', r['plinth_count'],
              'atMinY', r['components_touching_min_y'])
        for f in r['feet']:
            pl = f['plinth']
            print('  ', f['foot_id'], f['post_centre_xz'], 'sec', f['post_section_xz_m'],
                  'postY', f['post_bottom_y'], '->', f['post_top_y'],
                  'plinth', None if pl is None else (pl['min'][1], pl['max'][1], pl['top_minus_post_bottom_m']))
