# LY-048 prep measurement: boundary closure / service openings of the 6 in-city courtyard
# prototypes (as the city renders them: excludeNodes removed), plus world checks for all 44
# placed courtyards (lot overlap with neighbours, what lies outside each opening, ground cover).
# Read-only on the lab repo. Pure numpy/scipy; surface slices on a grid, NOT solid collision,
# NOT a continuous body sweep, NOT GPU.
#
# usage: python measure_closure.py <lab_root> <out_json> [cell_m]
import sys, os, json, time
import numpy as np
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glb_read import node_tris, sha256, col_major

H = 0.05  # grid cell (m); overridden by argv[3] in main()
HERE = os.path.dirname(os.path.abspath(__file__))
LOT_TOP = 0.2
# slice heights (world y, lot top = 0.20). Offsets of 3 mm avoid coplanar vertex rows.
HEIGHTS = [0.233, 0.353, 0.553, 0.953, 1.453, 1.953]
PERSON_H = 0.953  # height used to call an opening "passable" in the closure ring test
MIN_PASS_W = 0.60  # m, C working value for a person-sized gap (shoulder width); not a regulation


def lot_rect(nt):
    p = nt['site_lot'].reshape(-1, 3)
    return float(p[:, 0].min()), float(p[:, 0].max()), float(p[:, 2].min()), float(p[:, 2].max())


def slice_segments(tris, h):
    y = tris[:, :, 1] - h
    s = np.sign(y); s[s == 0] = 1e-9
    segs = []
    for a, b in ((0, 1), (1, 2), (2, 0)):
        cross = (s[:, a] * s[:, b]) < 0
        t = np.where(cross, y[:, a] / np.where(cross, (y[:, a] - y[:, b]), 1), 0)
        p = tris[:, a] + (tris[:, b] - tris[:, a]) * t[:, None]
        segs.append((cross, p[:, [0, 2]]))
    pts = []
    for i in range(len(tris)):
        q = [segs[k][1][i] for k in range(3) if segs[k][0][i]]
        if len(q) >= 2:
            pts.append((q[0], q[1]))
    return pts


def raster_block(tris, h, x0, z0, nx, nz):
    blk = np.zeros((nx, nz), bool)
    keep = (tris[:, :, 1].min(1) < h) & (tris[:, :, 1].max(1) > h)
    for a, b in slice_segments(tris[keep], h):
        L = float(np.hypot(*(b - a)))
        n = max(2, int(L / (H * 0.4)) + 2)
        t = np.linspace(0, 1, n)[:, None]
        q = a + (b - a) * t
        ix = np.floor((q[:, 0] - x0) / H).astype(int); iz = np.floor((q[:, 1] - z0) / H).astype(int)
        ok = (ix >= 0) & (ix < nx) & (iz >= 0) & (iz < nz)
        blk[ix[ok], iz[ok]] = True
    return blk


def vertical_hits(tris, x, z):
    """y of every triangle hit by the vertical line through (x,z)."""
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    def cr(p, q, r):
        return (q[:, 0] - p[:, 0]) * (r[1] - p[:, 2]) - (q[:, 2] - p[:, 2]) * (r[0] - p[:, 0])
    P = (x, z)
    d1, d2, d3 = cr(a, b, P), cr(b, c, P), cr(c, a, P)
    inside = ((d1 >= 0) & (d2 >= 0) & (d3 >= 0)) | ((d1 <= 0) & (d2 <= 0) & (d3 <= 0))
    ys = []
    for i in np.nonzero(inside)[0]:
        A, B, C = tris[i]
        n = np.cross(B - A, C - A)
        if abs(n[1]) < 1e-12:
            continue
        ys.append(float(A[1] - (n[0] * (x - A[0]) + n[2] * (z - A[2])) / n[1]))
    return sorted(set(round(v, 3) for v in ys))


