# LY-049 prep: gate passage -> lot boundary measurement (read-only on all inputs).
# Frame: glTF world (x east, y up, z = -north). C02-010 matrix = translate(531, 0, -818.45), no rotation.
# Usage:
#   python measure_gate49.py --lod LOD0 --out measure-gate-LOD0.json
#   python measure_gate49.py --lod LOD0 --drop-ground --out neg-no-ground.json            (negative)
#   python measure_gate49.py --lod LOD0 --inject threshold --out neg-threshold.json       (negative: 3 cm undeclared sill)
#   python measure_gate49.py --lod LOD0 --inject double-slab --out neg-double-slab.json   (negative: 2nd ground layer, 2 mm above)
#   python measure_gate49.py --lod LOD0 --inject overrun-slab --out neg-overrun.json      (negative: slab crosses boundary into LY-082 zone)
#   python measure_gate49.py --lod LOD0 --standalone --out standalone-LOD0.json           (prototype alone, site nodes kept, no city ground)
import argparse, json, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glb49

LAB = 'D:/GitHub/creation-notebook-lab/docs/cities/luoyang/'
PROTO = {'LOD0': 'assets/c02v/A2-LOD0-prototype.glb', 'LOD1': 'assets/c02v/A2-LOD1-prototype.glb'}
EXCLUDE = ('site_lot', 'site_neutral_lane', 'designed_hardpacked_activity_ground')  # city-data.mjs:92-96
GROUNDS = {  # city node -> (file, translation) ; city-data.mjs ground nodes
    'ground-south': ('assets/ground-atomic/south.glb', (0, 0, 0)),
    'ground-retained': ('assets/ground-atomic/retained.glb', (0, 0, 0)),
    'ground-network-ground-stitched': ('assets/ground-atomic/network-ground-stitched.glb', (0, 0, 0)),
    'ground-D08': ('assets/ground-atomic/D08.glb', (580, 0, -960)),
}
TX, TZ = 531.0, -818.45
GATE_LX = (-5.000, -2.000)           # exact: front-ring opening (earth wall comps x<=-5.0 / x>=-2.0, z 11.65..12.0), see gate-components.json
GATE_POSTS_CLEAR_LX = (-4.565, -2.435)  # exact inner faces of timber jamb posts z 10.45..11.55 -> 2.13 m
GATE_CX_LOCAL = -3.5
Z_BOUND_LOCAL = 12.0                 # LY-006 zone LY-049:write:001 z max; = site_lot max z
REGION_L = dict(x0=-5.6, x1=-1.4, z0=5.0, z1=12.6)   # local, includes 0.6 m beyond boundary for handoff check
CELL = 0.02
BODY_W, BODY_H = 0.60, 1.80          # C probe envelope, not a regulation
FOOT_BAND = (0.05, 1.80)             # obstacle band above foot


def M_translate(tx, ty, tz):
    M = np.eye(4); M[:3, 3] = (tx, ty, tz); return M


def clip_poly_y(poly, y0, y1):
    def clip(pts, keep, inter):
        out = []
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            ka, kb = keep(a), keep(b)
            if ka:
                out.append(a)
            if ka != kb:
                out.append(inter(a, b))
        return out
    def ix(a, b, y):
        t = (y - a[1]) / (b[1] - a[1]); return a + t * (b - a)
    p = list(poly)
    p = clip(p, lambda q: q[1] >= y0, lambda a, b: ix(a, b, y0))
    if len(p) < 2:
        return []
    p = clip(p, lambda q: q[1] <= y1, lambda a, b: ix(a, b, y1))
    return p


