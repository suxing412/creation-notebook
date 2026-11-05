# LY-043 prep: exact axis-aligned box recovery from flat-shaded GLB meshes (read-only on inputs).
# Every triangle pair forming an axis-aligned rectangle becomes a face; faces are matched into boxes
# (two opposite faces per axis with identical extents, outward winding). Whatever is not explained
# by a box is returned as residual triangles so nothing is silently dropped.
import numpy as np

EPS = 1e-4


def tri_normal(t):
    n = np.cross(t[1] - t[0], t[2] - t[0]); L = np.linalg.norm(n)
    return n / L if L > 1e-12 else None


def rects(tris, stored_normals=None):
    """-> list of faces {axis, sign, c, lo(2), hi(2), tris[idx]} for axis-aligned tri pairs; residual idx."""
    faces, used = {}, np.zeros(len(tris), bool)
    flipped = []
    for i, t in enumerate(tris):
        n = tri_normal(t)
        if n is None:
            continue
        ax = int(np.argmax(np.abs(n)))
        if abs(abs(n[ax]) - 1) > 1e-4:
            continue
        sgn = 1 if n[ax] > 0 else -1
        if stored_normals is not None:
            sn = stored_normals[i].mean(0)
            if sn @ n < 0:
                flipped.append(i)
        c = round(float(t[:, ax].mean()) / EPS) * EPS
        o = [k for k in range(3) if k != ax]
        lo = tuple(np.round(t[:, o].min(0) / EPS).astype(np.int64)); hi = tuple(np.round(t[:, o].max(0) / EPS).astype(np.int64))
        key = (ax, sgn, int(round(c / EPS)), lo, hi)
        faces.setdefault(key, []).append(i)
    out = []
    for (ax, sgn, ci, lo, hi), ids in faces.items():
        # a rectangle = 2 triangles whose bbox is the same rectangle and whose areas sum to it
        area = (hi[0] - lo[0]) * (hi[1] - lo[1]) * EPS * EPS
        tri_area = sum(np.linalg.norm(np.cross(tris[i][1] - tris[i][0], tris[i][2] - tris[i][0])) / 2 for i in ids)
        if area > 0 and abs(tri_area - area * (len(ids) // 2)) < 1e-4 * max(area, 1e-3) and len(ids) % 2 == 0:
            for k in range(0, len(ids), 2):
                out.append({'axis': ax, 'sign': sgn, 'c': ci * EPS, 'lo': np.array(lo) * EPS, 'hi': np.array(hi) * EPS,
                            'tris': ids[k:k + 2]})
                used[ids[k:k + 2]] = True
    return out, np.nonzero(~used)[0], flipped


def _match(faces):
    by = {}
    for f in faces:
        by.setdefault((f['axis'], f['sign']), []).append(f)

    def k2(f):
        return (tuple(np.round(f['lo'] / EPS).astype(int)), tuple(np.round(f['hi'] / EPS).astype(int)))
    idx = {}
    for f in by.get((0, 1), []):
        idx.setdefault(k2(f), []).append(f)
    taken, boxes = set(), []
    for f in sorted(by.get((0, -1), []), key=lambda f: f['c']):
        cands = [g for g in idx.get(k2(f), []) if g['c'] > f['c'] + EPS / 2 and id(g) not in taken]
        if not cands:
            continue
        g = min(cands, key=lambda g: g['c'])
        x0, x1 = f['c'], g['c']; (y0, z0), (y1, z1) = f['lo'], f['hi']
        need = [(1, -1, y0, (x0, z0), (x1, z1)), (1, 1, y1, (x0, z0), (x1, z1)), (2, -1, z0, (x0, y0), (x1, y1)), (2, 1, z1, (x0, y0), (x1, y1))]
        got = []
        for ax, sg, c, lo, hi in need:
            hit = None
            for h in by.get((ax, sg), []):
                if id(h) in taken:
                    continue
                if abs(h['c'] - c) < EPS / 2 and np.allclose(h['lo'], lo, atol=EPS / 2) and np.allclose(h['hi'], hi, atol=EPS / 2):
                    hit = h; break
            if hit is None:
                break
            got.append(hit)
        if len(got) != 4:
            continue
        for h in [f, g] + got:
            taken.add(id(h))
        boxes.append({'min': np.array([x0, y0, z0]), 'max': np.array([x1, y1, z1]),
                      'tris': sum([h['tris'] for h in [f, g] + got], []), 'mergedFaces': sum(h.get('merged', 1) for h in [f, g] + got)})
    left = [f for f in faces if id(f) not in taken]
    return boxes, left


def _merge_once(faces):
    """merge one pair of coplanar same-facing rectangles that tile a larger rectangle exactly."""
    by = {}
    for f in faces:
        by.setdefault((f['axis'], f['sign'], int(round(f['c'] / EPS))), []).append(f)
    for L in by.values():
        for i in range(len(L)):
            for j in range(i + 1, len(L)):
                a, b = L[i], L[j]
                for d in (0, 1):
                    o = 1 - d
                    if abs(a['lo'][o] - b['lo'][o]) < EPS / 2 and abs(a['hi'][o] - b['hi'][o]) < EPS / 2 and                             (abs(a['hi'][d] - b['lo'][d]) < EPS / 2 or abs(b['hi'][d] - a['lo'][d]) < EPS / 2):
                        m = {'axis': a['axis'], 'sign': a['sign'], 'c': a['c'], 'lo': np.minimum(a['lo'], b['lo']),
                             'hi': np.maximum(a['hi'], b['hi']), 'tris': a['tris'] + b['tris'],
                             'merged': a.get('merged', 1) + b.get('merged', 1)}
                        return [f for f in faces if f is not a and f is not b] + [m], True
    return faces, False


def boxes_from(tris, stored_normals=None):
    faces, residual, flipped = rects(tris, stored_normals)
    boxes, left = _match(faces)
    # retry on leftovers with exact-tiling merges (faces split where a neighbour abuts them)
    while True:
        merged, changed = _merge_once(left)
        if not changed:
            break
        nb, nl = _match(merged)
        boxes += nb; left = nl
    return boxes, left, residual, flipped


def box_relation(a, b, tol=1e-4):
    """exact relation of two axis-aligned boxes."""
    lo = np.maximum(a['min'], b['min']); hi = np.minimum(a['max'], b['max'])
    d = hi - lo                       # >0 overlap, =0 touching, <0 gap along that axis
    gap = np.maximum(0, -d)
    if (d > tol).all():
        vol = float(np.prod(d)); va = float(np.prod(a['max'] - a['min'])); vb = float(np.prod(b['max'] - b['min']))
        inside = vol >= min(va, vb) - 1e-9
        return {'class': 'containment' if inside else 'intrusion', 'overlapVolume_m3': round(vol, 6),
                'overlapExtent_m': np.round(d, 4).tolist(), 'gap_m': 0.0}
    touching = (np.abs(d) <= tol)
    if (d >= -tol).all():
        nt = int(touching.sum())
        if nt == 1:
            ax = int(np.argmax(touching)); o = [k for k in range(3) if k != ax]
            return {'class': 'face-contact', 'axis': 'xyz'[ax], 'contactArea_m2': round(float(np.prod(d[o])), 6),
                    'contactExtent_m': np.round(d[o], 4).tolist(), 'gap_m': 0.0}
        return {'class': 'edge-or-corner-contact', 'touchingAxes': ''.join('xyz'[k] for k in range(3) if touching[k]), 'gap_m': 0.0}
    return {'class': 'separate', 'gap_m': round(float(np.linalg.norm(gap)), 4), 'gapPerAxis_m': np.round(gap, 4).tolist(),
            'overlapExtent_m': np.round(np.maximum(d, 0), 4).tolist()}