def fill_solid_interiors(blk, tris, h, cx, cz, samples=5):
    """Free components enclosed by slice outlines that are the inside of a closed solid become
    blocked. Parity is taken PER NODE (odd number of that node's surface crossings on the vertical
    ray above the slice), so a wall top coplanar with a roof-cap bottom in another node is not
    cancelled out. `tris` is a list of per-node (N,3,3) arrays (or one array)."""
    parts = tris if isinstance(tris, (list, tuple)) else [tris]
    lab, n = ndimage.label(~blk)
    border = set(np.unique(np.r_[lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]]).tolist())
    rng = np.random.default_rng(48)
    out = blk.copy(); nsolid = 0
    for l in range(1, n + 1):
        if l in border:
            continue
        cells = np.argwhere(lab == l)
        pick = cells[rng.choice(len(cells), size=min(samples, len(cells)), replace=False)]
        odd = 0
        for i, k in pick:
            inside = False
            for t in parts:
                hits = [y for y in vertical_hits(t, cx[i], cz[k]) if y > h]
                if len(hits) % 2:
                    inside = True; break
            odd += inside
        if odd * 2 > len(pick):
            out[lab == l] = True; nsolid += 1
    return out, nsolid


def runs(mask1d):
    out = []; i = 0; n = len(mask1d)
    while i < n:
        if mask1d[i]:
            j = i
            while j + 1 < n and mask1d[j + 1]:
                j += 1
            out.append((i, j)); i = j + 1
        else:
            i += 1
    return out


def analyse(rel, excl):
    path = os.path.join(CITY, rel)
    res, rect = analyse_nt(node_tris(path), excl)
    res['file'] = rel; res['sha256'] = sha256(path)
    return res, rect