def raster_poly_xz(poly, occ, gx0, gz0, nx, nz):
    P = np.array([[q[0], q[2]] for q in poly])
    # edges (covers vertical faces, which project to segments)
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        L = np.hypot(*(b - a)); n = max(2, int(L / (CELL * 0.25)) + 2)
        t = np.linspace(0, 1, n)[:, None]; S = a + t * (b - a)
        ix = np.floor((S[:, 0] - gx0) / CELL).astype(int); iz = np.floor((S[:, 1] - gz0) / CELL).astype(int)
        k = (ix >= 0) & (ix < nx) & (iz >= 0) & (iz < nz); occ[iz[k], ix[k]] = True
    # interior (non-degenerate projection)
    if len(P) >= 3:
        area = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
        if abs(area) > 1e-8:
            x0, z0 = P.min(0); x1, z1 = P.max(0)
            i0, i1 = max(0, int((x0 - gx0) / CELL)), min(nx - 1, int((x1 - gx0) / CELL))
            j0, j1 = max(0, int((z0 - gz0) / CELL)), min(nz - 1, int((z1 - gz0) / CELL))
            if i1 >= i0 and j1 >= j0:
                xs = gx0 + (np.arange(i0, i1 + 1) + 0.5) * CELL; zs = gz0 + (np.arange(j0, j1 + 1) + 0.5) * CELL
                X, Z = np.meshgrid(xs, zs)
                inside = np.zeros_like(X, bool)
                n = len(P)
                for i in range(n):
                    (xa, za), (xb, zb) = P[i], P[(i + 1) % n]
                    cond = (za > Z) != (zb > Z)
                    xint = xa + (Z - za) * (xb - xa) / np.where(zb - za == 0, 1e-30, zb - za)
                    inside ^= cond & (X < xint)
                occ[j0:j1 + 1, i0:i1 + 1] |= inside


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lod', default='LOD0')
    ap.add_argument('--out', required=True)
    ap.add_argument('--drop-ground', action='store_true')
    ap.add_argument('--standalone', action='store_true')
    ap.add_argument('--inject', choices=['threshold', 'double-slab', 'overrun-slab'])
    a = ap.parse_args()

    proto_path = LAB + PROTO[a.lod]
    Mc = M_translate(TX, 0, TZ)
    skip = () if a.standalone else EXCLUDE
    court = glb49.node_tris(proto_path, outer=Mc, skip=skip)
    wx0, wx1 = TX + REGION_L['x0'], TX + REGION_L['x1']
    wz0, wz1 = TZ + REGION_L['z0'], TZ + REGION_L['z1']
    court = {k: glb49.clip_xz(v, wx0 - 0.1, wx1 + 0.1, wz0 - 0.1, wz1 + 0.1) for k, v in court.items()}
    court = {k: v for k, v in court.items() if len(v)}

    grounds, gsha = {}, {}
    if not a.standalone:
        for name, (f, t) in GROUNDS.items():
            gsha[name] = glb49.sha256(LAB + f)
            if a.drop_ground and name == 'ground-south':
                continue
            tri = glb49.node_tris(LAB + f, outer=M_translate(*t))
            tri = np.concatenate(list(tri.values()))
            tri = glb49.clip_xz(tri, wx0 - 0.1, wx1 + 0.1, wz0 - 0.1, wz1 + 0.1)
            if len(tri):
                grounds[name] = tri
    else:
        # standalone: site nodes act as ground
        for k in EXCLUDE:
            if k in court:
                grounds['proto:' + k] = court.pop(k)

    # injections (negative tests): simple boxes as triangles
    def box(x0, x1, y0, y1, z0, z1):
        v = np.array([[x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1], [x0, y1, z0], [x1, y1, z0], [x1, y1, z1], [x0, y1, z1]])
        f = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)]
        return v[np.array(f)[:, ::-1]]  # reversed -> outward normals (top +y)
    if a.inject == 'threshold':
        court['INJECT_threshold'] = box(TX - 4.975, TX - 2.0, 0.2, 0.23, TZ + 11.6, TZ + 11.75)
    if a.inject == 'double-slab':
        grounds['INJECT_double_slab'] = box(TX - 4.9, TX - 2.1, 0.19, 0.202, TZ + 9.0, TZ + 12.0)
    if a.inject == 'overrun-slab':
        grounds['INJECT_overrun_slab'] = box(TX - 4.9, TX - 2.1, 0.19, 0.200, TZ + 9.0, TZ + 12.5)

    nx = int(round((wx1 - wx0) / CELL)); nz = int(round((wz1 - wz0) / CELL))
    xs = wx0 + (np.arange(nx) + 0.5) * CELL; zs = wz0 + (np.arange(nz) + 0.5) * CELL

    foot = np.full((nz, nx), np.nan); src = np.full((nz, nx), '', dtype=object)
    layers = np.zeros((nz, nx), int); bstep = np.full((nz, nx), np.nan)
    clear = np.full((nz, nx), np.inf)
    gnames = list(grounds)
    for j, z in enumerate(zs):
        for i, x in enumerate(xs):
            best, bsrc, tops = -np.inf, '', []
            for g in gnames:
                h = [y for y, ny in glb49.vray_hits(grounds[g], x, z) if ny > 0.3]
                if h:
                    t = max(h); tops.append(t)
                    if t > best:
                        best, bsrc = t, g
            if tops:
                ts = sorted(tops)
                # distinct walkable layers within 0.10 m of each other
                layers[j, i] = 1 + sum(1 for k in range(1, len(ts)) if ts[-1] - ts[k - 1] < 0.10)
            # building upward faces close above ground = steps/sills/plinths
            bu = []
            for k, v in court.items():
                for y, ny in glb49.vray_hits(v, x, z):
                    if abs(ny) > 0.3 and (np.isfinite(best) and best - 0.005 <= y <= best + 0.35 or (not np.isfinite(best) and y <= 0.6)):
                        bu.append(y)
            f = best
            if bu and (not np.isfinite(best) or max(bu) > best + 0.002):
                f = max(bu + ([best] if np.isfinite(best) else [])); bstep[j, i] = f - (best if np.isfinite(best) else 0)
                bsrc = 'building'
            if np.isfinite(f):
                foot[j, i] = f; src[j, i] = bsrc
                c = [y for k, v in court.items() for y, ny in glb49.vray_hits(v, x, z) if y > f + 0.02]
                if c:
                    clear[j, i] = min(c) - f
    # obstacle occupancy in band above nominal foot 0.2
    occ = np.zeros((nz, nx), bool)
    y0, y1 = 0.2 + FOOT_BAND[0], 0.2 + FOOT_BAND[1]
    for k, v in court.items():
        for t in v:
            if t[:, 1].max() < y0 or t[:, 1].min() > y1:
                continue
            p = clip_poly_y(t, y0, y1)
            if len(p) >= 2:
                raster_poly_xz(p, occ, wx0, wz0, nx, nz)

    cx = TX + GATE_CX_LOCAL
    ic = int((cx - wx0) / CELL)
    loc_z = zs - TZ
    rows = []
    for j in range(nz):
        # free interval containing centre column
        if occ[j, ic]:
            rows.append(dict(zl=round(loc_z[j], 3), free=None)); continue
        l = ic
        while l - 1 >= 0 and not occ[j, l - 1]:
            l -= 1
        r = ic
        while r + 1 < nx and not occ[j, r + 1]:
            r += 1
        fx0, fx1 = xs[l] - CELL / 2, xs[r] + CELL / 2
        seg = slice(l, r + 1)
        fy = foot[j, seg]
        rows.append(dict(zl=round(loc_z[j], 3), free=[round(fx0, 3), round(fx1, 3)], width=round(fx1 - fx0, 3),
                         footMin=None if np.all(np.isnan(fy)) else round(float(np.nanmin(fy)), 4),
                         footMax=None if np.all(np.isnan(fy)) else round(float(np.nanmax(fy)), 4),
                         unsupported=int(np.isnan(fy).sum()),
                         clearMin=round(float(np.min(clear[j, seg])), 3) if np.isfinite(np.min(clear[j, seg])) else None))

    # route corridor = lot cells from local z 6 to boundary, inside free interval of each row
    def corridor_stats(zl0, zl1, xw=None):
        sel = (loc_z >= zl0) & (loc_z < zl1)
        cells, uns, mlayer, steps, ys, srcs, cl = 0, 0, 0, 0.0, [], {}, np.inf
        bsteps = []
        for j in np.where(sel)[0]:
            rw = rows[j]
            if rw['free'] is None:
                continue
            k = (xs >= rw['free'][0]) & (xs <= rw['free'][1])
            if xw is not None:
                k &= (xs >= xw[0]) & (xs <= xw[1])
            idx = np.where(k)[0]
            cells += len(idx); uns += int(np.isnan(foot[j, idx]).sum())
            mlayer = max(mlayer, int(layers[j, idx].max()) if len(idx) else 0)
            ys += [float(v) for v in foot[j, idx] if np.isfinite(v)]
            for s in src[j, idx]:
                srcs[s] = srcs.get(s, 0) + 1
            cl = min(cl, float(np.min(clear[j, idx])) if len(idx) else np.inf)
            bsteps += [float(v) for v in bstep[j, idx] if np.isfinite(v)]
            # adjacent step (x and z neighbours)
            for i in idx:
                for dj, di in ((0, 1), (1, 0)):
                    jj, ii = j + dj, i + di
                    if jj < nz and ii < nx and np.isfinite(foot[j, i]) and np.isfinite(foot[jj, ii]) and not occ[jj, ii]:
                        steps = max(steps, abs(foot[jj, ii] - foot[j, i]))
        return dict(cells=cells, unsupported=uns, maxLayers=mlayer, yMin=round(min(ys), 4) if ys else None,
                    yMax=round(max(ys), 4) if ys else None, maxAdjStep_m=round(steps, 4),
                    sources=srcs, minClear_m=round(cl, 3) if np.isfinite(cl) else None,
                    buildingStepCells=len(bsteps), buildingStepMax_m=round(max(bsteps), 4) if bsteps else 0.0)

    passage = [r for r in rows if r['free'] is not None and 9.0 <= r['zl'] < 12.0]
    minw = min(passage, key=lambda r: r['width'])
    # body sweep: can a 0.60 m wide body pass along the centre line (any lateral offset per row) with clearance >= 1.80?
    body_ok, body_fail = True, []
    for r in rows:
        if not (6.0 <= r['zl'] < 12.0):
            continue
        if r['free'] is None or r['width'] < BODY_W or (r['clearMin'] is not None and r['clearMin'] < BODY_H):
            body_ok = False; body_fail.append(r['zl'])
    # beyond-boundary layer check (0..0.6 m outside, belongs to LY-082)
    beyond = corridor_stats(12.0, 12.6)
    out = dict(
        seat='LY-049', lod=a.lod, mode=('standalone' if a.standalone else 'city-terrain-loaded') + (' DROP ground-south' if a.drop_ground else '') + (f' INJECT {a.inject}' if a.inject else ''),
        inputs=dict(prototype=PROTO[a.lod], prototypeSha256=glb49.sha256(proto_path), grounds={k: (GROUNDS[k][0], v) for k, v in gsha.items()}),
        frame='glTF world x east, y up, z=-north; court C02-010 matrix translate(531,0,-818.45)',
        cell_m=CELL, bodyProbe_m=dict(width=BODY_W, height=BODY_H, note='C probe, not a regulation'),
        obstacleBand_y=[y0, y1], excludeNodes=list(skip),
        courtNodesInRegion={k: int(len(v)) for k, v in court.items()}, groundsInRegion={k: int(len(v)) for k, v in grounds.items()},
        gatePassage=dict(zLocal=[9.0, 12.0], minFreeWidth_m=minw['width'], minFreeWidthAtZl=minw['zl'], minFreeX_world=minw['free'],
                         widthAtBoundaryRow=passage[-1]['width'], freeAtBoundaryRow=passage[-1]['free']),
        corridor_court_z6_9=corridor_stats(6.0, 9.0),
        corridor_gate_z9_12=corridor_stats(9.0, 12.0),
        corridor_gate_between_posts_2p13=corridor_stats(9.0, 12.0, xw=(TX + GATE_POSTS_CLEAR_LX[0], TX + GATE_POSTS_CLEAR_LX[1])),
        beyondBoundary_z12_12p6=beyond,
        bodySweep=dict(ok=body_ok, failRowsLocalZ=body_fail[:20], nFail=len(body_fail)),
        centreline=[dict(zl=r['zl'], footMin=r.get('footMin'), footMax=r.get('footMax'), width=r.get('width'), clearMin=r.get('clearMin'))
                    for jj, r in enumerate(rows) if jj % 10 == 0 or r['zl'] in (11.99, 12.01)],
        boundaryRows=[r for r in rows if r['zl'] in (11.99, 12.01)],
        boundaryPortCandidate=dict(local=[GATE_CX_LOCAL, 0.2, Z_BOUND_LOCAL], world=[TX + GATE_CX_LOCAL, 0.2, TZ + Z_BOUND_LOCAL],
                                   forward=[0, 0, 1], up=[0, 1, 0], openingLocalX=list(GATE_LX), note='candidate only; frozen by LY-049 at delivery after G'),
        limits=['surface height field at cell centres + edge-sampled band rasterisation; not solid collision',
                'gaps narrower than one cell (0.02 m) not detected', 'no GPU / browser / animation test'])
    json.dump(out, open(a.out, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    print(json.dumps({k: out[k] for k in ('mode', 'gatePassage', 'corridor_gate_z9_12', 'corridor_court_z6_9', 'beyondBoundary_z12_12p6', 'bodySweep')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