def analyse_nt(nt, excl):
    missing = [e for e in excl if e not in nt]
    keep = {k: t for k, t in nt.items() if k not in excl}
    allr = np.concatenate(list(keep.values()))
    lx0, lx1, lz0, lz1 = lot_rect(nt)
    x0, z0 = lx0 - 1.5, lz0 - 1.5
    nx = int(np.ceil((lx1 - lx0 + 3) / H)); nz = int(np.ceil((lz1 - lz0 + 3) / H))
    cx = x0 + (np.arange(nx) + 0.5) * H; cz = z0 + (np.arange(nz) + 0.5) * H
    L = (cx[:, None] > lx0) & (cx[:, None] < lx1) & (cz[None, :] > lz0) & (cz[None, :] < lz1)
    ix_lo, ix_hi = np.nonzero(L.any(1))[0][[0, -1]]; iz_lo, iz_hi = np.nonzero(L.any(0))[0][[0, -1]]
    sides = {  # name: (cells along edge (ix,iz) list, coordinate label, outward normal in local xz)
        'front(+z)': ([(i, iz_hi) for i in range(ix_lo, ix_hi + 1)], 'x', (0, 1)),
        'back(-z)': ([(i, iz_lo) for i in range(ix_lo, ix_hi + 1)], 'x', (0, -1)),
        'left(-x)': ([(ix_lo, k) for k in range(iz_lo, iz_hi + 1)], 'z', (-1, 0)),
        'right(+x)': ([(ix_hi, k) for k in range(iz_lo, iz_hi + 1)], 'z', (1, 0)),
    }
    res = {'excludeNodes': excl, 'excludeNodesMissing': missing,
           'retainedNodes': {k: int(len(t)) for k, t in keep.items()}, 'lotRect_xz': [lx0, lx1, lz0, lz1],
           'heights': {}}
    for h in HEIGHTS:
        blk = raster_block(allr, h, x0, z0, nx, nz)
        blk, nsolid = fill_solid_interiors(blk, list(keep.values()), h, cx, cz)
        F = (~blk) & L
        lab, nlab = ndimage.label(F)
        sizes = ndimage.sum(np.ones_like(lab), lab, index=np.arange(1, nlab + 1)) * H * H if nlab else np.array([])
        yard = int(np.argmax(sizes) + 1) if nlab else 0
        # outside region reachability (whole grid, free cells, from border)
        free_all = ~blk
        lab_all, _ = ndimage.label(free_all)
        border = set(np.unique(np.r_[lab_all[0, :], lab_all[-1, :], lab_all[:, 0], lab_all[:, -1]]).tolist()) - {0}
        yard_cells = lab == yard
        yard_reach_outside = bool(np.isin(lab_all[yard_cells], list(border)).any()) if yard else False
        ops = []
        for sname, (cells, ax, nrm) in sides.items():
            fr = np.array([F[i, k] for i, k in cells])
            for a, b in runs(fr):
                seg = cells[a:b + 1]
                labs = sorted(set(int(lab[i, k]) for i, k in seg))
                c0 = cx[seg[0][0]] if ax == 'x' else cz[seg[0][1]]
                c1 = cx[seg[-1][0]] if ax == 'x' else cz[seg[-1][1]]
                mid = seg[len(seg) // 2]
                ops.append({'side': sname, 'along': ax, 'from': round(float(c0 - H / 2), 3), 'to': round(float(c1 + H / 2), 3),
                            'width': round(float((b - a + 1) * H), 3),
                            'mid_xz': [round(float(cx[mid[0]]), 3), round(float(cz[mid[1]]), 3)], 'normal_xz': nrm,
                            'connectsYard': yard in labs,
                            'componentAreas_m2': [round(float(sizes[l - 1]), 2) for l in labs if l > 0]})
        res['heights'][str(h)] = {'yardArea_m2': round(float(sizes[yard - 1]), 2) if yard else 0,
                                  'components': int(nlab), 'yardReachableFromOutside': yard_reach_outside,
                                  'blockedLotCells': int((blk & L).sum()), 'solidInteriorsFilled': int(nsolid), 'openings': ops}
    # vertical profile at the middle of each person-height opening
    for o in res['heights'][str(PERSON_H)]['openings']:
        x, z = o['mid_xz']; nxz = o['normal_xz']
        o['verticalHits_atMid'] = vertical_hits(allr, x - nxz[0] * 0.10, z - nxz[1] * 0.10)
    return res, (lx0, lx1, lz0, lz1)


def world_rect(rect, M):
    lx0, lx1, lz0, lz1 = rect
    c = np.array([[lx0, 0, lz0, 1], [lx1, 0, lz0, 1], [lx0, 0, lz1, 1], [lx1, 0, lz1, 1]]) @ M.T
    return float(c[:, 0].min()), float(c[:, 0].max()), float(c[:, 2].min()), float(c[:, 2].max())


def ground_top(gtris, x, z):
    best = None
    for name, t in gtris.items():
        sel = (t[:, :, 0].min(1) <= x) & (t[:, :, 0].max(1) >= x) & (t[:, :, 2].min(1) <= z) & (t[:, :, 2].max(1) >= z)
        if not sel.any():
            continue
        hs = vertical_hits(t[sel], x, z)
        if hs:
            top = max(hs)
            if best is None or top > best[1]:
                best = (name, top)
    return best


def main():
    global H, CITY, REC
    LAB = sys.argv[1]; OUT = sys.argv[2]; H = float(sys.argv[3]) if len(sys.argv) > 3 else 0.05
    CITY = os.path.join(LAB, 'docs/cities/luoyang')
    REC = json.load(open(os.path.join(HERE, 'city-courtyards.json'), encoding='utf-8'))
    t0 = time.time()
    assets = {a['id']: a for a in REC['assets']}
    report = {'tool': 'measure_closure.py', 'cell_m': H, 'heights_world_y': HEIGHTS, 'lotTop': LOT_TOP,
              'personHeight_world_y': PERSON_H, 'minPassWidth_m_C': MIN_PASS_W,
              'scope': 'horizontal slice outlines of retained (city-rendered) triangles rasterised on a %.2f m grid; '
                       '4-connected free-space labelling inside the site_lot rectangle; ring = 1 cell inside the lot edge. '
                       'Not solid collision, not continuous body sweep, not GPU.' % H,
              'inputs': {'docs/cities/luoyang/city-data.mjs': sha256(os.path.join(CITY, 'city-data.mjs'))},
              'prototypes': {}, 'world': {}}
    rects = {}
    for aid, a in assets.items():
        if not aid.startswith('courtyard'):
            continue
        for lod, rel, sh in (('LOD1', a['path'], a['sha256']), ('LOD0', a['nearPath'], a['nearSha256'])):
            r, rect = analyse(rel, a['excludeNodes'])
            r['shaMatchesCityData'] = (r['sha256'] == sh)
            report['inputs']['docs/cities/luoyang/' + rel] = r['sha256']
            report['prototypes'][aid + '/' + lod] = r
            rects[aid] = rect
            print(aid, lod, round(time.time() - t0, 1), 's', flush=True)

    # ---- grounds (world)
    gtris = {}
    for g in REC['grounds']:
        a = assets[g['asset']]
        p = os.path.join(CITY, a['path'])
        report['inputs']['docs/cities/luoyang/' + a['path']] = sha256(p)
        t = np.concatenate(list(node_tris(p).values()))
        t = t + np.array(g['position'], dtype=float)[None, None, :]
        gtris[g['id']] = t

    # ---- world: 44 placed courtyards
    wr = {}
    for c in REC['courtyards']:
        M = col_major(c['matrix'])
        wr[c['id']] = (world_rect(rects[c['asset']], M), M, c['asset'])


    def inside(rect, x, z, pad=0.0):
        return rect[0] - pad < x < rect[1] + pad and rect[2] - pad < z < rect[3] + pad


    lane_local = {}  # site_neutral_lane rect per asset (local)
    for aid, a in assets.items():
        if aid.startswith('courtyard'):
            p = node_tris(os.path.join(CITY, a['path']))['site_neutral_lane'].reshape(-1, 3)
            lane_local[aid] = (float(p[:, 0].min()), float(p[:, 0].max()), float(p[:, 2].min()), float(p[:, 2].max()))

    pairs = []
    ids = list(wr)
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            A, B = wr[ids[i]][0], wr[ids[j]][0]
            ox = min(A[1], B[1]) - max(A[0], B[0]); oz = min(A[3], B[3]) - max(A[2], B[2])
            if ox > 0 and oz > 0:
                pairs.append({'a': ids[i], 'b': ids[j], 'overlap_m2': round(ox * oz, 3)})
            else:
                gap = np.hypot(max(0, -ox), max(0, -oz))
                if gap < 3.0:
                    pairs.append({'a': ids[i], 'b': ids[j], 'gap_m': round(float(gap), 3)})
    report['world']['lotPairsWithin3m'] = pairs

    for cid, (rect, M, aid) in wr.items():
        ent = {'asset': aid, 'lotRect_world_xz': [round(v, 3) for v in rect], 'openings_personHeight': []}
        for o in report['prototypes'][aid + '/LOD0']['heights'][str(PERSON_H)]['openings']:
            x, z = o['mid_xz']; n = o['normal_xz']
            probes = []
            for d in (0.25, 1.0, 2.5):
                p = M @ np.array([x + n[0] * d, 0, z + n[1] * d, 1])
                hit_lot = [k for k, v in wr.items() if k != cid and inside(v[0], p[0], p[2])]
                hit_lane = [k for k, v in wr.items() if inside(world_rect(lane_local[v[2]], v[1]), p[0], p[2])]
                g = ground_top(gtris, p[0], p[2])
                probes.append({'d_m': d, 'world_xz': [round(float(p[0]), 3), round(float(p[2]), 3)],
                               'insideOtherLot': hit_lot, 'insideLaneOf': hit_lane,
                               'ground': None if g is None else {'supplier': g[0], 'top_y': round(g[1], 3)}})
            ent['openings_personHeight'].append({'side': o['side'], 'from': o['from'], 'to': o['to'], 'width': o['width'],
                                                 'connectsYard': o['connectsYard'], 'probes': probes})
        report['world'][cid] = ent
    print('world', round(time.time() - t0, 1), 's', flush=True)
    json.dump(report, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
